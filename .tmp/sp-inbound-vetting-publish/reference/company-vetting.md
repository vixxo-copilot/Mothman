# Company Vetting — Gateway + VixxoLink + Salesforce



Run after [intake](intake.md) entity extraction. Search **Gateway**, **VixxoLink**,

and **Salesforce (Lead / Case / Account)** for the inbound contact.



Applies to **all** intake surfaces. For SF-primary queues (ksonboarding, COI,

spm), Salesforce Case/Lead context is usually **already present** — use it to

seed company and email before broad SOQL. Gateway remains authoritative for

**Known SP** (Siebel SP # + display name).



## Vetting output table (required in every packet)



| System | Entity | Match | Identifier | Status / notes |

| --- | --- | --- | --- | --- |

| Gateway / Siebel | Service Provider | Yes / No / Possible | SP # + display name | Source tool + match key |

| VixxoLink | Service Provider | Yes / No / Possible | SP # + name from SR | When SR resolved |

| Salesforce | Lead | Yes / No / Possible | Lead Id | Status, LastModifiedDate |

| Salesforce | Case | Yes / No / Possible | Case Id | Status, Subject |

| Salesforce | Account | Yes / No / Possible | Account Id | Type |



**Overall posture:** `Known SP` | `Prospect (SF Lead)` | `Open SF Case` |

`Known SP + SF Lead` | `Unknown / Not in systems`



## Search order



1. **SP number** (explicit or KS#####) — `gateway_search_invoices`

   (`serviceProviderNumber`) or `gateway_swm_get_provider`.

2. **SR number** — `gateway_get_service_request`, then

   `vixxolink_resolve_service_request` for cross-check.

3. **Requester email** — Gateway invoice search keyed to submitter email

   (`createdByUsername` on invoice rows). Skip `@vixxo.com` internal mailboxes.

4. **Email domain** — `gateway_search_invoices` on the full domain and

   registrable stem. **Skip generic freemail** domains (gmail, yahoo, etc.).

5. **Contact name** — Case contact / FD requester via Gateway invoice search.

6. **Company name (required after email vetting)** — subject, body, signature;

   `gateway_search_invoices` (`searchString`); confirm with

   `gateway_swm_get_provider` when KS/Siebel SP # returned.

7. On multiple fuzzy hits, pick the best match; list alternates under **Open

   questions**. Never merge distinct companies.



## SF-primary queues — use Case context first



When vetting an open queue Case:



| Step | Source | Action |

| --- | --- | --- |

| 1 | Case `AccountId` | If populated, `SELECT Name, Type FROM Account WHERE Id = …` |

| 2 | Case `ContactId` | Pull contact name + email for Gateway search |

| 3 | Case `Subject` / `Description` | Entity extraction + routing classification |

| 4 | Linked Lead | When Case references onboarding Lead, read Lead `Company` |

| 5 | Broad SOQL | Fall back to Lead/Case search below when Case fields are thin |



Document on the **queue Case** via Task even when a related Lead also matches.

When posture is **Known SP** and this search returns an Account Id, also update
the queue Case `AccountId` if it is blank or still on a Vixxo / SP Support shell
placeholder — see [salesforce-notes.md](salesforce-notes.md).

## Contact email — Gateway



Invoice rows expose the submitting portal user as `createdByUsername` (often

the provider contact email).



| Step | Tool | Arguments / filter |

| --- | --- | --- |

| Email search | `gateway_search_invoices` | `searchString`: full requester email |

| Confirm hit | _(client filter)_ | `createdByUsername` equals requester email (case-insensitive) |

| Local-part fallback | `gateway_search_invoices` | `searchString`: portion before `@` when full email returns empty |

| Extract SP | _(from invoice row)_ | `serviceProviderNumber`, `serviceProviderName` |



Do **not** run email-path Gateway searches for `@vixxo.com` requesters — those

are internal forwards.



## Email domain — Gateway



When the requester uses a **corporate domain** (not freemail), search Gateway

after full-email and local-part attempts. **Skip domain search** for consumer

mail hosts.



## Contact name — Gateway



Search Freshdesk requester / Case contact name via `gateway_search_invoices`.

Use contact-name hits as **Possible** when email does not exactly match but SP

name aligns with company context.



## SR anchor — Gateway + VixxoLink



| Step | Tool | Notes |

| --- | --- | --- |

| Gateway SR | `gateway_get_service_request` | Read `siebelServiceProviderNum`, `serviceProviderName` |

| VixxoLink SR | `vixxolink_resolve_service_request` | Cross-check assigned SP |

| Invoice → SR chain | `gateway_search_invoices` | When email/name hit returns `serviceRequestNumber` |



## Gateway — company name → SP # (post-email step)



Run **after** contact email / domain / name searches when no Known SP yet.



Example: COI email for **PEAK SEASON LLC** — search Gateway by company name to

resolve Siebel SP # before documenting on the SF Case.



Avoid `gateway_swm_list_providers` in batch runs (upstream 400 in current env);

use invoice search paths above instead.



## Salesforce



Resolve org with `get_username` before querying.



### Lead search



```sql

SELECT Id, Name, Company, Status, Phone, Email, LastModifiedDate

FROM Lead

WHERE Company LIKE '%{normalized_company}%'

   OR Name LIKE '%{contact_name}%'

   OR Name LIKE '%{normalized_company}%'

   OR Email = '{requester_email}'

   OR Phone LIKE '%{last10_digits}%'

ORDER BY LastModifiedDate DESC

LIMIT 10

```



Run email and contact-name predicates even when company is `Not stated`.



### Case search



```sql

SELECT Id, CaseNumber, Subject, Status, AccountId, ContactEmail, CreatedDate

FROM Case

WHERE ContactEmail = '{requester_email}'

   OR Subject LIKE '%{normalized_company}%'

   OR Subject LIKE '%{contact_name}%'

ORDER BY CreatedDate DESC

LIMIT 10

```



When vetting an **open queue Case**, the intake Case is the documentation

target — related Case hits are context only unless user asks otherwise.



### Account search (Service Provider bootstrap)

When Gateway company/email search returns empty but company name is confident,
query **Account** with `Type = 'Service Provider'` and read
`Service_Provider_Number__c` (KS#####). Re-run Gateway with that KS number.

```sql
SELECT Id, Name, Type, Service_Provider_Number__c
FROM Account
WHERE Type = 'Service Provider'
  AND Name LIKE '%{normalized_company}%'
LIMIT 5
```

If `Service_Provider_Number__c` is populated, call
`gateway_search_invoices(serviceProviderNumber=KS#####)` — this is the
authoritative Known SP path (see Allied Locksmiths / KS68937 in
[troubleshooting.md](troubleshooting.md)).

Prefer the most recently modified Lead when multiple Leads match.



## Posture → recommended handling



| Posture | SF-primary queues | AP Help (Freshdesk) | Tag / note |

| --- | --- | --- | --- |

| Known SP | Task on queue Case — include `{SP#} - {Gateway name}` | `cf_sp` = `{SP#} - {name}`; FD internal note | `known-sp` |

| Prospect (SF Lead only) | Task on Lead + queue Case when both exist | `cf_sp` = Lead company or `Unknown` | `sf-lead-match` |

| Open SF Case | Task on queue Case | `cf_sp` when confident company string | `sf-case-match` |

| Known SP + SF Lead/Case | Task linking SP # on Case and Lead | Same as Known SP | `known-sp` |

| Unknown | Task with extracted company; Gateway pending | `cf_sp` = company string or `Unknown` | `unknown-sp` |



When routing table recommends **AP Help forward**, include that in the SF Case

Task regardless of posture. Do not change Case status or send outbound email

unless the user explicitly requests it.



## Script implementation



Batch scripts use `scripts/gateway_vetting.py` and `scripts/entity_extraction.py`

for Freshdesk AP Help runs. SF queue runs use the same Gateway order via MCP in

Cursor sessions. Call **Gateway MCP**, **VixxoLink MCP**, then **Salesforce SOQL**

before writing Tasks.

