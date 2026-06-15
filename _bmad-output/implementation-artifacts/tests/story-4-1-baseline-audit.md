# Story 4.1 Baseline Audit

Captured 2026-04-21 as the Task 1 evidence artifact for Story 4.1. This audit precedes the canonical blueprint (Task 2), the `.cursor/mcp.json` + `.cursor/mcp.README.md` authoring (Tasks 3 + 4), and the deterministic validation harness (Task 5).

## Current state

- `.cursor/` exists with two subdirectories only:
  - `.cursor/rules/` — 5 `.mdc` rule files + `.gitkeep` (Stories 1.1 / 2.1 / 2.2).
  - `.cursor/skills/` — pre-existing skill library.
- `.cursor/mcp.json` does NOT exist yet (this story creates it).
- `.cursor/mcp.README.md` does NOT exist yet (this story creates it).
- `.gitignore` content is Story 1.1 + F1 patch canonical: `node_modules/`, `.env`, `.env.*`, `!.env.example`, `*.log`, `tmp/` — six lines, trailing newline. `shasum -a 256 .gitignore` = `49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1`. Neither `.cursor/mcp.json` nor `.cursor/mcp.README.md` matches any ignore pattern; Story 4.1 makes ZERO edits to `.gitignore`.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` has `4-1-…status: ready-for-dev` (Phase-1 SM pass already flipped it from `backlog`) and `epic-4.status: in-progress`. Task 7 flips story status `ready-for-dev → review` only.

## Cursor mcp.json 2026 schema

Cursor's project-local MCP configuration lives at `.cursor/mcp.json` relative to the repository root (distinct from the user-global `~/.cursor/mcp.json`). The file is strict JSON (per Apigene 2026 guide + TrueFoundry 2026 guide): no `//` or `/* … */` comments, no trailing commas, no JSON5 / JSONC extensions. Violations cause Cursor to silently reject the whole file — every MCP in it becomes unavailable, not just the offending entry.

The accepted shape:

- Root: single JSON object with exactly one top-level key `mcpServers` mapping to a JSON object (the "servers dict").
- Per-server value: a JSON object using ONE of two transport shapes:
  - **stdio local** — `command: string`, `args: array-of-string`, optional `env: object-of-string-to-string`.
  - **remote HTTP/SSE** — `url: string`, optional `headers: object-of-string-to-string`.
- Unknown keys are ignored by the parser but are banned here via explicit allowlist — drift would otherwise enter silently.
- Cursor's 2026 parser does NOT perform `${VAR}` or `$VAR` shell-expansion inside `env` blocks (confirmed by Cursor forum thread 79296 + 79639; re-confirmed by the Claude Code bug-report #9427 matching the same 2026 behaviour). A file that declares `"env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"}` passes the literal string `${GITHUB_PERSONAL_ACCESS_TOKEN}` to the spawned process — authentication fails with a PAT-shaped error that actually begins with `$`.
- Settings UI renders servers in file order (not alphabetical), so canonical ordering in the source file is meaningful for humans and must be locked.
- Indentation: 2-space. Line endings: LF. Trailing newline required.

Validation uses BOTH `python3 -m json.tool` and `node -e "JSON.parse(…)"` — these catch slightly different edge cases (Python stricter on Unicode escapes; Node stricter on lone surrogate pairs). Both must pass.

## Per-server canonical config

Five active Vixxo work MCPs, canonical order: **Linear → GitHub → Microsoft 365 → Salesforce → Gong**.

### Linear (remote URL)

```json
"linear": { "url": "https://mcp.linear.app/mcp" }
```

- Transport: remote URL (HTTP).
- Auth: OAuth 2.1 interactive via Cursor's MCP UI. No env vars needed; no `Authorization: Bearer …` header in the JSON file (header-form would require `${LINEAR_API_KEY}` expansion, which Cursor does not perform).
- Source: `https://linear.app/docs/mcp`; launch announcement `https://linear.app/changelog/2025-05-01-mcp`.
- Alternative considered and rejected: remote URL + `Authorization: Bearer ${LINEAR_API_KEY}` header. Rejected because `${}` is not expanded and a literal PAT would land in git.

