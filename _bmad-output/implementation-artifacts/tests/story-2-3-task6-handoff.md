# Story 2.3 Task 6 — Regression and Handoff Readiness

Generated: 2026-04-20 (Phase 2, Dev agent Amelia). Single generic work persona at `agents/personas/work.md` is authored, validated, and regressed against every predecessor story harness.

## AC-to-file evidence map

| AC | Evidence | Gate(s) |
| --- | --- | --- |
| AC1 — single persona file + frontmatter delimiters | `agents/personas/work.md` exists, non-zero byte, opens with `---` on line 1 | `task3` (file exists + frontmatter delimiters + required headers) |
| AC2 — frontmatter metadata with `scope: work` + placeholders | Exact-line match on seven frontmatter keys (`type`, `scope`, `role`, `department`, `name`, `manager`, `tags`) | `task3` (frontmatter keys + tags inline list) |
| AC3 — five active Vixxo MCPs only | Table `\| MCP \| Purpose \|` with `**Linear**`, `**GitHub**`, `**Microsoft 365**`, `**Salesforce**`, `**Gong**` exactly once; zero banned MCP tokens | `task3` (active-MCP positive count), `task4` (banned-MCP negative scan) |
| AC4 — banned-term scrub + regex self-probe + sensitive-data patterns | `grep -n -i -E "${BANNED_TERMS_REGEX}" agents/personas/work.md` returns no matches; regex self-probe passes all nine boundary-guard probes (`derek`, `ASU`, `blog`, `deke`, `arete`, `eudaimonia`, `slack`, `benji`, `family`); email / phone / GUID / Teams chatId patterns each return zero matches (post-review F3 extension) | `task4` (scrub + regex_self_probe + email/phone/GUID/chatId guards) |
| AC5 — M365-only email/calendar/task routing | `Microsoft 365 (Outlook).`, `Microsoft 365 (Outlook calendar).`, `Linear (Vixxo work task system).` present; `NON_M365_ROUTING_REGEX` returns zero matches | `task4` (routing one-liners + non-M365 scan) |
| AC6 — voice-biography absence | `VOICE_BIOGRAPHY_REGEX` (covers `### Voice Directives`, `NVC`, `Non-Violent Communication`, `Lift people up`, `Bias to action`) returns zero matches | `task4` (voice-biography scan) |
| AC7 — cross-reference integrity | `## Context Files` six bullets in locked order (exact-line match); identity rule at `.cursor/rules/agent-identity.mdc` still references `agents/personas/work.md`; no sibling persona files exist | `task3` (Context Files bullets), `task4` (identity pointer + sibling-persona absence) |
| AC8 — one-line "why" comment terminator | Last non-blank line matches `^<!--.*-->$` and contains zero banned terms | `task4` (require_why_comment_terminator helper) |
| AC9 — deterministic harness + regression | `bash story-2-3-work-persona-validation.sh all` exits 0 with `PASS: all`; `task6` invokes Story 1.1 / 1.2 / 1.3 / 2.1 / 2.2 harnesses in `all` mode | full transcript below |
| AC10 — sprint tracker lifecycle | `_bmad-output/implementation-artifacts/sprint-status.yaml` `2-3-create-single-generic-work-persona.status` transitioned to `review`; `epic-2.status` preserved as `in-progress`; `last_updated: 2026-04-20` | Task 7 diff on sprint-status.yaml |

## Full validation transcript

### Story 2.3 harness

```
$ bash _bmad-output/implementation-artifacts/tests/story-2-3-work-persona-validation.sh all
PASS: task1
PASS: task2
PASS: task3
PASS: task4
PASS: task5
PASS: task6
PASS: all
```

### Regression harnesses

```
$ bash _bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh all
PASS: all

$ bash _bmad-output/implementation-artifacts/tests/story-1-2-root-files-validation.sh all
PASS: all

$ bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh all
PASS: all

$ bash _bmad-output/implementation-artifacts/tests/story-2-1-agent-identity-validation.sh all
PASS: all

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
```

Every harness exited `0`. Every predecessor gate remains green.

## Zero-edit verification — identity rule still points at the persona

`grep -n "agents/personas/work.md" .cursor/rules/agent-identity.mdc` returns hits under both `## Work Persona` and `## Key References`. Story 2.1's pointer now resolves to a real file.

## Forward-looking notes

- **Story 2.4** will assert `.cursor/rules/benji-inbox-default.mdc` is NOT present (directory-level complementary scrub). Story 2.3's harness already fails on `benji` as a boundary-guarded banned term, so Story 2.4 layers a file-absence check on top.
- **Story 3.3** will populate `memory/me/identity.md` and `memory/me/preferences.md` — the two memory-vault paths this persona's `## Context Files` section references. The files do not need to exist for Story 2.3 to pass; Story 3.3 seeds them as empty stubs.
- **Story 5.2 (wizard)** will replace the four placeholders in `agents/personas/work.md` (`{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}`) with real values from the interactive prompt answers. The four-token placeholder contract is locked for wizard parity.
- **Epic 4 Story 4.1** will wire the five active MCPs in `.cursor/mcp.json`; the persona's `## Available MCPs` table is the human-readable companion to that machine-readable config.

No regression. No halt condition. Story 2.3 is ready for `review`.
