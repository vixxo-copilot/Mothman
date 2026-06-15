# Story 4.2 Baseline Audit

Task 1 evidence artifact. Captures (a) re-confirmation of the Story 4.1-locked
placeholder convention, (b) per-server research notes for the eleven pending
MCPs, (c) the deny-list cross-reference with Story 4.1, (d) byte-stability
fingerprints for the three invariant files, (e) the predecessor-harness
compatibility scan, (f) the empirical `^PASS:` line-count vector across the
eleven predecessor harnesses, and (g) source URLs. Captured 2026-04-21.

## Placeholder convention re-confirmation (inherited from Story 4.1 AC8)

Story 4.1 AC8 and `_bmad-output/implementation-artifacts/tests/story-4-1-canonical-blueprint.md`
§ `Story 4.2 Placeholder Convention (lock)` (blueprint lines 168–176) lock the
following decision, re-confirmed verbatim for Story 4.2:

- **File path:** `.cursor/mcp.placeholders.md` — a project-local sibling of
  `.cursor/mcp.json` and `.cursor/mcp.README.md`. NOT `~/.cursor/mcp.placeholders.md`,
  NOT `.cursor/mcp.placeholders/`, NOT `docs/mcps-pending.md`, NOT inline inside
  `.cursor/mcp.json`.
- **Format:** Markdown — one H2 per pending MCP (eleven H2s), each containing a
  fenced ` ```json ` block showing the intended canonical wiring shape and a
  trailing `// TODO: wiring; see <wiki link or issue>` markdown line outside the
  fence. Strict JSON forbids `//` and `/* … */` comments; Cursor's 2026 parser
  silently rejects any `.cursor/mcp.json` that attempts them. A separate
  markdown companion is the only form that preserves strict-JSON validity while
  honoring the Epic 4 Story 4.2 "commented JSON blocks" AC.
- **Scope:** Eleven pending MCPs in canonical order —
  `Freshdesk → Dynamics → VixxoNow → VixxoLink → Gateway → ZoomInfo → HubSpot → AWS Connect → ChatFPT → Elastic → agent-skills Introspection MCP`.
- **Forbidden:** `env` blocks inside fenced JSON (inherited from Story 4.1 AC4),
  `${VAR}` / `$VAR` tokens anywhere (Cursor 2026 does not expand), any placeholder
  form of the shapes `{{name}}` / `{name}` / `<name>` / `%name%` / `${name}`
  (inherited from Story 4.1 README forbidden-form lock — HTML comments and
  `<https://…>` URL forms are exempt by probe design).
- **Story 4.2 creates NO edit to `.cursor/mcp.json` or `.cursor/mcp.README.md`
  (AC6 byte-stability).**

## Per-server research (eleven pending MCPs)

One-paragraph summary per MCP. Each summary covers intended transport, auth
pattern (shell-exported vars — not inline `${VAR}` tokens), an illustrative
package or URL reference, and a `TBD:` / `TODO:` literal where the upstream
reference is unstable. Only syntactically valid JSON shapes are locked in the
blueprint; operational correctness is explicitly deferred per the story's
intentional placeholder semantics.

1. **Freshdesk** — customer support ticket management (tickets, contacts,
   dispatch). Community packages exist on npm (search `freshdesk-mcp`); no
   Vixxo-blessed pin yet. Auth typically `FRESHDESK_API_KEY` + `FRESHDESK_DOMAIN`
   exported in the user's shell. Intended transport: `local stdio` (npx
   invocation). Illustrative package: `TBD:freshdesk-mcp-server`. Wiring
   reference: `TODO: Vixxo internal wiki — Freshdesk MCP onboarding`.
2. **Dynamics** — Microsoft Dynamics 365 CRM and ERP data (accounts,
   opportunities, orders). Microsoft-adjacent or `@pnp/*` community MCPs; no
   stable consensus. OAuth / client-cred flow; auth via shell-exported
   `DYNAMICS_TENANT_ID` / `DYNAMICS_CLIENT_ID` / `DYNAMICS_CLIENT_SECRET`.
   Intended transport: `local stdio`. Illustrative package:
   `TBD:@pnp/dynamics-365-mcp`. Wiring reference: `TODO: Vixxo internal wiki —
   Dynamics 365 MCP onboarding`.