### GitHub (local Docker stdio)

```json
"github": {
  "command": "docker",
  "args": [
    "run",
    "-i",
    "--rm",
    "-e",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ghcr.io/github/github-mcp-server"
  ]
}
```

- Transport: local stdio (docker).
- Auth: Docker `-e GITHUB_PERSONAL_ACCESS_TOKEN` bare-name form. Docker reads the variable from its own environment (inherited from Cursor, inherited from shell). No `env` block in the JSON; no secret in the file.
- Source: `https://github.com/github/github-mcp-server` plus the install guide `https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-cursor.md`.
- Alternative considered and rejected: remote URL `https://api.githubcopilot.com/mcp/` with `Authorization: Bearer …` header. Rejected for the same `${VAR}` non-expansion reason.
- Deprecated legacy package `@modelcontextprotocol/server-github` (archived April 2025) is NOT used.

### Microsoft 365 (local npx stdio)

```json
"microsoft-365": {
  "command": "npx",
  "args": ["-y", "@softeria/ms-365-mcp-server@latest"]
}
```

- Transport: local stdio (npx).
- Auth: device-code flow on first run; token cached in the OS keychain. Optional env vars `MS365_MCP_CLIENT_ID` / `MS365_MCP_TENANT_ID` for multi-tenant scenarios — NOT declared in the JSON (shell-exported by the user if needed).
- Source: npm `https://www.npmjs.com/package/%40softeria%2Fms-365-mcp-server`; repo `https://github.com/softeria/ms-365-mcp-server`.
- Alternative considered and rejected: `@pnp/cli-microsoft365-mcp-server` — rejected because it wraps the `m365` CLI (adds an extra prereq) whereas Softeria wraps Graph directly.

### Salesforce (local npx stdio)

```json
"salesforce": {
  "command": "npx",
  "args": [
    "-y",
    "@salesforce/mcp@latest",
    "--orgs",
    "DEFAULT_TARGET_ORG",
    "--toolsets",
    "orgs,metadata,data,users"
  ]
}
```

- Transport: local stdio (npx).
- Auth: Salesforce CLI (`sf`) session file in `~/.sf/`. User runs `sf org login web` out of band. No env vars in the JSON.
- Source: npm `https://www.npmjs.com/package/%40salesforce/mcp`; repo `https://github.com/salesforcecli/mcp`.
- Prereq: `@salesforce/cli` installed and authenticated. Epic 5 wizard may install the CLI automatically in a later story.

### Gong (local npx stdio — interim, with known fallback)

```json
"gong": {
  "command": "npx",
  "args": ["-y", "@kenazk/gong-mcp@latest"]
}
```

- Transport: local stdio (npx).
- Auth: `GONG_ACCESS_KEY` + `GONG_ACCESS_KEY_SECRET` env vars inherited from shell.
- Sources: `https://help.gong.io/docs/gong-mcp-server` (official server "coming soon"); interim `https://github.com/kenazk/gong-mcp`; announcement `https://www.gong.io/press/gong-introduces-model-context-protocol-mcp-support-to-unify-enterprise-ai-agents-from-hubspot-microsoft-salesforce-and-others`.
- **Known issue (Task 1 finding, 2026-04-21):** `@kenazk/gong-mcp` is NOT currently published on npm. The repo's `package.json` `name` is the unscoped string `"gong-mcp"` and the npm registry has no matching published artifact. A different package `gong-mcp-server-minimal` exists but is not the kenazk project. Consequently `npx -y @kenazk/gong-mcp@latest` will fail at fetch time with `npm error 404 Not Found` on clean hosts.
- **Fallback install path (documented in `.cursor/mcp.README.md`):** users clone the repo and either (a) `node build/index.js` after `npm install && npm run build`, or (b) `docker build -t gong-mcp .` followed by a `docker run` invocation — per the upstream README. An alternative Dev-convenience path is `npx -y github:kenazk/gong-mcp`, which `npx` resolves directly from GitHub; this bypasses the missing-npm-artifact problem without editing `.cursor/mcp.json`.
- **Dev Note (forward-looking):** the canonical Task 2 blueprint keeps `npx -y @kenazk/gong-mcp@latest` as the literal value in `.cursor/mcp.json` so the JSON remains a stable lock-point. When Gong publishes its official MCP server (or when `kenazk` publishes the package to npm), a follow-up commit flips the `args` element to the working reference. The key name `gong` stays stable.

