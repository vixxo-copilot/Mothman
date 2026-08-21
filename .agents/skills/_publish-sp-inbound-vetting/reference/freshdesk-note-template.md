# Freshdesk Internal Note Template

Use for **AP Help (`aphelp`)** — Freshdesk-primary queue. SF-primary queues
(ksonboarding, COI, spm) document via Salesforce Case Tasks per
[salesforce-notes.md](salesforce-notes.md).

Post via `create_ticket_note` with `"private": true`.

```markdown
**SP Inbound Vetting — Freshdesk #{ticket_id}**

**Processed:** {ISO date}
**Inbox / queue:** {aphelp@vixxo.com}
**Requester:** {name} <{email}>
**Contact name searched:** {contact name from requester}
**Extracted company:** {company or Not stated}
**Reference IDs:** {SP # / SR / invoice / none}

---

**Vetting results**

| System | Match | Identifier |
| --- | --- | --- |
| Gateway SP | {Yes/No/Possible} | {SP # — display name} |
| VixxoLink SP | {Yes/No/Possible} | {SP # — name from SR} |
| Salesforce Lead | {Yes/No/Possible} | {Lead Id — Status} |
| Salesforce Case | {Yes/No/Possible} | {Case # — Status} |
| Salesforce Account | {Yes/No/Possible} | {Account Id} |

**Entity posture:** {Known SP | Prospect | Open SF Case | Unknown}

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
