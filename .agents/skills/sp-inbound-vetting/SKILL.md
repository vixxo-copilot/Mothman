---
name: sp-inbound-vetting
description: >-
  Vets inbound items received at aphelp@vixxo.com and ksonboarding@vixxo.com
  by searching Gateway for existing service providers and Salesforce for Leads
  and Cases. Posts Freshdesk internal notes, updates the ticket SP name/number
  field when a match is found, and adds Salesforce Task notes on matched Leads
  or Cases. Use when the user asks to vet AP Help or KS Onboarding intake,
  confirm whether an SP already exists, enrich Freshdesk with SP # and name, or
  document inbound mail against Gateway and Salesforce. For voicemail-only
  KSOnboarding queue work use sp-voicemail-triage. For AP invoice classification
  and replies use vixxo-freshdesk-invoice-review.
---

# SP Inbound Vetting (AP Help + KS Onboarding)

Work-only workflow that **vets service-provider identity** on inbound mail
received at **`aphelp@vixxo.com`** and **`ksonboarding@vixxo.com`**. For each
item the skill searches **Gateway** (Siebel SP) and **Salesforce** (Lead /
Case), then **documents findings** in Freshdesk and Salesforce.

This skill **enriches and annotates** tickets. It does **not** classify
invoices, draft provider replies, forward mail, or change ticket status unless
{{employee_name}} explicitly asks.

## When to use

- "Vet AP Help intake" / "vet ksonboarding tickets"
- "Check if this SP already exists" on an aphelp or ksonboarding item
- "Enrich Freshdesk with SP number and name" for inbound SPM mail
- Batch: "vet all open aphelp and ksonboarding items"
- Single ticket: "vet Freshdesk #51234"

**Use `sp-voicemail-triage`** for subject `New voicemail` items.

**Use `vixxo-freshdesk-invoice-review`** for AP invoice triage, bucket
classification, and provider reply drafting — that skill **excludes**
ksonboarding recipient tickets; this skill **owns** them.

## Operating modes

| Mode | Trigger | Behavior |
| --- | --- | --- |
| **Batch (default)** | No single item named | Pull all in-scope Open Freshdesk tickets |
| **Single** | Ticket id, URL, or one message | Full pipeline on one item |
| **Dry-run (opt-in)** | User says "dry-run" / "preview only" | Vetting + packet only; no writes |

**Phase 1 — Vet (automatic):** intake, entity extraction, Gateway + Salesforce
search.

**Phase 2 — Document (automatic):** Freshdesk internal note → Freshdesk field
update → Salesforce Task notes. No separate approval step for these internal
writes — {{employee_name}} pre-authorizes enrichment for this skill. Opt out
only with explicit **dry-run**.

**Write order (every item):** internal note → `cf_sp` + tags → Salesforce Lead
Task → Salesforce Case Task.

## Intake

Follow [reference/intake.md](reference/intake.md).

**In scope:** Freshdesk Open SPM tickets (`group_id:159000485013`, `status:2`)
whose recipient is `aphelp@vixxo.com` or `ksonboarding@vixxo.com`.

**Out of scope (default):** tickets tagged `sp-vetted` (unless `re-vet`);
subject includes `New voicemail` (unless user says include voicemails).

## Output format

### Batch summary (top of every batch run)

See [reference/examples.md](reference/examples.md).

### Vetting packet (per item)

```markdown
## SP Inbound Vetting — {Freshdesk # or mail subject}

| Field | Value |
| --- | --- |
| **Source** | Freshdesk #{id} / Outlook {message id} |
| **Inbox** | aphelp / ksonboarding |
| **Requester** | {name} <{email}> |
| **Company** | {extracted or Not stated} |
| **Reference IDs** | {SP # / SR / invoice / none} |
| **Entity posture** | {from company vetting} |
| **Gateway SP** | {SP # — name or No match} |
| **Salesforce** | {Lead / Case / Account ids or None} |
| **cf_sp target** | {value} |
| **Confidence** | High / Medium / Low |

### Company vetting
{table from reference/company-vetting.md}

### Summary / open questions
…

### Actions taken
- **Internal note:** {posted | failed + reason}
- **cf_sp + tags:** {updated | skipped + reason}
- **SF Lead Task:** {Id + posted | N/A | failed}
- **SF Case Task:** {Id + posted | N/A | failed}
```

