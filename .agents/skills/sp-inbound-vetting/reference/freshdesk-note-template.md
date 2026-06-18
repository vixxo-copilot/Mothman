# Freshdesk Internal Note Template

Post via `create_ticket_note` with `"private": true`.

```markdown
**SP Inbound Vetting — Freshdesk #{ticket_id}**

**Processed:** {ISO date}
**Inbox / queue:** {aphelp@vixxo.com | ksonboarding@vixxo.com | spm-invoice-concerns}
**Requester:** {name} <{email}>
**Contact name searched:** {contact name from requester}
**Extracted company:** {company or Not stated}
**Reference IDs:** {SP # / SR / invoice / none}

---

**Vetting results**

| System | Match | Identifier |
| --- | --- | --- |
| Gateway SP | {Yes/No/Possible} | {SP # — display name; include similarity score when Possible} |
| VixxoLink SP | {Yes/No/Possible} | {SP # — name from SR} |
| Salesforce Lead | {Yes/No/Possible} | {Lead Id — Status; score when Possible} |
| Salesforce Case | {Yes/No/Possible} | {Case # — Status; score when Possible} |
| Salesforce Account | {Yes/No/Possible} | {Account Id} |

**Entity posture:** {Known SP | Possible SP (Gateway) | Prospect | Open SF Case | Unknown}
**Confidence:** {High | Medium | Low}

Use **Possible** in the Match column when `match_type` is `fuzzy` (similar name,
not exact email or normalized company equality). List alternate SP or Lead
candidates under **Open questions** when `alternates` or `lead_alternates` are
present.

---

**Freshdesk field update**

- **cf_sp set to:** {value or skipped — reason}
- **Tags added:** sp-vetted, …

---

**Salesforce notes**

- **Lead Task:** {Lead Id — posted | N/A | failed + reason}
- **Case Task:** {Case Id — posted | N/A | failed + reason}

---

**Summary:** {2–3 sentences — what was found, what is still unknown}

**Open questions:** {ambiguous name matches, missing company, etc.}
```

Keep HTML out of the note body unless Freshdesk requires it.
