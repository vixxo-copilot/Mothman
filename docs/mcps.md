---
type: mcp-catalog
scope: work
created: 2026-04-21
updated: 2026-04-21
tags: [mcp, catalog, work]
---

# assistants-template — MCP catalog

This is the canonical catalog of every MCP the `assistants-template` ships. The template bundles sixteen servers in total: five active servers wired in `.cursor/mcp.json` (documented in `.cursor/mcp.README.md`) and eleven placeholder servers documented in `.cursor/mcp.placeholders.md`. Credentials for each server live in `.env.example`, and the onboarding checklist lives in `docs/setup.md`. The shared skill bundle for this template is published at `vixxo-copilot/agent-skills` — see `docs/setup.md` § `Clone and install` for the install command.

## Catalog at a glance

| Server key | Status | Transport | Env vars | Wiring reference |
| --- | --- | --- | --- | --- |
| linear | active-no-env | remote URL (HTTP) | — | https://linear.app/docs/mcp |
| github | active | local stdio (wrapper) | gh auth login or GITHUB_PERSONAL_ACCESS_TOKEN | https://github.com/github/github-mcp-server |
| microsoft-365 | active | local stdio (npx) | MS365_MCP_CLIENT_ID (opt), MS365_MCP_TENANT_ID (opt) | https://github.com/softeria/ms-365-mcp-server |
| salesforce | active-no-env | local stdio (npx) | — | https://github.com/salesforcecli/mcp |
| gong | active | local stdio (npx) | GONG_ACCESS_KEY, GONG_ACCESS_KEY_SECRET | https://github.com/kenazk/gong-mcp |
| freshdesk | placeholder | local stdio (intended) | FRESHDESK_API_KEY (TBD), FRESHDESK_DOMAIN (TBD) | TODO: Vixxo internal wiki — Freshdesk MCP onboarding |
| dynamics | placeholder | local stdio (intended) | DYNAMICS_CLIENT_ID (TBD), DYNAMICS_CLIENT_SECRET (TBD), DYNAMICS_TENANT_ID (TBD) | TODO: Vixxo internal wiki — Dynamics 365 MCP onboarding |
| vixxonow | placeholder | remote URL (HTTP) | VIXXONOW_API_TOKEN (TBD) | TODO: Vixxo internal wiki — VixxoNow MCP endpoint |
| vixxolink | placeholder | remote URL (HTTP) | VIXXOLINK_API_TOKEN (TBD) | TODO: Vixxo internal wiki — VixxoLink MCP endpoint |
| gateway | placeholder | remote URL (HTTP) | GATEWAY_API_TOKEN (TBD) | TODO: Vixxo internal wiki — Gateway MCP endpoint |
| zoominfo | placeholder | local stdio (intended) | ZOOMINFO_USERNAME (TBD), ZOOMINFO_PASSWORD (TBD) | TODO: Vixxo internal wiki — ZoomInfo MCP onboarding |
| hubspot | placeholder | remote URL (HTTP) | HUBSPOT_ACCESS_TOKEN (TBD) | https://developers.hubspot.com/docs/api/overview |
| aws-connect | placeholder | local stdio (intended) | AWS_ACCESS_KEY_ID (TBD), AWS_SECRET_ACCESS_KEY (TBD), AWS_REGION (TBD), AWS_CONNECT_INSTANCE_ID (TBD) | TODO: Vixxo internal wiki — AWS Connect MCP onboarding |
| chatfpt | placeholder | remote URL (HTTP) | CHATFPT_API_TOKEN (TBD) | TODO: Vixxo internal wiki — ChatFPT MCP endpoint |
| elastic | placeholder | local stdio (intended) | ELASTIC_URL (TBD), ELASTIC_API_KEY (TBD) | https://github.com/elastic/mcp-server-elasticsearch |
| introspection | placeholder | local stdio (intended) | — | https://github.com/vixxo-copilot/agent-skills |

