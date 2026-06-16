---
name: sp-voicemail-triage-no-email
description: >-
  SP voicemail triage without sending email. Same intake, transcription,
  classification, company vetting, and callback decision as sp-voicemail-triage,
  but posts Freshdesk internal notes (with recommended routing address), optional
  Salesforce Lead notes, and resolves tickets — never forward_ticket,
  forward-mail-message, or other outbound email. Use when the user wants voicemail
  triage documented in Freshdesk without auto-forwarding to SPM, AP, COI, or
  recruitment mailboxes.
---

# SP Voicemail Triage — No Email

Work-only variant of **`sp-voicemail-triage`**. Same voicemail intake and Phase 1
triage; Phase 2 **does not send any email**.

## When to use

- "Triage voicemails without sending email" / "no-email voicemail triage"
- Document triage in Freshdesk for manual routing review
- Batch KSOnboarding voicemails when auto-forward is not desired

**Use parent `sp-voicemail-triage`** when forwards to SPM/AP/COI/recruitment should
send automatically.

**Use `sp-voicemail-triage-webhook`** for WAV webhook intake (forwards email unless
you invoke this skill's rules manually on the result).

## Difference from parent

| Step | Parent | This skill |
| --- | --- | --- |
| Transcribe / classify / vet | Yes | Yes |
| Freshdesk internal note | Yes | Yes (includes **recommended** route) |
| Email forward | Yes | **No** |
| Salesforce Lead note | Yes | Yes |
| Resolve Freshdesk | Yes | Yes |

See [reference/no-email-actions.md](reference/no-email-actions.md).

## Operating modes

Same as parent: **Batch**, **Single**, **Dry-run (opt-in)**.

**Write order:** internal note → Salesforce Lead note (if applicable) → resolve.
**No forward step.**

Phase 2 runs automatically when invoked (except dry-run).

## Intake (unchanged)

Follow parent rules — subject must **include** `New voicemail`:

- Freshdesk KSOnboarding queue — [../sp-voicemail-triage/reference/freshdesk-voicemail-filter.md](../sp-voicemail-triage/reference/freshdesk-voicemail-filter.md)
- Outlook inbox — subject includes `New voicemail` only

Do not triage items where voicemail or ACH appears only in body/thread.

## Phase 1 — Triage (automatic)

1. Acquire and transcribe — [../sp-voicemail-triage/SKILL.md](../sp-voicemail-triage/SKILL.md)
2. Classify — [../sp-voicemail-triage/reference/categories.md](../sp-voicemail-triage/reference/categories.md)
3. Callback — [../sp-voicemail-triage/reference/callback-rules.md](../sp-voicemail-triage/reference/callback-rules.md)
4. Company vetting — [../sp-voicemail-triage/reference/company-vetting.md](../sp-voicemail-triage/reference/company-vetting.md)

Compute the **recommended route** using parent [routing-actions.md](../sp-voicemail-triage/reference/routing-actions.md) — record it in the internal note only.

## Phase 2 — Document (automatic, no email)

```
Route progress — {ticket/message id}:
- [ ] Internal note posted (recommended route documented)
- [ ] Forward sent — SKIPPED (no-email skill)
- [ ] Salesforce Lead note added (if onboarding + Lead found)
- [ ] Freshdesk resolved (status 5 + cf_sp)
```

### Freshdesk internal note

Use [../sp-voicemail-triage/reference/freshdesk-internal-note-template.md](../sp-voicemail-triage/reference/freshdesk-internal-note-template.md) and add:

- **Recommended forward to:** `{address from routing table}`
- **Email forward sent:** No

### Blocked tools (never call)

- `forward_ticket`
- `forward-mail-message`
- `create_outbound_email`
- `send-mail-message` / `reply-mail-message`

### Resolve

Same as parent: `status: 5`, valid `type`, `custom_fields.cf_sp` (use `Unknown` when
SP not identified).

## Batch script

```bash
python .agents/skills/sp-voicemail-triage-no-email/scripts/batch_process_freshdesk.py
```

Parent Freshdesk REST helpers live under `../sp-voicemail-triage/scripts/`.

## Output format

Batch summary **Status** column: `noted` (not `routed`). **Route to** column still
shows the recommended address for manual follow-up.

```markdown
**Counts:** {n} triaged | {n} skipped (non-voicemail) | {n} noted (no email) | {n} failed
```

## Guardrails

- **Never send outbound email** from this skill — including "just this once" unless
  the user explicitly switches to parent `sp-voicemail-triage`.
- Work context only; same memory and outbound guardrails as parent except email
  forwards are permanently disabled here.
- Same-contact combine: one internal note covering all messages; still no email.

## Additional resources

| File | Purpose |
| --- | --- |
| [reference/no-email-actions.md](reference/no-email-actions.md) | Blocked vs allowed actions |
| [../sp-voicemail-triage/reference/](../sp-voicemail-triage/reference/) | Shared triage taxonomy and filters |
