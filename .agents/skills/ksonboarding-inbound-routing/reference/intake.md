# Intake — KS Onboarding email routing

Pull Open **non-voicemail** email in the Freshdesk KS Onboarding queue for
content-based reclassification.

## Queue filter

```
group_id:159000485013 AND status:2 AND type:'KSOnboarding'
```

- SPM group `159000485013`
- Status `2` = Open
- Type must still be `KSOnboarding` (not yet routed)

Paginate all pages (`search_tickets` or REST `/api/v2/search/tickets`).

## Voicemail exclusion (mandatory)

After search, **drop** any ticket whose subject includes `New voicemail`
(case-insensitive).

Voicemail routing belongs to **`sp-voicemail-triage`**, not this skill.

Optional body-only voicemail mentions without that subject stay **in scope**
here.

## Dedupe and exclusions

| Condition | Action |
| --- | --- |
| Tagged `ks-inbound-routed` | Skip — unless user says `re-route` or names ticket id |
| Subject includes `New voicemail` | Skip — use `sp-voicemail-triage` |
| `type` is not `KSOnboarding` | Skip — already routed or created in another queue |
| User names a single ticket id | Process that ticket even if tagged (treat as re-route) |

**Ordering:** oldest-first by `created_at` unless the user asks newest-first.

## Single-item intake

Accept:

- Freshdesk ticket id or URL
- Pasted subject + body when previewing one item

When only Outlook mail exists (no Freshdesk ticket), classify and present the
packet; skip Freshdesk writes unless the user links or creates a ticket id.

## Recipient confirmation

KS Onboarding type-filtered pulls do **not** require a recipient gate — tickets
already landed in the KSOnboarding queue via `ksonboarding@vixxo.com` routing.

When reviewing a broad SPM search, keep only items sent to
`ksonboarding@vixxo.com` (case-insensitive) using the same recipient checks as
[../../sp-inbound-vetting/reference/intake.md](../../sp-inbound-vetting/reference/intake.md).
