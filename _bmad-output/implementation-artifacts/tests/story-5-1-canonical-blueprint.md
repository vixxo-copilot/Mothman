# Story 5.1 Canonical Blueprint

Captured: 2026-04-21. This blueprint is the Task 2 evidence required by AC: 1, 2, 3, 4, 5, 7, 8. It locks the exact shape of `bin/init`, `package.json`, `package-lock.json`, the `description`-field content-allowlist carve-out, and the evidence constants consumed by `story-5-1-bin-init-validation.sh`.

## Inheritance-only note

The following catalogs are inherited VERBATIM from Story 4.4 (which inherited them verbatim from Stories 4.3 / 4.2 / 4.1 / 3.3 / 3.2 / 3.1). Story 5.1 adds ZERO entries and removes ZERO entries.

- Banned-term regex (17 tokens; `personal` included).
- Twelve Derek fixed-string probes (`Chiron`, `MasteryLab`, `Agile Weekly`, `Queen Creek`, `Gangplank`, `Bodybuilding.com`, `Integrum`, `Omarchy`, `derekneighbors.com`, `Playrix`, `Laurie`, `Deke`).
- Three path-reference probes (`/Users/`, `Public/gtd-life`, `@gmail.com`).
- Four `…=` lowercase-literal probes (`password=`, `token=`, `secret=`, `api_key=`).
- Five placeholder-form probes (`{{name}}`, `{name}`, `<name>`, `%name%`, `${name}`).
- `${VAR}` / `$VAR` shell-expansion-token probe.
- Eleven secret-pattern regexes (`sk-…`, `ghp_…`, `gho_…`, `ghs_…`, `github_pat_…`, `xox[baprs]-…`, JWT, `Bearer …`, `AKIA[0-9A-Z]{16}`, `AIza…`, `[A-Fa-f0-9]{32,}`).

Story 5.1 ADDS two new artifacts to the harness library:

- `content_allowlist_for_personal()` — a single-scope `sed` substitution of the full locked `description` string in `package.json` (see below).
- `json_strict_parse()` — Node-based JSON parser (`node -e 'JSON.parse(fs.readFileSync(path,"utf8"))'`), used for `package.json` and `package-lock.json` since Node is now a hard prerequisite for the story.

## Blueprint — `bin/init`

Exact structural blueprint (line 1 is literally `#!/usr/bin/env node`; other lines may vary in whitespace and comments but MUST preserve the function-set, flag-handler order, banner text, and error prefix):

```text
#!/usr/bin/env node
// assistants-template — setup wizard (Epic 5).
// Story 5.1 scaffold: runnable entry point, auto-bootstrap of local deps on first run.
// Story 5.2 will add prompt flows + file generation.
// Story 5.3 will add `npx skills add vixxo-copilot/agent-skills` + per-MCP verification.

'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const ROOT = path.resolve(__dirname, '..');
const PKG_PATH = path.join(ROOT, 'package.json');
const NODE_MODULES_PROMPTS = path.join(ROOT, 'node_modules', 'prompts', 'package.json');

function loadPackage() {
  return JSON.parse(fs.readFileSync(PKG_PATH, 'utf8'));
}

function printHelp(pkg) {
  console.log('assistants-template — setup wizard');
  console.log('');
  console.log('Usage: ./bin/init [--help | -h] [--version | -v]');
  console.log('');
  console.log('Story 5.1 (this scaffold): entry point + auto-bootstrap.');
  console.log('Story 5.2 (pending):        prompts + file generation.');
  console.log('Story 5.3 (pending):        npx skills add + MCP verification.');
  console.log('');
  console.log('Version: ' + pkg.version);
}

function printVersion(pkg) {
  console.log('assistants-template init ' + pkg.version);
}

function ensureDependencies() {
  if (fs.existsSync(NODE_MODULES_PROMPTS)) return;
  console.log('Installing local dependencies (first-run only)...');
  const result = spawnSync('npm', ['install'], { cwd: ROOT, stdio: 'inherit' });
  const status = result.status;
  if (status !== 0) {
    const code = (status === null || status === undefined) ? 'unknown' : String(status);
    console.error('[bin/init] npm install failed; exit ' + code + ". Please run 'npm install' manually and retry.");
    process.exit(typeof status === 'number' ? status : 1);
  }
  console.log('Dependencies installed.');
}

function main() {
  const pkg = loadPackage();
  const args = process.argv.slice(2);
  if (args.indexOf('--help') !== -1 || args.indexOf('-h') !== -1) { printHelp(pkg); return; }
  if (args.indexOf('--version') !== -1 || args.indexOf('-v') !== -1) { printVersion(pkg); return; }
  ensureDependencies();
  console.log('assistants-template — setup wizard');
  console.log('Story 5.1 scaffold — runnable entry point confirmed.');
  console.log('Story 5.2 (prompts + file generation) and Story 5.3 (skills install + MCP verification) extend this entry point in later epics.');
  console.log('');
  console.log('Next: wait for Story 5.2 to land, or run manual onboarding steps from docs/setup.md.');
}

main();
```

