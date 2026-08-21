# Freshdesk Voicemail Filter (QSIAP only)

Freshdesk remaining voicemail intake for this skill is **QSIAP AP only**
(`qsiap@vixxo.com`). SPM Vendor Relations voicemails on **8x8 extension 4046**
are triaged in **Salesforce**, not Freshdesk — see
[salesforce-4046-voicemail.md](salesforce-4046-voicemail.md).

**Retired:** Freshdesk `type:'KSOnboarding'` / `ksonboarding@vixxo.com` is not
an active mailbox. Do **not** search that queue for default batch runs.

## Include (process) — QSIAP

**Subject must include** the phrase `New voicemail` (case-insensitive).

Typical subject:

```
New voicemail from {CALLER} via ACCOUNTS PAYABLE
```

Prefixes or suffixes before/after the phrase are allowed as long as `New voicemail`
appears in the subject line.

**QSIAP gate (required):** after subject match, keep only tickets whose
to/cc/support_email/description/conversations contain `qsiap@vixxo.com`.

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
- Any open `type:'KSOnboarding'` ticket (out of scope for this skill)

Log skipped ticket IDs in the batch summary under **Skipped (non-voicemail)**.

## Freshdesk search (QSIAP discovery)

Type-sliced SPM open searches (Freshdesk caps force slices):

```
group_id:159000485013 AND status:2 AND type:'Invoice Support'
group_id:159000485013 AND status:2 AND type:null
```

Paginate, then **post-filter**: subject includes `New voicemail` **and** QSIAP
recipient gate. Full rules: [qsiap-voicemail.md](qsiap-voicemail.md).

## Outlook

**Folder:** {{employee_name}}'s Outlook subfolder **`VM`** (voicemail rule target).
Do not scan Inbox only — messages land in **VM** after the rule runs.

Same rule: **subject must include** `New voicemail` (case-insensitive).

4046 Vendor Relations messages in Outlook often duplicate SF Email-to-Case —
prefer the open **SF Case** when both exist
([salesforce-4046-voicemail.md](salesforce-4046-voicemail.md)).

Do not include messages that only mention voicemail, ACH, or payment in the
body or quoted thread while the subject lacks `New voicemail`.

Optional secondary signal after subject match: **audio attachment** (`.wav` or
`.mp3`) from 8x8 — required for transcription. The email body does not
contain the spoken message; never use body keywords alone to include a message or
to classify.

## Transcription source

**Audio attachment (`.wav` or `.mp3`) only.** 8x8 voicemail notifications include
caller name, phone, and duration in the email/ticket body — **not** the spoken
voicemail. Download the audio file and transcribe before triage. Missing audio
attachment or failed STT → skip item (no writes).

## Classification guardrail

After intake, classify from **audio transcript only** — not from email body, ticket
description, conversation thread, or incidental `ACH` / `voicemail` tokens in HTML
boilerplate. Failed transcription → do not classify or route; leave item unchanged.
