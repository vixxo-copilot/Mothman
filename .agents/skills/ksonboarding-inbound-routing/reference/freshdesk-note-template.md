# Freshdesk Internal Note Template — KS Onboarding routing

Post via `create_ticket_note` with `"private": true`.

```markdown
**KS Onboarding Inbound Routing — Freshdesk #{ticket_id}**

**Processed:** {ISO date}
**Queue:** ksonboarding@vixxo.com (KSOnboarding)
**Requester:** {name} <{email}>
**Subject:** {subject}

---

**Classification**

| Field | Value |
| --- | --- |
| **Outcome** | {COIs | VixxoLink Support | Invoice Support | KSOnboarding retained} |
| **Type change** | KSOnboarding → {new type | none} |
| **Signals** | {keywords, attachment names, COI/portal/statement indicators} |
| **Ambiguity** | {none | describe if retained due to weak signals} |

---

**Vetting results**

| System | Match | Identifier |
| --- | --- | --- |
| Gateway SP | {Yes/No/Possible} | {SP # — display name} |
| VixxoLink SP | {Yes/No/Possible} | {SP # — name from SR} |
| Salesforce Lead | {Yes/No/Possible} | {Lead Id — Status} |
| Salesforce Case | {Yes/No/Possible} | {Case # — Status} |

**Entity posture:** {Known SP | Possible SP | Prospect | Unknown}
**Confidence:** {High | Medium | Low}

---

**Field updates**

- **cf_sp:** {set to … | left blank — uncertain | skipped — existing value}
- **cf_type_of_request:** {Follow up on an Unpaid Invoice | n/a}
- **Tags added:** ks-inbound-routed, …

---

**Summary:** {2–3 sentences — why this type, what vetting found}

**Open questions:** {ambiguous classification, missing SP identity, client-portal flag, etc.}
```

Keep HTML out of the note body unless Freshdesk requires it.