Structural invariants (enforced by `story-5-1-bin-init-validation.sh check_task3`):

- Line 1 is literally `#!/usr/bin/env node` — no variants (`#!/usr/bin/node`, `#!/usr/local/bin/node`, leading space).
- Exactly one `spawnSync('npm',` substring (wired via `require('node:child_process')`).
- Exactly one `require('node:fs')` and one `require('node:path')` and one `require('node:child_process')` import.
- Zero `bash` / `sh` / `zsh` / `/bin/bash` / `/bin/sh` string literals (whole-word match; no false positive on `spawnSync`).
- Zero `/Users/` and `/home/` absolute-path literals.
- Zero backtick-exec (` `` ` style child_process.execSync).
- Zero `os.homedir()`, `~`-literal, or `process.env.HOME` references.
- Contains each of the four locked banner lines from AC4 verbatim.
- Fast-path flag handlers (`--help` / `-h` / `--version` / `-v`) BEFORE `ensureDependencies` — so `./bin/init --help` does not trigger `npm install`.
- Error-message prefix `[bin/init] npm install failed; exit` exactly.
- UTF-8 encoded, LF line endings, trailing newline (last byte `0x0a`), executable bit set.

## Blueprint — `package.json`

Exact verbatim lock (two-space indent, trailing newline, LF, strict JSON):

```json
{
  "name": "assistants-template",
  "version": "0.1.0",
  "private": true,
  "description": "Vixxo-deployable personal AI agent template; clone, run ./bin/init, work.",
  "type": "commonjs",
  "bin": {
    "assistants-init": "./bin/init"
  },
  "scripts": {
    "init": "node ./bin/init",
    "start": "node ./bin/init"
  },
  "engines": {
    "node": ">=20.0.0"
  },
  "dependencies": {
    "prompts": "2.4.2"
  }
}
```

Top-level key order (enforced at `check_task4`): `name`, `version`, `private`, `description`, `type`, `bin`, `scripts`, `engines`, `dependencies`. Nine keys, canonical order. NO additional top-level keys (no `main`, `exports`, `devDependencies`, `peerDependencies`, `repository`, `author`, `license` — template repo is not publishable; `license` is tracked separately via root `LICENSE`).

## Blueprint — `package-lock.json`

Generated by `npm install` from Dev workstation. The shape assertions (enforced at `check_task5`):

- `lockfileVersion` equals `3` (default for npm 10+).
- `name` equals `"assistants-template"`.
- `version` equals `"0.1.0"`.
- `packages[""].dependencies.prompts` equals `"2.4.2"` (mirrors `package.json` direct dep).
- `packages["node_modules/prompts"].version` equals `"2.4.2"`.
- `packages["node_modules/kleur"]` present (transitive of prompts; `^3.0.3`).
- `packages["node_modules/sisteransi"]` present (transitive of prompts; `^1.0.5`).
- Sorted set equality on non-root `packages` keys equals `{node_modules/kleur, node_modules/prompts, node_modules/sisteransi}` — three packages total, no bloat.
- Full SHA-512 integrity hashes per package-tarball entry (standard npm output).
- Strict JSON parse succeeds via `node -e 'JSON.parse(require("fs").readFileSync("package-lock.json","utf8"))'`.

## Description-content-allowlist carve-out

The locked `description` value `"Vixxo-deployable personal AI agent template; clone, run ./bin/init, work."` contains the substring `personal`. The banned-term regex's `personal` token WILL match case-insensitively against this phrase. To resolve the conflict without weakening the banned-term discipline globally, `story-5-1-bin-init-validation.sh` introduces a SECOND sanitization helper:

```bash
content_allowlist_for_personal() {
  local path="$1"
  sed -E "s|\"description\": \"Vixxo-deployable personal AI agent template; clone, run \./bin/init, work\.\"|\"description\": \"__LOCKED_DESC__\"|g" "${path}"
}
```

Allowlist contract:

