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

**Input:** SF Case (4046 Vendor Relations) or Outlook VM with voicemail transcript

> Hi, this is Tom with Summit Electric. We're interested in becoming a Vixxo
> service provider in Colorado. Please call 555-111-2222.

**Company vetting:** Salesforce Lead `00Qxx000001AbCd` — Company Summit Electric,
Status Open. No Siebel SP match.

**Routing:** Lead found → Salesforce **Lead Task** with transcript, **Case Task**
on the 4046 Case. No forward to recruitment when Lead is active. No Freshdesk.

See [salesforce-notes.md](salesforce-notes.md).

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

---

## Example 7 — Misroute: sourcing ask sent to AP Help (FD #57452)

**Source:** Freshdesk **#57452** / Outlook VM — misrouted by automated triage

**Transcript excerpt:**

> Hey, Max. It's Sean McCormick with the Restoration Group. Hope all is well.
> Just wanted to check in with you to see if you have any losses for us this
> week. My telephone is 908-632-7188. Thanks so much.

**Incorrect triage (what happened):**

| Field | Wrong value |
| --- | --- |
| Category | Payment Information |
| Route to | `aphelp@vixxo.com` |

**Why this is wrong:** The caller is **not** asking about payment, invoices, or
AP. They want to reach **sourcing / account team** about **work opportunities**
("losses for us this week") and named a Vixxo contact (Max).

**Correct triage:**

| Field | Value |
| --- | --- |
| Callback required | Recommended |
| Urgency | Normal |
| Category | Sourcing / Account Team |
| Sub-reason | SP check-in on work opportunities; asked to speak with sourcing contact (Max) |
| Caller name | Sean McCormick |
| Company | Restoration Group |
| Callback number | 908-632-7188 |
| Route to | `service.providermanagement@vixxo.com` |
| Review for {{employee_name}} | **Yes** — named Vixxo contact + sourcing/work-opportunity ask |
| Confidence | High |

**Correct actions:** Internal note with **Review for {{employee_name}}: Yes**,
forward to SPM (not AP Help), resolve Freshdesk after forward.

**Guardrail:** Sourcing / account-team intent in the **audio transcript**
overrides incidental billing/payment keywords in email boilerplate. See
[routing-actions.md](routing-actions.md) AP misroute guardrail.

---

## Example 8 — Salesforce 4046 Vendor Relations (primary SPM path)

**Source:** Salesforce Case **00008035** — subject
`New voicemail from CORREA,LUIS via VENDOR RELATIONS` (8x8 extension **4046**)

**Flow:**

1. 8x8 Email-to-Case creates the SF Case with `.wav` on the inbound EmailMessage.
2. Triage downloads ContentVersion audio, transcribes (faster-whisper).
3. Vets company (Gateway + SF Account/Lead/Contact).
4. Posts **Completed Case Task** with category, posture, route, transcript.
5. No Freshdesk ticket — KSOnboarding mailbox is retired.
6. If the same message is also in Outlook **VM**, skip a second forward; link
   Outlook id on the Task when known.

**Dedupe:** Do not create a second Case for the same 4046 voicemail. Re-runs
check for an existing `SP Voicemail Triage` Task on the Case.

---

## Example 9 — Circle K Help Desk on the SPS queue (account team, not SPS)

**Source:** Salesforce Case **00012047** — subject `Vixxo Voicemail` (Amazon
Connect / SP Support). Caller ANI **952-921-4916**, callback
**866-805-4357**. STT: Circle Clay / Circle Cree Maintenance asking an SP
to accept or reassign a store WO (FWKD `1-#########`).

**Correct category:** Customer / Circle K Help Desk

**Correct actions:**

1. Subject `Voicemail — Circle K Help Desk — {store / WO ask}`
2. Completed Task: route = Circle K account team (Gateway SR PM + Support
   if FWKD present)
3. Forward to those account-team recipients — **never**
   `service.providermanagement@vixxo.com`
4. Close the 4046 / SPS Case as Duplicate (wrong queue)

**Guardrail:** An SP who mentions a Circle K **store** is still an SP
voicemail (vet the contractor). Only the **Circle K Maintenance / Help
Desk** identity (or those ANIs) uses this path.

---

## Example 10 — Closed Lead (first-name-only + web identity)

**Source:** Salesforce Case **00011971** — `Vixxo Voicemail` (Amazon Connect).
ANI **+1 716-209-3703**. STT: Turnkey / Tom / onboarding issue.

**Miss:** Lead `Phone` is **716-216-4086**, not the ANI. A phone-only or
open-Lead-only search returns nothing.

**Correct vet:**

1. Company search `Turnkey` on **all** Leads (no Status / IsConverted filter).
2. Web search the ANI → **Thomas Kornacki**.
3. Re-query Lead `LastName = Kornacki`.
4. Match Closed Lead **00QTS00000h2lQH2AY** — Thomas Kornacki / TURNKEY
   PROPERTY MAINTENANCE LLC / Status Closed / unconverted.

**Routing:** Coverage / Onboarding. Lead Task on the Closed Lead. 4046 Case
Subject `Voicemail — Turnkey — onboarding`; close Case as Duplicate
(recruitment, not Crystal / SPS). Do **not** treat as “no Lead found.”
