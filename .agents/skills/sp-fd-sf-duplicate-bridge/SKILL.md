---
name: sp-fd-sf-duplicate-bridge
description: >-
  Detect and reconcile duplicate intake between Freshdesk and Salesforce
  (voicemail dual-intake, email-to-case overlaps, KS onboarding mirrors,
  Federated Insurance COI Req-id duplicates). Scan for FD/SF pairs, classify
  same-thread vs contact collision, vet Federated COI by Req id and subject,
  route updates to open SF Cases, sync FD attachments, and document cross-links.
  Use when matching a Freshdesk ticket to a Salesforce Case, vetting Federated
  COI notifications, forwarding attachments between systems, scanning duplicate
  pairs in a time window, or bridging ProSite-style onboarding dual intake.
---

# Freshdesk ↔ Salesforce Duplicate Bridge

Work-only skill for **finding duplicate intake** across Freshdesk and Salesforce
and **reconciling** paired records — especially attachment gaps on the SF Case.

Sibling skills:

| Skill | Role |
| --- | --- |
| `sp-voicemail-triage` | Creates SF Cases from FD voicemails; writes `Freshdesk #{id}` cross-ref |
| `sp-inbound-vetting` | SP identity vetting on SF queues + AP Help |
| `vixxo-coi-review` | COI field compliance after pairing |

## When to use

- "Find the Salesforce Case for Freshdesk #57142"
- "Scan FD/SF duplicates since {date}"
- "Forward attachments from FD #{id} to SF Case #{number}"
- "Sync onboarding files to the SF Case" (KS onboarding mirror)
- Reconcile voicemail **dual-intake** (FD `.wav` + SF triage Case)
- **Vet Federated COI notification** — parse Req id, find open Case, avoid duplicate
- **Route Federated update** to existing SF Case for same `{policy-id} Req {req_id}`

## Operating modes

| Mode | Trigger | Output |
| --- | --- | --- |
| **Single pair** | FD `#` + SF Case `#` (or one id + search) | Pair summary + optional attachment sync |
| **Detect** | FD `#` only | SOQL search for SF Case with `Freshdesk #{id}` in Description |
| **Batch scan** | Time window | JSON pair list + operator summary table |
| **Federated COI vet** | Inbound cert / auto-reply subject | Req-id parse + open Case lookup + route (no new Case) |
| **Dry-run** | Any sync with `dry-run` / `--dry-run` | Selected files only; no SF writes |

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

## Workflow — batch scan

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
| [reference/detection.md](reference/detection.md) | Match signals, SOQL, batch scan |
| [reference/federated-coi.md](reference/federated-coi.md) | Req-id parsing, vetting, routing |
| [reference/attachment-sync.md](reference/attachment-sync.md) | FD → SF file sync policies |
| [reference/examples.md](reference/examples.md) | Worked examples |

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/scan_duplicates.py` | Window batch pair detection |
| `scripts/sync_attachments_to_sf.py` | FD → SF Case file sync with policy |

## Artifacts

Write scan/sync JSON under `.tmp/` inside this skill directory. Do not commit
`.tmp/` outputs.
