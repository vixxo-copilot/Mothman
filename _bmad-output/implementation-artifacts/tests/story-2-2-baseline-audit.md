# Story 2.2 Baseline Audit

Baseline evidence for Task 1. Captures source frontmatter + section list for each of the four upstream rules, confirms target-path state under `.cursor/rules/`, and locks the consolidated banned-term set Tasks 3-8 will scan against.

Source tree surveyed: `~/Public/gtd-life/.cursor/rules/` (read-only reference).
Target tree: `/Users/dneighbors/Public/assistants-template/.cursor/rules/` (Story 2.2 write surface).

## Source rules

### Source rule 1 — `outbound-messaging-guardrail.mdc`

- Path: `~/Public/gtd-life/.cursor/rules/outbound-messaging-guardrail.mdc`
- Size: 1737 bytes, 46 lines
- Accessible: yes

#### Source frontmatter

```yaml
description: CRITICAL safety guardrail - all outbound messaging must be approved before send
globs:
alwaysApply: true
```

- Frontmatter is well-formed (opening `---` on line 1, closing `---` on line 5).
- `globs:` value is empty (bare key).

#### Source section list (ordered, verbatim headings)

1. `# OUTBOUND MESSAGING GUARDRAIL (MANDATORY)`
2. `## The Rule`
3. `## Required Workflow`
4. `## No Exceptions`
5. `## Signing Convention`

#### Source identity-sensitive content inventory

- Named addressee: "Derek" (approver) appears on lines 13, 24, 25, 28, 36, 46.
- Named agent: "Chiron" and "Deke's AI" signature (line 40, 42, 45, 46) — must not survive port.
- Non-Vixxo chat surfaces in the "covered platforms" bullet list: "Slack messages (any channel or DM)" and "SMS / iMessage" (lines 17, 19).
- Non-M365 email stacks in the "covered platforms" bullet list: "Gmail, any provider" (line 18).
- Voice-of-employee signing exception on line 46: "Messages sent as Derek (leadership comms, strategy, feedback), do not sign as Chiron" — generalize to `{{employee_name}}` and strip assistant proper name.

No fenced JSON payloads in this source file. The Teams Graph API payload belongs to `teams-dm-formatting.mdc`.

### Source rule 2 — `memory-vault-protection.mdc`

- Path: `~/Public/gtd-life/.cursor/rules/memory-vault-protection.mdc`
- Size: 984 bytes, 17 lines
- Accessible: yes

#### Source frontmatter

```yaml
description: Protects the memory vault from PII-motivated deletion by any agent
globs: memory/**
alwaysApply: true
```

- Frontmatter is well-formed (opening `---` on line 1, closing `---` on line 5).
- `globs: memory/**` is KEPT for the target port (the only one of the four rules that is path-scoped).

#### Source section list (ordered, verbatim headings)

1. `# Memory Vault Protection`
2. `## Rules`

(A single opening paragraph sits between the H1 and the `## Rules` numbered list.)

#### Source identity-sensitive content inventory

- Repository self-reference: "This repository (gtd-life)" on line 9 — strip `gtd-life` name; rephrase as the generic `assistants-template` work vault.
- Framing to remove: "personal AI life operating system" (line 9), "PII is the product, not a vulnerability" (line 13), "personal information" / "names, addresses, family details, org charts, property info" (lines 13, 14) — all `gtd-life`-specific framing; replace with Epic 3 work-memory surfaces.
- No named individuals and no named agent appear in this source file.
- No Google / Slack / SMS references.

No fenced JSON payloads in this source file.

### Source rule 3 — `teams-dm-formatting.mdc`

- Path: `~/Public/gtd-life/.cursor/rules/teams-dm-formatting.mdc`
- Size: 1450 bytes, 29 lines
- Accessible: yes

#### Source frontmatter

```yaml
description: Formatting rules for Teams messages sent by Chiron
globs: 
alwaysApply: true
```

- Frontmatter is MALFORMED in the source: the opening `---` delimiter on line 1 is MISSING. Line 1 starts with `description:` directly, and the closing `---` appears on line 4. Target port MUST FIX this by writing a proper opening `---` on line 1.
- `description:` contains the named agent "Chiron" — strip; rewrite around `{{employee_name}}`.

#### Source section list (ordered, verbatim headings)

1. `# Teams Message Formatting`
2. `### Example Teams body`

(A numbered rule list (1-7) sits between the H1 and the `### Example Teams body` block; the list is not under its own `##` heading in the source.)

#### Source identity-sensitive content inventory

- Named addressee: "Derek" (reviewer) on line 11 — replace with `{{employee_name}}`.
- Named agent: "Chiron" in the `description` (line 1), the rule-5 signature mandate (line 14), and the example payload body (line 25) — strip; signing convention pointer now lives in `outbound-messaging-guardrail.mdc`.
- "Deke's AI" appears in the example payload body (line 25) — strip.
- Fenced JSON payload (lines 22-29) carries real names: `"Can you go ahead and cancel Derek's one-on-one with Tiffany today? He's already spoken with her, just needs it off the calendar. -- Chiron (Deke's AI)"`. Target payload MUST be an anonymized neutral work sentence per AC6.