## Env-var handling decision (no env blocks; shell inheritance + Docker -e NAME form)

`.cursor/mcp.json` contains ZERO `env` blocks. Rationale: the 2026 Cursor parser does not perform `${VAR}` expansion inside `env` blocks (confirmed by the Cursor forum threads linked above). Three allowed patterns for env-var delivery:

1. **Shell inheritance** — any env var exported in `~/.zshrc` / `~/.bashrc` flows through the shell → Cursor → spawned MCP subprocess. Used by Gong (`GONG_ACCESS_KEY`, `GONG_ACCESS_KEY_SECRET`) and optionally Microsoft 365 (`MS365_MCP_CLIENT_ID`, `MS365_MCP_TENANT_ID`).
2. **Docker `-e NAME` bare-form** — `docker run … -e GITHUB_PERSONAL_ACCESS_TOKEN …` tells Docker to read the variable from its own inherited env. The JSON holds only the flag and the name — no secret, no expansion token. Used by GitHub.
3. **Interactive auth / external CLI session** — Linear uses OAuth 2.1 via Cursor's MCP UI; Salesforce uses the `sf` CLI session in `~/.sf/`; Microsoft 365 uses device-code flow with keychain-cached tokens. No env vars required in the JSON.

macOS caveat: Cursor launched from Finder may inherit `launchctl`'s env rather than the shell's, so exported vars may be invisible. Workaround: launch Cursor from a terminal that inherited the vars, or use `launchctl setenv`. Documented in the README.

## Banned-term regex — underscore-aware boundary (Dev decision)

The 17-token regex inherited from Stories 3.1 / 3.2 / 3.3 is `(^|[^A-Za-z])(…|personal|…)($|[^A-Za-z])` — boundary on `[^A-Za-z]`. Story 4.1 files necessarily reference the GitHub MCP env var name `GITHUB_PERSONAL_ACCESS_TOKEN`, in which the underscore-delimited token `PERSONAL` sits between two underscores. The Story-3.x boundary class `[^A-Za-z]` admits underscore on both sides, so the regex matches the env var name. That match is semantically unrelated to the "personal life / personal AI agent" human-word context the 17-token lock is intended to catch.

Dev decision (2026-04-21): in the Story 4.1 harness, the banned-term regex boundary is tightened to `[^A-Za-z_]` — underscore is treated as a word character. This matches POSIX `\b` semantics, remains POSIX-ERE (no Perl `\b`, no `\<` / `\>`), and continues to admit legitimate positive hits (`personal note` still matches) and continues to reject boundary-adjacent tokens (`personally` still rejects). The semantic catch-surface is preserved; the env var reference is safely excluded.

This is additive to the Story 3.x convention — `memory/me/*.md` files have no underscore-delimited identifier contexts, so Story 3.3's harness never exercised the underscore case. Stories 3.x harnesses are untouched. Story 4.1 harness alone uses the tightened boundary.

Updated regex used by the Story 4.1 harness:

```
(^|[^A-Za-z_])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z_])
```

## Secret-pattern regex set (eleven patterns)

The harness runs these against `.cursor/mcp.json` AND `.cursor/mcp.README.md`; each must return zero matches:

1. `sk-[A-Za-z0-9_-]{20,}` — OpenAI-style keys.
2. `ghp_[A-Za-z0-9]{20,}` — GitHub classic PAT prefix.
3. `gho_[A-Za-z0-9]{20,}` — GitHub OAuth token prefix.
4. `ghs_[A-Za-z0-9]{20,}` — GitHub server token prefix.
5. `github_pat_[A-Za-z0-9_]{20,}` — GitHub fine-grained PAT prefix.
6. `xox[baprs]-[A-Za-z0-9-]{10,}` — Slack token prefix family.
7. `eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}` — JWT.
8. `Bearer [A-Za-z0-9_.-]{20,}` — inline bearer header.
9. `AKIA[0-9A-Z]{16}` — AWS access-key ID.
10. `AIza[A-Za-z0-9_-]{35}` — Google API key prefix.
11. `[A-Fa-f0-9]{32,}` — any long hex run (intentionally broad).

Additionally: zero `${VAR}` / `$VAR` substrings; zero `password=` / `token=` / `secret=` / `api_key=` literal substrings; zero `env` keys under any `mcpServers` entry.

## Gitignore invariance

`.gitignore` pre-Story-4.1 content (6 lines):

```
node_modules/
.env
.env.*
!.env.example
*.log
tmp/
```

