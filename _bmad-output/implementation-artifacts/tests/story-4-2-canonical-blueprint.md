# Story 4.2 Canonical Blueprint

Task 2 evidence artifact. Locks the byte-stable shape of
`.cursor/mcp.placeholders.md` (frontmatter, body section order, per-server H2
template, per-server content) and the byte-stable shape of the Story 4.2
validation harness constants (banned-term regex, secret-pattern catalog,
Derek fixed-string probes, placeholder-form probes, deny-list cross-reference,
evidence constants). Captured 2026-04-21.

## Frontmatter lock

`.cursor/mcp.placeholders.md` begins with the following YAML frontmatter block
(bracketed by `---` / `---` on their own lines). Keys appear in canonical order:
`type`, `scope`, `created`, `updated`, `tags`.

```yaml
---
type: mcp-placeholders
scope: work
created: 2026-04-21
updated: 2026-04-21
tags: [mcp, work, placeholder]
---
```

## Body section order lock

The body below the closing `---` of the frontmatter contains, in order:

1. H1 heading: `# Pending MCPs (.cursor/mcp.placeholders.md)`
2. Preamble paragraph — four sentences stating (a) this is the Story 4.2
   placeholder companion for `.cursor/mcp.json`, (b) each entry ships as
   markdown with a fenced `json` code block showing the intended canonical
   wiring shape and a trailing `// TODO:` markdown line, (c) none of the
   entries are wired — `.cursor/mcp.json` remains the single source of truth
   for active MCPs, (d) flipping a pending MCP to active is done by copying the
   fenced JSON block into `.cursor/mcp.json`, removing the `// TODO` line, and
   adding the server's documentation to `.cursor/mcp.README.md`.
3. Eleven per-server H2 sections in canonical order:
   `## Freshdesk → ## Dynamics → ## VixxoNow → ## VixxoLink → ## Gateway → ## ZoomInfo → ## HubSpot → ## AWS Connect → ## ChatFPT → ## Elastic → ## agent-skills Introspection MCP`
4. `## Conventions` H2
5. `## Forward References` H2
6. HTML-comment terminator on the last non-blank line:
   `<!-- Why: strict JSON forbids comments; this file is the Story 4.2 pending-MCP companion to .cursor/mcp.json per Epic 4 Story 4.2 AC1. -->`

**Thirteen H2 sections total.** `grep -c '^## ' .cursor/mcp.placeholders.md`
MUST return `13`. Absence of any additional H2 section is enforced by the
harness equality check.

## Per-server H2 template lock

Each of the eleven pending-MCP H2 sections follows this exact shape:

```
## <Server Display Name>

**Purpose:** <one-sentence purpose>
**Status:** placeholder — not wired
**Intended transport:** <remote URL (HTTP) | local stdio>
**Wiring reference:** <https-URL | Linear-URL | TODO: descriptive phrase>

```json
{
  "<server-key>": {
    "<shape-specific fields>": "..."
  }
}
```

// TODO: wiring; see <wiring-reference-token>

```

Five required `**Field:**` markers per section: `**Purpose:**`, `**Status:**
placeholder — not wired` (literal fixed form), `**Intended transport:**`,
`**Wiring reference:**`. One fenced ` ```json ` block immediately after the
fields. One `// TODO: wiring; see <…>` markdown line immediately after the
fenced block's closing ` ``` `. One blank line before the next H2.

Counts asserted by the harness (`check_task4`):

- `grep -c '^\*\*Status:\*\* placeholder — not wired$' .cursor/mcp.placeholders.md` → `11`
- `grep -c '^// TODO: wiring; see ' .cursor/mcp.placeholders.md` → `11`
- `grep -c '^```json$' .cursor/mcp.placeholders.md` → `11`

## Per-server content locks

Values below are the canonical whitespace-normalized per-server content. The
blueprint is the authoritative source; any AC4 deviation fails harness
`check_task4`. Each fenced JSON block uses 2-space indentation and mirrors the
Story 4.1 AC3 shape locks: remote `{ "url": "…" }` OR stdio
`{ "command": "…", "args": [ … ] }`. ZERO `env` blocks.

### Freshdesk (stdio)

- **Purpose:** `Customer support ticket management (tickets, contacts, dispatch)`
- **Intended transport:** `local stdio`
- **Wiring reference:** `TODO: Vixxo internal wiki — Freshdesk MCP onboarding`
- **Sample shape (top-level key `freshdesk`):**
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
- **TODO line:** `// TODO: wiring; see TODO: Vixxo internal wiki — Freshdesk MCP onboarding`

