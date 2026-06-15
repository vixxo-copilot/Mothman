---
type: mcp-placeholders
scope: work
created: 2026-04-21
updated: 2026-04-21
tags: [mcp, work, placeholder]
---

# Pending MCPs (.cursor/mcp.placeholders.md)

This file is the Story 4.2 placeholder companion for `.cursor/mcp.json`. Each entry below ships as a markdown H2 section with a fenced `json` code block showing the intended canonical wiring shape and a trailing `// TODO:` markdown line outside the fence. None of the entries are wired — `.cursor/mcp.json` remains the single source of truth for active Vixxo MCPs. Flipping a pending MCP to active is done by copying the fenced JSON contents into `.cursor/mcp.json` under `mcpServers`, removing the `// TODO` markdown line, deleting this entry's H2 block from this file, and adding the corresponding H2 section to `.cursor/mcp.README.md`.

## Freshdesk

**Purpose:** Customer support ticket management (tickets, contacts, dispatch).
**Status:** placeholder — not wired
**Intended transport:** local stdio
**Wiring reference:** TODO: Vixxo internal wiki — Freshdesk MCP onboarding

```json
{
  "freshdesk": {
    "command": "npx",
    "args": [
      "-y",
      "TBD:freshdesk-mcp-server"
    ]
  }
}
```

// TODO: wiring; see Vixxo internal wiki — Freshdesk MCP onboarding

## Dynamics

**Purpose:** Microsoft Dynamics 365 CRM and ERP data (accounts, opportunities, orders).
**Status:** placeholder — not wired
**Intended transport:** local stdio
**Wiring reference:** TODO: Vixxo internal wiki — Dynamics 365 MCP onboarding

```json
{
  "dynamics": {
    "command": "npx",
    "args": [
      "-y",
      "TBD:@pnp/dynamics-365-mcp"
    ]
  }
}
```

// TODO: wiring; see Vixxo internal wiki — Dynamics 365 MCP onboarding

## VixxoNow

**Purpose:** Vixxo internal service operations platform (work orders, technicians, SLAs).
**Status:** placeholder — not wired
**Intended transport:** remote URL (HTTP)
**Wiring reference:** TODO: Vixxo internal wiki — VixxoNow MCP endpoint

```json
{
  "vixxonow": {
    "url": "TODO://vixxonow.example.internal/mcp"
  }
}
```

// TODO: wiring; see Vixxo internal wiki — VixxoNow MCP endpoint

## VixxoLink

**Purpose:** Vixxo partner/supplier connectivity portal.
**Status:** placeholder — not wired
**Intended transport:** remote URL (HTTP)
**Wiring reference:** TODO: Vixxo internal wiki — VixxoLink MCP endpoint

```json
{
  "vixxolink": {
    "url": "TODO://vixxolink.example.internal/mcp"
  }
}
```

// TODO: wiring; see Vixxo internal wiki — VixxoLink MCP endpoint

## Gateway

**Purpose:** Vixxo API gateway — aggregated access to internal services.
**Status:** placeholder — not wired
**Intended transport:** remote URL (HTTP)
**Wiring reference:** TODO: Vixxo internal wiki — Gateway MCP endpoint

```json
{
  "gateway": {
    "url": "TODO://gateway.example.internal/mcp"
  }
}
```

// TODO: wiring; see Vixxo internal wiki — Gateway MCP endpoint

## ZoomInfo

**Purpose:** Sales and marketing intelligence (contacts, company firmographics, intent data).
**Status:** placeholder — not wired
**Intended transport:** local stdio
**Wiring reference:** TODO: Vixxo internal wiki — ZoomInfo MCP onboarding

```json
{
  "zoominfo": {
    "command": "npx",
    "args": [
      "-y",
      "TBD:zoominfo-mcp-server"
    ]
  }
}
```

// TODO: wiring; see Vixxo internal wiki — ZoomInfo MCP onboarding

## HubSpot

**Purpose:** Marketing automation, CRM, and customer journey data.
**Status:** placeholder — not wired
**Intended transport:** remote URL (HTTP)
**Wiring reference:** https://developers.hubspot.com/docs/api/overview

```json
{
  "hubspot": {
    "url": "TODO://api.hubapi.com/mcp"
  }
}
```

// TODO: wiring; see https://developers.hubspot.com/docs/api/overview

## AWS Connect

**Purpose:** AWS Contact Center (call metadata, contact flows, agent queues).
**Status:** placeholder — not wired
**Intended transport:** local stdio
**Wiring reference:** TODO: Vixxo internal wiki — AWS Connect MCP onboarding

