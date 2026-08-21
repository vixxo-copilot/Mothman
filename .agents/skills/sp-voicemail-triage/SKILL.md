---
name: sp-voicemail-triage
description: >-
  Auto-transcribes and triages service-provider voicemails from Salesforce
  Cases for 8x8 extension 4046 (Vendor Relations Email-to-Case), Freshdesk
  QSIAP AP mailbox (qsiap@vixxo.com), and the user's Outlook VM folder.
  Vets company names against Siebel, Gateway, JDE, and Salesforce (Lead,
  Case, Account, Contact); classifies the call reason; determines callback
  need; posts SF Case Tasks (4046 path — no Freshdesk); for QSIAP posts
  Freshdesk notes/resolves; Billing / Invoice Support and Payment Information
  stay Freshdesk-only when on QSIAP (no SF Case/Task writes); forwards to
  service.providermanagement@vixxo.com, aphelp@vixxo.com, COI@vixxo.com,
  spm-recruitment@vixxo.com, or Gateway SR PM/support staff. KSOnboarding
  Freshdesk mailbox is retired — do not scan FD type KSOnboarding. Use when
  the user asks to process SP voicemails, triage extension 4046 / Vendor
  Relations voicemails, triage QSIAP/AP voicemails, transcribe voicemails, or
  route onboarding, billing, COI, or SR callback mail. For triage without
  outbound email, use sibling skill `sp-voicemail-triage-no-email`. For HTTP
  webhook + WAV intake, use sibling skill `sp-voicemail-triage-webhook`.
---

# SP Voicemail Triage

Work-only workflow for **service provider (SP) voicemails**. Default run:
**auto-transcribe and triage all voicemails** from **Salesforce Cases** for
**8x8 extension 4046** (Vendor Relations), Freshdesk **QSIAP**
(`qsiap@vixxo.com`) AP voicemails, and {{employee_name}}'s **Outlook VM
folder**, vet the company across Vixxo systems, classify the reason, decide
callback need, then **automatically** route (SF Tasks on 4046 Cases; Freshdesk
notes/forwards/resolve for QSIAP; Outlook forwards when no SF Case). No
separate approval step — {{employee_name}} has pre-authorized these actions
for this skill.

**Retired:** Freshdesk **KSOnboarding** (`ksonboarding@vixxo.com`) is no longer
an active mailbox. Do **not** search or write that queue.

**Write order:**

- **SF 4046:** Case Task (or close AP/short) → optional email forward — **no
  Freshdesk**
- **QSIAP:** internal note → forward when misrouted → resolve when required
  (Billing/Payment stay Open on QSIAP; **no SF writes**) — see
  [qsiap-voicemail.md](reference/qsiap-voicemail.md)
- **Outlook-only:** forward → SF Case + Task when warranted (not Billing/Payment)

## When to use

- "Process SP voicemails" / "run voicemail triage" / "triage the queue"
- "Triage extension 4046" / "Vendor Relations voicemails" / "SF voicemails"
- "Transcribe voicemails in SF and my Outlook VM folder"
- "Triage QSIAP voicemails" / "process AP voicemails on qsiap"
- Single voicemail: attach audio, paste transcript, or point at a Case/message
- **Webhook + WAV:** use **`sp-voicemail-triage-webhook`** (not this skill)
- **No outbound email:** use **`sp-voicemail-triage-no-email`**
- **Legacy FD KSOnboarding fast cron:** sibling **`sp-voicemail-triage-fast`**
  is retired for default SPM intake (mailbox inactive); use this skill's SF
  4046 path instead. QSIAP still uses `scripts/batch_process_qsiap.py`.

## Operating modes

| Mode | Trigger | Behavior |
| --- | --- | --- |
| **Batch (default)** | "Process voicemails" without a single item | Scan all three sources; full pipeline on every candidate |
| **Single** | One ticket, message, or attachment | Full pipeline on one item |
| **Dry-run (opt-in)** | User says "dry-run" / "preview only" | Triage + vet only; no writes |

**Phase 1 — Triage (automatic):** transcribe, classify, vet company (Gateway +
Salesforce Lead/Case/Account/Contact), decide callback.

**Phase 2 — Route (automatic):** post Freshdesk internal notes, forward
mail/tickets, add Salesforce Lead/Case Tasks (create Case when needed), resolve
Freshdesk. No separate approval step — {{employee_name}} has pre-authorized
these actions for this skill.

## Default batch sources

### 1. Salesforce — 8x8 extension 4046 (Vendor Relations)

**Primary SPM path.** Full rules:
[reference/salesforce-4046-voicemail.md](reference/salesforce-4046-voicemail.md).

