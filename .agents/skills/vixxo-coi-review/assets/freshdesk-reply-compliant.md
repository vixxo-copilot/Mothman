# Freshdesk Public Reply — COI Accepted (Mode B)

Use this skeleton when posting a `conversations_manage create_reply` on a COI ticket whose certificate is fully compliant. Freshdesk preserves the original subject and threads to the original requester — **do not include a Subject header here, and do not BCC `COI@vixxo.com`**.

---

Hello {Service Provider Contact First Name or "Team"},

Thank you for submitting the Certificate of Insurance dated {COI Effective Date} on behalf of {Service Provider Name}. We have reviewed the certificate against Vixxo's minimum insurance requirements and confirm that it has been **accepted**. No further action is required at this time.

Please plan to send a renewal certificate prior to the policy expiration date of **{Earliest Policy Expiration Date}** to avoid any lapse in coverage on file.

If you have any questions, please reply to this thread.

Thank you,
Vixxo Risk & Compliance

---

## Notes for the operator

- Confirm with the operator before applying status `Resolved` (4) or `Closed` (5). The two are not interchangeable in this Freshdesk instance — Resolved keeps the ticket appealable for a period; Closed is final.
- If the COI is accepted but the renewal date is within 30 days, consider also adding tag `coi-renewal-due-soon` so the queue can flag it for follow-up.
- **Compliant outcome ticket-field flip (mandatory):** the `tickets_manage update` for this outcome must include `"type": "Account Update"` and `"custom_fields": {"cf_vixxo_link_type_of_request": "Profile Update"}` (verified key, 2026-05-04). Do **not** set `cf_type_of_request` — that field belongs to the Invoice Support form and stays null on Account Update tickets. Tags on a Freshdesk update **replace** the full set, so include `coi` and `risk-compliance-routed` alongside the new tags in the same call.
- **Siebel handoff private note (mandatory):** after this public reply is posted, post a second internal `conversations_manage create_note` with this exact text — it is the operational handoff to whoever uploads the COI to Siebel:

  > This COI was confirmed as compliant, please upload to Siebel and update Additional SC Info tab.
