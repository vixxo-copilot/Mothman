# Examples — KS Onboarding inbound routing

## Batch summary (top of run)

```markdown
# KS Onboarding Routing — 2026-06-19

| # | FD # | Subject (short) | Classification | Type change | cf_sp | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 52001 | Updated COI attached | COI | → COIs | blank | routed |
| 2 | 52002 | Can't log into VixxoLink | Portal | → VixxoLink Support | 1044555 - KS - Apex HVAC | routed |
| 3 | 52003 | Past due statement Jun 2026 | Invoice | → Invoice Support | blank | routed |
| 4 | 52004 | New HVAC onboarding question | Retained | — | blank | noted |

**Counts:** 4 reviewed | 0 voicemails skipped | 3 retyped | 1 retained
```

## COI retype

**Input:** KSOnboarding ticket; attachment `ACORD_Certificate.pdf`; body
"Please find our updated certificate of insurance."

**Output:**

| Field | Value |
| --- | --- |
| **Classification** | COI |
| **Type change** | KSOnboarding → COIs |
| **cf_sp** | left blank — Gateway Possible match only (Medium) |
| **Tags** | ks-inbound-routed, coi, risk-compliance-routed |

## Portal retype

**Input:** "I reset my password but still can't see jobs on the dispatch board."

**Output:**

| Field | Value |
| --- | --- |
| **Classification** | VixxoLink Support |
| **Type change** | KSOnboarding → VixxoLink Support |
| **cf_sp** | `1044555 - KS - Apex HVAC LLC` — Known SP, High confidence |

## Invoice / statement retype

**Input:** Attachment `Statement_of_Account_May2026.pdf`; body asks when three
listed invoices will be paid — all marked past due.

**Output:**

| Field | Value |
| --- | --- |
| **Classification** | Invoice Support |
| **Type change** | KSOnboarding → Invoice Support |
| **cf_type_of_request** | Follow up on an Unpaid Invoice |
| **cf_sp** | left blank — no Gateway match |

## Retained onboarding

**Input:** "We'd like to enroll as a new plumbing contractor in Texas."

**Output:**

| Field | Value |
| --- | --- |
| **Classification** | KSOnboarding retained |
| **Type change** | none |
| **Tags** | ks-inbound-routed, ks-onboarding-retained |
