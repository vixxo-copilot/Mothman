# Story 2.2 — Task 9 Handoff Readiness Package

Generated: 2026-04-20 (Phase 2, Amelia — Dev, Tasks 7/9/10)

## Purpose

Package the Story 2.2 validation evidence for code review and downstream story consumption. This document maps every acceptance criterion to its harness gate and the rule-pack file(s) it exercises, captures the full validation-command transcript (Story 2.2 harness plus Story 1.1/1.2/1.3/2.1 regression harnesses), and records forward-compatibility notes for Stories 2.3 and 2.4.

## AC-to-file map (AC1 through AC12)

| AC  | Harness gate(s)                                      | Rule file(s) and supporting artifacts                                                                                                                                                                                                                                                                                          |
| --- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| AC1 | `task3`, `task4`, `task5`, `task6`                   | `.cursor/rules/outbound-messaging-guardrail.mdc`, `.cursor/rules/memory-vault-protection.mdc`, `.cursor/rules/teams-dm-formatting.mdc`, `.cursor/rules/email-triage-thread-defaults.mdc` — file existence + Cursor Rules v6.x frontmatter (`description`, `globs`, `alwaysApply: true`), `globs: memory/**` only for the memory rule |
| AC2 | `task3`, `task4`, `task5`, `task6`, `task7`          | All four rule files — placeholder audit (only `{{employee_name}}` appears in bodies; the approved token set `{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}` is the cross-pack allowlist; zero hard-coded employee/assistant/family/company proper names other than "Vixxo")        |
| AC3 | `task3`, `task4`, `task5`, `task6`, `task7`          | All four rule files — Story 2.1 banned-term set plus `slack` plus `benji` with POSIX-ERE boundary guards; `regex_self_probe` fail-fast confirms host `grep -E` honors the guards for `ASU`/`blog`/`deke`/`arete`/`eudaimonia`/`slack`/`benji`                                                                                   |
| AC4 | `task6`                                              | `.cursor/rules/email-triage-thread-defaults.mdc` — Microsoft 365 framing present, `## Gmail` heading absent, Gmail/Google/INBOX-label/`google-workspace`/`chiron/inspiration` all zero                                                                                                                                          |
| AC5 | `task3`, `task5`, `task7`                            | `.cursor/rules/outbound-messaging-guardrail.mdc`, `.cursor/rules/teams-dm-formatting.mdc` — Microsoft Teams scope present, non-Teams chat surfaces (Slack/Discord/Mattermost/iMessage/SMS/Google Chat) absent                                                                                                                   |
| AC6 | `task5`                                              | `.cursor/rules/teams-dm-formatting.mdc` — `"contentType": "html"` appears exactly once, locked neutral body `<p>Short status update. -- AI assistant for {{employee_name}}</p>`, zero email-address patterns, exactly one fenced JSON block; other rules carry zero fenced JSON                                                |
| AC7 | `task4`                                              | `.cursor/rules/memory-vault-protection.mdc` — every Epic 3 memory path enumerated (`memory/me/identity.md`, `memory/me/preferences.md`, `memory/meetings/_template/{meeting,agenda,prep,transcript}.md`, `memory/people/_template.md`, `memory/decisions/_template.md`, `memory/reference/_template.md`, `memory/inbox/_template.md`, `memory/appreciations/_template.md`); "work context only" framing present; `personal AI life operating system`, `PII is the product`, `family.md`, `ventures.md` all absent |
| AC8 | `task6`                                              | `.cursor/rules/email-triage-thread-defaults.mdc` — `Microsoft 365` framing, `conversationId` primitive, all seven required tag/status tokens (`Ask`/`Decision`/`FYI`/`Open`/`Closed`/`Waiting`/`Superseded`), one-line "why" comment terminator                                                                                 |
| AC9 | `task3`, `task4`, `task5`, `task6`, `task7`          | All four rule files — last non-blank line matches `^<!--.*-->$` (HTML-comment form); "why" comment itself scrubbed (zero banned terms)                                                                                                                                                                                         |
| AC10| `task7`, `task9` (regression against Story 2.1)      | All four sibling rules cross-reference `.cursor/rules/agent-identity.mdc`; duplicated-identity-block guard passes (no sibling contains both `Vixxo employee` and `work context only` in body; `work context only` appears only in `memory-vault-protection.mdc`'s opening paragraph, exactly once); `agent-identity.mdc` not edited |
| AC11| `task7`, `task9` (Story 1.1/1.2/1.3/2.1 regression)  | Placeholder parity across rule pack (only approved tokens appear); Story 1.1 extension-based `.cursor/rules/*.mdc` allowlist admits all four new files without harness edits; Story 1.3 root files (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`) and Story 2.1 rule remain green                                                    |
| AC12| `task1`–`task9`, `all`                               | `_bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh` — `all` gate exits 0; each of `task1` through `task9` individually exits 0; `task9` regression invokes Story 1.1/1.2/1.3/2.1 `all` runs, all return zero                                                                           |

Supporting evidence artifacts:

- `_bmad-output/implementation-artifacts/tests/story-2-2-baseline-audit.md` (Task 1)
- `_bmad-output/implementation-artifacts/tests/story-2-2-canonical-blueprint.md` (Task 2)
- `_bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh` (Task 8; executable harness)

## Validation transcript

Commands run in `_bmad-output/implementation-artifacts/tests/` working tree at 2026-04-20. All exit codes captured; every harness exits 0 on success.

### Story 2.2 harness — `all` mode

```
$ bash _bmad-output/implementation-artifacts/tests/story-2-2-guardrail-and-formatting-validation.sh all
PASS: task1
PASS: task2
PASS: task3
PASS: task4
PASS: task5
PASS: task6
PASS: task7
PASS: task8
PASS: task9
PASS: all
(exit 0)
```

### Story 1.1 regression

```
$ bash _bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh all
PASS: all
(exit 0)
```

### Story 1.2 regression

```
$ bash _bmad-output/implementation-artifacts/tests/story-1-2-root-files-validation.sh all
PASS: all
(exit 0)
```

### Story 1.3 regression

```
$ bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh all
PASS: all
(exit 0)
```

### Story 2.1 regression

```
$ bash _bmad-output/implementation-artifacts/tests/story-2-1-agent-identity-validation.sh all
PASS: all
(exit 0)
```

### Task 7 cross-file scrub evidence

- Banned-term unbounded regex (`neighbors|chiron|revivago|derekneighbors\.com|agile weekly|masterylab|bodybuilding\.com|gangplank|gtd-life|gmail|google calendar|google workspace|google drive|google chat|personal email|slack|benji`) — 0 matches per file across all four files.
- Boundary-guarded short-token regex (`(^|[^A-Za-z])(derek|deke|asu|blog|arete|eudaimonia)($|[^A-Za-z])`) — 0 matches per file across all four files.
- Placeholder inventory across pack — exactly `{{employee_name}}` appears (no drift, no new tokens introduced).
- Deferred-content constraints:
  - `outbound-messaging-guardrail.mdc`: 0 matches for `graph.microsoft|"contentType"|<p>|<br>|<div>|<span>|<a href`; 0 fenced-code-block openers.
  - `memory-vault-protection.mdc`: 0 matches for `gmail|google|slack|<p>|<br>|<div>|<span>`; 0 fenced-code-block openers.
  - `teams-dm-formatting.mdc`: 0 matches for `gmail|google|slack`; `"contentType": "html"` count = 1 (allowed — required payload shape per AC6).
  - `email-triage-thread-defaults.mdc`: 0 `^## Gmail` headings; 0 matches for `gmail|google|chiron/inspiration|inbox label|google-workspace`; 0 fenced-code-block openers.
- Cross-reference check: each of the four sibling rule files references `agent-identity.mdc` exactly once.
- Duplicated-identity-block guard: no sibling contains both `Vixxo employee` and `work context only`; `work context only` appears only in `memory-vault-protection.mdc` (1 occurrence).
- AC9 "why"-comment terminators (last non-blank line per file):
  - `outbound-messaging-guardrail.mdc`: `<!-- Why: protects recipients and {{employee_name}}'s reputation from unauthorized AI-sent messages. -->`
  - `memory-vault-protection.mdc`: `<!-- Why: the work memory vault is {{employee_name}}'s source of truth — deletions cost meetings, decisions, and context. -->`
  - `teams-dm-formatting.mdc`: `<!-- Why: Teams is conversational — walls of text and wrong signatures cost trust. -->`
  - `email-triage-thread-defaults.mdc`: `<!-- Why: email threads lose signal when collapsed; preserve structure so {{employee_name}} can decide fast. -->`

## Forward-compatibility notes

- **Story 2.3** will add `agents/personas/work.md` (single generic work persona). Story 2.1's `agent-identity.mdc` already references `agents/personas/work.md` via its `Key References` section, and Story 1.1's extension-based allowlist (refactored in Story 2.1 Phase 4 F7) admits any `.mdc` under `.cursor/rules/`. Story 2.3's `work.md` lands under `agents/personas/`, not `.cursor/rules/`, so no edits to the Story 2.2 rule pack or its harness are required for 2.3.
- **Story 2.4** will assert `.cursor/rules/benji-inbox-default.mdc` is NOT present. Story 2.2's harness actively fails on any occurrence of the boundary-guarded token `benji` across the rule pack (including its frontmatter and body), so 2.4's negative assertion is complementary and does not supersede the 2.2 scrub.
- **Story 3.1** will populate the memory-path targets enumerated by `memory-vault-protection.mdc`. The rule is authored to protect paths that do not yet exist; this is intentional and safe under `alwaysApply: true` + `globs: memory/**`.
- **Placeholder contract:** Only `{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}` are approved for cross-story use. This story's rule bodies use only `{{employee_name}}`; the remaining three tokens remain in the shared inventory for Story 1.3 / 2.1 / 3.3 consumption. No new placeholder token was introduced.

## Summary

Story 2.2 is code-review ready. All twelve acceptance criteria have at least one harness gate confirming them; the Story 2.2 harness passes in `all` mode and per-gate mode; all four predecessor harnesses (Story 1.1, 1.2, 1.3, 2.1) pass in `all` mode. No regressions to `agent-identity.mdc`, the Story 1.x root files, or any predecessor harness.
