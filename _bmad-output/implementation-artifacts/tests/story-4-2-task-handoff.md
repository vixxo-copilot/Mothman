# Story 4.2 Task Handoff

Task 6 evidence artifact. Summarizes the Story 4.2 validation pass, the
eleven-predecessor regression transcript, byte-level fingerprints for
future drift detection, per-fenced-block JSON parse transcripts, and
forward-looking notes for Stories 4.3 / 4.4 + Epic 5 Story 5.3.
Captured 2026-04-21.

## AC → evidence map

| AC | What it asserts | Where it is proven |
|----|-----------------|--------------------|
| AC1 | `.cursor/mcp.placeholders.md` exists at the locked path with canonical-order frontmatter, H1, preamble paragraph, and `<!-- Why: … -->` terminator | `check_task3` (frontmatter three-byte prefix, key-order awk, H1 grep-xF, preamble substring, terminator case) |
| AC2 | Exactly eleven pending-MCP H2 sections in canonical order plus `## Conventions` and `## Forward References` — thirteen H2 sections total, no others | `check_task3` (`grep -c '^## '` equals 13; `EXPECTED_H2_HEADINGS` line-order loop) |
| AC3 | Each pending-MCP H2 has the locked five-line discipline (Purpose / Status / Intended transport / Wiring reference / fenced `json` block / `// TODO:` line); fenced JSON blocks are syntactically valid; zero `env` blocks; keyset subset of `{command, args, url, headers}` | `check_task4` (per-section field markers + fence + TODO line); `check_task5` (`extract_fenced_json_blocks` + `python3 -m json.tool` per block + python keyset assertion) |
| AC4 | Eleven placeholder entries use fixed canonical content verbatim (purpose, wiring reference, intended transport, sample JSON shape) | `check_task4` combined with the canonical blueprint (`story-4-2-canonical-blueprint.md` § `Per-server H2 template lock` + § `Inheritance-only note`); Status count `11`; TODO prefix count `11` |
| AC5 | `## Conventions` documents the field order, the `.cursor/mcp.json` byte-stability rule, the two allowed shapes + no `env`, the flip-to-active three-step process, and the placeholder-form probe-free discipline | `check_task3` enforces the heading presence; `check_task6` enforces the placeholder-form probe-free invariant; content locked in the blueprint (`Conventions body lock` section) |
| AC6 | Zero bytes change in `.cursor/mcp.json`, `.cursor/mcp.README.md`, `.gitignore`, root context files, rule pack, personas, memory artifacts, and the eleven predecessor harnesses | `check_task7` (SHA-256 equality vs. `STORY_4_1_MCP_JSON_SHA256`, `STORY_4_1_MCP_README_SHA256`, `STORY_1_1_GITIGNORE_SHA256`); `check_task9` byte-stability is inherited from each predecessor harness's own invariance checks |
| AC7 | Zero PII, Derek-identifying content, secret-shaped strings, `${VAR}` tokens, `password=/token=/secret=/api_key=` literals, or placeholder-form probes | `check_task6` (eleven secret-pattern regexes, 12 Derek fixed-string probes, three path-reference probes, five placeholder-form probes, four key=value literal probes); `check_task5` `${VAR}` scan |
| AC8 | Deterministic harness exists, `#!/usr/bin/env bash` on line 1, `set -euo pipefail` on line 2, nine gates + `all`, POSIX-bash-3.2 / BSD + GNU grep compatible, exits 0 with `PASS: all`, emits exactly 10 `^PASS:` lines on success | `check_task8` self-check; `all`-mode transcript below emits 10 `^PASS:` lines |
| AC9 | Eleven predecessor harnesses continue to pass unchanged; each exit 0; per-harness PASS-count fingerprint `( 1 1 1 1 10 7 7 7 7 7 10 )` | `check_task9`; regression transcript below |
| AC10 | Sprint tracker flips `4-2-…status: ready-for-dev → review` at Phase 2; `epic-4.status: in-progress` preserved; `last_updated: 2026-04-21`; no regression of other statuses | Task 7 edits `_bmad-output/implementation-artifacts/sprint-status.yaml`; diff below |
| AC11 | Additive-only; story creates only `.cursor/mcp.placeholders.md`, harness, three evidence artifacts, and this story file | File List in story file; `git status` one-shot before commit |
| AC12 | Deliverable satisfies Epic 4 Story 4.2 AC at `epics.md` lines 302–310 (eleven commented JSON blocks in canonical order with `// TODO:` tails) | Blueprint `Per-server content locks` + placeholders file shape validated by `check_task4` + `check_task5`; reconciliation documented in blueprint |

## Validation transcript — Story 4.2 harness `all` mode

```
$ bash _bmad-output/implementation-artifacts/tests/story-4-2-mcp-placeholders-validation.sh all
PASS: task1
PASS: task2
PASS: task3
PASS: task4
PASS: task5
PASS: task6
PASS: task7
PASS: task8
PASS: task9
PASS: all
```

Exit code: `0`. Exactly 10 `^PASS:` lines.

