---
name: sp-voicemail-triage
description: >-
  Auto-transcribes and triages service-provider voicemails from the Freshdesk
  KSOnboarding queue and the user's Outlook inbox. Vets company names against
  Siebel, Gateway, JDE, and Salesforce; classifies the call reason; determines
  callback need; posts Freshdesk internal notes; resolves tickets; adds
  Salesforce Lead notes; and automatically forwards to
  service.providermanagement@vixxo.com, aphelp@vixxo.com, COI@vixxo.com,
  spm-recruitment@vixxo.com, or Gateway SR PM/support staff. Combines multiple
  voicemails from the same contact into one forward with a unified summary. Use when
  the user asks to process SP voicemails, triage the voicemail queue, transcribe
  voicemails,   or route onboarding, billing, COI, or SR callback mail. For triage
  without outbound email, use sibling skill `sp-voicemail-triage-no-email`. For HTTP
  webhook + WAV intake, use sibling skill `sp-voicemail-triage-webhook`. For
  scheduled automation with Whisper transcription and no external vetting, use
  sibling skill `sp-voicemail-triage-fast`.
---

# SP Voicemail Triage

Work-only workflow for **service provider (SP) voicemails**. Default run:
**auto-transcribe and triage all voicemails** in the Freshdesk **KSOnboarding**
queue and {{employee_name}}'s **Outlook inbox**, vet the company across Vixxo
systems, classify the reason, decide callback need, then **automatically**
post internal notes, forward, add Salesforce Lead notes, and resolve tickets.

## When to use

- "Process SP voicemails" / "run voicemail triage" / "triage the queue"
- "Transcribe voicemails in KSOnboarding and my inbox"
- Single voicemail: attach audio, paste transcript, or point at a ticket/message
- **Webhook + WAV:** use **`sp-voicemail-triage-webhook`** (not this skill)
- **No outbound email:** use **`sp-voicemail-triage-no-email`**
- **Scheduled automation / fast batch:** use **`sp-voicemail-triage-fast`**

## Operating modes

| Mode | Trigger | Behavior |
| --- | --- | --- |
| **Batch (default)** | "Process voicemails" without a single item | Scan both sources; full pipeline on every candidate |
| **Single** | One ticket, message, or attachment | Full pipeline on one item |
| **Dry-run (opt-in)** | User says "dry-run" / "preview only" | Triage + vet only; no writes |

**Phase 1 — Triage (automatic):** transcribe, classify, vet company, decide
callback.

**Phase 2 — Route (automatic):** post Freshdesk internal notes, forward
mail/tickets, add Salesforce Lead notes, resolve Freshdesk. No separate approval
step — {{employee_name}} has pre-authorized these actions for this skill.

**Write order (every item):** internal note → forward → Salesforce Lead note (if
applicable) → resolve Freshdesk.

## Default batch sources

Process **both** on every batch run unless the user narrows scope:

### 1. Freshdesk — KSOnboarding queue (voicemail only)

```
group_id:159000485013 AND status:2 AND type:'KSOnboarding'
```

Then **post-filter** to voicemail items only — see
[reference/freshdesk-voicemail-filter.md](reference/freshdesk-voicemail-filter.md).

**In scope:** subject **includes** `New voicemail` (case-insensitive).

**Out of scope:** everything else in the KSOnboarding queue — including tickets
whose body or thread mentions `voicemail`, `ACH`, payment, or billing but whose
subject does not include `New voicemail`. Log skipped IDs; do not triage.

- SPM group `159000485013`; ticket type `KSOnboarding`.
- Use `search_tickets`; paginate all pages; apply voicemail filter.
- For each in-scope ticket: `get_ticket`, conversations, attachments; download and
  transcribe the **audio attachment** (`.wav` or `.mp3`, required). The notification
  **email body does not contain the spoken message** — only caller metadata and
  routing boilerplate.

**Batch REST script (Freshdesk-only):** When running
`scripts/batch_process_freshdesk.py`, the script downloads the ticket **audio
attachment** (`.wav` or `.mp3`) and transcribes via **local faster-whisper**
(no API key). Transcription **must succeed** before any note, forward, or resolve —
failed STT leaves the ticket open. For scheduled automation without external vetting,
use sibling **`sp-voicemail-triage-fast`**. See
[reference/automation-setup.md](reference/automation-setup.md).

### 2. Outlook — {{employee_name}}'s inbox

1. `verify-login` on Microsoft 365 MCP.
2. `list-mail-folder-messages` — `mailFolderId: inbox`.
3. Candidate filter (run sequential passes if needed — do not combine
   `$search` and `$filter` on one Graph call):
   - **Subject includes** `New voicemail` (case-insensitive) — required
   - Do **not** include messages that only mention voicemail, ACH, or payment in
     the body or quoted thread with a different subject
   - Default window: **last 7 days**, unread first; user may override
