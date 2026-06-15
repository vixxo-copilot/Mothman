# Story 5.1 Baseline Audit

Captured: 2026-04-21 on Dev workstation (macOS, Apple Silicon, bash 3.2.57, Node 25.7.0, npm 11.10.1).

This audit is the Task 1 evidence required by AC: 1, 2, 3, 6, 7, 8, 9. It is consumed by `story-5-1-bin-init-validation.sh task1` and cross-checked at Task 4 and Task 6.

## Node / npm version-requirement rationale

- Story 5.1 locks `engines.node = ">=20.0.0"`. Node 20 is the Active LTS series as of 2026-04 (Node 22 is LTS `Iron`; Node 20 `Hydrogen` remains supported through 2026-04). This matches `docs/setup.md` Prerequisites line 18 ("Node.js Active LTS").
- npm 10+ ships with Node 20+ and defaults to `lockfileVersion: 3`, which Story 5.1 codifies as `EXPECTED_LOCKFILE_VERSION`.
- Dev workstation runs Node 25.7.0 / npm 11.10.1; the `>=20.0.0` engines floor is satisfied by a wide margin. The `./bin/init` script uses only APIs that have been stable since Node 18 (`node:fs`, `node:path`, `node:child_process`.spawnSync), so it degrades cleanly on Node 20.
- Source URL: `https://nodejs.org/en/about/previous-releases`.

## prompts@2.4.2 upstream cross-reference and alternatives evaluation

- Upstream repo: `https://github.com/terkelg/prompts` — `terkelg/prompts`.
- npm registry: `https://www.npmjs.com/package/prompts`.
- Published version at author time: `2.4.2` — released 2021-10-07.
- Package engines: `node >= 14`; Story 5.1's `>=20.0.0` floor is a strict superset.
- Transitive dep tree: `kleur` (`^3.0.3`), `sisteransi` (`^1.0.5`). Three-package total (`prompts`, `kleur`, `sisteransi`).
- Zero open `npm audit` advisories against `prompts@2.4.2`, `kleur`, or `sisteransi` as of 2026-04-21.
- Alternatives evaluated and rejected:
  - `inquirer` — maintenance-mode `9.x` / `10.x` split; ~30 transitive packages. Larger `node_modules/` surface.
  - `@inquirer/prompts` — ESM-only; ~100 transitive packages. Would force `"type": "module"` which complicates the single-file entry point.
  - `enquirer` — smaller footprint than inquirer but stricter API and less battle-tested.
  - `prompt-sync` — synchronous, no choice/multi-select/validator surface.
  - `readline-sync` — no TTY-aware behavior; poor ergonomics for multi-select.
- Decision: `prompts@2.4.2` exact-pin. CommonJS-first, smallest transitive footprint, battle-tested (used by `create-react-app`, `vite`, `astro`, `create-svelte`, `nuxt` init flows), API stable for 4+ years, zero CVEs.

## Byte-stability fingerprints (SHA-256)

Captured 2026-04-21 on on-disk post-Story-4.4 state. Every value below is asserted invariant by `story-5-1-bin-init-validation.sh task7`.

| Path | SHA-256 |
| --- | --- |
| `.cursor/mcp.json` | `d749b788efa974330d104875a5b63793253a40b450f70341da971a403ac3477c` |
| `.cursor/mcp.README.md` | `4f27217a93f71b5bc45b0e4055a4ab82b1d052b2f346277b2dd945d89150af09` |
| `.cursor/mcp.placeholders.md` | `1fd08afbf68f8d97d0110dbdbdcf7b7f289adba0e7c649dcbe80609b395fa010` |
| `.env.example` | `19f9c52047f821f814dfe3b200f0fb77f641d1b373499691f445f8c83d4ed6a4` |
| `.gitignore` | `49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1` |
| `docs/legal/license-vixxo-internal-canonical.md` | `4b1cbb2d7e7ba1629df5913a45df3a43e4dd3f78d0c786262589ea53160193cc` |
| `docs/setup.md` | `ddce66f02d496e6d5fcd9ed8c53bbca633b9f10772ee2e956b7cb3124ec27276` |
| `docs/mcps.md` | `7b2a16f84fa1b087a0efcc08e72508ce834ef6820317e03485066de3d92668d6` |
| `docs/pii-denylist.md` (Epic 6 artifact) | `8f7911369c8db8dfb51d69c93d5701ee6907fc663a1c0e5d23a44a488add62fa` |
| `bin/.gitkeep` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty file canonical sentinel) |

`docs/pii-denylist.md` is an Epic 6 artifact on a parallel branch; not chained into Story 5.1's regression task9 but re-captured here to document byte-stability during Story 5.1's working-set edits.

## Predecessor-harness SHA-256 vector (fourteen predecessors)

Positional-parallel to `EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 10 10 10 )`.

