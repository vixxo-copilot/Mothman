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
| Salesforce | Lead / Account | Yes / No / Possible | SF Id | |

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

Resolve org with `get_username` before querying.

Search for **existing or previous leads** (required for onboarding voicemails):

```sql
SELECT Id, Name, Company, Status, Phone, Email, LastModifiedDate
FROM Lead
WHERE Company LIKE '%{normalized_company}%'
   OR Name LIKE '%{normalized_company}%'
ORDER BY LastModifiedDate DESC
LIMIT 10
```

Also check converted/historical context:

```sql
SELECT Id, Name, Type, Phone, Website
FROM Account
WHERE Name LIKE '%{normalized_company}%'
LIMIT 5
```

Prefer the most recently modified Lead when multiple match. Capture **Lead Id**
(or Account Id) for onboarding routing.

**Salesforce notes:** The Salesforce MCP supports SOQL read (`run_soql_query`)
only. To add a note on a Lead automatically during Phase 2, use the Salesforce
CLI (`sf data create record --sobject Task` / Chatter) with the transcribed
voicemail text, or the Salesforce UI if CLI is unavailable — record success or
failure in the Freshdesk internal note. See [routing-actions.md](routing-actions.md)
onboarding branch.

## When vetting changes routing

| Posture | Routing hint |
| --- | --- |
| Known SP + billing/invoice category | AP path still applies; mention SP # in forward |
| Known SP + VixxoLink/technical | `service.providermanagement@vixxo.com` |
| Known Customer (not SP) | Unlikely SP onboarding — clarify in summary; do not route to recruitment |
| Prospect (SF Lead only) | Onboarding branch → Lead note + resolve Freshdesk |
| Unknown + onboarding intent | Onboarding branch → recruitment forward |
| Unknown + other category | Route by category; flag unknown entity in internal note |
