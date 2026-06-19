---
name: ksonboarding-inbound-routing
description: >-
  Reviews inbound email to ksonboarding@vixxo.com in the Freshdesk KSOnboarding
  queue, vets SP identity via Gateway/VixxoLink/Salesforce, and reclassifies
  misrouted mail by changing Freshdesk type — COIs when a COI is present,
  VixxoLink Support for portal assistance, Invoice Support for past-due invoice
  status or account statements. Leaves cf_sp blank when SP name is uncertain
  after vetting. Use when the user asks to route ksonboarding mail, classify
  KS Onboarding intake, retype ksonboarding tickets, or triage non-voicemail
  ksonboarding email. For voicemails use sp-voicemail-triage. For SP enrichment
  without type changes use sp-inbound-vetting.
---

# KS Onboarding Inbound Routing

Work-only workflow that **reviews inbound email** to `ksonboarding@vixxo.com`,
**vets service-provider identity**, and **reclassifies Freshdesk ticket type**
when the message belongs in a specialist queue.

This skill **routes by type change only**. It does **not** forward mail, send
public replies, close tickets, or resolve items unless {{employee_name}}
explicitly asks.

## When to use

- "Route ksonboarding mail" / "classify KS Onboarding intake"
- "Retype ksonboarding tickets" / "triage ksonboarding email"
- "Review inbound ksonboarding" (non-voicemail)
- Batch: "route all open ksonboarding email"
- Single ticket: "route Freshdesk #51234" (KSOnboarding queue)

**Use `sp-voicemail-triage`** for subject `New voicemail` items.

**Use `sp-inbound-vetting`** when the goal is SP enrichment (cf_sp, Salesforce
Tasks) **without** changing ticket type.

**Use `vixxo-coi-review`** after a ticket is retyped to `COIs`.

**Use `vixxo-spm-invoice-concerns`** or **`vixxo-freshdesk-invoice-review`**
after a ticket is retyped to `Invoice Support`.

## Operating modes

| Mode | Trigger | Behavior |
| --- | --- | --- |
| **Batch (default)** | No single item named | Pull all in-scope Open KSOnboarding email tickets |
| **Single** | Ticket id, URL, or one message | Full pipeline on one item |
| **Dry-run (opt-in)** | User says "dry-run" / "preview only" | Classify + vet only; no writes |

**Untouched** = ticket is Open, type `KSOnboarding`, and **not** tagged
`ks-inbound-routed` (unless `re-route`).

**Phase 1 — Classify + vet (automatic):** intake, entity extraction, content
classification, Gateway + Salesforce search.

**Phase 2 — Route (automatic):** Freshdesk internal note → type change (+ tags,
optional cf_sp). No separate approval step for these internal writes —
{{employee_name}} pre-authorizes routing for this skill. Opt out only with
explicit **dry-run**.

**Write order (every item):** internal note → type + tags (+ cf_sp when certain).

## Intake

Follow [reference/intake.md](reference/intake.md).

**In scope (batch default):**

```
group_id:159000485013 AND status:2 AND type:'KSOnboarding'
```

Then **exclude voicemails** — subject must **not** include `New voicemail`
(case-insensitive). See
[../sp-voicemail-triage/reference/freshdesk-voicemail-filter.md](../sp-voicemail-triage/reference/freshdesk-voicemail-filter.md).

**Out of scope (default):** tickets tagged `ks-inbound-routed` (unless
`re-route`); voicemail subjects; tickets already retyped away from
`KSOnboarding`.

## Classification rules

Follow [reference/classification.md](reference/classification.md).

Evaluate **top to bottom**; first match wins:

| Priority | Signal | New Freshdesk `type` |
| --- | --- | --- |
| 1 | Inbound email **contains a COI** | `COIs` |
| 2 | Inbound email **requests assistance with the portal** | `VixxoLink Support` |
| 3 | Inbound email **requests status for past-due invoices**, or **contains a statement** | `Invoice Support` |
| 4 | No match above | **Leave** `KSOnboarding` — document only |

**COI** includes ACORD 25 attachments, insurance certificate PDFs/images, or
body text referencing certificate of insurance / COI / additional insured /
ACORD.

**Portal assistance** means VixxoLink / SP portal access — login, password,
mobile app, dispatch board, accepting work. **Exclude** client/customer portal
asks (flag in note; do not retype).

**Invoice / statement** includes past-due, overdue, aging, account statement,
statement of account, outstanding balance lists, unpaid invoice status asks, or
attachments whose filename/content indicates a statement.

When **no retype applies**, still post the routing note and tag
`ks-inbound-routed` with sub-tag `ks-onboarding-retained`.

## SP name field (`cf_sp`)

After completing vetting ([reference/company-vetting.md](reference/company-vetting.md)):

| Vetting outcome | `cf_sp` action |
| --- | --- |
| **Known SP** — exact email, KS/SR anchor, or fuzzy match ≥ 0.75 with **High** confidence | Set `{SP_NUMBER} - {Gateway display name}` |
| **Possible** (Medium/Low confidence, fuzzy alternates, or SF-only match) | **Leave blank** — do not set `Unknown` |
| **Unknown / no match** | **Leave blank** |

**Never overwrite** an existing human-set `cf_sp` without user confirmation.
When setting `cf_sp`, include it in the same `tickets_manage update` as the
type change.

## Type-change payloads

Freshdesk allowed types include: `Account Update`, `Invoice Support`,
`VixxoLink Support`, `Credit/Debit Submission`, `NTE`, `Capital Project`,
`SWS`, `COIs`, `No Action Required`, `KSOnboarding`.

Merge tags with existing tags; Freshdesk **replaces** the full tag array on
update — always include prior tags plus new ones.