The `Status` column mirrors the `# status:` mapping in `.env.example`: three `active`, two `active-no-env`, and eleven `placeholder`. The `Transport` column mirrors the `# Transport:` mapping in `.env.example`. Every `Wiring reference` value that is not an HTTPS URL is a `TODO:` phrase that a future story will resolve to a Vixxo internal wiki page.

## Active MCPs

The five active servers are wired in `.cursor/mcp.json` and documented per-server in `.cursor/mcp.README.md`. Consult that companion README for the authoritative Purpose, Transport, Auth, Required env vars, and Wiring link for each active server. The markdown anchor links below jump to the corresponding H2 in `.cursor/mcp.README.md` (the `../` prefix resolves against `docs/mcps.md`'s location one directory below the repository root):

- [Linear](../.cursor/mcp.README.md#linear) — Vixxo work task and project management (issues, projects, cycles).
- [GitHub](../.cursor/mcp.README.md#github) — Source control, code review, repository documentation, PR automation.
- [Microsoft 365](../.cursor/mcp.README.md#microsoft-365) — Outlook mail and calendar, OneDrive files, Teams chat, Microsoft Graph API coverage.
- [Salesforce](../.cursor/mcp.README.md#salesforce) — CRM, pipeline, accounts, contacts, Apex execution, SOQL queries.
- [Gong](../.cursor/mcp.README.md#gong) — Call recordings, transcripts, deal intelligence.

Every active server uses exactly one of three env-delivery patterns (shell inheritance, Docker `-e NAME` bare-form, or interactive OAuth / external CLI session). See `.cursor/mcp.README.md` § `Env Variable Handling Convention` for the full pattern catalog and `docs/setup.md` § `Configure active MCPs` for the onboarding walkthrough.

## Placeholder MCPs

Eleven placeholder servers ship as descriptive-only documentation in `.cursor/mcp.placeholders.md`. Each entry contains a Purpose line, a Status line (`placeholder — not wired`), an intended transport, a wiring reference, and a fenced JSON stub showing the canonical active-shape a future flip-to-active story would copy into `.cursor/mcp.json`. Placeholder servers are explicitly SKIPPED by the Epic 5 Story 5.3 wizard verification.

- [Freshdesk](../.cursor/mcp.placeholders.md#freshdesk) — Customer support ticket management (tickets, contacts, dispatch).
- [Dynamics](../.cursor/mcp.placeholders.md#dynamics) — Microsoft Dynamics 365 CRM and ERP data (accounts, opportunities, orders).
- [VixxoNow](../.cursor/mcp.placeholders.md#vixxonow) — Vixxo internal service operations platform (work orders, technicians, SLAs).
- [VixxoLink](../.cursor/mcp.placeholders.md#vixxolink) — Vixxo partner / supplier connectivity portal.
- [Gateway](../.cursor/mcp.placeholders.md#gateway) — Vixxo API gateway aggregating access to internal services.
- [ZoomInfo](../.cursor/mcp.placeholders.md#zoominfo) — Sales and marketing intelligence (contacts, company firmographics, intent data).
- [HubSpot](../.cursor/mcp.placeholders.md#hubspot) — Marketing automation, CRM, and customer journey data.
- [AWS Connect](../.cursor/mcp.placeholders.md#aws-connect) — AWS Contact Center (call metadata, contact flows, agent queues).
- [ChatFPT](../.cursor/mcp.placeholders.md#chatfpt) — Vixxo internal conversational AI channel (logs, queries, completions).
- [Elastic](../.cursor/mcp.placeholders.md#elastic) — Elasticsearch and Elastic Observability (log and metric search).
- [agent-skills Introspection MCP](../.cursor/mcp.placeholders.md#agent-skills-introspection-mcp) — surfaces skill metadata, registry status, and static-browser state from the companion `vixxo-copilot/agent-skills` repository; wired as `github:vixxo-copilot/agent-skills#introspection` when flipped to active.

## Credential surface

Every credential the template can consume is declared in `.env.example`. Copy that file to `.env` (see `docs/setup.md` § `Configure credentials`), then populate values for the active MCPs you intend to use. The `.env` file is ignored by `.gitignore`; `.env.example` is allowlisted via the `!.env.example` rule.

Three required and two optional variables back the five active MCPs:

- `GITHUB_PERSONAL_ACCESS_TOKEN` — optional GitHub MCP override; defaults to `gh auth token`.
- `GONG_ACCESS_KEY` — required by the Gong MCP; delivered via shell inheritance.
- `GONG_ACCESS_KEY_SECRET` — required by the Gong MCP; delivered via shell inheritance.
- `MS365_MCP_CLIENT_ID` — optional for the Microsoft 365 MCP (multi-tenant app registrations only); delivered via shell inheritance.
- `MS365_MCP_TENANT_ID` — optional for the Microsoft 365 MCP (multi-tenant app registrations only); delivered via shell inheritance.

Linear and Salesforce deliberately surface no env vars — Linear uses OAuth 2.1 via Cursor's MCP UI on first connect; Salesforce uses the `sf` CLI session file under `~/.sf/` after a one-time `sf org login web` invocation. Placeholder-MCP variables in `.env.example` are illustrative `(TBD)` markers; each one will be reconciled with the real credential surface when its server is flipped to active.

## Flipping a placeholder to active

The flip-to-active operation is a predictable five-step edit documented in `.cursor/mcp.placeholders.md` § `Conventions`. Story 4.4 does NOT flip any placeholder; the flip is out of scope. The canonical steps are:

1. Copy the fenced JSON object's inner contents from `.cursor/mcp.placeholders.md` into `.cursor/mcp.json` under `mcpServers`. Replace any `TBD:` prefix on the npm package or URL with the real value.
2. Delete the corresponding H2 block from `.cursor/mcp.placeholders.md` so the placeholder catalog no longer double-counts the server.
3. Add a matching H2 section to `.cursor/mcp.README.md` documenting Purpose, Transport, Auth, Required env vars, and Wiring link in the same shape used by the existing five active servers.
4. Update `.env.example` — flip the commented `# VAR=` declarations to bare `VAR=` form if the env vars are required, or keep them commented if optional. Update the section's `# status:` line from `placeholder` to `active` or `active-no-env`.
5. Update `docs/mcps.md` — flip the catalog-table row's `Status` column, promote the bullet from `## Placeholder MCPs` to `## Active MCPs`, and refresh the `Env vars` column to drop the `(TBD)` markers.

Future stories in Epic 5 and beyond will exercise this playbook — for example when `vixxonow`, `vixxolink`, or `gateway` get their real endpoints, or when the `introspection` MCP is wired from `github:vixxo-copilot/agent-skills#introspection` to a pinned release. The companion `vixxo-copilot/agent-skills` skills registry is the canonical skill-bundle source referenced throughout this catalog and in `docs/setup.md`.

## Skill-based tools (not MCP)

Some integrations are **not** MCP servers. They use agent skills, local scripts,
and `.env` credentials instead of `.cursor/mcp.json` wiring.

| Tool | Status | Env vars | Skill / docs |
| --- | --- | --- | --- |
| polyai | active-skill | `POLYAI_API_KEY`, `POLYAI_REGION`, `POLYAI_ACCOUNT_ID`, `POLYAI_PROJECT_ID` | `.agents/skills/polyai/` — see also `polyai-vixxo-bridge` for Studio MCP wiring |

PolyAI does not appear in Cursor Settings → Tools & MCP. Use skill `polyai` in
chat (e.g. "Use polyai — run health check"). Full setup: `.cursor/mcp.README.md`
§ `Skill-based tools (not MCP)`.

<!-- Why: canonical catalog of every MCP the assistants-template ships (five active + eleven placeholder) per Epic 4 Story 4.4 AC3; cross-links .cursor/mcp.README.md (Story 4.1), .cursor/mcp.placeholders.md (Story 4.2), .env.example (Story 4.3), and docs/setup.md (Story 4.4). -->
