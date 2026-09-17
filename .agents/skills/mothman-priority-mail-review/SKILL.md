---
name: mothman-priority-mail-review
description: >-
  Reviews Crystal Gagner's unread Outlook in Inbox plus Maria/Leslie/SPM,
  Kate/ORMB, and Invoices/Statements; ranks higher-priority asks; lists each
  box oldest to newest; writes a Mothman HTML report. Use when Crystal asks
  for priority mail review, unread boxes, Maria/Leslie/SPM, Kate/ORMB,
  Invoices/Statements, or a priority-mail HTML report. Also runs from
  mothman-good-morning Phase 2.
---

# Mothman Priority Mail Review

Work-only unread review of **four Outlook boxes** for **Crystal Gagner**.
Read-only. Do not send mail.

Default boxes:

| Box | Folder (match) |
| --- | --- |
| Inbox | well-known Inbox (messages in that folder only, not children) |
| Maria/Leslie/SPM | `Maria/Leslie/SPM & Adam` (under Michelle) |
| Kate/ORMB | `ORMB/ Kate` |
| Invoices/Statements | `AP / Invoices/Statements` |

## When to use

- "priority mail review" / "unread boxes" / "priority-mail HTML"
- "review unread in Inbox and Maria/Leslie/SPM, Kate/ORMB, Invoices/Statements"
- Good Morning Phase 2 cascade (automatic unless brief-only / skip mail)

## Deliverable

1. Run export + HTML (opens Chrome):

```bash
python .agents/skills/mothman-priority-mail-review/scripts/export_priority_mail.py \
  --json --open
```

2. Chat: unread totals, urgent/today counts, 2–4 first moves, HTML path.
   Do not dump the full HTML into chat.

Artifacts:

- `.tmp/mothman-priority-mail/priority-mail-YYYY-MM-DD.json`
- `.tmp/mothman-priority-mail/priority-mail-YYYY-MM-DD.html`

## Urgency

| Bucket | Meaning |
| --- | --- |
| `urgent` | Same-day / blocking Ask, high importance, payment/past-due, case transferred today |
| `today` | Clear Ask from last ~2 days |
| `this_week` | Aging Ask (up to ~3 weeks) |
| `fyi` | Thanks, CC, stale, no Ask |
| `archive` | Noise (2nd floor, Navan, Cursor, Affordable Solutions QuickBooks nags) |

Tags: `Ask` / `Decision` / `FYI`. Sort each box **oldest → newest**.

## Extra folders

Crystal can name more boxes in the prompt. Pass:

```bash
python .agents/skills/mothman-priority-mail-review/scripts/export_priority_mail.py \
  --json --open --extra-folder "New SP Approvals"
```

`--extra-folder` currently helps **match** a default box if the display name
changed. To add a fifth box, extend `BOX_SPECS` in
`scripts/graph_unread_mail.mjs`.

## Guardrails

- Microsoft 365 Graph via the existing MCP token cache (same as case-mail sync).
- No outbound send/reply.
- Collapse invoice-spam groups in HTML; keep the full oldest→newest list.

## Trigger phrases

priority mail review, unread boxes, Maria/Leslie/SPM, Kate/ORMB,
Invoices/Statements, priority-mail HTML, review my four mail boxes
