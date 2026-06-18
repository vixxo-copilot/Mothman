# SP Voicemail — Category Taxonomy

Assign **one primary category** per voicemail. Use **sub-reason** for the
specific ask in plain English.

Evaluate top to bottom when signals overlap; pick the category that matches
the **dominant unresolved ask**.

## Categories

### VixxoLink Support

SP needs help with VixxoLink access, login, mobile app, password reset,
dispatch visibility, accepting/declining work, posting notes, or general
platform usage.

**Signals:** VixxoLink, portal, app, login, password, can't see jobs, accept
work, mobile, dispatch board, time in/out

**Forward to:** `service.providermanagement@vixxo.com`

**Related skills:** `polyai` (if voice-agent context)

---

### Billing / Invoice Support

Questions about submitting invoices, invoice rejection, invoice status in
VixxoLink, billing workflow, or correcting invoice data.

**Signals:** invoice, rejected, submit invoice, billing, invoice status,
correction, resubmit, short pay dispute on invoice line

**Forward to:** `aphelp@vixxo.com`

**Related skills:** `vixxo-freshdesk-invoice-review`, `vixxo-spm-invoice-concerns`

---

### Payment Information

Payment timing, check status, remittance, ACH/wire, "when will I get paid",
missing payment, payment amount questions.

**Signals:** payment, paid, check, remittance, ACH, wire, when paid, haven't
received payment, payment status, balance due from Vixxo

**Forward to:** `aphelp@vixxo.com`

**Related skills:** `vixxo-freshdesk-invoice-review`, `vixxo-spm-invoice-concerns`

---

### Service Request / Dispatch

SR status, assignment, ETA, scope questions, release/reassign, can't reach
site, need dispatch callback, job details.

**Signals:** service request, SR, work order, dispatch, ETA, assigned, release,
technician, site access, scope, priority

**Forward to:** Gateway SR **Project Manager + Support staff** (from
`vixxolink_resolve_service_request` / `gateway_get_service_request`); subject
`{SR#}, Need Assistance`. Resolve Freshdesk after forward + internal note.

**Related skills:** `sr-triage-pre-dispatch`, VixxoLink MCP for SR lookup

---

### COI / Compliance

Certificate of insurance, insurance requirements, additional insured,
expiration, compliance hold blocking work.

**Signals:** COI, certificate of insurance, insurance, additional insured,
ACORD, compliance, coverage certificate

**Forward to:** `COI@vixxo.com`

**Related skills:** `vixxo-coi-review`

---

### Coverage / Onboarding

New SP onboarding, coverage area, trade enrollment, rate card, contract,
activation, or account setup.

**Signals:** onboarding, coverage, new provider, enrollment, contract,
activation, rate card, W-9 setup (onboarding context)

**Forward to:** See onboarding branch in [routing-actions.md](routing-actions.md)
— Salesforce Lead found → Lead note + resolve; no Lead →
`spm-recruitment@vixxo.com`

---

### Quote / Estimate

Quote submission, quote approval status, estimate follow-up, pricing on pending
work.

**Signals:** quote, estimate, pricing, bid, approval on quote, pending quote

**Suggested routing:** Service center or program-specific quote desk

---

### Account Update

Contact info change, banking/ACH update, address change, W-9 resubmit
(account maintenance — not onboarding).

**Signals:** update address, change contact, banking, ACH, W-9, remit-to,
account change

**Suggested routing:** SPM account maintenance

---

### Technical / Trade Support

Trade-specific how-to, parts, warranty, scope interpretation — not VixxoLink
login issues.

**Signals:** how to fix, parts, warranty, technical question, trade guidance

**Forward to:** `service.providermanagement@vixxo.com`

---

### General Inquiry

Caller intent is unclear, wrong department, or general question without a
 sharper category above.

**Signals:** none of the above clearly apply

**Forward to:** `service.providermanagement@vixxo.com`

---

### Wrong Number / Non-SP

Not a service provider, wrong number, sales solicitation, personal call.

**Signals:** wrong number, not Vixxo, sales pitch, unrelated business

**Suggested routing:** None — document and archive

---

### Foul Language / Abusive

Transcript contains profanity or abusive language (word-boundary match on the
foul-language term list in `batch_process_freshdesk.py`).

**Signals:** profanity detected in Whisper transcript after successful STT

**Forward to:** **None** — post private internal note, **resolve without forward**

**Priority:** Overrides all other categories when matched.

---

### Too Short (<10s)

Voicemail duration under 10 seconds (from 8x8 `Duration: MM:SS` metadata or
Whisper audio length).

**Signals:** duration &lt; 0:10

**Forward to:** **None** — post private internal note, **resolve without forward**

---

### Blank / Minimal Speech

Spoken transcript is empty or only one or two words after STT.

**Signals:** blank audio, hang-up, "hello", "test", single-word messages

**Forward to:** **None** — post private internal note, **resolve without forward**

## Multi-topic messages

When the caller mentions multiple topics:

1. Identify the **primary ask** — what blocks them from working or getting paid.
2. Typical priority order: **COI/compliance hold** > **payment** >
   **invoice rejection** > **dispatch/SR** > **VixxoLink access** > **general**.
3. Note secondary topics in the summary; do not split into multiple categories.
