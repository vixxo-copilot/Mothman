---
type: setup-guide
scope: work
created: 2026-04-21
updated: 2026-04-21
tags: [setup, onboarding, work]
---

# assistants-template — setup and onboarding

Welcome. This document is the canonical self-serve onboarding checklist for the `assistants-template` repository. Follow it top to bottom: clone the repo, install the shared skill bundle, copy credentials, confirm your five active MCPs are green, and move on to real work. For the per-MCP reference catalog (sixteen servers: five active, eleven placeholder), see `docs/mcps.md`.

## Prerequisites

Install the following tools before starting. Commands in parentheses print the installed version.

- `git` (`git --version`) — available on your shell path.
- Node.js Active LTS (`node --version`) — required by `npx` and by the Microsoft 365, Salesforce, and Gong MCPs.
- `npx` (`npx --version`) — ships with Node.js; used for the shared skill bundle and for several active MCPs.
- GitHub CLI (`gh`) — required for GitHub MCP auth via `gh auth login`. Optional: export `GITHUB_PERSONAL_ACCESS_TOKEN` to override.
- `@salesforce/cli` (install via `npm install -g @salesforce/cli` or the macOS installer) — required for the Salesforce MCP. Run `sf org login web` once out of band before the first MCP invocation; the CLI writes its session file under your account directory and the MCP reuses it.

macOS caveat: when Cursor is launched from Finder (double-click), it inherits the `launchctl` environment rather than the shell environment, and shell-exported variables may be invisible to spawned MCP subprocesses. Workaround: launch Cursor from a terminal with `cursor .` so your shell environment propagates, or register each variable once with `launchctl setenv NAME value`. See `.cursor/mcp.README.md` § `Env Variable Handling Convention` for the full rationale.

## Clone and install

Clone the repository and change into it:

```bash
git clone YOUR-REPO-URL assistants-template
cd assistants-template
```

Replace `YOUR-REPO-URL` with the repository URL provided by your Vixxo maintainer. The clone target directory can be named anything; `assistants-template` is the convention used throughout this document.

Install the shared `vixxo-copilot/agent-skills` skill bundle (this is the canonical skills registry handle referenced throughout the template):

```bash
npx skills add vixxo-copilot/agent-skills
```

The `npx skills add` command pulls the skills registry into your workstation so Cursor can surface project skills alongside the active MCPs. The registry is re-runnable; future updates replace the local bundle in place.

## Configure credentials (`.env`)

Copy the tracked credential template into a local `.env` file:

```bash
cp .env.example .env
```

The repository's `.gitignore` ignores `.env` (and every `.env.*` variant) while allowlisting `.env.example` via the `!.env.example` rule, so `.env.example` is tracked and `.env` stays out of git. See `.gitignore` for the rule ordering and `.env.example` for the full list of supported variables.

Three required variables (fill these in your new `.env` file — never commit real values to `.env.example`):

- `GITHUB_PERSONAL_ACCESS_TOKEN` — optional override for GitHub MCP; defaults to `gh auth token` when `gh auth login` is complete.
- `GONG_ACCESS_KEY` — Gong API access key used by the Gong MCP; exported in your shell rc file before launching Cursor.
- `GONG_ACCESS_KEY_SECRET` — Gong API secret paired with the access key; exported in your shell rc file before launching Cursor.

Two optional Microsoft 365 variables (only set these if your Vixxo tenant requires a custom app registration):

- `MS365_MCP_CLIENT_ID` — multi-tenant app-registration client id.
- `MS365_MCP_TENANT_ID` — multi-tenant app-registration tenant id.

For the complete per-MCP credential surface — including placeholder-MCP variables marked `(TBD)` — see `docs/mcps.md` § `Credential surface`.

Reminder: `.env` remains gitignored by the existing `.env` and `.env.*` rules in `.gitignore`. Never add real values to `.env.example`; the file is tracked and visible to every clone of the repository.

## Configure active MCPs

The template ships five active MCPs wired in `.cursor/mcp.json`: Linear, GitHub, Microsoft 365, Salesforce, and Gong. Each one uses exactly one of three env-delivery patterns documented in `.cursor/mcp.README.md` § `Env Variable Handling Convention`:

- Shell inheritance — export the variable in your shell rc file; values flow shell to Cursor to the spawned MCP subprocess. Used by Gong (`GONG_ACCESS_KEY`, `GONG_ACCESS_KEY_SECRET`) and optionally Microsoft 365 (`MS365_MCP_CLIENT_ID`, `MS365_MCP_TENANT_ID`). GitHub MCP uses `gh auth token` by default via `bin/run-github-mcp.sh`.
- Interactive OAuth or external CLI session — Linear uses OAuth 2.1 via Cursor's MCP UI; Salesforce uses the `sf` CLI session file under `~/.sf/`; Microsoft 365 uses device-code flow with keychain-cached tokens. No env vars live in the JSON.

