# SP Voicemail Triage — Examples

## Example 1 — Payment callback required

**Input:** Audio transcript excerpt

> Hi, this is Mike Torres with Apex Mechanical. I'm calling about invoice
> 884521 for SR 12345678. We still haven't received payment and it's been
> over 45 days. Can someone please call me back at 555-867-5309? Thanks.

**Output (abbreviated):**

| Field | Value |
| --- | --- |
| Callback required | Yes |
| Urgency | High |
| Category | Payment Information |
| Sub-reason | Missing payment on invoice 884521 / SR 12345678 (~45 days) |
| Caller name | Mike Torres |
| Company | Apex Mechanical |
| Callback number | 555-867-5309 |
| Reference IDs | SR 12345678, Invoice 884521 |
| Suggested routing | AP Help Desk / SPM-Invoice Concerns |
| Route to | aphelp@vixxo.com |
| Confidence | High |

**Callback rationale:** Explicit "call me back"; unresolved missing payment
with invoice and SR cited.

---

## Example 2 — VixxoLink, no callback

**Input:** Email body auto-transcript from Exchange voicemail

> This is Sarah at CoolAir HVAC. I was able to reset my password through the
> forgot-password link. No need to call back. Just wanted to let you know
> I'm back in VixxoLink.

**Output (abbreviated):**

| Field | Value |
| --- | --- |
| Callback required | No |
| Urgency | Low |
| Category | VixxoLink Support |
| Sub-reason | Password reset — self-resolved |
| Caller name | Sarah |
| Company | CoolAir HVAC |
| Callback number | Not stated |
| Suggested routing | None — archive |
| Confidence | High |

**Callback rationale:** Caller explicitly said "no need to call back"; issue
self-resolved.

---

## Example 3 — Dispatch, critical

**Input:** Transcript

> This is James, BrightSign Services. I'm at the Starbucks on Main, SR
> 99887766. The manager is here and we can't get in — no access code was in
> the dispatch. Need a callback ASAP, 555-234-9900.

**Output (abbreviated):**

| Field | Value |
| --- | --- |
| Callback required | Yes |
| Urgency | Critical |
| Category | Service Request / Dispatch |
| Sub-reason | On-site, no access code for SR 99887766 |
| Caller name | James |
| Company | BrightSign Services |
| Callback number | 555-234-9900 |
| Reference IDs | SR 99887766 |
| Suggested routing | Service center / dispatch |
| Confidence | High |

**Callback rationale:** On-site blocking issue; "ASAP" + live coordination
needed.

---

## Example 4 — Onboarding, Salesforce Lead found

**Input:** Freshdesk KSOnboarding ticket with voicemail transcript

> Hi, this is Tom with Summit Electric. We're interested in becoming a Vixxo
> service provider in Colorado. Please call 555-111-2222.

**Company vetting:** Salesforce Lead `00Qxx000001AbCd` — Company Summit Electric,
Status Open. No Siebel SP match.

**Routing:** Lead found → internal note referencing Lead Id, Salesforce Task
note with transcript, resolve Freshdesk. No forward to recruitment.

---

## Example 5 — SR assistance

**Input:** Transcript cites SR 55443322

**Gateway:** PM `jane.doe@vixxo.com`, Support `support.team@vixxo.com`

**Forward:** To PM + Support; subject `55443322, Need Assistance`

**Freshdesk:** Internal note + forward + resolve (`status: 5`).

---

## Example 6 — Same contact, combined forward

**Input:** Two Outlook voicemails from +1 228-861-2196 (Jun 12 Donnie, Jun 15
Dottie), both Absolute Better Contracting.

**Combine:** One triage item; urgency elevated to High (repeat caller, no
callbacks reported).

**Forward:** Single `forward-mail-message` to `aphelp@vixxo.com` anchored on
the newest VM; `Comment` includes combined summary plus both transcript blocks.
