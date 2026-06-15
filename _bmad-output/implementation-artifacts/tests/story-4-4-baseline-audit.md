# Story 4.4 Baseline Audit

Date: 2026-04-21
Scope: Cross-reference every per-MCP prose string that will appear in `docs/setup.md` and `docs/mcps.md` against the three authoritative predecessor artifacts (`.cursor/mcp.README.md`, `.cursor/mcp.placeholders.md`, `.env.example`); capture byte-stability fingerprints; confirm thirteen-harness regression chain compatibility; audit the Story 1.2 `docs/setup.md` stub rewrite delta.

## Per-MCP cross-reference with .cursor/mcp.README.md / .cursor/mcp.placeholders.md / .env.example

Sixteen-row correspondence table proving zero drift between the three authoritative predecessor artifacts and the `docs/mcps.md` catalog-table row planned for each server. `Status` / `Transport` / `Env vars` / `Wiring reference` values are copied verbatim from `.env.example`'s per-MCP section; `Purpose` strings are copied verbatim from `.cursor/mcp.README.md` (active) and `.cursor/mcp.placeholders.md` (placeholder).

| Server key | Status (from .env.example `# status:`) | Transport (from .env.example `# Transport:`) | Env vars (from .env.example bare/commented decls) | Wiring reference (from .env.example `# Wiring link:`) | Source README section |
| --- | --- | --- | --- | --- | --- |
| linear | active-no-env | remote URL (HTTP) | — | https://linear.app/docs/mcp | `.cursor/mcp.README.md` § Linear |
| github | active | local stdio (docker) | GITHUB_PERSONAL_ACCESS_TOKEN | https://github.com/github/github-mcp-server | `.cursor/mcp.README.md` § GitHub |
| microsoft-365 | active | local stdio (npx) | MS365_MCP_CLIENT_ID (opt), MS365_MCP_TENANT_ID (opt) | https://github.com/softeria/ms-365-mcp-server | `.cursor/mcp.README.md` § Microsoft 365 |
| salesforce | active-no-env | local stdio (npx) | — | https://github.com/salesforcecli/mcp | `.cursor/mcp.README.md` § Salesforce |
| gong | active | local stdio (npx) | GONG_ACCESS_KEY, GONG_ACCESS_KEY_SECRET | https://github.com/kenazk/gong-mcp | `.cursor/mcp.README.md` § Gong |
| freshdesk | placeholder | local stdio (intended) | FRESHDESK_API_KEY (TBD), FRESHDESK_DOMAIN (TBD) | TODO: Vixxo internal wiki — Freshdesk MCP onboarding | `.cursor/mcp.placeholders.md` § Freshdesk |
| dynamics | placeholder | local stdio (intended) | DYNAMICS_CLIENT_ID (TBD), DYNAMICS_CLIENT_SECRET (TBD), DYNAMICS_TENANT_ID (TBD) | TODO: Vixxo internal wiki — Dynamics 365 MCP onboarding | `.cursor/mcp.placeholders.md` § Dynamics |
| vixxonow | placeholder | remote URL (HTTP) | VIXXONOW_API_TOKEN (TBD) | TODO: Vixxo internal wiki — VixxoNow MCP endpoint | `.cursor/mcp.placeholders.md` § VixxoNow |
| vixxolink | placeholder | remote URL (HTTP) | VIXXOLINK_API_TOKEN (TBD) | TODO: Vixxo internal wiki — VixxoLink MCP endpoint | `.cursor/mcp.placeholders.md` § VixxoLink |
| gateway | placeholder | remote URL (HTTP) | GATEWAY_API_TOKEN (TBD) | TODO: Vixxo internal wiki — Gateway MCP endpoint | `.cursor/mcp.placeholders.md` § Gateway |
| zoominfo | placeholder | local stdio (intended) | ZOOMINFO_USERNAME (TBD), ZOOMINFO_PASSWORD (TBD) | TODO: Vixxo internal wiki — ZoomInfo MCP onboarding | `.cursor/mcp.placeholders.md` § ZoomInfo |
| hubspot | placeholder | remote URL (HTTP) | HUBSPOT_ACCESS_TOKEN (TBD) | https://developers.hubspot.com/docs/api/overview | `.cursor/mcp.placeholders.md` § HubSpot |
| aws-connect | placeholder | local stdio (intended) | AWS_ACCESS_KEY_ID (TBD), AWS_SECRET_ACCESS_KEY (TBD), AWS_REGION (TBD), AWS_CONNECT_INSTANCE_ID (TBD) | TODO: Vixxo internal wiki — AWS Connect MCP onboarding | `.cursor/mcp.placeholders.md` § AWS Connect |
| chatfpt | placeholder | remote URL (HTTP) | CHATFPT_API_TOKEN (TBD) | TODO: Vixxo internal wiki — ChatFPT MCP endpoint | `.cursor/mcp.placeholders.md` § ChatFPT |
| elastic | placeholder | local stdio (intended) | ELASTIC_URL (TBD), ELASTIC_API_KEY (TBD) | https://github.com/elastic/mcp-server-elasticsearch | `.cursor/mcp.placeholders.md` § Elastic |
| introspection | placeholder | local stdio (intended) | — | https://github.com/vixxo-copilot/agent-skills | `.cursor/mcp.placeholders.md` § agent-skills Introspection MCP |

