# Freshdesk Queues — SP Inbound Vetting

Batch intake pulls **Open, untouched** tickets from the queues below.
**Untouched** means the ticket is **not** tagged `sp-vetted` (unless the
operator passes `re-vet`).

Tickets may already carry tags from sibling skills (for example
`spm-invoice-concerns-reviewed` from `vixxo-spm-invoice-concerns`). Those
tags do **not** satisfy SP identity vetting — run this skill until
`sp-vetted` is present.

## Queue registry

| Queue key | Freshdesk folder / view | Search filter | Inbox label (notes) |
| --- | --- | --- | --- |
| `ksonboarding` | KS Onboarding | `group_id:159000485013 AND status:2 AND type:'KSOnboarding'` | `ksonboarding@vixxo.com` |
| `invoice-concerns` | **SPM - Invoice Concerns** | `group_id:159000485013 AND status:2 AND type:'Invoice Support'` | `spm-invoice-concerns` |
| `aphelp` | AP Help (mailbox gate) | `group_id:159000485013 AND status:2` + recipient `aphelp@vixxo.com` | `aphelp@vixxo.com` |
| `all` | Union of the three | Dedupe by ticket id | Per-ticket source |

### SPM - Invoice Concerns (confirmed)

The Freshdesk sidebar folder **SPM - Invoice Concerns** maps to Open SPM
tickets with type **`Invoice Support`** in group **`159000485013`**. This
matches the filter confirmed in `vixxo-spm-invoice-concerns` (2026-05-06).

```text
group_id:159000485013 AND status:2 AND type:'Invoice Support'
```

No mailbox recipient gate is required for this queue — the view/type filter
is sufficient.

## Batch selection rules (every queue)

1. Run the queue search filter; paginate all pages.
2. **Skip** tickets tagged `sp-vetted` (unless `re-vet`).
3. **Skip** subject contains `New voicemail` (unless `include voicemails`).
4. For `aphelp` only: apply the recipient gate from [intake.md](intake.md).
5. **Order:** oldest-first by `created_at` unless the user asks newest-first.
6. **Dedupe:** when running `all`, merge by ticket id before processing.

## Sibling skill boundaries

| Skill | Owns |
| --- | --- |
| **`sp-inbound-vetting`** (this skill) | Gateway SP + Salesforce identity lookup; internal note; `cf_sp`; `sp-vetted` + posture tags; SF Lead/Case Tasks |
| **`vixxo-spm-invoice-concerns`** | Invoice/payment Gateway analysis; proposed resolution; `spm-invoice-concerns-reviewed` and invoice workflow tags |
| **`vixxo-freshdesk-invoice-review`** | AP Help Desk No Agent queue; bucket classification; provider reply drafting |
| **`sp-voicemail-triage`** | `New voicemail` KSOnboarding items |

This skill **does not** classify invoices, draft provider replies, change
ticket status, or overwrite invoice-concerns workflow tags. It **does** complete
SP identity vetting on open Invoice Concerns items that lack `sp-vetted`.

## Script entry points

```bash
# Dry-run one queue
python .agents/skills/sp-inbound-vetting/scripts/dry_run_batch.py --queue invoice-concerns

# Live run (vet + write) one queue
python .agents/skills/sp-inbound-vetting/scripts/live_run_batch.py --queue invoice-concerns

# All queues
python .agents/skills/sp-inbound-vetting/scripts/live_run_batch.py --queue all
```

Legacy scripts `dry_run_ksonboarding*.py` and `live_run_ksonboarding.py`
remain aliases for `--queue ksonboarding`.