### COI → `COIs`

```json
{
  "ticket_id": "<id>",
  "ticket": {
    "type": "COIs",
    "tags": ["<existing tags>", "ks-inbound-routed", "coi", "risk-compliance-routed"],
    "custom_fields": {
      "cf_sp": "<only when Known SP — otherwise omit cf_sp key>"
    }
  }
}
```

Clear stale `cf_vixxo_link_type_of_request` if present (set `null` when API
accepts it).

### Portal → `VixxoLink Support`

```json
{
  "ticket_id": "<id>",
  "ticket": {
    "type": "VixxoLink Support",
    "tags": ["<existing tags>", "ks-inbound-routed", "vixxolink-routed"],
    "custom_fields": {
      "cf_sp": "<only when Known SP — otherwise omit cf_sp key>"
    }
  }
}
```

### Past-due invoice / statement → `Invoice Support`

```json
{
  "ticket_id": "<id>",
  "ticket": {
    "type": "Invoice Support",
    "tags": ["<existing tags>", "ks-inbound-routed", "invoice-routed"],
    "custom_fields": {
      "cf_type_of_request": "Follow up on an Unpaid Invoice",
      "cf_sp": "<only when Known SP — otherwise omit cf_sp key>"
    }
  }
}
```

`cf_type_of_request` has only three valid values; use **`Follow up on an
Unpaid Invoice`** for past-due status and statement mail.

### No retype (true onboarding)

Post internal note only; add tags `ks-inbound-routed`, `ks-onboarding-retained`.
Do **not** change `type`.

## Output format

### Batch summary (top of every batch run)

See [reference/examples.md](reference/examples.md).

### Routing packet (per item)

```markdown
## KS Onboarding Routing — FD #{id}

| Field | Value |
| --- | --- |
| **Subject** | {subject} |
| **Requester** | {name} <{email}> |
| **Classification** | COI / VixxoLink Support / Invoice Support / KSOnboarding (retained) |
| **Signals** | {bullets — attachment names, keywords matched} |
| **Entity posture** | {from vetting} |
| **Gateway SP** | {SP # — name or No match} |
| **Salesforce** | {Lead / Case ids or None} |
| **cf_sp** | {value set | left blank — reason} |
| **Type change** | KSOnboarding → {new type | none} |

### Vetting summary
{table from company-vetting.md}

### Actions taken
- **Internal note:** {posted | failed + reason}
- **Type + tags:** {updated | skipped — retained KSOnboarding}
- **cf_sp:** {set | left blank | skipped — existing value}
```

## Workflow (per item)

1. **Acquire content** — `get_ticket`, conversations, attachment metadata.
2. **Extract entities** — company, SP #, SR, contact email/phone (reuse
   [../sp-inbound-vetting/reference/intake.md](../sp-inbound-vetting/reference/intake.md)
   entity extraction).
3. **Classify** — [reference/classification.md](reference/classification.md).
4. **Company vetting** — [reference/company-vetting.md](reference/company-vetting.md)
   (Gateway email/name/company, VixxoLink SR cross-check, Salesforce Lead/Case).
5. **Post Freshdesk internal note** —
   [reference/freshdesk-note-template.md](reference/freshdesk-note-template.md).
6. **Update ticket** — apply type-change payload when classification requires
   retype; set `cf_sp` only on Known SP / High confidence; tag
   `ks-inbound-routed`.
7. **Verify** — direct `get_ticket` after write; search results may lag.

## Batch scripts

| Command | Purpose |
| --- | --- |
| `python scripts/dry_run_batch.py` | Classify + vet all in-scope KSOnboarding email; no writes |
| `python scripts/dry_run_batch.py --skip-vetting` | Fast classification-only preview (no Gateway/SF) |
| `python scripts/live_run_batch.py` | Dry-run then post notes + retype tickets |
| `python scripts/live_run_batch.py --dry-run-json .tmp/dry-run-latest.json` | Apply a saved dry-run |

Output JSON: `.tmp/dry-run-{timestamp}.json` and `.tmp/dry-run-latest.json`;
live runs under `.tmp/live-run/`.

## Guardrails

- Work context only — Vixxo SP operations.
- Facts from ticket content and MCP responses; mark assumptions.
- **No outbound email** — no `forward_ticket`, public replies, or M365 send
  unless {{employee_name}} explicitly directs it.
- **No ticket close / resolve** from this skill by default.
- Never invent SP numbers or Salesforce ids.
- **`cf_sp` blank when uncertain** — do not populate `Unknown` or a guessed
  company name.
- If classification is ambiguous between two buckets, pick the **higher
  priority** rule only when signals are strong; otherwise retain `KSOnboarding`
  and document ambiguity in the internal note.
- **Operator exclusions:** tickets listed in `scripts/exclusions.py` are never
  retyped (currently **#56976**, **#51923** — leave in KSOnboarding).
- Redact full phone numbers in chat summaries.

## Additional resources

| File | Purpose |
| --- | --- |
| [reference/intake.md](reference/intake.md) | Queue pull + exclusions |
| [reference/classification.md](reference/classification.md) | Retype rules + signals |
| [reference/company-vetting.md](reference/company-vetting.md) | Gateway + SF search |
| [reference/freshdesk-note-template.md](reference/freshdesk-note-template.md) | Internal note body |
| [reference/examples.md](reference/examples.md) | Sample outputs |

Sibling skills: **`sp-voicemail-triage`** (voicemail routing),
**`sp-inbound-vetting`** (SP enrichment without type change),
**`vixxo-coi-review`** (COI compliance review after retype),
**`vixxo-spm-invoice-concerns`** (invoice concern resolution).