4. `download-bytes` on the **audio attachment** (`.wav` or `.mp3`); transcribe via
   Whisper. The email body is notification metadata only — **not a transcript** and
   not used for classification.

Dedupe: if the same voicemail exists in Freshdesk and Outlook, triage once and
link both IDs in the packet.

**Same-contact combine:** When multiple voicemails share a contact (same callback
number, same company name, or same Freshdesk requester) within the batch
window, **merge into one triage item** before routing. Produce:

- One combined **summary** covering all messages (newest escalation first)
- Per-message **transcript blocks** with date, duration, and caller name
- One **forward** (or one Freshdesk note + forward) referencing every voicemail
- **Callback / urgency** based on the highest signal across the thread (repeat
  calls elevate urgency)

Do not send separate forwards to the same routing address for the same contact
in one batch run.

## Output format

### Batch summary (top of every batch run)

```markdown
# SP Voicemail batch — {date}

| # | Source | ID | Company | Category | Callback | Entity | Route to | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | FD #12345 | … | Apex Mechanical | Payment | Yes | Known SP | aphelp@vixxo.com | routed |

**Counts:** {n} triaged | {n} skipped (non-voicemail) | {n} callback Yes | {n} routed | {n} failed
```

Then one **triage packet** per item (see below).

### Triage packet (per voicemail)

```markdown
## Voicemail triage — {label}

| Field | Value |
| --- | --- |
| **Source** | Freshdesk #{id} / Outlook message {id} |
| **Callback required** | Yes / No / Recommended |
| **Urgency** | Critical / High / Normal / Low |
| **Category** | {primary category} |
| **Sub-reason** | {plain English} |
| **Caller name** | {name or Not stated} |
| **Company** | {company or Not stated} |
| **Callback number** | {number or Not stated} |
| **Reference IDs** | {SR, invoice, SF Lead, …} |
| **Entity posture** | {from company vetting} |
| **Route to** | {email list} |
| **Freshdesk disposition** | {Resolve + forward / note only / …} |
| **Confidence** | High / Medium / Low |

### Company vetting
{table from reference/company-vetting.md}

### Transcript
{verbatim}

### Summary / callback rationale / open questions
…

### Actions taken
- **Internal note:** {posted | failed + reason}
- **Forward:** {recipients + subject | skipped + reason}
- **Salesforce Lead note:** {Lead Id + posted | N/A | failed}
- **Resolved:** {yes/no + type}
```

## Workflow (per voicemail)

