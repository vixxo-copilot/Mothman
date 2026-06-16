# Company Vetting — Gateway + Salesforce

Run after [intake](intake.md) entity extraction. This skill searches **Gateway
(Siebel SP)** and **Salesforce (Lead / Case / Account)** only.

## Vetting output table (required in every packet)

| System | Entity | Match | Identifier | Status / notes |
| --- | --- | --- | --- | --- |
| Gateway / Siebel | Service Provider | Yes / No / Possible | SP # + display name | Active / inactive if visible |
| Salesforce | Lead | Yes / No / Possible | Lead Id | Status, LastModifiedDate |
| Salesforce | Case | Yes / No / Possible | Case Id | Status, Subject |
| Salesforce | Account | Yes / No / Possible | Account Id | Type |

**Overall posture:** `Known SP` | `Prospect (SF Lead)` | `Open SF Case` |
`Known SP + SF Lead` | `Unknown / Not in systems`

## Search order

1. If an **SP number** is cited, resolve it first via
   `gateway_swm_get_provider` (or equivalent Gateway SWM read).
2. If an **SR number** is cited, pull `gateway_get_service_request` and capture
   the assigned SP number + name from the SR payload.
3. Run **parallel name searches** when MCP is available.
4. On multiple fuzzy hits, pick the best match; list alternates under **Open
   questions**. Never merge distinct companies.

## Gateway — Service Provider

| Step | Tool | Notes |
| --- | --- | --- |
| List / filter | `gateway_swm_list_providers` | Scan returned rows for name match |
| Detail | `gateway_swm_get_provider` | When SP number is known |
| SR anchor | `gateway_get_service_request` | When SR cited; inherit SP from SR |

Treat a confident Gateway SP hit as **Known SP**. Capture:

- SP number (Siebel / Gateway id)
- Display name exactly as Gateway returns it
- Active/inactive or status fields when present

## Salesforce

Resolve org with `get_username` before querying.

### Lead search (required for ksonboarding items; recommended for all)

```sql
SELECT Id, Name, Company, Status, Phone, Email, LastModifiedDate
FROM Lead
WHERE Company LIKE '%{normalized_company}%'
   OR Name LIKE '%{normalized_company}%'
   OR Email = '{requester_email}'
   OR Phone LIKE '%{last10_digits}%'
ORDER BY LastModifiedDate DESC
LIMIT 10
```

### Case search

```sql
SELECT Id, CaseNumber, Subject, Status, AccountId, ContactEmail, CreatedDate
FROM Case
WHERE ContactEmail = '{requester_email}'
   OR Subject LIKE '%{normalized_company}%'
ORDER BY CreatedDate DESC
LIMIT 10
```

When requester email is on a Case, prefer that hit over fuzzy company match.

### Account search (secondary)

```sql
SELECT Id, Name, Type, Phone, Website
FROM Account
WHERE Name LIKE '%{normalized_company}%'
LIMIT 5
```

Prefer the most recently modified Lead when multiple Leads match.

## Posture → recommended handling

| Posture | Freshdesk `cf_sp` | Salesforce note | Tag |
| --- | --- | --- | --- |
| Known SP | `{SP#} - {Gateway display name}` | Optional Task on related Lead/Case if also found | `sp-vetted`, `known-sp` |
| Prospect (SF Lead only) | Lead company name or `Unknown` | **Required** Task on Lead | `sp-vetted`, `sf-lead-match` |
| Open SF Case | Case subject company or `Unknown` | **Required** Task on Case | `sp-vetted`, `sf-case-match` |
| Known SP + SF Lead/Case | `{SP#} - {name}` | Task on Lead/Case linking SP # | `sp-vetted`, `known-sp` |
| Unknown | `Unknown` or extracted company string | None | `sp-vetted`, `unknown-sp` |

Do not change ticket status or send outbound email from this skill unless the
user explicitly requests it.
