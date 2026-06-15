# Story 4.4 Canonical Blueprint

Date: 2026-04-21
Scope: Lock every byte-level invariant the Story 4.4 harness will assert against `docs/setup.md` and `docs/mcps.md`.

## Frontmatter lock — docs/setup.md (lines 1–7, verbatim)

```text
---
type: setup-guide
scope: work
created: 2026-04-21
updated: 2026-04-21
tags: [setup, onboarding, work]
---
```

## Frontmatter lock — docs/mcps.md (lines 1–7, verbatim)

```text
---
type: mcp-catalog
scope: work
created: 2026-04-21
updated: 2026-04-21
tags: [mcp, catalog, work]
---
```

## H1 lock — docs/setup.md (line 9, verbatim)

```text
# assistants-template — setup and onboarding
```

## H1 lock — docs/mcps.md (line 9, verbatim)

```text
# assistants-template — MCP catalog
```

## H2 sequence lock — docs/setup.md (seven headings, canonical order)

```text
## Prerequisites
## Clone and install
## Configure credentials (`.env`)
## Configure active MCPs
## Review placeholder MCPs
## Run the setup smoke test
## Troubleshooting and next steps
```

Each H2 appears once; no duplicates; no other H2 headings in the body.

## H2 sequence lock — docs/mcps.md (five headings, canonical order)

```text
## Catalog at a glance
## Active MCPs
## Placeholder MCPs
## Credential surface
## Flipping a placeholder to active
```

Each H2 appears once; no duplicates; no other H2 headings in the body.

## Terminator lock — docs/setup.md (last non-blank line, verbatim)