| idx | Harness | SHA-256 |
| --- | --- | --- |
| 0 | `story-1-1-scaffold-validation.sh` | `a609f6a857235a57588bab081c2775c3d59c9282ae0d1256f4183b5e923617b8` |
| 1 | `story-1-2-root-files-validation.sh` | `0226aa1b2086ee63065a533bc720afe876fde0958af9ed99276c1ff68fb4afaf` |
| 2 | `story-1-3-root-context-validation.sh` | `0cecd5293af7e5896bede460ef1f2a7e822554f735dc10b81d0beb8e0e840ba9` |
| 3 | `story-2-1-agent-identity-validation.sh` | `dc9b98e5e89239d41429e4436b13c671822d237f616eb8ca99c016085e2bb08a` |
| 4 | `story-2-2-guardrail-and-formatting-validation.sh` | `5412bcfc7bd829a98a9054efb8fdf32c72b7e59c2b542cacca0c58648da6df10` |
| 5 | `story-2-3-work-persona-validation.sh` | `9d455eaebb775f80d29b24de4a35febc3a8ffba0ed7f237af492723d2096a591` |
| 6 | `story-2-4-benji-inbox-absence-validation.sh` | `f70d8c25e333123c3aae9d44a388594f1850be1449e86a540fdbe2dbec701687` |
| 7 | `story-3-1-memory-template-tree-validation.sh` | `cb298fff4f83ddbf27644293f4a38ecfd36b099b4d7d4ceb180c41a4af383ff7` |
| 8 | `story-3-2-obsidian-config-validation.sh` | `10ef5221ed1e64e3222c7d95297824175693f66c313eced1260d5645be81292e` |
| 9 | `story-3-3-identity-preferences-validation.sh` | `f49f21c1811be49fc7aafa386f7f14553f46deb8a5bee6d4e609ca4d1b39bea8` |
| 10 | `story-4-1-mcp-json-validation.sh` | `cfe810169aef5c2abf7bc021aad4fbb43d3c91eda58fc99b3d16123907dbba8f` |
| 11 | `story-4-2-mcp-placeholders-validation.sh` | `ac01c393e68c41df07cc4792abab703d62d4a10d40e96b68c9ac771bd9a1a490` |
| 12 | `story-4-3-env-example-validation.sh` | `7aa2733e3b0e93d6b35bd0d7c89645ded810ae876b10e81554d26c738d61a277` |
| 13 | `story-4-4-setup-and-mcps-docs-validation.sh` | `e5a254b4f15ac2903c0fda15a6a832199abcc47c920e5823f997c13c255c0473` |

### Story 3.3 SHA drift vs. Story 4.4 embedded lock

- Story 4.4's `EXPECTED_PREDECESSOR_SHA256[9]` embeds `77a5376887f03909223074b2f21e1306f689a9238d6da0cf191aa79a0427b427` for Story 3.3.
- The CURRENT on-disk SHA of `story-3-3-identity-preferences-validation.sh` is `f49f21c1811be49fc7aafa386f7f14553f46deb8a5bee6d4e609ca4d1b39bea8` (re-computed 2026-04-21 as shown above).
- Root cause: the Story 3.3 harness was updated in-place after Story 4.4 lock-in; Story 4.4's lock was never re-synced.
- Impact on Story 5.1: none when Story 5.1's `task9` invokes Story 4.4 with `BMAD_REGRESSION_DEPTH=1` exported. Story 4.4's own `check_task9` short-circuits via the F6 guard, so the embedded Story 3.3 SHA is not compared. Empirically verified: running Story 4.4 `all` in depth-1 mode emits `task9 SKIP: BMAD_REGRESSION_DEPTH=1 (nested)` and still emits `PASS: task9` + `PASS: all` — 10 PASS lines total, matching `EXPECTED_PASS_COUNTS[13]=10`.
- Mitigation for Story 5.1: Story 5.1's own `EXPECTED_PREDECESSOR_SHA256[9]` locks the CURRENT on-disk value (`f49f21c1…`), so direct Story 5.1 SHA pre-check passes.
- Integration-fix follow-up (out of scope for Story 5.1, filed as `drift note`): update Story 4.4's embedded `EXPECTED_PREDECESSOR_SHA256[9]` to the current Story 3.3 on-disk value once Epic 5 is parked for a moment, OR document permanent depth-1 invocation as the only sanctioned Story 4.4 invocation path.

## Predecessor-harness compatibility scan (fourteen harnesses)

Scan approach: for each predecessor harness, grep for any repo-root path reference or `bin/*` / `package.json` / `package-lock.json` / `node_modules/` pattern that could reject the new Story 5.1 artifacts.

