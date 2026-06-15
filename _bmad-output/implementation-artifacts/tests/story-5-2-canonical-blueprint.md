# Story 5.2 Canonical Blueprint

Date: 2026-04-21
Story: `5-2-wizard-prompts-and-file-generation`
Scope: canonical implementation contract for `bin/init` prompt orchestration, deterministic rendering, safe writes, and deterministic test mode.

## Inheritance-only note

- Reuse Story 5.1 fast paths and bootstrap semantics.
- Do not run Story 5.3 responsibilities (`npx skills add ...`, MCP health checks).
- Keep CommonJS and Node-only execution.

## Prompt schema lock

Prompt order (hard lock):

1. `employeeName` (text, required, trimmed, non-empty)
2. `employeeEmail` (text, required, trimmed, basic email validation)
3. `employeeRole` (text, required, trimmed, non-empty)
4. `optionalMcps` (multiselect, source list locked to `docs/mcps.md` table order)
5. `overwriteEnv` (confirm; asked only if `.env` exists; default `false`)

Prompt wording rules:

- Work-only labels/help text.
- No Derek/PII carryover tokens.
- Validation must use `prompts` `validate` callbacks (return `true` or message).

## Cancel behavior lock

- Use `onCancel` handler.
- On cancellation (`esc`, `ctrl+c`, `ctrl+d`, or injected `Error`), exit non-zero.
- Emit concise stderr guidance including `re-run ./bin/init`.
- No writes occur before prompt completion and cancellation check.

## Canonical optional-MCP list lock

Derived from `docs/mcps.md` first column in table order:

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

## Normalization lock

- `employeeName`: trim + collapse internal whitespace.
- `employeeRole`: trim + collapse internal whitespace.
- `employeeEmail`: trim + lowercase.
- `optionalMcps`: unique list in canonical order.
- All generated outputs: UTF-8, LF-only, trailing newline.

## Department mapping lock

From normalized `employeeRole` (lowercase keyword scan):

- any of `engineer`, `developer`, `architect`, `qa`, `sre`, `devops` -> `Engineering`
- any of `product`, `pm` -> `Product`
- any of `design`, `ux`, `ui` -> `Design`
- any of `sales`, `account executive`, `business development` -> `Sales`
- any of `marketing`, `growth` -> `Marketing`
- any of `operations`, `ops` -> `Operations`
- any of `finance`, `accounting` -> `Finance`
- any of `hr`, `people`, `talent` -> `People`
- else -> `General`

## Manager placeholder policy lock

No manager prompt in Story 5.2. Derive deterministic placeholder:

- `manager = "<Department> Manager (TBD)"`

## Identity renderer blueprint (`memory/me/identity.md`)

- Frontmatter keys include:
  - `type: identity`
  - `scope: work`
  - `name`, `role`, `department`, `manager`, `email`
  - `created: YYYY-MM-DD`
  - `updated: YYYY-MM-DD`
  - `tags: [identity, work]`
- Body must remain work-only.
- Include `## Optional MCPs` section:
  - bullet list of selected keys in canonical order, or
  - line `none selected` when empty.

## Work persona renderer blueprint (`agents/personas/work.md`)

- Frontmatter keys include:
  - `type: persona`
  - `scope: work`
  - `role`, `department`, `name`, `manager`
  - `tags: [persona, work, vixxo]`
- Body remains work-scoped.
- Preserve Active MCP table discipline from Story 2.3:
  - `Linear`, `GitHub`, `Microsoft 365`, `Salesforce`, `Gong`
- No unresolved `{{employee_*}}` tokens for answered fields.

## Safe write and path-guard blueprint

- Implement `writeAtomic(targetPath, content)`:
  - resolve target relative to repo root
  - verify resolved path remains under repo root
  - write temp file in same destination directory
  - `rename` temp -> target
- Serialize writes to same target path.
- Use same helper for:
  - `memory/me/identity.md`
  - `agents/personas/work.md`
  - `.env` copy materialization

## `.env` copy decision flow lock

- if `.env` missing: copy from `.env.example` with atomic write.
- if `.env` exists:
  - ask `overwriteEnv` confirm prompt (default `false`)
  - `false`: skip `.env`
  - `true`: overwrite via atomic write.
- never mutate `.env.example`.

## Deterministic non-interactive mode lock

- Opt-in only through environment flag:
  - fixture path env var points to JSON payload.
- Validate payload shape before use:
  - object with `responses` array.
- Apply `prompts.inject(...)` from fixture.
- Support cancellation simulation:
  - fixture token object `{ "type": "error", "message": "..." }` maps to injected `Error`.

## Validation harness blueprint

Create executable script:

- `_bmad-output/implementation-artifacts/tests/story-5-2-wizard-prompts-and-file-generation-validation.sh`

Gate pattern:

- `task1`: baseline-audit artifact integrity
- `task2`: canonical-blueprint artifact integrity
- `task3`: prompt schema wiring and fast-path behavior
- `task4`: cancellation path with zero side effects
- `task5`: deterministic rendering + atomic writes + path safety
- `task6`: `.env` copy semantics (missing/create + existing/confirm)
- `task7`: no-scope-creep guard (no Story 5.3 behavior)
- `task8`: superseded Story 2.3/3.3 compatibility checks
- `task9`: unaffected predecessor harness regression sweep
- `all`: `task1..task9` sequentially + final `PASS: all`

Expected predecessor regression set (unchanged):

- Stories `1.1`, `1.2`, `1.3`, `2.1`, `2.2`, `2.4`, `3.1`, `3.2`, `4.1`, `4.2`, `4.3`, `4.4`

Superseded checks to replace in Story 5.2 harness:

- Story 2.3/3.3 placeholder-presence assertions become compatibility shape/scope checks against generated concrete outputs.

## Evidence outputs lock

Task 7 handoff package must include:

- Story 5.2 harness `all` transcript.
- predecessor regression pass vector.
- checksums for modified files and byte-stability anchors.
- AC-to-evidence map with forward notes for Story 5.3 boundary.