### Dynamics (stdio)

- **Purpose:** `Microsoft Dynamics 365 CRM and ERP data (accounts, opportunities, orders)`
- **Intended transport:** `local stdio`
- **Wiring reference:** `TODO: Vixxo internal wiki — Dynamics 365 MCP onboarding`
- **Sample shape (top-level key `dynamics`):**
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
- **TODO line:** `// TODO: wiring; see TODO: Vixxo internal wiki — Dynamics 365 MCP onboarding`

### VixxoNow (remote URL)

- **Purpose:** `Vixxo internal service operations platform (work orders, technicians, SLAs)`
- **Intended transport:** `remote URL (HTTP)`
- **Wiring reference:** `TODO: Vixxo internal wiki — VixxoNow MCP endpoint`
- **Sample shape (top-level key `vixxonow`):**
  ```json
  {
    "vixxonow": {
      "url": "TODO://vixxonow.example.internal/mcp"
    }
  }
  ```
- **TODO line:** `// TODO: wiring; see TODO: Vixxo internal wiki — VixxoNow MCP endpoint`

### VixxoLink (remote URL)

- **Purpose:** `Vixxo partner/supplier connectivity portal`
- **Intended transport:** `remote URL (HTTP)`
- **Wiring reference:** `TODO: Vixxo internal wiki — VixxoLink MCP endpoint`
- **Sample shape (top-level key `vixxolink`):**
  ```json
  {
    "vixxolink": {
      "url": "TODO://vixxolink.example.internal/mcp"
    }
  }
  ```
- **TODO line:** `// TODO: wiring; see TODO: Vixxo internal wiki — VixxoLink MCP endpoint`

### Gateway (remote URL)

- **Purpose:** `Vixxo API gateway — aggregated access to internal services`
- **Intended transport:** `remote URL (HTTP)`
- **Wiring reference:** `TODO: Vixxo internal wiki — Gateway MCP endpoint`
- **Sample shape (top-level key `gateway`):**
  ```json
  {
    "gateway": {
      "url": "TODO://gateway.example.internal/mcp"
    }
  }
  ```
- **TODO line:** `// TODO: wiring; see TODO: Vixxo internal wiki — Gateway MCP endpoint`

### ZoomInfo (stdio)

- **Purpose:** `Sales and marketing intelligence (contacts, company firmographics, intent data)`
- **Intended transport:** `local stdio`
- **Wiring reference:** `TODO: Vixxo internal wiki — ZoomInfo MCP onboarding`
- **Sample shape (top-level key `zoominfo`):**
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
- **TODO line:** `// TODO: wiring; see TODO: Vixxo internal wiki — ZoomInfo MCP onboarding`

### HubSpot (remote URL)

- **Purpose:** `Marketing automation, CRM, and customer journey data`
- **Intended transport:** `remote URL (HTTP)`
- **Wiring reference:** `https://developers.hubspot.com/docs/api/overview`
- **Sample shape (top-level key `hubspot`):**
  ```json
  {
    "hubspot": {
      "url": "TODO://api.hubapi.com/mcp"
    }
  }
  ```
- **TODO line:** `// TODO: wiring; see https://developers.hubspot.com/docs/api/overview`

### AWS Connect (stdio)

- **Purpose:** `AWS Contact Center (call metadata, contact flows, agent queues)`
- **Intended transport:** `local stdio`
- **Wiring reference:** `TODO: Vixxo internal wiki — AWS Connect MCP onboarding`
- **Sample shape (top-level key `aws-connect`):**
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
- **TODO line:** `// TODO: wiring; see TODO: Vixxo internal wiki — AWS Connect MCP onboarding`

### ChatFPT (remote URL)

- **Purpose:** `Vixxo internal conversational AI channel (logs, queries, completions)`
- **Intended transport:** `remote URL (HTTP)`
- **Wiring reference:** `TODO: Vixxo internal wiki — ChatFPT MCP endpoint`
- **Sample shape (top-level key `chatfpt`):**
  ```json
  {
    "chatfpt": {
      "url": "TODO://chatfpt.example.internal/mcp"
    }
  }
  ```
- **TODO line:** `// TODO: wiring; see TODO: Vixxo internal wiki — ChatFPT MCP endpoint`

### Elastic (stdio)

- **Purpose:** `Elasticsearch / Elastic Observability — log and metric search`
- **Intended transport:** `local stdio`
- **Wiring reference:** `https://github.com/elastic/mcp-server-elasticsearch`
- **Sample shape (top-level key `elastic`):**
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
- **TODO line:** `// TODO: wiring; see https://github.com/elastic/mcp-server-elasticsearch`

