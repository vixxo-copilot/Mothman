# Inbound vetting document phase — agent dry-run extension

Extends the **agent fast** path beyond lite vet ([inbound-vetting-reroute.md](inbound-vetting-reroute.md))
to include **`sp-inbound-vetting` Phase 2 — Document** in **dry-run only**. No Freshdesk
writes, no Salesforce Task posts, no forwards until {{employee_name}} approves a live apply.

Use this when you want **SF-platform documentation planned** (Tasks on matched Lead/Case)
alongside **Freshdesk resolve/forward** — without running the full parent
`sp-voicemail-triage` batch.

## Tiers (recap)

| Tier | Vet | Document | Writes |
| --- | --- | --- | --- |
| Shell cron | Keyword only | Skipped | FD (live) |
| Agent lite | `sp-inbound-vetting` read-only | FD only | FD (live) |
| **Agent + document dry-run** | Full inbound search + routing | **Planned SF + FD** | **None** |
| Agent + document live | Same | Same | FD + SF CLI (after approval) |
| Parent `sp-voicemail-triage` | Full parent vet | SF + FD | Live (default) |

## Prerequisites

Same as lite vet, plus:

| Requirement | Dry-run | Live apply |
| --- | --- | --- |
| Skills MCP `get_skill("sp-inbound-vetting")` | Required | Required |
| Gateway, VixxoLink, Salesforce, Freshdesk MCP | Required | Required |
| `sf` CLI authenticated | Optional (plan only) | Required for SF Tasks |
| Explicit user phrase | `"document phase dry-run"` / `"preview SF Tasks"` | `"apply document phase"` after review |

Load inbound references from the published skill or repo fallback:

- [company-vetting.md](../../sp-inbound-vetting/reference/company-vetting.md) — posture table
- [salesforce-notes.md](../../sp-inbound-vetting/reference/salesforce-notes.md) — Task bodies
- [freshdesk-note-template.md](../../sp-inbound-vetting/reference/freshdesk-note-template.md)
- Parent dedupe: [salesforce-notes.md](../../sp-voicemail-triage/reference/salesforce-notes.md)

## Pipeline

```text
1. get_skill("sp-inbound-vetting", source: "vixxo")
2. Dry-run batch (transcribe + keyword classify, no FD writes):
   python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py --dry-run
3. For each forwardable / resolve-on-KS item (skip no-forward branches):
   a. Lite vet — entity extraction, Gateway, VixxoLink, SF SOQL, routing table
   b. Merge route — [inbound-vetting-reroute.md](inbound-vetting-reroute.md)
   c. Document phase (DRY-RUN) — plan all writes below; emit packet; do NOT call write APIs
4. Write combined output:
   .agents/skills/sp-voicemail-triage/.tmp/batch-run/batch-*-document-dry-run.json
   plus per-ticket markdown packets in chat summary
5. Batch summary — counts: document_dry_run, sf_tasks_planned, fd_writes_planned, rerouted
```

Skip document planning for `foul-language`, `short-duration`, `minimal-speech` — keyword
result is final (note + resolve only).

## Document phase scope (from sp-inbound-vetting)

Apply the inbound **document checklist** in plan-only mode:

| Action | Voicemail fast path | Dry-run output |
| --- | --- | --- |
| Routing classified | Merged route from lite vet | `routing.stay_sf` / `recommend_ap_help` / `fd_forward:{target}` |
| Gateway + VixxoLink + SF search | Already in lite vet table | Copy into packet |
| **SF Case Task** | When dedupe Case **or** open ksonboarding Case matches | `sf.case_task: planned` + draft Subject/Description/WhatId |
| **SF Lead Task** | When posture requires Lead Task per [company-vetting.md](../../sp-inbound-vetting/reference/company-vetting.md) | `sf.lead_task: planned` + draft |
| **SF Case create** | **Do not plan** in this extension — use parent skill if no dedupe Case | `sf.case_create: N/A (use parent)` |
| **FD internal note** | Full vetting table + voicemail fields | `fd.internal_note: planned` + body |
| **FD cf_sp + tags** | GET ticket first; merge tags; posture tags | `fd.cf_sp`, `fd.tags` planned values |
| **FD forward** | Merged route recipients | `fd.forward: planned` (not sent) |
| **FD resolve** | After forward or KS resolve branch | `fd.resolve: planned` |
| **AP Help forward draft** | When routing table matches payment/AP | Text block only — **no auto-send** |

### SF dedupe (required before Case Task plan)

```sql
SELECT Id, CaseNumber, Subject, Status, Description
FROM Case
WHERE Description LIKE '%Freshdesk #{ticket_id}%'
   OR Subject LIKE '%Freshdesk #{ticket_id}%'
ORDER BY CreatedDate DESC
LIMIT 5
```

When a Case matches, plan **Task on that Case** (not Case create). Subject line:

`SP Inbound Vetting — FD #{ticket_id}`

When Lead matches and posture table requires Lead Task, plan **WhoId** Task with
voicemail transcript excerpt in Description.

### FD tag merge (plan only)

Mirror [troubleshooting.md](../../sp-inbound-vetting/reference/troubleshooting.md):

1. Plan `get_ticket` snapshot → existing `tags`, `cf_sp`
2. Plan merged tag set: existing + `sp-vetted` + posture tag (`known-sp`, `sf-lead-match`, `unknown-sp`, …)
3. If `cf_sp` conflict with human-set value → plan **tags-only** update; note conflict in packet

## Per-ticket dry-run packet

Emit one block per ticket (chat + JSON `document_plan`):

```markdown
## Voicemail + Inbound Document Dry-Run — FD #{ticket_id}

| Field | Value |
| --- | --- |
| **Batch route** | {keyword route} |
| **Merged route** | {after lite vet} |
| **Reroute** | {yes/no — batch → merged} |
| **Posture** | {Known SP / Prospect / Unknown / …} |
| **Gateway SP** | {SP # — name or No match} |
| **SF dedupe Case** | {CaseNumber or None} |
| **SF Lead** | {Lead Id or None} |

### Planned writes (not applied)

**SF Case Task:** planned | N/A
- WhatId: {CaseId}
- Subject: SP Inbound Vetting — FD #{ticket_id}
- Description: (draft — queue ksonboarding, posture, SP #, routing, transcript excerpt)

**SF Lead Task:** planned | N/A
- WhoId: {LeadId}
- Description: (draft)

**Freshdesk internal note:** planned
(body — vetting table + transcript + callback)

**Freshdesk update:** planned
- cf_sp: {value}
- tags: {merged list}
- forward: {recipients or none}
- resolve: closed | open

**Recommended AP forward (draft only):** {none | aphelp@vixxo.com — …}

### Status
document_dry_run — awaiting operator approval for live apply
```

## JSON envelope (optional merge file)

Append to dry-run batch output or save sibling file:

```json
{
  "mode": "document_dry_run",
  "source_batch": ".agents/skills/sp-voicemail-triage/.tmp/batch-run/batch-20260626T120000Z.json",
  "tickets": [
    {
      "ticket_id": 58752,
      "merged_route": "service.providermanagement@vixxo.com",
      "vetting_rerouted": true,
      "posture": "Known SP",
      "sf": {
        "case_task": { "status": "planned", "what_id": "500…", "subject": "…", "description": "…" },
        "lead_task": { "status": "N/A" }
      },
      "freshdesk": {
        "internal_note": { "status": "planned", "body": "…" },
        "cf_sp": "KS101347 - KS - LockPro LLC",
        "tags": ["sp-vetted", "known-sp", "…"],
        "forward": { "status": "planned", "to": ["service.providermanagement@vixxo.com"] },
        "resolve": { "status": "planned", "status_code": 5 }
      }
    }
  ],
  "summary": {
    "document_dry_run": 12,
    "sf_tasks_planned": 8,
    "fd_writes_planned": 12,
    "vetting_rerouted": 3
  }
}
```

## Live apply (after approval only)

Only when {{employee_name}} explicitly approves (`apply document phase`, `go live`, etc.):

1. **SF Tasks** — `sf data create record` per [salesforce-notes.md](../../sp-inbound-vetting/reference/salesforce-notes.md)
2. **Freshdesk** — internal note → forward (if any) → resolve with `cf_sp`/tags per plan
3. Record failures in batch summary; partial apply is allowed (SF failed, FD succeeded → mark partial)

Do **not** auto-apply from cron or automation prompts.

## Agent prompt (document dry-run)

```markdown
Run SP voicemail fast batch with inbound vetting **document phase dry-run**:

1. get_skill("sp-inbound-vetting", source: "vixxo") on project-0-assistant-CGagner-skills
2. python .agents/skills/sp-voicemail-triage-fast/scripts/batch_process_freshdesk.py --dry-run
3. Lite-vet + merge routes per reference/inbound-vetting-reroute.md
4. Plan full document phase per reference/inbound-vetting-document-phase-dry-run.md
   — SF Task drafts, FD note/cf_sp/tags/forward/resolve — NO writes
5. Save document-dry-run JSON under sp-voicemail-triage/.tmp/batch-run/
6. Report summary: document_dry_run, sf_tasks_planned, fd_writes_planned, vetting_rerouted

Enable Gateway, VixxoLink, Salesforce, and Freshdesk MCPs.
```

## When to use parent instead

| Need | Skill |
| --- | --- |
| SF **Case create** when no dedupe match | `sp-voicemail-triage` |
| Live run without a separate approval step | Parent or lite agent path |
| Outlook inbox voicemails | `sp-voicemail-triage` |
| Non-voicemail SF queue Cases | `sp-inbound-vetting` full workflow |