```json
{
  "aws-connect": {
    "command": "npx",
    "args": [
      "-y",
      "TBD:@awslabs/connect-mcp"
    ]
  }
}
```

// TODO: wiring; see Vixxo internal wiki — AWS Connect MCP onboarding

## ChatFPT

**Purpose:** Vixxo internal conversational AI channel (logs, queries, completions).
**Status:** placeholder — not wired
**Intended transport:** remote URL (HTTP)
**Wiring reference:** TODO: Vixxo internal wiki — ChatFPT MCP endpoint

```json
{
  "chatfpt": {
    "url": "TODO://chatfpt.example.internal/mcp"
  }
}
```

// TODO: wiring; see Vixxo internal wiki — ChatFPT MCP endpoint

## Elastic

**Purpose:** Elasticsearch / Elastic Observability — log and metric search.
**Status:** placeholder — not wired
**Intended transport:** local stdio
**Wiring reference:** https://github.com/elastic/mcp-server-elasticsearch

```json
{
  "elastic": {
    "command": "npx",
    "args": [
      "-y",
      "TBD:@elastic/mcp-server-elasticsearch"
    ]
  }
}
```

// TODO: wiring; see https://github.com/elastic/mcp-server-elasticsearch

## agent-skills Introspection MCP

**Purpose:** Introspection MCP from the companion vixxo-copilot/agent-skills repo — surfaces skill metadata, registry status, static-browser state to the agent.
**Status:** placeholder — not wired
**Intended transport:** local stdio
**Wiring reference:** https://github.com/vixxo-copilot/agent-skills

```json
{
  "introspection": {
    "command": "npx",
    "args": [
      "-y",
      "github:vixxo-copilot/agent-skills#introspection"
    ]
  }
}
```

// TODO: wiring; see https://github.com/vixxo-copilot/agent-skills

## Conventions

Each pending-MCP H2 section follows a fixed five-line discipline. The ordered fields are:

1. `**Purpose:**` — one sentence stating what the MCP does for Vixxo work.
2. `**Status:** placeholder — not wired` — literal fixed form; appears exactly eleven times in this file (once per pending MCP).
3. `**Intended transport:**` — one of two locked values, `remote URL (HTTP)` or `local stdio`.
4. `**Wiring reference:**` — an HTTPS URL, a Vixxo Linear issue URL, or a literal `TODO:` marker followed by a descriptive phrase.
5. A fenced `json` code block showing the intended canonical wiring shape, immediately followed by a single `// TODO: wiring; see ` markdown line on its own line outside the fence.

Additional invariants:

- `.cursor/mcp.json` is strict JSON and MUST NOT be modified by this story; Story 4.1 byte-stability is asserted by the Story 4.2 harness (see AC6). Placeholders live in this file, never inline inside `.cursor/mcp.json`.
- Every fenced JSON block uses one of the two Story 4.1 AC3 shapes — the remote shape with a single `url` string, or the stdio shape with `command` plus `args` — and MUST NOT contain an `env` block. Secrets travel through shell inheritance, interactive auth, or Docker bare-name flags, never through the JSON.
- Flipping a pending MCP to active is a three-step operation: copy the fenced JSON object's inner contents into `.cursor/mcp.json` under `mcpServers`, delete this file's H2 block for that server, and add a matching H2 section to `.cursor/mcp.README.md` documenting Purpose / Transport / Auth / Required env vars / Wiring link. The flip is out of scope for Story 4.2.
- This file is descriptive documentation — not a template. It contains ZERO placeholder tokens of the five discouraged forms inherited from the Story 4.1 README forbidden-form lock: double-curly templating form, single-curly identifier form, angle-bracket identifier form, percent-wrapped Windows-env form, and dollar-curly shell-expansion form. HTML comments (opened with an exclamation-dash-dash marker) and bracketed HTTPS URLs are legitimate content and are excluded by probe design.

## Forward References

- Story 4.3 — `.env.example` will gain `status: placeholder` sections for each of the eleven pending MCPs listed above. Active-MCP sections inherit env vars from `.cursor/mcp.README.md`; placeholder sections inherit names from this file.
- Story 4.4 — `docs/mcps.md` will build a catalog table enumerating active vs. pending MCPs; the pending rows inherit names and intended transports from this file.
- Epic 5 Story 5.3 — the `bin/init` setup wizard will call each active MCP once and report PASS / FAIL per server. Placeholder entries in this file are descriptive documentation; the wizard explicitly SKIPS them.

<!-- Why: strict JSON forbids comments; this file is the Story 4.2 pending-MCP companion to .cursor/mcp.json per Epic 4 Story 4.2 AC1. -->
