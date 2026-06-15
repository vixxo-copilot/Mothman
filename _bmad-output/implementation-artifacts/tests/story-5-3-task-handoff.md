# Story 5.3 Task Handoff

Date: 2026-04-22
Story: `5-3-wizard-runs-skills-install-and-verifies`

## AC-to-evidence map

| AC | Evidence |
| --- | --- |
| AC1 | `runPostWizardSetup()` in `bin/init`; harness `story-5-3 ... task4` confirms deterministic heading order (`skills install -> active MCP verification -> summary`) and fast-path isolation via `--help` checks in `task3`. |
| AC2 | `runSkillsInstall()` executes `npx skills add vixxo-copilot/agent-skills` once; unit tests cover success, ENOENT, signal, and non-zero exit. |
| AC3 | `loadActiveMcpConfig()` / `loadActiveMcpServerKeys()` parse `.cursor/mcp.json` and enforce `mcpServers` object contract; verification scope keyed to active JSON order. |
| AC4 | `verifyActiveMcps()` emits deterministic per-server `{server_key,status,reason,remediation}` results with one probe per active key. |
| AC5 | `mcpRemediationFor()` + summary output include explicit key-level remediation commands/links; harness `task5` checks failure rendering including rerun command text. |
| AC6 | `summarizePostWizard()` + `printPostWizardSummary()` output PASS/FAIL counts and failing keys; `main()` exit code uses post-wizard summary result. |
| AC7 | Story 5.2 write/cancel flow remains intact: reruns of Story 5.2 and Story 5.1 harnesses both `PASS: all`. |
| AC8 | `BMAD_STORY_5_3_FIXTURE_PATH` fixture mode implemented; `validateStory53FixturePayload()` fails malformed payloads fast; harness `task6` validates invalid-fixture failure path. |
| AC9 | Story 5.2 harness compatibility updated and passing under Story 5.3 behavior; Story 5.3 harness becomes source of truth for post-wizard checks. |
| AC10 | `_bmad-output/implementation-artifacts/tests/story-5-3-wizard-runs-skills-install-and-verifies-validation.sh` exists, executable, and passes `task1..task9` plus `all`. |
| AC11 | Evidence set present: baseline audit, canonical blueprint, this handoff, plus test/harness transcripts and checksums below. |
| AC12 | Sprint status updated through implementation lifecycle for Story 5.3 with Epic 5 remaining `in-progress` until close. |

## Validation transcripts

```text
$ node --test test/bin-init.story-5-3.test.js
tests: 10
pass: 10
fail: 0
```

```text
$ bash _bmad-output/implementation-artifacts/tests/story-5-3-wizard-runs-skills-install-and-verifies-validation.sh all
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

```text
$ bash _bmad-output/implementation-artifacts/tests/story-5-2-wizard-prompts-and-file-generation-validation.sh all
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

```text
$ bash _bmad-output/implementation-artifacts/tests/story-5-1-bin-init-validation.sh all
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

## Key checksums

```text
759c69f90d57e7d2879c0f55d917a7617aae1be9e25716ad57e236751b95932d  bin/init
d4b7e14d64f098134d6a54a3d86fba72394c6a79cf010d9eec2eeef0648daadb  test/bin-init.story-5-3.test.js
a611a21920daa25c0a392f566e386f2bca104b85bc179997e844e18240b125d5  tests/story-5-3-baseline-audit.md
1092566757a1b3c7573c11b8da16efd4676cdb88f35046030bee193e7d6412ae  tests/story-5-3-canonical-blueprint.md
913ebdc45a562caa41493d27b8525a6e597f0b58f4a84e860983ef0dd1e52275  tests/story-5-3-wizard-runs-skills-install-and-verifies-validation.sh
```

## Review-fix notes

- Hardened known MCP probes to fail when active server config entries are missing/non-object.
- Changed `normalizeProbeStatus()` to treat unknown statuses as `FAIL` (no silent PASS fallback).
- Added tests for `runSkillsInstall()` signal and non-zero exit branches.
- Added this handoff artifact to close AC11 evidence completeness.