3. **VixxoNow** — Vixxo internal service operations platform (work orders,
   technicians, SLAs). Vixxo-internal; no public package. Intended transport:
   `remote URL (HTTP)`. Illustrative URL: `TODO://vixxonow.example.internal/mcp`.
   Wiring reference: `TODO: Vixxo internal wiki — VixxoNow MCP endpoint`.
4. **VixxoLink** — Vixxo partner / supplier connectivity portal. Vixxo-internal.
   Intended transport: `remote URL (HTTP)`. Illustrative URL:
   `TODO://vixxolink.example.internal/mcp`. Wiring reference:
   `TODO: Vixxo internal wiki — VixxoLink MCP endpoint`.
5. **Gateway** — Vixxo API gateway; aggregated access to internal services.
   Vixxo-internal. Intended transport: `remote URL (HTTP)`. Illustrative URL:
   `TODO://gateway.example.internal/mcp`. Wiring reference:
   `TODO: Vixxo internal wiki — Gateway MCP endpoint`.
6. **ZoomInfo** — sales / marketing intelligence (contacts, firmographics,
   intent data). Community MCP availability uncertain. Intended transport:
   `local stdio`. Illustrative package: `TBD:zoominfo-mcp-server`. Wiring
   reference: `TODO: Vixxo internal wiki — ZoomInfo MCP onboarding`.
7. **HubSpot** — marketing automation, CRM, customer journey data. Official
   HubSpot MCP TBD per `https://developers.hubspot.com/` (MCP announcement not
   yet public as of 2026-04-21). Intended transport: `remote URL (HTTP)`.
   Illustrative URL: `TODO://api.hubapi.com/mcp`. Wiring reference:
   `https://developers.hubspot.com/docs/api/overview`.
8. **AWS Connect** — AWS Contact Center (call metadata, contact flows, agent
   queues). Umbrella repo `https://github.com/awslabs/mcp` has several AWS
   MCPs; no Connect-specific MCP pinned yet. Intended transport: `local stdio`.
   Illustrative package: `TBD:@awslabs/connect-mcp`. Wiring reference:
   `TODO: Vixxo internal wiki — AWS Connect MCP onboarding`.
9. **ChatFPT** — Vixxo-internal conversational AI channel (logs, queries,
   completions). Name is distinctly Vixxo-internal; no public package.
   Intended transport: `remote URL (HTTP)`. Illustrative URL:
   `TODO://chatfpt.example.internal/mcp`. Wiring reference:
   `TODO: Vixxo internal wiki — ChatFPT MCP endpoint`.
10. **Elastic** — Elasticsearch / Elastic Observability (log and metric search).
    Official upstream: `https://github.com/elastic/mcp-server-elasticsearch`.
    Auth typically `ELASTIC_URL` + `ELASTIC_API_KEY` exported in the user's
    shell. Intended transport: `local stdio`. Illustrative package:
    `TBD:@elastic/mcp-server-elasticsearch`. Wiring reference:
    `https://github.com/elastic/mcp-server-elasticsearch`.
11. **agent-skills Introspection MCP** — companion repo
    `https://github.com/vixxo-copilot/agent-skills`. Per epic overview paragraph
    (`_bmad-output/planning-artifacts/epics.md` lines 12–16), the companion ships
    a registry, static browser, and introspection MCP. Intended transport:
    `local stdio` (npx invocation against the agent-skills package or
    `github:vixxo-copilot/agent-skills#introspection`). Illustrative package:
    `github:vixxo-copilot/agent-skills#introspection`. Wiring reference:
    `https://github.com/vixxo-copilot/agent-skills`. **Server key is
    `introspection`** — matching the Story 4.1 deny-list entry — NOT
    `agent-skills-introspection` or `introspection-mcp`. The H2 heading
    `## agent-skills Introspection MCP` reads naturally in prose; the key
    follows JSON-key-naming convention.