For the per-server Purpose, Transport, Auth, Required env vars, and Wiring link metadata, see `.cursor/mcp.README.md`. For the sixteen-row catalog table aligning each active server with its placeholder counterparts, see `docs/mcps.md` § `Active MCPs`.

After exporting any required variables, launch Cursor from a terminal (`cursor .`) and open the MCP UI. All five active servers should report green. Run `gh auth login` once if GitHub MCP is red. Run `sf org login web` once out of band before the first Salesforce MCP invocation if you have not already.

## Review placeholder MCPs

Eleven additional MCPs ship as descriptive placeholders for awareness — they are NOT wired, they contain no secrets, and they are explicitly SKIPPED by the Epic 5 Story 5.3 wizard verification. See `.cursor/mcp.placeholders.md` for the full placeholder surface and `docs/mcps.md` § `Placeholder MCPs` for the cross-linked catalog table entries.

For quick reference the eleven placeholder server keys are, in canonical order:

- `freshdesk`
- `dynamics`
- `vixxonow`
- `vixxolink`
- `gateway`
- `zoominfo`
- `hubspot`
- `aws-connect`
- `chatfpt`
- `elastic`
- `introspection`

Each placeholder entry has a stable shape — Purpose, Status, Intended transport, Wiring reference, fenced JSON wiring draft — so a future story can flip it to active with a small, predictable diff.

## Run the setup smoke test

Once Epic 5 Story 5.1 lands, running `./bin/init` will execute the smoke test end-to-end. The `./bin/init` file does not yet exist; the shell-invocation string is a forward reference to the wizard that Epic 5 will ship.

Manual fallback checklist — run through each step until you reach the first FAIL, then consult the next section:

1. Launch Cursor from a terminal with `cursor .` from the cloned repository root so your shell environment propagates to Cursor and to every spawned MCP subprocess.
2. Open Cursor's MCP UI (via the command palette) and confirm all five active servers — Linear, GitHub, Microsoft 365, Salesforce, Gong — report green.
3. Issue a trivial query against each active MCP to confirm round-trip auth:
   - Linear — list your open issues for the current cycle.
   - GitHub — list the repositories you own.
   - Microsoft 365 — show your next three calendar events.
   - Salesforce — run `SELECT Id, Name FROM Account LIMIT 3`.
   - Gong — list your most recent calls.
4. Any FAIL at step 2 or step 3 means the corresponding active MCP failed to initialize or round-trip. Consult the `## Troubleshooting and next steps` section below.

## Troubleshooting and next steps

Three recurring workstation-setup issues, each inherited verbatim from `.cursor/mcp.README.md`'s macOS caveats:

- Cursor launched from Finder is missing shell environment. Symptom: GitHub or Gong MCPs fail with a missing-variable error even though the variables are exported in your shell rc. Workaround: close Cursor, relaunch it from a terminal with `cursor .`, or register each variable with `launchctl setenv NAME value` so Finder-launched Cursor picks them up too.
- GitHub MCP fails at spawn. Symptom: `connected=false` for github. Workaround: run `gh auth login`, confirm `bin/github-mcp-server` exists (see `.cursor/mcp.README.md` § GitHub), then restart the GitHub MCP in Cursor Settings.
- `sf` CLI session expired. Symptom: the Salesforce MCP returns an auth error on its first query. Workaround: run `sf org login web` once in your terminal; the CLI writes a fresh session file and the MCP reuses it on the next spawn.

For per-MCP troubleshooting (including placeholder-MCP activation notes) see `docs/mcps.md`. For bug reports, file a Linear issue at [https://linear.app/vixxo/project/assistants-template-e4cee6d7ae70](https://linear.app/vixxo/project/assistants-template-e4cee6d7ae70).

Forward-looking context — Epic 5 and Epic 6 stories build directly on this document:

- Epic 5 Story 5.1 — scaffolds the `./bin/init` Node entry point this smoke-test section references.
- Epic 5 Story 5.2 — wires the wizard prompts that copy `.env.example` to `.env` and generate identity files.
- Epic 5 Story 5.3 — runs the skills install plus active-MCP verification defined by the checklist above.
- Epic 6 Story 6.1 — lands the shared deny-list config consumed by future CI guardrails.
- Epic 6 Story 6.2 — wires the GitHub Action that blocks PRs containing deny-list violations.

<!-- Why: canonical self-serve onboarding checklist from clone through smoke-test per Epic 4 Story 4.4 AC1; cross-links .env.example (Story 4.3), .cursor/mcp.README.md (Story 4.1), .cursor/mcp.placeholders.md (Story 4.2), and docs/mcps.md (Story 4.4). -->