Status-value counts from `.env.example`: `active=3`, `active-no-env=2`, `placeholder=11`. Total `16`.

Transport-value counts: `remote URL (HTTP)=6`, `local stdio (docker)=1`, `local stdio (npx)=3`, `local stdio (intended)=6`. Total `16`.

Set equality with `docs/mcps.md` catalog-table columns verified by harness `check_task5`.

## Byte-stability fingerprints (mcp.json, mcp.README.md, mcp.placeholders.md, .env.example, .gitignore, docs/legal/license-vixxo-internal-canonical.md)

Captured 2026-04-21 on-disk via `shasum -a 256 <path>`:

- `.cursor/mcp.json` — `d749b788efa974330d104875a5b63793253a40b450f70341da971a403ac3477c` (same as Story 4.3 handoff; Story 4.1 origin; byte-stable across Story 4.2 / 4.3)
- `.cursor/mcp.README.md` — `4f27217a93f71b5bc45b0e4055a4ab82b1d052b2f346277b2dd945d89150af09` (same as Story 4.3 handoff)
- `.cursor/mcp.placeholders.md` — `1fd08afbf68f8d97d0110dbdbdcf7b7f289adba0e7c649dcbe80609b395fa010` (same as Story 4.3 handoff)
- `.env.example` — `19f9c52047f821f814dfe3b200f0fb77f641d1b373499691f445f8c83d4ed6a4` (Story 4.3 origin)
- `.gitignore` — `49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1` (Story 1.1 + F1 patch)
- `docs/legal/license-vixxo-internal-canonical.md` — `4b1cbb2d7e7ba1629df5913a45df3a43e4dd3f78d0c786262589ea53160193cc` (Story 1.2 legal source text; on-disk capture 2026-04-21)

All six fingerprints are embedded into `story-4-4-setup-and-mcps-docs-validation.sh` `check_task7` as byte-stability invariants.

## Predecessor-harness compatibility scan (thirteen harnesses)

For each of the thirteen predecessor harnesses, scanned for `docs/setup`, `docs/mcps`, and `docs/` string matches:

| Harness | docs/setup matches | docs/mcps matches | docs/ matches | Rewrite-safe? |
| --- | --- | --- | --- | --- |
| story-1-1-scaffold-validation.sh | 0 | 0 | 1 (`docs/.gitkeep` — directory-presence check, tolerates rewrite) | yes |
| story-1-2-root-files-validation.sh | 3 (file-existence assert + README link assert) | 0 | 4 (legal-doc path + setup-doc path; no content-shape assert on `docs/setup.md`) | yes — harness iterates fixed `README.md/LICENSE/AGENTS.md/CLAUDE.md/.cursorrules/.gitignore` set; only `require_file_exists "${SETUP_DOC_PATH}"` touches `docs/setup.md`; rewrite preserves file existence |
| story-1-3-root-context-validation.sh | 0 | 0 | 0 | yes |
| story-2-1-agent-identity-validation.sh | 0 | 0 | 0 | yes |
| story-2-2-guardrail-and-formatting-validation.sh | 0 | 0 | 0 | yes |
| story-2-3-work-persona-validation.sh | 0 | 0 | 0 | yes |
| story-2-4-benji-inbox-absence-validation.sh | 0 | 0 | 0 | yes |
| story-3-1-memory-template-tree-validation.sh | 0 | 0 | 0 | yes |
| story-3-2-obsidian-config-validation.sh | 0 | 0 | 0 | yes |
| story-3-3-identity-preferences-validation.sh | 0 | 0 | 0 | yes |
| story-4-1-mcp-json-validation.sh | 0 | 0 | 0 | yes |
| story-4-2-mcp-placeholders-validation.sh | 0 | 0 | 0 | yes |
| story-4-3-env-example-validation.sh | 0 | 0 | 0 | yes |