## Workflow (per item)

1. **Acquire content** — `get_ticket`, conversations, requester; optional
   Outlook `get-mail-message` when no ticket.
2. **Extract entities** — company, SP #, SR, contact email/phone
   ([intake.md](reference/intake.md)).
3. **Company vetting** — [reference/company-vetting.md](reference/company-vetting.md):
   - Gateway: `gateway_swm_list_providers`, `gateway_swm_get_provider`,
     `gateway_get_service_request` when SR cited.
   - Salesforce: Lead, Case, Account SOQL ([company-vetting.md](reference/company-vetting.md)).
4. **Post Freshdesk internal note** —
   [reference/freshdesk-note-template.md](reference/freshdesk-note-template.md)
   via `create_ticket_note` (`"private": true`).
5. **Update Freshdesk ticket fields** when posture is known or a company string
   was extracted:

```json
{
  "ticket_id": "<id>",
  "ticket": {
    "custom_fields": {
      "cf_sp": "<SP# - Gateway display name | Lead company | Unknown>"
    },
    "tags": ["sp-vetted", "<known-sp|sf-lead-match|sf-case-match|unknown-sp>"]
  }
}
```

**`cf_sp` formatting rules:**

| Match | Value |
| --- | --- |
| Known SP | `{SP_NUMBER} - {Gateway display name}` (example: `1044555 - KS - Apex HVAC LLC`) |
| SF Lead only | Lead `Company` field or best extracted company name |
| Unknown | `Unknown` — only when field is empty; do not overwrite a human-set value |

Merge tags with existing tags; do not remove unrelated tags.

**Do not** set `status`, `type`, or other custom fields unless {{employee_name}}
explicitly asks — invoice-review and COI skills own those transitions.

6. **Salesforce notes** — [reference/salesforce-notes.md](reference/salesforce-notes.md):
   - Task on matched **Lead** (ksonboarding items: always attempt when Lead found).
   - Task on matched **Case** when Case search hits.
7. **Record failures** in the batch summary **Status** column; continue the
   pipeline where safe.

## Document checklist (automatic)

```
Vetting progress — {ticket id}:
- [ ] Gateway SP search complete
- [ ] Salesforce Lead search complete
- [ ] Salesforce Case search complete
- [ ] Internal note posted
- [ ] cf_sp + sp-vetted tag updated
- [ ] SF Lead Task posted (if Lead found)
- [ ] SF Case Task posted (if Case found)
```

## Guardrails

- Work context only — Vixxo SP operations.
- Facts from ticket content and MCP responses; mark assumptions.
- **No outbound email** — no `forward_ticket`, `forward-mail-message`, or
  public Freshdesk replies unless {{employee_name}} explicitly directs it.
- **No ticket close / resolve** from this skill by default.
- Never invent SP numbers or Salesforce ids — use Gateway/SOQL results only.
- If `cf_sp` already has a value that conflicts with vetting, note the conflict
  in the internal note and **do not overwrite** without user confirmation.
- Redact full phone numbers in chat summaries; keep full numbers in internal
  notes for operators.

## Additional resources

| File | Purpose |
| --- | --- |
| [reference/intake.md](reference/intake.md) | Queue pull + entity extraction |
| [reference/company-vetting.md](reference/company-vetting.md) | Gateway + Salesforce search |
| [reference/freshdesk-note-template.md](reference/freshdesk-note-template.md) | Internal note body |
| [reference/salesforce-notes.md](reference/salesforce-notes.md) | Task / Chatter writes |
| [reference/examples.md](reference/examples.md) | Sample outputs |

Sibling skills: **`sp-voicemail-triage`** (voicemail routing),
**`vixxo-freshdesk-invoice-review`** (AP invoice triage — excludes ksonboarding).
