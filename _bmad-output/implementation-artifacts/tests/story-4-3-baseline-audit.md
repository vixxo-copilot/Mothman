# Story 4.3 Baseline Audit

Date: 2026-04-21
Worktree root: repo root (relative paths throughout; absolute paths intentionally omitted to preserve path-reference discipline per AC6/AC9).
Author: Amelia (Dev agent)

## Env-var source-of-truth cross-reference with Story 4.1 mcp.README.md

The Story 4.1 `.cursor/mcp.README.md` locks the Required env vars per active MCP. Story 4.3 inherits these verbatim for the five active sections of `.env.example`.

| MCP key         | `# status:`       | Required env vars (bare `VAR=`)                           | Optional env vars (commented `# VAR=`)                          | Source (mcp.README.md) |
|-----------------|-------------------|-----------------------------------------------------------|-----------------------------------------------------------------|------------------------|
| `linear`        | `active-no-env`   | *(none — interactive OAuth)*                              | *(none)*                                                        | § Linear lines 21–25   |
| `github`        | `active`          | `GITHUB_PERSONAL_ACCESS_TOKEN`                            | *(none)*                                                        | § GitHub lines 35–39   |
| `microsoft-365` | `active`          | *(none required)*                                         | `MS365_MCP_CLIENT_ID`, `MS365_MCP_TENANT_ID`                    | § Microsoft 365 lines 51–55 |
| `salesforce`    | `active-no-env`   | *(none — sf CLI session at `~/.sf/`)*                     | *(none)*                                                        | § Salesforce lines 67–71 |
| `gong`          | `active`          | `GONG_ACCESS_KEY`, `GONG_ACCESS_KEY_SECRET`                | *(none)*                                                        | § Gong lines 83–86     |

Total bare env vars across active sections: three (`GITHUB_PERSONAL_ACCESS_TOKEN`, `GONG_ACCESS_KEY`, `GONG_ACCESS_KEY_SECRET`). Total commented optional env vars across active sections: two (`MS365_MCP_CLIENT_ID`, `MS365_MCP_TENANT_ID`). Matches AC4 exactly.

The three env-delivery patterns locked by `.cursor/mcp.README.md` § `Env Variable Handling Convention`:

1. Shell inheritance (Gong; optional Microsoft 365).
2. Docker `-e NAME` bare-form (GitHub).
3. Interactive OAuth / CLI session (Linear; Salesforce; Microsoft 365 device-code).

The `.env.example` `# Auth:` line per section paraphrases one of these three patterns (or the literal `TBD — placeholder; not yet wired` phrase for placeholder sections).

## Placeholder env-var TBD locks (eleven MCPs)

Illustrative SCREAMING_SNAKE_CASE names picked per the MCP's domain / upstream convention. Empty-RHS commented form (`# VAR=`). Names are NOT load-bearing — the future flip-to-active story will reconcile them against the actual upstream auth flow.