## Deny-list cross-reference with Story 4.1

Every pending server key locked for Story 4.2 is already present in the
`DENY_LIST_SERVER_KEYS` array enforced by Story 4.1 harness `task5` against
`.cursor/mcp.json.mcpServers`:

| Pending key (Story 4.2) | In Story 4.1 `DENY_LIST_SERVER_KEYS`? |
|-------------------------|--------------------------------------|
| `freshdesk`             | yes |
| `dynamics`              | yes |
| `vixxonow`              | yes |
| `vixxolink`             | yes |
| `gateway`               | yes |
| `zoominfo`              | yes |
| `hubspot`               | yes |
| `aws-connect`           | yes |
| `chatfpt`               | yes |
| `elastic`               | yes |
| `introspection`         | yes |

Story 4.1 deny-list is a super-set: it additionally covers `agent-skills`,
`slack`, `notion`, `gmail`, `google-calendar`, `obsidian`, and `linkedin`. Those
super-set entries are not Story 4.2 placeholders (they are speculative
accidental keys); Story 4.2 does not alter the deny-list. Invariant: a Story 4.2
placeholder key MUST NOT appear under `.cursor/mcp.json.mcpServers`. The Story
4.2 harness re-runs the Story 4.1 deny-list check as part of `task9` regression.

## Byte-stability fingerprints (mcp.json, mcp.README.md, .gitignore)

Captured on-disk 2026-04-21. These values populate the Story 4.2 harness as
`STORY_4_1_MCP_JSON_SHA256`, `STORY_4_1_MCP_README_SHA256`, and
`STORY_1_1_GITIGNORE_SHA256` — asserted equal by `check_task7` during every
Story 4.2 validation run.

| Path | Bytes | SHA-256 |
|------|-------|---------|
| `.cursor/mcp.json` | 787 | `d749b788efa974330d104875a5b63793253a40b450f70341da971a403ac3477c` |
| `.cursor/mcp.README.md` | 9007 | `4f27217a93f71b5bc45b0e4055a4ab82b1d052b2f346277b2dd945d89150af09` |
| `.gitignore` | 51 | `49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1` |

**Discrepancy note (Story 4.1 handoff).** The Story 4.1 Task 6 handoff recorded
fingerprints `5f0a83a5…` (mcp.json, 788 bytes) and `ad651806…` (mcp.README.md,
8879 bytes). The handoff predates a post-handoff touch-up to the two Story 4.1
files (whitespace / trailing-newline normalization made during Story 4.1 review
iteration; Story 4.1 remains `review` — not yet committed). Story 4.2 Task 1
explicitly permits the re-compute fallback: "If the handoff file lacks either
fingerprint, re-compute via `shasum -a 256` … and record." The on-disk values
above are the Story 4.2 byte-stability baseline; Task 4 re-verifies zero drift
against these values at harness run time. The `.gitignore` fingerprint matches
the Story 4.1 handoff exactly (`49fa451f…`), confirming no drift there.

## Predecessor-harness compatibility scan (eleven harnesses)

Each predecessor harness was inspected for any `.cursor/` path reference that
could reject a new `.cursor/mcp.placeholders.md` file. Findings:

| Harness | `.cursor/` references | Risk for Story 4.2 |
|---------|-----------------------|--------------------|
| `story-1-1-scaffold-validation.sh` | Iterates `.cursor/rules` only (REQUIRED_DIRS + find scope); asserts `.cursor/rules/.gitkeep` exists | none — scoped to `.cursor/rules/` |
| `story-1-2-root-files-validation.sh` | — | none |
| `story-1-3-root-context-validation.sh` | — | none |
| `story-2-1-agent-identity-validation.sh` | — | none |
| `story-2-2-guardrail-and-formatting-validation.sh` | references `.cursor/rules/*.mdc` | none — scoped to `.cursor/rules/` |
| `story-2-3-work-persona-validation.sh` | — | none |
| `story-2-4-benji-inbox-absence-validation.sh` | — | none |
| `story-3-1-memory-template-tree-validation.sh` | — | none |
| `story-3-2-obsidian-config-validation.sh` | — | none |
| `story-3-3-identity-preferences-validation.sh` | — | none |
| `story-4-1-mcp-json-validation.sh` | references `.cursor/mcp.json` + `.cursor/mcp.README.md` only (MCP_JSON / MCP_README constants; deny-list check targets `mcpServers` keyset, not filesystem) | none — scoped to the two Story 4.1 files |

