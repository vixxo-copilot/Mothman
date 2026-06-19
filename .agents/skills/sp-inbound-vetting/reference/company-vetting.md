# Company Vetting — Gateway + VixxoLink + Salesforce

Run after [intake](intake.md) entity extraction. Search **Gateway**, **VixxoLink**,
and **Salesforce (Lead / Case / Account)** for the inbound contact.

## Vetting output table (required in every packet)

| System | Entity | Match | Identifier | Status / notes |
| --- | --- | --- | --- | --- |
| Gateway / Siebel | Service Provider | Yes / No / Possible | SP # + display name | Source tool + match key |
| VixxoLink | Service Provider | Yes / No / Possible | SP # + name from SR | When SR resolved |
| Salesforce | Lead | Yes / No / Possible | Lead Id | Status, LastModifiedDate |
| Salesforce | Case | Yes / No / Possible | Case Id | Status, Subject |
| Salesforce | Account | Yes / No / Possible | Account Id | Type |

**Overall posture:** `Known SP` | `Possible SP (Gateway)` |
`Prospect (SF Lead)` | `Prospect (SF Lead — possible match)` | `Open SF Case` |
`Known SP + SF Lead` | `Possible SP (Gateway) + SF Lead` |
`Unknown / Not in systems`

## Fuzzy / similar name matching

Batch scripts use `scripts/entity_match.py` (normalization + similarity scoring).
Apply after Gateway/Salesforce search returns candidate rows — not only on exact
string equality.

### Normalization (company and contact)

1. Lowercase; strip punctuation; collapse whitespace.
2. Drop common suffix tokens: `LLC`, `Inc`, `Co`, `Corp`, `Ltd`, `The`,
   `Company`, `Services`, `Service`.
3. **Strip Gateway tracking prefixes** from Siebel SP display names before
   comparing to intake text — these are internal labels, not on provider docs:
   `KS`, `KS-`, `CCPAY`, `STRYKER ONLY`, trailing `ONLY`.
4. Compare normalized strings — do not require punctuation, suffix parity, or
   tracking-prefix parity with Siebel display names.

Example: intake company **Alpha Concepts** matches Gateway SP
**KS - Alpha Concepts LLC** after stripping `KS -` and scoring fuzzy tokens.

### Identification priority

Prefer **contact email** and **contact name** over company string matching.
Provider documentation often uses the trade name; Gateway/Siebel uses tracking
prefixes. Email (`createdByUsername`) and requester name are stronger anchors.

| Priority | Signal | Why |
| --- | --- | --- |
| 1 | Requester email | Portal submitter on invoice rows |
| 2 | Contact name | Correlates to `createdByUsername` / Lead name |
| 3 | KS / SR number | Hard identifiers when present |
| 4 | Company / SP display name | Fuzzy match after tracking-prefix strip |
| 5 | Email domain stem | Fallback when company missing |

Do **not** accept a weak first-hit company search without scoring ≥ 0.75.

### Similarity scoring

| Kind | Method | Threshold |
| --- | --- | --- |
| Company | Max of `SequenceMatcher` ratio, token Jaccard overlap, substring containment | **≥ 0.75** → match |
| Contact name | Last-name + first-initial match **or** `SequenceMatcher` on full name | **≥ 0.75** → match |

When multiple candidates score ≥ 0.75, pick the highest score. Include
**alternates** in the packet when scores are within **0.05** of the best hit.

### Match labels (vetting table)

| Label | When to use |
| --- | --- |
| **Yes** | Exact email on `createdByUsername`, exact KS/SR anchor, or normalized company string equals Gateway SP name |
| **Possible** | Fuzzy company or contact match above threshold; similar SP display name (e.g. `Alpha Concept` vs `Alpha Concepts LLC`) |
| **No** | No candidate ≥ 0.75 and no exact anchor (KS, SR, email) |

Script payloads carry `match_type` (`exact` \| `fuzzy`), `confidence`
(`High` \| `Medium` \| `Low`), and optional `match_score`.

## Search order

