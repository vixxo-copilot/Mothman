# Story 5.2 Baseline Audit

Date: 2026-04-21
Story: `5-2-wizard-prompts-and-file-generation`
Scope: establish pre-change fingerprints and lock deterministic implementation inputs for prompt flow and generated outputs.

## Baseline targets reviewed

- `bin/init`
- `package.json`
- `memory/me/identity.md`
- `agents/personas/work.md`
- `.env.example`
- `docs/setup.md`
- `docs/mcps.md`

## Pre-change SHA-256 fingerprints

- `bin/init` — `684b7a243806340929999a632a640d033b3606b57a8df44ec23231cdf9a8035d`
- `package.json` — `90627f8024998141107eceab2da5e7016527c976c359bcecb552bef5eb2426ef`
- `memory/me/identity.md` — `19218e21611820113c1bf28fcc54d625475af8389075933d61ad427e89770dbc`
- `agents/personas/work.md` — `810d9cc25ba11de8fe82918b962812b16dac82d4dcbe02aa83c5d0d1b0d6bb2e`
- `.env.example` — `19f9c52047f821f814dfe3b200f0fb77f641d1b373499691f445f8c83d4ed6a4`
- `docs/setup.md` — `ddce66f02d496e6d5fcd9ed8c53bbca633b9f10772ee2e956b7cb3124ec27276`
- `docs/mcps.md` — `7b2a16f84fa1b087a0efcc08e72508ce834ef6820317e03485066de3d92668d6`

## Superseded scaffolds (Story 2.3 and Story 3.3)

### `agents/personas/work.md` (Story 2.3 scaffold)

- Current file is placeholder-driven (`{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}`).
- Story 5.2 intentionally replaces those placeholders with concrete wizard answers.
- Body discipline to preserve:
  - work-only scope wording
  - Active MCP table entries (`Linear`, `GitHub`, `Microsoft 365`, `Salesforce`, `Gong`)
  - Context-files section references

### `memory/me/identity.md` (Story 3.3 scaffold)

- Current file is placeholder-driven (`{{employee_name}}`, `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}`, `{{employee_email}}`).
- Story 5.2 intentionally replaces those placeholders with concrete wizard answers and adds Optional MCP capture.
- Work-scope invariants to preserve:
  - `scope: work`
  - work-only narrative in body
  - no personal-context language

## Unchanged artifacts requirement

The following files remain byte-stable during Story 5.2 implementation:

- `.env.example`
- `docs/setup.md`
- `docs/mcps.md`

These are read-only sources for copy behavior and canonical MCP option ordering.

## Prompt source inventory

### Prompt transport and runtime

- Runtime remains CommonJS (`package.json` type is `commonjs`).
- `prompts@2.4.2` is already pinned and available in root dependencies.
- `bin/init` currently has first-run `npm install` bootstrap and `--help` / `--version` fast-path behavior to preserve.

### Canonical optional-MCP source list (from `docs/mcps.md` table order)

1. `linear`
2. `github`
3. `microsoft-365`
4. `salesforce`
5. `gong`
6. `freshdesk`
7. `dynamics`
8. `vixxonow`
9. `vixxolink`
10. `gateway`
11. `zoominfo`
12. `hubspot`
13. `aws-connect`
14. `chatfpt`
15. `elastic`
16. `introspection`

## Deterministic mapping policy lock

Story 5.2 prompts only collect `name`, `email`, and `role/title`; `department` and `manager` are derived deterministically:

- Department mapping is keyword-based on normalized role/title:
  - engineering keywords -> `Engineering`
  - product keywords -> `Product`
  - design keywords -> `Design`
  - sales keywords -> `Sales`
  - marketing keywords -> `Marketing`
  - operations keywords -> `Operations`
  - finance keywords -> `Finance`
  - people/hr keywords -> `People`
  - fallback -> `General`
- Manager policy: always derive placeholder text from department:
  - `<Department> Manager (TBD)`

Rationale: deterministic and work-only while staying inside Story 5.2 prompt scope (no manager prompt yet).

## `.env` overwrite flow baseline

- `.env.example` exists and is tracked.
- `.env` copy semantics for Story 5.2:
  - create `.env` from `.env.example` when missing
  - if `.env` exists, explicit confirm prompt defaults to keep existing (`no overwrite`)
  - `.env.example` content remains unchanged

## Story 5.1 compatibility baseline

- `./bin/init --help` and `./bin/init --version` currently exit without running default scaffold flow.
- Dependency bootstrap (`npm install` when `node_modules/prompts/package.json` missing) is already implemented and must remain.
- Story 5.2 replaces the default scaffold banner output path with prompt wizard behavior; this is expected and in-scope.

## Source URLs

- `https://www.npmjs.com/package/prompts`
- `https://nodejs.org/api/fs.html`
