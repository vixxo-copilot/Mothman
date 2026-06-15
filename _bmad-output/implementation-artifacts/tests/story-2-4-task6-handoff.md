# Story 2.4 Task 6 — Handoff Readiness Package

Story: `2-4-confirm-benji-inbox-default-not-ported`
Linear: AIP-32
Date: 2026-04-20
Agent: Amelia (BMAD autonomous Developer, Claude Opus 4.7)

This artifact is the Phase-2 Dev-to-Review handoff package for Story 2.4.
It provides an AC-to-file evidence map, a full validation transcript
covering the new Story 2.4 harness plus all six predecessor harnesses, a
zero-edit verification over the Story 2.1 / 2.2 / 2.3 artifacts, and a
forward-looking note covering Epic 3 (memory scaffolds) and Epic 6
(GitHub Action denylist).

## AC-to-file evidence map

| AC   | Claim | Evidence location |
|------|-------|-------------------|
| AC1  | `.cursor/rules/benji-inbox-default.mdc` does not exist | Harness `check_task2` gate + `[[ ! -e "${BANNED_RULE_PATH}" ]]` assertion; `ls .cursor/rules/` shows five `.mdc` files, none starting with `benji` |
| AC1  | No `benji*.mdc` anywhere in the repo outside evidence paths | Harness `check_task2` repository-wide `find` scan; exclusions `_bmad-output/`, `_bmad/`, `.git/` |
| AC1  | Existing Story 2.1 + 2.2 rule pack + Story 2.3 persona remain byte-for-byte unchanged | Harness `check_task3` integrity gate (all six files present and non-empty); `git status` shows zero modifications to those files |
| AC2  | Pattern-level scan rejects any `benji`-prefixed or `-benji-` / `_benji_` / `benji-inbox` / `benji_inbox` basename | Harness `check_task2` enumeration of `.cursor/rules/*.mdc`, `*.md`, `*.markdown` with `BENJI_BASENAME_PATTERN='^[Bb][Ee][Nn][Jj][Ii]'` + case statement for substring shapes |
| AC2  | Scope limited to `.cursor/rules/` at the file-level (persona + docs + memory content scrubs owned by other stories) | Harness confines basename glob to `${RULES_DIR}/*.{mdc,md,markdown}`; repo-wide `find` only matches `benji*.mdc`, `benji*.md`, `benji*.markdown` |
| AC3  | Story 2.3 harness still exits `0` with `PASS: all` | Harness `check_task6` regression gate invokes `bash story-2-3-work-persona-validation.sh all` and requires zero exit (see transcript below) |
| AC3  | Story 2.4 performs its own boundary-guarded `benji` probe (not duplicating Story 2.3's persona scan) | Harness `regex_self_probe` with synthetic `benjiman` (negative) and `benji inbox` (positive) test cases; invoked by `check_task4` |
| AC3  | Complementary-not-duplicative relationship documented | Harness header comment block (lines 4–15); baseline-absence-audit `## Complement to Story 2.3 content scrub` section |
| AC4  | Deterministic harness exists, executable, invokable with `bash <path> <gate>` and `bash <path> all` | `_bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh` (exists, chmod +x, shebang on line 1, `set -euo pipefail` on line 2) |
| AC4  | PASS/FAIL contract matches Story 2.1 / 2.2 / 2.3 | Harness emits `PASS: <gate>` on stdout per passing gate, `FAIL: <gate>: <reason>` on stderr with exit 1 on failure, `PASS: all` on full run |
| AC4  | Optional docs/setup.md checklist line | SKIPPED — the OR-clause in AC4 permits harness-only satisfaction. See "Task 4 skip rationale" section below. |
| AC5  | `task1` baseline-absence-audit evidence | `_bmad-output/implementation-artifacts/tests/story-2-4-baseline-absence-audit.md` contains the five required section headers |
| AC5  | `task2` file-absence + pattern-level + repo-wide | Gate passes; banned rule absent; enumeration finds zero `benji`-prefixed entries; `find` outputs zero rows outside evidence paths |
| AC5  | `task3` rule-pack integrity | Gate passes; five `.mdc` files + `agents/personas/work.md` all exist and non-empty; `agent-identity.mdc` still references persona path |
| AC5  | `task4` content-scrub parity probe | Gate passes; `regex_self_probe` confirms host grep honors boundary guard |
| AC5  | `task5` self-check | Gate passes; shebang, `set -euo pipefail`, all 7 case branches, all 13 required constants, `regex_self_probe` function all present |
| AC5  | `task6` regression (six sub-harnesses) | Gate passes; see transcript below — each of the six harnesses exits zero with final `PASS: all` |
| AC5  | BSD+GNU portable tooling (`bash`, `grep`, `awk`, `sed`, `find` + built-ins; no `rg`; no Python) | Harness uses only `grep -E`, `grep -F`, `grep -i`, `find -type f -name -not -path -print`, `head -n`, `tr`, `basename`, bash built-in `[[` and `case` |
| AC6  | Prior harnesses exit `0` with `PASS: all`; zero bytes changed in any prior harness | Transcript below; `git status` confirms `_bmad-output/implementation-artifacts/tests/story-{1-1,1-2,1-3,2-1,2-2,2-3}-*.sh` unmodified |
| AC6  | Zero bytes changed in `.cursor/rules/*.mdc`, `agents/personas/work.md`, root context files, README/LICENSE/.gitignore | Story 2.4 added only three files under `_bmad-output/implementation-artifacts/tests/` plus edited `sprint-status.yaml` (single status flip) and this story file (DAR / checkboxes) |
| AC7  | Sprint tracker flip to `review` | `_bmad-output/implementation-artifacts/sprint-status.yaml` updated: `2-4-confirm-benji-inbox-default-not-ported.status` → `review`. Phase-1 `backlog → ready-for-dev` and `last_updated: 2026-04-20` were already set by the SM pass. |
| AC7  | `epic-2.status` remains `in-progress` | Verified unchanged; the in-progress→done transition is an explicit separate post-Story-2.4 evidence pass |
| AC7  | Byte-for-byte preservation of comments, ordering, spacing in `sprint-status.yaml` | Single-line diff: the `2-4-*.status` value only |
| AC8  | Story is additive — no new files under `.cursor/rules/`, `agents/`, `memory/`, `docs/legal/`, `bin/`, `scripts/` | Only three new files under `_bmad-output/implementation-artifacts/tests/`; modifications confined to `sprint-status.yaml` + this story file |

## Task 4 skip rationale

Task 4 (optional docs/setup.md checklist line) is explicitly marked OPTIONAL
in the story. AC4 specifies a CI-assertion OR checklist-item satisfaction
contract, and the Story 2.4 harness satisfies the CI-assertion half on its
own. Amelia elected to SKIP Task 4 on the following grounds:

1. The epic AC uses an "OR" between CI assertion and checklist item —
   either alone satisfies the contract. The harness alone passes.
2. Adding a new `## Exclusions (not ported)` heading to `docs/setup.md`
   introduces text containing the literal token `benji` (as part of the
   banned filename citation). While no CURRENT predecessor harness scans
   `docs/setup.md` for banned-term content (verified: Story 1.2 only
   asserts file-existence; Story 2.3 confines its banned-term scan to
   `agents/personas/work.md`; the cross-pack placeholder parity scan in
   Story 2.3 does NOT include `docs/setup.md`), a FUTURE harness that
   extends content scrubs to docs could trip on the checklist line.
3. The story's Task 4 subtask includes an explicit "if any regression
   occurs, revert the docs edit and rely on the harness alone" escape
   hatch. Skipping preemptively is equivalent to exercising that escape
   hatch at zero cost, and it preserves `docs/setup.md` byte-for-byte.
4. AC8 is additive-only; skipping Task 4 produces strictly fewer diffs
   and strictly less risk for review.

Net result: Story 2.4 satisfies AC4 via the harness path alone. If a
future epic elects to add the exclusion bullet to `docs/setup.md`, it can
do so independently without touching the Story 2.4 harness.

## Full validation command transcript

All commands run from `/Users/dneighbors/Public/assistants-template`.

### Story 2.4 harness — full `all` mode

```
$ bash _bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh all
PASS: task1
PASS: task2
PASS: task3
PASS: task4
PASS: task5
PASS: task6
PASS: all
$ echo "EXIT=$?"
EXIT=0
```

### Story 2.4 harness — per-gate smoke check (task1–task5)

```
$ bash _bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh task1
PASS: task1

$ bash _bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh task2
PASS: task2

$ bash _bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh task3
PASS: task3

$ bash _bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh task4
PASS: task4

$ bash _bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh task5
PASS: task5
```

(Per-gate invocations print a single `PASS: <gate>` — the end-of-script
`echo "PASS: ${mode}"` emits it once because the individual `task1)`–`task5)`
case arms do not print their own `PASS:` line. In `all` mode, each
`check_taskN` function is followed by an explicit `echo "PASS: taskN"`
line, and then the end-of-script `echo "PASS: all"` fires. This matches
the Story 2.3 harness contract exactly.)

### Predecessor harnesses — each in `all` mode (direct, not via task6)

```
$ bash _bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh all
PASS: all
EXIT=0

$ bash _bmad-output/implementation-artifacts/tests/story-1-2-root-files-validation.sh all
PASS: all
EXIT=0

$ bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh all
PASS: all
EXIT=0

$ bash _bmad-output/implementation-artifacts/tests/story-2-1-agent-identity-validation.sh all
PASS: all
EXIT=0

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
EXIT=0

$ bash _bmad-output/implementation-artifacts/tests/story-2-3-work-persona-validation.sh all
PASS: task1
PASS: task2
PASS: task3
PASS: task4
PASS: task5
PASS: task6
PASS: all
EXIT=0
```

Every one of the seven harnesses (Story 2.4 plus the six predecessors)
exits `0` with its contractual `PASS: all` line. No failures. No
regressions.

## Zero-edit verification

Story 2.4 is strictly additive. Verified by inspection before handoff:

- `.cursor/rules/agent-identity.mdc` — unchanged (byte-for-byte; Story 2.1 output).
- `.cursor/rules/outbound-messaging-guardrail.mdc` — unchanged (Story 2.2).
- `.cursor/rules/memory-vault-protection.mdc` — unchanged (Story 2.2).
- `.cursor/rules/teams-dm-formatting.mdc` — unchanged (Story 2.2).
- `.cursor/rules/email-triage-thread-defaults.mdc` — unchanged (Story 2.2).
- `agents/personas/work.md` — unchanged (Story 2.3).
- Root context files (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`) — unchanged (Story 1.3).
- `README.md`, `LICENSE`, `.gitignore` — unchanged (Story 1.2).
- `docs/setup.md`, `docs/legal/*` — unchanged (Task 4 SKIP).
- All prior harnesses under `_bmad-output/implementation-artifacts/tests/story-{1-1,1-2,1-3,2-1,2-2,2-3}-*.sh` — unchanged (regression invokes them; does not edit them).

Files Story 2.4 creates (three under `_bmad-output/implementation-artifacts/tests/`):

- `story-2-4-baseline-absence-audit.md` (Task 1)
- `story-2-4-benji-inbox-absence-validation.sh` (Task 2; chmod +x)
- `story-2-4-task6-handoff.md` (Task 6; this file)

Files Story 2.4 modifies:

- `_bmad-output/implementation-artifacts/sprint-status.yaml` (Task 7 status flip)
- `_bmad-output/implementation-artifacts/2-4-confirm-benji-inbox-default-not-ported.md` (DAR / Change Log / File List / checkboxes)

## Forward-looking notes

### Epic 3 — memory vault scaffolds (Stories 3.1 / 3.2 / 3.3)

Epic 3 will populate `memory/me/` and `memory/companies/` scaffolds. None
of those scaffolds may re-introduce a `benji-inbox-default.mdc` file.

The Story 2.4 harness's repository-wide `find` gate (`check_task2`) will
catch any such attempt because the scan excludes only `_bmad-output/`,
`_bmad/`, and `.git/` — `memory/` is in-scope for the scan. If Story 3.1
accidentally copies `~/Public/gtd-life/.cursor/rules/benji-inbox-default.mdc`
into `memory/companies/gtd-life/`, the Story 2.4 harness will fail `task2`
with `FAIL: task2: repository-wide scan found banned benji*.mdc file: ...`
before the developer commits.

### Epic 4 — MCP packaging (Stories 4.1 / 4.2 / 4.3 / 4.4)

Epic 4 will add `.cursor/mcp.json` and related MCP configuration. The
Story 2.4 harness does NOT scan `.cursor/mcp.json` for the banned token
(that is Story 2.3's persona scan's domain and the forthcoming Epic 6
denylist's domain). Epic 4 remains orthogonal to Story 2.4's
file-absence assertion.

### Epic 6 — PII scrub and CI guardrail (Stories 6.1 / 6.2)

Epic 6 will add a shared PII denylist and a GitHub Action that blocks
PRs violating the denylist. The Story 2.4 harness is already
GitHub-Actions-ready: it exits `0` on pass and `1` on fail; it prints
`PASS: <gate>` lines on stdout and `FAIL: <gate>: <reason>` lines on
stderr; it has zero external dependencies beyond `bash`, `grep`, `awk`,
`sed`, `find`, and shell built-ins (all present on GitHub Actions
`ubuntu-latest` and `macos-latest` runners); it uses no GNU-only regex
extensions. Epic 6 Story 6.2's GitHub Action can invoke:

```yaml
- name: Rule-file absence check (Story 2.4)
  run: bash _bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh all
```

without modification to the harness.

### Epic 7 — pilot rollout

When the `assistants-template` is rolled out to the Vixxo AI cohort, any
cohort member cloning the template receives the Story 2.4 harness as
part of the repository. If an over-eager port-everything script at
rollout time attempts to copy the cohort member's personal gtd-life
rules into the work template, the Story 2.4 harness catches it on the
first local `bash story-2-4-benji-inbox-absence-validation.sh all`
invocation — before the PR is raised against the template.

## Summary

Story 2.4 installs a deterministic, POSIX-portable, CI-ready file-level
absence assertion for the Benji inbox rule. The harness is complementary
to (not a replacement for) Story 2.3's content-level scrub of the work
persona, and all six predecessor harnesses continue to pass unchanged.
Zero bytes changed in Story 2.1 / 2.2 / 2.3 artifacts. Task 4 skipped
by design under AC4's OR clause. Ready for Phase 3 code review.
