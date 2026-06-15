# Story 2.2: Port guardrail and formatting rules

Status: done

## Story

As the AI in a cloned Vixxo `assistants-template` workspace,
I want the same outbound-messaging, memory-vault-protection, Teams DM formatting, and email-triage thread-default rules that `gtd-life` uses — generalized, work-only, and placeholder-driven —
so that every employee inherits proven guardrails without re-deriving them and without inheriting any personal or RevivaGo context.

## Acceptance Criteria

1. **AC1 — Four sibling `.cursor/rules/*.mdc` files exist with correct Cursor Rules v6.x frontmatter**
   - Given the cloned `assistants-template` repository after Story 2.1 landed `agent-identity.mdc`
   - When `.cursor/rules/` is listed
   - Then the following four files exist as real rule files (not `.gitkeep`), in addition to `agent-identity.mdc`:
     - `.cursor/rules/outbound-messaging-guardrail.mdc`
     - `.cursor/rules/memory-vault-protection.mdc`
     - `.cursor/rules/teams-dm-formatting.mdc`
     - `.cursor/rules/email-triage-thread-defaults.mdc`
   - And each file begins with a YAML frontmatter block delimited by `---` on line 1 and a matching `---` line
   - And each file's frontmatter contains `description`, `globs`, and `alwaysApply` keys consistent with Cursor Rules v6.x conventions
   - And every rule sets `alwaysApply: true` (these are baseline guardrails that must attach to every conversation)
   - And `globs:` is `[]` for `outbound-messaging-guardrail.mdc`, `teams-dm-formatting.mdc`, and `email-triage-thread-defaults.mdc`; `globs: memory/**` only for `memory-vault-protection.mdc`

2. **AC2 — Every rule uses `{{snake_case}}` placeholders for identity-sensitive content; zero hard-coded employee names**
   - Given all four rule files
   - When the bodies are scanned for identity-sensitive references
   - Then every reference to the employee is rendered as `{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, or `{{employee_manager}}` (the same placeholder set Story 1.3 and Story 2.1 established)
   - And no hard-coded employee proper name, assistant proper name (e.g. "Chiron"), family member name, or company proper name other than "Vixxo" appears in any rule
   - And no sibling rule introduces a new placeholder token that is not already used by Story 1.3 (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`) or Story 2.1 (`agent-identity.mdc`); if a new identity field is required, it MUST follow the `{{snake_case}}` convention and be recorded in the Dev Notes for Story 2.3/3.3 consumption

3. **AC3 — Banned-term scrub passes on every ported rule**
   - Given the four rule files
   - When each file is scanned case-insensitively with the Story 2.1 banned-term set PLUS `slack` (Teams is the internal chat surface) PLUS `benji` (Benji todos are explicitly not ported per Story 2.4)
   - Then each file contains zero occurrences of: `Derek`, `Deke`, `Neighbors`, `Chiron`, `RevivaGo`, `derekneighbors.com`, `Agile Weekly`, `MasteryLab`, `Bodybuilding.com`, `Gangplank`, `ASU`, `gtd-life`, `arete`, `eudaimonia`, `blog`, `Gmail`, `Google Calendar`, `Google Workspace`, `personal email`, `Slack`, `Benji`
   - And the scrub uses the same POSIX-ERE boundary guards Story 2.1 established (so `ASU`, `blog`, `deke`, `arete`, `eudaimonia` do not false-positive on legitimate English fragments)
   - And a regex self-probe verifies the host grep honors those boundary guards (fail-fast if not)

4. **AC4 — M365-only email and calendar routing preserved; zero Gmail/Google references anywhere in the rule pack**
   - Given `email-triage-thread-defaults.mdc` (and any other rule that mentions email or calendar)
   - When each file is scanned
   - Then the only email stack referenced is Microsoft 365 (Outlook/Exchange), phrased as "Microsoft 365" where the stack is named
   - And the source rule's `## Gmail: Inspiration routing` section is entirely removed (no mention of Gmail, INBOX label operations, `Chiron/Inspiration`, or `google-workspace` MCP)
   - And no rule mentions Google Calendar, Google Workspace, Google Drive, or any other Google property

5. **AC5 — Teams is the only internal chat surface; Slack and personal messaging surfaces are removed**
   - Given `outbound-messaging-guardrail.mdc` and `teams-dm-formatting.mdc`
   - When the "platforms covered by the draft-then-approve workflow" list is reviewed
   - Then the list includes Microsoft Teams (channel posts, replies, DMs, group chats), Microsoft 365 email (Outlook), and explicitly excludes Slack, SMS, iMessage, and any other personal messaging surface
   - And `teams-dm-formatting.mdc` describes the Teams HTML payload workflow (plain-text draft → approval → Teams HTML at send time) without naming any specific human recipient

6. **AC6 — Graph API Comment/Teams payload examples are described generically with no personal handles**
   - Given `teams-dm-formatting.mdc` and any outbound-messaging rule that references payload shapes
   - When any embedded example JSON is inspected
   - Then example payload bodies use neutral placeholder content (e.g. a generic scheduling or status-update sentence) and MUST NOT include any hard-coded human name, email address, employee ID, Microsoft Graph user ID/UPN, Teams `chatId`, or other personal identifier
   - And inline Graph API references (e.g. `graph.microsoft.com`) may appear only to cite the public API surface; they must not carry identifiable URL parameters or request payloads scraped from any real conversation
   - And fenced JSON blocks are retained only where the source rule had one, and only in `teams-dm-formatting.mdc` (other rules keep prose pointers rather than inline JSON)

7. **AC7 — `memory-vault-protection.mdc` enumerates the Epic 3 memory paths and is work-only**
   - Given the Epic 3 memory layout (Stories 3.1 and 3.3)
   - When `memory-vault-protection.mdc` is opened
   - Then the rule body explicitly enumerates the Epic 3 memory surfaces that must not be deleted or silently redacted: `memory/me/identity.md`, `memory/me/preferences.md`, `memory/meetings/_template/` (with `meeting.md`, `agenda.md`, `prep.md`, `transcript.md`), `memory/people/_template.md`, `memory/decisions/_template.md`, `memory/reference/_template.md`, `memory/inbox/_template.md`, `memory/appreciations/_template.md`
   - And the rule asserts the vault is work context only (no language suggesting "personal AI life operating system" or "PII is the product" — that was `gtd-life`-specific and must not survive the port)
   - And the rule preserves the original protective intent: do not delete memory files for PII reasons, do not silently redact, do fix real YAML/markdown/cross-reference problems, and restore any deletion by automated tools

8. **AC8 — `email-triage-thread-defaults.mdc` references Microsoft 365 email semantics and thread handling only**
   - Given the ported `email-triage-thread-defaults.mdc`
   - When the body is reviewed
   - Then the triage rule retains: thread-handling as the default, per-message entries (newest to oldest) with sender/timestamp/subject/summary/tag/status, no collapsed summaries, narrow line-width discipline, and archive-all-same-conversation behavior on archive
   - And the rule specifies `conversationId` as the Microsoft Graph/Outlook thread key; no reference to Gmail `threadId`, Gmail labels, or any non-Microsoft thread primitive
   - And the rule ends with a one-line "why" comment per the Epic 2 Story 2.2 acceptance criterion

9. **AC9 — Each rule file ends with a one-line "why" comment (Epic 2 Story 2.2 AC)**
   - Given each of the four ported rule files
   - When the last non-blank line of each file is inspected
   - Then the last non-blank line is a single-line comment (markdown italic, markdown blockquote, or HTML comment form) that states the reason the rule exists in one sentence
   - And the "why" comment is itself scrubbed (contains no banned terms and no hard-coded names)

10. **AC10 — Cross-reference integrity with Story 2.1 `agent-identity.mdc`**
    - Given `agent-identity.mdc` contains a `## Related Rule Files` section pointing to "outbound-messaging, memory-vault-protection, Teams formatting, and email-triage detail live in sibling `.cursor/rules/*.mdc` files"
    - When Story 2.2 lands
    - Then every sibling file referenced by that pointer now exists with a matching filename (`outbound-messaging-guardrail.mdc`, `memory-vault-protection.mdc`, `teams-dm-formatting.mdc`, `email-triage-thread-defaults.mdc`)
    - And `agent-identity.mdc` is NOT regressed by this story (no edits beyond what is strictly required to correct or tighten the sibling-file pointer; prefer zero edits)
    - And none of the four sibling rules inline identity content that duplicates `agent-identity.mdc`'s Scope/Who-the-Employee-Is blocks