- Stories 1.1 / 1.2 / 1.3 — iterate a locked root-file allowlist via named constants (`REQUIRED_ROOT_FILES=…`); the allowlist does NOT include `package.json` or `bin/init` generically and the harnesses do not grep the repo root for new files. Adding `package.json` and `bin/init` does not drift any assertion.
- Stories 2.1 / 2.2 / 2.3 / 2.4 — scope to `.cursor/rules/*.mdc` and `agents/personas/*.md`; no reference to `bin/` subtree or root-level JSON files.
- Stories 3.1 / 3.2 / 3.3 — scope to `memory/**` and `.obsidian/*.json`; no reference to `bin/` subtree or root-level JSON files.
- Stories 4.1 / 4.2 — scope to `.cursor/mcp.json` and `.cursor/mcp.README.md` / `.cursor/mcp.placeholders.md`; no reference to `bin/` or root-level JSON other than the one target.
- Story 4.3 — scope to `.env.example`; no reference to `bin/` or `package.json`.
- Story 4.4 — scope to `docs/setup.md` and `docs/mcps.md`; references `./bin/init` as a FORWARD-REFERENCE prose string in `docs/setup.md` (which stays byte-stable during Story 5.1), but the harness does not grep for `bin/init`'s on-disk existence. Adding `bin/init` on-disk does not drift any Story 4.4 assertion.

Expected outcome: zero predecessor allowlist extensions needed. Empirically verified: all fourteen predecessor harnesses emit `PASS: all` and the positional-parallel `^PASS:` line-count vector `( 1 1 1 1 10 7 7 7 7 7 10 10 10 10 )` under `BMAD_REGRESSION_DEPTH=1` against the post-Story-5.1 working tree (re-verified at Task 6).

## .gitignore compatibility re-confirmation

- `.gitignore` line 1 = `node_modules/` (exact — no leading `!`, no nested glob). SHA-256 `49fa451f69…` matches Story 1.1+F1 lock.
- `git check-ignore -v node_modules/prompts/package.json` → exit `0`, output `.gitignore:1:node_modules/ node_modules/prompts/package.json` — confirming `node_modules/` is ignored.
- `git check-ignore -v bin/init` → exit `1`, empty output — confirming `bin/init` is NOT ignored (tracked).
- `git check-ignore -v package.json` → exit `1`, empty output — confirming `package.json` is NOT ignored (tracked).
- `git check-ignore -v package-lock.json` → exit `1`, empty output — confirming `package-lock.json` is NOT ignored (tracked; reproducibility invariant).
- Conclusion: `.gitignore` is not edited by Story 5.1. The existing `node_modules/` rule at line 1 handles the bootstrap-created directory without modification.

## bin/ directory pre-state check

- `bin/` directory exists (Story 1.1 scaffold), contains only `.gitkeep` (empty 0-byte file, SHA-256 `e3b0c44298fc1…` — the canonical SHA-256 of the empty string).
- Adding `bin/init` alongside `bin/.gitkeep` does not require `.gitkeep` removal; both coexist. `.gitkeep` remains a defense against accidental `bin/` removal when `bin/init` is deleted in any future story.
- Story 1.1 scaffold validation harness does not enumerate files inside `bin/`; adding `bin/init` does not drift the Story 1.1 scan.

## Empirical predecessor PASS-count vector

Captured 2026-04-21 against the current on-disk state (pre-`bin/init`, pre-`package.json`):

```
1  story-1-1-scaffold-validation.sh
1  story-1-2-root-files-validation.sh
1  story-1-3-root-context-validation.sh
1  story-2-1-agent-identity-validation.sh
10 story-2-2-guardrail-and-formatting-validation.sh
7  story-2-3-work-persona-validation.sh
7  story-2-4-benji-inbox-absence-validation.sh
7  story-3-1-memory-template-tree-validation.sh
7  story-3-2-obsidian-config-validation.sh
7  story-3-3-identity-preferences-validation.sh
10 story-4-1-mcp-json-validation.sh
10 story-4-2-mcp-placeholders-validation.sh
10 story-4-3-env-example-validation.sh
10 story-4-4-setup-and-mcps-docs-validation.sh
```

Locked as `EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 10 10 10 )` in the Story 5.1 harness. Fourteen-element positional-parallel vector.

## Source URLs

- Node.js Active LTS release schedule: `https://nodejs.org/en/about/previous-releases`
- `child_process.spawnSync`: `https://nodejs.org/docs/latest-v20.x/api/child_process.html#child_processspawnsynccommand-args-options`
- `node:` built-in prefix: `https://nodejs.org/api/modules.html#core-modules`
- `package.json` `bin` field: `https://docs.npmjs.com/cli/v10/configuring-npm/package-json#bin`
- `package.json` `engines` field: `https://docs.npmjs.com/cli/v10/configuring-npm/package-json#engines`
- `package-lock.json` format: `https://docs.npmjs.com/cli/v10/configuring-npm/package-lock-json`
- `prompts` upstream: `https://github.com/terkelg/prompts`
- `prompts` registry: `https://www.npmjs.com/package/prompts`
