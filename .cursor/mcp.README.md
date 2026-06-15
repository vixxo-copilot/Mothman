---
type: mcp-readme
scope: work
created: 2026-04-21
updated: 2026-04-21
tags: [mcp, work]
---

# Active MCPs (.cursor/mcp.json)

This file documents the five active Vixxo work MCPs wired in `.cursor/mcp.json`: Linear, GitHub, Microsoft 365, Salesforce, and Gong. Strict JSON forbids inline comments, so per-server documentation lives here instead. Placeholder / pending MCPs are NOT listed in `.cursor/mcp.json` — they live in a separate Story 4.2 companion `.cursor/mcp.placeholders.md` (see Forward References).

## Linear

**Purpose:** Vixxo work task and project management (issues, projects, cycles).

**Transport:** remote URL (HTTP).

**Auth:** OAuth 2.1 interactive via Cursor's MCP UI on first connect.

**Required env vars:**

- None — interactive OAuth. Cursor opens the Linear login flow the first time the MCP is invoked.

**Wiring link:** TODO: Vixxo internal wiki — Linear MCP onboarding. Upstream docs at `https://linear.app/docs/mcp`.

## GitHub

**Purpose:** Source control, code review, repository documentation, PR automation.

**Transport:** local stdio — project wrapper `bin/run-github-mcp.sh` runs the official `github-mcp-server` binary from `bin/github-mcp-server`.

**Auth:** Uses `GITHUB_PERSONAL_ACCESS_TOKEN` when exported, otherwise falls back to `gh auth token` (requires `gh auth login`). No Docker required.

**Setup (one-time):**

1. `gh auth login` if not already authenticated.
2. Download the binary (Darwin arm64 example):
   `curl -fsSL -o bin/github-mcp-server.tar.gz https://github.com/github/github-mcp-server/releases/download/v1.1.2/github-mcp-server_Darwin_arm64.tar.gz && tar -xzf bin/github-mcp-server.tar.gz -C bin && chmod +x bin/github-mcp-server && rm bin/github-mcp-server.tar.gz`
3. Restart the GitHub MCP in Cursor (Settings → MCP → github).

**Optional env var:** `GITHUB_PERSONAL_ACCESS_TOKEN` — overrides `gh auth token` when set.

**Wiring link:** `https://github.com/github/github-mcp-server` (install guide at `https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-cursor.md`).

**Alternatives:** Remote HTTP at `https://api.githubcopilot.com/mcp/` with `"type": "http"` and a real PAT in the `Authorization` header; or Docker `ghcr.io/github/github-mcp-server` if Docker Desktop is installed.

## Microsoft 365

**Purpose:** Outlook email and calendar, OneDrive files, Teams chat, Microsoft Graph API coverage.

**Transport:** local stdio (npx).

**Auth:** Device-code flow on first run. The MCP prints a device code and URL; the user completes auth in a browser. Token is cached in the OS keychain after the first successful login.

**Required env vars:**

- None required in the common case. Optional: `MS365_MCP_CLIENT_ID` and `MS365_MCP_TENANT_ID` for multi-tenant scenarios or restricted app registrations — export these in your shell rc file if needed; do NOT add them to the JSON.

**Wiring link:** `https://github.com/softeria/ms-365-mcp-server` (npm package `@softeria/ms-365-mcp-server`).

Note on Vixxo tenant conditional-access: if the Vixxo tenant blocks device-code flow by policy, the MCP cannot complete first-run auth. This is a tenant-configuration matter, not an MCP bug. Follow up with the Vixxo IT / identity team and reference the upstream issue tracker at `https://github.com/softeria/ms-365-mcp-server/issues`.

## Salesforce

**Purpose:** CRM, pipeline, accounts, contacts, Apex execution, SOQL queries.

**Transport:** local stdio (npx).

**Auth:** Salesforce CLI (`sf`) session stored under the user's account directory at `~/.sf/`. Run `sf org login web` once out of band before invoking the MCP; the CLI writes its session file and the MCP reuses it.

**Required env vars:**

- None required — the `sf` CLI session file provides auth. The `--orgs DEFAULT_TARGET_ORG` arg in the JSON tells the MCP to target whichever org the CLI has set as default.

**Wiring link:** `https://github.com/salesforcecli/mcp` (npm package `@salesforce/mcp`).

Prerequisite: `@salesforce/cli` installed globally (`npm install -g @salesforce/cli`) or via the macOS installer. Epic 5 Story 5.3 may install the CLI automatically in a later iteration; for now, install manually.

## Gong

**Purpose:** Call recordings, transcripts, deal intelligence.

**Transport:** local stdio (npx).

**Auth:** Environment variables inherited from shell.

**Required env vars:**

- `GONG_ACCESS_KEY` — Gong API access key; export in your shell rc file before launching Cursor.
- `GONG_ACCESS_KEY_SECRET` — Gong API secret paired with the access key; export in your shell rc file before launching Cursor.

**Wiring link:** `https://github.com/kenazk/gong-mcp` (community interim package until Gong ships its official MCP server per `https://help.gong.io/docs/gong-mcp-server`, targeted April 2026).