```sql
SELECT Id, CaseNumber, Subject, Status, Owner.Name, CreatedDate
FROM Case
WHERE IsClosed = false
  AND Subject LIKE '%New voicemail%'
  AND Subject LIKE '%VENDOR RELATIONS%'
ORDER BY CreatedDate DESC
LIMIT 50
```

- Notification body (Email-to-Case): *"Your extension **4046** just received a
  new voicemail. Tap the attachment to listen…"* — metadata only, not a transcript.
- Download `.wav` / `.mp3` from `EmailMessage` → `ContentDocumentLink` →
  `ContentVersion`; transcribe with faster-whisper before routing.
- **No Freshdesk** for this source — post Completed Case Tasks (or close
  Billing/Payment / short as Duplicate per policy).
- Prefer SF Case over Outlook when the same 4046 message exists in both.

### 2. Outlook — {{employee_name}}'s **VM** folder

Voicemail notifications are filed by rule into the Outlook subfolder **`VM`**
(not Inbox). Resolve that folder first (`list-mail-folders` / inbox child
folders); override with `VM_MAIL_FOLDER_NAME` or `VM_MAIL_FOLDER_ID` when
needed.

1. `verify-login` on Microsoft 365 MCP.
2. `list-mail-folder-messages` — `mailFolderId` = the **VM** folder id.
3. Candidate filter (run sequential passes if needed — do not combine
   `$search` and `$filter` on one Graph call):
   - **Subject includes** `New voicemail` (case-insensitive) — required
   - Do **not** include messages that only mention voicemail, ACH, or payment in
     the body or quoted thread with a different subject
   - Default window: **last 7 days**, unread first; user may override
4. `download-bytes` on the **audio attachment** (`.wav` or `.mp3`); transcribe via
   Whisper. The email body is notification metadata only — **not a transcript** and
   not used for classification.

Dedupe: if the same 4046 voicemail exists as an **SF Case** and in Outlook,
triage once on the SF Case and link the Outlook message id in the Task.

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

### 3. Freshdesk — QSIAP AP voicemails (`qsiap@vixxo.com`)

Open SPM tickets with subject **`New voicemail`** gated to recipient
**`qsiap@vixxo.com`**. Full rules:
[reference/qsiap-voicemail.md](reference/qsiap-voicemail.md).

- Discover via type-sliced SPM searches (`Invoice Support` + `type:null`), then
  subject filter + QSIAP recipient gate.
- **Transcript-first:** never use 8x8 caller ID as company; extract company /
  contact / SR from Whisper transcript.
- **Billing / Payment:** internal note + tags (`qsiap-source`,
  `voicemail-triaged`) + `cf_sp`; **no forward** (already on QSIAP); leave Open
  when callback Yes/Recommended; resolve only for short/foul/minimal branches.
- **Misroute** (COI, onboarding, SPM, SR, etc.): forward to the normal triage
  recipient, then resolve.
- **Batch REST script:** `scripts/batch_process_qsiap.py`
  (`--dry-run`, `--re-triage`).

## Output format

### Batch summary (top of every batch run)

```markdown
# SP Voicemail batch — {date}

| # | Source | ID | Company | Category | Callback | Entity | Route to | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | SF 00008035 | … | Facility Maintenance Pros | General | Yes | Known SP | SPM (Case Task) | task posted |
| 2 | QSIAP #86700 | … | Goodson Services | Payment | Recommended | Known SP | qsiap@ (stay) | noted / open |

**Counts:** {n} triaged | {n} SF 4046 | {n} QSIAP | {n} Outlook | {n} callback Yes | {n} routed | {n} failed
```

Then one **triage packet** per item (see below).

### Triage packet (per voicemail)

```markdown
## Voicemail triage — {label}

| Field | Value |
| --- | --- |
| **Source** | SF Case {CaseNumber} / QSIAP Freshdesk #{id} / Outlook message {id} |
| **Callback required** | Yes / No / Recommended |
| **Urgency** | Critical / High / Normal / Low |
| **Category** | {primary category} |
| **Sub-reason** | {plain English} |
| **Caller name** | {name or Not stated} |
| **Company** | {company or Not stated} |
| **Callback number** | {number or Not stated} |
| **Reference IDs** | {SR, invoice, SF Lead, SF Case, …} |
| **Entity posture** | {from company vetting} |
| **SF Lead** | {Id / Status / Company or None} |
| **SF Case** | {CaseNumber / Status or None} |
| **SF writes** | Lead Task / Case Task / Case create — {posted | failed | N/A} |
| **Route to** | {email list} |
| **Disposition** | {SF Task / Case closed / FD resolve + forward / note only / …} |
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
- **Salesforce Lead Task:** {Lead Id + posted | N/A | failed}
- **Salesforce Case Task / Case:** {CaseNumber + posted | created | N/A | failed}
- **Resolved:** {yes/no + type}
```

