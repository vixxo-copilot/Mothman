---
name: sp-fd-sf-duplicate-bridge
description: >-
  Detect duplicate Salesforce Cases (Federated COI Req-id, same subject+email,
  voicemail phone). Default is SF-only — no Freshdesk comparison. Optional
  separate FD↔SF review for AP-related SF Cases; plus FD attachment sync and
  Federated COI routing when explicitly requested.
---

# Freshdesk ↔ Salesforce Duplicate Bridge

Work-only skill. **Default duplicate review is Salesforce-only** (intra-SF
Cases: Federated COI Req-id, subject+email, voicemail phone). Do **not**
compare SF Cases to Freshdesk as part of that default flow.

**Freshdesk pairing is opt-in and separate** — mainly when an SF Case is an
AP-related request and the operator asks whether a matching AP Help / QSIAP
ticket already exists.

## When to use

**SF-only (default — always use for “duplicate bridge” / shell / all-org scan):**
- "Review duplicate SF Cases" / "SF-only duplicate scan" / all-org shell vet
- Federated COI created multiple Cases for the same Req id
- Same subject + requester email landed twice in Email-to-Case

**Cross-system (FD↔SF) — separate pass only:**
- SF Case is **AP / payment / remittance** and operator asks “is this also in FD?”
- "Find the Salesforce Case for Freshdesk #57142"
- "Scan FD/SF duplicates since {date}" (explicit)
- Voicemail dual-intake, KS onboarding mirror, attachment sync
- **Vet Federated COI notification** — parse Req id, find open Case, avoid duplicate
- **Route Federated update** to existing SF Case for same `{policy-id} Req {req_id}`

Sibling skills:

| Skill | Role |
| --- | --- |
| `sp-voicemail-triage` | Creates SF Cases from FD voicemails; writes `Freshdesk #{id}` cross-ref |
| `sp-inbound-vetting` | SP identity vetting on SF queues + AP Help |
| `vixxo-coi-review` | COI field compliance after pairing |

## Operating modes

| Mode | Trigger | Output |
| --- | --- | --- |
| **SF-only review** | Default / “duplicate bridge” / shell all-org | Per-SP table + merge/close list (**no FD compare**) |
| **AP → FD check** | SF Case is payment/AP and operator asks | Separate `scan_duplicates.py` / single-pair FD lookup |
| **Single pair** | FD `#` + SF Case `#` (or one id + search) | Pair summary + optional attachment sync |
| **Detect** | FD `#` only | SOQL search for SF Case with `Freshdesk #{id}` in Description |
| **Batch scan (FD↔SF)** | Explicit time-window FD/SF ask | JSON pair list + operator summary table |
| **Federated COI vet** | Inbound cert / auto-reply subject | Req-id parse + open Case lookup + route (no new Case) |
| **Dry-run** | Any sync with `dry-run` / `--dry-run` | Selected files only; no SF writes |
| **Merge plan** | Bucket duplicate groups | JSON plan + dry-run merge steps |
| **Merge execute** | Operator approves plan | Files → primary, Case comment, close dupes |

## Workflow — merge / close duplicates (bucket automation)

Consolidate duplicate Cases into **one open ticket per bucket** (rate change,
COI update, VixxoLink same-user, voicemail when SP captured). COI dupes may
route into an **open onboarding Case** for that SP.

1. Export SF Cases with **Description** (voicemail context; not for FD pairing).
2. Run SF-only scan (below) or use existing scan JSON.
3. Build merge plan (**dry-run default**). Plan JSON includes `manual_review[]`
   for groups needing operator decision (multiple New queue-owned Cases):

```bash
python scripts/merge_sf_duplicates.py \
  --sf-cache .tmp/sf-cases-window-{date}.json \
  --scan-input .tmp/sf-duplicate-scan-{date}.json \
  --buckets coi_federated,coi_update,rate_change,vixxolink_support,voicemail \
  --resolve-coi-onboarding \
  --output .tmp/sf-merge-plan-{date}.json \
  --report .tmp/sf-merge-manual-review-{date}.md
```

