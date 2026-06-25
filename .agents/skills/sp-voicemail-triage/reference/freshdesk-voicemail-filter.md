# Freshdesk Voicemail Filter

The KSOnboarding queue (`group_id:159000485013`) receives **8x8 voicemail
notifications** and **non-voicemail** KSOnboarding mail (invoice concerns, ACH
updates, account threads, etc.). This skill triages **8x8 intake only**.

## Include (process)

**Subject must include** the phrase `New voicemail` (case-insensitive).

Typical subject:

```
New voicemail from {CALLER} via VENDOR RELATIONS
```

Prefixes or suffixes before/after the phrase are allowed as long as `New voicemail`
appears in the subject line.

## Exclude (skip)

Do **not** triage when the subject does **not** include `New voicemail`, even if:

- The body or conversation thread mentions `voicemail`, `voice mail`, or `VM`
- The body or thread mentions `ACH`, payment, billing, or invoice text
- Tags contain `voicemail` or related labels
- The subject contains `voicemail` alone but not the phrase `New voicemail`

Examples to **skip**:

- `Vendor Contact Information Is Incorrect` (body may mention unrelated terms)
- Invoice / SPM threads tagged `spm-invoice-concerns-reviewed`
- Subject `Voicemail follow-up` without `New voicemail`

Log skipped ticket IDs in the batch summary under **Skipped (non-voicemail)**.

## Freshdesk search (first pass)

```
group_id:159000485013 AND status:2 AND type:'KSOnboarding'
```

Paginate all pages, then **post-filter**: keep only tickets whose **subject**
includes `New voicemail`. Do not use body or thread text for inclusion.

## Outlook

**Folder:** {{employee_name}}'s Outlook subfolder **`VM`** (voicemail rule target).
Do not scan Inbox only — messages land in **VM** after the rule runs.

Same rule: **subject must include** `New voicemail` (case-insensitive).

Do not include messages that only mention voicemail, ACH, or payment in the
body or quoted thread while the subject lacks `New voicemail`.

Optional secondary signal after subject match: **audio attachment** (`.wav` or
`.mp3`) from 8x8/Teams — required for transcription. The email body does not
contain the spoken message; never use body keywords alone to include a message or
to classify.

## Transcription source

**Audio attachment (`.wav` or `.mp3`) only.** 8x8 voicemail notifications include
caller name, phone, and duration in the email/ticket body — **not** the spoken
voicemail. Download the audio file and transcribe before triage. Missing audio
attachment or failed STT → skip ticket (no Freshdesk writes).

## Classification guardrail

After intake, classify from **audio transcript only** — not from email body, ticket
description, conversation thread, or incidental `ACH` / `voicemail` tokens in HTML
boilerplate. Failed transcription → do not classify or route; leave ticket open.
