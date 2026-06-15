---
name: pm-survey-review
description: >-
  Reviews preventative-maintenance (PM) survey submissions for data
  completeness, before/after photo coverage and quality, and additional
  repairs needed, then emits a per-survey chat review packet. Trade-agnostic
  (works for any trade). Two input modes: (1) a list of SR numbers, where the
  agent pulls the SR attachments, finds the survey PDF plus before/after
  photos, and reviews them; or (2) one or more PDFs attached directly by the
  user. Use when Eric says "review this PM survey", "review these PM surveys",
  "audit these PM SRs", "check the PM survey for SR <number>", "review the
  preventative maintenance survey", or hands over survey PDFs for review.
---

# PM Survey Review

Audits preventative-maintenance survey submissions and produces a structured
**review packet** per survey: a verdict, data-completeness flags, a
before/after photo assessment, the additional repairs the survey identifies,
any discrepancies, and an owner plus next action. Trade-agnostic by design —
the same rubric runs for HVAC, plumbing, electrical, handyman, refrigeration,
and any other trade.

This skill answers a different question than
[`sr-post-completion-review`](../sr-post-completion-review/SKILL.md). That
skill asks "did the work finish and can the invoice proceed." This skill asks
**"is this PM survey itself good — complete data, real before/after photos,
correctly flagged additional repairs."** It reuses that skill's packet
discipline (field-tied evidence, explicit verdict taxonomy, owner plus next
action) with a PM-survey rubric instead of a completion/invoice rubric.

## What this skill does NOT do

- Does not send any outbound message. Per
  [`.cursor/rules/outbound-messaging-guardrail.mdc`](../../../.cursor/rules/outbound-messaging-guardrail.mdc),
  the review packet is a chat deliverable only.
- Does not modify the SR, survey, attachments, quotes, or invoices. Read-only
  against Gateway / VixxoLink.
- Does not create Linear issues or render a PDF report in v1. Both are listed
  under "Future extensions" — offer them, do not auto-run them.
- Does not decide invoice readiness or completion proof. That is
  `sr-post-completion-review`'s job; hand off if Eric asks for it.

## Dependencies

- **VixxoLink MCP** (`project-0-Eric-sAssistant-vixxolink`) — primary,
  verified path for SR attachment listing/download URLs and for structured
  survey-form submissions when no survey PDF is attached.
- **Gateway MCP** (`project-0-Eric-sAssistant-gateway`) — fallback path for SR
  attachment listing and attachment download URLs. Tool descriptors in this
  MCP are bare (no argument schemas exposed); discover the working payload
  shape only if the VixxoLink path cannot be used, then record it in the
  "Verified payload shapes" table at the bottom of this file for future runs.
- **Read tool** — multimodal. Reads survey PDF text AND visually assesses
  photo images (`.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`, `.heic`). This is
  how the before/after photo quality assessment happens.
- **Shell (PowerShell)** — downloads attachment bytes from the cloud storage
  URL to the local scratch directory so the Read tool can open them.

## Reference files

- [`review-packet.md`](./review-packet.md) — the per-survey packet schema, the
  verdict taxonomy, and the cohort-summary block. Read this before emitting any
  packet.
- [`quality-rubric.md`](./quality-rubric.md) — the trade-agnostic scoring
  rubric (data completeness, photo coverage/quality, additional-repairs
  detection). Read this before scoring a survey.
- [`trades/generic.md`](./trades/generic.md) — the seeded generic per-trade
  checklist and the extension point for future trade-specific checklists.
- [`lessons-from-runs.md`](./lessons-from-runs.md) — empirical patterns from
  real review runs (data paths, classification, photo storage, gotchas).

## Scratch directory

Download attachments to `_tmp/pm-survey-review/<SR-or-batch>/`. Keep files for
the duration of the run so the Read tool can open them; they are working
artifacts, not deliverables.

## Workflow

Copy this checklist and track progress in the turn:

```
Task progress (PM Survey Review):
- [ ] 1. Detect input mode (SR list vs attached PDF) + gather scope
- [ ] 2. Per survey: locate the survey PDF + before/after photos
- [ ] 3. Download artifacts to _tmp and read them (PDF text + photo images)
- [ ] 4. Apply the quality rubric
- [ ] 5. Emit the per-survey review packet
- [ ] 6. Emit the cohort summary (when more than one survey)
```

### Step 1 — Detect input mode and gather scope

Two input modes:

| Mode | Trigger | What you have |
|---|---|---|
| **SR-list** | Eric gives one or more SR numbers (or a customer + date window to sweep). | SR numbers, or customer/date sweep inputs that you must resolve to SR numbers before pulling attachments. |
| **Attached-PDF** | Eric attaches one or more PDFs directly in chat. | The survey PDF(s) in hand. Photos may be embedded in the PDF or attached separately. |

If both are present (Eric pastes SR numbers AND attaches a PDF for one of
them), use the attached PDF for that SR and the SR-list path for the rest.

Optional scope inputs to capture if offered: **trade** (only narrows which
`trades/<trade>.md` checklist to load; the generic rubric runs regardless),
**customer**, **date window** (for a sweep).