4. Review auto-merge plan **and** manual-review report. Voicemail cross-routing
   requires **matching request context** (Category/transcript bucket) plus an
   actively-worked open Case — never closed, never `New` when an active Case
   exists, and never rate → VixxoLink (or other bucket mismatches).
5. Execute after explicit approval:

```bash
python scripts/merge_sf_duplicates.py \
  --plan .tmp/sf-merge-plan-{date}.json \
  --execute --sync-voicemail
```

Per merge: copy files to primary → Case comment on primary → **Case comment on
duplicate** (Duplicate + primary Case #) → audit Task → close duplicate.
Details: [reference/merge-automation.md](reference/merge-automation.md).

## Workflow — SF-only duplicate review

1. Export SF Cases (MCP SOQL) → `.tmp/sf-cases-window-{date}.json`
2. Run:

```bash
python scripts/scan_sf_duplicates.py \
  --sf-cache .tmp/sf-cases-window-{date}.json \
  --output .tmp/sf-duplicate-scan-{date}.json \
  --report .tmp/sf-duplicate-report-{date}.md
```

3. Present **one row per SP**: recommended primary Case, Cases to merge/close.
4. Operator approves before any Case status change or merge.

**Do not** run `scan_duplicates.py` (FD↔SF) or `--include-fd-xref` unless the
operator explicitly asks. All-org shell pipeline
(`run_allorg_duplicate_vet_pipeline.py`) is SF-only.

Logic: [reference/sf-intra-duplicates.md](reference/sf-intra-duplicates.md).

## Workflow — AP-related SF Case → separate FD duplicate check

When an **SF** Case is payment / remittance / invoice-AP (bucket `payment_ap` or
routing table “forward to AP Help”) and the operator wants a Freshdesk twin:

1. Finish SF-only identity + intra-SF duplicate review first.
2. Run a **separate** FD↔SF pass — single Case or short window:

```bash
python scripts/scan_duplicates.py \
  --window-start {iso} \
  --sf-cache .tmp/sf-cases-window-{date}.json \
  --output .tmp/fd-sf-duplicate-scan-ap-{date}.json
```

Or resolve one FD ticket / one SF Case via the single-pair workflow below.
Do **not** fold this into the default shell/all-org HTML report.

## Workflow — single pair

### 1. Resolve records

**Freshdesk:** MCP `get_ticket` + `get_ticket_conversation`.

**Salesforce:** MCP `run_soql_query` — see [reference/detection.md](reference/detection.md).

### 2. Classify the pair

| `dup_type` | Attachment sync? |
| --- | --- |
| `true_same_thread` | Yes (default) |
| `likely_same_thread` | Yes with operator confirmation |
| `contact_collision` | No — report only unless operator overrides |

### 3. Sync attachments (when requested)

Default policy: **`ks-onboarding-reply`** — original ticket packet + latest
requester reply; excludes Vixxo outbound templates.

```bash
python scripts/sync_attachments_to_sf.py \
  --fd-ticket-id {id} \
  --sf-case-number {number} \
  --policy ks-onboarding-reply \
  --include-original-packet
```

Details: [reference/attachment-sync.md](reference/attachment-sync.md).

**Salesforce writes:** `sf data create file` / `sf data delete record` via CLI
(org `vixxo`). MCP Salesforce is read-only for files.

### 4. Document the bridge

- SF **Task** on Case: `FD attachment sync — Freshdesk #{id}` (completed)
- Cross-ref in Task body: file list + policy used
- Freshdesk internal note optional when FD ticket stays open (draft-then-approve
  if outbound)

## Workflow — batch scan (FD↔SF, explicit only)

Not part of the default duplicate-bridge / shell HTML run. Use when the
operator explicitly asks for Freshdesk↔Salesforce pairs (or AP twin check).

1. Export SF Cases for window (MCP SOQL) → `.tmp/sf-cases-window-{date}.json`
2. Run:

```bash
python scripts/scan_duplicates.py \
  --window-start {iso} \
  --sf-cache .tmp/sf-cases-window-{date}.json \
  --output .tmp/fd-sf-duplicate-scan-{date}.json
```

3. Present summary: pair counts by `dup_type`, table with FD/SF links, attachment
   counts for `true_same_thread` pairs missing SF ContentDocumentLink files.

Matching logic: [reference/detection.md](reference/detection.md). Federated COI:
[reference/federated-coi.md](reference/federated-coi.md).

Use `--include-coi` when scanning Federated cert intake.

## Workflow — Federated COI vet (single notification)

1. **Parse subject** — extract `{provider}`, `{policy-id}`, `Req {req_id}` per
   [reference/federated-coi.md](reference/federated-coi.md).
2. **SOQL** — search SF Cases with same `{policy-id} Req {req_id}`; prefer open
   status.
3. **FD search** — same Req id string; prefer open ticket.
4. **Route** — append to open Case/ticket; sync attachments if FD holds the cert.
   Do **not** create a new SF Case when an open match exists.
5. **Document** — SF Task noting Req id, source, and any duplicate Cases to close.

## Guardrails

- **No outbound** email/forwards unless {{employee_name}} explicitly approves.
- **Do not create duplicate SF Cases** when a pair already exists — sync to the
  existing Case (see `sp-voicemail-triage` dedupe SOQL). For Federated COI, dedupe
  on **`(policy_id, req_id)`** before creating Cases.
- **Contact collisions** (batch COI senders, AP vs onboarding same email) are not
  auto-synced. **Same Req id with different ticket numbers is a duplicate** — merge
  or route, do not treat as new intake.
- Prefer **`--dry-run`** when policy or pair classification is uncertain.

## Examples

[reference/examples.md](reference/examples.md) — ProSite FD #57142 ↔ SF #00005739,
voicemail dual-intake, contact collision, batch scan, **Angeles Plumbing Federated
COI Req-id duplicates**.

## Reference

| Doc | Purpose |
| --- | --- |
| [reference/sf-intra-duplicates.md](reference/sf-intra-duplicates.md) | **SF-only** duplicate review |
| [reference/merge-automation.md](reference/merge-automation.md) | **Bucket merge/close** automation |
| [reference/detection.md](reference/detection.md) | FD↔SF match signals, SOQL, batch scan |
| [reference/federated-coi.md](reference/federated-coi.md) | Req-id parsing, vetting, routing |
| [reference/attachment-sync.md](reference/attachment-sync.md) | FD → SF file sync policies |
| [reference/examples.md](reference/examples.md) | Worked examples |

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/scan_sf_duplicates.py` | **SF-only** duplicate Case review |
| `scripts/extract_shell_coi_insured.py` | **Required** COI PDF insured/SP extraction (Case + EmailMessage) |
| `scripts/render_shell_needs_manual_html.py` | Full needs-manual list (Case # + subject) → Chrome |
| `scripts/merge_sf_duplicates.py` | **Bucket merge/close** plan + execute |
| `scripts/sf_merge_primary.py` | Status/assignment-aware primary selection |
| `scripts/sf_case_activity.py` | CaseComment/History/Task last-touch lookup |
| `scripts/voicemail_match.py` | Voicemail description/transcript work-target search |
| `scripts/sf_case_buckets.py` | Case bucket classification helpers |
| `scripts/scan_duplicates.py` | FD↔SF window batch pair detection |
| `scripts/sync_attachments_to_sf.py` | FD → SF Case file sync with policy |

## Artifacts

Write scan/sync JSON under `.tmp/` inside this skill directory. Do not commit
`.tmp/` outputs. Vetted HTML reports open in **Chrome** by default
(`OPEN_REPORT=0` to skip).
