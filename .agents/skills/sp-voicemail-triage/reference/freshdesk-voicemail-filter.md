# Freshdesk Voicemail Filter (Legacy)

**Optional.** Primary intake is Outlook extension **4046** — see
[outlook-voicemail-intake.md](outlook-voicemail-intake.md).

The KSOnboarding queue (`group_id:159000485013`) receives **8x8 voicemail
notifications** and **non-voicemail** KSOnboarding mail (invoice concerns, ACH
updates, account threads, etc.). Include this queue only when running
`batch_process_all.py --freshdesk` or when the user explicitly requests Freshdesk
coverage.

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

## Outlook (primary)

See [outlook-voicemail-intake.md](outlook-voicemail-intake.md). Extension **4046**,
subject `via VENDOR RELATIONS`, sender `8x8.com`, audio attachment required.

## Transcription source

**Audio attachment (`.wav` or `.mp3`) only.** 8x8 voicemail notifications include
caller name, phone, and duration in the email/ticket body — **not** the spoken
voicemail. Download the audio file and transcribe before triage. Missing audio
attachment or failed STT → skip item (no writes).

## Classification guardrail

After intake, classify from **audio transcript only** — not from email body, ticket
description, conversation thread, or incidental `ACH` / `voicemail` tokens in HTML
boilerplate. Failed transcription → do not classify or route; leave item unchanged.