## Regression transcript — eleven predecessor harnesses (individual, `all` mode)

```
$ for h in story-1-1-scaffold-validation.sh story-1-2-root-files-validation.sh \
           story-1-3-root-context-validation.sh story-2-1-agent-identity-validation.sh \
           story-2-2-guardrail-and-formatting-validation.sh \
           story-2-3-work-persona-validation.sh story-2-4-benji-inbox-absence-validation.sh \
           story-3-1-memory-template-tree-validation.sh \
           story-3-2-obsidian-config-validation.sh \
           story-3-3-identity-preferences-validation.sh \
           story-4-1-mcp-json-validation.sh; do
    out=$(bash _bmad-output/implementation-artifacts/tests/${h} all 2>&1); ec=$?
    c=$(printf '%s\n' "${out}" | grep -c '^PASS:')
    printf '%-55s exit=%d PASS=%d\n' "${h}" "${ec}" "${c}"
  done

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

Every harness exited `0`. PASS-count vector `( 1 1 1 1 10 7 7 7 7 7 10 )`
matches the `EXPECTED_PASS_COUNTS` constant embedded in
`story-4-2-mcp-placeholders-validation.sh` exactly — no discrepancy; no
adjustment required.

## Byte-stability re-verification (AC6)

```
$ shasum -a 256 .cursor/mcp.json .cursor/mcp.README.md .gitignore
d749b788efa974330d104875a5b63793253a40b450f70341da971a403ac3477c  .cursor/mcp.json
4f27217a93f71b5bc45b0e4055a4ab82b1d052b2f346277b2dd945d89150af09  .cursor/mcp.README.md
49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1  .gitignore
```

All three values match the Task 1 baseline captures exactly (see
`story-4-2-baseline-audit.md` § `Byte-stability fingerprints`). `.gitignore`
additionally matches the Story 4.1 F1-patch handoff fingerprint verbatim.

```
$ git check-ignore -v .cursor/mcp.placeholders.md; echo $?
1        # NOT gitignored (exit 1, empty output)
```

The placeholders file is committed-eligible and is not covered by any
`.gitignore` pattern.

## Per-entry JSON parse transcript (eleven fenced blocks)

Each fenced `json` block was awk-extracted from
`.cursor/mcp.placeholders.md` into a temp file and passed through
`python3 -m json.tool`:

```
block-01.json (freshdesk)                               PARSE OK
block-02.json (dynamics)                                PARSE OK
block-03.json (vixxonow)                                PARSE OK
block-04.json (vixxolink)                               PARSE OK
block-05.json (gateway)                                 PARSE OK
block-06.json (zoominfo)                                PARSE OK
block-07.json (hubspot)                                 PARSE OK
block-08.json (aws-connect)                             PARSE OK
block-09.json (chatfpt)                                 PARSE OK
block-10.json (elastic)                                 PARSE OK
block-11.json (introspection)                           PARSE OK
```

All eleven blocks parse cleanly. Each object has exactly one top-level
key matching the corresponding `EXPECTED_PLACEHOLDER_KEYS[i]` in
canonical order; each nested value is an object whose key set is a
subset of `{ command, args, url, headers }` (zero `env` blocks). This
transcript was re-confirmed by `check_task5` on the Story 4.2 harness
`all` run above.

## SHA-256 + byte-count fingerprints

| Path | Bytes | SHA-256 |
|------|-------|---------|
| `.cursor/mcp.placeholders.md` | 8556 | `9214af7f4db5fbbf850e68feecaf55b84fbb49d37e57018d2620e82846e12f24` |
| `.cursor/mcp.json` | 787 | `d749b788efa974330d104875a5b63793253a40b450f70341da971a403ac3477c` (byte-stable vs. Task 1 baseline) |
| `.cursor/mcp.README.md` | 9007 | `4f27217a93f71b5bc45b0e4055a4ab82b1d052b2f346277b2dd945d89150af09` (byte-stable vs. Task 1 baseline) |
| `.gitignore` | 51 | `49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1` (byte-stable vs. Story 1.1 F1-patch handoff) |
| `_bmad-output/implementation-artifacts/tests/story-4-2-mcp-placeholders-validation.sh` | — | `8540416f5df3cb0796602795ec3c4513fa909fcf0fd30a8303a2bc2afaa01325` |
| `_bmad-output/implementation-artifacts/tests/story-4-2-baseline-audit.md` | — | `d95b9b2cd272a4d3c2dabe7d2a08612f4d15a94d0392679603ad38f3907666f5` |
| `_bmad-output/implementation-artifacts/tests/story-4-2-canonical-blueprint.md` | — | `100fe8ee9a4fd2904e10865b300b71f508cb1397dfede050cd9f62dc9fe7471c` |

## Zero-edit verification (AC6 + AC11)

The following predecessor artifacts are asserted byte-stable by the
Story 4.2 regression gate (`check_task9`) and by their own harnesses
running internally. Story 4.2 touches NONE of these paths:

- Active MCP artifacts: `.cursor/mcp.json`, `.cursor/mcp.README.md`
  (Story 4.1 outputs — SHA-256 asserted equal to Task 1 baseline).
- Root context files: `AGENTS.md`, `CLAUDE.md`, `.cursorrules`,
  `README.md`, `LICENSE`, `.gitignore`.
- Rule pack: `.cursor/rules/agent-identity.mdc`,
  `outbound-messaging-guardrail.mdc`, `memory-vault-protection.mdc`,
  `teams-dm-formatting.mdc`, `email-triage-thread-defaults.mdc`
  (plus `.cursor/rules/.gitkeep`).
- Persona pack: `agents/personas/work.md`, `agents/personas/.gitkeep`.
- Memory templates: nine Story 3.1 `_template.md` files under `memory/`.
- Memory identity seeds: `memory/me/identity.md`,
  `memory/me/preferences.md`, `memory/.gitkeep`.
- Obsidian config: seven Story 3.2 JSON files under `memory/.obsidian/`.
- Eleven predecessor harnesses under
  `_bmad-output/implementation-artifacts/tests/story-[1-4]-*.sh`.

Story 4.1 `STORY_1_1_HARNESS_BYTES` / `STORY_1_1_HARNESS_SHA256` drift
alarms embedded in the Story 3.3 + Story 4.1 harnesses continue to
match on this Story 4.2 run, confirming zero predecessor-harness edits.

## Forward-looking notes

- **Story 4.3** — will add `.env.example` at the repo root with a
  `status: placeholder` section for each of the eleven pending MCPs
  listed in `.cursor/mcp.placeholders.md`. Active-MCP sections inherit
  env vars from `.cursor/mcp.README.md` (`GITHUB_PERSONAL_ACCESS_TOKEN`,
  `GONG_ACCESS_KEY`, `GONG_ACCESS_KEY_SECRET`, optional
  `MS365_MCP_CLIENT_ID` and `MS365_MCP_TENANT_ID`). Placeholder sections
  may enumerate the shell-exported env vars noted in the Story 4.2
  per-server research (for example Freshdesk:
  `FRESHDESK_API_KEY` / `FRESHDESK_DOMAIN`; Elastic: `ELASTIC_URL` /
  `ELASTIC_API_KEY`).
- **Story 4.4** — will rewrite `docs/setup.md` + `docs/mcps.md` with
  self-serve onboarding (clone → `bin/init` → verify). The
  `docs/mcps.md` catalog table will cross-link to
  `.cursor/mcp.README.md` (active) and `.cursor/mcp.placeholders.md`
  (pending).
- **Epic 5 Story 5.3** — the `bin/init` setup wizard will call each
  active MCP once and report PASS / FAIL per server.
  `.cursor/mcp.placeholders.md` entries are descriptive documentation;
  the wizard SKIPS them explicitly.
- **Flip-to-active discipline** — when a pending MCP is promoted to
  active, the fenced JSON block is copied into `.cursor/mcp.json`
  under `mcpServers`; the `// TODO:` markdown line is dropped; the
  server's H2 section is removed from `.cursor/mcp.placeholders.md`;
  a matching H2 is added to `.cursor/mcp.README.md`. The Story 4.1
  deny-list for that key is removed atomically with the flip. This is
  the subject of a future story.
