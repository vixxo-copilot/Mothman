---
name: sp-voicemail-triage-fast
description: >-
  Fast SP voicemail triage for scheduled automation and agent batch runs.
  Downloads audio attachments (.wav or .mp3), transcribes locally with
  faster-whisper, classifies, posts Freshdesk internal notes, forwards to
  SPM/AP/COI/recruitment, resolves KSOnboarding tickets, and includes QSIAP
  AP voicemails for Freshdesk enrichment. Agent sessions
  load published skill sp-inbound-vetting via Skills MCP for lite identity
  vetting and quicker reroute before writes. Shell cron batch skips external
  vetting (--skip-vetting). For full vetting + SF Tasks use parent
  sp-voicemail-triage; for no email use sp-voicemail-triage-no-email.
---

# SP Voicemail Triage — Fast

Automation-first variant of **`sp-voicemail-triage`**. Same Freshdesk intake,
**Whisper transcription**, classification, callback decision, internal note,
forward, and resolve.

Two execution tiers:

| Tier | Vetting | Document | Writes |
| --- | --- | --- | --- |
| **Shell batch (cron)** | Keyword only — `--skip-vetting` | Skipped | Batch script (FD live) |
| **Agent session (lite)** | **`sp-inbound-vetting`** lite vet via **Skills MCP** | FD note + forward + resolve only | Freshdesk MCP or batch |
| **Agent + document dry-run** | Lite vet + full inbound **document phase** | SF Task + FD plans in packet | **None** until approved |

## When to use

- Scheduled Cursor Automation on KSOnboarding and QSIAP voicemail queues
- "Run fast voicemail triage" / "automation voicemail batch"
- Agent batch when Gateway/Salesforce MCP is available and **quicker reroute**
  matters more than full parent SF Task writes

**Use parent `sp-voicemail-triage`** when Siebel/Gateway/JDE/Salesforce vetting
with Salesforce Lead/Case Tasks is required, or for Outlook inbox voicemails.

**Use `sp-voicemail-triage-no-email`** when forwards must not send.

## Prerequisites

| Requirement | Details |
| --- | --- |
| `FRESHDESK_API_KEY` | Yes — `.env` or `~/.vixxo/freshdesk_token` |
| `FRESHDESK_DOMAIN` | Optional (default `vixxo-helpdesk.freshdesk.com`) |
| **faster-whisper** | `pip install -r ../sp-voicemail-triage/scripts/requirements.txt` |
| **ffmpeg** | On `PATH` |
| **Skills MCP** | **`project-0-assistant-CGagner-skills`** — agent tier only |
| **Published skill** | **`sp-inbound-vetting`** (`get_skill`, `source: "vixxo"`) — agent tier |

Optional: `WHISPER_MODEL` (default `small`), `WHISPER_DEVICE` (`cpu`), `WHISPER_COMPUTE_TYPE` (`int8`).

Verify:

```bash
python .agents/skills/sp-voicemail-triage/scripts/setup_transcription.py
python .agents/skills/sp-voicemail-triage/scripts/verify_transcription.py
```

The fast batch wrapper runs preflight automatically. See
[../sp-voicemail-triage/reference/automation-setup.md](../sp-voicemail-triage/reference/automation-setup.md).

## Skills MCP — load sp-inbound-vetting

At the start of every **agent** run (not required for shell-only cron):

1. Call **`get_skill`** on server **`project-0-assistant-CGagner-skills`**:

   ```json
   { "name": "sp-inbound-vetting", "source": "vixxo" }
   ```

2. If `found: false`, load the repo copy:

   ```text
   .agents/skills/sp-inbound-vetting/SKILL.md
   ```

3. Enable Gateway, VixxoLink, Salesforce, and Freshdesk MCPs for lite vetting.

Full reroute workflow: [reference/inbound-vetting-reroute.md](reference/inbound-vetting-reroute.md).

**Document phase dry-run** (SF Task drafts + planned FD writes, no API posts):
[reference/inbound-vetting-document-phase-dry-run.md](reference/inbound-vetting-document-phase-dry-run.md).

## Batch command (shell / cron)

```bash
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py
```

The wrapper injects **`--skip-vetting`**. Transcription is **always on** — do not
pass `--no-transcribe` in automation.

By default the wrapper now runs two Freshdesk voicemail paths:

1. **KSOnboarding:** parent fast voicemail triage, keyword routing, internal note,
   optional forward, and resolve.
2. **QSIAP AP voicemail:** `sp-inbound-vetting` QSIAP runner for
   `qsiap@vixxo.com` `New voicemail` tickets; transcribes audio, performs
   Gateway/SF identity enrichment when available, posts Freshdesk internal notes,
   updates `cf_sp`/tags, and leaves outbound forwarding out of scope.

Use `--no-qsiap` for a KSOnboarding-only run or `--qsiap-only` to run only the
QSIAP voicemail path. Use `--qsiap-re-vet` when already-vetted QSIAP voicemail
tickets should be included again.