Fenced JSON payloads present: one (`### Example Teams body`). Preserved in the target under the same heading, anonymized.

### Source rule 4 — `email-triage-thread-defaults.mdc`

- Path: `~/Public/gtd-life/.cursor/rules/email-triage-thread-defaults.mdc`
- Size: 2120 bytes, 37 lines
- Accessible: yes

#### Source frontmatter

```yaml
description: Default email triage thread detail and archive behavior
globs:
alwaysApply: true
```

- Frontmatter is well-formed (opening `---` on line 1, closing `---` on line 5).
- `globs:` value is empty (bare key) — target port locks as explicit `[]`.

#### Source section list (ordered, verbatim headings)

1. `# Email Triage Thread Defaults`
2. `## Gmail: Inspiration routing (`Inspire` / `inspire`)`

(A numbered rule list (1-5, with a duplicated `5.` numbering bug in the source) sits between the H1 and the `## Gmail ...` section; the triage rule body is not under its own `##` heading in the source.)

#### Source identity-sensitive content inventory

- Google-property references in the `## Gmail: Inspiration routing` section (lines 27-37): `Gmail`, `INBOX` label, `Chiron/Inspiration` label, `Chiron/InspirationProcessed` label, `google-workspace` MCP, `google-workspace` `addGmailLabel` / `removeGmailLabel` operations, "extract → email to personal Gmail" bridge paragraph. The entire `## Gmail ...` section must be deleted in the port (per AC4 and Task 6 subtask "Explicitly DO NOT port the source file's `## Gmail: Inspiration routing (Inspire / inspire)` section").
- `blog inspiration processing` reference (line 33) — `blog` is banned by the scrub scan.
- No named individuals in the non-Gmail portion of the rule.
- `Outlook` appears once on line 9 (`When processing Outlook triage requests`). Target port rephrases as "Microsoft 365 email triage requests" per the source-to-target scrub map. Story 2.1's identity rule bans `Outlook` entirely as Story 2.2 deferred content; Story 2.2 rules may mention it only in the "Microsoft 365 (Outlook)" phrasing where strictly needed, and Task 2's blueprint prefers pure "Microsoft 365" phrasing to avoid the stack name entirely.
- Microsoft Graph thread primitive `conversationId` appears on lines 15, 25 — KEPT verbatim; positive assertion for Task 8's memory-path harness-twin.

No fenced JSON payloads in this source file.

## Target paths (post-Story-2.1 state)

| Target path | Current state |
| ----------- | -------------- |
| `.cursor/rules/outbound-messaging-guardrail.mdc`  | does **not** exist |
| `.cursor/rules/memory-vault-protection.mdc`       | does **not** exist |
| `.cursor/rules/teams-dm-formatting.mdc`           | does **not** exist |
| `.cursor/rules/email-triage-thread-defaults.mdc`  | does **not** exist |

Directory state snapshot on 2026-04-20 (pre-Task-3 authoring):

```
.cursor/rules/
├── .gitkeep            (Story 1.1 sentinel)
└── agent-identity.mdc  (Story 2.1 output)
```

No other `.mdc` files present. No pre-existing file conflicts. Story 1.1's extension-based allowlist (Story 2.1 Phase 4 F7 refactor) admits any `*.mdc` under `.cursor/rules/` — the four new files will land without harness edits.

## Banned-term set for Story 2.2 scrub scan

Case-insensitive, whole-file scan of each of the four new rule files. Any match is a FAIL.

### Story 2.1 banned-term carryover (identity / biography)

- `Derek`
- `Deke` (POSIX-ERE boundary-guarded: `(^|[^A-Za-z])deke($|[^A-Za-z])`)
- `Neighbors`
- `Chiron`
- `RevivaGo`
- `derekneighbors.com`
- `Agile Weekly`
- `MasteryLab`
- `Bodybuilding.com`
- `Gangplank`
- `ASU` (POSIX-ERE boundary-guarded: `(^|[^A-Za-z])ASU($|[^A-Za-z])`)
- `gtd-life`
- `arete` (POSIX-ERE boundary-guarded: `(^|[^A-Za-z])arete($|[^A-Za-z])`)
- `eudaimonia` (POSIX-ERE boundary-guarded: `(^|[^A-Za-z])eudaimonia($|[^A-Za-z])`)
- `blog` (POSIX-ERE boundary-guarded: `(^|[^A-Za-z])blog($|[^A-Za-z])`)

### Story 2.1 banned-term carryover (email / calendar stack)

- `Gmail`
- `Google Calendar`
- `Google Workspace`
- `personal email`

### Story 2.2 additions