### agent-skills Introspection MCP (stdio)

- **Purpose:** `Introspection MCP from the companion vixxo-copilot/agent-skills repo — surfaces skill metadata, registry status, static-browser state to the agent`
- **Intended transport:** `local stdio`
- **Wiring reference:** `https://github.com/vixxo-copilot/agent-skills`
- **Sample shape (top-level key `introspection`):**
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
- **TODO line:** `// TODO: wiring; see https://github.com/vixxo-copilot/agent-skills`

The H2 heading `## agent-skills Introspection MCP` is deliberate prose form; the
JSON-block top-level key `introspection` follows the JSON-key convention AND
matches the existing Story 4.1 `DENY_LIST_SERVER_KEYS` entry. The key is NOT
`agent-skills-introspection` or `introspection-mcp`.

## Conventions body lock (`## Conventions`)

The `## Conventions` H2 contains:

1. Numbered list (five items) of the per-entry field order lock:
   (1) `**Purpose:**`, (2) `**Status:** placeholder — not wired`,
   (3) `**Intended transport:**`, (4) `**Wiring reference:**`,
   (5) fenced ` ```json ` block + `// TODO: wiring; see …` markdown line.
2. Bullet — `.cursor/mcp.json` is strict JSON; Story 4.2 MUST NOT modify it
   (Story 4.1 invariance; see AC6).
3. Bullet — every fenced JSON block MUST use one of the two Story 4.1 AC3
   shapes (remote `{ "url": "…" }` or stdio `{ "command": "…", "args": [ … ] }`)
   and MUST NOT contain an `env` block.
4. Bullet — flipping a pending MCP to active is a three-step operation
   (copy fenced JSON into `.cursor/mcp.json` under `mcpServers`, delete the
   entry's H2 block from `.cursor/mcp.placeholders.md`, add the corresponding
   H2 section to `.cursor/mcp.README.md`) — scope of a future story, not
   Story 4.2.
5. Bullet — this file is descriptive documentation; ZERO placeholder-form
   tokens of the shapes `{{…}}`, `{name}`, `<name>`, `%name%`, `${name}`
   (inherited from Story 4.1 README forbidden-form lock; the `<!-- Why: … -->`
   HTML comment and `<https://…>` bracketed URLs are legitimate content and
   excluded by the same harness probes as Story 4.1).

## Forward References body lock (`## Forward References`)

The `## Forward References` H2 contains three bullets:

- Story 4.3 — `.env.example` `status: placeholder` sections inherit the eleven
  pending-MCP names from this file.
- Story 4.4 — `docs/mcps.md` catalog table inherits the eleven pending-MCP
  names and their intended transports from this file.
- Epic 5 Story 5.3 — `bin/init` wizard SKIPS every placeholder entry (only
  active MCPs from `.cursor/mcp.json` are health-checked; placeholders are
  descriptive documentation, not runnable).

## Banned-term lock (inherited verbatim)

Seventeen-token boundary-guarded regex inherited from Stories 3.1 / 3.2 / 3.3 /
4.1. Zero tokens added; zero tokens removed:

```
(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])
```

Applied case-insensitively (`grep -iE`) to `sanitize_for_banned_scan()`-filtered
contents of `.cursor/mcp.placeholders.md`. The pre-filter replaces
`GITHUB_PERSONAL_ACCESS_TOKEN` → `__GH_PAT_NAME__` before scanning (defensive —
this file is not expected to reference the GitHub PAT env var, because GitHub
is active, not pending; consistent pre-filter across the harness family).

## Twelve Derek fixed-string probes (inherited verbatim)

`grep -Fi` against `.cursor/mcp.placeholders.md`; zero matches expected per
string:

1. `Chiron`
2. `MasteryLab`
3. `Agile Weekly`
4. `Queen Creek`
5. `Gangplank`
6. `Bodybuilding.com`
7. `Integrum`
8. `Omarchy`
9. `derekneighbors.com`
10. `Playrix`
11. `Laurie`
12. `Deke`

Plus three path-reference probes (`/Users/`, `Public/gtd-life`, `@gmail.com`).

## Secret-pattern catalog lock (inherited verbatim)

Eleven POSIX ERE regexes (case-sensitive). Applied against
`.cursor/mcp.placeholders.md`. Zero matches expected per pattern:

1. `sk-[A-Za-z0-9_-]{20,}`
2. `ghp_[A-Za-z0-9]{20,}`
3. `gho_[A-Za-z0-9]{20,}`
4. `ghs_[A-Za-z0-9]{20,}`
5. `github_pat_[A-Za-z0-9_]{20,}`
6. `xox[baprs]-[A-Za-z0-9-]{10,}`
7. `eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}`
8. `Bearer [A-Za-z0-9_.-]{20,}`
9. `AKIA[0-9A-Z]{16}`
10. `AIza[A-Za-z0-9_-]{35}`
11. `[A-Fa-f0-9]{32,}`

Plus `password=`, `token=`, `secret=`, `api_key=` literal-substring scans. Plus
the `${VAR}` / `$VAR` shell-expansion-token scan. Plus the per-fenced-block
`env`-block-absence assertion (enforced in `check_task5` via `python3 -c`
iteration over each extracted object's `.values()`).

## Placeholder-form probes (inherited verbatim)

Applied to `.cursor/mcp.placeholders.md`; zero matches expected per form:

- `\{\{[^}]+\}\}` — double-brace `{{name}}` (reserved for `memory/me/identity.md`).
- `\{[A-Za-z_][A-Za-z0-9_]*\}` — single-brace identifier-only `{name}` (JSON object
  literals `{"url": "…"}` do NOT match this form because the key is quoted).
- `<[A-Za-z_][A-Za-z0-9_]*>` — angle-bracket identifier-only `<name>` (HTML
  comments `<!-- … -->` and bracketed URL forms `<https://…>` do NOT match).
- `%[A-Za-z_][A-Za-z0-9_]*%` — percent-wrapped `%name%`.
- `\$\{[A-Za-z_][A-Za-z0-9_]*\}` — dollar-brace `${name}` (banned everywhere in
  this family per Story 4.1 AC4 `${VAR}` rule).

The `TODO:` literal prefix in Wiring-reference values and the `TODO://` URL
scheme in remote-shape sample URLs are NOT placeholder tokens — they are
literal content and do not match any of the five probes above.

## Deny-list cross-reference (Story 4.1)

Invariant: every `EXPECTED_PLACEHOLDER_KEYS` entry appears in the Story 4.1
`DENY_LIST_SERVER_KEYS` array. Verified in the baseline audit's cross-reference
table. The Story 4.2 harness re-runs the Story 4.1 deny-list check as part of
`check_task9` regression. Story 4.2 never edits the Story 4.1 harness or its
deny-list array.

## Evidence constants for Task 5 harness

- `EXPECTED_PLACEHOLDER_KEYS=( freshdesk dynamics vixxonow vixxolink gateway zoominfo hubspot aws-connect chatfpt elastic introspection )` — eleven keys, canonical order.
- `EXPECTED_H2_HEADINGS=( "## Freshdesk" "## Dynamics" "## VixxoNow" "## VixxoLink" "## Gateway" "## ZoomInfo" "## HubSpot" "## AWS Connect" "## ChatFPT" "## Elastic" "## agent-skills Introspection MCP" "## Conventions" "## Forward References" )` — thirteen headings, canonical order.
- `EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 )` — eleven-element vector; eleventh is Story 4.1 (10 `^PASS:` lines per Story 4.1 harness header). **Empirically verified 2026-04-21 — matches.**
- `STORY_4_1_MCP_JSON_SHA256="d749b788efa974330d104875a5b63793253a40b450f70341da971a403ac3477c"` (from Task 1 baseline; 787 bytes on-disk).
- `STORY_4_1_MCP_README_SHA256="4f27217a93f71b5bc45b0e4055a4ab82b1d052b2f346277b2dd945d89150af09"` (from Task 1 baseline; 9007 bytes on-disk).
- `STORY_1_1_GITIGNORE_SHA256="49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1"` (matches Story 4.1 handoff fingerprint exactly).

## Inheritance-only note

Story 4.2 adds ZERO new banned-term tokens, ZERO new Derek fixed-string probes,
ZERO new secret-pattern regexes, ZERO new placeholder-form probes. Every
catalog carries over from Stories 3.1 / 3.2 / 3.3 / 4.1 unchanged. The Story
4.2 harness re-references each catalog verbatim.

<!-- Why: Task 2 evidence artifact. Locks the byte-stable shape of .cursor/mcp.placeholders.md and the Story 4.2 harness constants; every AC4 per-server content value, every AC5 conventions-body bullet, and every AC8 harness gate consumes this blueprint as its single source of truth. -->
