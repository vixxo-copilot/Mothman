---
name: sp-fd-sf-duplicate-bridge
description: >-
  Detect and reconcile duplicate intake between Freshdesk and Salesforce
  (voicemail dual-intake, email-to-case overlaps, KS onboarding mirrors).
  Scan for FD/SF pairs, classify same-thread vs contact collision, sync FD
  attachments to SF Cases with retention policy, and document cross-links.
  Use when matching a Freshdesk ticket to a Salesforce Case, forwarding
  attachments between systems, scanning duplicate pairs in a time window, or
  bridging ProSite-style onboarding dual intake.
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

## Operating modes

| Mode | Trigger | Output |
| --- | --- | --- |
| **Single pair** | FD `#` + SF Case `#` (or one id + search) | Pair summary + optional attachment sync |
| **Detect** | FD `#` only | SOQL search for SF Case with `Freshdesk #{id}` in Description |
| **Batch scan** | Time window | JSON pair list + operator summary table |
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

Matching logic: [reference/detection.md](reference/detection.md).

## Guardrails

- **No outbound** email/forwards unless {{employee_name}} explicitly approves.
- **Do not create duplicate SF Cases** when a pair already exists — sync to the
  existing Case (see `sp-voicemail-triage` dedupe SOQL).
- **Contact collisions** (batch COI senders, AP vs onboarding same email) are not
  auto-synced.
- Prefer **`--dry-run`** when policy or pair classification is uncertain.

## Examples

[reference/examples.md](reference/examples.md) — ProSite FD #57142 ↔ SF #00005739,
voicemail dual-intake, contact collision, batch scan.

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/scan_duplicates.py` | Window batch pair detection |
| `scripts/sync_attachments_to_sf.py` | FD → SF Case file sync with policy |

## Artifacts

Write scan/sync JSON under `.tmp/` inside this skill directory. Do not commit
`.tmp/` outputs.
