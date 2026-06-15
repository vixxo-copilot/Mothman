# Story 4.4 Task Handoff

Date: 2026-04-21
Scope: Final evidence package for Story 4.4 (rewrite `docs/setup.md` + create `docs/mcps.md`); closes Epic 4.

## AC-to-file map

| AC | Proof surface |
| --- | --- |
| AC1 (docs/setup.md frontmatter + H1 + H2 sequence + terminator) | Harness `check_task3` (line-level asserts on lines 1–7, line 9 H1, seven H2 in canonical order, terminator equality) |
| AC2 (docs/setup.md content: prereqs / clone / `npx skills add` / `./bin/init`) | `docs/setup.md` §§ Prerequisites → Troubleshooting; harness `check_task3` skills-registry + `./bin/init` grep asserts; AC5 sub-probes in `check_task5` |
| AC3 (docs/mcps.md frontmatter + H1 + H2 sequence + terminator) | Harness `check_task4` (line-level asserts on lines 1–7, line 9 H1, five H2 in canonical order, terminator equality) |
| AC4 (docs/mcps.md catalog table header + separator + 16 data rows) | Harness `check_task4` (`EXPECTED_TABLE_HEADER` and `EXPECTED_TABLE_SEPARATOR` exact-match grep; pipe-count equality to 18; positional server-key ordering loop over `EXPECTED_SECTION_KEYS`) |
| AC5 (skills-registry refs in both docs) | Harness `check_task3` (`npx skills add vixxo-copilot/agent-skills` literal); `check_task5` (`vixxo-copilot/agent-skills` in both docs; `github:vixxo-copilot/agent-skills` in mcps.md) |
| AC6 (repo-relative paths only; no `/Users/`) | Harness `check_task6` (path-reference probes `/Users/`, `Public/gtd-life`, `@gmail.com` against concatenated sanitized view; zero matches) |
| AC7 (no secrets / banned / Derek / placeholder / shell-expansion) | Harness `check_task6` (eleven secret-pattern regexes; seventeen-token banned regex on sanitized view; twelve Derek fixed strings; four lowercase-literal `…=` probes; five placeholder-form probes; `${VAR}`/`$VAR` expansion probe) |
| AC8 (predecessor artifacts byte-stable) | Harness `check_task7` (six SHA-256 anchors: `.cursor/mcp.json`, `.cursor/mcp.README.md`, `.cursor/mcp.placeholders.md`, `.env.example`, `.gitignore`, `docs/legal/license-vixxo-internal-canonical.md`); plus `check_task9` pre-invocation SHA-256 checks on all thirteen predecessor harnesses |
| AC9 (setup.md is full rewrite; Story 1.2 harness still green) | Harness `check_task9` invokes `story-1-2-root-files-validation.sh all` and asserts `PASS: all` + `^PASS:` count = 1; Story 1.2 harness only checks `docs/setup.md` existence, not content |
| AC10 (new harness exists with 9 gates + `all`) | `story-4-4-setup-and-mcps-docs-validation.sh` exists, `chmod +x`, 10 `^PASS:` lines on success |
| AC11 (thirteen-predecessor regression) | Harness `check_task9` loops thirteen predecessors with `BMAD_REGRESSION_DEPTH=1`; `EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 10 10 )`; retry-on-flake wrapper (up to 3) and `mkdir -p tmp/` defensive pre-creation |
| AC12 (sprint-status flips; epic-4 closes at Phase 3) | `sprint-status.yaml` edit: `4-4-rewrite-setup-and-mcps-docs.status` flipped to `done`; `epic-4.status` flipped from `in-progress` to `done`; `last_updated: 2026-04-21` preserved |
| AC13 (story is additive; no Epic 5/6/7 spill) | File list below — no `bin/init`, no `.github/workflows/`, no `.cursor/rules/*.mdc` edits, no predecessor-artifact edits, no `.gitignore` edits |
| AC14 (epic AC lines 323–333 satisfied) | See "Epic AC trace" section below |

## Full validation command transcript

All fourteen harnesses invoked from repo root via `bash <harness> all`. Each emits `PASS: all` on exit 0. Expected runtimes in comments.

```text
# Story 4.4 own harness (nine gates + all; runtime ~150–200 s due to thirteen-predecessor regression in check_task9)
$ bash _bmad-output/implementation-artifacts/tests/story-4-4-setup-and-mcps-docs-validation.sh all
PASS: task1
PASS: task2
PASS: task3
PASS: task4
PASS: task5
PASS: task6
PASS: task7
PASS: task8
task9 OK: thirteen-predecessor byte-stability + regression verified (SHA-256 + ^PASS: fingerprint)     # stderr
PASS: task9
PASS: all
# exit code: 0
# ^PASS: line count: 10
```

Thirteen predecessor harnesses invoked individually (each with `BMAD_REGRESSION_DEPTH=1` inside Story 4.4 `check_task9`; also invoked standalone here without the depth guard — outer-level invocations where task9 runs its own nested regression). Per-harness `^PASS:` fingerprints:

```text
story-1-1-scaffold-validation.sh                                          →  1 PASS line
story-1-2-root-files-validation.sh                                        →  1 PASS line
story-1-3-root-context-validation.sh                                      →  1 PASS line
story-2-1-agent-identity-validation.sh                                    →  1 PASS line
story-2-2-guardrail-and-formatting-validation.sh                          → 10 PASS lines
story-2-3-work-persona-validation.sh                                      →  7 PASS lines
story-2-4-benji-inbox-absence-validation.sh                               →  7 PASS lines
story-3-1-memory-template-tree-validation.sh                              →  7 PASS lines
story-3-2-obsidian-config-validation.sh                                   →  7 PASS lines
story-3-3-identity-preferences-validation.sh                              →  7 PASS lines
story-4-1-mcp-json-validation.sh                                          → 10 PASS lines
story-4-2-mcp-placeholders-validation.sh                                  → 10 PASS lines
story-4-3-env-example-validation.sh                                       → 10 PASS lines
```

Empirical PASS-count vector `( 1 1 1 1 10 7 7 7 7 7 10 10 10 )` matches `EXPECTED_PASS_COUNTS` exactly.

## Additional verification commands

```text
$ shasum -a 256 .cursor/mcp.json .cursor/mcp.README.md .cursor/mcp.placeholders.md .env.example .gitignore docs/legal/license-vixxo-internal-canonical.md
d749b788efa974330d104875a5b63793253a40b450f70341da971a403ac3477c  .cursor/mcp.json
4f27217a93f71b5bc45b0e4055a4ab82b1d052b2f346277b2dd945d89150af09  .cursor/mcp.README.md
1fd08afbf68f8d97d0110dbdbdcf7b7f289adba0e7c649dcbe80609b395fa010  .cursor/mcp.placeholders.md
19f9c52047f821f814dfe3b200f0fb77f641d1b373499691f445f8c83d4ed6a4  .env.example
49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1  .gitignore
4b1cbb2d7e7ba1629df5913a45df3a43e4dd3f78d0c786262589ea53160193cc  docs/legal/license-vixxo-internal-canonical.md

$ grep -cE '^\|' docs/mcps.md
18

$ grep -c '^## ' docs/setup.md
7

$ grep -c '^## ' docs/mcps.md
5

$ grep -Fq 'npx skills add vixxo-copilot/agent-skills' docs/setup.md && echo match
match

$ grep -Fc 'vixxo-copilot/agent-skills' docs/setup.md
2

$ grep -Fc 'vixxo-copilot/agent-skills' docs/mcps.md
4

$ grep -Fq './bin/init' docs/setup.md && echo match
match

$ git check-ignore .env.example; echo $?
1

$ git check-ignore -v .env
.gitignore:2:.env	.env
```

## New-artifact fingerprints

Captured 2026-04-21 on-disk:

```text
docs/setup.md                                                                     6b14758de020d5199f8c1d766f0f019f94784c68a0508bcbe764485ab0f46daf
docs/mcps.md                                                                      9bee1816365eeab12c0b77a701676eab29e182bde7a01c73fda443f273738c27
_bmad-output/implementation-artifacts/tests/story-4-4-setup-and-mcps-docs-validation.sh  e5a254b4f15ac2903c0fda15a6a832199abcc47c920e5823f997c13c255c0473
```

## Extracted Status / Transport vectors from docs/mcps.md

Extracted via `extract_table_column docs/mcps.md 2` (Status column) and `extract_table_column docs/mcps.md 3` (Transport column), positionally parallel to `EXPECTED_SECTION_KEYS`:

```text
row  key              status           transport
---  ---------------- ---------------- -----------------------
  1  linear           active-no-env    remote URL (HTTP)
  2  github           active           local stdio (docker)
  3  microsoft-365    active           local stdio (npx)
  4  salesforce       active-no-env    local stdio (npx)
  5  gong             active           local stdio (npx)
  6  freshdesk        placeholder      local stdio (intended)
  7  dynamics         placeholder      local stdio (intended)
  8  vixxonow         placeholder      remote URL (HTTP)
  9  vixxolink        placeholder      remote URL (HTTP)
 10  gateway          placeholder      remote URL (HTTP)
 11  zoominfo         placeholder      local stdio (intended)
 12  hubspot          placeholder      remote URL (HTTP)
 13  aws-connect      placeholder      local stdio (intended)
 14  chatfpt          placeholder      remote URL (HTTP)
 15  elastic          placeholder      local stdio (intended)
 16  introspection    placeholder      local stdio (intended)
```

Set-equality vs `.env.example` `# status:` mapping: `active=3`, `active-no-env=2`, `placeholder=11` — confirmed.

Set-equality vs `.env.example` `# Transport:` mapping: `remote URL (HTTP)=6`, `local stdio (docker)=1`, `local stdio (npx)=3`, `local stdio (intended)=6` — confirmed.