**Package reference (2026-04-21):** `.cursor/mcp.json` pins the Gong server to `github:kenazk/gong-mcp` because `@kenazk/gong-mcp` is NOT currently published on the npm registry (the repo's `package.json` `name` is the unscoped `gong-mcp` and no matching artifact exists on npm — registry `GET` returns 404). `github:kenazk/gong-mcp` installs from the public GitHub repo; requires the upstream `package.json` build step to succeed on install; when Gong ships its official MCP server this pin will flip. Alternate install paths if the git-install fails in a locked-down environment:

- Clone + build: `git clone https://github.com/kenazk/gong-mcp && cd gong-mcp && npm install && npm run build && node build/index.js`.
- Docker: `git clone https://github.com/kenazk/gong-mcp && cd gong-mcp && docker build -t gong-mcp . && docker run --rm -i -e GONG_ACCESS_KEY -e GONG_ACCESS_KEY_SECRET gong-mcp`.

A follow-up ticket will swap the JSON `args` element to the official package reference once available.

## Env Variable Handling Convention

Cursor's 2026 `.cursor/mcp.json` parser does NOT expand `${VAR}` or `$VAR` tokens inside `env` blocks (confirmed by Cursor forum threads 79296 and 79639). A file that declares `"env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"}` passes the literal 31-character string `${GITHUB_PERSONAL_ACCESS_TOKEN}` to the spawned process — not the expanded secret. The process then fails with a token-shape error that actually begins with a dollar sign.

Consequence: `.cursor/mcp.json` contains ZERO `env` blocks. The harness asserts this invariant at every validation pass.

Three env-delivery patterns are allowed; any future MCP added to `.cursor/mcp.json` MUST use one of them:

1. **Shell inheritance.** Export the variable in your shell rc file (`~/.zshrc`, `~/.bashrc`, `~/.profile`, etc.). Values flow: shell → Cursor → spawned MCP subprocess. Used by Gong (`GONG_ACCESS_KEY`, `GONG_ACCESS_KEY_SECRET`) and optionally Microsoft 365 (`MS365_MCP_CLIENT_ID`, `MS365_MCP_TENANT_ID`).
2. **Docker `-e NAME` bare-form.** When the spawn command is `docker run … -e GITHUB_PERSONAL_ACCESS_TOKEN … image`, the bare-name `-e` flag (with NO `=value`) instructs Docker to read the variable from its own inherited environment. The JSON file holds the flag and the variable name only — no secret, no expansion token. Used by GitHub.
3. **Interactive auth / external CLI session.** Linear uses OAuth 2.1 via Cursor's MCP UI. Salesforce uses the `sf` CLI session file under `~/.sf/`. Microsoft 365 uses device-code flow with keychain-cached tokens. None of these require env vars in the JSON.

macOS caveat: when Cursor is launched from Finder (double-click), it inherits the `launchctl` environment rather than the shell's; shell-exported vars may be invisible. Workarounds: launch Cursor from a terminal (`cursor .`) so the shell env propagates, or register the vars with `launchctl setenv NAME value`. See the Cursor community thread at `https://forum.cursor.com/t/how-to-use-environment-variables-in-mcp-json/79296`.

## Skill-based tools (not MCP)

These integrations use agent skills and `.env` credentials. They do **not** appear
in `.cursor/mcp.json` and are not invoked through Cursor's MCP UI.

### PolyAI

**Purpose:** Outbound voice-agent operations — Conversations API health, list/get,
conversation audit, Jupiter/Studio config, integration metrics (`VALID_SR`,
`API_OK`).

**Transport:** local Python scripts + HTTPS API (`api.{region}-1.platform.polyai.app`).

**Auth:** `POLYAI_API_KEY` in `.env` (shell inheritance).

**Required env vars:**

- `POLYAI_API_KEY` — Conversations API key from PolyAI.
- `POLYAI_REGION` — e.g. `us`.
- `POLYAI_ACCOUNT_ID` — e.g. `vixxo-us`.
- `POLYAI_PROJECT_ID` — e.g. `vixxo-outbound-usp`.

**Skills:**

| Skill | Purpose |
| --- | --- |
| `polyai` | API, audit, config, metrics |
| `polyai-vixxo-bridge` | VixxoLink MCP tool pack in Agent Studio |
| `polyai-conversation-audit` | Alias → `polyai` |

**Wiring link:** `.agents/skills/polyai/SKILL.md`

**Health check:**

```bash
python3 .agents/skills/polyai/scripts/polyai_client.py health
```

## Forward References

- Story 4.2 — will add `.cursor/mcp.placeholders.md` with one H2 section per pending MCP (Freshdesk, Dynamics, VixxoNow, VixxoLink, Gateway, ZoomInfo, HubSpot, AWS Connect, ChatFPT, Elastic, agent-skills Introspection MCP). Each entry will show its canonical active-shape in a fenced `json` code block plus a markdown `// TODO:` note outside the JSON. Placeholders are NOT stored in `.cursor/mcp.json` because strict JSON forbids comments, and a partially-commented JSON file would be rejected wholesale by the parser.
- Story 4.3 — will add `.env.example` at the repo root with per-MCP sections enumerating the env vars documented above (`GITHUB_PERSONAL_ACCESS_TOKEN`, `GONG_ACCESS_KEY`, `GONG_ACCESS_KEY_SECRET`, optional `MS365_MCP_CLIENT_ID` / `MS365_MCP_TENANT_ID`). `.env.example` is allowlisted by the existing `.gitignore` rule `!.env.example`; `.env` remains ignored.
- Story 4.4 — will rewrite `docs/setup.md` and `docs/mcps.md` with self-serve onboarding: clone → `bin/init` → verify. The MCP catalog table in `docs/mcps.md` will cross-link to this README.
- Epic 5 Story 5.3 — the `bin/init` setup wizard will call each active MCP once and report PASS / FAIL per server. `.cursor/mcp.json` is the wizard's configuration source.

<!-- Why: strict JSON forbids comments; this README documents each entry in .cursor/mcp.json per Epic 4 Story 4.1 AC5. -->