1. **Acquire content** — download and transcribe the **audio attachment** (`.wav`
   or `.mp3`, required for Freshdesk/Outlook intake); or user-pasted transcript /
   attached audio in single-item mode ([Acquire and transcribe](#acquire-and-transcribe)).
2. **Transcribe** verbatim; capture name, company, callback #, SR/invoice IDs.
   Use spoken context to infer the SP/company name when the caller states it
   (for example, "`This is Jane with Acme Maintenance`").
3. **Classify** — one primary category from [reference/categories.md](reference/categories.md).
4. **Callback decision** — [reference/callback-rules.md](reference/callback-rules.md).
5. **Company vetting** — [reference/company-vetting.md](reference/company-vetting.md)
   (Siebel/Gateway SP, Gateway/VixxoLink customer, JDE vendor, Salesforce Lead).
6. **Route** — [reference/routing-actions.md](reference/routing-actions.md):
   - VixxoLink, Technical, General → `service.providermanagement@vixxo.com`
   - Billing / Invoice / Payment → `aphelp@vixxo.com`
   - Insurance / COI → `COI@vixxo.com`
   - Onboarding → Salesforce Lead branch → Lead note + resolve FD, or forward
     `spm-recruitment@vixxo.com`
   - SR assistance → Gateway PM + Support emails; subject `{SR#}, Need Assistance`
7. **Post internal note** — [reference/freshdesk-internal-note-template.md](reference/freshdesk-internal-note-template.md).
8. **Forward** — per [reference/routing-actions.md](reference/routing-actions.md).
9. **Salesforce Lead note** — onboarding branch when Lead found.
10. **Resolve Freshdesk** — `status: 5` with valid `type` and required
    `custom_fields.cf_sp` (use the transcript-inferred SP/company name when
    available; use `Unknown` when SP is not identified).

## Acquire and transcribe

**Transcription source: audio attachment (`.wav` or `.mp3`) only.** Voicemail
notification emails (Freshdesk tickets and Outlook messages) carry caller ID,
duration, and callback metadata in the **body** — they do **not** include the
spoken message. All triage content must come from transcribing the attached audio
file.

Do not post Freshdesk internal notes, forwards, or resolves until that verbatim
transcript exists. If audio download or STT fails, **leave the ticket/message
unchanged** and report the failure.

**Freshdesk KSOnboarding voicemails:** Each ticket includes an audio attachment
(typically **`.wav`**, sometimes **`.mp3`**) from the 8x8 voicemail email.
Download and transcribe that file. Do not read, parse, or classify from the ticket
description, email body, or conversation thread.

**Outlook voicemails:** Same rule — body is notification metadata only. Download
the **`.wav` or `.mp3` attachment** (`download-bytes` on M365) and transcribe via
Whisper or agent STT.

**Batch REST script steps:**

1. Pick the first `.wav` or `.mp3` attachment on the ticket (prefers `.wav` when both exist).
2. Download via Freshdesk attachment URL (authenticated).
3. Transcribe via **faster-whisper** (local; `pip install -r scripts/requirements.txt`, ffmpeg on PATH).
4. Note `Transcript source: faster-whisper`.
5. Build a short voicemail summary from the spoken content and use it in the
   Freshdesk private note and any forward body.
6. Infer SP/company name from the spoken content before falling back to caller
   metadata; use that value for `cf_sp` when no verified SP number is available.
7. If transcript matches a **no-forward** rule (foul language, &lt;10s duration,
   blank or one/two words) → internal note, **skip forward**, resolve.
8. Only then run classify, vetting (if applicable), and Phase 2 writes.

**Single-item exception:** {{employee_name}} may paste a transcript or attach audio
directly in chat — that is user-provided input, not email body text.

Mark `[inaudible]` where needed. Do not use metadata-only placeholders for routing
in production runs.

## Routing checklist (automatic)

Track per item during Phase 2:

```
Route progress — {ticket/message id}:
- [ ] Internal note posted (create_ticket_note, private)
- [ ] Forward sent (forward_ticket or forward-mail-message)
- [ ] Salesforce Lead note added (if onboarding + Lead found)
- [ ] Freshdesk resolved (update_ticket status 5)
```

For **onboarding + Lead found**: resolve Freshdesk after SF note is recorded (or
document SF write failure in the internal note before resolve).

For **SR branch**: confirm PM/support emails from Gateway before forward; subject
must be `{SR_NUMBER}, Need Assistance`.

For **foul language in transcript**: post internal note, **do not forward**, resolve.

For **voicemail under 10 seconds** or **blank / one–two words**: post internal
note, **do not forward**, resolve.

If a voicemail is forwarded without a confirmed SP/company name, set `cf_sp` to
`Unknown`, tag the ticket `sp-name-review-needed`, and include the review request
in the internal note/forward summary so {{employee_name}} can review and update
the SP name.

If any write fails, continue the pipeline where safe, record the failure in the
batch summary **Status** column, and do not re-attempt without user direction.

## Guardrails

- Work context only — Vixxo SP operations.
- Facts from recording/transcript and MCP responses; mark assumptions.
- **Transcription required** from **audio attachment** (`.wav` or `.mp3`) — email
  body has no spoken content; failed download/STT → skip ticket.
- **Foul language:** profanity in the transcript → internal note + resolve,
  **no forward** (overrides category routing). See
  [reference/routing-actions.md](reference/routing-actions.md).
- **Short duration:** voicemail under **10 seconds** → internal note + resolve,
  **no forward**.
- **Minimal speech:** blank transcript or **one/two words** only → internal note
  + resolve, **no forward**.
- Phase 2 writes (internal notes, forwards, SF Lead notes, resolve) run
  automatically when this skill is invoked — except in explicit **dry-run** mode.
- Never invent recipient emails — resolve via Gateway SR payload or `list-users`.
- Redact full phone numbers in shared-channel summaries; keep full numbers in
  internal notes for {{employee_name}}.

## Additional resources

| File | Purpose |
| --- | --- |
| [reference/categories.md](reference/categories.md) | Category taxonomy |
| [reference/callback-rules.md](reference/callback-rules.md) | Callback decision |
| [reference/company-vetting.md](reference/company-vetting.md) | Siebel, Gateway, JDE, SF |
| [reference/routing-actions.md](reference/routing-actions.md) | Forwards + resolve rules |
| [reference/freshdesk-voicemail-filter.md](reference/freshdesk-voicemail-filter.md) | Voicemail-only queue filter |
| [reference/freshdesk-internal-note-template.md](reference/freshdesk-internal-note-template.md) | Note body |
| [reference/examples.md](reference/examples.md) | Sample outputs |
| [reference/automation-setup.md](reference/automation-setup.md) | Scheduled cron + batch script |

Sibling skills: **`sp-voicemail-triage-no-email`** (no forwards),
**`sp-voicemail-triage-webhook`** (WAV webhook intake),
**`sp-voicemail-triage-fast`** (Whisper + no vetting, for automation).