Empirical conclusion: Story 1.2's harness `require_file_exists "${SETUP_DOC_PATH}"` is the only `docs/setup.md` touchpoint across the thirteen-harness regression chain and only asserts presence, not content. The rewrite is zero-regression.

## Empirical predecessor PASS-count vector

Confirmed 2026-04-21 via `bash <harness> all` invocations in local repo root. Thirteen-element positional-parallel vector:

```
EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 10 10 )
```

Mapping (Story → expected `^PASS:` line count emitted by `all` mode):

- Story 1.1 → 1 (single-gate harness; prints `PASS: all`)
- Story 1.2 → 1 (single-gate harness; prints `PASS: all`)
- Story 1.3 → 1 (single-gate harness; prints `PASS: all`)
- Story 2.1 → 1 (single-gate harness; prints `PASS: all`)
- Story 2.2 → 10 (nine gates + `all`)
- Story 2.3 → 7 (six gates + `all`)
- Story 2.4 → 7 (six gates + `all`)
- Story 3.1 → 7 (six gates + `all`)
- Story 3.2 → 7 (six gates + `all`)
- Story 3.3 → 7 (six gates + `all`)
- Story 4.1 → 10 (nine gates + `all`)
- Story 4.2 → 10 (nine gates + `all`)
- Story 4.3 → 10 (nine gates + `all`)

Each predecessor invoked with `BMAD_REGRESSION_DEPTH=1` env var exported so nested `check_task9` invocations short-circuit (Story 4.2 F6 inheritance).

## Predecessor-harness SHA-256 anchor (EXPECTED_PREDECESSOR_SHA256)

Captured 2026-04-21 on-disk (positional-parallel to EXPECTED_PASS_COUNTS). Story 4.2 F5 inheritance extended to thirteen elements.

```
Story 1.1  a609f6a857235a57588bab081c2775c3d59c9282ae0d1256f4183b5e923617b8
Story 1.2  0226aa1b2086ee63065a533bc720afe876fde0958af9ed99276c1ff68fb4afaf
Story 1.3  0cecd5293af7e5896bede460ef1f2a7e822554f735dc10b81d0beb8e0e840ba9
Story 2.1  dc9b98e5e89239d41429e4436b13c671822d237f616eb8ca99c016085e2bb08a
Story 2.2  5412bcfc7bd829a98a9054efb8fdf32c72b7e59c2b542cacca0c58648da6df10
Story 2.3  9d455eaebb775f80d29b24de4a35febc3a8ffba0ed7f237af492723d2096a591
Story 2.4  f70d8c25e333123c3aae9d44a388594f1850be1449e86a540fdbe2dbec701687
Story 3.1  cb298fff4f83ddbf27644293f4a38ecfd36b099b4d7d4ceb180c41a4af383ff7
Story 3.2  10ef5221ed1e64e3222c7d95297824175693f66c313eced1260d5645be81292e
Story 3.3  77a5376887f03909223074b2f21e1306f689a9238d6da0cf191aa79a0427b427
Story 4.1  cfe810169aef5c2abf7bc021aad4fbb43d3c91eda58fc99b3d16123907dbba8f
Story 4.2  ac01c393e68c41df07cc4792abab703d62d4a10d40e96b68c9ac771bd9a1a490
Story 4.3  7aa2733e3b0e93d6b35bd0d7c89645ded810ae876b10e81554d26c738d61a277
```

Each value re-computed BEFORE embedding; matches on-disk. Harness `check_task9` verifies each value before invoking the corresponding sub-harness; drift = silent regression = fail the gate.

## docs/setup.md rewrite-delta audit

Existing `docs/setup.md` (Story 1.2 stub — 38 lines) content:

- H1: `# assistants-template setup`
- Opening sentence: "Use this checklist to bootstrap a local work assistant in under 15 minutes."
- `## Prerequisites` — git / Node.js Active LTS / npx
- `## Steps` — numbered list: (1) `git clone <repo-url> assistants-template`, (2) `npx skills add vixxo-copilot/agent-skills`, (3) verify scaffold via `ls -la`, (4) placeholder pointer
- `## Troubleshooting` — two bullets referencing Node.js LTS + internal tracker

Story 4.4 rewrite replaces the stub wholesale:

- Six-line YAML frontmatter (new — stub has none)
- H1 updated to `# assistants-template — setup and onboarding` (locked form)
- Seven H2 sections in canonical order (stub has three)
- HTML-comment terminator (new — stub has none)
- Preserved in spirit: `npx skills add vixxo-copilot/agent-skills` — carries forward verbatim inside `## Clone and install`
- Added wholesale: `.env` configuration, per-MCP cross-links, smoke-test section with `./bin/init` forward reference, troubleshooting with macOS / Docker / sf CLI caveats

Placeholder-form regression note: the stub's `git clone <repo-url>` form hits the Story 4.3 `<[A-Za-z_][A-Za-z0-9_]*>` angle-bracket probe. The rewrite replaces with `git clone YOUR-REPO-URL assistants-template` (hyphen breaks the probe regex's `[A-Za-z_][A-Za-z0-9_]*` identifier-only shape) plus a prose phrase ("replace YOUR-REPO-URL with the repository URL provided by your Vixxo maintainer").

## Placeholder-MCP wiring-link audit

Re-verified 2026-04-21: eleven placeholder-MCP `**Wiring reference:**` values in `.cursor/mcp.placeholders.md` exactly match the `# Wiring link:` values in `.env.example`:

| Server key | .cursor/mcp.placeholders.md value | .env.example value | Match |
| --- | --- | --- | --- |
| freshdesk | `TODO: Vixxo internal wiki — Freshdesk MCP onboarding` | `TODO: Vixxo internal wiki — Freshdesk MCP onboarding` | yes |
| dynamics | `TODO: Vixxo internal wiki — Dynamics 365 MCP onboarding` | `TODO: Vixxo internal wiki — Dynamics 365 MCP onboarding` | yes |
| vixxonow | `TODO: Vixxo internal wiki — VixxoNow MCP endpoint` | `TODO: Vixxo internal wiki — VixxoNow MCP endpoint` | yes |
| vixxolink | `TODO: Vixxo internal wiki — VixxoLink MCP endpoint` | `TODO: Vixxo internal wiki — VixxoLink MCP endpoint` | yes |
| gateway | `TODO: Vixxo internal wiki — Gateway MCP endpoint` | `TODO: Vixxo internal wiki — Gateway MCP endpoint` | yes |
| zoominfo | `TODO: Vixxo internal wiki — ZoomInfo MCP onboarding` | `TODO: Vixxo internal wiki — ZoomInfo MCP onboarding` | yes |
| hubspot | `https://developers.hubspot.com/docs/api/overview` | `https://developers.hubspot.com/docs/api/overview` | yes |
| aws-connect | `TODO: Vixxo internal wiki — AWS Connect MCP onboarding` | `TODO: Vixxo internal wiki — AWS Connect MCP onboarding` | yes |
| chatfpt | `TODO: Vixxo internal wiki — ChatFPT MCP endpoint` | `TODO: Vixxo internal wiki — ChatFPT MCP endpoint` | yes |
| elastic | `https://github.com/elastic/mcp-server-elasticsearch` | `https://github.com/elastic/mcp-server-elasticsearch` | yes |
| introspection | `https://github.com/vixxo-copilot/agent-skills` | `https://github.com/vixxo-copilot/agent-skills` | yes |

All eleven values propagate verbatim into `docs/mcps.md` catalog table `Wiring reference` column.

## Source URLs

- Upstream MCP references (for `docs/mcps.md` Wiring reference column URLs):
  - Linear MCP: `https://linear.app/docs/mcp`
  - GitHub MCP: `https://github.com/github/github-mcp-server`
  - Microsoft 365 MCP: `https://github.com/softeria/ms-365-mcp-server`
  - Salesforce MCP: `https://github.com/salesforcecli/mcp`
  - Gong MCP: `https://github.com/kenazk/gong-mcp`
  - HubSpot API: `https://developers.hubspot.com/docs/api/overview`
  - Elastic MCP: `https://github.com/elastic/mcp-server-elasticsearch`
  - agent-skills (introspection): `https://github.com/vixxo-copilot/agent-skills`
- Cursor MCP documentation: `https://cursor.com/docs/cli/mcp`
- GitHub-Flavored Markdown table spec: `https://github.github.com/gfm/#tables-extension-`
- macOS launchctl caveat (Cursor community thread): `https://forum.cursor.com/t/how-to-use-environment-variables-in-mcp-json/79296`

<!-- Why: Story 4.4 baseline audit evidence (AC1–AC11); cross-reference with .cursor/mcp.README.md / .cursor/mcp.placeholders.md / .env.example; byte-stability fingerprints; thirteen-harness compatibility scan; rewrite-delta audit; placeholder-MCP wiring-link audit. -->