HTML-comment form (markdown-idiomatic; reverts from Story 4.3's shell-comment deviation because `docs/setup.md` is markdown).

```text
<!-- Why: canonical self-serve onboarding checklist from clone through smoke-test per Epic 4 Story 4.4 AC1; cross-links .env.example (Story 4.3), .cursor/mcp.README.md (Story 4.1), .cursor/mcp.placeholders.md (Story 4.2), and docs/mcps.md (Story 4.4). -->
```

## Terminator lock — docs/mcps.md (last non-blank line, verbatim)

```text
<!-- Why: canonical catalog of every MCP the assistants-template ships (five active + eleven placeholder) per Epic 4 Story 4.4 AC3; cross-links .cursor/mcp.README.md (Story 4.1), .cursor/mcp.placeholders.md (Story 4.2), .env.example (Story 4.3), and docs/setup.md (Story 4.4). -->
```

## Catalog-table header + separator lock — docs/mcps.md § Catalog at a glance

Header row (verbatim):

```text
| Server key | Status | Transport | Env vars | Wiring reference |
```

Separator row (verbatim):

```text
| --- | --- | --- | --- | --- |
```

Exactly 18 pipe-prefixed lines total under `## Catalog at a glance` (1 header + 1 separator + 16 data rows). No other pipe-prefixed lines permitted anywhere else in the file.

## Catalog-table data-row lock (sixteen rows, canonical order, verbatim)

### linear
`| linear | active-no-env | remote URL (HTTP) | — | https://linear.app/docs/mcp |`

### github
`| github | active | local stdio (docker) | GITHUB_PERSONAL_ACCESS_TOKEN | https://github.com/github/github-mcp-server |`

### microsoft-365
`| microsoft-365 | active | local stdio (npx) | MS365_MCP_CLIENT_ID (opt), MS365_MCP_TENANT_ID (opt) | https://github.com/softeria/ms-365-mcp-server |`

### salesforce
`| salesforce | active-no-env | local stdio (npx) | — | https://github.com/salesforcecli/mcp |`

### gong
`| gong | active | local stdio (npx) | GONG_ACCESS_KEY, GONG_ACCESS_KEY_SECRET | https://github.com/kenazk/gong-mcp |`

### freshdesk
`| freshdesk | placeholder | local stdio (intended) | FRESHDESK_API_KEY (TBD), FRESHDESK_DOMAIN (TBD) | TODO: Vixxo internal wiki — Freshdesk MCP onboarding |`

### dynamics
`| dynamics | placeholder | local stdio (intended) | DYNAMICS_CLIENT_ID (TBD), DYNAMICS_CLIENT_SECRET (TBD), DYNAMICS_TENANT_ID (TBD) | TODO: Vixxo internal wiki — Dynamics 365 MCP onboarding |`

### vixxonow
`| vixxonow | placeholder | remote URL (HTTP) | VIXXONOW_API_TOKEN (TBD) | TODO: Vixxo internal wiki — VixxoNow MCP endpoint |`

### vixxolink
`| vixxolink | placeholder | remote URL (HTTP) | VIXXOLINK_API_TOKEN (TBD) | TODO: Vixxo internal wiki — VixxoLink MCP endpoint |`

### gateway
`| gateway | placeholder | remote URL (HTTP) | GATEWAY_API_TOKEN (TBD) | TODO: Vixxo internal wiki — Gateway MCP endpoint |`

### zoominfo
`| zoominfo | placeholder | local stdio (intended) | ZOOMINFO_USERNAME (TBD), ZOOMINFO_PASSWORD (TBD) | TODO: Vixxo internal wiki — ZoomInfo MCP onboarding |`

### hubspot
`| hubspot | placeholder | remote URL (HTTP) | HUBSPOT_ACCESS_TOKEN (TBD) | https://developers.hubspot.com/docs/api/overview |`

### aws-connect
`| aws-connect | placeholder | local stdio (intended) | AWS_ACCESS_KEY_ID (TBD), AWS_SECRET_ACCESS_KEY (TBD), AWS_REGION (TBD), AWS_CONNECT_INSTANCE_ID (TBD) | TODO: Vixxo internal wiki — AWS Connect MCP onboarding |`

### chatfpt
`| chatfpt | placeholder | remote URL (HTTP) | CHATFPT_API_TOKEN (TBD) | TODO: Vixxo internal wiki — ChatFPT MCP endpoint |`

### elastic
`| elastic | placeholder | local stdio (intended) | ELASTIC_URL (TBD), ELASTIC_API_KEY (TBD) | https://github.com/elastic/mcp-server-elasticsearch |`

### introspection
`| introspection | placeholder | local stdio (intended) | — | https://github.com/vixxo-copilot/agent-skills |`

## Skills-registry-reference lock

The literal string `npx skills add vixxo-copilot/agent-skills` MUST appear inside a fenced `bash` code block in `docs/setup.md` under `## Clone and install`.

The literal string `vixxo-copilot/agent-skills` MUST appear at least once in BOTH `docs/setup.md` AND `docs/mcps.md`.

The literal string `github:vixxo-copilot/agent-skills` MUST appear in `docs/mcps.md` (in the Introspection MCP context — carries the `github:vixxo-copilot/agent-skills#introspection` canonical form from `.cursor/mcp.placeholders.md`).

The literal string `./bin/init` MUST appear in `docs/setup.md` under `## Run the setup smoke test` (forward reference to Epic 5 Story 5.1).

## Banned-term lock (inherited verbatim from Story 4.3)

Seventeen-token boundary-guarded banned-term regex applied case-insensitively to the `sanitize_for_banned_scan()`-filtered concatenated view of both docs:

```
(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])
```

Twelve Derek fixed-string probes applied via `grep -Fi`:

```
Chiron, MasteryLab, Agile Weekly, Queen Creek, Gangplank, Bodybuilding.com, Integrum, Omarchy, derekneighbors.com, Playrix, Laurie, Deke
```

## Secret-pattern catalog lock (inherited verbatim from Story 4.1 AC4)

Eleven regex patterns:

```
sk-[A-Za-z0-9_-]{20,}
ghp_[A-Za-z0-9]{20,}
gho_[A-Za-z0-9]{20,}
ghs_[A-Za-z0-9]{20,}
github_pat_[A-Za-z0-9_]{20,}
xox[baprs]-[A-Za-z0-9-]{10,}
eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}
Bearer [A-Za-z0-9_.-]{20,}
AKIA[0-9A-Z]{16}
AIza[A-Za-z0-9_-]{35}
[A-Fa-f0-9]{32,}
```

Plus four lowercase-literal `…=` probes: `password=`, `token=`, `secret=`, `api_key=`.

## Placeholder-form probes (inherited verbatim)

Five placeholder-form regex probes applied to both docs; zero matches required:

```
\{\{[^}]+\}\}                         (double-curly templating form)
\{[A-Za-z_][A-Za-z0-9_]*\}            (single-brace identifier-only)
<[A-Za-z_][A-Za-z0-9_]*>              (angle-bracket identifier-only)
%[A-Za-z_][A-Za-z0-9_]*%              (percent-wrapped Windows-env form)
\$\{[A-Za-z_][A-Za-z0-9_]*\}          (dollar-brace shell-expansion form)
```

Plus the `${VAR}` / `$VAR` shell-expansion-token probe — `\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]+` — zero matches required.

Plus the three path-reference probes (`/Users/`, `Public/gtd-life`, `@gmail.com`) via `grep -F`; zero matches required.

## Inheritance-only note

Banned-term regex, twelve Derek fixed-string probes, eleven secret-pattern regexes, five placeholder-form probes, `${VAR}`/`$VAR` shell-expansion probe, three path-reference probes, four lowercase-literal `…=` probes: all inherited VERBATIM from Story 4.3 (which inherited from Story 4.1 / 4.2 / 3.3 / 3.2 / 3.1). Story 4.4 ADDS zero probes and REMOVES zero probes from the catalog. Story 4.4 ADDS one new helper: `extract_table_column` for GFM table parsing (`check_task5` consistency assertions).

## Evidence constants for Task 5 harness

```bash
EXPECTED_SECTION_KEYS=( linear github microsoft-365 salesforce gong \
  freshdesk dynamics vixxonow vixxolink gateway zoominfo hubspot \
  aws-connect chatfpt elastic introspection )

EXPECTED_SETUP_H2=( "Prerequisites" "Clone and install" \
  "Configure credentials (\`.env\`)" "Configure active MCPs" \
  "Review placeholder MCPs" "Run the setup smoke test" \
  "Troubleshooting and next steps" )

EXPECTED_MCPS_H2=( "Catalog at a glance" "Active MCPs" \
  "Placeholder MCPs" "Credential surface" "Flipping a placeholder to active" )

EXPECTED_TABLE_HEADER="| Server key | Status | Transport | Env vars | Wiring reference |"
EXPECTED_TABLE_SEPARATOR="| --- | --- | --- | --- | --- |"

EXPECTED_STATUS_VALUES=( active-no-env active active active-no-env active \
  placeholder placeholder placeholder placeholder placeholder placeholder \
  placeholder placeholder placeholder placeholder placeholder )

EXPECTED_TRANSPORT_VALUES=( "remote URL (HTTP)" "local stdio (docker)" \
  "local stdio (npx)" "local stdio (npx)" "local stdio (npx)" \
  "local stdio (intended)" "local stdio (intended)" "remote URL (HTTP)" \
  "remote URL (HTTP)" "remote URL (HTTP)" "local stdio (intended)" \
  "remote URL (HTTP)" "local stdio (intended)" "remote URL (HTTP)" \
  "local stdio (intended)" "local stdio (intended)" )

EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 10 10 )

# Thirteen positional-parallel SHA-256 values from Task 1 (Story 4.2 F5 pattern extended)
EXPECTED_PREDECESSOR_SHA256=( <thirteen values — see baseline audit> )

# Byte-stability fingerprints (AC8) — six values captured Task 1
STORY_4_3_MCP_JSON_SHA256="d749b788efa974330d104875a5b63793253a40b450f70341da971a403ac3477c"
STORY_4_3_MCP_README_SHA256="4f27217a93f71b5bc45b0e4055a4ab82b1d052b2f346277b2dd945d89150af09"
STORY_4_3_MCP_PLACEHOLDERS_SHA256="1fd08afbf68f8d97d0110dbdbdcf7b7f289adba0e7c649dcbe80609b395fa010"
STORY_4_3_ENV_EXAMPLE_SHA256="19f9c52047f821f814dfe3b200f0fb77f641d1b373499691f445f8c83d4ed6a4"
STORY_1_1_GITIGNORE_SHA256="49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1"
STORY_1_2_LICENSE_CANONICAL_SHA256="4b1cbb2d7e7ba1629df5913a45df3a43e4dd3f78d0c786262589ea53160193cc"
```

Runtime expectation: thirteen-predecessor regression ~150–200 s on macOS bash 3.2.57.

## Inheritance reference

- Story 4.1 — active-MCP README origin (`.cursor/mcp.README.md`); five-active-MCP catalog.
- Story 4.2 — placeholder MCPs companion (`.cursor/mcp.placeholders.md`); eleven-placeholder catalog.
- Story 4.3 — `.env.example` credential template; sixteen-section mapping; `EXPECTED_PREDECESSOR_SHA256` F5 anchor discipline; `BMAD_REGRESSION_DEPTH` F6 guard; shell-expansion-token probe. Harness structure is the direct model for Story 4.4 (same F-series review-fix patterns; one additional helper `extract_table_column`).
- Stories 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3 — regression chain tail (ten earlier predecessors).

<!-- Why: Story 4.4 canonical blueprint (AC1–AC7); locked frontmatter / H1 / H2 / catalog-table / terminator / probe-catalog / evidence-constants for harness enforcement. -->