- **Anchored on the full locked string** (not the single word `personal`). A new line adding `personal` outside this locked description would NOT be substituted and WOULD trip the banned-term regex.
- **Single-scope** — applied only to `package.json`. `bin/init` uses the plain `sanitize_for_banned_scan()` view (which only substitutes `GITHUB_PERSONAL_ACCESS_TOKEN`; not relevant to Story 5.1 because `bin/init` does not reference env-var names).
- **Self-testing** — the harness asserts the PRE-substitution view of `package.json` contains the substring `personal AI agent template` (proving the allowlist is exercised) AND the POST-substitution view's banned-term regex returns zero matches (proving the allowlist works).
- **Rationale** — the phrase "personal AI agent template" is product-positioning language inherited from Epic 5's FR1 narrative ("every Vixxo employee's PERSONAL AI agent template"). Replacing `personal` with `individual` / `employee` loses positioning nuance. The content-allowlist is a narrow, documented, self-testing carve-out — not a general relaxation of the banned-term rule.

## Banner text lock

Locked literal banner strings from AC4 (enforced by `check_task3` via `grep -Fq`):

1. `assistants-template — setup wizard`
2. `Story 5.1 scaffold — runnable entry point confirmed.`
3. `Story 5.2 (prompts + file generation) and Story 5.3 (skills install + MCP verification) extend this entry point in later epics.`
4. `Next: wait for Story 5.2 to land, or run manual onboarding steps from docs/setup.md.`

## Evidence constants for the Task 5 harness

- `EXPECTED_TOP_KEYS=( name version private description type bin scripts engines dependencies )` — nine keys, canonical order.
- `EXPECTED_LOCK_PACKAGES=( node_modules/kleur node_modules/prompts node_modules/sisteransi )` — three sorted transitive-package keys.
- `EXPECTED_PROMPTS_VERSION="2.4.2"`.
- `EXPECTED_NODE_ENGINE=">=20.0.0"`.
- `EXPECTED_LOCKFILE_VERSION=3`.
- `EXPECTED_PACKAGE_NAME="assistants-template"`.
- `EXPECTED_PACKAGE_VERSION="0.1.0"`.
- `EXPECTED_DESCRIPTION_LOCKED='"description": "Vixxo-deployable personal AI agent template; clone, run ./bin/init, work."'` — single-quoted bash literal.
- `EXPECTED_BANNER_LINES=( 'assistants-template — setup wizard' 'Story 5.1 scaffold — runnable entry point confirmed.' 'Story 5.2 (prompts + file generation) and Story 5.3 (skills install + MCP verification) extend this entry point in later epics.' 'Next: wait for Story 5.2 to land, or run manual onboarding steps from docs/setup.md.' )` — four non-blank banner lines from AC4.
- `SECRET_PATTERNS=( … 11 patterns … )` — copy verbatim from Story 4.4.
- `SECRET_EQUALS_LITERALS=( 'password=' 'token=' 'secret=' 'api_key=' )`.
- `BANNED_TERMS_REGEX='(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])'` — verbatim inheritance.
- `DEREK_FIXED_STRINGS=( Chiron MasteryLab "Agile Weekly" "Queen Creek" Gangplank "Bodybuilding.com" Integrum Omarchy derekneighbors.com Playrix Laurie Deke )` — twelve probes.
- `GH_PAT_ENV_NAME="GITHUB_PERSONAL_ACCESS_TOKEN"`; `GH_PAT_ALLOWLIST_PLACEHOLDER="__GH_PAT_NAME__"`.
- `EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 10 10 10 )` — fourteen-element vector.
- `EXPECTED_PREDECESSOR_SHA256=( … )` — fourteen-element positional-parallel SHA-256 array; see baseline audit.
- Byte-stability SHA-256 anchors (constant names):
  - `STORY_4_3_MCP_JSON_SHA256`
  - `STORY_4_3_MCP_README_SHA256`
  - `STORY_4_3_MCP_PLACEHOLDERS_SHA256`
  - `STORY_4_3_ENV_EXAMPLE_SHA256`
  - `STORY_1_1_GITIGNORE_SHA256`
  - `STORY_1_2_LICENSE_CANONICAL_SHA256`
  - `STORY_4_4_SETUP_MD_SHA256`
  - `STORY_4_4_MCPS_MD_SHA256`

## Frontmatter lock — `bin/init`

Line 1: `#!/usr/bin/env node`.

## Frontmatter lock — `package.json`

Line 1: `{` (no BOM, no comment; strict JSON).

## H1 lock / H2 sequence lock

Not applicable — Story 5.1 artifacts are code / JSON, not markdown. The "markdown shape" invariants from Stories 4.3 / 4.4 do not apply here. The structural equivalents are the top-level-key sequence for `package.json` and the function-set / shebang / banner for `bin/init`, both locked above.

## Terminator lock

Not applicable — code / JSON files have no markdown terminator. Trailing newline (LF) invariance is locked instead (AC1 last byte `0x0a`).

## Secret-pattern catalog lock / Banned-term lock / Derek probe lock / Placeholder-form probes / Shell-expansion probe

Inherited verbatim from Story 4.4. See inheritance-only note above.