1. **SP number** (explicit or KS#####) — `gateway_search_invoices`
   (`serviceProviderNumber`) or `gateway_swm_get_provider`.
2. **SR number** — `gateway_get_service_request`, then
   `vixxolink_resolve_service_request` for cross-check.
3. **Requester email** — Gateway invoice search keyed to submitter email
   (`createdByUsername` on invoice rows). Skip `@vixxo.com` internal mailboxes.
   **Strongest soft identifier when KS/SR absent.**
4. **Contact name** — Freshdesk requester display name via Gateway invoice
   search; prefer rows whose `createdByUsername` correlates.
5. **Company name** — fuzzy match against Gateway SP display names after
   stripping tracking prefixes (`KS`, `CCPAY`, `STRYKER ONLY`, etc.) + Salesforce
   company SOQL.
6. **Email domain stem** — when company is missing, search Gateway on the
   domain token before `@` (skip generic freemail domains).
7. On multiple fuzzy hits, pick the best score; list alternates under **Open
   questions**. Never merge distinct companies. **No un-scored first-hit fallback.**

## Contact email — Gateway

Invoice rows expose the submitting portal user as `createdByUsername` (often
the provider contact email).

| Step | Tool | Arguments / filter |
| --- | --- | --- |
| Email search | `gateway_search_invoices` | `searchString`: full requester email |
| Confirm hit | _(client filter)_ | `createdByUsername` equals requester email (case-insensitive) |
| Local-part fallback | `gateway_search_invoices` | `searchString`: portion before `@` when full email returns empty |
| Extract SP | _(from invoice row)_ | `serviceProviderNumber`, `serviceProviderName` |

Example: `philips@alphaconceptsllc.com` → invoices for **KS101031 — KS - Alpha
Concepts LLC**.

Do **not** run email-path Gateway searches for `@vixxo.com` requesters — those
are internal forwards.

## Contact name — Gateway

| Step | Tool | Arguments |
| --- | --- | --- |
| Full name | `gateway_search_invoices` | `searchString`: Freshdesk requester `name` |
| Last name | `gateway_search_invoices` | `searchString`: last token when full name is inconclusive |
| Confirm hit | _(client filter)_ | Match `createdByUsername` or correlate SP name |

Use contact-name hits as **Possible** when `createdByUsername` does not exactly
match the requester email but SP name aligns with extracted company context.

## SR anchor — Gateway + VixxoLink

| Step | Tool | Notes |
| --- | --- | --- |
| Gateway SR | `gateway_get_service_request` | Read `siebelServiceProviderNum`, `serviceProviderName` |
| VixxoLink SR | `vixxolink_resolve_service_request` | Cross-check assigned SP; include `notes` when SR cited in ticket |
| Invoice → SR chain | `gateway_search_invoices` | When email/name hit returns `serviceRequestNumber`, optionally re-resolve SR for confirmation |

Prefer Gateway SR payload when both agree; note conflicts in the internal note.

## Gateway — company / KS fallbacks

| Step | Tool | Notes |
| --- | --- | --- |
| SP by KS# | `gateway_search_invoices` | `serviceProviderNumber` (e.g. `KS101031`) |
| SP by company | `gateway_search_invoices` | `searchString` (company name) |
| Legacy detail | `gateway_swm_get_provider` | When KS lookup returns empty |

Avoid `gateway_swm_list_providers` in batch runs (upstream 400 in current env);
use invoice search paths above instead.

Treat a confident Gateway or VixxoLink SP hit as **Known SP**. Capture:

- SP number (Siebel / Gateway id)
- Display name exactly as Gateway returns it
- Match source (email / name / company / SR / KS)

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

**Voicemail cross-reference:** When vetting SP voicemails, also search by
**callback phone** (last 10 digits) — see
[sp-voicemail-triage/reference/company-vetting.md](../../sp-voicemail-triage/reference/company-vetting.md)
for Gateway customer + Salesforce Contact/Lead/Account phone paths and client
routing rules.

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
| Known SP | `{SP#} - {Gateway display name}` | Task only if exact/High Lead also found | `sp-vetted`, `known-sp` |
| Possible SP (Gateway) | `{SP#} - {Gateway display name}` (note **Possible** in internal note) | No SF Task unless exact/High Lead/Case; flag fuzzy SF hits | `sp-vetted`, `known-sp` |
| Prospect (SF Lead only) | Lead company name or `Unknown` | **Required** Task on Lead (exact/High or exact email) | `sp-vetted`, `sf-lead-match` |
| Prospect (SF Lead — possible match) | Lead company name or `Unknown` | **No auto Task** — `sf-match-review`; operator confirms Lead | `sp-vetted`, `sf-lead-match`, `sf-match-review` |
| Open SF Case | Case subject company or `Unknown` | **Required** Task on Case when exact/High (`ContactEmail`) | `sp-vetted`, `sf-case-match` |
| Open SF Case (possible match) | Case subject company or `Unknown` | **No auto Task** — `sf-match-review`; operator confirms Case | `sp-vetted`, `sf-case-match`, `sf-match-review` |
| Known SP + SF Lead/Case | `{SP#} - {name}` | Task on Lead/Case only when exact/High (or Lead exact email) | `sp-vetted`, `known-sp` |
| Possible SP (Gateway) + SF Lead | `{SP#} - {name}` | Task on Lead only when exact/High or exact email; else `sf-match-review` | `sp-vetted`, `known-sp` |
| Unknown | `Unknown` or extracted company string | None | `sp-vetted`, `unknown-sp` |

**SF Task auto-post rule:** `match_type: exact` and `confidence: High`, or Lead
`Email` equals requester email. Fuzzy or Medium/Low matches → internal note
**SF match — review required** + tag `sf-match-review`; no Task until confirmed.

Do not change ticket status or send outbound email from this skill unless the
user explicitly requests it.

## Script implementation

Batch scripts use `scripts/gateway_vetting.py` and `scripts/entity_match.py`
for Gateway + VixxoLink lookup and fuzzy scoring. When running interactively in
Cursor, call the same tools via **Gateway MCP** and **VixxoLink MCP** before
Salesforce SOQL; apply the fuzzy rules above to filter invoice rows and SOQL
results.