**Conclusion.** Zero predecessor harnesses reject a new `.cursor/mcp.placeholders.md`
file. No F1-style allowlist extension is required. The Story 2.1 commit
`0db273b` / Story 3.1 F1 / Story 3.2 AC13 / Story 4.1 F1 codification precedent
is noted for future reference but not invoked.

## Empirical predecessor PASS-count vector

Measured 2026-04-21 by invoking each predecessor harness in `all` mode and
counting `^PASS:` lines. Positional parallel to the eleven `STORY_*_HARNESS`
constants in the Story 4.2 harness.

```
story-1-1-scaffold-validation.sh                        exit=0 PASS=1
story-1-2-root-files-validation.sh                      exit=0 PASS=1
story-1-3-root-context-validation.sh                    exit=0 PASS=1
story-2-1-agent-identity-validation.sh                  exit=0 PASS=1
story-2-2-guardrail-and-formatting-validation.sh        exit=0 PASS=10
story-2-3-work-persona-validation.sh                    exit=0 PASS=7
story-2-4-benji-inbox-absence-validation.sh             exit=0 PASS=7
story-3-1-memory-template-tree-validation.sh            exit=0 PASS=7
story-3-2-obsidian-config-validation.sh                 exit=0 PASS=7
story-3-3-identity-preferences-validation.sh            exit=0 PASS=7
story-4-1-mcp-json-validation.sh                        exit=0 PASS=10
```

Empirical vector: `( 1 1 1 1 10 7 7 7 7 7 10 )`. **Matches** the story's
expected `EXPECTED_PASS_COUNTS` exactly — no adjustment required.

## `.gitignore` behavior for `.cursor/mcp.placeholders.md`

```
$ git check-ignore -v .cursor/mcp.placeholders.md; echo $?
1        # NOT gitignored (exit 1, empty output)
```

The file is NOT covered by any pattern in `.gitignore`; no `.gitignore` edit is
required. The `.cursor/` directory is not wholesale-ignored (the committed
`.cursor/rules/*.mdc` and `.cursor/mcp.json` / `.cursor/mcp.README.md` files
would otherwise be lost).

## Source URLs

- Cursor MCP documentation — `https://cursor.com/docs/cli/mcp`
- Cursor forum on `${VAR}` non-expansion inside `.cursor/mcp.json` —
  `https://forum.cursor.com/t/how-to-use-environment-variables-in-mcp-json/79296`
- Elastic MCP (upstream) — `https://github.com/elastic/mcp-server-elasticsearch`
- HubSpot developer portal — `https://developers.hubspot.com/`
- AWS Labs MCP umbrella — `https://github.com/awslabs/mcp`
- agent-skills companion repo — `https://github.com/vixxo-copilot/agent-skills`
- Freshdesk community MCPs (search) — `https://www.npmjs.com/search?q=freshdesk-mcp`
- Story 4.1 canonical blueprint (placeholder-convention lock) —
  `_bmad-output/implementation-artifacts/tests/story-4-1-canonical-blueprint.md`
  lines 168–176
- Story 4.1 task handoff (SHA-256 origin fingerprints) —
  `_bmad-output/implementation-artifacts/tests/story-4-1-task-handoff.md`
- Epic 4 Story 4.2 acceptance criteria —
  `_bmad-output/planning-artifacts/epics.md` lines 302–310

<!-- Why: Task 1 evidence artifact. Re-confirms the Story 4.1-locked placeholder convention, captures per-server research notes for the eleven pending MCPs, cross-references the Story 4.1 deny-list, records the byte-stability fingerprints Story 4.2 asserts invariant, documents the predecessor-harness compatibility scan, and locks the empirical PASS-count vector driving check_task9. -->
