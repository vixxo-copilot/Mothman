# Freshdesk Internal Note Template

Post via `create_ticket_note` with `"private": true` (internal only — not visible
to the requester).

```markdown
**SP Voicemail Triage — {Freshdesk ticket # or email subject}**

**Processed:** {ISO date}
**Category:** {category} — {sub-reason}
**Callback required:** {Yes | Recommended | No} ({urgency})
**Caller:** {name or Not stated} | **Company:** {company or Not stated}
**Callback #:** {number or Not stated}
**Reference IDs:** {SR / invoice / SF Lead / none}
**Review for {{employee_name}}:** {Yes | No} — {reason when Yes}

---

**Company vetting**

| System | Match | ID |
| --- | --- | --- |
| Siebel / Gateway SP | {Yes/No/Possible} | {SP #} |
| Gateway / VixxoLink Customer | {Yes/No/Possible} | {Customer #} |
| JDE Vendor | {Yes/No/Unknown} | {Vendor #} |
| Salesforce Lead/Account/Contact | {Yes/No/Possible} | {SF Id} |
| Salesforce Case | {Yes/No/Possible} | {CaseNumber} |

**Entity posture:** {Known SP | Known Customer | Prospect | Unknown}

---

**Transcript**

{verbatim transcript}

---

**Routing action**

- **Forward to:** {recipients or None}
- **Subject:** {forward subject if SR branch}
- **Salesforce Lead Task:** {Lead Id + posted | N/A | failed}
- **Salesforce Case Task / Case:** {CaseNumber + posted | created | N/A | failed}
- **Disposition:** {Resolve | Open — reason}

---

**Summary:** {2–3 sentences}

**Callback rationale:** {cite transcript phrases}
```

Keep HTML out of the note body unless Freshdesk requires it for a specific field.
