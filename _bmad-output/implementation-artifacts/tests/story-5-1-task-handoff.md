# Story 5.1 Task Handoff

Date: 2026-04-21
Scope: Final evidence package for Story 5.1 (`bin/init` scaffold + `package.json` + `package-lock.json`).

## AC-to-file map

| AC | Proof surface |
| --- | --- |
| AC1 (`bin/init` exists, executable, Node-only) | `story-5-1-bin-init-validation.sh` `task3` (shebang, executable bit, Node imports, no bash/sh/zsh literals, no absolute paths) |
| AC2 (single-command auto-bootstrap after clone) | `bin/init` `ensureDependencies()` + smoke transcript below (`rm -rf node_modules && ./bin/init`) |
| AC3 (`package.json` lock) | Harness `task4` (top-level key order + locked values + strict JSON parse + exact `prompts` pin) |
| AC4 (deterministic banner + clean exits) | Harness `task3` + smoke transcript for `--help`, `--version`, and default run |
| AC5 (secret/banned/Derek/placeholder/path/shell-expansion clean) | Harness `task6` (full inherited scan catalog + `content_allowlist_for_personal()` two-stage scan for `package.json`) |
| AC6 (byte-stability invariants preserved) | Harness `task7` (SHA-256 constants for prior locked artifacts) |
| AC7 (`.gitignore` unchanged; `node_modules/` ignored; lockfile tracked) | Harness `task7` + additional verification commands below |
| AC8 (new deterministic harness exists and passes) | `story-5-1-bin-init-validation.sh` with `task1..task9` + `all`, run transcript below |
| AC9 (fourteen-predecessor regression passes) | Harness `task9` + standalone predecessor sweep summary below |
| AC10 (sprint status flow) | `sprint-status.yaml` progression recorded as `backlog -> ready-for-dev -> review -> done` for Story 5.1 (epic remains `in-progress`) |
| AC11 (no spill into 5.2/5.3/other epics) | Working-set diff limited to Story 5.1 files listed below |
| AC12 (matches Epic 5 Story 5.1 AC shape) | `bin/init` + `package.json` + harness checks align with `epics.md` Story 5.1 AC language |

## Full validation command transcript

```text
$ bash _bmad-output/implementation-artifacts/tests/story-5-1-bin-init-validation.sh all
PASS: task1
PASS: task2
PASS: task3
PASS: task4
PASS: task5
PASS: task6
PASS: task7
PASS: task8
task9 OK: fourteen-predecessor byte-stability + regression verified (SHA-256 + ^PASS: fingerprint)
PASS: task9
PASS: all
# exit code: 0
# ^PASS: line count: 10
```

Standalone predecessor sweep (`BMAD_REGRESSION_DEPTH=1`) results:

```text
story-1-1-scaffold-validation.sh|exit=0|pass_lines=1|pass_all=1
story-1-2-root-files-validation.sh|exit=0|pass_lines=1|pass_all=1
story-1-3-root-context-validation.sh|exit=0|pass_lines=1|pass_all=1
story-2-1-agent-identity-validation.sh|exit=0|pass_lines=1|pass_all=1
story-2-2-guardrail-and-formatting-validation.sh|exit=0|pass_lines=10|pass_all=1
story-2-3-work-persona-validation.sh|exit=0|pass_lines=7|pass_all=1
story-2-4-benji-inbox-absence-validation.sh|exit=0|pass_lines=7|pass_all=1
story-3-1-memory-template-tree-validation.sh|exit=0|pass_lines=7|pass_all=1
story-3-2-obsidian-config-validation.sh|exit=0|pass_lines=7|pass_all=1
story-3-3-identity-preferences-validation.sh|exit=0|pass_lines=7|pass_all=1
story-4-1-mcp-json-validation.sh|exit=0|pass_lines=10|pass_all=1
story-4-2-mcp-placeholders-validation.sh|exit=0|pass_lines=10|pass_all=1
story-4-3-env-example-validation.sh|exit=0|pass_lines=10|pass_all=1
story-4-4-setup-and-mcps-docs-validation.sh|exit=0|pass_lines=10|pass_all=1
```

Empirical pass-count vector matches lock exactly:
`( 1 1 1 1 10 7 7 7 7 7 10 10 10 10 )`.

## `bin/init` functional smoke transcript

```text
$ ./bin/init --help
assistants-template - setup wizard

Usage: ./bin/init [--help | -h] [--version | -v]

Story 5.1 (this scaffold): entry point + auto-bootstrap.
Story 5.2 (pending):        prompts + file generation.
Story 5.3 (pending):        npx skills add + MCP verification.

Version: 0.1.0

$ ./bin/init --version
assistants-template init 0.1.0

$ ./bin/init
assistants-template - setup wizard
Story 5.1 scaffold - runnable entry point confirmed.
Story 5.2 (prompts + file generation) and Story 5.3 (skills install + MCP verification) extend this entry point in later epics.

Next: wait for Story 5.2 to land, or run manual onboarding steps from docs/setup.md.

$ rm -rf node_modules && ./bin/init
Installing local dependencies (first-run only)...
added 3 packages, and audited 4 packages in 1s
found 0 vulnerabilities
Dependencies installed.
assistants-template - setup wizard
Story 5.1 scaffold - runnable entry point confirmed.
Story 5.2 (prompts + file generation) and Story 5.3 (skills install + MCP verification) extend this entry point in later epics.

Next: wait for Story 5.2 to land, or run manual onboarding steps from docs/setup.md.

$ ./bin/init
assistants-template - setup wizard
Story 5.1 scaffold - runnable entry point confirmed.
Story 5.2 (prompts + file generation) and Story 5.3 (skills install + MCP verification) extend this entry point in later epics.

Next: wait for Story 5.2 to land, or run manual onboarding steps from docs/setup.md.
```