| MCP key         | Commented `# VAR=` tokens                                                                     | Count | Rationale                                                                                               |
|-----------------|-----------------------------------------------------------------------------------------------|-------|---------------------------------------------------------------------------------------------------------|
| `freshdesk`     | `FRESHDESK_API_KEY`, `FRESHDESK_DOMAIN`                                                       | 2     | Freshdesk REST API uses an API key + domain pair per `https://developers.freshdesk.com/api/`.           |
| `dynamics`      | `DYNAMICS_CLIENT_ID`, `DYNAMICS_CLIENT_SECRET`, `DYNAMICS_TENANT_ID`                          | 3     | Azure AD app-registration triple for Dynamics 365 OAuth.                                                |
| `vixxonow`      | `VIXXONOW_API_TOKEN`                                                                          | 1     | Vixxo-internal; speculative `<KEY>_API_TOKEN` form for remote HTTP endpoint.                            |
| `vixxolink`     | `VIXXOLINK_API_TOKEN`                                                                         | 1     | Vixxo-internal; speculative form.                                                                       |
| `gateway`       | `GATEWAY_API_TOKEN`                                                                           | 1     | Vixxo-internal; speculative form.                                                                       |
| `zoominfo`      | `ZOOMINFO_USERNAME`, `ZOOMINFO_PASSWORD`                                                      | 2     | ZoomInfo REST API uses HTTP Basic auth (username + password).                                           |
| `hubspot`       | `HUBSPOT_ACCESS_TOKEN`                                                                        | 1     | HubSpot OAuth yields an access token per `https://developers.hubspot.com/docs/api/overview`.            |
| `aws-connect`   | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_CONNECT_INSTANCE_ID`         | 4     | AWS SDK env convention plus Connect-specific instance identifier.                                       |
| `chatfpt`       | `CHATFPT_API_TOKEN`                                                                           | 1     | Vixxo-internal; speculative form.                                                                       |
| `elastic`       | `ELASTIC_URL`, `ELASTIC_API_KEY`                                                              | 2     | `@elastic/mcp-server-elasticsearch` documented pair.                                                    |
| `introspection` | *(none)*                                                                                      | 0     | Local stdio invocation against companion agent-skills repo; parameterless at env layer.                 |

Total commented tokens across placeholder sections: 18 (2 + 3 + 1 + 1 + 1 + 2 + 1 + 4 + 1 + 2 + 0). Combined with the two under microsoft-365 optional, the full `EXPECTED_COMMENTED_VARS` set size is 20. Matches AC5 exactly.

## .gitignore allowlist re-confirmation (.env.example tracked, .env ignored)

Line 4 of `.gitignore` reads `!.env.example` verbatim (with leading `!`). This is the Story 1.1 + F1 patch result and is byte-stable.

Empirical results (run from repo root):

- `git check-ignore -v .env.example` → exit `0`, output `.gitignore:4:!.env.example\t.env.example`.
- `git check-ignore .env.example` → exit `1`, empty output.
- `git check-ignore -v .env` → exit `0`, output `.gitignore:2:.env\t.env`.

Note on `-v` exit code with negation patterns: on git 2.50.1 (Apple Git-155), `git check-ignore -v <path>` returns exit `0` when a negation pattern matches (printing the `!…` line), whereas `git check-ignore <path>` without `-v` returns exit `1` (none of the provided paths are ignored). The semantic invariant — "`.env.example` is NOT gitignored" — is validated by the bare `git check-ignore .env.example` form. The Story 4.3 harness uses the bare form to assert non-ignore; the `-v` form is used only for `.env` to confirm the positive-match output shape. This is a minor rephrasing of Story 4.2 F3 `.cursor/mcp.placeholders.md` pattern (where no negation is involved and `-v` does exit `1`).

`.env` itself remains ignored (matches `.env` pattern at line 2). The negation is `.env.example`-specific and does not leak.

## Byte-stability fingerprints (mcp.json, mcp.README.md, mcp.placeholders.md, .gitignore)

Captured 2026-04-21 via `shasum -a 256`. All values match the Story 4.2 task-handoff fingerprints (zero drift).

| Path                            | SHA-256                                                              |
|---------------------------------|----------------------------------------------------------------------|
| `.cursor/mcp.json`              | `d749b788efa974330d104875a5b63793253a40b450f70341da971a403ac3477c`   |
| `.cursor/mcp.README.md`         | `4f27217a93f71b5bc45b0e4055a4ab82b1d052b2f346277b2dd945d89150af09`   |
| `.cursor/mcp.placeholders.md`   | `1fd08afbf68f8d97d0110dbdbdcf7b7f289adba0e7c649dcbe80609b395fa010`   |
| `.gitignore`                    | `49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1`   |

These four fingerprints are asserted by the Story 4.3 harness `task7` at every run.

## Predecessor-harness compatibility scan (twelve harnesses)

For each of the twelve predecessor harnesses, inspected for any repo-root path reference or `*.example` / `.env*` pattern that could reject a new `.env.example` file. Findings:

- Stories 1.1 / 1.2 / 1.3 iterate a locked root-file list (`README.md`, `LICENSE`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.gitignore`) plus specific directories — NOT a wildcard. Adding `.env.example` at the root does NOT drift any root-file enumeration.
- Stories 2.x / 3.x / 4.1 / 4.2 scope to their own subtrees (`agents/personas/*.md`, `.cursor/rules/*.mdc`, `memory/**`, `.cursor/mcp.json`, `.cursor/mcp.README.md`, `.cursor/mcp.placeholders.md`). None of them traverse the repo root in a way that would discover or reject `.env.example`.
- Zero predecessor harness contains a `.env*` or `*.example` regex.

Conclusion: zero allowlist extensions needed across the twelve predecessor harnesses. Adding `.env.example` is fully additive.

## Empirical predecessor PASS-count vector

Running each of the twelve predecessor harnesses with `BMAD_REGRESSION_DEPTH=1` exported (so nested `task9` chains short-circuit per Story 4.2 F6):

| Position | Harness                                               | PASS lines (all mode) |
|----------|-------------------------------------------------------|-----------------------|
| 0        | `story-1-1-scaffold-validation.sh`                    | 1                     |
| 1        | `story-1-2-root-files-validation.sh`                  | 1                     |
| 2        | `story-1-3-root-context-validation.sh`                | 1                     |
| 3        | `story-2-1-agent-identity-validation.sh`              | 1                     |
| 4        | `story-2-2-guardrail-and-formatting-validation.sh`    | 10                    |
| 5        | `story-2-3-work-persona-validation.sh`                | 7                     |
| 6        | `story-2-4-benji-inbox-absence-validation.sh`         | 7                     |
| 7        | `story-3-1-memory-template-tree-validation.sh`        | 7                     |
| 8        | `story-3-2-obsidian-config-validation.sh`             | 7                     |
| 9        | `story-3-3-identity-preferences-validation.sh`        | 7                     |
| 10       | `story-4-1-mcp-json-validation.sh`                    | 10                    |
| 11       | `story-4-2-mcp-placeholders-validation.sh`            | 10                    |

`EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 10 )` — twelve-element positional-parallel vector. Matches the Story 4.2 vector extended by one (Story 4.2 contributes `10` — nine gates + `all`).

## Predecessor harness SHA-256 fingerprints (EXPECTED_PREDECESSOR_SHA256)

Captured 2026-04-21 on-disk via `shasum -a 256`. Twelve-element positional-parallel array (Story 4.2 F5 pattern extended to twelve).

| Position | Harness                                               | SHA-256                                                              |
|----------|-------------------------------------------------------|----------------------------------------------------------------------|
| 0        | `story-1-1-scaffold-validation.sh`                    | `a609f6a857235a57588bab081c2775c3d59c9282ae0d1256f4183b5e923617b8` |
| 1        | `story-1-2-root-files-validation.sh`                  | `0226aa1b2086ee63065a533bc720afe876fde0958af9ed99276c1ff68fb4afaf` |
| 2        | `story-1-3-root-context-validation.sh`                | `0cecd5293af7e5896bede460ef1f2a7e822554f735dc10b81d0beb8e0e840ba9` |
| 3        | `story-2-1-agent-identity-validation.sh`              | `dc9b98e5e89239d41429e4436b13c671822d237f616eb8ca99c016085e2bb08a` |
| 4        | `story-2-2-guardrail-and-formatting-validation.sh`    | `5412bcfc7bd829a98a9054efb8fdf32c72b7e59c2b542cacca0c58648da6df10` |
| 5        | `story-2-3-work-persona-validation.sh`                | `9d455eaebb775f80d29b24de4a35febc3a8ffba0ed7f237af492723d2096a591` |
| 6        | `story-2-4-benji-inbox-absence-validation.sh`         | `f70d8c25e333123c3aae9d44a388594f1850be1449e86a540fdbe2dbec701687` |
| 7        | `story-3-1-memory-template-tree-validation.sh`        | `cb298fff4f83ddbf27644293f4a38ecfd36b099b4d7d4ceb180c41a4af383ff7` |
| 8        | `story-3-2-obsidian-config-validation.sh`             | `10ef5221ed1e64e3222c7d95297824175693f66c313eced1260d5645be81292e` |
| 9        | `story-3-3-identity-preferences-validation.sh`        | `77a5376887f03909223074b2f21e1306f689a9238d6da0cf191aa79a0427b427` |
| 10       | `story-4-1-mcp-json-validation.sh`                    | `cfe810169aef5c2abf7bc021aad4fbb43d3c91eda58fc99b3d16123907dbba8f` |
| 11       | `story-4-2-mcp-placeholders-validation.sh`            | `ac01c393e68c41df07cc4792abab703d62d4a10d40e96b68c9ac771bd9a1a490` |

Zero drift vs. Story 4.2 handoff (Stories 1.1 → 4.1 unchanged; Story 4.2 is new in the twelve-element array — per-harness SHA for Story 4.2 captured on first invocation).

## Source URLs

- `.cursor/mcp.README.md` — authoritative for active-MCP Required env vars. Lines 15–86 per § headings.
- `.cursor/mcp.placeholders.md` — authoritative for placeholder-MCP Purpose / Intended transport / Wiring reference. Eleven H2 sections.
- `_bmad-output/planning-artifacts/epics.md` Epic 4 Story 4.3 — lines 312–321. AC: "Section per MCP with variable name, purpose, and wiring link" + "Marked `status: active | placeholder` per MCP".
- `_bmad-output/planning-artifacts/architecture.md` line 24 — "Keep secrets/local artifacts out of git via root `.gitignore`".
- `https://cursor.com/docs/cli/mcp` — Cursor MCP documentation.
- `https://forum.cursor.com/t/how-to-use-environment-variables-in-mcp-json/79296` — `${VAR}` non-expansion doctrine (empty-RHS only).
- `https://developers.freshdesk.com/api/` — Freshdesk API key + domain convention.
- `https://developers.hubspot.com/docs/api/overview` — HubSpot OAuth access-token pattern.
- `https://github.com/elastic/mcp-server-elasticsearch` — Elastic env-var pair.
- `https://github.com/vixxo-copilot/agent-skills` — agent-skills companion repo (introspection MCP host).

<!-- Why: Story 4.3 baseline evidence per Task 1; cross-references env-var sources from Story 4.1 mcp.README.md and Story 4.2 mcp.placeholders.md; locks fingerprints feeding Task 5 harness. -->
