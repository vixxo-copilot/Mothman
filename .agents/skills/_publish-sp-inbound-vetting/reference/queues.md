# Queues — SP Inbound Vetting

Batch intake pulls **open, untouched** items from the queues below.

**Untouched (Salesforce):** Case/Lead in queue without a completed vetting Task
from this skill (subject contains `SP Inbound Vetting`) and no operator-applied
`sp-vetted` tag equivalent on linked Freshdesk mirror (if any).

**Untouched (Freshdesk — AP Help):** ticket is Open and **not** tagged
`sp-vetted` (unless `re-vet`).

## Architecture

| Queue key | Primary system | Mailbox / queue name | Identity vetting | Documentation |
| --- | --- | --- | --- | --- |
| `ksonboarding` | **Salesforce** | ksonboarding queue | Gateway + VixxoLink + SF | SF Case/Lead Task |
| `coi` | **Salesforce** | COI queue | Gateway + VixxoLink + SF | SF Case Task |
| `spm` | **Salesforce** | service.providermanagement queue | Gateway + VixxoLink + SF | SF Case Task |
| `aphelp` | **Freshdesk** | `aphelp@vixxo.com` | Gateway + VixxoLink + SF | FD internal note + `cf_sp` + SF Tasks |

Gateway and VixxoLink are used on **all** queues for SP number / SR / email /
company resolution. Salesforce is the **system of record** for the three
SF-pivot queues.

---

## Salesforce queue registry

> **Open question:** Queue `DeveloperName` values and 15/18-char Queue Ids are
> not yet confirmed in this repo. Run the discovery SOQL below once per org and
> paste results into the **Confirmed ids** subsection when known.

| Queue key | SF list view / queue label (expected) | DeveloperName (placeholder) | Email alias (context) |
| --- | --- | --- | --- |
| `ksonboarding` | KS Onboarding | `ksonboarding` _(TBD)_ | `ksonboarding@vixxo.com` |
| `coi` | COI | `COI` or `coi` _(TBD)_ | `COI@vixxo.com` |
| `spm` | Service Provider Management | `service_providermanagement` or similar _(TBD)_ | `service.providermanagement@vixxo.com` |

### Queue discovery (operator — run once)

```sql
SELECT Id, Name, DeveloperName, Email
FROM Group
WHERE Type = 'Queue'
  AND (DeveloperName LIKE '%ksonboarding%'
    OR DeveloperName LIKE '%coi%'
    OR DeveloperName LIKE '%providermanagement%'
    OR Name LIKE '%Onboarding%'
    OR Name LIKE '%COI%'
    OR Name LIKE '%Provider Management%')
ORDER BY Name
```

Record results:

| Queue key | Queue Id | DeveloperName | Confirmed by |
| --- | --- | --- | --- |
| `ksonboarding` | _TBD_ | _TBD_ | |
| `coi` | _TBD_ | _TBD_ | |
| `spm` | _TBD_ | _TBD_ | |

### Case pull SOQL (per queue)

Replace `{QUEUE_ID}` with the Id from discovery.

```sql
SELECT Id, CaseNumber, Subject, Status, OwnerId, ContactEmail,
       ContactId, AccountId, Description, CreatedDate, SuppliedEmail
FROM Case
WHERE OwnerId = '{QUEUE_ID}'
  AND IsClosed = false
ORDER BY CreatedDate ASC
LIMIT 200
```

**ksonboarding — Lead pull (when onboarding Cases link to Leads):**

```sql
SELECT Id, Name, Company, Status, Email, Phone, LastModifiedDate
FROM Lead
WHERE OwnerId = '{QUEUE_ID}'
  AND IsConverted = false
ORDER BY LastModifiedDate DESC
LIMIT 200
```

Adjust `OwnerId` filter if your org routes ksonboarding via a RecordType or
custom queue-assignment field — document the org-specific filter when confirmed.

### SF batch selection rules

1. Run queue discovery if ids are not cached.
2. Pull open Cases (and Leads for `ksonboarding` when applicable).
3. **Skip** Cases already vetted (Task subject `SP Inbound Vetting — Case …`
   exists, or user says `re-vet`).
4. **Order:** oldest-first by `CreatedDate` unless user asks newest-first.
5. **Dedupe:** when running `all`, merge by Case Id before processing.

---

## Freshdesk queue — AP Help only

| Queue key | Freshdesk view | Search filter | Inbox label |
| --- | --- | --- | --- |
| `aphelp` | AP Help (mailbox gate) | `group_id:159000485013 AND status:2` + recipient `aphelp@vixxo.com` | `aphelp@vixxo.com` |

