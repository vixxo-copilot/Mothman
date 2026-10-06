# Company Vetting

Run after extracting **Company** from the transcript (or ticket requester name when
company is missing). Goal: determine whether the caller's organization already
exists as a **Service Provider**, **Customer/Client**, both, or neither.

Search all four systems below. Record every hit; note ambiguous matches.

## Vetting output (include in every triage packet)

| System | Entity type | Match | Identifier | Notes |
| --- | --- | --- | --- | --- |
| Siebel / Gateway | Service Provider | Yes / No / Possible | SP # or name | |
| Gateway / VixxoLink | Customer | Yes / No / Possible | Customer # or name | |
| JDE | Vendor | Yes / No / Unknown | Vendor # if found | |
| Salesforce | Lead / Case / Account / Contact | Yes / No / Possible | SF Id | Status, CaseNumber |

**Overall entity posture:** `Known SP` | `Known Customer` | `Known SP + Customer` |
`Prospect (SF Lead only)` | `Unknown / Not in systems`

## Search order

1. Normalize the spoken company name (strip LLC, Inc, punctuation; keep legal
   suffixes when matching Siebel records).
2. If the transcript cites an **SP number**, **customer number**, or **SR
   number**, resolve that ID first — it is stronger than fuzzy name search.
3. Run name searches across systems in parallel when MCP is available.
4. If multiple name matches, pick the best match and list alternates under
   **Open questions**. Do not merge distinct companies.

## Siebel (via Gateway)

Siebel SP master data is reachable through Gateway SWM tools.

| Step | Tool | Notes |
| --- | --- | --- |
| List / filter providers | `gateway_swm_list_providers` | Scan for name match on returned rows |
| Provider detail | `gateway_swm_get_provider` | When SP number is known |
| Siebel SP lookup | `gateway_swm_siebel_sp_*` read paths | Use when SWM list is inconclusive |

Treat a Siebel/Gateway SP hit as **Known SP**.

## Gateway — customers

| Step | Tool | Notes |
| --- | --- | --- |
| List customers | `gateway_swm_list_customers` | Match on customer name |
| Customer options | `gateway_swm_list_customer_options` | When customer number is known |

Also use **VixxoLink**:

| Step | Tool | Notes |
| --- | --- | --- |
| Customer list | `vixxolink_list_customers` | Cross-check visible customer names |
| Customer detail | `vixxolink_get_customer` | When customer number is known |

Treat a customer hit as **Known Customer**. Callers asking about **their
stores/sites as a client** may be a customer contact, not an SP.

## JDE

JDE vendor master is not exposed as a dedicated MCP search today. Use
best-effort validation:

1. **Gateway invoice / vendor context** — when an invoice # or SR is cited,
   pull invoice header via `gateway_search_invoices` / `gateway_get_invoice`
   and capture vendor/supplier identifiers on the record.
2. **Business Objects (optional)** — if a JDE vendor universe report is
   configured in this workspace, run a name search via `bo_universe_*` tools.
3. If neither path returns a vendor row, set JDE match to **Unknown** (not
   **No**) unless you have positive evidence the vendor does not exist.

Document which path was used in the vetting **Notes** column.

## Salesforce

Resolve org with `get_username` before querying. Run **Lead, Case, Account,
and Contact** searches on every voicemail (unless `--skip-vetting`). Full write
rules: [salesforce-notes.md](salesforce-notes.md).

### Lead search (mandatory — include Closed and converted)

Search **all** Leads. Do **not** add `IsConverted = false`, `Status = 'New'`,
or `Status != 'Closed'`. A Closed Lead is still a match (Case **00011971**:
Tom / Turnkey / ANI `716-209-3703` → web identity Thomas Kornacki → Closed
Lead `00QTS00000h2lQH2AY`, TURNKEY PROPERTY MAINTENANCE LLC, Lead phone
`716-216-4086` — different from ANI).

Helper (preferred):

```bash
python .agents/skills/sp-voicemail-triage/scripts/search_sf_leads.py \
  --phone {ani_or_callback} --company "{spoken_company}" --name "{caller}" --json
```

