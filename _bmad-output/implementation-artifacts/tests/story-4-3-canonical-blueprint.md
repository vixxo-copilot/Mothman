# Story 4.3 Canonical Blueprint

Date: 2026-04-21
Scope: Lock every byte-level invariant the Story 4.3 harness will assert against `.env.example`.

## Header banner lock (lines 1–5, verbatim)

```text
# .env.example — credential template for assistants-template
# Copy this file to `.env` and fill in values for the MCPs you use.
# `.env` is gitignored (see `.gitignore`). `.env.example` is tracked (allowlist: `!.env.example`).
# NEVER commit `.env.example` with real values — every RHS below is intentionally blank or commented.
# Sections are ordered: ACTIVE MCPs first (mcp.json order), then PLACEHOLDER MCPs (mcp.placeholders.md order).
```

## Terminator lock (last non-blank line, verbatim)

Shell-comment form (NOT HTML-comment form — deliberate deviation documented in the story Dev Notes § "Shell-comment terminator form").

```text
# Why: documents every credential the assistants-template MCP surface can consume per Epic 4 Story 4.3 AC1; mirrors .cursor/mcp.README.md (active) and .cursor/mcp.placeholders.md (pending).
```

## Active/placeholder banner-divider locks (verbatim)

- ACTIVE banner (appears after the five-line header banner and a single blank line, before the `linear` section):

  ```text
  # === ACTIVE MCPs (wired in .cursor/mcp.json — see .cursor/mcp.README.md) ===
  ```

