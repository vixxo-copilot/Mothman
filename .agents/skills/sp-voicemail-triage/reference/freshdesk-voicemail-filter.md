# Freshdesk Voicemail Filter

The KSOnboarding queue (`group_id:159000485013`) receives **8x8 voicemail
notifications** and **non-voicemail** KSOnboarding mail (invoice concerns, ACH
updates, account threads, etc.). This skill triages **8x8 intake only**.

## Include (process)

**Subject must begin with** `New voicemail` (case-insensitive; ignore leading
whitespace).

Typical subject:

```
New voicemail from {CALLER} via VENDOR RELATIONS
```

That is the 8x8 extension notification — the only Freshdesk shape this skill
handles.

## Exclude (skip)

Do **not** triage when the subject does **not** start with `New voicemail`, even if:

- The body or conversation thread mentions `voicemail`, `voice mail`, or `VM`
- The body or thread mentions `ACH`, payment, billing, or invoice text
- Tags contain `voicemail` or related labels
- The subject contains `voicemail` mid-string but does not **begin** with
  `New voicemail`

Examples to **skip**:

- `Vendor Contact Information Is Incorrect` (body may mention unrelated terms)
- Invoice / SPM threads tagged `spm-invoice-concerns-reviewed`
- Replies or forwards where `voicemail` appears only in thread history

Log skipped ticket IDs in the batch summary under **Skipped (non-voicemail)**.

## Freshdesk search (first pass)

```
group_id:159000485013 AND status:2 AND type:'KSOnboarding'
```

Paginate all pages, then **post-filter**: keep only tickets whose **subject**
starts with `New voicemail`. Do not use body or thread text for inclusion.

## Outlook

Same rule: **subject must begin with** `New voicemail` (case-insensitive).

Do not include messages that only mention voicemail, ACH, or payment in the
body or quoted thread while using a different subject line.

Optional secondary signal after subject match: audio attachment (`.wav`) from
8x8/Teams — never use body keywords alone to include a message.

## Classification guardrail

After intake, classify from **transcript / audio content only** — not from
incidental `ACH` or `voicemail` tokens in email footers, quoted threads, or HTML
boilerplate. Audio-only 8x8 notifications with no spoken transcript default to
**General Inquiry** → `service.providermanagement@vixxo.com`.
