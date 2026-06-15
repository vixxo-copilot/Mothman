# Story 2.1 — Task 6 Handoff

- Story: `2-1-port-agent-identity-rule-generic`
- Linear: `AIP-29`
- Date: 2026-04-20
- Gate owner: Amelia (Dev)

## Summary

Task 6 regression-and-handoff gate is green. Story 2.1's deterministic
validation harness (`story-2-1-agent-identity-validation.sh all`) and each
Story 1.x regression harness (`story-1-1-scaffold-validation.sh all`,
`story-1-2-root-files-validation.sh all`,
`story-1-3-root-context-validation.sh all`) return exit 0 with `PASS: all`.

The Story 1.1 scaffold harness was minimally updated so its `task6`
scaffold-content guard allowlists `.cursor/rules/agent-identity.mdc`
alongside `.gitkeep`. This is a forward-compatibility edit only; every other
branch of `check_task6` — including the `agents/personas`, `bin`, `memory`,
`scripts` exclusion lists and the PII-term scan over the scaffold
`.gitkeep` files and `.gitignore` — is untouched.

With that allowlist in place, Story 2.1's harness can now invoke Story 1.1
with `all` rather than the previous narrower `task5` gate; this is the
stronger regression signal and matches the `all`-invocation pattern used
for Stories 1.2 and 1.3.

## AC-to-file map

| AC | Requirement | Evidence file |
| --- | --- | --- |
| AC1 | Rule file exists at `.cursor/rules/agent-identity.mdc` with `{{employee_name}}` placeholder; no hard-coded employee name | `.cursor/rules/agent-identity.mdc` (Task 3 artifact); asserted by harness `task3`, `task4` |
| AC2 | Rule declares `Vixxo employee` and `work context only` verbatim; personal/home/family scope explicitly out of bounds | `.cursor/rules/agent-identity.mdc` Scope section; asserted by harness `task3` |
| AC3 | Zero banned-term occurrences (Derek, Deke, Neighbors, Chiron, RevivaGo, derekneighbors.com, Agile Weekly, MasteryLab, Bodybuilding.com, Gangplank, ASU, gtd-life, arete, eudaimonia, blog, Gmail, Google Calendar, Google Workspace, personal email) | `.cursor/rules/agent-identity.mdc`; asserted by harness `task4` (`BANNED_TERMS_REGEX`) |
| AC4 | Frontmatter has `description`, `globs`, `alwaysApply: true` | `.cursor/rules/agent-identity.mdc` lines 1–5; asserted by harness `task3` |
| AC5 | References `agents/personas/work.md`, `memory/me/identity.md`, `memory/me/preferences.md`; no `vixxo-cto.md`, `revivago-ceo.md`, `personal.md` | `.cursor/rules/agent-identity.mdc` Key References section |
| AC6 | Defers Outlook Comment reply workflow and Teams HTML formatting detail to Story 2.2 sibling rules | `.cursor/rules/agent-identity.mdc` Related Rule Files section; asserted by harness `task4` (zero inline JSON / Graph Comment payloads) |
| AC7 | Story 1.3 root files (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`) unchanged; placeholder parity preserved | Asserted by harness `task4` (root-file placeholder parity + hard-coded-name negative scan) |
| AC8 | Deterministic validation harness exists and passes; covers Story 1.1/1.2/1.3 regression | `_bmad-output/implementation-artifacts/tests/story-2-1-agent-identity-validation.sh`; asserted by self-check `task5` plus full `task6` regression invocation |

## Validation command transcript

```
$ bash _bmad-output/implementation-artifacts/tests/story-2-1-agent-identity-validation.sh all
PASS: all

$ bash _bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh all
PASS: all

$ bash _bmad-output/implementation-artifacts/tests/story-1-2-root-files-validation.sh all
PASS: all

$ bash _bmad-output/implementation-artifacts/tests/story-1-3-root-context-validation.sh all
PASS: all
```

All four commands exit 0.

## Story 1.1 harness allowlist update

- File: `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh`
- Function: `check_task6`
- Change: for the `.cursor/rules` iteration only, the non-scaffold filter is
  `grep -Ev '^(\.gitkeep|agent-identity\.mdc)?$'` instead of the generic
  `grep -Ev '^(\.gitkeep)?$'`. The other four directories in the same loop
  (`agents/personas`, `bin`, `memory`, `scripts`) keep the original filter
  unchanged, and the PII-term scan over `.gitkeep` files and `.gitignore` is
  unchanged. This is the minimal edit that keeps Story 1.1's `all` gate green
  in the presence of the legitimate Story 2.1 rule file.

## Forward-looking notes

- Story 2.2 will add sibling rule files under `.cursor/rules/` (e.g.
  `outbound-messaging-guardrail.mdc`, `memory-vault-protection.mdc`,
  `teams-dm-formatting.mdc`, `email-triage-thread-defaults.mdc`). When those
  land, the Story 1.1 `check_task6` allowlist will need another minimal
  expansion (add each new filename to the `.cursor/rules` alternation) and
  the Story 2.2 harness should follow the same `all`-invocation pattern this
  story now uses.
- Story 2.3 will add `agents/personas/work.md`. Story 1.1's
  `agents/personas` branch will need an equivalent allowlist expansion at
  that time (add `work\.md` to the grep alternation for that directory
  only).
- The banned-term scan logic in
  `story-2-1-agent-identity-validation.sh` is untouched by this handoff;
  only the Story 1.x invocation pattern in `task6` changed.

## Files touched by Task 6

- `_bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh` (modified — `.cursor/rules` allowlist in `check_task6`)
- `_bmad-output/implementation-artifacts/tests/story-2-1-agent-identity-validation.sh` (modified — `task6` now invokes `story-1-1` with `all`)
- `_bmad-output/implementation-artifacts/tests/story-2-1-task6-handoff.md` (new — this file)
