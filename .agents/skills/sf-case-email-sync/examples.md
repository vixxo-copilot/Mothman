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

## Operator summary template

```markdown
## SF Case Email Sync — 2026-07-23

**Case 6911** — CarMax window treatment / Mechoshade onboarding
- Matched: 10 messages (SR 1-6574285042)
- Uploaded: 10 .eml + 3 PDFs
- EmailMessage: 6 created, 4 flow errors (files OK)

Case: https://vixxo.my.salesforce.com/500TS00000p2Ry4YAE
```