## Forward-looking notes

- Epic 5 Story 5.1 (`bin/init` scaffold) consumes `docs/setup.md` § `Run the setup smoke test` as its implementation spec. The manual-fallback checklist (launch Cursor, open MCP UI, issue trivial query per active MCP) becomes the wizard's PASS / FAIL contract.
- Epic 5 Story 5.2 (wizard prompts) runs `cp .env.example .env` and surfaces the three required vars (`GITHUB_PERSONAL_ACCESS_TOKEN`, `GONG_ACCESS_KEY`, `GONG_ACCESS_KEY_SECRET`) plus the two optional Microsoft 365 vars — the same set enumerated in `docs/setup.md` § `Configure credentials`.
- Epic 5 Story 5.3 (wizard verification) enumerates the three required env vars when probing each active MCP. The wizard explicitly SKIPS the eleven placeholder MCPs per `docs/setup.md` § `Review placeholder MCPs` guidance.
- Epic 6 Story 6.1 (PII deny-list config) consumes the same probe catalog this harness inherits from Stories 3.1 → 4.3: seventeen-token banned regex + twelve Derek fixed strings + eleven secret-pattern regexes + five placeholder-form probes + `${VAR}`/`$VAR` shell-expansion probe + three path-reference probes + four lowercase-literal `…=` probes.
- Epic 6 Story 6.2 (GitHub Action) wires the Epic 6 Story 6.1 deny-list into PR gating; Story 4.4's harness is the reference implementation for the in-repo side of the same contract.
- Epic 7 Story 7.1 (Vixxo-internal getting-started doc) cross-links `docs/setup.md` as the template-facing parent; the internal doc adds Vixxo-cohort / Teams-channel / feedback-loop content on top of this canonical onboarding surface.

## Zero-edit verification block (AC8)

Every Story 1.x / 2.x / 3.x / 4.1 / 4.2 / 4.3 artifact remains byte-stable during Story 4.4. The following is the full invariant set:

- `.cursor/mcp.json` — `d749b788efa974330d104875a5b63793253a40b450f70341da971a403ac3477c`
- `.cursor/mcp.README.md` — `4f27217a93f71b5bc45b0e4055a4ab82b1d052b2f346277b2dd945d89150af09`
- `.cursor/mcp.placeholders.md` — `1fd08afbf68f8d97d0110dbdbdcf7b7f289adba0e7c649dcbe80609b395fa010`
- `.env.example` — `19f9c52047f821f814dfe3b200f0fb77f641d1b373499691f445f8c83d4ed6a4`
- `.gitignore` — `49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1`
- `docs/legal/license-vixxo-internal-canonical.md` — `4b1cbb2d7e7ba1629df5913a45df3a43e4dd3f78d0c786262589ea53160193cc`
- Thirteen predecessor harnesses (SHA-256 verified pre-invocation inside `check_task9` against `EXPECTED_PREDECESSOR_SHA256`).
- `README.md`, `LICENSE`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules` — not touched by Story 4.4.
- Every `.cursor/rules/*.mdc` file — not touched.
- Every `agents/personas/*.md` and `agents/personas/.gitkeep` — not touched.
- Every `memory/**/*.md`, `memory/.obsidian/*.json`, `memory/**/.gitkeep` — not touched.

## Epic AC trace (epics.md lines 323–333)

Epic 4 Story 4.4 AC from `_bmad-output/planning-artifacts/epics.md` lines 323–333 satisfied as follows:

- "`docs/setup.md` covers prerequisites, clone, wizard, verify." → `docs/setup.md` sections: `## Prerequisites` (prereqs), `## Clone and install` (clone), `## Configure credentials (\`.env\`)` + `## Configure active MCPs` + `## Review placeholder MCPs` (wizard precursors), `## Run the setup smoke test` (verify).
- "`docs/mcps.md` has a table: MCP, status (active/placeholder), env vars, link to internal wiki or issue." → `docs/mcps.md` § `## Catalog at a glance` GFM table with columns `Server key | Status | Transport | Env vars | Wiring reference` — five columns satisfy the epic's four-column requirement (Server key↔MCP, Status↔status, Env vars↔env vars, Wiring reference↔link); `Transport` is additive.
- "Both docs reference the skills registry and `npx skills add vixxo-copilot/agent-skills`." → Both docs contain `vixxo-copilot/agent-skills` at least once (setup.md: 2 occurrences; mcps.md: 4 occurrences); `docs/setup.md` § `## Clone and install` contains the literal `npx skills add vixxo-copilot/agent-skills` inside a fenced `bash` code block.

## Epic-closure confirmation

`epic-4.status: in-progress → done` at Phase 3 review approval. Story 4.4 is the last story in Epic 4 (Stories 4.1, 4.2, 4.3 already `done` at Phase 1).

<!-- Why: Story 4.4 Phase 3 task handoff evidence package (AC10 + AC11 + AC12); thirteen-harness regression passing; epic-4 closure confirmed. -->