- PLACEHOLDER banner (appears after the `gong` section's blank-line terminator, before the `freshdesk` section):

  ```text
  # === PLACEHOLDER MCPs (not wired — see .cursor/mcp.placeholders.md) ===
  ```

Exactly two banner-divider lines total.

## Body section order lock (sixteen per-MCP dividers, canonical order)

```text
# --- linear ---
# --- github ---
# --- microsoft-365 ---
# --- salesforce ---
# --- gong ---
# --- freshdesk ---
# --- dynamics ---
# --- vixxonow ---
# --- vixxolink ---
# --- gateway ---
# --- zoominfo ---
# --- hubspot ---
# --- aws-connect ---
# --- chatfpt ---
# --- elastic ---
# --- introspection ---
```

Exactly sixteen dividers matching the regex `^# --- [a-z][a-z0-9-]* ---$`. No other divider-shaped lines permitted.

## Per-section template lock (five metadata lines + zero-or-more declarations + trailing blank line)

```text
# --- <server-key> ---
# status: <active | active-no-env | placeholder>
# Purpose: <one-sentence purpose>
# Transport: <remote URL (HTTP) | local stdio (docker) | local stdio (npx) | local stdio (intended)>
# Auth: <one-line auth summary OR "TBD — placeholder; not yet wired">
# Wiring link: <URL | TODO: descriptive phrase>
<optional bare VAR= lines OR commented # VAR= lines>

```

Every section ends with a single blank line before the next divider (or the terminator). No trailing whitespace permitted anywhere in the file.

## Env-var declaration lock (empty-RHS only)

- Bare declarations match `^[A-Z][A-Z0-9_]*=$`. The character immediately after `=` is a newline.
- Commented declarations match `^# [A-Z][A-Z0-9_]*=$`. Same empty-RHS discipline.
- Zero `${VAR}` / `$VAR` tokens permitted anywhere in the file.
- Zero `VAR=<non-whitespace>` lines permitted.

## Per-server content locks — ACTIVE (five)

### linear

```text
# --- linear ---
# status: active-no-env
# Purpose: Vixxo work task and project management (issues, projects, cycles).
# Transport: remote URL (HTTP)
# Auth: OAuth 2.1 interactive via Cursor's MCP UI on first connect.
# Wiring link: https://linear.app/docs/mcp
```

Zero env-var declaration lines.

### github

```text
# --- github ---
# status: active
# Purpose: Source control, code review, repository documentation, PR automation.
# Transport: local stdio (docker)
# Auth: Shell env inherited via Docker `-e NAME` bare-form.
# Wiring link: https://github.com/github/github-mcp-server
GITHUB_PERSONAL_ACCESS_TOKEN=
```

One bare env-var declaration.

### microsoft-365

```text
# --- microsoft-365 ---
# status: active
# Purpose: Outlook mail/calendar, OneDrive files, Teams chat, Microsoft Graph API coverage.
# Transport: local stdio (npx)
# Auth: Device-code flow on first run; token cached in OS keychain.
# Wiring link: https://github.com/softeria/ms-365-mcp-server
# MS365_MCP_CLIENT_ID=
# MS365_MCP_TENANT_ID=
```

Zero bare declarations, two commented optional declarations.

### salesforce

```text
# --- salesforce ---
# status: active-no-env
# Purpose: CRM, pipeline, accounts, contacts, Apex execution, SOQL queries.
# Transport: local stdio (npx)
# Auth: Salesforce CLI (`sf`) session at `~/.sf/`; run `sf org login web` once out of band.
# Wiring link: https://github.com/salesforcecli/mcp
```

Zero env-var declaration lines.

### gong

```text
# --- gong ---
# status: active
# Purpose: Call recordings, transcripts, deal intelligence.
# Transport: local stdio (npx)
# Auth: Shell env inherited (variables exported in shell rc before launching Cursor).
# Wiring link: https://github.com/kenazk/gong-mcp
GONG_ACCESS_KEY=
GONG_ACCESS_KEY_SECRET=
```

Two bare env-var declarations.

## Per-server content locks — PLACEHOLDER (eleven)

### freshdesk

```text
# --- freshdesk ---
# status: placeholder
# Purpose: Customer support ticket management (tickets, contacts, dispatch).
# Transport: local stdio (intended)
# Auth: TBD — placeholder; not yet wired
# Wiring link: TODO: Vixxo internal wiki — Freshdesk MCP onboarding
# FRESHDESK_API_KEY=
# FRESHDESK_DOMAIN=
```

### dynamics

```text
# --- dynamics ---
# status: placeholder
# Purpose: Microsoft Dynamics 365 CRM and ERP data (accounts, opportunities, orders).
# Transport: local stdio (intended)
# Auth: TBD — placeholder; not yet wired
# Wiring link: TODO: Vixxo internal wiki — Dynamics 365 MCP onboarding
# DYNAMICS_CLIENT_ID=
# DYNAMICS_CLIENT_SECRET=
# DYNAMICS_TENANT_ID=
```

### vixxonow

```text
# --- vixxonow ---
# status: placeholder
# Purpose: Vixxo internal service operations platform (work orders, technicians, SLAs).
# Transport: remote URL (HTTP)
# Auth: TBD — placeholder; not yet wired
# Wiring link: TODO: Vixxo internal wiki — VixxoNow MCP endpoint
# VIXXONOW_API_TOKEN=
```

### vixxolink

```text
# --- vixxolink ---
# status: placeholder
# Purpose: Vixxo partner/supplier connectivity portal.
# Transport: remote URL (HTTP)
# Auth: TBD — placeholder; not yet wired
# Wiring link: TODO: Vixxo internal wiki — VixxoLink MCP endpoint
# VIXXOLINK_API_TOKEN=
```

### gateway

```text
# --- gateway ---
# status: placeholder
# Purpose: Vixxo API gateway — aggregated access to internal services.
# Transport: remote URL (HTTP)
# Auth: TBD — placeholder; not yet wired
# Wiring link: TODO: Vixxo internal wiki — Gateway MCP endpoint
# GATEWAY_API_TOKEN=
```

### zoominfo

```text
# --- zoominfo ---
# status: placeholder
# Purpose: Sales and marketing intelligence (contacts, company firmographics, intent data).
# Transport: local stdio (intended)
# Auth: TBD — placeholder; not yet wired
# Wiring link: TODO: Vixxo internal wiki — ZoomInfo MCP onboarding
# ZOOMINFO_USERNAME=
# ZOOMINFO_PASSWORD=
```

### hubspot

```text
# --- hubspot ---
# status: placeholder
# Purpose: Marketing automation, CRM, and customer journey data.
# Transport: remote URL (HTTP)
# Auth: TBD — placeholder; not yet wired
# Wiring link: https://developers.hubspot.com/docs/api/overview
# HUBSPOT_ACCESS_TOKEN=
```

### aws-connect

```text
# --- aws-connect ---
# status: placeholder
# Purpose: AWS Contact Center (call metadata, contact flows, agent queues).
# Transport: local stdio (intended)
# Auth: TBD — placeholder; not yet wired
# Wiring link: TODO: Vixxo internal wiki — AWS Connect MCP onboarding
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# AWS_REGION=
# AWS_CONNECT_INSTANCE_ID=
```

### chatfpt

```text
# --- chatfpt ---
# status: placeholder
# Purpose: Vixxo internal conversational AI channel (logs, queries, completions).
# Transport: remote URL (HTTP)
# Auth: TBD — placeholder; not yet wired
# Wiring link: TODO: Vixxo internal wiki — ChatFPT MCP endpoint
# CHATFPT_API_TOKEN=
```

### elastic

```text
# --- elastic ---
# status: placeholder
# Purpose: Elasticsearch / Elastic Observability — log and metric search.
# Transport: local stdio (intended)
# Auth: TBD — placeholder; not yet wired
# Wiring link: https://github.com/elastic/mcp-server-elasticsearch
# ELASTIC_URL=
# ELASTIC_API_KEY=
```

### introspection

```text
# --- introspection ---
# status: placeholder
# Purpose: Introspection MCP from the companion vixxo-copilot/agent-skills repo — surfaces skill metadata, registry status, static-browser state to the agent.
# Transport: local stdio (intended)
# Auth: TBD — placeholder; not yet wired
# Wiring link: https://github.com/vixxo-copilot/agent-skills
```

Zero env-var declaration lines (introspection is parameterless at the env layer).

## Banned-term lock (inherited verbatim)

Seventeen-token boundary-guarded banned-term regex:

```
(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])
```

Applied case-insensitively via `grep -iE` against the `sanitize_for_banned_scan()` view (with `GITHUB_PERSONAL_ACCESS_TOKEN` substituted to `__GH_PAT_NAME__`). Zero matches expected.

Twelve Derek fixed-string probes (verbatim inheritance from Stories 3.x / 4.1 / 4.2):

```
Chiron, MasteryLab, Agile Weekly, Queen Creek, Gangplank, Bodybuilding.com, Integrum, Omarchy, derekneighbors.com, Playrix, Laurie, Deke
```

Three path-reference probes: `/Users/`, `Public/gtd-life`, `@gmail.com`.

## Secret-pattern catalog lock (inherited verbatim)

Eleven secret-pattern regexes (Story 4.1 AC4 catalog), applied against the `sanitize_for_banned_scan()`-filtered view. Zero matches per pattern expected.

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

Four `…=` lowercase literal probes (case-sensitive `grep -F`): `password=`, `token=`, `secret=`, `api_key=`. Zero matches expected (SCREAMING_SNAKE_CASE `_TOKEN=` / `_KEY=` declarations are uppercase and do NOT match lowercase literals).

## Placeholder-form probes (inherited verbatim)

Five probes; zero matches expected. `.env.example` is a shell-env template with ZERO template tokens.

```
\{\{[^}]+\}\}
\{[A-Za-z_][A-Za-z0-9_]*\}
<[A-Za-z_][A-Za-z0-9_]*>
%[A-Za-z_][A-Za-z0-9_]*%
\$\{[A-Za-z_][A-Za-z0-9_]*\}
```

Plus the full `${VAR}` / `$VAR` shell-expansion probe: `\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]+`. Zero matches expected (shell-expansion safety doctrine per AC6).

## Inheritance-only note

Every probe catalog (banned-term regex, Derek fixed strings, path-reference probes, secret-pattern regexes, `…=` literal probes, placeholder-form probes, `${VAR}/$VAR` probe) is inherited VERBATIM from Stories 3.1 / 3.2 / 3.3 / 4.1 / 4.2. Zero additions, zero removals. Story 4.3 adds ONE new probe family specific to its scope: the empty-RHS env-var declaration probes (`^[A-Z][A-Z0-9_]*=$` for bare form, `^# [A-Z][A-Z0-9_]*=$` for commented form). This is additive and does not alter any prior probe.

## Deny-list cross-reference (Story 4.1)

Per Story 4.1 AC8, `.cursor/mcp.json` is limited to five server keys (`linear`, `github`, `microsoft-365`, `salesforce`, `gong`). Story 4.3's five active-MCP sections mirror this set exactly. Per Story 4.2, the eleven placeholder-MCP server keys mirror the eleven H2 sections in `.cursor/mcp.placeholders.md`. The union of sixteen keys in `.env.example` satisfies AC2 set-equality.

## Evidence constants for Task 5 harness

- `EXPECTED_SECTION_KEYS=( linear github microsoft-365 salesforce gong freshdesk dynamics vixxonow vixxolink gateway zoominfo hubspot aws-connect chatfpt elastic introspection )` — sixteen keys, canonical order.
- `EXPECTED_STATUS_COUNTS`: `active=3` (github, microsoft-365, gong), `active-no-env=2` (linear, salesforce), `placeholder=11`. Total `^# status:` lines equals 16.
- `EXPECTED_BARE_VARS=( GITHUB_PERSONAL_ACCESS_TOKEN GONG_ACCESS_KEY GONG_ACCESS_KEY_SECRET )` — three tokens.
- `EXPECTED_COMMENTED_VARS=( MS365_MCP_CLIENT_ID MS365_MCP_TENANT_ID FRESHDESK_API_KEY FRESHDESK_DOMAIN DYNAMICS_CLIENT_ID DYNAMICS_CLIENT_SECRET DYNAMICS_TENANT_ID VIXXONOW_API_TOKEN VIXXOLINK_API_TOKEN GATEWAY_API_TOKEN ZOOMINFO_USERNAME ZOOMINFO_PASSWORD HUBSPOT_ACCESS_TOKEN AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_REGION AWS_CONNECT_INSTANCE_ID CHATFPT_API_TOKEN ELASTIC_URL ELASTIC_API_KEY )` — twenty tokens.
- `EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 10 )` — twelve-element vector.
- `EXPECTED_PREDECESSOR_SHA256=( … )` — twelve-element positional-parallel SHA-256 array from the baseline audit.
- `STORY_4_2_MCP_JSON_SHA256="d749b788efa974330d104875a5b63793253a40b450f70341da971a403ac3477c"`
- `STORY_4_2_MCP_README_SHA256="4f27217a93f71b5bc45b0e4055a4ab82b1d052b2f346277b2dd945d89150af09"`
- `STORY_4_2_MCP_PLACEHOLDERS_SHA256="1fd08afbf68f8d97d0110dbdbdcf7b7f289adba0e7c649dcbe80609b395fa010"`
- `STORY_1_1_GITIGNORE_SHA256="49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1"`

<!-- Why: Story 4.3 canonical blueprint per Task 2; locks every byte-level invariant the Task 5 harness asserts for `.env.example`; inheritance-only (zero probe additions vs Stories 4.1/4.2). -->