## Checksums and additional verification

```text
$ shasum -a 256 bin/init package.json package-lock.json .cursor/mcp.json .cursor/mcp.README.md .cursor/mcp.placeholders.md .env.example .gitignore docs/legal/license-vixxo-internal-canonical.md docs/setup.md docs/mcps.md
684b7a243806340929999a632a640d033b3606b57a8df44ec23231cdf9a8035d  bin/init
90627f8024998141107eceab2da5e7016527c976c359bcecb552bef5eb2426ef  package.json
cf1b4c4b98fceb4d6f98b9bb5cb98e31336cba84417c930a9865bdaa8d91392d  package-lock.json
d749b788efa974330d104875a5b63793253a40b450f70341da971a403ac3477c  .cursor/mcp.json
4f27217a93f71b5bc45b0e4055a4ab82b1d052b2f346277b2dd945d89150af09  .cursor/mcp.README.md
1fd08afbf68f8d97d0110dbdbdcf7b7f289adba0e7c649dcbe80609b395fa010  .cursor/mcp.placeholders.md
19f9c52047f821f814dfe3b200f0fb77f641d1b373499691f445f8c83d4ed6a4  .env.example
49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1  .gitignore
4b1cbb2d7e7ba1629df5913a45df3a43e4dd3f78d0c786262589ea53160193cc  docs/legal/license-vixxo-internal-canonical.md
ddce66f02d496e6d5fcd9ed8c53bbca633b9f10772ee2e956b7cb3124ec27276  docs/setup.md
7b2a16f84fa1b087a0efcc08e72508ce834ef6820317e03485066de3d92668d6  docs/mcps.md

$ git check-ignore -v node_modules/prompts/package.json
.gitignore:1:node_modules/  node_modules/prompts/package.json

$ node -e 'JSON.parse(require("fs").readFileSync("package.json","utf8"))'
$ node -e 'JSON.parse(require("fs").readFileSync("package-lock.json","utf8"))'
JSON_PARSE_OK

$ ls node_modules
kleur
prompts
sisteransi
```

Predecessor harness SHA-256 snapshot:

```text
a609f6a857235a57588bab081c2775c3d59c9282ae0d1256f4183b5e923617b8  story-1-1-scaffold-validation.sh
0226aa1b2086ee63065a533bc720afe876fde0958af9ed99276c1ff68fb4afaf  story-1-2-root-files-validation.sh
0cecd5293af7e5896bede460ef1f2a7e822554f735dc10b81d0beb8e0e840ba9  story-1-3-root-context-validation.sh
dc9b98e5e89239d41429e4436b13c671822d237f616eb8ca99c016085e2bb08a  story-2-1-agent-identity-validation.sh
5412bcfc7bd829a98a9054efb8fdf32c72b7e59c2b542cacca0c58648da6df10  story-2-2-guardrail-and-formatting-validation.sh
9d455eaebb775f80d29b24de4a35febc3a8ffba0ed7f237af492723d2096a591  story-2-3-work-persona-validation.sh
f70d8c25e333123c3aae9d44a388594f1850be1449e86a540fdbe2dbec701687  story-2-4-benji-inbox-absence-validation.sh
cb298fff4f83ddbf27644293f4a38ecfd36b099b4d7d4ceb180c41a4af383ff7  story-3-1-memory-template-tree-validation.sh
10ef5221ed1e64e3222c7d95297824175693f66c313eced1260d5645be81292e  story-3-2-obsidian-config-validation.sh
f49f21c1811be49fc7aafa386f7f14553f46deb8a5bee6d4e609ca4d1b39bea8  story-3-3-identity-preferences-validation.sh
cfe810169aef5c2abf7bc021aad4fbb43d3c91eda58fc99b3d16123907dbba8f  story-4-1-mcp-json-validation.sh
ac01c393e68c41df07cc4792abab703d62d4a10d40e96b68c9ac771bd9a1a490  story-4-2-mcp-placeholders-validation.sh
7aa2733e3b0e93d6b35bd0d7c89645ded810ae876b10e81554d26c738d61a277  story-4-3-env-example-validation.sh
e5a254b4f15ac2903c0fda15a6a832199abcc47c920e5823f997c13c255c0473  story-4-4-setup-and-mcps-docs-validation.sh
```

## AC11 creates-only working set

- `bin/init`
- `package.json`
- `package-lock.json`
- `_bmad-output/implementation-artifacts/tests/story-5-1-baseline-audit.md`
- `_bmad-output/implementation-artifacts/tests/story-5-1-canonical-blueprint.md`
- `_bmad-output/implementation-artifacts/tests/story-5-1-bin-init-validation.sh`
- `_bmad-output/implementation-artifacts/tests/story-5-1-task-handoff.md`
- `_bmad-output/implementation-artifacts/5-1-scaffold-bin-init-node-entry-point.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status-only update)

## Forward-looking notes

- Story 5.2 extends `bin/init` with prompt flow and file generation.
- Story 5.3 extends `bin/init` with `npx skills add vixxo-copilot/agent-skills` and MCP verification.
- Epic 5 remains `in-progress` until Stories 5.2 and 5.3 close.
