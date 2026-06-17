---
name: sp-inbound-vetting
description: >-
  Vets inbound Freshdesk items for aphelp@vixxo.com, ksonboarding@vixxo.com,
  and the SPM - Invoice Concerns folder by searching Gateway for existing
  service providers and Salesforce for Leads and Cases. Posts Freshdesk internal
  notes, updates the ticket SP name/number field when a match is found, and
  adds Salesforce Task notes on matched Leads or Cases. Use when the user asks
  to vet AP Help, KS Onboarding, or SPM Invoice Concerns intake, confirm whether
  an SP already exists, enrich Freshdesk with SP # and name, or document inbound
  mail against Gateway and Salesforce. For voicemail-only KSOnboarding queue
  work use sp-voicemail-triage. For invoice resolution and provider replies use
  vixxo-spm-invoice-concerns or vixxo-freshdesk-invoice-review.
---

# SP Inbound Vetting (AP Help + KS Onboarding + SPM Invoice Concerns)

Work-only workflow that **vets service-provider identity** on inbound SPM
mail and tickets. For each item the skill searches **Gateway** (Siebel SP) and
**Salesforce** (Lead / Case), then **documents findings** in Freshdesk and
Salesforce.

**Intake surfaces:**

| Surface | Scope |
| --- | --- |
| `aphelp@vixxo.com` | Open SPM tickets sent to AP Help |
| `ksonboarding@vixxo.com` | KS Onboarding queue (`type:'KSOnboarding'`) |
| **SPM - Invoice Concerns** | Open `Invoice Support` tickets in the Freshdesk folder of that name |

This skill **enriches and annotates** tickets. It does **not** classify
invoices, draft provider replies, forward mail, or change ticket status unless
{{employee_name}} explicitly asks.

## When to use

- "Vet AP Help intake" / "vet ksonboarding tickets"
- "Vet SPM Invoice Concerns" / "vet open invoice concern tickets"
- "Vet untouched items in SPM - Invoice Concerns"
- "Check if this SP already exists" on an aphelp, ksonboarding, or invoice-concerns item
- "Enrich Freshdesk with SP number and name" for inbound SPM mail
- Batch: "vet all open aphelp, ksonboarding, and invoice concerns items"
- Single ticket: "vet Freshdesk #51234"

**Use `sp-voicemail-triage`** for subject `New voicemail` items.

**Use `vixxo-spm-invoice-concerns`** for invoice/payment Gateway analysis,
proposed resolutions, and invoice workflow tags (`spm-invoice-concerns-reviewed`).
That skill does **not** replace SP identity vetting — run this skill on Invoice
Concerns items until they carry `sp-vetted`.

**Use `vixxo-freshdesk-invoice-review`** for AP Help Desk No Agent queue,
bucket classification, and provider reply drafting.

## Operating modes

| Mode | Trigger | Behavior |
| --- | --- | --- |
| **Batch (default)** | No single item named | Pull all in-scope Open, untouched Freshdesk tickets |
| **Single** | Ticket id, URL, or one message | Full pipeline on one item |
| **Dry-run (opt-in)** | User says "dry-run" / "preview only" | Vetting + packet only; no writes |

**Untouched** = ticket is Open and **not** tagged `sp-vetted` (unless `re-vet`).

**Phase 1 — Vet (automatic):** intake, entity extraction, Gateway + Salesforce
search.

**Phase 2 — Document (automatic):** Freshdesk internal note → Freshdesk field
update → Salesforce Task notes. No separate approval step for these internal
writes — {{employee_name}} pre-authorizes enrichment for this skill. Opt out
only with explicit **dry-run**.

**Write order (every item):** internal note → `cf_sp` + tags → Salesforce Lead
Task → Salesforce Case Task.

## Intake

Follow [reference/intake.md](reference/intake.md) and
[reference/queues.md](reference/queues.md).

**In scope (batch default — `all`):**

1. Open SPM tickets (`group_id:159000485013`, `status:2`) sent to
   `aphelp@vixxo.com` or `ksonboarding@vixxo.com` (recipient gate).
2. Open tickets in the Freshdesk folder **SPM - Invoice Concerns** — filter:
   `group_id:159000485013 AND status:2 AND type:'Invoice Support'`.
3. KS Onboarding queue:
   `group_id:159000485013 AND status:2 AND type:'KSOnboarding'`.

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
| **Inbox / queue** | aphelp / ksonboarding / spm-invoice-concerns |
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
   - Gateway: `gateway_search_invoices` (by `serviceProviderNumber` or
     `searchString`), `gateway_get_service_request` when SR cited.
   - Salesforce: Lead, Case, Account SOQL.
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

Merge tags with existing tags; do not remove unrelated tags (including
`spm-invoice-concerns-reviewed` from sibling skills).

**Do not** set `status`, `type`, or other custom fields unless {{employee_name}}
explicitly asks — invoice-review and COI skills own those transitions.

6. **Salesforce notes** — [reference/salesforce-notes.md](reference/salesforce-notes.md):
   - Task on matched **Lead** when Lead found.
   - Task on matched **Case** when Case search hits.
7. **Record failures** in the batch summary **Status** column; continue the
   pipeline where safe.

## Batch scripts

| Command | Purpose |
| --- | --- |
| `python scripts/dry_run_batch.py --queue invoice-concerns` | Preview Invoice Concerns vetting |
| `python scripts/live_run_batch.py --queue invoice-concerns` | Live vet + write Invoice Concerns |
| `python scripts/live_run_batch.py --queue all` | All three intake surfaces |

See [reference/queues.md](reference/queues.md) for queue keys and filters.

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
| [reference/queues.md](reference/queues.md) | Queue filters incl. SPM Invoice Concerns |
| [reference/company-vetting.md](reference/company-vetting.md) | Gateway + Salesforce search |
| [reference/freshdesk-note-template.md](reference/freshdesk-note-template.md) | Internal note body |
| [reference/salesforce-notes.md](reference/salesforce-notes.md) | Task / Chatter writes |
| [reference/examples.md](reference/examples.md) | Sample outputs |

Sibling skills: **`sp-voicemail-triage`** (voicemail routing),
**`vixxo-spm-invoice-concerns`** (invoice concern resolution — complements this skill),
**`vixxo-freshdesk-invoice-review`** (AP Help Desk invoice triage).