## Agent batch command (vet + reroute)

```bash
# Phase 1 — transcribe + keyword classify, no writes
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py --dry-run
```

Then run **lite vetting** per forwardable ticket using **`sp-inbound-vetting`**
(routing table + company vetting — read-only). Merge routes and apply Freshdesk
writes via MCP. See [reference/inbound-vetting-reroute.md](reference/inbound-vetting-reroute.md).

## Intake filter

Same as parent — subject must **include** `New voicemail`:

[../sp-voicemail-triage/reference/freshdesk-voicemail-filter.md](../sp-voicemail-triage/reference/freshdesk-voicemail-filter.md)

Each ticket includes an **audio attachment** (`.wav` or `.mp3`) from the voicemail
email. The email body is notification metadata only — **not a transcript**. Spoken
content must come from transcribing the attachment.

## Pipeline

### Shell batch

1. Search open KSOnboarding tickets (paginated REST)
2. Filter voicemail subjects
3. Download **audio attachment** (`.wav` or `.mp3`, required)
4. Transcribe with **faster-whisper** (local) — **required**
5. If **no-forward** rule matches (foul language, &lt;10s, blank/1–2 words) → note, no forward, resolve
6. **Otherwise:** keyword classify, internal note (vetting skipped), forward, resolve
7. **On transcription failure:** skip ticket — no Freshdesk updates
8. Run QSIAP AP voicemail enrichment for open `qsiap@vixxo.com` `New voicemail`
   Freshdesk tickets unless `--no-qsiap` was passed

### Agent batch (with sp-inbound-vetting)

1. **`get_skill("sp-inbound-vetting")`** (+ MCP enablement)
2. Dry-run batch (steps 1–4 above + keyword classify)
3. **Lite vet** forwardable items — Gateway + SF + [queues routing table](../sp-inbound-vetting/reference/queues.md)
4. **Merge route** (payment/AP, sourcing guardrail, Known SP onboarding — see reroute doc)
5. Post internal note **with vetting table**, forward merged route, resolve (`cf_sp` when known)
6. Report `vetting_rerouted` / `vetting_rerouted_ids` in summary

Phase 2 runs automatically (except `--dry-run`).

## Skipped vs parent

See [reference/fast-mode.md](reference/fast-mode.md).

## Scheduled automation

[../sp-voicemail-triage/reference/automation-setup.md](../sp-voicemail-triage/reference/automation-setup.md)

### Shell-only cron prompt

```markdown
Run SP voicemail fast batch:
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py

Report processed, transcribed, transcription_failed, routed, closed, failed from JSON summary.
Do not pass --no-transcribe. Shell path uses --skip-vetting for KSOnboarding
(keyword routing only) and includes QSIAP AP voicemail enrichment by default.
Tickets with transcription_failed were left open unchanged.
```

### Agent cron prompt (with vetting reroute — lite, live FD writes)

```markdown
Run SP voicemail fast batch with inbound vetting reroute:

1. get_skill("sp-inbound-vetting", source: "vixxo") on project-0-assistant-CGagner-skills
   (fallback: .agents/skills/sp-inbound-vetting/SKILL.md)
2. Dry-run batch:
   python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py --dry-run
3. Lite-vet each forwardable ticket per reference/inbound-vetting-reroute.md
4. Apply Freshdesk writes with merged routes and vetting table in internal notes
5. Report batch JSON fields plus vetting_rerouted and vetting_rerouted_ids

Enable Gateway, VixxoLink, Salesforce, and Freshdesk MCPs.
Do not pass --no-transcribe. Do not auto-send outbound beyond FD forward API.
```

### Agent prompt (document phase dry-run — SF + FD planned, no writes)

```markdown
Run SP voicemail fast batch with inbound vetting document phase dry-run:

1. get_skill("sp-inbound-vetting", source: "vixxo") on project-0-assistant-CGagner-skills
2. python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py --dry-run
3. Lite-vet + merge routes per reference/inbound-vetting-reroute.md
4. Plan document phase per reference/inbound-vetting-document-phase-dry-run.md
   (SF Case/Lead Task drafts, FD note/cf_sp/tags/forward/resolve) — NO writes
5. Save *-document-dry-run.json under sp-voicemail-triage/.tmp/batch-run/
6. Report document_dry_run, sf_tasks_planned, fd_writes_planned, vetting_rerouted

Enable Gateway, VixxoLink, Salesforce, and Freshdesk MCPs.
Live apply only after explicit operator approval.
```

## Sibling skills

| Skill | Use |
| --- | --- |
| `sp-inbound-vetting` | Published skill — lite vet, routing table, document phase dry-run |
| `sp-voicemail-triage` | Full vetting + Outlook + SF Tasks |
| `sp-voicemail-triage-no-email` | No forwards |
| `sp-voicemail-triage-webhook` | WAV webhook intake |
