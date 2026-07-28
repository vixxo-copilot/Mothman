# SF Case Email Sync — Examples

## Example 1 — SR thread to Case (Case 6911)

**Request:** Save emails containing `1-6574285042` to SF 6911.

```bash
python .agents/skills/sf-case-email-sync/scripts/sync_case_emails.py \
  --case-number 6911 --sr 1-6574285042 \
  --output .tmp/sf-email-sync-6911-plan.json

python .agents/skills/sf-case-email-sync/scripts/sync_case_emails.py \
  --case-number 6911 --sr 1-6574285042 --execute

python .agents/skills/sf-case-email-sync/scripts/verify_sync.py --case-number 6911
```

**Expected:** 10 `.eml` files + COI/W-9 PDFs on Files tab; EmailMessages for
most thread messages (some may fail SF flow — files still present).

## Example 2 — Vendor reply by email address (Case 5784)

Case subject references Economy Lock; contact email `economylock@yahoo.com`.

```bash
python .agents/skills/sf-case-email-sync/scripts/sync_case_emails.py \
  --case-number 5784 --days 7 --execute
```

Matching uses contact email + subject token overlap.

## Example 3 — Batch dry-run for open Cases

```bash
python .agents/skills/sf-case-email-sync/scripts/sync_case_emails.py \
  --owner-me --days 14 --limit 25 \
  --output .tmp/sf-email-sync-batch-plan.json
```

Review plan JSON, then execute selected Cases individually or approve batch:

```bash
python .agents/skills/sf-case-email-sync/scripts/sync_case_emails.py \
  --case-number 5732 --execute
```

## Example 4 — Files only (skip EmailMessage flow)

When SF automation rejects EmailMessage inserts:

```bash
python .agents/skills/sf-case-email-sync/scripts/sync_case_emails.py \
  --case-number 6911 --sr 1-6574285042 --execute --skip-email-message
```

## Example 5 — EOD automation batch

Daily Cursor automation (4 PM America/Chicago). Dry-run first, then execute
high/medium matches; leave `manual_review` for the operator.

```bash
python .agents/skills/sf-case-email-sync/scripts/eod_case_mail_sync.py \
  --days 1 --limit 25
```

Reports:

- `.tmp/sf-email-sync-eod-{stamp}-plan.json` — dry-run plan
- `.tmp/sf-email-sync-eod-{stamp}-execute.json` — execute results (when matches)
- `.tmp/sf-email-sync-eod-{stamp}.json` — operator summary

Dry-run only (no uploads):

```bash
python .agents/skills/sf-case-email-sync/scripts/eod_case_mail_sync.py --dry-run-only
```

## Operator summary template

```markdown
## SF Case Email Sync — 2026-07-23

**Case 6911** — CarMax window treatment / Mechoshade onboarding
- Matched: 10 messages (SR 1-6574285042)
- Uploaded: 10 .eml + 3 PDFs
- EmailMessage: 6 created, 4 flow errors (files OK)

Case: https://vixxo.my.salesforce.com/500TS00000p2Ry4YAE
```