Apply the recipient gate from [intake.md](intake.md).

### Legacy Freshdesk pulls (transition)

Batch scripts still support Freshdesk filters for `ksonboarding` and
`invoice-concerns`. **Prefer Salesforce SOQL** for ksonboarding vetting.
Invoice Concerns identity + resolution is owned by sibling skills — see below.

| Legacy key | Freshdesk filter | Status |
| --- | --- | --- |
| `ksonboarding` (FD) | `group_id:159000485013 AND status:2 AND type:'KSOnboarding'` | Legacy — use SF `ksonboarding` |
| `invoice-concerns` | `group_id:159000485013 AND status:2 AND type:'Invoice Support'` | Sibling skill territory |

---

## Routing table — SF queues vs AP Help

Apply **after** reading Case/ticket subject and body. When signals conflict,
prefer the **dominant operational ask** (payment/AP → AP Help; COI/onboarding/SPM
→ stay in SF).

| Signals (subject/body keywords) | Queue context | Vetting path | Recommended routing |
| --- | --- | --- | --- |
| COI, certificate of insurance, ACORD, additional insured, compliance hold | `coi`, `ksonboarding`, `spm` | Complete SF vetting + Gateway SP lookup | **Stay in SF queue** — sibling `vixxo-coi-review` for certificate fields |
| Onboarding, coverage area, enrollment, W-9, activation, rate card, new provider | `ksonboarding` | SF Lead/Case Task + Gateway | **Stay in SF queue** |
| Sourcing, account team, VixxoLink support, trade support, program manager callback | `spm`, `ksonboarding` | SF Case Task + Gateway | **Stay in SF queue** |
| Payment status, remittance advice, check number, ACH, wire, "when will I be paid" | Any SF queue | Vet SP identity in SF first | **Recommend forward to `aphelp@vixxo.com`** — draft only |
| Invoice dispute, AP hold, billing correction, duplicate payment, 1099 | Any SF queue | Vet SP identity in SF first | **Recommend forward to `aphelp@vixxo.com`** — draft only |
| Invoice # + payment question (no COI/onboarding primary ask) | `ksonboarding`, `spm` | SF Task noting SP match | **Recommend forward to AP Help** |
| Mixed COI + payment question | `coi`, `ksonboarding` | SF vetting for identity; split asks in Task | **Stay for COI**; **recommend AP Help forward** for payment portion |

### Forward recommendation format (no auto-send)

When routing table points to AP Help, add to the SF Case Task (and chat summary):

```markdown
**Recommended routing (requires operator approval):**
Forward payment/AP portion to aphelp@vixxo.com (Freshdesk AP Help).
Draft forward — do not send until {{employee_name}} approves.
Include: SP # (if known), invoice/payment refs, requester email, SF Case link.
```

Do **not** call `forward_ticket`, email forward APIs, or Case email actions
unless {{employee_name}} explicitly approves.

---

## Sibling skill boundaries

| Skill | Owns |
| --- | --- |
| **`sp-inbound-vetting`** (this skill) | Gateway SP + Salesforce identity lookup; SF Tasks (SF queues); FD note + `cf_sp` (AP Help); routing recommendations |
| **`vixxo-coi-review`** | COI certificate field compliance after identity vet |
| **`vixxo-spm-invoice-concerns`** | Invoice/payment Gateway analysis; Freshdesk Invoice Concerns resolution |
| **`vixxo-freshdesk-invoice-review`** | AP Help Desk No Agent queue; bucket classification; provider reply drafting |
| **`sp-voicemail-triage`** | `New voicemail` KSOnboarding items |

This skill does **not** classify invoices, draft provider replies, auto-forward
mail, or change Case/ticket status unless the user explicitly requests it.

---

## Script entry points

**Freshdesk (AP Help):**

```bash
python .agents/skills/sp-inbound-vetting/scripts/dry_run_batch.py --queue aphelp
python .agents/skills/sp-inbound-vetting/scripts/live_run_batch.py --queue aphelp
```

**Salesforce queues (`ksonboarding`, `coi`, `spm`):**

Use Salesforce MCP `run_soql_query` with the SOQL above, then run the per-item
workflow from [SKILL.md](../SKILL.md). Batch shell scripts for SF queues are
**not yet implemented** — track as future enhancement.

Legacy: `dry_run_ksonboarding*.py` and `live_run_ksonboarding.py` target
Freshdesk `--queue ksonboarding` during transition.