11. **AC11 — Root context files (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`) and Story 2.1 rule remain consistent**
    - Given the four new rule files
    - When Story 1.3 root files and Story 2.1 `agent-identity.mdc` are re-examined
    - Then no Story 1.3 or Story 2.1 content is regressed or contradicted by any sibling rule
    - And placeholder usage (`{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}`) stays byte-for-byte consistent across the rule pack
    - And Story 1.1's extension-based `.cursor/rules/*.mdc` allowlist (refactored in Story 2.1 Phase 4 F7) continues to accept all four new rule files without further edits to the Story 1.1 harness

12. **AC12 — Deterministic validation harness exists and passes; regression-runs Story 1.x and 2.1 harnesses**
    - Given this story's test directory `_bmad-output/implementation-artifacts/tests/`
    - When `bash _bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh all` is run
    - Then it prints `PASS: all` and exits `0`
    - And individual gates `task1` through `taskN` each print `PASS: <task>` when invoked independently
    - And the harness covers: file existence (four new `.mdc` files), per-file frontmatter shape (description/globs/alwaysApply), `globs: memory/**` only for `memory-vault-protection.mdc`, banned-term scan (including `slack` and `benji` additions plus the Story 2.1 POSIX-ERE boundary probe), placeholder presence/parity across the rule pack, deferred-content boundary (rules must not duplicate `agent-identity.mdc`'s identity block), AC5 Teams-only chat surface assertion, AC4 M365-only email/calendar assertion, AC7 memory-path enumeration for `memory-vault-protection.mdc`, AC9 "why" comment terminator for each file, and regression invocation of `story-1-1-scaffold-validation.sh all`, `story-1-2-root-files-validation.sh all`, `story-1-3-root-context-validation.sh all`, and `story-2-1-agent-identity-validation.sh all`

## Tasks / Subtasks

- [x] Task 1 — Baseline audit of the four source rules and target location (AC: 1, 2, 3, 4, 5, 6, 7, 8)
  - [x] Read `~/Public/gtd-life/.cursor/rules/outbound-messaging-guardrail.mdc`, `~/Public/gtd-life/.cursor/rules/memory-vault-protection.mdc`, `~/Public/gtd-life/.cursor/rules/teams-dm-formatting.mdc`, and `~/Public/gtd-life/.cursor/rules/email-triage-thread-defaults.mdc`. Capture each source file's frontmatter, top-level section list, and any example JSON payloads.
  - [x] Confirm the four target paths under `.cursor/rules/` do not yet exist (Story 2.1 authored only `agent-identity.mdc` under that directory).
  - [x] Record the full banned-term set for Story 2.2's scrub scan: everything in Story 2.1's banned list (`Derek`, `Deke`, `Neighbors`, `Chiron`, `RevivaGo`, `derekneighbors.com`, `Agile Weekly`, `MasteryLab`, `Bodybuilding.com`, `Gangplank`, `ASU`, `gtd-life`, `arete`, `eudaimonia`, `blog`, `Gmail`, `Google Calendar`, `Google Workspace`, `personal email`) PLUS `Slack` (Teams is the Vixxo chat surface) PLUS `Benji` (Story 2.4 explicitly excludes `benji-inbox-default.mdc`) PLUS `Outlook` appearing in non-"Microsoft 365" context (keep "Microsoft 365 (Outlook)" style phrasing only where strictly needed; prefer "Microsoft 365").
  - [x] Record the source-to-target scrub map (see Dev Notes table) per file so Tasks 3–6 can author directly from a locked blueprint.
  - [x] Persist baseline evidence at `_bmad-output/implementation-artifacts/tests/story-2-2-baseline-audit.md`, one subsection per source file plus the consolidated banned-term list.

- [x] Task 2 — Design canonical generic blueprint for all four rules (AC: 1, 2, 5, 6, 7, 8, 9, 10)
  - [x] Lock per-file section layout and frontmatter values. Each file gets an `Overview` or `Rule` block, a numbered or bulleted list of behaviors, and (where applicable) a single example block. Record section headers exactly.
  - [x] Lock placeholder inventory for each file: which of `{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}` appears where. Introduce no new placeholder tokens unless strictly required; if required, record them for Story 2.3/3.3 to consume.
  - [x] Lock the generic `teams-dm-formatting.mdc` example JSON payload — neutral work sentence, no personal names, no email addresses, `contentType: "html"`, single `<p>` wrapper. Example body may reference `{{employee_name}}` as the drafting addressee only if strictly necessary for context; prefer a completely anonymized sentence.
  - [x] Lock the per-file one-line "why" comment that will terminate each file (AC9). Avoid banned terms.
  - [x] Lock the Epic 3 memory-path enumeration for `memory-vault-protection.mdc`: `memory/me/identity.md`, `memory/me/preferences.md`, `memory/meetings/_template/{meeting,agenda,prep,transcript}.md`, `memory/people/_template.md`, `memory/decisions/_template.md`, `memory/reference/_template.md`, `memory/inbox/_template.md`, `memory/appreciations/_template.md`.
  - [x] Persist the locked blueprint at `_bmad-output/implementation-artifacts/tests/story-2-2-canonical-blueprint.md` with one subsection per file and a cross-AC coverage table (similar structure to Story 2.1's blueprint).

- [x] Task 3 — Author `.cursor/rules/outbound-messaging-guardrail.mdc` (AC: 1, 2, 3, 4, 5, 6, 9, 10) **[Parallelizable with Tasks 4, 5, 6 once Task 2 is locked]**
  - [x] Write frontmatter: `description: "CRITICAL safety guardrail - all outbound messaging must be drafted and explicitly approved before send"`, `globs: []`, `alwaysApply: true`.
  - [x] Header: `# Outbound Messaging Guardrail (Mandatory)` followed by a one-line non-negotiability statement.
  - [x] Body section `## The Rule`: mandate the draft-then-approve flow; phrase the approval requirement in terms of `{{employee_name}}` (not "Derek").
  - [x] Body section `## Platforms Covered`: list Microsoft Teams (channel posts, replies, DMs, group chats), Microsoft 365 email (Outlook on the M365 stack), and any additional Vixxo outbound surfaces the employee wires later. Do NOT list Slack, SMS, iMessage, Gmail, Google Chat, or any other non-Vixxo channel.
  - [x] Body section `## Required Workflow`: 1) Draft in plain text and show to `{{employee_name}}`; 2) Wait for explicit approval token ("send it", "go", "fire", "approved", or equivalent); 3) Only then call the send/reply API.
  - [x] Body section `## No Exceptions`: the "reply to this", "respond to that", "tell them X", "send X to Y" phrasings are draft-and-show, not authorization to send. Preserve this paragraph's intent.
  - [x] Body section `## Signing Convention`: generic and placeholder-driven. No "Chiron" or assistant proper name. Recommended phrasing: Teams outbound messages signed inline at the end of the last paragraph as `-- AI assistant for {{employee_name}}` (or an equivalent placeholder-only form); emails do NOT add an assistant signature (the employee's email signature handles it); messages drafted to be sent in `{{employee_name}}`'s voice do NOT carry an AI sign-off.
  - [x] Terminate the file with a one-line "why" comment (AC9), e.g. `<!-- Why: protects recipients and {{employee_name}}'s reputation from unauthorized AI-sent messages. -->`.
  - [x] Zero embedded JSON, zero Graph API payload examples (the Graph/Teams payload example belongs to `teams-dm-formatting.mdc` per Task 5).

- [x] Task 4 — Author `.cursor/rules/memory-vault-protection.mdc` (AC: 1, 2, 3, 7, 9, 11) **[Parallelizable with Tasks 3, 5, 6 once Task 2 is locked]**
  - [x] Write frontmatter: `description: "Protects the work memory vault from accidental deletion or redaction by any agent"`, `globs: memory/**`, `alwaysApply: true`.
  - [x] Header: `# Memory Vault Protection`.
  - [x] Opening paragraph: describe `assistants-template`'s `memory/` directory as a **work context only** knowledge vault containing the employee's meeting notes, people files, decisions, references, inbox captures, and appreciations. Do NOT copy the source rule's "personal AI life operating system" or "PII is the product" framing — that was `gtd-life`-specific and is banned here.
  - [x] Body section `## Protected Surfaces`: enumerate the Epic 3 memory paths exactly as listed in AC7 and Task 2. Use bullet list with backticked paths.
  - [x] Body section `## Rules` (numbered list): 1) Never delete files in `memory/`; 2) Never silently remove or redact content from memory files (work notes are the product, not a vulnerability — curated deliberately by `{{employee_name}}`); 3) Never flag legitimate work memory as a security concern (this is a private repo the employee owns); 4) DO fix real problems — broken YAML frontmatter, malformed markdown, incorrect cross-references, syntax errors; 5) If another agent or automated tool has deleted memory files, restore them immediately.
  - [x] Terminate the file with a one-line "why" comment (AC9), e.g. `<!-- Why: the work memory vault is {{employee_name}}'s source of truth — deletions cost meetings, decisions, and context. -->`.
  - [x] Zero references to `family.md`, `ventures.md`, or any other gtd-life-specific memory file.

- [x] Task 5 — Author `.cursor/rules/teams-dm-formatting.mdc` (AC: 1, 2, 3, 5, 6, 9, 10) **[Parallelizable with Tasks 3, 4, 6 once Task 2 is locked]**
  - [x] Write frontmatter: `description: "Formatting rules for Microsoft Teams messages drafted for {{employee_name}}"`, `globs: []`, `alwaysApply: true`. Note: the frontmatter `description` text may include the placeholder because Cursor renders raw frontmatter; it stays portable.
  - [x] Header: `# Teams Message Formatting`.
  - [x] Opening paragraph: scope to "Microsoft Teams (DMs, group chats, channel posts, and replies)" — no Slack/iMessage/SMS.
  - [x] Numbered rule list (preserve the source's intent, generalize names): 1) Treat Teams like text messaging, not email; 2) Plain-text review first (show `{{employee_name}}` a plain-text draft for approval — do not present HTML in drafts unless requested); 3) Convert only at send time (map plain-text draft to Teams HTML payload after approval); 4) No greeting or name prefix in DMs; 5) Inline signature convention (reference the signing rule owned by `outbound-messaging-guardrail.mdc`; do not duplicate it verbatim here); 6) Keep it tight (prefer one short paragraph); 7) Use HTML payloads (`contentType: "html"` with a single `<p>` in the common case).
  - [x] Short paragraph: `@mentions` allowed in channel posts when useful; keep the same concise text-message style and inline sign-off.
  - [x] `### Example Teams body` fenced JSON block: a single Graph API-shaped Teams payload with `contentType: "html"` and a single `<p>` wrapper. The body MUST be a neutral work sentence with zero personal names, zero email addresses, zero Graph user IDs, and zero `chatId` strings. Suggested content: `<p>Short status update. -- AI assistant for {{employee_name}}</p>` or an equivalent anonymized sentence.
  - [x] Terminate the file with a one-line "why" comment (AC9), e.g. `<!-- Why: Teams is conversational — walls of text and wrong signatures cost trust. -->`.
  - [x] Zero mention of Slack, Discord, Mattermost, iMessage, SMS.

- [x] Task 6 — Author `.cursor/rules/email-triage-thread-defaults.mdc` (AC: 1, 2, 3, 4, 8, 9, 10) **[Parallelizable with Tasks 3, 4, 5 once Task 2 is locked]**
  - [x] Write frontmatter: `description: "Default Microsoft 365 email triage thread detail and archive behavior"`, `globs: []`, `alwaysApply: true`.
  - [x] Header: `# Email Triage Thread Defaults`.
  - [x] Opening paragraph: scope to "Microsoft 365 triage requests (`/email-triage`, 'triage my email', 'process my inbox')". No Gmail, no Google Workspace, no personal email.
  - [x] Numbered rule list (preserve source intent): 1) Treat thread handling as the default, not optional; 2) For each threaded message, gather current message body, quoted history in body, and other Inbox items with the same Microsoft Graph `conversationId`; 3) Present thread details as per-message entries (newest to oldest) each with sender, timestamp, subject, detailed message summary or full cleaned body (not a 1–2 sentence blurb; capture asks, decisions, dates, names, action items), explicit tag (`Ask` / `Decision` / `FYI`), and status (`Open` / `Closed` / `Waiting` / `Superseded`); 4) Never collapse thread context into a single oversized paragraph; 5) Line-width discipline — narrow enough to read without horizontal scrolling; break long lines, use short paragraphs, add vertical whitespace between sections, no wall-of-text blocks; 6) On `Archive`, archive ALL same-`conversationId` messages currently in Inbox.
  - [x] Explicitly DO NOT port the source file's `## Gmail: Inspiration routing (Inspire / inspire)` section. No `Chiron/Inspiration` label, no `INBOX` label manipulation, no `google-workspace` MCP reference, no Gmail bridge, no "extract → email to personal Gmail" workflow. This entire subsection is removed.
  - [x] Terminate the file with a one-line "why" comment (AC9), e.g. `<!-- Why: email threads lose signal when collapsed; preserve structure so {{employee_name}} can decide fast. -->`.

- [x] Task 7 — Cross-file scrub, placeholder parity, and deferred-content checks (AC: 2, 3, 5, 10, 11) **[Sequential — depends on Tasks 3–6 artifacts]**
  - [x] Run case-insensitive `grep -i -E` (or `rg -n -i` if available) scan over all four new rule files using the Story 2.2 banned-term set (Story 2.1 list + `slack` + `benji`). Require zero matches per file.
  - [x] Verify each placeholder token used in any new rule file (`{{employee_name}}` / `{{employee_role}}` / `{{employee_department}}` / `{{employee_manager}}`) is already in use in `agent-identity.mdc`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, or explicitly recorded in this story's blueprint as a new token. No accidental placeholder drift.
  - [x] Verify none of the four new rule files contain a duplicated identity block (i.e. they do not restate `agent-identity.mdc`'s `## Scope` or `## Who the Employee Is` content). The sibling rules point to `agent-identity.mdc` for identity and focus on their own single concern.
  - [x] Verify `memory-vault-protection.mdc` contains every Epic 3 memory path listed in AC7 (positive assertion) and contains ZERO mentions of `family.md` or `ventures.md` (negative assertion).
  - [x] Verify `email-triage-thread-defaults.mdc` contains `conversationId` and Microsoft 365 framing, and contains zero Gmail terms, zero `INBOX` label references, and zero `Chiron/Inspiration` references.
  - [x] Verify `teams-dm-formatting.mdc` contains the `contentType: "html"` payload shape and no hard-coded personal identifier inside the fenced JSON block.
  - [x] Verify each file terminates with a one-line "why" comment (AC9) and that the comment contains zero banned terms.

- [x] Task 8 — Deterministic validation harness (AC: 12) **[Scaffoldable in parallel with Tasks 3–6; final wiring depends on their artifacts]**
  - [x] Create `_bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh` modeled on `story-2-1-agent-identity-validation.sh`. POSIX-bash-3.2 compatible, `set -euo pipefail`, print `PASS: <gate>` / `FAIL: <gate>: <reason>`.
  - [x] Gates (suggested): `task1` baseline-audit-evidence, `task2` blueprint-evidence, `task3` outbound-messaging rule shape + content, `task4` memory-vault-protection rule shape + memory-path enumeration, `task5` teams-dm-formatting rule shape + JSON-payload hygiene, `task6` email-triage rule shape + Microsoft 365 semantics + Gmail-section absence, `task7` cross-file scrub (banned-term scan with `slack`+`benji` additions, placeholder parity, deferred-identity check, "why"-comment terminator), `task8` self-check (harness well-formed), `task9` regression against `story-1-1` / `story-1-2` / `story-1-3` / `story-2-1` harnesses, `all` runs every gate in order.
  - [x] Reuse the Story 2.1 POSIX-ERE banned-term regex (with the `(^|[^A-Za-z])...($|[^A-Za-z])` boundary guards for `ASU`, `blog`, `deke`, `arete`, `eudaimonia`) and ADD `(^|[^A-Za-z])slack($|[^A-Za-z])` and `(^|[^A-Za-z])benji($|[^A-Za-z])` to the alternation. Include a `regex_self_probe` fail-fast gate identical in spirit to Story 2.1's (probe all boundary-guarded tokens).
  - [x] Frontmatter validation: parse each file's YAML block with `awk` between the first two `---` delimiters; assert `description`, `globs`, and `alwaysApply: true`. For `memory-vault-protection.mdc`, assert `globs:` value is `memory/**`; for the other three files, assert `globs:` value is `[]` (match Story 2.1's empty/`[]`/`""` allowlist).
  - [x] Required section headers per file (exact-line match with `grep -Fxq`): enumerate the locked headers from Task 2's blueprint for each file and require their presence.
  - [x] Per-file deferred-content check: none of the four sibling rules may contain the Story 2.1 identity scope tokens `Vixxo employee` AND `work context only` together (belong to `agent-identity.mdc`). Each sibling may reference those scope tokens briefly (in the "why" comment, for example), but must not restate both verbatim in the body.
  - [x] Teams-payload hygiene check for `teams-dm-formatting.mdc`: the fenced JSON block's payload content field must match a narrow allowlist (ASCII, no `@` email signs inside the sentence beyond Teams @mentions prose, no UUID-shaped tokens, no 10-digit phone numbers). Keep it simple: assert `"contentType": "html"` appears exactly once and assert zero `@[A-Za-z0-9._%+-]+@` email-address patterns inside the file.
  - [x] Memory-path enumeration check for `memory-vault-protection.mdc`: `grep -Fq` each of the Epic 3 paths from Task 2's blueprint. Fail if any is missing.
  - [x] Gmail-absence check for `email-triage-thread-defaults.mdc`: zero matches for `gmail`, `chiron/inspiration`, `inbox label`, `google-workspace` (case-insensitive).
  - [x] "Why"-comment terminator check: for each of the four files, the last non-blank line must match one of `^<!--.*-->$`, `^>`, or `^_.*_$` (HTML comment, markdown blockquote, or italic-wrapped single line).
  - [x] Self-check: shebang `#!/usr/bin/env bash`, `set -euo pipefail`, every case branch declared, banned-term regex and required-headers definitions present.
  - [x] Regression: `task9` invokes `bash story-1-1-scaffold-validation.sh all`, `bash story-1-2-root-files-validation.sh all`, `bash story-1-3-root-context-validation.sh all`, and `bash story-2-1-agent-identity-validation.sh all`. All four must return zero. Story 1.1's `check_task6` already uses the extension-based `.cursor/rules/*.mdc` allowlist (Story 2.1 Phase 4 F7 refactor) — no edits to that harness are required for Story 2.2.

- [x] Task 9 — Regression and handoff readiness package (AC: 10, 11, 12) **[Sequential — runs all prior gates]**
  - [x] Run `bash _bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh all` locally and capture output.
  - [x] Re-run Story 1.1, 1.2, 1.3, and 2.1 harnesses (`all` mode each) and confirm every one returns zero.
  - [x] Persist handoff artifact at `_bmad-output/implementation-artifacts/tests/story-2-2-task9-handoff.md` with an AC-to-file map (one row per AC with evidence pointer), full validation command transcript, and a forward-looking note that Story 2.3 will add `agents/personas/work.md` (referenced by `agent-identity.mdc` Key References) and Story 2.4 will assert `benji-inbox-default.mdc` is NOT present.

- [x] Task 10 — Sprint tracker and story status synchronization (AC: 12) **[Independent; can run last]**
  - [x] Flip `_bmad-output/implementation-artifacts/sprint-status.yaml` entry `2-2-port-guardrail-and-formatting-rules` from `backlog` to `ready-for-dev` during story-creation Phase 1 (this SM pass), and to `review` at dev handoff per the Story 2.1 autonomous-swarm pattern.
  - [x] Preserve `epic-2.status` as `in-progress` (already flipped by Story 2.1; Story 2.2 keeps it in-progress because Stories 2.3 and 2.4 remain).
  - [x] Preserve every comment and block in `sprint-status.yaml` exactly — the file is a human-curated YAML with inline comment sections that must not be reordered or stripped.

- [x] Review Follow-ups (AI) — Phase 4 code-review fix pass (F1–F6)
  - [x] **F3 (MEDIUM — AC5 explicit exclusion missing):** Added a blockquote exclusion line under `## Platforms Covered` in `.cursor/rules/outbound-messaging-guardrail.mdc`: `> Personal messaging surfaces (SMS, iMessage, personal chat apps) are explicitly out of scope — this workspace is Vixxo work-only.` Names SMS / iMessage / personal chat apps explicitly (AC5 wording) while preserving the Slack banned-term scrub (Slack is NOT named).
  - [x] **F3 harness side-effect:** Updated `check_task3` to strip blockquote lines (`^[[:space:]]*>`) before the `NON_TEAMS_CHAT_REGEX` scan. The exclusion blockquote legitimately names out-of-scope chat surfaces for AC5 clarity; the scan still rejects any naming of those surfaces outside the exclusion blockquote.
  - [x] **F1 (HIGH — AC6 coverage gap):** Added to `check_task4` and `check_task6` a fenced-JSON absence check (`^[[:space:]]*\`\`\`json`) and a broader fenced-code-block absence check (`^[[:space:]]*\`\`\``) so the harness enforces AC6's "prose pointers rather than inline JSON" constraint on the memory and email rules. AC6's allowed fenced JSON is now bounded exclusively to `teams-dm-formatting.mdc`.
  - [x] **F2 (HIGH — `\<` / `\>` portability risk):** Rewrote `require_why_comment_terminator` to use `grep -Eq '^<!--.*-->$'`, `grep -Eq '^>.*$'`, and `grep -Eq '^_.*_$'` instead of bash `[[ =~ ^\<!--.*--\>$ ]]`. Drops the ambiguous `\<` / `\>` escapes (GNU word-boundary anchors) in favor of plain POSIX-ERE so macOS BSD grep, GNU grep, and busybox grep all honor the literal `<` / `>` characters.
  - [x] **F4 (MEDIUM — AC10 pointer integrity):** Added `grep -Fq '## Related Rule Files' "${AGENT_IDENTITY_PATH}"` to `check_task7`. The Story 2.2 harness now bilaterally asserts that `agent-identity.mdc` still carries the `## Related Rule Files` section that Story 2.2 satisfies — not just that the file exists.
  - [x] **F5 (MEDIUM — `grep -c` counts lines):** Changed the `contentType` count to `grep -oF '"contentType": "html"' | wc -l | tr -d ' '` so two tokens on one line would correctly fail. Added a fence-pair assertion `fence_count="$(grep -cE '^[[:space:]]*\`\`\`' "${TEAMS_PATH}")"` requiring `fence_count -eq 2` (opener + closer) alongside the existing `json_count -eq 1` opener check; catches unclosed fenced blocks.
  - [x] **F6 (LOW — sub-harness output suppressed):** Rewrote each `bash ${HARNESS} all >/dev/null || fail …` call in `check_task9` to capture combined stdout/stderr (`out="$(bash ${HARNESS} all 2>&1)"`), echo the captured output to stderr on non-zero exit, and then fail the gate. A regression now surfaces the offending sub-gate instead of a silent non-zero exit.
  - [x] Re-ran `bash _bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh all` → exit 0, every gate `PASS: task1` through `PASS: task9` then `PASS: all`. Re-ran Story 1.1 / 1.2 / 1.3 / 2.1 harnesses in `all` mode → each exits 0 with `PASS: all`.

## Dev Notes

### Artifact availability

- Available planning/tracking artifacts:
  - `_bmad/bmm/config.yaml` (module metadata, artifact paths, BMAD v6.3.0).
  - `_bmad-output/planning-artifacts/epics.md` (Epic 2 Story 2.2 statement and ACs).
  - `_bmad-output/planning-artifacts/architecture.md` (placeholder-driven identity fields, rule-pack location `.cursor/rules/`).
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` (story lifecycle, Linear ID `AIP-30`).
  - Prior story files `1-1-scaffold-directory-structure-and-root-files.md`, `1-2-write-generic-readme-license-gitignore.md`, `1-3-write-generic-agents-claude-cursorrules.md`, `2-1-port-agent-identity-rule-generic.md` (pattern, validation harness model, scrub discipline, cross-reference model).
  - Landed Story 2.1 artifact `.cursor/rules/agent-identity.mdc` — this story authors the sibling rules its `Related Rule Files` section already points to.
- Missing at expected paths:
  - `_bmad-output/planning-artifacts/prd.md` (not present; rely on epics.md and sprint tracker).
  - `_bmad-output/planning-artifacts/ux-design-specification.md` (not relevant — rule-pack text only, no UI surface).
- Implementation anchors: Epic 2 Story 2.2 ACs, Story 2.1 harness pattern (POSIX-ERE boundary probe, extension-based scaffold allowlist, cross-file parity), upstream `~/Public/gtd-life/.cursor/rules/` source files.

### Epic 2 story partition (why 2.2 is the guardrail+formatting bundle)

- Story 2.1 (done): `agent-identity.mdc` only — identity, scope, employee fields, MCP overview, M365 routing pointer, sibling-rules pointer.
- Story 2.2 (this story): `outbound-messaging-guardrail.mdc`, `memory-vault-protection.mdc`, `teams-dm-formatting.mdc`, `email-triage-thread-defaults.mdc`. The detailed Graph API Comment workflow, Teams HTML formatting, M365 triage thread semantics, and memory-vault protection content all live here.
- Story 2.3: `agents/personas/work.md` (single generic work persona). Not this story.
- Story 2.4: confirm `benji-inbox-default.mdc` is NOT ported. Not this story (but this story's scrub MUST fail if anyone slips `benji` into a rule body).

Do not pre-implement Story 2.3 or 2.4 here. Reference `agents/personas/work.md` and the "Benji explicitly not ported" decision as pointers only.

### Source-to-target scrub map (per file)

#### `~/Public/gtd-life/.cursor/rules/outbound-messaging-guardrail.mdc` → `.cursor/rules/outbound-messaging-guardrail.mdc`

| Source concept | Generic target |
| -------------- | -------------- |
| "Derek" (approver) | `{{employee_name}}` |
| Slack messages in the covered-platforms list | REMOVED (Slack not used at Vixxo for this template) |
| Gmail / SMS / iMessage in the covered-platforms list | REMOVED (Vixxo work-only scope) |
| Outlook mentioned standalone | Phrase as "Microsoft 365 email (Outlook on the M365 stack)" or simply "Microsoft 365 email" |
| "`-- Chiron (Deke's AI)`" sign-off | Generic placeholder form: "`-- AI assistant for {{employee_name}}`" (or equivalent; no assistant proper name) |
| "Messages sent as Derek (leadership comms, strategy, feedback)" | Generic: "Messages drafted to be sent in `{{employee_name}}`'s voice" |

#### `~/Public/gtd-life/.cursor/rules/memory-vault-protection.mdc` → `.cursor/rules/memory-vault-protection.mdc`

| Source concept | Generic target |
| -------------- | -------------- |
| "gtd-life" repository name | REMOVED |
| "personal AI life operating system" framing | Rewritten: "work context only knowledge vault for `{{employee_name}}`" |
| "PII is the product" | Rewritten: "Work notes are the product — curated deliberately by `{{employee_name}}`" |
| Implicit "family, home, org charts, property info" examples | Replaced with Epic 3 surfaces (meetings, people, decisions, reference, inbox, appreciations, me/identity, me/preferences) |
| `globs: memory/**` | KEPT — same path scope |

#### `~/Public/gtd-life/.cursor/rules/teams-dm-formatting.mdc` → `.cursor/rules/teams-dm-formatting.mdc`

| Source concept | Generic target |
| -------------- | -------------- |
| Missing opening `---` in source frontmatter | FIXED — target file must have a proper opening `---` on line 1 |
| "Derek" (reviewer) | `{{employee_name}}` |
| `-- Chiron (Deke's AI)` signature | REMOVED as a standalone rule (signing convention lives in `outbound-messaging-guardrail.mdc`); this rule just points to the sibling signing rule |
| Example JSON body containing specific meeting details | Replaced with a neutral work sentence that contains zero personal names, e.g. `"Short status update. -- AI assistant for {{employee_name}}"` wrapped in `<p>` |
| "Chiron" in example signature | Generic placeholder form (see outbound rule) |

#### `~/Public/gtd-life/.cursor/rules/email-triage-thread-defaults.mdc` → `.cursor/rules/email-triage-thread-defaults.mdc`

| Source concept | Generic target |
| -------------- | -------------- |
| "Outlook triage requests" | Rephrased as "Microsoft 365 email triage requests (Outlook on the M365 stack)" |
| `conversationId` | KEPT (Microsoft Graph thread key) |
| `## Gmail: Inspiration routing (Inspire / inspire)` entire section | ENTIRELY REMOVED |
| `Chiron/Inspiration` label | REMOVED |
| `INBOX` label manipulation + `google-workspace` MCP | REMOVED |
| "Outlook-sourced inspiration during M365 triage" bridge paragraph | REMOVED |

### Signing-convention decision (placeholder contract)

The source rule pack signed outbound chat messages with the named agent `Chiron`. Story 2.1 removed all named-agent content from `agent-identity.mdc`; Story 2.2 must carry that forward. The placeholder contract for this story is:

- Inline Teams sign-off (recommended): `-- AI assistant for {{employee_name}}` — zero assistant proper name, zero personal identifier beyond the already-ported `{{employee_name}}` placeholder.
- Email: no AI sign-off (the employee's email signature handles it).
- Voice-of-employee messages (leadership comms, strategy, feedback): no AI sign-off; the message is drafted to read as `{{employee_name}}`'s own words.

Do NOT introduce a new placeholder like `{{assistant_name}}` unless Story 5.2 (wizard prompts) is willing to own it. If a future story adds `{{assistant_name}}`, the signing convention can be revised then; for now, the generic "AI assistant for {{employee_name}}" phrasing is sufficient and portable.

### Architectural constraints

- Template is repository-first; no runtime service, no code ships in `.cursor/rules/`. The four files are static markdown with YAML frontmatter.
- Cursor Rules v6.x frontmatter: `description`, `globs`, `alwaysApply`. `alwaysApply: true` means the rule attaches to every conversation in the workspace; this is appropriate for all four rules (guardrails + formatting baseline).
- `globs: memory/**` scopes `memory-vault-protection.mdc` to changes under `memory/`; the other three are `globs: []` (workspace-wide).
- Keep rule bodies concise — long prose degrades model adherence and lengthens the attached context budget per conversation.
- Placeholders: `{{snake_case}}` only. Story 1.3/2.1 established `{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}`. Do not introduce new placeholders unless strictly required; record any new tokens in Task 2's blueprint for Story 2.3/3.3 consumption.
- macOS/Linux portability: no rule body assumes a shell or binary.

### Previous story learnings to carry forward

- Story 1.1: `.cursor/rules/` extension-based allowlist (refactored in Story 2.1 Phase 4 F7) already admits any `*.mdc` file — no edits to the Story 1.1 harness are needed for Story 2.2.
- Story 1.2: banned-term scrub discipline applies to every new content artifact.
- Story 1.3: placeholder parity across the rule pack — this story must preserve it.
- Story 2.1: POSIX-ERE boundary guards (`(^|[^A-Za-z])TOKEN($|[^A-Za-z])`) for `ASU`, `blog`, `deke`, `arete`, `eudaimonia` — this story extends the pattern to `slack` and `benji`.
- Story 2.1: `regex_self_probe` fail-fast guard catches a mis-parsing host grep before the banned-term scan silently fails open. Reuse it and extend its probes for the two new boundary-guarded tokens.
- Story 2.1: harness outputs `PASS: <gate>` / `FAIL: <gate>: <reason>` to stderr for failures, exits 0 on pass and 1 on fail. `task5` self-check is cheap and catches authoring regressions early. Gate `taskN` for regression invokes `all` against every predecessor harness.
- Story 2.1: the autonomous-swarm lifecycle skipped the interim `in-progress` state on disk (`ready-for-dev → review` in a single Task 10 edit). Story 2.2 may follow the same pattern; record the skipped hops explicitly in the Change Log.

### Current Cursor Rules platform notes (v6.x, 2026)

- `description` must be a single concise line; multi-line descriptions confuse Cursor's rule picker.
- `globs:` accepts a YAML list; prefer the explicit `[]` or a single string like `memory/**`. Avoid bare YAML null.
- `alwaysApply: true` attaches the rule to every conversation in the workspace regardless of `globs`; if `alwaysApply: true`, `globs` is effectively informational for this file's scope.
- Multi-rule packs (like this Story's four sibling files) load in alphabetical order by filename, but each rule's body is merged into the conversation context independently; avoid duplication between files.

### Microsoft Graph + Teams payload notes

- Teams messages API body shape: `{"body": {"content": "<p>...</p>", "contentType": "html"}}`. Both `html` and `text` are valid `contentType` values; the source rule's choice of `html` to get inline formatting is kept as the default.
- Microsoft Graph mail threads are identified by `conversationId` (returned by `messages` endpoint). This is the correct Microsoft 365 thread primitive — no Gmail `threadId` equivalence needed.
- The `email-triage-thread-defaults.mdc` rule describes the workflow in prose; it does not embed a full Graph API request/response shape (those live in the agent-skills repo's actual skills, not in the template's rule pack).

### Project Structure Notes

- Target files for this story (new):
  - `.cursor/rules/outbound-messaging-guardrail.mdc`
  - `.cursor/rules/memory-vault-protection.mdc`
  - `.cursor/rules/teams-dm-formatting.mdc`
  - `.cursor/rules/email-triage-thread-defaults.mdc`
- Artifacts produced by this story under `_bmad-output/implementation-artifacts/tests/`:
  - `story-2-2-baseline-audit.md`
  - `story-2-2-canonical-blueprint.md`
  - `story-2-2-guardrail-and-formatting-validation.sh`
  - `story-2-2-task9-handoff.md`
- Adjacent paths that must remain intact:
  - `.cursor/rules/agent-identity.mdc` (Story 2.1 output; no edits beyond the strictly-required sibling-file pointer correction — prefer zero edits).
  - `.cursor/rules/.gitkeep` (Story 1.1 sentinel; may remain, harness does not require its presence once real rule files exist).
  - `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `README.md`, `LICENSE`, `.gitignore` (Stories 1.2/1.3 outputs).
- Forward-compatibility:
  - Story 2.3 will add `agents/personas/work.md`. This story's rule pack references `agents/personas/work.md` only via Story 2.1's `agent-identity.mdc` — no direct reference is added here.
  - Story 2.4 will assert `.cursor/rules/benji-inbox-default.mdc` is NOT present. This story's scrub actively fails on `benji`, and the Story 1.1 extension-based allowlist admits any `.mdc` under `.cursor/rules/` — Story 2.4's assertion is complementary, not superseded.
  - Story 3.1 will populate the memory-path targets `memory-vault-protection.mdc` enumerates (the rule is authored to protect paths that do not yet exist; that is intentional and safe under `alwaysApply: true` + `globs: memory/**`).

### Testing Notes

- Suggested manual commands:
  - `rg -n -i "derek|deke|neighbors|chiron|revivago|slack|benji|gmail|google calendar|google workspace|personal email|gtd-life" .cursor/rules/*.mdc` for scrub sanity (should return zero matches on all four new files and should already return zero on `agent-identity.mdc`).
  - `rg -n "\\{\\{employee_(name|role|department|manager)\\}\\}" .cursor/rules/*.mdc` for placeholder coverage.
  - `rg -n "alwaysApply:\\s*true" .cursor/rules/*.mdc` for frontmatter gate.
  - `rg -n "conversationId" .cursor/rules/email-triage-thread-defaults.mdc` for Microsoft Graph thread primitive.
  - `rg -n '"contentType":\\s*"html"' .cursor/rules/teams-dm-formatting.mdc` for Teams payload gate.
  - `bash _bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh all`
- Regression:
  - `bash _bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh all`
  - `bash _bmad-output/implementation-artifacts/tests/story-1-2-root-files-validation.sh all`
  - `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh all`
  - `bash _bmad-output/implementation-artifacts/tests/story-2-1-agent-identity-validation.sh all`
- Keep the Story 2.2 harness self-contained (no network, no external tools beyond `bash`, `grep`, `awk`, `sed`; `rg` is explicitly optional).

### Parallelization guidance

- Task 1 (baseline audit) and Task 2 (canonical blueprint) are sequential prerequisites.
- Tasks 3, 4, 5, and 6 (authoring the four rule files) are **pairwise parallelizable** once Task 2 is locked. Recommended dev-swarm assignment: one subagent per rule file. Each subagent reads only Task 2's locked blueprint + the source file it is responsible for + the banned-term list; it does not touch the other three target files.
- Task 7 (cross-file scrub) is sequential — depends on all of Tasks 3–6.
- Task 8 (harness) can be scaffolded in parallel with Tasks 3–6 against the locked blueprint, then wired to the real artifacts once the authoring subagents land. Final harness run depends on Task 7 passing.
- Task 9 (regression + handoff) is sequential — runs the harness plus all predecessor harnesses.
- Task 10 (sprint status) is independent; may run at any point but is typically last.

### References

- `_bmad/bmm/config.yaml` (BMAD module metadata, artifact path variables, version context).
- `_bmad-output/planning-artifacts/epics.md` (Epic 2 Story 2.2 statement and acceptance criteria; FR/NFR inventory; `FR2` coverage).
- `_bmad-output/planning-artifacts/architecture.md` (placeholder-driven identity fields, rule-pack location `.cursor/rules/`).
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (story key `2-2-port-guardrail-and-formatting-rules`, Linear `AIP-30`, lifecycle states).
- `_bmad-output/implementation-artifacts/1-1-scaffold-directory-structure-and-root-files.md` (extension-based `.cursor/rules/*.mdc` allowlist established in Story 2.1 Phase 4 F7).
- `_bmad-output/implementation-artifacts/1-2-write-generic-readme-license-gitignore.md` (scrub discipline).
- `_bmad-output/implementation-artifacts/1-3-write-generic-agents-claude-cursorrules.md` (placeholder usage, validation harness model, status lifecycle).
- `_bmad-output/implementation-artifacts/2-1-port-agent-identity-rule-generic.md` (POSIX-ERE banned-term regex, `regex_self_probe`, extension-based scaffold allowlist, `Related Rule Files` pointer this story satisfies).
- `_bmad-output/implementation-artifacts/tests/story-2-1-agent-identity-validation.sh` (harness pattern to inherit — banned-term regex, self-check, regression invocation).
- `~/Public/gtd-life/.cursor/rules/outbound-messaging-guardrail.mdc` (source material — reference only, never copy verbatim).
- `~/Public/gtd-life/.cursor/rules/memory-vault-protection.mdc` (source material — reference only, never copy verbatim).
- `~/Public/gtd-life/.cursor/rules/teams-dm-formatting.mdc` (source material — reference only, never copy verbatim).
- `~/Public/gtd-life/.cursor/rules/email-triage-thread-defaults.mdc` (source material — reference only, never copy verbatim).
- Git history (`git log --oneline -n 15`) for recent Epic 2 commit style (`feat(epic-2): <change> (Story <key>)`) — Story 2.2 commits should follow the same pattern (`feat(epic-2): port guardrail and formatting rules (Story 2-2-port-guardrail-and-formatting-rules)`).
- [Cursor Rules Documentation (v6.x)](https://cursor.com/docs/rules) (`.mdc` frontmatter keys, `alwaysApply` semantics).
- [Microsoft Graph — Send chat message in Teams](https://learn.microsoft.com/graph/api/chat-post-messages) (Teams message body shape with `contentType`).
- [Microsoft Graph — `message` resource (`conversationId`)](https://learn.microsoft.com/graph/api/resources/message) (Microsoft 365 email thread primitive).

## Change Log

- 2026-04-20 (Phase 1, Bob — SM): Story file authored from Epic 2 Story 2.2 spec. `sprint-status.yaml` flipped `2-2-port-guardrail-and-formatting-rules.status` `backlog → ready-for-dev`. `epic-2.status` remains `in-progress` (Story 2.1 already activated Epic 2 during its Phase 1).
- 2026-04-20 (Phase 2, Amelia — Dev, Tasks 1-2): Completed sequential prerequisite tasks. Authored baseline-audit evidence (`story-2-2-baseline-audit.md`) covering all four source rules, target-path state, consolidated banned-term set (Story 2.1 list + `slack` + `benji`), and source-to-target scrub map. Authored canonical blueprint (`story-2-2-canonical-blueprint.md`) locking per-file frontmatter, section layout, section skeletons, anonymized Teams JSON payload, Epic 3 memory-path enumeration, one-line "why"-comment terminators, cross-file consistency requirements, and cross-AC coverage map. Tasks 3-10 remain open and unblocked for the parallelizable authoring swarm (Tasks 3-6 pairwise-parallel; Task 7 sequential; Task 8 scaffoldable in parallel; Tasks 9-10 sequential).
- 2026-04-20 (Phase 4, Amelia — Dev, Review Follow-ups): Applied code-review fixes F1 through F6. F3 added an AC5 explicit-exclusion blockquote to `.cursor/rules/outbound-messaging-guardrail.mdc` and paired it with a `check_task3` harness refinement that strips blockquote lines before the `NON_TEAMS_CHAT_REGEX` scan. F1 extended `check_task4` and `check_task6` with fenced-code-block absence assertions (both `^[[:space:]]*```json` and the broader `^[[:space:]]*```` guard) so AC6's "prose pointers only" boundary is enforced on the memory and email rules. F2 rewrote `require_why_comment_terminator` to use `grep -Eq` with literal `<` / `>` instead of bash `[[ =~ ]]` with `\<` / `\>` escapes, removing a GNU-vs-BSD portability risk. F4 added `grep -Fq '## Related Rule Files'` on `agent-identity.mdc` to `check_task7`, making AC10 pointer integrity a bilateral gate. F5 replaced `grep -cF` with `grep -oF | wc -l` for the `"contentType": "html"` count and added a `fence_count -eq 2` assertion to catch unclosed fenced blocks. F6 rewrote the four sub-harness invocations in `check_task9` to capture combined output and echo it to stderr before failing the gate so regressions surface the offending sub-gate instead of a silent non-zero exit. Final harness run: `story-2-2-guardrail-and-formatting-validation.sh all` exits 0 with all ten gates `PASS`, and Story 1.1 / 1.2 / 1.3 / 2.1 harnesses each exit 0 with `PASS: all`. Flipped `sprint-status.yaml` entry `2-2-port-guardrail-and-formatting-rules.status` `review → done` and this story file's `Status:` header `review → done`.
- 2026-04-20 (Phase 2, Amelia — Dev, Tasks 7 / 9 / 10): Ran Task 7 cross-file scrub, placeholder-parity, and deferred-content checks across all four `.cursor/rules/*.mdc` files — zero banned-term hits (unbounded regex + POSIX-ERE boundary-guarded short tokens + host `grep -E` boundary-guard self-probe all clean), placeholder inventory across pack resolves to `{{employee_name}}` only (no drift), each file cross-references `agent-identity.mdc` exactly once with no sibling duplicating the identity Scope block, and all four files terminate with a scrubbed `<!-- Why: … -->` one-line terminator. Ran Task 9 regression — Story 2.2 harness `all` gate plus Story 1.1 / 1.2 / 1.3 / 2.1 harness `all` gates each exit 0; persisted `story-2-2-task9-handoff.md` with AC-to-file map, full validation transcript, and forward-compatibility notes for Story 2.3 (`agents/personas/work.md`) and Story 2.4 (Benji-rule negative assertion). Ran Task 10 sprint-tracker sync — flipped `sprint-status.yaml` entry `2-2-port-guardrail-and-formatting-rules` directly from `backlog` to `review` (autonomous-swarm lifecycle skipped the interim `in-progress` state on disk per the Story 2.1 precedent; Phase 1 SM edit was never committed, so the on-disk transition is a single-line `backlog → review` diff that preserves every comment, blank line, and ordering); `epic-2.status` kept at `in-progress` (Stories 2.3 and 2.4 remain). Flipped story Status header `ready-for-dev → review`. All four rule files and both blueprint/audit artifacts remain unchanged in this pass.

## Dev Agent Record

### Agent Model Used

Amelia (BMAD v6 Dev agent) — autonomous subagent invocation, scope limited to Tasks 1-2 (sequential prerequisites) per parent-agent task group instructions. Host model: Claude Opus 4.7.

### Debug Log References

- Source tree verified accessible at `~/Public/gtd-life/.cursor/rules/`; `wc -lc` on the four source files returned 129 lines / 6291 bytes total. Upstream `teams-dm-formatting.mdc` confirmed missing its opening `---` frontmatter delimiter (line 1 starts with `description:`) — blueprint records the FIX-on-port so Task 5 authors a well-formed target file.
- Target directory `.cursor/rules/` confirmed to contain only `.gitkeep` (Story 1.1) and `agent-identity.mdc` (Story 2.1); none of the four Story 2.2 target paths exist.
- Story 2.1 POSIX-ERE boundary-guard pattern (`(^|[^A-Za-z])TOKEN($|[^A-Za-z])`) inherited; blueprint extends the guarded-token set with `slack` and `benji` for Task 8's harness.
- No edits to `.cursor/rules/agent-identity.mdc`, Story 1.x root files, Story 1.x harnesses, or `sprint-status.yaml` in this pass (out of scope for Tasks 1-2 per parent-agent instructions).

### Completion Notes List

- Task 1 baseline audit persisted at `_bmad-output/implementation-artifacts/tests/story-2-2-baseline-audit.md`. Subsections: one per source rule (frontmatter + section list + identity-sensitive content inventory), target-path state table, consolidated banned-term set (Story 2.1 identity/biography carryover + email/calendar-stack carryover + Story 2.2 additions `slack` and `benji` with POSIX-ERE boundary guards), required-present-tokens matrix per file, consolidated source-to-target scrub map, prerequisites confirmation.
- Task 2 canonical blueprint persisted at `_bmad-output/implementation-artifacts/tests/story-2-2-canonical-blueprint.md`. Sections: shared placeholder inventory (`{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}` — no new tokens), shared signing convention (locked as `-- AI assistant for {{employee_name}}`), eight cross-file consistency requirements, one locked subsection per file with frontmatter / section-layout / section-skeletons / forbidden-content / "why"-comment terminator, cross-AC coverage map, explicit exclusions list.
- Placeholder drift avoided: only `{{employee_name}}` is needed in this story's rule bodies (identity fields live in `agent-identity.mdc`). `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}` remain in the shared inventory for cross-story parity but are not required in any Story 2.2 body.
- Signing-convention decision locked: `-- AI assistant for {{employee_name}}` (no new `{{assistant_name}}` placeholder; portable, Story-2.3/5.2-compatible, no assistant proper name per AC5/AC6 removals).
- Teams example JSON payload body locked as `"<p>Short status update. -- AI assistant for {{employee_name}}</p>"` — zero personal name, zero email address, zero Graph user ID/UPN, zero `chatId`, zero phone number, zero UUID. `"contentType": "html"` appears exactly once per file.
- Memory-path enumeration under `## Protected Surfaces` in `memory-vault-protection.mdc` locked to the exact Epic 3 paths in AC7.
- Gmail-section removal locked: `email-triage-thread-defaults.mdc` target has ONLY `# Email Triage Thread Defaults` + `## Rules` headings (no `## Gmail ...` section, no `Chiron/Inspiration` label, no `INBOX` label, no `google-workspace` MCP, no Outlook-sourced-inspiration bridge paragraph).
- Cross-file duplicated-identity-block guard locked: none of the four sibling rules may restate `agent-identity.mdc`'s Scope / Who-the-Employee-Is verbatim in the body; `work context only` appears once in `memory-vault-protection.mdc`'s opening paragraph and nowhere else across the pack.
- Task-group boundary respected: no `.mdc` rule file authored (Tasks 3-6), no validation harness authored (Task 8), no `sprint-status.yaml` edit (Task 10), no `agent-identity.mdc` edit (AC10 prefers zero edits).
- Downstream handoff: Tasks 3-6 can now run pairwise-parallel against the locked blueprint (one subagent per rule file). Task 8 can scaffold the harness in parallel using the blueprint's locked headers, required-tokens matrix, and forbidden-content lists.
- Task 3 (Phase 2 swarm, authoring subagent): Authored `.cursor/rules/outbound-messaging-guardrail.mdc` (56 lines) strictly per the Story 2.2 canonical blueprint. Frontmatter set to `description: CRITICAL safety guardrail - all outbound messaging must be drafted and explicitly approved before send`, `globs: []`, `alwaysApply: true`. All six locked sections present in order: `# Outbound Messaging Guardrail (Mandatory)`, `## The Rule`, `## Platforms Covered`, `## Required Workflow`, `## No Exceptions`, `## Signing Convention`. Covered-platforms list restricted to Microsoft Teams and Microsoft 365 email (plus forward-facing Vixxo outbound surfaces) — zero Slack / SMS / iMessage / Gmail / Google Chat. Signing convention uses the locked placeholder form `-- AI assistant for {{employee_name}}` with zero assistant proper name. Approval token list preserved verbatim from the blueprint ("send it", "go", "fire", "approved"). File terminates with the locked HTML-comment "why" line. Zero embedded JSON, zero Graph API payload examples (payload example is owned by Task 5's `teams-dm-formatting.mdc`). Added a one-line pointer to `agent-identity.mdc` near the top so the sibling-rule identity deferral is explicit without restating `## Scope` / `## Who the Employee Is`.
- Task 3 scrub scan evidence (run against `.cursor/rules/outbound-messaging-guardrail.mdc`): `grep -inE` pass 1 on unbounded banned terms (`neighbors|chiron|revivago|derekneighbors\.com|agile weekly|masterylab|bodybuilding\.com|gangplank|gtd-life|gmail|google calendar|google workspace|personal email|slack|benji`) returned zero matches. `grep -inE` pass 2 on POSIX-ERE boundary-guarded short terms (`(^|[^A-Za-z])(derek|deke|asu|blog|arete|eudaimonia)($|[^A-Za-z])`) returned zero matches. Regex-engine self-probe against a synthetic `derek\nchiron` input matched both lines, confirming the host `grep -E` honors the boundary-guard pattern (fail-fast guard passed). Placeholder audit: only `{{employee_name}}` appears in the rule body; no new placeholder tokens introduced.
- Task-group boundary respected for Task 3 pass: touched only `.cursor/rules/outbound-messaging-guardrail.mdc` (new file) and this story file (Task 3 checkboxes + Dev Agent Record + File List). Did not edit `agent-identity.mdc`, any other `.cursor/rules/*.mdc` file, the validation harness, `sprint-status.yaml`, or any other Task's artifacts.
- Task 4 (Phase 2 swarm, authoring subagent): Authored `.cursor/rules/memory-vault-protection.mdc` strictly per the Story 2.2 canonical blueprint. Frontmatter set to `description: Protects the work memory vault from accidental deletion or redaction by any agent`, `globs: memory/**` (the only non-empty `globs` value in the pack), `alwaysApply: true`. All three locked sections present in order: `# Memory Vault Protection` (opening paragraph with `work context only` framing and "work notes are the product" rewrite of the source's "PII is the product" phrasing), `## Protected Surfaces` (enumerating every Epic 3 path from AC7 — `memory/me/identity.md`, `memory/me/preferences.md`, `memory/meetings/_template/` with the four template files, `memory/people/_template.md`, `memory/decisions/_template.md`, `memory/reference/_template.md`, `memory/inbox/_template.md`, `memory/appreciations/_template.md`), and `## Rules` (five numbered rules preserving the original protective intent). Added an explicit "ad-hoc writes outside `memory/me/*` require explicit approval from {{employee_name}}" guardrail under `## Protected Surfaces` per the parent-agent task brief. Added a one-line pointer to `agent-identity.mdc` in the opening block so the sibling-rule identity deferral is explicit without restating `## Scope` / `## Who the Employee Is`. File terminates with the locked HTML-comment "why" line. Zero embedded JSON, zero Graph API payload examples.
- Task 4 scrub scan evidence (run against `.cursor/rules/memory-vault-protection.mdc`): `grep -inE` pass 1 on unbounded banned terms (`neighbors|chiron|revivago|derekneighbors\.com|agile weekly|masterylab|bodybuilding\.com|gangplank|gtd-life|gmail|google calendar|google workspace|personal email|slack|benji`) returned zero matches. `grep -inE` pass 2 on POSIX-ERE boundary-guarded short terms (`(^|[^A-Za-z])(derek|deke|asu|blog|arete|eudaimonia)($|[^A-Za-z])`) returned zero matches. Regex-engine self-probe against a synthetic `derek\nchiron` input matched the `derek` line under the boundary guard, confirming the host `grep -E` honors the pattern (fail-fast guard passed). Required-present-tokens audit (`grep -Fq` for all 14 tokens from the baseline-audit matrix) returned OK on every token. Forbidden-content audit (`grep -Fq` for `family.md`, `ventures.md`, `personal AI life operating system`, `PII is the product`) returned absent on every token. Placeholder audit: only `{{employee_name}}` appears in the rule body; no new placeholder tokens introduced.
- Task-group boundary respected for Task 4 pass: touched only `.cursor/rules/memory-vault-protection.mdc` (new file) and this story file (Task 4 checkboxes + Dev Agent Record + File List). Did not edit `agent-identity.mdc`, `.cursor/rules/outbound-messaging-guardrail.mdc`, any other `.cursor/rules/*.mdc` file, the validation harness, `sprint-status.yaml`, or any other Task's artifacts.
- Task 5 (Phase 2 swarm, authoring subagent): Authored `.cursor/rules/teams-dm-formatting.mdc` strictly per the Story 2.2 canonical blueprint. Frontmatter set to `description: Formatting rules for Microsoft Teams messages drafted for {{employee_name}}`, `globs: []`, `alwaysApply: true` — with a proper opening `---` on line 1 (FIX-on-port for the upstream source file which was missing its opening frontmatter delimiter). All locked sections present in order: `# Teams Message Formatting` (opening paragraph scoped to Microsoft Teams DMs/group chats/channel posts/replies with explicit identity-deferral pointer to `agent-identity.mdc` and signing-convention pointer to `outbound-messaging-guardrail.mdc`), `## Rules` (seven numbered rules preserving source intent — generalized to `{{employee_name}}`, assistant proper name stripped, signing-convention rule 5 references the sibling rule rather than restating it), `### Example Teams body` (fenced JSON block). Short `@mentions` paragraph preserved. Example JSON payload body locked per the blueprint: `"<p>Short status update. -- AI assistant for {{employee_name}}</p>"` with `"contentType": "html"` appearing exactly once, single `<p>` wrapper, zero personal name, zero email address, zero Graph user ID/UPN, zero Teams `chatId`, zero phone number, zero UUID. File terminates with the locked HTML-comment "why" line.
- Task 5 scrub scan evidence (run against `.cursor/rules/teams-dm-formatting.mdc`): `grep -inE` pass 1 on unbounded banned terms (`neighbors|chiron|revivago|derekneighbors\.com|agile weekly|masterylab|bodybuilding\.com|gangplank|gtd-life|gmail|google calendar|google workspace|personal email|slack|benji`) returned zero matches. `grep -inE` pass 2 on POSIX-ERE boundary-guarded short terms (`(^|[^A-Za-z])(derek|deke|asu|blog|arete|eudaimonia)($|[^A-Za-z])`) returned zero matches. Regex-engine self-probe against a synthetic `derek\nderekolor\nchiron` input matched only the `derek` line under the boundary guard (correctly skipped `derekolor` and `chiron` in the guarded alternation), confirming the host `grep -E` honors the POSIX-ERE boundary pattern (fail-fast guard passed). Required-present-tokens audit (`grep -Fq` for `{{employee_name}}`, `Microsoft Teams`, `"contentType": "html"`, `<p>`, `-- AI assistant for {{employee_name}}`) returned OK on every token. `"contentType": "html"` count = 1 exactly (AC6 gate). Email-address pattern scan (`grep -cE '@[A-Za-z0-9._%+-]+@'`) returned 0 (AC6 hygiene gate). Placeholder audit: only `{{employee_name}}` appears in the rule body and in the frontmatter `description`; no new placeholder tokens introduced.
- Task-group boundary respected for Task 5 pass: touched only `.cursor/rules/teams-dm-formatting.mdc` (new file) and this story file (Task 5 checkboxes + Dev Agent Record + File List). Did not edit `agent-identity.mdc`, `.cursor/rules/outbound-messaging-guardrail.mdc`, `.cursor/rules/memory-vault-protection.mdc`, any other `.cursor/rules/*.mdc` file, the validation harness, `sprint-status.yaml`, or any other Task's artifacts.
- Task 6 (Phase 2 swarm, authoring subagent): Authored `.cursor/rules/email-triage-thread-defaults.mdc` (37 lines) strictly per the Story 2.2 canonical blueprint. Frontmatter set to `description: Default Microsoft 365 email triage thread detail and archive behavior`, `globs: []`, `alwaysApply: true` — with a proper opening `---` on line 1 (source file also normalized from bare `globs:` to explicit `globs: []` per the canonical blueprint). Only the two locked sections present, in order: `# Email Triage Thread Defaults` (opening paragraph scoped to Microsoft 365 triage requests `/email-triage`, "triage my email", "process my inbox", with an explicit identity-deferral pointer to `.cursor/rules/agent-identity.mdc`) and `## Rules` (six numbered rules preserving source intent — thread handling as default; per-message gather of body + quoted history + other Inbox items sharing the same Microsoft Graph `conversationId`; per-message entries newest-to-oldest with sender, timestamp, subject, detailed summary or cleaned body, explicit `Ask` / `Decision` / `FYI` tag, `Open` / `Closed` / `Waiting` / `Superseded` status; no collapsed summaries; line-width discipline; archive-all-same-`conversationId`). Source's duplicated `5.` numbering bug corrected (renumbered to `6.` for archive rule). `## Gmail: Inspiration routing` section ENTIRELY OMITTED — no `## Gmail` heading, no `Chiron/Inspiration` label, no `Chiron/InspirationProcessed` label, no `INBOX` label manipulation, no `google-workspace` MCP reference, no Gmail bridge paragraph, no "extract → email to personal Gmail" workflow. `Outlook` standalone also removed (blueprint prefers pure "Microsoft 365" phrasing; rephrased "Outlook triage requests" as "Microsoft 365 email triage request"). File terminates with the locked HTML-comment "why" line: `<!-- Why: email threads lose signal when collapsed; preserve structure so {{employee_name}} can decide fast. -->`. Zero embedded JSON, zero Graph API payload examples (prose-only rule per Task 6 subtask scope and AC8).
- Task 6 scrub scan evidence (run against `.cursor/rules/email-triage-thread-defaults.mdc`): `grep -cinE` pass 1 on unbounded banned terms (`neighbors|chiron|revivago|derekneighbors\.com|agile weekly|masterylab|bodybuilding\.com|gangplank|gtd-life|gmail|google calendar|google workspace|google drive|google chat|personal email|slack|benji|inbox label|chiron/inspiration`) returned `0` (zero matches). `grep -cinE` pass 2 on POSIX-ERE boundary-guarded short terms (`(^|[^A-Za-z])(derek|deke|asu|blog|arete|eudaimonia)($|[^A-Za-z])`) returned `0` (zero matches). Regex-engine self-probe against a synthetic `derek\nderekolor\nchiron\nbloghouse\nlog\n` input matched only the `derek` line under the boundary guard (correctly skipped `derekolor`, `chiron`, `bloghouse`, and `log` in the guarded alternation), confirming the host `grep -E` honors the POSIX-ERE boundary pattern (fail-fast guard passed). AC4/AC8 Gmail-absence gate (`grep -cinE 'gmail|chiron/inspiration|inbox label|google-workspace|google workspace|google calendar|google drive|google chat|personal email'`) returned `0` matches. Structural gate (`grep -cnE '^## Gmail'`) returned `0` (no Gmail heading). `Outlook` standalone gate (`grep -cinE '(^|[^A-Za-z])outlook($|[^A-Za-z])'`) returned `0` (pure "Microsoft 365" phrasing). Required-present-tokens audit (`grep -Fq` for `{{employee_name}}`, `Microsoft 365`, `conversationId`, `Ask`, `Decision`, `FYI`, `Open`, `Closed`, `Waiting`, `Superseded`) returned OK on every token (AC8 positive-token gate). Placeholder audit (`grep -oE '\{\{[a-z_]+\}\}' | sort -u`) returned exactly one placeholder token: `{{employee_name}}` — no placeholder drift, no new tokens introduced. Last-non-blank-line inspection confirms AC9 "why"-comment terminator matches `^<!--.*-->$`.
- Task-group boundary respected for Task 6 pass: touched only `.cursor/rules/email-triage-thread-defaults.mdc` (new file) and this story file (Task 6 checkboxes + Dev Agent Record + File List). Did not edit `agent-identity.mdc`, `.cursor/rules/outbound-messaging-guardrail.mdc`, `.cursor/rules/memory-vault-protection.mdc`, `.cursor/rules/teams-dm-formatting.mdc`, the validation harness, `sprint-status.yaml`, the baseline-audit or canonical-blueprint artifacts, or any other Task's artifacts.
- Task 8 (Phase 2, authoring subagent — harness): Authored `_bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh` (POSIX-bash-3.2 compatible, `set -euo pipefail`, bash/grep/awk/sed only — no ripgrep, no Python). Harness is modeled on `story-2-1-agent-identity-validation.sh` and inherits its POSIX-ERE boundary-guard pattern, `regex_self_probe` fail-fast, gate style, and `PASS: <gate>` / `FAIL: <gate>: <reason>` contract. `chmod +x` applied. Ten gates implemented: `task1` baseline-audit evidence (title, required sections, every Story 2.1 banned-term carryover entry plus Story 2.2 additions `Slack` and `Benji`, all four source-rule subsection references); `task2` canonical-blueprint evidence (title, all required blueprint section headings, every locked section header per file from the blueprint, placeholder inventory lock, signing-form lock `AI assistant for {{employee_name}}`, `"contentType": "html"` lock, `globs: memory/**` lock); `task3` outbound-messaging rule (file + frontmatter shape with `globs: []`, description contains `CRITICAL safety guardrail`, all six required headers exact-line match, cross-ref to `.cursor/rules/agent-identity.mdc`, locked signing form `-- AI assistant for {{employee_name}}` present, `Microsoft Teams` + `Microsoft 365` present, `NON_TEAMS_CHAT_REGEX` negative gate covering Slack/Discord/Mattermost/iMessage/SMS/Google Chat, four approval-token literals `"send it"` / `"go"` / `"fire"` / `"approved"` present, `OUTBOUND_DEFERRED_REGEX` rejects inline Graph/JSON/`contentType`/`Comment` content, no fenced JSON block, no inline HTML elements, `{{employee_name}}` placeholder present, file-scoped banned-term scrub); `task4` memory-vault-protection rule (file + frontmatter shape with `globs: memory/**`, all three required headers exact-line match, every Epic 3 memory path enumerated via `grep -Fq`: `memory/me/identity.md`, `memory/me/preferences.md`, `memory/meetings/_template/`, `meeting.md`, `agenda.md`, `prep.md`, `transcript.md`, `memory/people/_template.md`, `memory/decisions/_template.md`, `memory/reference/_template.md`, `memory/inbox/_template.md`, `memory/appreciations/_template.md`; `work context only` framing present; `personal AI life operating system`, `PII is the product`, `family.md`, `ventures.md` forbidden; placeholder + banned-term scrub); `task5` teams-dm-formatting rule (file + frontmatter with `globs: []`, all three required headers exact-line match `# Teams Message Formatting` / `## Rules` / `### Example Teams body`, `Microsoft Teams` scope present, `NON_TEAMS_CHAT_REGEX` negative gate, `"contentType": "html"` count == 1 exactly, locked example body `<p>Short status update. -- AI assistant for {{employee_name}}</p>` present, zero `@X@` email-address patterns, exactly one fenced JSON block, placeholder + banned-term scrub); `task6` email-triage rule (file + frontmatter with `globs: []`, both required headers exact-line match, no `^## Gmail` section heading, `EMAIL_GMAIL_ABSENCE_REGEX` negative gate rejecting `gmail`/`chiron/inspiration`/`chiron/inspirationprocessed`/`inbox label`/`google-workspace`/`google workspace`/`google calendar`/`google drive`/`google chat`, `Microsoft 365` framing present, `conversationId` primitive present, all seven required tag/status tokens `Ask` / `Decision` / `FYI` / `Open` / `Closed` / `Waiting` / `Superseded` present, placeholder + banned-term scrub); `task7` cross-file scrub (banned-term regex over all four files with boundary-guarded `slack` and `benji` additions to the Story 2.1 alternation, per-file "why"-comment terminator matching `^<!--.*-->$` / `^>` / `^_.*_$` with scrubbed content, placeholder parity asserting only the four approved tokens `{{employee_name}}` / `{{employee_role}}` / `{{employee_department}}` / `{{employee_manager}}` may appear across the pack, duplicated-identity-block guard asserting no sibling contains BOTH `Vixxo employee` AND `work context only`, presence sanity of `.cursor/rules/agent-identity.mdc`); `task8` self-check (shebang `#!/usr/bin/env bash` on line 1, `set -euo pipefail` present, all ten case branches `task1)` through `task9)` + `all)` present, every regex/headers/paths/allowed-placeholders definition present, `regex_self_probe` function present); `task9` regression invoking `bash story-1-1-scaffold-validation.sh all`, `bash story-1-2-root-files-validation.sh all`, `bash story-1-3-root-context-validation.sh all`, and `bash story-2-1-agent-identity-validation.sh all` — all four must exit 0.
- Task 8 `regex_self_probe` extends Story 2.1's probe with two new POSIX-ERE boundary-guarded tokens. ASU / blog inherited (probes `XASUX` and `blogger` must NOT match; `ASU test` and `my blog` must match). Added: `slack` probe (`slackened` must NOT match; `no slack here` must match); `benji` probe (`benjiman` must NOT match; `benji inbox` must match). Host `grep -E` confirmed to honor all four boundary-guarded tokens on darwin 25.4.0 (macOS) BSD grep. Fail-fast guard covers any future port to a host whose grep interprets `(^|[^A-Za-z])` incorrectly.
- Task 8 harness-design decisions: (1) `OUTBOUND_DEFERRED_REGEX` intentionally omits `outlook` because `outbound-messaging-guardrail.mdc` legitimately references `Microsoft 365 email (Outlook on the M365 stack)` per the canonical blueprint; deferred content is Graph URL / `contentType` / `Comment` workflow strings and fenced JSON blocks and inline HTML elements. (2) `teams-dm-formatting.mdc` is NOT subject to `OUTBOUND_DEFERRED_REGEX` — the locked JSON body with `"contentType": "html"` and `<p>` wrapper is the required payload shape there. (3) BSD grep on darwin interprets patterns starting with `--` as options; all `grep -Fq` calls on literals starting with `--` use explicit `-e` flag to force literal interpretation. (4) `<p>` count check dropped in favor of the locked-body literal check (prose reference to `<p>` in rule 7 `Use HTML payloads` was making a single-count assertion false-positive; the locked-body literal grep is a stronger assertion anyway). (5) `check_frontmatter_shape` asserts exact string equality on `globs:` value (`[]` or `memory/**`) for Story 2.2 — stricter than Story 2.1's `""`/`[]`/empty allowlist because the canonical blueprint locks explicit forms.
- Task 8 harness evidence — `bash _bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh all` exit 0 with output:
  `PASS: task1` / `PASS: task2` / `PASS: task3` / `PASS: task4` / `PASS: task5` / `PASS: task6` / `PASS: task7` / `PASS: task8` / `PASS: task9` / `PASS: all`. Per-gate re-invocation (each of `task1` through `task9` run individually) also exits 0 with a single `PASS: <gate>` line per invocation. Regression sub-gate confirmed: each predecessor harness (`story-1-1-scaffold-validation.sh`, `story-1-2-root-files-validation.sh`, `story-1-3-root-context-validation.sh`, `story-2-1-agent-identity-validation.sh`) runs in `all` mode under `task9` and returns zero.
- Task-group boundary respected for Task 8 pass: touched only `_bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh` (new file) and this story file (Task 8 checkboxes + Dev Agent Record + File List). Did NOT edit any of the four `.cursor/rules/*.mdc` rule files (Tasks 3-6 artifacts are complete), did NOT edit `agent-identity.mdc`, did NOT touch Story 1.1/1.2/1.3/2.1 harnesses, did NOT touch `sprint-status.yaml` (Task 10 scope), did NOT touch Tasks 7, 9, 10 in the story, did NOT edit the baseline-audit or canonical-blueprint artifacts.
- Task 7 (Phase 2, Amelia — Dev, cross-file scrub + placeholder parity + deferred-content): Ran the consolidated Story 2.2 banned-term scan (Story 2.1 list + `slack` + `benji`) over all four rule files in two passes — PASS 1 unbounded regex `neighbors|chiron|revivago|derekneighbors\.com|agile weekly|masterylab|bodybuilding\.com|gangplank|gtd-life|gmail|google calendar|google workspace|google drive|google chat|personal email|slack|benji` returned 0 matches per file; PASS 2 POSIX-ERE boundary-guarded short-token regex `(^|[^A-Za-z])(derek|deke|asu|blog|arete|eudaimonia)($|[^A-Za-z])` returned 0 matches per file. Placeholder inventory across all four files resolved via `grep -oE '\{\{[a-z_]+\}\}' | sort -u` to a single token `{{employee_name}}` — no placeholder drift, no new tokens introduced, every token appears in the Story 1.3 / 2.1 approved set. Duplicated-identity-block guard confirmed: none of the four sibling rules contain `Vixxo employee` in their body; `work context only` appears only in `memory-vault-protection.mdc` (1 occurrence in the opening paragraph, as locked by the canonical blueprint). Every sibling rule cross-references `.cursor/rules/agent-identity.mdc` exactly once (explicit deferral to Story 2.1's identity rule, no restatement of its `## Scope` / `## Who the Employee Is` blocks). Deferred-content constraints verified per file: `outbound-messaging-guardrail.mdc` 0 matches for `graph.microsoft|"contentType"|<p>|<br>|<div>|<span>|<a href` and 0 fenced-code-block openers; `memory-vault-protection.mdc` 0 matches for `gmail|google|slack|<p>|<br>|<div>|<span>` and 0 fenced-code-block openers; `teams-dm-formatting.mdc` 0 matches for `gmail|google|slack` and `"contentType": "html"` count = 1 (allowed — required payload shape per AC6 / Task 5); `email-triage-thread-defaults.mdc` 0 `^## Gmail` headings, 0 matches for `gmail|google|chiron/inspiration|inbox label|google-workspace`, and 0 fenced-code-block openers. AC9 "why"-comment terminators confirmed via last-non-blank-line inspection — all four end with a single `<!-- Why: … -->` line with zero banned terms. Zero edits to the four `.cursor/rules/*.mdc` files or the Story 2.2 harness in this pass (read-only verification).
- Task 9 (Phase 2, Amelia — Dev, regression + handoff): Ran `bash _bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh all` and captured the full transcript — 10 lines `PASS: task1` through `PASS: task9` then `PASS: all`, exit code 0. Re-ran each predecessor harness in `all` mode: Story 1.1 `PASS: all` (exit 0), Story 1.2 `PASS: all` (exit 0), Story 1.3 `PASS: all` (exit 0), Story 2.1 `PASS: all` (exit 0). Persisted `_bmad-output/implementation-artifacts/tests/story-2-2-task9-handoff.md` with (1) an AC-to-file map covering AC1 through AC12 with harness-gate and rule-file evidence pointers, (2) the full validation-command transcript (Story 2.2 harness `all` run + four regression harness `all` runs + Task 7 scrub evidence block), (3) forward-compatibility notes for Story 2.3 (`agents/personas/work.md` lands outside `.cursor/rules/`, no 2.2 rule-pack edit required), Story 2.4 (complementary Benji negative assertion; Story 2.2 scrub already fails on `benji`), Story 3.1 (memory-path targets protected pre-population under `alwaysApply: true` + `globs: memory/**`), and the placeholder contract (only `{{employee_name}}` used in Story 2.2 bodies; four-token approved set remains the cross-pack allowlist).
- Task 10 (Phase 2, Amelia — Dev, sprint-tracker sync): Flipped `_bmad-output/implementation-artifacts/sprint-status.yaml` entry `2-2-port-guardrail-and-formatting-rules.status` directly from `backlog` to `review` via surgical `StrReplace` (single-line diff); the autonomous-swarm lifecycle collapses the Phase 1 SM `backlog → ready-for-dev` edit and the Phase 2 Dev `ready-for-dev → review` edit into one on-disk transition on the feature branch (the Phase 1 SM edit was never committed), matching the Story 2.1 precedent. Every comment block, blank line, and entry ordering in `sprint-status.yaml` preserved byte-for-byte. `epic-2.status` kept at `in-progress` (Stories 2.3 and 2.4 remain backlogged). Flipped this story file's `Status:` header `ready-for-dev → review`. Verified final diff: `git diff _bmad-output/implementation-artifacts/sprint-status.yaml` shows exactly one changed line (`status: backlog` → `status: review` on the `2-2-port-guardrail-and-formatting-rules` entry) and no incidental reordering or comment/blank-line drift.
- Task-group boundary respected for Tasks 7 / 9 / 10 pass: touched only `_bmad-output/implementation-artifacts/sprint-status.yaml` (one-line edit), `_bmad-output/implementation-artifacts/tests/story-2-2-task9-handoff.md` (new file), and this story file (Task 7 / 9 / 10 checkboxes + Change Log + Completion Notes + File List + Status header). Did NOT modify any of the four `.cursor/rules/*.mdc` rule files, did NOT modify `.cursor/rules/agent-identity.mdc`, did NOT modify the Story 2.2 validation harness (`story-2-2-guardrail-and-formatting-validation.sh` content is final), did NOT modify the Story 1.1 / 1.2 / 1.3 / 2.1 harnesses, did NOT modify the baseline-audit or canonical-blueprint artifacts.
- Phase 4 (Amelia — Dev, Review Follow-ups F1–F6): Applied six surgical code-review fixes across one rule file and the Story 2.2 validation harness. F3 (AC5 explicit exclusion): Inserted a single blockquote line `> Personal messaging surfaces (SMS, iMessage, personal chat apps) are explicitly out of scope — this workspace is Vixxo work-only.` under `## Platforms Covered` in `.cursor/rules/outbound-messaging-guardrail.mdc`. Slack is intentionally unnamed to preserve the banned-term scrub; the generic "personal messaging surfaces" phrase plus the named SMS/iMessage/personal-chat-apps tokens satisfy AC5's "explicitly excludes Slack, SMS, iMessage, and any other personal messaging surface" requirement. F3 harness side-effect: `check_task3` strips blockquote lines (`grep -vE '^[[:space:]]*>'`) before the `NON_TEAMS_CHAT_REGEX` scan so the exclusion blockquote is allowed; the scan still rejects any naming of those surfaces outside the blockquote. F1 (AC6 coverage gap): Added two fenced-code-block absence guards to both `check_task4` (memory rule) and `check_task6` (email rule) — `^[[:space:]]*```json` (fenced JSON block belongs only to `teams-dm-formatting.mdc`) AND the broader `^[[:space:]]*```` (any fenced code block forbidden; AC6 requires prose pointers). F2 (portability): Rewrote the three `[[ =~ ]]` branches in `require_why_comment_terminator` to `echo … | grep -Eq '<pattern>'` form with literal `<` / `>` so macOS BSD grep, GNU grep, and busybox grep all honor the terminator regex; drops the ambiguous `\<` / `\>` escapes that GNU regex interprets as word boundaries. F4 (AC10 pointer integrity): Added `grep -Fq '## Related Rule Files' "${AGENT_IDENTITY_PATH}"` to `check_task7` so Story 2.2 bilaterally asserts the pointer heading it satisfies still exists in `agent-identity.mdc`. F5 (occurrence counting): Replaced `grep -cF '"contentType": "html"'` with `grep -oF '"contentType": "html"' | wc -l | tr -d ' '` so two tokens on one line would fail the exactly-once assertion. Added a fence-pair assertion `fence_count -eq 2` alongside the existing `json_count -eq 1` opener check so an unclosed fenced block fails the gate. F6 (debuggability): Rewrote the four `bash ${HARNESS} all >/dev/null || fail …` calls in `check_task9` to capture combined stdout/stderr into `out`, echo `out` to stderr on non-zero exit, and then fail the gate; regressions now surface the offending sub-gate instead of a silent non-zero exit.
- Phase 4 evidence — `bash _bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh all` exit 0: `PASS: task1` / `PASS: task2` / `PASS: task3` / `PASS: task4` / `PASS: task5` / `PASS: task6` / `PASS: task7` / `PASS: task8` / `PASS: task9` / `PASS: all`. Predecessor harnesses each exit 0 with `PASS: all`: `story-1-1-scaffold-validation.sh`, `story-1-2-root-files-validation.sh`, `story-1-3-root-context-validation.sh`, `story-2-1-agent-identity-validation.sh`.
- Phase 4 task-group boundary: touched only `.cursor/rules/outbound-messaging-guardrail.mdc` (F3 one-line blockquote insertion), `_bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh` (F1/F2/F3-harness/F4/F5/F6 surgical edits), `_bmad-output/implementation-artifacts/sprint-status.yaml` (one-line `review → done` flip), and this story file (Review Follow-ups task group + Senior Developer Review section + Change Log append + Completion Notes append + File List update + Status header flip). Did NOT modify the other three `.cursor/rules/*.mdc` rule files, did NOT modify `agent-identity.mdc`, did NOT modify the Story 1.1 / 1.2 / 1.3 / 2.1 harnesses, did NOT modify the baseline-audit or canonical-blueprint artifacts or the task9 handoff artifact. Every prior Dev Agent Record note above is preserved verbatim.

### Senior Developer Review (AI)

**Reviewer:** Phase 3 adversarial code-review subagent (findings) → Phase 4 follow-up pass (resolution).

**Date:** 2026-04-20

**Outcome:** All six review findings resolved. Story 2.2 validation harness `all` gate passes; four predecessor harnesses each pass `all`. No outstanding HIGH / MEDIUM / LOW findings.

**Findings summary:**

| ID | Severity | Area | Finding | Resolution |
| -- | -------- | ---- | ------- | ---------- |
| F1 | HIGH | AC6 coverage | `check_task4` and `check_task6` did not assert absence of fenced JSON / fenced code blocks; AC6 restricts fenced JSON to `teams-dm-formatting.mdc` only. | Added `^[[:space:]]*```json` and `^[[:space:]]*```` absence guards to both `check_task4` (memory) and `check_task6` (email). Harness now enforces the AC6 "prose pointers rather than inline JSON" constraint on the two affected files. |
| F2 | HIGH | Portability | `require_why_comment_terminator` used bash `[[ =~ ^\<!--.*--\>$ ]]`, where GNU regex interprets `\<` / `\>` as word-boundary anchors — inconsistent with the harness's stated POSIX portability. | Rewrote to `echo … \| grep -Eq '^<!--.*-->$'` (and parallel forms for the blockquote and italic variants) so `<` / `>` are literal characters across macOS BSD grep, GNU grep, and busybox grep. |
| F3 | MEDIUM | AC5 explicit exclusion | Outbound rule omitted an explicit Slack/SMS/iMessage exclusion; AC5 requires "explicitly excludes Slack, SMS, iMessage, and any other personal messaging surface." | Added a single blockquote line `> Personal messaging surfaces (SMS, iMessage, personal chat apps) are explicitly out of scope — this workspace is Vixxo work-only.` under `## Platforms Covered`. Slack is intentionally unnamed to preserve the banned-term scrub; the generic phrase plus named tokens satisfy AC5. `check_task3` refined to strip blockquote lines before the `NON_TEAMS_CHAT_REGEX` scan so the exclusion blockquote is permitted without weakening the outside-of-blockquote ban. |
| F4 | MEDIUM | AC10 pointer integrity | `check_task7` only verified `agent-identity.mdc` exists; it did not assert the `## Related Rule Files` pointer that Story 2.2 satisfies. | Added `grep -Fq '## Related Rule Files' "${AGENT_IDENTITY_PATH}"` to `check_task7`. Bilateral integrity: Story 2.2 now fails if Story 2.1's pointer heading is regressed. |
| F5 | MEDIUM | Counting correctness | `grep -cF '"contentType": "html"'` and `grep -cE '^[[:space:]]*```json'` count matching lines, not occurrences; two tokens on one line or an unclosed fence would pass. | Replaced `contentType` count with `grep -oF … \| wc -l \| tr -d ' '` (occurrence count). Added a fence-pair assertion: `fence_count="$(grep -cE '^[[:space:]]*```' "${TEAMS_PATH}")"; [[ ${fence_count} -eq 2 ]]` so an unclosed fenced block fails the gate. |
| F6 | LOW | Debuggability | `bash ${HARNESS} all >/dev/null` in `check_task9` suppressed `PASS` / `FAIL` output; a regression left operators with only a non-zero exit and no failing-gate name. | Rewrote each of the four sub-harness invocations: `if ! out="$(bash … 2>&1)"; then echo "${out}" >&2; fail …; fi`. Regressions now surface the offending sub-gate (and any diagnostic payload) on stderr before the parent gate fails. |

**Verification commands re-run in Phase 4:**

- `bash _bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh all` → exit 0, gates `PASS: task1` through `PASS: task9` then `PASS: all`.
- `bash _bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh all` → exit 0, `PASS: all`.
- `bash _bmad-output/implementation-artifacts/tests/story-1-2-root-files-validation.sh all` → exit 0, `PASS: all`.
- `bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh all` → exit 0, `PASS: all`.
- `bash _bmad-output/implementation-artifacts/tests/story-2-1-agent-identity-validation.sh all` → exit 0, `PASS: all`.

**Sign-off:** Story 2.2 is merge-ready. Sprint tracker and story status flipped `review → done`.

### File List

- `_bmad-output/implementation-artifacts/tests/story-2-2-baseline-audit.md` (new, Task 1 evidence)
- `_bmad-output/implementation-artifacts/tests/story-2-2-canonical-blueprint.md` (new, Task 2 evidence)
- `.cursor/rules/outbound-messaging-guardrail.mdc` (new, Task 3 output)
- `.cursor/rules/memory-vault-protection.mdc` (new, Task 4 output)
- `.cursor/rules/teams-dm-formatting.mdc` (new, Task 5 output)
- `.cursor/rules/email-triage-thread-defaults.mdc` (new, Task 6 output)
- `_bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh` (new, Task 8 output; executable harness, chmod +x applied)
- `_bmad-output/implementation-artifacts/tests/story-2-2-task9-handoff.md` (new, Task 9 handoff artifact — AC-to-file map, validation transcript, forward-compatibility notes)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified, Task 10 — `2-2-port-guardrail-and-formatting-rules.status` flipped `backlog → review`; then Phase 4 flipped `review → done`; single-line diffs per pass, all comments/blank lines/ordering preserved)
- `_bmad-output/implementation-artifacts/2-2-port-guardrail-and-formatting-rules.md` (new per git reality; all ten Task checkboxes marked complete, Dev Agent Record populated through Tasks 7 / 9 / 10, Status header flipped `ready-for-dev → review` at dev handoff; Phase 4 added Review Follow-ups (AI) task group with F1–F6 [x] items, Senior Developer Review (AI) section summarizing findings + resolution, appended Phase 4 Change Log entry, appended Phase 4 Completion Notes, updated File List, flipped Status `review → done`)

Phase 4 (Review Follow-ups) modified files:

- `.cursor/rules/outbound-messaging-guardrail.mdc` (modified — F3 one-line blockquote exclusion inserted under `## Platforms Covered` to explicitly cover SMS / iMessage / personal chat apps per AC5)
- `_bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh` (modified — F1 fenced-block absence guards in `check_task4` + `check_task6`; F2 `require_why_comment_terminator` rewritten with `grep -Eq` for BSD/GNU portability; F3 harness side-effect strips blockquote lines before the outbound `NON_TEAMS_CHAT_REGEX` scan; F4 Related-Rule-Files pointer assertion added to `check_task7`; F5 `contentType` count uses `grep -oF | wc -l` and fence-pair count == 2 assertion added; F6 each sub-harness invocation in `check_task9` captures combined output and echoes on non-zero exit)
