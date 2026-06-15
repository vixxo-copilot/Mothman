# Freshdesk Public Reply — COI Deficiency Notice (Mode B)

Use this skeleton when posting a `conversations_manage create_reply` on a COI ticket that has deficiencies. Freshdesk preserves the original ticket's subject line and threads the reply to the original requester automatically — **do not include a Subject header here, and do not BCC `COI@vixxo.com`** (it forwards back into Freshdesk and creates a circular reference).

Fill in placeholders, and only include bullets for items that are actually deficient. Remove sections that don't apply.

---

Hello {Service Provider Contact First Name or "Team"},

Thank you for submitting the Certificate of Insurance dated {COI Effective Date} on behalf of {Service Provider Name}. Upon review against Vixxo's minimum insurance requirements, the following items must be corrected or clarified before the certificate can be accepted:

- {Deficiency 1 — phrased as a specific, actionable request, with form numbers, exact wording, or limits cited verbatim where applicable}
- {Deficiency 2}
- {Deficiency 3}
- {…}

Please have your broker issue an updated Certificate of Insurance reflecting the items above and reply to this email with the corrected certificate attached. The Certificate Holder should be listed exactly as:

> Vixxo Corporation
> 7580 N. Dobson Road, Suite 201
> Scottsdale, AZ 85256

If you have any questions regarding any of these requirements, please reply to this thread and we will be happy to clarify.

Thank you for your prompt attention to this matter.

Sincerely,
Vixxo Risk & Compliance

---

## Why "reply to this email" instead of "send to COI@vixxo.com"

The `COI@vixxo.com` address forwards into Freshdesk as a new ticket, which would split the conversation across two tickets and break the audit trail on this one. Asking the SP to reply to the existing thread keeps the resubmitted COI on the same ticket and preserves history.

## Why the deficient outcome resolves the ticket (not Pending)

Per the SKILL outcomes table, after this reply is posted the ticket is set to **Resolved (`status: 4`)**, not Pending. Freshdesk auto-reopens a Resolved ticket the moment the customer (the SP) replies, so the corrected COI lands on this same ticket and the queue does not have to babysit a Pending follow-up. Keep the closing language ("reply to this email with the corrected certificate attached") exactly as written — it pairs with the auto-reopen behavior. Do not rewrite it to "open a new ticket" or "send a fresh COI to COI@vixxo.com."

## Common deficiency phrasings (copy-paste ready)

- *Please add the full Vixxo Additional Insured wording to the Description of Operations. The required language reads: "Vixxo Corporation, its subsidiaries, affiliates, related entities and their officers, officials, employees, volunteers (collectively, 'Vixxo'), its customers, the owner, operator and, if required, mortgagee of any site where SP performs Services are included as Additional Insured…" (full text per the Vixxo standard).*
- *Please reference Additional Insured endorsement **CG 20 10 04/13** (or equivalent) for ongoing operations on the General Liability policy.*
- *Please reference Additional Insured endorsement **CG 20 37 04/13** (or equivalent) for completed operations on the General Liability policy.*
- *Please reference Additional Insured endorsement **CA 20 48 10/13** (or equivalent) on the Automobile Liability policy.*
- *Please confirm in writing that the General Liability policy is **primary and non-contributory** with respect to any other insurance available to Vixxo.*
- *Please confirm Waiver of Subrogation applies in favor of the Additional Insureds on the **General Liability**, **Automobile Liability**, and **Workers' Compensation / Employers' Liability** policies.*
- *Please reference **30 days' Notice of Cancellation** in the Description of Operations.*
- *Please update the Certificate Holder to read exactly: Vixxo Corporation, 7580 N. Dobson Road, Suite 201, Scottsdale, AZ 85256.*
- *The {coverage line} policy expired on {date}. Please provide a renewal certificate.*
- *The {limit field} on the {coverage line} policy is blank. Please provide a certificate showing the applicable limit.*
- *The Workers' Compensation section indicates an executive officer/member exclusion. Please provide an explanation under Description of Operations.*