- SHA-256: `49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1`.
- Byte count: 51 (matches Story 3.3 AC12 fingerprint).
- `git check-ignore -v .cursor/mcp.json` and `git check-ignore -v .cursor/mcp.README.md` both exit non-zero (files NOT ignored). Confirmed via dry-run prior to file creation (git-ignore-check follows the active tree's `.gitignore` patterns regardless of file existence on disk).
- Story 4.1 makes ZERO edits to `.gitignore`.

## Predecessor-harness compatibility scan

Purpose: confirm Story 4.1 can add `.cursor/mcp.json` + `.cursor/mcp.README.md` without any predecessor harness needing an allowlist extension.

Method: read each of the ten predecessor harnesses (`story-1-1-*` through `story-3-3-*`) and grep for `.cursor/` references. Evaluate whether any harness has a content deny-list for `.cursor/` that would reject new non-rule files.

Findings:

- `story-1-1-scaffold-validation.sh` — iterates `.cursor/rules` only (line 146–170). Does NOT scan `.cursor/` at the root. Allowlisting any new `.cursor/` top-level file is **not required**. Zero harness edit.
- `story-1-2-root-files-validation.sh` — inspects `README.md`, `LICENSE`, `.gitignore` only. No `.cursor/` content scan. Zero harness edit.
- `story-1-3-root-context-validation.sh` — inspects `AGENTS.md`, `CLAUDE.md`, `.cursorrules`. No `.cursor/` content scan. Zero harness edit.
- `story-2-1-agent-identity-validation.sh` — inspects `.cursor/rules/agent-identity.mdc` only. Path-specific. Zero harness edit.
- `story-2-2-guardrail-and-formatting-validation.sh` — inspects four specific `.cursor/rules/*.mdc` files. Path-specific. Zero harness edit.
- `story-2-3-work-persona-validation.sh` — inspects `agents/personas/work.md`. No `.cursor/` content scan. Zero harness edit.
- `story-2-4-benji-inbox-absence-validation.sh` — asserts `.cursor/rules/benji-inbox-default.mdc` is ABSENT (deny-list for one specific path). Does not deny other `.cursor/` files. Zero harness edit.
- `story-3-1-memory-template-tree-validation.sh` — inspects `memory/` tree. No `.cursor/` content scan. Zero harness edit.
- `story-3-2-obsidian-config-validation.sh` — inspects `memory/.obsidian/`. No `.cursor/` scan. Zero harness edit.
- `story-3-3-identity-preferences-validation.sh` — inspects `memory/me/`, references `.cursor/rules/*.mdc` as AC12 byte-stable fingerprints. No `.cursor/` content scan that would object to new files. Zero harness edit.

**Result: zero predecessor harness needs an allowlist extension.** AC10 zero-edit invariance holds for all ten predecessor harnesses.

`shasum -a 256 _bmad-output/implementation-artifacts/tests/story-1-1-scaffold-validation.sh` = `a609f6a857235a57588bab081c2775c3d59c9282ae0d1256f4183b5e923617b8` (matches the Story 3.3 harness's `STORY_1_1_HARNESS_SHA256` constant).

### Predecessor harness PASS-count fingerprint (empirical, 2026-04-21)

| Harness | `^PASS:` lines in `all` mode |
|---------|-----------------------------|
| story-1-1-scaffold-validation.sh | 1 |
| story-1-2-root-files-validation.sh | 1 |
| story-1-3-root-context-validation.sh | 1 |
| story-2-1-agent-identity-validation.sh | 1 |
| story-2-2-guardrail-and-formatting-validation.sh | 10 |
| story-2-3-work-persona-validation.sh | 7 |
| story-2-4-benji-inbox-absence-validation.sh | 7 |
| story-3-1-memory-template-tree-validation.sh | 7 |
| story-3-2-obsidian-config-validation.sh | 7 |
| story-3-3-identity-preferences-validation.sh | 7 |

Vector: `( 1 1 1 1 10 7 7 7 7 7 )` — exactly matches the story's `EXPECTED_PASS_COUNTS` default. Populated into the Task 5 harness `EXPECTED_PASS_COUNTS` constant.

## Source URLs

- Cursor docs / guides
  - `https://www.apigene.ai/blog/how-to-use-mcp-in-cursor-2026-guide` — 2026 schema, strict-JSON, `mcpServers` key.
  - `https://www.truefoundry.com/blog/mcp-servers-in-cursor-setup-configuration-and-security-guide` — 2026 schema + security.
  - `https://www.nxcode.io/resources/news/cursor-mcp-servers-complete-guide-2026` — project-local `.cursor/mcp.json` vs global.
  - `https://cursor.com/docs/cli/mcp` — CLI MCP config.
  - `https://forum.cursor.com/t/how-to-use-environment-variables-in-mcp-json/79296` — `${VAR}` not expanded; wrapper-script workarounds.
  - `https://forum.cursor.com/t/resolve-local-environment-variables-in-mcp-server-definitions/79639` — re-confirmation; feature request.
  - `https://forum.cursor.com/t/cursor-agent-mcp-list-silently-drops-entire-mcp-json-when-any-entry-has-type-streamable-http-works-in-ide/158521` — strict-JSON silent-reject behaviour.
- Linear
  - `https://linear.app/docs/mcp`
  - `https://linear.app/changelog/2025-05-01-mcp`
- GitHub
  - `https://github.com/github/github-mcp-server`
  - `https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-cursor.md`
- Microsoft 365
  - `https://www.npmjs.com/package/%40softeria%2Fms-365-mcp-server`
  - `https://github.com/softeria/ms-365-mcp-server`
- Salesforce
  - `https://www.npmjs.com/package/%40salesforce/mcp`
  - `https://github.com/salesforcecli/mcp`
- Gong
  - `https://help.gong.io/docs/gong-mcp-server`
  - `https://github.com/kenazk/gong-mcp`
  - `https://www.pulsemcp.com/servers/kenazk-gong`
  - `https://www.gong.io/press/gong-introduces-model-context-protocol-mcp-support-to-unify-enterprise-ai-agents-from-hubspot-microsoft-salesforce-and-others`
- Claude Code bug (cross-reference for `${VAR}` non-expansion behaviour in MCP config)
  - `https://github.com/anthropics/claude-code/issues/9427`

<!-- Why: Task 1 evidence artifact. Captures schema research, per-server canonical-config sources, env-var decision, predecessor-harness zero-edit verification, and the empirical PASS-count vector that Task 5 feeds into EXPECTED_PASS_COUNTS. -->
