# Story 5.3 Baseline Audit

Date: 2026-04-21
Story: `5-3-wizard-runs-skills-install-and-verifies`
Scope: establish pre-change fingerprints and lock deterministic contracts for post-wizard skills install + active MCP verification.

## Baseline targets reviewed

- `bin/init`
- `test/bin-init.story-5-2.test.js`
- `.cursor/mcp.json`
- `.cursor/mcp.README.md`
- `docs/mcps.md`
- `docs/setup.md`
- `_bmad-output/implementation-artifacts/tests/story-5-2-wizard-prompts-and-file-generation-validation.sh`

## Pre-change SHA-256 fingerprints

- `bin/init` - `32dab11636f8dd470352e6cf35268e39dbe7d3cb3776364920f6b07ca3edc4fc`
- `test/bin-init.story-5-2.test.js` - `7303492de8de85b385f7e88af592924b497a54b361e62badddbb5536ed57e583`
- `.cursor/mcp.json` - `d749b788efa974330d104875a5b63793253a40b450f70341da971a403ac3477c`
- `.cursor/mcp.README.md` - `4f27217a93f71b5bc45b0e4055a4ab82b1d052b2f346277b2dd945d89150af09`
- `docs/mcps.md` - `7b2a16f84fa1b087a0efcc08e72508ce834ef6820317e03485066de3d92668d6`
- `docs/setup.md` - `ddce66f02d496e6d5fcd9ed8c53bbca633b9f10772ee2e956b7cb3124ec27276`

## Active MCP matrix from `.cursor/mcp.json`

JSON key order under `mcpServers` is the verification order lock:

1. `linear`
2. `github`
3. `microsoft-365`
4. `salesforce`
5. `gong`

This scope excludes placeholder-only entries documented in `.cursor/mcp.placeholders.md`.

## Probe strategy lock (deterministic and timeout bounded)

- Parse `.cursor/mcp.json` exactly once at verification planning time.
- Fail fast with actionable guidance if JSON is malformed or if `mcpServers` is missing/non-object.
- Probe each active key exactly once with a deterministic adapter and bounded command checks.
- Result contract for every probe:
  - `server_key`
  - `status` (`PASS` or `FAIL`)
  - `reason` (stable diagnostic, no secret values)
  - `remediation` (exact command or canonical docs link)

## Remediation catalog lock

- `linear`: reconnect via Cursor MCP UI and review `https://linear.app/docs/mcp`
- `github`: export `GITHUB_PERSONAL_ACCESS_TOKEN`, ensure Docker is running, review `https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-cursor.md`
- `microsoft-365`: rerun device-code auth flow, review `https://github.com/softeria/ms-365-mcp-server`
- `salesforce`: run `sf org login web`, ensure `@salesforce/cli` is installed
- `gong`: export `GONG_ACCESS_KEY` and `GONG_ACCESS_KEY_SECRET`, review `https://github.com/kenazk/gong-mcp`
- unknown key fallback: `docs/mcps.md` and `.cursor/mcp.README.md`

## Deterministic Story 5.3 fixture payload schema

Fixture env flag (new, Story 5.3 specific):

- `BMAD_STORY_5_3_FIXTURE_PATH`

Payload shape lock:

```json
{
  "skillsInstall": {
    "status": "PASS | FAIL",
    "reason": "optional stable string"
  },
  "mcpResults": {
    "linear": { "status": "PASS | FAIL", "reason": "optional stable string" },
    "github": { "status": "PASS | FAIL", "reason": "optional stable string" }
  }
}
```

Validation rules:

- top-level must be object
- `skillsInstall` required object with `status`
- `mcpResults` required object map of server key to result object
- each result object requires `status` in `{PASS, FAIL}`
- optional `reason` must be non-empty string when provided
- fixture mode is opt-in only; default user path runs real checks

## Story 5.2 supersession map (harness updates required)

Superseded assertion in Story 5.2 harness:

- prior `task7` rejected any Story 5.3 wiring in `bin/init` by grepping for `npx skills add...` and verification text

Compatibility replacement required after Story 5.3:

- Story 5.2 harness should validate Story 5.2 behavior still works even when post-wizard Story 5.3 phase exists
- Story 5.3 harness becomes source of truth for:
  - skills install command wiring
  - active MCP verification result formatting
  - fixture-driven deterministic pass/fail paths

## Story 5.1 compatibility anchors

`--help` and `--version` must remain fast paths and bypass:

- prompt flow
- skills install
- MCP verification

Dependency bootstrap (`ensureDependencies`) remains unchanged.

## Source references

- `bin/init`
- `.cursor/mcp.json`
- `.cursor/mcp.README.md`
- `docs/mcps.md`
- `docs/setup.md`
