# Story 5.3 Canonical Blueprint

Date: 2026-04-21
Story: `5-3-wizard-runs-skills-install-and-verifies`
Scope: canonical implementation contract for post-wizard orchestration, skills install execution, active MCP verification, fixture determinism, and summary/exit behavior.

## Inheritance-only note

- Preserve Story 5.2 prompt, rendering, cancellation, and atomic-write semantics unchanged.
- Preserve Story 5.1 fast paths (`--help`, `--version`) and dependency bootstrap.
- Story 5.3 is additive after successful wizard completion.

## Post-wizard call-order lock

After successful Story 5.2 wizard writes:

1. skills install
2. active MCP verification
3. consolidated summary
4. exit code decision

Stable headings are required and printed in this order.

## Locked helper signatures

Required helper surface in `bin/init` (names can vary only if tests/harness are updated in the same change):

- `runPostWizardSetup(env, options?)`
- `runSkillsInstall(env, options?)`
- `loadActiveMcpServerKeys(mcpConfigPath?)`
- `verifyActiveMcps(env, options?)`
- `summarizePostWizard(skillsResult, mcpResults)`
- `loadStory53FixtureIfPresent(env)`
- `validateStory53FixturePayload(payload)`

All helpers return deterministic structured objects; no thrown surprises for expected failure paths.

## Skills install lock

Command contract:

- invoke exactly once: `npx skills add vixxo-copilot/agent-skills`
- use Node child-process execution with inherited stdio
- preserve stdout/stderr passthrough for user visibility

Failure classes:

- spawn error (`ENOENT` etc.)
- signal interruption
- non-zero status

Result contract:

- `status`: `PASS` or `FAIL`
- `reason`: stable text
- `remediation`: must include exact rerun command

## Active MCP verification lock

Configuration source:

- `.cursor/mcp.json` only
- parse `mcpServers` keys in JSON order

Failure handling:

- malformed JSON or missing/non-object `mcpServers` -> deterministic verification failure with guidance to inspect `.cursor/mcp.json`

Per-server probe lock:

- probe each active key once
- bounded timeout for command-based checks
- deterministic result object per key:
  - `server_key`
  - `status`
  - `reason`
  - `remediation`

Placeholder behavior:

- no probes for `.cursor/mcp.placeholders.md` entries

## Remediation map lock

- `linear` -> reconnect in MCP UI + `https://linear.app/docs/mcp`
- `github` -> export `GITHUB_PERSONAL_ACCESS_TOKEN`, ensure Docker running, GitHub install guide URL
- `microsoft-365` -> rerun device-code auth + `https://github.com/softeria/ms-365-mcp-server`
- `salesforce` -> `sf org login web` + install/verify `@salesforce/cli`
- `gong` -> export `GONG_ACCESS_KEY` + `GONG_ACCESS_KEY_SECRET` + `https://github.com/kenazk/gong-mcp`
- unknown key -> `docs/mcps.md` and `.cursor/mcp.README.md`

## Summary and exit contract lock

Summary must include:

- skills install status
- MCP PASS count and FAIL count
- bullet list of failing MCP keys with remediation hints

Exit code:

- `0` only if skills install PASS and all MCP results PASS
- non-zero otherwise

## Deterministic fixture mode lock (Story 5.3)

Env flag:

- `BMAD_STORY_5_3_FIXTURE_PATH` (independent of Story 5.2 fixture flag)

Schema:

```json
{
  "skillsInstall": { "status": "PASS | FAIL", "reason": "optional" },
  "mcpResults": {
    "<server_key>": { "status": "PASS | FAIL", "reason": "optional" }
  }
}
```

Rules:

- fixture mode disabled by default
- payload validated before execution; invalid fixture fails fast
- fixture supports deterministic simulation of skills PASS/FAIL and per-MCP PASS/FAIL
- fixture never prints secret values

## Validation harness blueprint

Create:

- `_bmad-output/implementation-artifacts/tests/story-5-3-wizard-runs-skills-install-and-verifies-validation.sh`

Required gates:

- artifact integrity (`task1`, `task2`)
- skills command wiring and failure semantics
- MCP parse/probe/result formatting
- summary/exit-code contract
- Story 5.3 fixture-mode determinism
- Story 5.2 harness compatibility supersession
- Story 5.1 fast-path compatibility
- predecessor regression sweep with `BMAD_REGRESSION_DEPTH=1`

Dispatcher:

- support `task1..taskN` and `all`
- output convention `PASS: <task>`

## Evidence lock

Required evidence artifacts:

- `_bmad-output/implementation-artifacts/tests/story-5-3-baseline-audit.md`
- `_bmad-output/implementation-artifacts/tests/story-5-3-canonical-blueprint.md`
- `_bmad-output/implementation-artifacts/tests/story-5-3-task-handoff.md`

Handoff must include AC-to-evidence map, command transcripts, and checksums.