If the input is ambiguous (no SR numbers, no customer + date sweep, no
attachment), ask once: "Give me the SR numbers to audit, a customer plus date
window to sweep, or attach the survey PDFs."

### Step 2 — Locate the survey PDF and before/after photos (SR-list mode)

If Eric gave a customer + date-window sweep instead of SR numbers, first run
`vixxolink_search_service_requests` to discover the completed PM SRs. Filter on
the customer/date window with `priority: "Planned/PM"` and completed billing
sub-statuses such as `AR Successful` or `Invoice Review`; do **not** use
`isJobComplete` as the completion filter. Omit `sortDirection: "desc"` because
the API rejects that value; the default order is already newest-first. Capture
the returned SR numbers, then continue with the per-SR attachment workflow.

For each SR:

1. **List attachments.** Call `vixxolink_get_service_request_attachments`
   with `{"service_request_number": "1-..."}` (the human SR number). This is
   the **primary, verified** path (Run 1, 2026-06-05). It returns one record
   per attachment with a `subType`, a `key` (filename), and a **directly
   downloadable presigned `url`** — no separate cloud-URL call is needed. The
   Gateway tool `gateway_list_sr_attachments` is a fallback only; in Run 1 the
   simple `{"sr_number"}` / `{"service_request_number"}` payloads returned
   HTTP 400, so prefer VixxoLink.

2. **Classify each attachment by `subType`** (authoritative — far better than
   filename keywords):

   | `subType` | Meaning | Action |
   |---|---|---|
   | `pmSurvey` | The PM survey PDF. | Review (Step 3). If more than one, pick the **latest `createdDate`** — duplicate resubmissions happen (Run 1: SR `1-6533423702` had two). |
   | `mobileTechnicianPhotos` | Field photos attached separately. | Download + assess as before/after coverage. |
   | `general` | General attachment; observed as Peet's field-photo `.jpg`s and Safeway roofing audit PDFs. | If image, download + assess as before/after coverage. If PDF and roofing/audit survey with no `pmSurvey`, review as the survey. Otherwise context only. |
   | `asset` / `mfgPlate` (`type: AssetPhoto`) | Asset and nameplate photos. | Support the asset-identity field. |
   | `workTicket` | SP work ticket PDF. | Context only; not the survey. |
   | other | quotes, invoices, etc. | Note, do not review. |

   Fall back to filename keywords (`survey`, `pm`, `preventative`,
   `checklist`, `inspection`) only if `subType` is absent.
   If there is no `pmSurvey` attachment, first check any `general` PDF for a
   roofing/audit survey (per `trades/roofing.md`), then try
   `vixxolink_get_form_service_form_submission_survey` /
   `gateway_swm_list_surveys` with the current SR in the payload (prefer
   `{"service_request_number": "1-..."}`). If a tool only accepts `{}`, treat
   the response as unscoped and filter to a record that explicitly references
   the current SR before scoring. Never score a fallback survey unless its
   provenance matches the SR under review. If there is genuinely no survey,
   emit a packet with verdict `data-incomplete` and say the survey itself is
   missing.

3. **Photos live in TWO places — check both** (Run 1):
   - **Embedded in the survey PDF** (most common — Run 1: 7 of 10 SRs). Extract
     them with PyMuPDF/`fitz` (see Step 3) — the Read tool's PDF text
     extraction does NOT surface embedded raster images.
   - **Separate photo attachments** (`mobileTechnicianPhotos` / `asset` /
     `mfgPlate` / image `general`) — download each via its presigned `url`.
   Total photo coverage = embedded count + separate-attachment count.

4. **Download URLs.** The VixxoLink listing already gives a presigned `url` per
   attachment; download it directly (Step 3). Only if you fell back to the
   Gateway listing do you need `gateway_get_attachment_cloud_storage_url`.

### Step 3 — Download and read

1. Download each artifact to `_tmp/pm-survey-review/<SR>/` with PowerShell:

```powershell
Invoke-WebRequest -Uri "<cloud-storage-url>" -OutFile "_tmp/pm-survey-review/<SR>/<filename>"
```

2. **Read the survey PDF** with the Read tool (it extracts PDF text). Capture:
   the **survey completion date** (STANDARD: the chosen `pmSurvey` attachment's
   `createdDate`, or the PDF's `creationDate` metadata — both equal the
   submission timestamp; include it on every packet and report row),
   asset id/identity, readings/measurements, dates, technician name,
   signatures, checklist line items and their pass/fail/NA marks, the per-asset
   "Repairs needed?" answers, and any free text recommending additional work.
3. **Extract embedded photos** from the survey PDF with PyMuPDF before viewing
   them — the Read tool's text extraction skips embedded images. A helper that
   probes per-page image counts and extracts them to files is the proven
   approach (`fitz`, available on this box). Then **view each photo** (and each
   separate photo attachment) with the Read tool (multimodal). Assess: legible,
   in focus, shows the asset/condition, and before vs after. Do not claim to
   see something a photo does not show. For large surveys, count coverage from
   the embedded-image probe + separate attachments, and spot-check quality on a
   representative sample rather than every image.