## Workflow (per voicemail)

1. **Acquire content** — download and transcribe the **audio attachment** (`.wav`
   or `.mp3`) from SF Case EmailMessage, Outlook, or QSIAP Freshdesk; or
   user-pasted transcript / attached audio in single-item mode
   ([Acquire and transcribe](#acquire-and-transcribe)).
2. **Transcribe** verbatim; capture name, company, callback #, SR/invoice IDs.
3. **Classify** — one primary category from [reference/categories.md](reference/categories.md).
4. **Callback decision** — [reference/callback-rules.md](reference/callback-rules.md).
5. **Company vetting** — [reference/company-vetting.md](reference/company-vetting.md)
   (Siebel/Gateway SP, Gateway/VixxoLink customer, JDE vendor, Salesforce
   Lead/Case/Account/Contact). See [reference/salesforce-notes.md](reference/salesforce-notes.md).
6. **Route** — [reference/routing-actions.md](reference/routing-actions.md):
   - VixxoLink, Technical, General → `service.providermanagement@vixxo.com`
     (4046: Case Task; Outlook-only: forward)
   - Billing / Invoice / Payment → `aphelp@vixxo.com` or QSIAP stay; **no SF
     writes** on AP path (close mistaken 4046 Cases as Duplicate)
   - Insurance / COI → `COI@vixxo.com`
   - Onboarding → Salesforce Lead branch → Lead Task, or forward
     `spm-recruitment@vixxo.com`
   - SR assistance → Gateway PM + Support emails; subject `{SR#}, Need Assistance`
7. **SF 4046:** Completed Case Task (or close per short/AP rules) — see
   [salesforce-4046-voicemail.md](reference/salesforce-4046-voicemail.md).
8. **QSIAP only:** post Freshdesk internal note
   ([freshdesk-internal-note-template.md](reference/freshdesk-internal-note-template.md)),
   forward when misrouted, resolve when disposition requires it.
9. **Outlook-only (no SF Case):** forward per routing-actions; create SF Case +
   Task when category warrants (not Billing/Payment).
10. **Do not** search or update Freshdesk KSOnboarding.

## Acquire and transcribe

**Transcription source: audio attachment (`.wav` or `.mp3`) only.** Voicemail
notification emails (Freshdesk tickets and Outlook messages) carry caller ID,
duration, and callback metadata in the **body** — they do **not** include the
spoken message. All triage content must come from transcribing the attached audio
file.

Do not post Freshdesk internal notes, forwards, or resolves until that verbatim
transcript exists. If audio download or STT fails, **leave the ticket/message
unchanged** and report the failure.

**Salesforce 4046 (Vendor Relations):** Audio is on the Case's inbound
`EmailMessage` ContentDocument (`.wav` / `.mp3`). Download via Salesforce CLI
`ContentVersion` VersionData; transcribe before any Case Task or close. Body
text is 8x8 metadata only (extension 4046 notice) — not a transcript.

**Outlook voicemails:** Same rule — body is notification metadata only. Download
the **`.wav` or `.mp3` attachment** (`download-bytes` on M365) and transcribe via
Whisper or agent STT.

**QSIAP Freshdesk:** Download ticket audio attachment URL; same Whisper path.

**STT steps (all sources):**

1. Pick the first `.wav` or `.mp3` attachment (prefers `.wav` when both exist).
2. Download (SF ContentVersion, Graph `download-bytes`, or Freshdesk URL).
3. Transcribe via **faster-whisper** (local; `pip install -r scripts/requirements.txt`, ffmpeg on PATH).
4. Note `Transcript source: faster-whisper`.
5. If transcript matches a **no-forward** rule (foul language, &lt;10s duration,
   blank or one/two words) → document skip; close SF Case or resolve QSIAP as
   applicable; **no route forward**.
6. Only then run classify, vetting (if applicable), and Phase 2 writes.

**Single-item exception:** {{employee_name}} may paste a transcript or attach audio
directly in chat — that is user-provided input, not email body text.

Mark `[inaudible]` where needed. Do not use metadata-only placeholders for routing
in production runs.

## Routing checklist (automatic)

Track per item during Phase 2:

```
Route progress — {SF Case / QSIAP # / Outlook id}:
- [ ] Audio transcribed (faster-whisper)
- [ ] SF 4046: Completed Case Task (or Case closed for AP/short)
- [ ] QSIAP: internal note posted (create_ticket_note, private)
- [ ] Forward sent when required (forward_ticket or forward-mail-message)
- [ ] Salesforce Lead Task posted (if Lead match / onboarding)
- [ ] Outlook-only: Case created when warranted (not Billing/Payment)
- [ ] QSIAP resolved when disposition requires (update_ticket status 5)
```

For **onboarding + Lead found**: post Lead Task; resolve QSIAP Freshdesk when
applicable; on 4046 leave Case with Completed Task.

For **SR branch**: confirm PM/support emails from Gateway before forward; subject
must be `{SR_NUMBER}, Need Assistance`.

For **foul language in transcript**: document skip, **do not forward**; close SF
Case or resolve QSIAP as applicable.

For **voicemail under 10 seconds** or **blank / one–two words**: document skip,
**do not forward**; close SF Case or resolve QSIAP.

If any write fails, continue the pipeline where safe, record the failure in the
batch summary **Status** column, and do not re-attempt without user direction.

## Guardrails

- Work context only — Vixxo SP operations.
- Facts from recording/transcript and MCP responses; mark assumptions.
- **Transcription required** from **audio attachment** (`.wav` or `.mp3`) — email
  body has no spoken content; failed download/STT → skip item.
- **No Freshdesk KSOnboarding** — mailbox retired; SPM voicemails are SF 4046.
- **Foul language:** profanity in the transcript → skip forward; close SF Case
  or resolve QSIAP. See [reference/routing-actions.md](reference/routing-actions.md).
- **Short duration:** voicemail under **10 seconds** → skip forward; close SF
  Case or resolve QSIAP.
- **Minimal speech:** blank transcript or **one/two words** only → same as short.
- **Sourcing / account team:** transcript asks to speak with sourcing,
  procurement, or an account/program manager about work opportunities → route
  **`service.providermanagement@vixxo.com`**, **not** `aphelp@vixxo.com`. Set
  **Review for {{employee_name}}: Yes** when a Vixxo contact is named or the
  caller explicitly wants sourcing. See FD **#57452** in
  [reference/examples.md](reference/examples.md).
- Phase 2 writes run automatically when this skill is invoked — except in
  explicit **dry-run** mode.
- **Salesforce:** for 4046, Case already exists — Task (or close AP/short). For
  Outlook-only / QSIAP non-AP, run Lead/Case/Account/Contact SOQL; dedupe before
  Case create. See [reference/salesforce-notes.md](reference/salesforce-notes.md)
  and [reference/salesforce-4046-voicemail.md](reference/salesforce-4046-voicemail.md).
- Never invent recipient emails — resolve via Gateway SR payload or `list-users`.
- Redact full phone numbers in shared-channel summaries; keep full numbers in
  internal notes / Task bodies for {{employee_name}}.

## Additional resources

| File | Purpose |
| --- | --- |
| [reference/salesforce-4046-voicemail.md](reference/salesforce-4046-voicemail.md) | Primary SPM intake — extension 4046 SF Cases |
| [reference/categories.md](reference/categories.md) | Category taxonomy |
| [reference/callback-rules.md](reference/callback-rules.md) | Callback decision |
| [reference/company-vetting.md](reference/company-vetting.md) | Siebel, Gateway, JDE, SF |
| [reference/salesforce-notes.md](reference/salesforce-notes.md) | SF SOQL, Tasks, Case create, dedupe |
| [reference/routing-actions.md](reference/routing-actions.md) | Forwards + resolve rules |
| [reference/freshdesk-voicemail-filter.md](reference/freshdesk-voicemail-filter.md) | QSIAP Freshdesk voicemail-only filter |
| [reference/freshdesk-internal-note-template.md](reference/freshdesk-internal-note-template.md) | QSIAP note body |
| [reference/examples.md](reference/examples.md) | Sample outputs |
| [reference/automation-setup.md](reference/automation-setup.md) | Scheduled automation notes |
| [reference/qsiap-voicemail.md](reference/qsiap-voicemail.md) | QSIAP AP mailbox intake + disposition |

Sibling skills: **`sp-voicemail-triage-no-email`** (no forwards),
**`sp-voicemail-triage-webhook`** (WAV webhook intake).
**`sp-voicemail-triage-fast`** is legacy FD KSOnboarding automation — not for
default 4046 runs.
**`sp-inbound-vetting`** owns non-voicemail AP Help / SF queue identity
enrichment — QSIAP **voicemails** are owned here.