- `Slack` (POSIX-ERE boundary-guarded: `(^|[^A-Za-z])slack($|[^A-Za-z])`) — Teams is the internal chat surface at Vixxo; Slack must not appear in the ported rule pack. Boundary guards keep English fragments such as "slackened" or "slacks" from false-positiving (not expected in any rule body, but the guard costs nothing and keeps the regex symmetric with the other short tokens).
- `Benji` (POSIX-ERE boundary-guarded: `(^|[^A-Za-z])benji($|[^A-Za-z])`) — Story 2.4 explicitly excludes `benji-inbox-default.mdc`; any `benji` reference in this story's rule bodies is a deferred-content violation.

### Story 2.2 deferred-content signal (contextual, per-file)

- `Outlook` standalone — per Task 1 story subtask, prefer pure "Microsoft 365" phrasing; only allow `Microsoft 365 (Outlook)` compound phrasing where strictly needed. Enforced as a soft guidance rule for authoring (Task 2 blueprint captures the authorized phrasings) rather than as a hard banned-term regex.

## Required present tokens (AC positive gates, per file)

| File | Required tokens |
| ---- | --------------- |
| `outbound-messaging-guardrail.mdc` | `{{employee_name}}`, `Microsoft Teams`, `Microsoft 365`, `-- AI assistant for {{employee_name}}` |
| `memory-vault-protection.mdc` | `{{employee_name}}`, `memory/me/identity.md`, `memory/me/preferences.md`, `memory/meetings/_template/`, `meeting.md`, `agenda.md`, `prep.md`, `transcript.md`, `memory/people/_template.md`, `memory/decisions/_template.md`, `memory/reference/_template.md`, `memory/inbox/_template.md`, `memory/appreciations/_template.md`, `work context only` |
| `teams-dm-formatting.mdc` | `{{employee_name}}`, `Microsoft Teams`, `"contentType": "html"`, `<p>`, `-- AI assistant for {{employee_name}}` |
| `email-triage-thread-defaults.mdc` | `{{employee_name}}`, `Microsoft 365`, `conversationId`, `Ask`, `Decision`, `FYI`, `Open`, `Closed`, `Waiting`, `Superseded` |

## Source-to-target scrub map (consolidated)

(Per-file detail already sits in the story's Dev Notes section under "Source-to-target scrub map (per file)". The table below is the consolidated quick-reference.)

| Source concept (any file) | Target treatment |
| ------------------------- | ---------------- |
| `Derek` / `Deke` / `Neighbors` / `Derek Neighbors` | `{{employee_name}}` |
| `Chiron` / `Deke's AI` (agent proper name) | REMOVED; signing convention owned by `outbound-messaging-guardrail.mdc` as `-- AI assistant for {{employee_name}}` |
| `Slack messages` platform entry | REMOVED from covered-platforms list |
| `SMS / iMessage` platform entries | REMOVED from covered-platforms list |
| `Email (Outlook, Gmail, any provider)` platform entry | REPLACED with `Microsoft 365 email (Outlook on the M365 stack)` or simply `Microsoft 365 email` |
| `gtd-life` repository name | REMOVED |
| `personal AI life operating system` framing | REPLACED with `work context only knowledge vault` |
| `PII is the product` framing | REPLACED with `work notes are the product — curated deliberately by {{employee_name}}` |
| `family, home, org charts, property info` examples | REPLACED with Epic 3 memory surfaces (meetings, people, decisions, reference, inbox, appreciations, me/identity, me/preferences) |
| `family.md` / `ventures.md` file references | REMOVED |
| Teams example JSON body ("cancel Derek's one-on-one with Tiffany…") | REPLACED with anonymized neutral work sentence wrapped in `<p>` |
| `## Gmail: Inspiration routing (Inspire / inspire)` section | ENTIRELY REMOVED |
| `Chiron/Inspiration` label | REMOVED |
| `Chiron/InspirationProcessed` label | REMOVED |
| `INBOX` label manipulation | REMOVED |
| `google-workspace` MCP reference | REMOVED |
| `Outlook-sourced inspiration during M365 triage` bridge paragraph | REMOVED |
| Missing opening `---` in `teams-dm-formatting.mdc` source frontmatter | FIXED — target file has opening `---` on line 1 |

## Confirmation of prerequisites

- Story 2.1 landed `.cursor/rules/agent-identity.mdc` with `Related Rule Files` pointer to the four sibling files this story authors.
- Story 2.1 validation harness (`story-2-1-agent-identity-validation.sh`) present and passing; POSIX-ERE boundary-guard probe (`regex_self_probe`) pattern available for Story 2.2 to inherit and extend with the two new tokens (`slack`, `benji`).
- Story 1.1's extension-based `.cursor/rules/*.mdc` allowlist (Story 2.1 Phase 4 F7 refactor) confirmed — no edits to the Story 1.1 harness are needed for Story 2.2.
- Story 1.3 root files (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`) present and use matching `{{employee_name}}` / `{{employee_role}}` placeholders; no new placeholder tokens required by Story 2.2.
- Upstream `~/Public/gtd-life/.cursor/rules/` source tree accessible; all four source files read successfully.

Baseline complete. Proceeds to Task 2 canonical blueprint lock.
