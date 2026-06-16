# Freshdesk Voicemail Filter

The KSOnboarding queue (`group_id:159000485013`) receives **voicemail notifications**
and **non-voicemail** KSOnboarding mail (invoice concerns, account updates, etc.).
This skill processes **voicemail items only**.

## Include (process)

A Freshdesk ticket is in scope when **any** of these match:

| Signal | Rule |
| --- | --- |
| **Tag** | Tag list contains `voicemail` (case-insensitive) |
| **Subject** | Contains `voicemail`, `voice mail`, or `new voice message` (case-insensitive) |
| **Body** | 8x8 notification text: `New voicemail from` or `has a new voicemail` |

Typical subject: `New voicemail from {CALLER} via VENDOR RELATIONS`

## Exclude (skip)

Do **not** triage with this skill when none of the include signals match. Examples
seen in the same queue:

- `Vendor Contact Information Is Incorrect`
- Invoice / SPM concern threads tagged `spm-invoice-concerns-reviewed`
- General onboarding email without voicemail subject or 8x8 body

Log skipped ticket IDs in the batch summary under **Skipped (non-voicemail)**.

## Freshdesk search (first pass)

```
group_id:159000485013 AND status:2 AND type:'KSOnboarding'
```

Paginate all pages, then **post-filter** with the rules above. Do not rely on
search alone — some voicemails have empty tag lists.

## Outlook (unchanged)

Inbox candidates still require voicemail subject patterns (`Voice Mail`, `Voicemail`,
`New Voice Message`, `VM from`) or an audio attachment plus voicemail subject.