- **Per-server package-reference discipline** — three illustrative
  patterns are in use: `TBD:<package-name>` for unstable upstreams,
  upstream literal references for known-stable packages, and
  `TODO://<hostname>.example.internal/mcp` or `TODO://api.<host>/mcp`
  for remote URL placeholders. None are operationally valid as written;
  the flip-to-active step chooses a concrete package ref and pins
  `@latest` where applicable.

## File List (produced by Story 4.2)

- `.cursor/mcp.placeholders.md` (new — eleven pending-MCP H2 sections +
  Conventions + Forward References; markdown with fenced `json` blocks
  and `// TODO:` markdown lines outside the fences)
- `_bmad-output/implementation-artifacts/tests/story-4-2-mcp-placeholders-validation.sh`
  (new — nine-gate + `all` harness; chmod +x)
- `_bmad-output/implementation-artifacts/tests/story-4-2-baseline-audit.md`
  (new — Task 1 evidence)
- `_bmad-output/implementation-artifacts/tests/story-4-2-canonical-blueprint.md`
  (new — Task 2 evidence)
- `_bmad-output/implementation-artifacts/tests/story-4-2-task-handoff.md`
  (new — this file)
- `_bmad-output/implementation-artifacts/4-2-add-commented-out-placeholders-for-pending-mcps.md`
  (updated — Status flip, Task checkboxes, Change Log + Dev Agent
  Record populated)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (updated —
  `4-2-…status: ready-for-dev → review` + `last_updated` value kept at
  `2026-04-21`)

<!-- Why: Task 6 evidence artifact. Binds every Story 4.2 AC to its harness gate or inline proof, captures the full validation + eleven-harness regression transcript, records the SHA-256 / byte-count fingerprints Stories 4.3 / 4.4 and Epic 5 Story 5.3 will inherit for zero-drift assertions, and locks the per-fenced-block JSON parse transcript for AC3 / AC12. -->
