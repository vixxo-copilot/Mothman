# Examples

## Batch summary — mixed SF + AP Help

```markdown
# SP Inbound Vetting — 2026-06-25

| # | Source | Queue | Company | Posture | SP # | Routing | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | SF Case 001234 | coi | Peak Season LLC | Known SP | 1044892 | Stay in SF | complete |
| 2 | SF Case 001235 | ksonboarding | Apex HVAC LLC | Known SP | 1044555 | Stay in SF | complete |
| 3 | SF Case 001236 | ksonboarding | LockPro LLC | Known SP | KS101347 | **→ AP Help (draft)** | complete |
| 4 | FD #51235 | aphelp | NewCo Electric | Prospect | — | FD primary | complete |

**Counts:** 4 vetted | 0 skipped | 3 Known SP | 1 Prospect | 1 AP forward recommended
```

## Single packet — COI queue stays in Salesforce

COI submission — vet identity and document on the SF Case; do **not** forward to
AP Help.

```markdown
## SP Inbound Vetting — SF Case 00123456

| Field | Value |
| --- | --- |
| **Queue** | coi |
| **System of record** | Salesforce |
| **Company** | Peak Season LLC |
| **Posture** | Known SP |
| **Gateway SP** | 1044892 — KS - Peak Season LLC |
| **Salesforce** | Case 00123456 (Open, COI queue) |
| **Routing** | Stay in SF — COI/compliance ask |

### Actions taken
- SF Case Task: posted (includes Gateway SP # + COI summary)
- SF Lead Task: N/A
- Recommended forward: none
- Freshdesk: N/A (SF-primary)
```

After identity vetting, hand certificate field review to **`vixxo-coi-review`**.

## Single packet — Payment inquiry on ksonboarding → recommend AP Help

Payment-status ask on a Case that landed in ksonboarding — **vet SP identity in
SF**, then **recommend** forward to AP Help (draft only; no auto-send).

```markdown
## SP Inbound Vetting — SF Case 00123789

| Field | Value |
| --- | --- |
| **Queue** | ksonboarding |
| **System of record** | Salesforce |
| **Subject** | Payment status for invoice INV-88421 |
| **Company** | LockPro LLC |
| **Posture** | Known SP |
| **Gateway SP** | KS101347 — KS - LockPro LLC |
| **Routing** | **Recommend forward to aphelp@vixxo.com** |

### Summary
Provider asks when payment will post for invoice INV-88421. Identity confirmed
via Gateway. This is an AP/payment ask — not KS onboarding work.

### Actions taken
- SF Case Task: posted (SP #, invoice ref, routing recommendation)
- Recommended forward (draft — awaiting operator approval):
  Forward to aphelp@vixxo.com with SP KS101347, invoice INV-88421, requester email.
```

**Do not** call forward APIs until {{employee_name}} approves.

## Single packet — AP Help (Freshdesk primary)

```markdown
## SP Inbound Vetting — FD #51235

| Field | Value |
| --- | --- |
| **Queue** | aphelp |
| **System of record** | Freshdesk |
| **Company** | NewCo Electric |
| **Posture** | Prospect (SF Lead) |
| **Gateway SP** | No match |
| **Salesforce** | Lead 00Q… (Working) |
| **cf_sp** | `NewCo Electric` |

### Actions taken
- Internal note: posted
- cf_sp + tags: updated (`sp-vetted`, `sf-lead-match`)
- SF Lead Task: posted
- SF Case Task: N/A
```

## Single packet — Known SP (ksonboarding, stay in SF)

```markdown
## SP Inbound Vetting — SF Case 00124000

| Field | Value |
| --- | --- |
| **Queue** | ksonboarding |
| **Company** | Apex HVAC LLC |
| **Posture** | Known SP |
| **Gateway SP** | 1044555 — KS - Apex HVAC LLC |
| **Salesforce** | Lead 00Q… (Working) + Case 00124000 |
| **Routing** | Stay in SF — coverage/onboarding ask |

### Actions taken
- SF Case Task: posted
- SF Lead Task: posted
```

## Signature extraction — Brewer Lock & Safe

Requester display name `S Earl` on `brewerbooks@yahoo.com` is not the SP.
Body signature:

```text
Tom Wilson
Bookkeeper for Brewer Lock & Safe Co, Inc.
254-753-6663
```

**Extract:** `Brewer Lock & Safe Co, Inc` from the `Bookkeeper for …` line.
Run Gateway company search (yahoo.com is freemail — skip domain search).

## Subject + signature company — COI (Peak Season)

Subject `COI from "PEAK SEASON"` on the **COI Salesforce queue** — stay in SF.

| Source | Extract |
| --- | --- |
| Subject | `COI from "PEAK SEASON"` → `PEAK SEASON` |
| Body | `Certificate of Insurance (COI) from PEAK SEASON LLC` |
| Signature | `Account Manager- Peak Season, Inc.` → strip title prefix |
| Email | `monique@peakseasonservice.com` |

When Gateway returns `serviceProviderNumber`, posture = **Known SP**. Document
on the SF Case Task with SP # — do not forward to AP Help.
