# Inbound vetting reroute — Skills MCP + sp-inbound-vetting

Agent sessions use the **published** skill **`sp-inbound-vetting`** (via Skills MCP)
for **read-only lite vetting** after transcription and before Freshdesk writes.
Goal: correct keyword misroutes (especially payment → AP vs sourcing → SPM) and
enrich internal notes with Gateway / Salesforce identity — faster than running the
full parent **`sp-voicemail-triage`** pipeline.

Shell-only cron runs **do not** invoke this path; they keep `--skip-vetting` keyword
routing. See [fast-mode.md](fast-mode.md).

## Skills MCP (session start)

Server: **`project-0-assistant-CGagner-skills`**

| Tool | Use |
| --- | --- |
| `get_skill` | Load **`sp-inbound-vetting`** (`source: "vixxo"`) — routing table, company vetting, entity extraction |
| `search_skills` | Confirm catalog name if `get_skill` fails |
| `list_skills` | Optional — filter `source: "vixxo"` |

**Fallback** when the catalog entry is missing (local-only or not yet synced):

```text
.agents/skills/sp-inbound-vetting/SKILL.md
.agents/skills/sp-inbound-vetting/reference/queues.md
.agents/skills/sp-inbound-vetting/reference/company-vetting.md
.agents/skills/sp-inbound-vetting/reference/intake.md
```

Required MCPs for lite vet (same as **`sp-inbound-vetting`** reads):

- **`project-0-assistant-CGagner-gateway`**
- **`project-0-assistant-CGagner-vixxolink`**
- **`project-0-assistant-CGagner-salesforce`**
- **`project-0-assistant-CGagner-freshdesk`** (writes)

## Lite vetting scope (voicemail)

Follow **`sp-inbound-vetting`** for **search and routing only**. Do **not** run its
document phase on voicemail items:

| sp-inbound-vetting step | Voicemail fast path |
| --- | --- |
| Entity extraction | **Yes** — transcript + ticket metadata |
| Gateway + VixxoLink SP lookup | **Yes** — per [company-vetting.md](../../sp-inbound-vetting/reference/company-vetting.md) |
| Salesforce Lead/Case/Account SOQL | **Yes** — read-only |
| [queues.md routing table](../../sp-inbound-vetting/reference/queues.md) | **Yes** — reroute recommendation |
| SF Case/Lead Task | **No** — voicemail skill owns FD note + resolve |
| Freshdesk `cf_sp` / `sp-vetted` from inbound skill | **No** — set `cf_sp` on resolve when posture known (see below) |
| Outbound forward draft to AP Help | **No auto-send** — apply corrected **`route`** on FD forward |

## Recommended agent pipeline

```text
1. get_skill("sp-inbound-vetting", source: "vixxo")  [+ fallback paths above]
2. Dry-run batch (transcribe + keyword classify, no writes):
   python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py --dry-run
3. Read JSON under sp-voicemail-triage/.tmp/batch-run/batch-*.json
4. For each result with transcribed=yes and route != "—":
   a. Lite vet (Gateway + SF + routing table from sp-inbound-vetting)
   b. Merge route (see precedence below)
   c. Build internal note with company vetting table (not "vetting skipped")
5. Apply Freshdesk writes per ticket (MCP or approved live batch per ticket):
   internal note → forward (merged route) → resolve (cf_sp when Known SP)
```

Skip lite vet for no-forward branches (`foul-language`, `short-duration`,
`minimal-speech`) — keyword batch result is final.

## Route merge precedence

Apply top to bottom; first match wins.

| Priority | Rule | Forward target |
| --- | --- | --- |
| 1 | No-forward branch (foul / &lt;10s / minimal speech) | None — resolve only |
| 2 | **sp-inbound-vetting** routing: payment/AP/remittance/check/ACH dominates | `aphelp@vixxo.com` |
| 3 | **AP misroute guardrail** — sourcing/account manager/work opportunities in transcript | `service.providermanagement@vixxo.com` (not AP) |
| 4 | **sp-inbound-vetting** routing: COI/compliance primary ask | `COI@vixxo.com` |
| 5 | Onboarding + **Unknown / Not in systems** posture | `spm-recruitment@vixxo.com` |
| 6 | Onboarding + **Known SP** or **Prospect (SF Lead)** | Resolve on KSOnboarding — no recruitment forward unless caller says new entity |
| 7 | SR cited + Gateway/VixxoLink resolves SR | SR branch from parent [routing-actions.md](../../sp-voicemail-triage/reference/routing-actions.md) |
| 8 | Batch keyword `category` / `route` | Use batch route if no override above |

When lite vet **changes** the batch keyword route, add to the internal note:

```markdown
**Reroute:** Keyword route `{batch_route}` → `{merged_route}` (sp-inbound-vetting lite vet).
```

Use parent batch flag **`--reroute-spm`** only when correcting a known AP misroute to
SPM without a full agent vet pass.

## Internal note — vetting block

Replace the fast skill default "vetting skipped" block with the
**sp-inbound-vetting** vetting table and **Entity posture** from company vetting.
Include **Gateway SP** line and **Salesforce** matches. Keep voicemail-specific
fields (transcript, callback, category, urgency) from
[freshdesk-internal-note-template.md](../../sp-voicemail-triage/reference/freshdesk-internal-note-template.md).

## Resolve — cf_sp

| Posture | `cf_sp` on resolve |
| --- | --- |
| Known SP (Gateway match) | SP display name or `#` + number |
| Prospect / open SF Case | Company or Lead company |
| Unknown | `Unknown` |

## Document phase extension (dry-run)

To **plan** inbound vetting's document phase (SF Task drafts + full FD write plan)
without applying writes, use the agent extension:

[inbound-vetting-document-phase-dry-run.md](inbound-vetting-document-phase-dry-run.md)

Lite vet (this doc) remains read-only on SF. The document dry-run tier adds
**planned** Case/Lead Tasks and merged FD updates to the batch packet — live
apply requires explicit operator approval after review.

## When to use parent or full inbound skill instead

| Need | Skill |
| --- | --- |
| SF **Case create** when no dedupe Case | **`sp-voicemail-triage`** (parent) |
| SF Lead/Case Task **live** without dry-run gate | **`sp-voicemail-triage`** (parent) |
| SF queue Case vetting (non-voicemail) | **`sp-inbound-vetting`** full workflow |
| Outlook inbox voicemails | **`sp-voicemail-triage`** |
| Cron with no MCP / no agent | **`sp-voicemail-triage-fast`** shell batch only |

## Batch summary fields (agent runs)

Report after apply:

- `vetting_rerouted` — count where merged route ≠ batch route
- `vetting_rerouted_ids` — ticket ids
- Standard batch JSON: `processed`, `transcribed`, `transcription_failed`, `routed`, `closed`, `failed`
