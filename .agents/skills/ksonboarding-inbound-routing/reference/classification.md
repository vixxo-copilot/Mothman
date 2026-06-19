# Classification — KS Onboarding retype rules

Assign **one routing outcome** per inbound email. Evaluate rules **top to
bottom**; the first strong match wins.

When signals are weak or evenly split between two buckets, **retain
`KSOnboarding`**, document ambiguity in the internal note, and tag
`ks-onboarding-retained`.

## Priority 1 — COI → `COIs`

**When:** the inbound email **contains a COI**.

**Strong signals:**

| Signal | Examples |
| --- | --- |
| Attachment | PDF/JPG/PNG named `COI`, `certificate`, `ACORD`, `insurance`, `cert` |
| ACORD form | Body or attachment text shows ACORD 25 fields |
| Body keywords | COI, certificate of insurance, insurance certificate, additional insured, ACORD, compliance certificate, coverage certificate |
| Forward chain | Quoted mail from broker/insurer submitting updated certificate |

**Exclude:** general "send us your COI" onboarding instructions with **no**
certificate attached or pasted — that is onboarding, not a COI submission.

**Actions:**

- Set `type: COIs`
- Add tags: `ks-inbound-routed`, `coi`, `risk-compliance-routed`
- Clear stale `cf_vixxo_link_type_of_request` when present

**Downstream:** `vixxo-coi-review` works the COI queue after retype.

---

## Priority 2 — Portal assistance → `VixxoLink Support`

**When:** the inbound email **requests assistance with the portal** (VixxoLink /
SP portal).

**Strong signals:**

| Signal | Examples |
| --- | --- |
| Product names | VixxoLink, Vixxo Link, provider portal, SP portal, mobile app |
| Access issues | login, log in, password, reset password, locked out, can't access |
| Workflow | dispatch board, accept work, decline job, can't see jobs, post notes, time in/out, upload photos |

**Exclude — client portal:**

- client portal, customer portal, store portal, facilities portal
- Flag in internal note; **do not** retype to VixxoLink Support
- Tag `client-portal-review` when client posture is clear

**Actions:**

- Set `type: VixxoLink Support`
- Add tags: `ks-inbound-routed`, `vixxolink-routed`

---

## Priority 3 — Past-due invoice / statement → `Invoice Support`

**When:** the inbound email **requests status for past-due invoices**, or
**contains a statement**.

**Strong signals:**

| Signal | Examples |
| --- | --- |
| Past-due language | past due, past-due, overdue, aging, delinquent, unpaid invoice, outstanding balance, when will this be paid, payment status |
| Statement | statement, statement of account, account statement, AR statement, open invoices list, balance notice |
| Attachment | Filename contains `statement`, `aging`, `pastdue`, `past_due`, `open invoices`, `AR` |
| Content | Spreadsheet or PDF listing multiple invoice numbers with balances or ages |

**Exclude:**

- First-time invoice **submission** with no past-due / status ask — may stay
  KSOnboarding or route via `vixxo-freshdesk-invoice-review` if user asks
- Pure payment-method / remittance setup without statement or past-due ask

**Actions:**

- Set `type: Invoice Support`
- Set `custom_fields.cf_type_of_request: Follow up on an Unpaid Invoice`
- Add tags: `ks-inbound-routed`, `invoice-routed`

**Downstream:** `vixxo-spm-invoice-concerns` or `vixxo-freshdesk-invoice-review`.

---

## Priority 4 — Retain `KSOnboarding`

**When:** none of the above apply with confidence.

Typical retained mail:

- New SP onboarding / coverage enrollment
- Recruitment / rate card / contract questions
- W-9 or banking setup in onboarding context
- General SPM questions without portal, COI, or invoice/statement signals

**Actions:**

- Do **not** change `type`
- Add tags: `ks-inbound-routed`, `ks-onboarding-retained`
- Post internal note with classification rationale

---

## Multi-topic messages

When the email mentions multiple topics:

1. Apply priority order: **COI > Portal > Invoice/Statement > Retain**.
2. Use the category matching the **dominant unresolved ask** when one topic
   clearly blocks the sender.
3. Note secondary topics in the internal note summary.

Example: COI attachment plus a portal login question → retype **`COIs`**
(COI attachment is priority 1).

Example: portal login plus one overdue invoice status ask → retype **`Invoice
Support`** only if the past-due ask is the dominant ask; otherwise **`VixxoLink
Support`** when portal access is the blocker.