4. **Attached-PDF mode:** skip Steps 1-2; read the attached PDF directly and
   extract its embedded photos the same way. If Eric also attached separate
   photo files, read those too.

If a Gateway call hangs or returns a 401/timeout mid-run, stop and trigger the
[`fix-my-gateway`](../../../.claude/skills/fix-my-gateway/SKILL.md) skill, then
resume from the last completed step.

### Step 4 — Apply the quality rubric

Score the survey against [`quality-rubric.md`](./quality-rubric.md): data
completeness, before/after photo coverage and quality, and additional-repairs
detection. Load `trades/<trade>.md` if a matching trade-specific checklist
exists; otherwise use `trades/generic.md`. The generic rubric always runs.

### Step 5 — Emit the per-survey review packet

Emit the packet exactly as specified in [`review-packet.md`](./review-packet.md).
Keep fields tied to evidence (quote the survey text, name the specific photo).
Do not collapse fields into a prose paragraph. Keep line width narrow per
[`.cursor/rules/email-triage-thread-defaults.mdc`](../../../.cursor/rules/email-triage-thread-defaults.mdc)
line-width discipline.

### Step 6 — Cohort summary

When more than one survey is reviewed, lead with (or end with) the cohort
summary block from [`review-packet.md`](./review-packet.md): verdict counts and
the top repeated gaps. Escalate a pattern when it repeats across 3 or more
surveys in the run.

## Guardrails

- Do not fabricate readings, photo contents, technician names, or repair
  recommendations. If a value is not in the survey or a photo, mark it missing
  or unknown — never invent it.
- A photo that is blurry, dark, mislabeled, or does not show the asset is
  **not** valid coverage. Say so explicitly; do not count it.
- "Survey present" is not "survey complete." A survey with the form attached
  but blank/partial fields is `data-incomplete`, not `pass`.
- Separate the survey-quality verdict (Field 1) from the additional-repairs
  finding (Field 4). A clean, complete survey can still surface real follow-on
  repairs, and a sloppy survey can still have no additional work.
- Preserve provenance: quote the survey's own words before inferring scope on
  any additional repair.
- Read-only. Never call any `*_update_*`, `*_create_*`, `*_delete_*`,
  `*_add_*`, or `*_post_*` tool from this skill.

## Verified payload shapes

Record the working payload shape the first time each tool succeeds, so future
runs are deterministic. (Descriptors are bare; this table is the memory.)

| Tool | Payload shape | Verified date | Notes |
|---|---|---|---|
| `vixxolink_get_service_request_attachments` | `{"service_request_number": "1-6533419834"}` | 2026-06-05 | **PRIMARY.** Returns `data.data[]`, each with `subType`, `key` (filename), `createdDate`, and a directly downloadable presigned S3 `url`. No separate cloud-URL call needed. |
| `gateway_list_sr_attachments` | _(unresolved)_ | 2026-06-05 | Fallback only. `{"sr_number"}` returned HTTP 400 against `/vixxolink/v2/servicerequest/attachments`. Use VixxoLink instead until the shape is found. |
| `gateway_get_attachment_cloud_storage_url` | _(only needed if Gateway listing is used)_ | — | Not needed on the VixxoLink path (presigned url already provided). |
| `vixxolink_get_form_service_form_submission_survey` | _(SR-scoped shape unresolved; try `{"service_request_number": "1-6533419834"}` before any `{}` call)_ | — | Active survey form submission; use when no `pmSurvey` PDF is attached. If only `{}` is accepted, filter response records to the current SR before scoring. |
| `gateway_swm_list_surveys` | _(SR-scoped shape unresolved; try `{"service_request_number": "1-6533419834"}` before any `{}` call)_ | — | SWM survey list; secondary structured-survey source. If only `{}` is accepted, filter response records to the current SR before scoring. |

## Future extensions (not built in v1)

- **Auto-redispatch (recall) on a failed survey** — when a survey verdict is
  `fail` (or `photos-insufficient` / `data-incomplete` where the field work
  cannot be trusted), create a recall / redispatch back to the same SP to
  re-perform or correct the PM. The recall must carry the specific gaps from
  the review packet (missing readings, missing/illegible before-after photos,
  unaddressed checklist failures) so the SP knows exactly what to fix.
  Draft-then-approve per
  [`.cursor/rules/outbound-messaging-guardrail.mdc`](../../../.cursor/rules/outbound-messaging-guardrail.mdc)
  — never auto-dispatch without explicit approval. Likely implemented via the
  VixxoLink SR write tools (e.g. a recall/redispatch action or a new child SR
  referencing the original FWKD) once the recall payload shape is verified.
- **Rendered PDF report** with photo thumbnails — reuse
  [`vixxo-project-history-research/scripts/render_combined_pdf.py`](../vixxo-project-history-research/scripts/render_combined_pdf.py).
- **Linear follow-up issues** for additional repairs / data gaps — route via
  the `linear-issue-manager` skill on explicit approval.
- **Per-trade rubric library** — add `trades/<trade>.md` checklists beyond the
  seeded generic one as patterns accumulate.
