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

---

**Company vetting**

| System | Match | ID |
| --- | --- | --- |
| Siebel / Gateway SP | {Yes/No/Possible} | {SP #} |
| Gateway / VixxoLink Customer | {Yes/No/Possible} | {Customer #} |
| JDE Vendor | {Yes/No/Unknown} | {Vendor #} |
| Salesforce Lead/Account | {Yes/No/Possible} | {SF Id} |

**Entity posture:** {Known SP | Known Customer | Prospect | Unknown}

---

**Transcript**

{verbatim transcript}

---

**Routing action**

- **Forward to:** {recipients or None}
- **Subject:** {forward subject if SR branch}
- **Salesforce Lead note:** {Lead Id + yes/no/pending}
- **Disposition:** {Resolve | Open — reason}

---

**Summary:** {2–3 sentences}

**Callback rationale:** {cite transcript phrases}
```

Keep HTML out of the note body unless Freshdesk requires it for a specific field.
