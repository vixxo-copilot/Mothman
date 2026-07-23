---
name: sf-case-email-sync
description: >-
  Syncs Microsoft 365 Outlook email threads and attachments onto open Salesforce
  Cases. Matches mail by SR number, Case number, or contact email. Use when the
  user asks to save emails to a Case, sync case correspondence, pull Outlook mail
  onto SF Cases, or batch-sync open Cases assigned to them.
---

# Salesforce Case Email Sync (M365 → SF)

Work-only skill. Read mail from Microsoft 365; write `.eml`, attachments, and
optional `EmailMessage` records to Salesforce Cases. **No outbound mail.**

## When to use

- "Save emails containing 1-6574285042 to SF 6911"
- "Sync my open case emails"
- "Pull Outlook thread onto Case 5784"
- Morning routine: scan Cases you own for new correspondence

## Guardrails

- **Dry-run default** for batch scans. Require explicit `--execute` or user approval.
- **Files-first** — always upload `.eml`; `EmailMessage` create is best-effort.
- **No outbound** — read-only from M365.
- Resolve Case owner live (`--owner-me` uses SF org username).
- Dedupe by `MessageIdentifier` and normalized file titles before upload.

## Quick commands

From repo root:

```bash
# Plan sync for one Case (default dry-run)
python .agents/skills/sf-case-email-sync/scripts/sync_case_emails.py \
  --case-number 6911 --sr 1-6574285042 \
  --output .tmp/sf-email-sync-6911-plan.json

# Execute after review
python .agents/skills/sf-case-email-sync/scripts/sync_case_emails.py \
  --case-number 6911 --sr 1-6574285042 --execute

# Batch: all open Cases assigned to you
python .agents/skills/sf-case-email-sync/scripts/sync_case_emails.py \
  --owner-me --days 14 \
  --output .tmp/sf-email-sync-batch-plan.json

# Verify coverage
python .agents/skills/sf-case-email-sync/scripts/verify_sync.py --case-number 6911

# Morning brief dry-run (compact summary)
python .agents/skills/sf-case-email-sync/scripts/morning_case_mail_scan.py \
  --days 7 --limit 15 --output .tmp/sf-email-sync-morning.json

# Account audit (audit-only — no Case writes)
python .agents/skills/sf-case-email-sync/scripts/audit_case_accounts.py \
  --owner-me --limit 15 --output .tmp/sf-account-audit.json

# Combined email sync plan + account audit
python .agents/skills/sf-case-email-sync/scripts/sync_case_emails.py \
  --owner-me --days 7 --account-audit --output .tmp/sf-email-sync-plan.json
```

## Workflow

### 1. Resolve scope

| Scope | Flags |
| --- | --- |
| Single Case | `--case-number 6911` or `--case-id 500...` |
| SR override | `--sr 1-6574285042` when SR not in Case text |
| Your open Cases | `--owner-me --status open --limit 25` |
| Owner override | `--owner-email user@vixxo.com` |

### 2. Dry-run plan

Run without `--execute`. Review JSON report:

- `matched_messages` — auto-sync candidates (high/medium confidence)
- `manual_review` — low-confidence hits; do not sync without operator OK
- `search_keys` — SR numbers, emails, subject tokens extracted from Case

Present a short table to the operator before execute.

### 3. Execute sync

Re-run with `--execute`. Per message the script:

1. Creates `EmailMessage` when `internetMessageId` not already on Case
2. Uploads `.eml` to Files (title without extension)
3. Uploads attachments (W-9, COI, PDFs) with dedupe

Use `--skip-email-message` when SF flow errors are expected; Files tab still
gets full `.eml`.

### 4. Verify

```bash
python .agents/skills/sf-case-email-sync/scripts/verify_sync.py --case-number 6911
```

Or `--owner-me` for a batch summary.

## Matching rules

Priority (first match wins):

1. **SR** `1-##########` in subject/body → high confidence
2. **Case number** in subject/body → high confidence
3. **Contact email** as sender + subject token overlap → medium confidence
4. Otherwise → `manual_review` (not auto-synced)

Default lookback: **30 days** (`--days`).

## Report format (operator summary)

```markdown
## SF Case Email Sync — {date}

**Mode:** dry-run | execute
**Cases scanned:** N

| Case | Subject | Match | Action |
| --- | --- | --- | --- |
| 6911 | CarMax window treatment | 10 msgs | would upload 10 .eml + 3 PDF |

**Manual review:** {count} low-confidence messages
**Errors:** {EmailMessage flow failures — files still uploaded}
```

## Prerequisites

- Salesforce CLI authenticated to `vixxo` org
- Microsoft 365 Graph token cached (same as `sp-voicemail-triage` / ms365-mcp)
- Node.js for `scripts/outlook_mail.mjs`

## Known limitations

- SF **Inbound/Outbound Email Automation** flow may reject some `EmailMessage`
  inserts (multi-recipient). Files upload succeeds; note in report.
- Graph `$search` is eventual-consistency; re-run if mail just arrived.
- Email-only matches without subject overlap go to manual review.

## Related skills

| Skill | Role |
| --- | --- |
| `sp-fd-sf-duplicate-bridge` | FD↔SF dupes and attachment gaps |
| `email-triage` | Inbox prioritization (not case archival) |
| `check-flagged-emails` | Flagged mail review |

## Additional resources

- Field mapping and SF flow notes: [reference.md](reference.md)
- Examples: [examples.md](examples.md)