SOQL (same rules if running MCP directly):

```sql
SELECT Id, Name, FirstName, LastName, Company, Status, IsConverted,
       ConvertedAccountId, Phone, MobilePhone, Email, LastModifiedDate
FROM Lead
WHERE Company LIKE '%{normalized_company}%'
   OR LastName LIKE '%{last_name}%'
   OR Name LIKE '%{full_name}%'
   OR Phone LIKE '%{last10_digits}%'
   OR MobilePhone LIKE '%{last10_digits}%'
ORDER BY LastModifiedDate DESC
LIMIT 25
```

**Required predicates**

1. **Company** — always, even when the caller is first-name-only (`Tom` +
   Turnkey). Phone on the Lead may not match the voicemail ANI.
2. **Phone and MobilePhone** — last 10 digits of **ANI and** spoken callback
   (search both). Run even when company is `Not stated`.
3. **Full name** — when STT or web identity gives first + last.
4. **Do not** require a phone match to accept a company + name Lead.

**Web identity when first-name-only**

If STT has a first name (`Tom`) and a phone/ANI, and Lead phone search is
empty **or** you need to confirm which Turnkey Lead:

1. Public web search: `{ANI/callback}`, then `{first name} {company} {phone}`.
2. If a full name surfaces (Thomas Kornacki), **re-run Lead search** with
   `--name "Thomas Kornacki"` (LastName).
3. Record the web source in vetting Notes. Do not invent a last name.

**Which Lead to keep**

- Prefer same **Company** over same first name at another company.
- Prefer most recently modified when still ambiguous.
- **Closed** unconverted: still `Prospect (SF Lead only)` — post Lead Task.
- **Converted:** report `ConvertedAccountId`; Task on Account/Contact, not
  `WhoId` on the converted Lead.

### Case search

```sql
SELECT Id, CaseNumber, Subject, Status, ContactEmail, Description, CreatedDate
FROM Case
WHERE Description LIKE '%Freshdesk #{ticket_id}%'
   OR Subject LIKE '%{normalized_company}%'
   OR Subject LIKE '%{contact_name}%'
   OR Description LIKE '%{last10_digits}%'
ORDER BY CreatedDate DESC
LIMIT 10
```

When a Freshdesk ticket id is known, the **`Freshdesk #{id}`** predicate is
**required first** — prevents duplicate Cases on re-triage.

### Account search (Service Provider bootstrap)

When Gateway returns empty but company name is confident:

```sql
SELECT Id, Name, Type, Service_Provider_Number__c, Phone
FROM Account
WHERE Type = 'Service Provider'
  AND Name LIKE '%{normalized_company}%'
LIMIT 5
```

If `Service_Provider_Number__c` is populated, re-run Gateway with that KS
number.

### Contact search (callback phone)

```sql
SELECT Id, Name, Email, Phone, AccountId
FROM Contact
WHERE Phone LIKE '%{last10_digits}%'
   OR MobilePhone LIKE '%{last10_digits}%'
LIMIT 5
```

Prefer the most recently modified Lead when multiple Leads match. Capture
**Lead Id**, **Case Number**, and **Account Id** in the triage packet.

**Salesforce writes:** MCP is read-only. Phase 2 uses Salesforce CLI — Task
on Lead and/or Case; create Case when no dedupe match and category maps to an
SF queue. See [salesforce-notes.md](salesforce-notes.md).

## When vetting changes routing

| Posture | Routing hint |
| --- | --- |
| Known SP + billing/invoice category | AP path still applies; mention SP # in forward |
| Known SP + VixxoLink/technical | `service.providermanagement@vixxo.com` |
| Known Customer (not SP) | Unlikely SP onboarding — clarify in summary; do not route to recruitment |
| Prospect (SF Lead only) | Onboarding branch → Lead Task + Case Task; resolve Freshdesk |
| Open SF Case (incl. prior triage Case) | Task on existing Case — **do not duplicate Case** |
| Unknown + onboarding intent | Onboarding branch → recruitment forward + SF Case when no Case exists |
| Unknown + other category | Route by category; flag unknown entity in internal note |
