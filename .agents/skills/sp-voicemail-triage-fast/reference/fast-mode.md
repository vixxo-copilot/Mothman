# Fast mode — shell vs agent vetting

`sp-voicemail-triage-fast` runs the parent KSOnboarding batch pipeline with
**`--skip-vetting`** in the **shell wrapper**, then runs the QSIAP AP voicemail
transcript-only handoff path from `sp-inbound-vetting`. Agent sessions add
**`sp-inbound-vetting`** lite vet via **Skills MCP** before KSOnboarding writes —
see [inbound-vetting-reroute.md](inbound-vetting-reroute.md).

## Shell batch — skipped (for speed)

| Step | Parent skill | Shell fast skill |
| --- | --- | --- |
| Siebel / Gateway SP lookup | MCP | **Skipped** |
| Gateway / VixxoLink customer lookup | MCP | **Skipped** |
| JDE vendor lookup | MCP | **Skipped** |
| Salesforce Lead / Account lookup | MCP | **Skipped** |
| Salesforce Lead note (onboarding branch) | MCP write | **Skipped** |
| Outlook inbox scan (batch REST path) | M365 MCP | **Skipped** (Freshdesk REST only) |
| **sp-inbound-vetting** routing table | — | **Skipped** |

Internal notes record **vetting skipped** and **entity posture: Unknown**.

## Agent batch — lite vet via sp-inbound-vetting

| Step | Shell fast | Agent fast (lite) | Agent + document dry-run |
| --- | --- | --- | --- |
| Skills MCP `get_skill("sp-inbound-vetting")` | Skipped | **Required** | **Required** |
| Gateway + VixxoLink SP lookup | Skipped | **Yes** (read-only) | **Yes** |
| Salesforce Lead/Case/Account SOQL | Skipped | **Yes** (read-only) | **Yes** + dedupe Case |
| Routing table reroute (AP vs SPM, COI, onboarding) | Keyword only | **Merged with keywords** | **Merged** |
| SF Case/Lead Task | Skipped | **Skipped** | **Planned** (not posted) |
| Internal note vetting table | "Skipped" | **Gateway + SF table** | **Full planned body** |
| FD forward / resolve / cf_sp / tags | Live (shell) | **Live** | **Planned only** |
| `cf_sp` on resolve | `Unknown` | **SP name/# when Known SP** | **Planned value** |

Document dry-run spec: [inbound-vetting-document-phase-dry-run.md](inbound-vetting-document-phase-dry-run.md)

## Still performed (both tiers)

- Freshdesk KSOnboarding search + voicemail subject filter
- Freshdesk QSIAP AP voicemail search (`qsiap@vixxo.com`, subject `New voicemail`)
- **Audio download** (`.wav` or `.mp3`) from ticket attachments (required — body has no spoken content)
- **faster-whisper** transcription (local, no API key) — **required before any write**
- On success: keyword classification, callback decision, internal note, forward, resolve
- On transcription failure: **no Freshdesk updates** — ticket stays open
- QSIAP fast mode posts transcript handoff notes/tags only; it does not perform
  Gateway/VixxoLink/SF SP attribution or update `cf_sp`

## When to use parent instead

- Single-item triage with full company vetting table **and** Salesforce Lead/Case Tasks
- Onboarding branch where Salesforce Lead note is **required**
- Outlook inbox voicemails (M365 MCP)
- SR branch needing full Gateway PM/support email resolution with parent SR workflow

## Batch commands

**Shell / cron:**

```bash
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py
```

**KSOnboarding only:**

```bash
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py --no-qsiap
```

**QSIAP only:**

```bash
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py --qsiap-only
```

**Agent — preview:**

```bash
python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py --dry-run
```

Optional flags (passed through to parent script):

| Flag | Effect |
| --- | --- |
| `--dry-run` | Triage preview only; no writes — use before lite vet |
| `--no-email` | Same as `sp-voicemail-triage-no-email` |
| `--no-transcribe` | **Not for automation** — disables STT; no writes |
| `--reroute-spm` | Parent flag — AP→SPM correction note on forward (narrow fix) |
| `--no-qsiap` | Skip the QSIAP AP voicemail enrichment path |
| `--qsiap-only` | Run only QSIAP AP voicemail enrichment |
| `--qsiap-re-vet` | Include already-vetted QSIAP voicemail tickets |

Scheduled automation setup: [../../sp-voicemail-triage/reference/automation-setup.md](../../sp-voicemail-triage/reference/automation-setup.md)
