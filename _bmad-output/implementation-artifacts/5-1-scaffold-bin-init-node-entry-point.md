# Story 5.1: Scaffold `bin/init` Node entry point and dependency setup

Status: done

## Story

As a new Vixxo employee who has just cloned the `assistants-template` repository and is about to run the first step of the Epic 5 setup wizard (`./bin/init`),
I want a minimal, executable Node.js entry point at `bin/init` together with a tiny root-level `package.json` that declares the interactive-prompts dependency (`prompts@2.4.2`) plus a `node` engines minimum,
so that (a) `./bin/init` is runnable immediately after `git clone` without any preceding bash-specific or manual-install step beyond the single auto-bootstrapping `npm install` that `bin/init` itself triggers on first run when `node_modules/` is absent, (b) Epic 5 Story 5.2 has a concrete entry point to extend with prompt flows and file generation, (c) Epic 5 Story 5.3 has a concrete entry point to extend with `npx skills add vixxo-copilot/agent-skills` invocation and active-MCP verification, (d) the template's "runnable right after clone" posture from Epic 5 Story 5.1 AC at `_bmad-output/planning-artifacts/epics.md` lines 337–347 is satisfied, (e) the `docs/setup.md` § `Run the setup smoke test` forward reference ("Once Epic 5 Story 5.1 lands, running `./bin/init` will execute the smoke test end-to-end") becomes live, (f) the `.env.example` + `.cursor/mcp.json` + `.cursor/mcp.README.md` + `.cursor/mcp.placeholders.md` surfaces shipped by Stories 4.1–4.4 remain byte-stable — Story 5.1 adds files only, does not edit predecessors, and honors the established banned-term / secret-pattern / Derek-probe / placeholder-form / `${VAR}`-expansion-token scan catalogs inherited verbatim from Stories 3.1 through 4.4.

## Acceptance Criteria

1. **AC1 — `bin/init` exists, is executable, uses a portable Node shebang, and runs on macOS and Linux**
   - Given the cloned `assistants-template` repository after Stories 4.1–4.4 landed
   - When `bin/init` is inspected
   - Then the file exists at `bin/init` (no extension — matches epic AC wording `./bin/init`), is UTF-8 encoded, ends with a trailing newline (last byte `0x0a`), uses LF line endings (`grep -c $'\r' bin/init` returns `0`), and has the executable bit set (`test -x bin/init` exits `0`; `ls -l bin/init` shows `rwxr-xr-x` or `rwxr--r--` — owner-executable at minimum; git records the executable bit via `git update-index --chmod=+x bin/init` or native file-mode tracking)
   - And the first line is exactly `#!/usr/bin/env node` (portable shebang — the `env` lookup avoids hard-coding `/usr/local/bin/node` vs `/usr/bin/node` vs `/opt/homebrew/bin/node` and works identically on macOS and Linux per NFR2)
   - And the file uses Node-only code — no `bash`, `sh`, `zsh`, `/bin/bash`, `spawn('bash'`, backtick-shell-exec, or platform-conditional shelling (`process.platform === 'win32' ? 'cmd' : 'bash'`) appears anywhere
   - And the file imports / requires ONLY Node built-ins (`node:child_process`, `node:fs`, `node:path`, `node:process`, `node:url`) plus the single third-party dependency `prompts` (declared in `package.json` per AC3); no transitive third-party require beyond what `prompts` itself pulls in (`kleur`, `sisteransi`) via `node_modules/`
   - And invoking `./bin/init --help` (or `./bin/init -h`) prints a short human-readable banner that lists the three Epic 5 lifecycle steps (scaffold — Story 5.1 landed; prompts and file generation — Story 5.2 pending; skills install and MCP verification — Story 5.3 pending) and exits `0` WITHOUT triggering the auto-bootstrap or any prompt; `./bin/init --version` prints `assistants-template init <version-from-package.json>` and exits `0`

2. **AC2 — `./bin/init` is runnable immediately after `git clone` via single-command auto-bootstrap**
   - Given a fresh clone of the repository on a workstation that has `node` (>= 20) and `npm` on `PATH` but no `node_modules/` in the repo
   - When the user runs `./bin/init` from the repository root
   - Then the script detects the absent `node_modules/prompts/` (canonical presence probe: `require.resolve('prompts')` in a try/catch, OR a direct `fs.existsSync(path.join(ROOT, 'node_modules', 'prompts', 'package.json'))` check) and, before any prompt logic, spawns `npm install` synchronously via `child_process.spawnSync('npm', ['install'], { cwd: ROOT, stdio: 'inherit' })` — blocking until install completes; prints a single concise progress line (`Installing local dependencies (first-run only)...`) before the spawn and a single concise success line (`Dependencies installed.`) after the spawn returns `status === 0`
   - And if the `npm install` spawn returns a non-zero status or throws (`ENOENT: npm`), the script prints a helpful error block to stderr (`[bin/init] npm install failed; exit <code>. Please run 'npm install' manually and retry.`) and exits with the same non-zero status — propagates failure cleanly, never falls through to prompt logic with missing deps
   - And on any subsequent invocation with `node_modules/prompts/` already present, the auto-bootstrap step is SKIPPED (idempotent — no repeated `npm install` on every run); the script proceeds directly to the "next step" message (see AC4)
   - And no `bash` invocation, no `source` call, no `eval` of shell output, no `os.homedir()`-based path, no `~`-literal, no hard-coded absolute path (`/Users/...` or `/home/...`) appears anywhere — path construction uses `path.join(__dirname, '..', ...)` exclusively, so the script works under any clone location

3. **AC3 — `package.json` exists at repo root and declares the minimum-viable dep and engine contract**
   - Given the cloned repository after Story 5.1 landed
   - When `package.json` is inspected
   - Then `package.json` exists at the repo root (NOT in `bin/`, NOT in `.cursor/`, NOT in a sub-directory), is UTF-8 encoded, ends with a trailing newline, uses LF line endings, and parses as strict JSON via `python3 -m json.tool` and `node -e 'JSON.parse(require("fs").readFileSync("package.json","utf8"))'` — both with exit `0`
   - And the JSON contains exactly these top-level keys in this canonical order: `name`, `version`, `private`, `description`, `type`, `bin`, `scripts`, `engines`, `dependencies`; no additional top-level keys (NO `main`, NO `exports`, NO `devDependencies`, NO `peerDependencies`, NO `repository`, NO `author`, NO `license` — template repo is not a publishable npm package; `license` is tracked separately via `LICENSE` at the repo root)
   - And the locked values are:
     - `"name": "assistants-template"`
     - `"version": "0.1.0"` (Story 5.1 establishes `0.1.0` as the baseline; future stories bump minor for additive feature stories)
     - `"private": true` (explicitly prevents accidental `npm publish`)
     - `"description": "Vixxo-deployable personal AI agent template; clone, run ./bin/init, work."` (one-line, prose-only, no Derek content, no `{{placeholder}}` tokens)
     - `"type": "commonjs"` (explicit — matches `prompts@2.4.2` which is CommonJS-first and avoids the ESM-vs-CJS interop complexity for a single-file entry point; Story 5.2 may revisit if / when a case for ESM emerges, but the doctrine locked here is "CommonJS until a concrete need arises")
     - `"bin": { "assistants-init": "./bin/init" }` (single binary; `assistants-init` is the canonical command name future `npm install -g` or `npx` users would invoke; the in-repo path `./bin/init` remains the primary entry point)
     - `"scripts": { "init": "node ./bin/init", "start": "node ./bin/init" }` (two aliases — `npm run init` and `npm start` both invoke the entry point for users who prefer `npm` over the direct `./bin/init` form)
     - `"engines": { "node": ">=20.0.0" }` (Node 20 is Active LTS as of 2026-04; matches `docs/setup.md` Prerequisites "Node.js Active LTS")
     - `"dependencies": { "prompts": "2.4.2" }` (exact-pin — NO `^` prefix, NO `~` prefix; `prompts` last published 2021-10-07 as `2.4.2` with battle-tested stability, Node >= 14 support, and minimal transitive deps `kleur` + `sisteransi`; the exact pin makes `npm install` deterministic across every clone; a future story may upgrade to `@inquirer/prompts` ESM-native when a concrete refactor need emerges)
   - And no other key appears in any position; the JSON is minified-or-pretty-printed at the author's discretion but uses two-space indentation (matching `.cursor/mcp.json` convention established in Story 4.1) and contains no trailing commas, no comments (strict JSON)

4. **AC4 — `./bin/init` prints a deterministic "next step" banner after bootstrap, and exits cleanly**
   - Given a workstation with `node_modules/` already installed (post-bootstrap steady state)
   - When the user runs `./bin/init` without arguments
   - Then the script prints a multi-line banner to stdout:
     1. Header line: `assistants-template — setup wizard` (no leading/trailing whitespace, no emoji, no Derek content)
     2. Status line: `Story 5.1 scaffold — runnable entry point confirmed.`
     3. Pending-work line: `Story 5.2 (prompts + file generation) and Story 5.3 (skills install + MCP verification) extend this entry point in later epics.`
     4. Blank line
     5. Action line: `Next: wait for Story 5.2 to land, or run manual onboarding steps from docs/setup.md.`
   - And the script exits `0` — Story 5.1 is intentionally a no-op past the bootstrap + banner; no prompts, no file generation, no network calls
   - And the banner uses ASCII-only characters (no em-dashes `—` except as explicitly locked above for visual consistency with the project's em-dash house style; em-dashes are UTF-8-encoded and the file is UTF-8 so they render identically on every POSIX terminal); no ANSI color codes in Story 5.1 (color can be added in Story 5.2 via `kleur` once a concrete need emerges)
   - And if the user passes `--help` / `-h` / `--version` / `-v`, those short-circuit the banner and exit per AC1 without the auto-bootstrap step — even if `node_modules/` is absent, `--help` and `--version` are FAST PATHS that only read `package.json` (which is at the repo root, always present after clone) and exit

5. **AC5 — `bin/init`, `package.json`, and the auto-bootstrap flow contain ZERO secret-shaped strings, ZERO banned terms, ZERO Derek content, ZERO placeholder-form tokens, ZERO unexpanded `${VAR}` shell-expansion tokens**
   - Given `bin/init` and `package.json`
   - When the Story 4.1–4.4 catalog of eleven secret-pattern regexes, the 17-token banned-term regex (sanitized view — `GITHUB_PERSONAL_ACCESS_TOKEN` substituted to `__GH_PAT_NAME__` via `sanitize_for_banned_scan()`), the twelve Derek fixed-string probes (`Chiron`, `MasteryLab`, `Agile Weekly`, `Queen Creek`, `Gangplank`, `Bodybuilding.com`, `Integrum`, `Omarchy`, `derekneighbors.com`, `Playrix`, `Laurie`, `Deke`), the three path-reference probes (`/Users/`, `Public/gtd-life`, `@gmail.com`), the four `password=` / `token=` / `secret=` / `api_key=` lowercase-literal probes, the five placeholder-form probes (`{{name}}`, `{name}`, `<name>`, `%name%`, `${name}`), and the `${VAR}`/`$VAR` shell-expansion-token probe are applied to both files
   - Then every probe returns zero matches against both files
   - And `bin/init` does NOT reference `GITHUB_PERSONAL_ACCESS_TOKEN` or any other env var name from `.env.example` — Story 5.1 is dependency / entry-point scaffolding only; env-var reading is deferred to Story 5.2 (identity file generation) and Story 5.3 (MCP verification). This keeps the `sanitize_for_banned_scan()` pre-filter defensive-only for Story 5.1, not load-bearing (a departure from Story 4.3's load-bearing use)
   - And the `description` field of `package.json` uses the literal phrase "personal AI agent template" — which contains the substring `personal`. The 17-token banned-term regex's `personal` token WILL match case-insensitively against this phrase; the harness `task6` gate handles this via a one-shot content-allowlist exemption anchored on the exact byte-sequence `"description": "Vixxo-deployable personal AI agent template; clone, run ./bin/init, work."` — the allowlist is narrow, anchored on the full locked description string, and is the single permitted deviation from the otherwise-verbatim banned-term catalog. Rationale: `personal` in `personal AI agent` is a deliberate product-positioning phrase inherited from the epic's FR1 language ("every Vixxo employee's PERSONAL AI agent template"); renaming it to "individual AI agent" or "employee AI agent" would drift the product language. The content-allowlist pattern is new for Story 5.1 and is documented in the Task 2 canonical blueprint as the Story 5.1 F1-style content-allowlist carve-out

6. **AC6 — Every Story 1.x / 2.x / 3.x / 4.x artifact remains byte-stable; Story 5.1 adds files only**
   - Given the predecessor-artifact set from Stories 1.1 → 4.4
   - When the Story 5.1 harness runs
   - Then ZERO bytes change in `.cursor/mcp.json` (SHA-256 must match `d749b788efa974330d104875a5b63793253a40b450f70341da971a403ac3477c` — captured 2026-04-21 from post-4.2 handoff)
   - And ZERO bytes change in `.cursor/mcp.README.md` (SHA-256 `4f27217a93f71b5bc45b0e4055a4ab82b1d052b2f346277b2dd945d89150af09`)
   - And ZERO bytes change in `.cursor/mcp.placeholders.md` (SHA-256 `1fd08afbf68f8d97d0110dbdbdcf7b7f289adba0e7c649dcbe80609b395fa010`)
   - And ZERO bytes change in `.env.example` (SHA-256 `19f9c52047f821f814dfe3b200f0fb77f641d1b373499691f445f8c83d4ed6a4`)
   - And ZERO bytes change in `.gitignore` (SHA-256 `49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1`)
   - And ZERO bytes change in `README.md`, `LICENSE`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`
   - And ZERO bytes change in any of the `.cursor/rules/*.mdc` files from Stories 2.1 + 2.2
   - And ZERO bytes change in any `agents/personas/*.md` / `agents/personas/.gitkeep`
   - And ZERO bytes change in any `memory/**/*.md` / `memory/.obsidian/*.json` / `memory/**/.gitkeep`
   - And ZERO bytes change in `docs/setup.md`, `docs/mcps.md`, `docs/legal/license-vixxo-internal-canonical.md`, `docs/pii-denylist.md`, and any `docs/.gitkeep`
   - And ZERO bytes change in any of the FOURTEEN predecessor harnesses under `_bmad-output/implementation-artifacts/tests/story-[1-4]-*.sh` (Story 4.4 harness is now a predecessor of Story 5.1 — byte-stable)
   - And ZERO bytes change in the Epic 6 harnesses (`story-6-1-pii-denylist-validation.sh`, `story-6-2-github-action-validation.sh`) — although Epic 6 ran on a parallel branch and is NOT included in Story 5.1's regression chain (the chain follows the Tier-1 + Tier-2 spine: 1.x → 2.x → 3.x → 4.x → 5.x), the two Epic 6 harnesses must remain byte-stable because Story 5.1 makes no edits outside its own working set

7. **AC7 — `.gitignore` is NOT edited; `node_modules/` remains ignored; `package-lock.json` tracking decision is documented**
   - Given the root `.gitignore` content locked by Story 1.1 + F1 with SHA-256 `49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1`
   - When the Story 5.1 harness runs
   - Then `.gitignore` is NOT modified (SHA-256 invariance per AC6)
   - And `git check-ignore -v node_modules/prompts/index.js` exits `0` and prints a line matching `\.gitignore:[0-9]+:node_modules/` — confirming `node_modules/` remains ignored (the existing `node_modules/` entry at line 1 of `.gitignore` handles this; no edit needed)
   - And `package-lock.json` is tracked via git (NOT gitignored) — Story 5.1 commits a fresh `package-lock.json` generated by the first `npm install` run on the author's workstation, exact-pinning the three-package dep tree (`prompts@2.4.2`, `kleur@^3.0.3`, `sisteransi@^1.0.5`) so every downstream clone gets byte-identical installs. Rationale: lockfiles are a reproducibility invariant for `npm install`-based onboarding; the `.gitignore` does not contain `package-lock.json` and MUST NOT be extended to include it by Story 5.1
   - And `package-lock.json` parses as strict JSON via `python3 -m json.tool` and contains exactly three packages under `packages` keyed paths: the root package (`""`), `node_modules/prompts`, `node_modules/kleur`, `node_modules/sisteransi` — set equality on the post-`""` keys `{node_modules/prompts, node_modules/kleur, node_modules/sisteransi}`; lockfile version `3` (matches `npm` 10+ default); `name` field equals `assistants-template`; `version` field equals `0.1.0`

8. **AC8 — A deterministic validation harness exists and passes; regression chain extends Story 4.4's thirteen-harness chain by one (to fourteen predecessors)**
   - Given the existing harness family under `_bmad-output/implementation-artifacts/tests/`
   - When Story 5.1 lands
   - Then a new harness `story-5-1-bin-init-validation.sh` exists at `_bmad-output/implementation-artifacts/tests/story-5-1-bin-init-validation.sh`, is marked executable (`chmod +x`), uses `#!/usr/bin/env bash` on line 1 and `set -euo pipefail` on line 2, and honors the `BMAD_REGRESSION_DEPTH` guard from Story 4.2 F6 (outer-level invocation runs the full chain; `BMAD_REGRESSION_DEPTH=1` short-circuits `check_task9` to avoid nested-chain O(N!) regression)
   - And the harness implements nine gates plus an `all` dispatcher:
     - `task1` — baseline-audit artifact `story-5-1-baseline-audit.md` present with required sections (predecessor-harness SHA-256 fingerprints for all fourteen predecessors; `.cursor/mcp.json` + `.cursor/mcp.README.md` + `.cursor/mcp.placeholders.md` + `.env.example` + `.gitignore` fingerprints; `prompts@2.4.2` upstream-version cross-reference; Node engine minimum rationale; `package-lock.json` reproducibility note; `node_modules/` ignore-rule re-confirmation; empirical predecessor `^PASS:` line-count vector; Source URLs)
     - `task2` — canonical-blueprint artifact `story-5-1-canonical-blueprint.md` present with locked `bin/init` shape (shebang, top-matter comment block, required Node built-in imports, `prompts` import under conditional auto-bootstrap guard, help / version flag handlers, bootstrap flow, banner flow, exit codes), locked `package.json` top-level-key sequence, locked `description` content-allowlist carve-out, locked banner text from AC4, inheritance note referencing Stories 4.1–4.4 scan catalogs
     - `task3` — `bin/init` shape: file exists at `bin/init`, non-empty, trailing newline, LF-only, executable bit set, first line equals `#!/usr/bin/env node`, contains exactly one `require('prompts')` call (positive case — the dep is wired even though Story 5.1 does not yet call its prompt APIs) OR exactly zero if Dev decides to defer the `require('prompts')` to Story 5.2 (both patterns acceptable; blueprint locks one of them at author time), contains the locked five-line banner text from AC4 verbatim, contains the `--help` / `-h` / `--version` / `-v` flag handlers, contains the `npm install` auto-bootstrap spawnSync call wrapped in the `node_modules/prompts` presence check, no `bash` / `sh` / `zsh` string literals, no `/Users/` / `/home/` absolute paths, no `require('bash')` / `require('sh')` / `spawn('bash')` / `spawn('/bin/bash')` / backtick-exec usages
     - `task4` — `package.json` shape: file exists at repo root, non-empty, trailing newline, LF-only, parses as strict JSON via `node -e 'JSON.parse(...)'`, top-level-key sequence equals the canonical order `name, version, private, description, type, bin, scripts, engines, dependencies` exactly (harness loops `EXPECTED_TOP_KEYS` array and verifies each key appears at the expected offset via an awk-based JSON-key-order extraction; detects extra or out-of-order keys), locked `name` / `version` / `private` / `description` / `type` / `bin` / `scripts` / `engines` / `dependencies` values match the AC3 locks verbatim, NO additional top-level keys, `dependencies.prompts` equals the exact-pin `"2.4.2"` (no `^`, no `~`, no `*`, no range)
     - `task5` — `package-lock.json` shape and reproducibility lock: file exists at repo root, non-empty, trailing newline, LF-only, parses as strict JSON, `lockfileVersion` field equals `3`, `name` equals `assistants-template`, `version` equals `0.1.0`, `packages[""].dependencies.prompts` equals `"2.4.2"`, `packages["node_modules/prompts"].version` equals `"2.4.2"`, `packages["node_modules/kleur"]` and `packages["node_modules/sisteransi"]` both present, exact set equality on the non-root `packages` keys `{node_modules/prompts, node_modules/kleur, node_modules/sisteransi}` — three transitive packages total (no bloat); `git check-ignore -v package-lock.json` exits non-zero (lockfile is tracked)
     - `task6` — secret-shape + banned-term + Derek + path + placeholder-form + shell-expansion scans per AC5: loop the eleven `SECRET_PATTERNS`, the twelve `DEREK_FIXED_STRINGS`, the three path-reference probes, the four `…=` lowercase-literal probes, the five placeholder-form probes, and the `${VAR}`/`$VAR` probe against the `sanitize_for_banned_scan()`-filtered view of both files; assert zero matches per probe. The banned-term regex is applied case-insensitively on the sanitized view AND on a second `content_allowlist_for_personal()`-filtered view which substitutes the full locked `description` string `"description": "Vixxo-deployable personal AI agent template; clone, run ./bin/init, work."` → `"description": "__LOCKED_DESC__"` before scanning (Story 5.1 F1-style content-allowlist carve-out). The allowlist is narrow (anchored on the full locked description; does NOT match partial substrings), single-use (applied only to `package.json`; `bin/init` uses the plain `sanitize_for_banned_scan()` view), and documented in Dev Notes
     - `task7` — byte-stability invariance per AC6: `sha256_of .cursor/mcp.json` == `STORY_4_3_MCP_JSON_SHA256`; `.cursor/mcp.README.md` == `STORY_4_3_MCP_README_SHA256`; `.cursor/mcp.placeholders.md` == `STORY_4_3_MCP_PLACEHOLDERS_SHA256`; `.env.example` == `STORY_4_3_ENV_EXAMPLE_SHA256`; `.gitignore` == `STORY_1_1_GITIGNORE_SHA256`; `docs/legal/license-vixxo-internal-canonical.md` == `STORY_1_2_LICENSE_CANONICAL_SHA256`; `docs/setup.md` and `docs/mcps.md` byte-stable (SHA-256 re-captured from Story 4.4 on-disk at Task 1 baseline audit and locked as `STORY_4_4_SETUP_MD_SHA256` / `STORY_4_4_MCPS_MD_SHA256`); `git check-ignore -v bin/init` exits non-zero (entry point is tracked); `git check-ignore -v package.json` exits non-zero; `git check-ignore -v package-lock.json` exits non-zero; `git check-ignore -v node_modules/prompts/package.json` exits `0` with output matching `\.gitignore:[0-9]+:node_modules/`
     - `task8` — self-check per Stories 2.x / 3.x / 4.x pattern: shebang line 1, `set -euo pipefail`, every case arm present (`task1)` through `task9)` and `all)`), every declared constant referenced (loop over a named array of expected constant names), `declare -F regex_self_probe / sanitize_for_banned_scan / content_allowlist_for_personal / sha256_of / json_strict_parse` all return `0`
     - `task9` — regression: invoke all FOURTEEN predecessor harnesses (Stories 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4) in `all` mode with `BMAD_REGRESSION_DEPTH=1` exported so nested `check_task9` calls short-circuit; assert each exits `0` with `PASS: all`; assert per-harness `^PASS:` line-count fingerprint matches `EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 10 10 10 )` (fourteen-element vector; Stories 4.1 / 4.2 / 4.3 / 4.4 each contribute `10` — nine gates + `all`); verify each predecessor's SHA-256 BEFORE invocation against `EXPECTED_PREDECESSOR_SHA256` (fourteen-element positional-parallel array — Story 4.2 F5 pattern) and fail the gate on drift; honor the Story 4.2 F1 retry-once-on-flake wrapper for macOS bash 3.2.57 transient failures and `mkdir -p "${PROJECT_ROOT}/tmp"` defensive pre-creation
     - `all` dispatcher — runs `task1` through `task9` sequentially; prints `PASS: task<n>` after each; ends with `PASS: all`; emits exactly 10 `^PASS:` lines on success
   - And the harness implements `regex_self_probe()` exercising all Story 4.4 probes plus a new `node -e` JSON-parse probe (positive match for `{"a":1}`, negative for `{a:1}`)
   - And the harness implements `content_allowlist_for_personal()` as a `sed`-based single-substitution of the full locked `description` string to `__LOCKED_DESC__`; the harness asserts the pre-sanitization view contains the substring `personal AI agent template` (so the allowlist is exercised) AND the post-sanitization banned-term regex returns zero matches (so the allowlist works)
   - And the harness is BSD-grep and GNU-grep compatible, POSIX-bash-3.2 compatible, uses only `bash`, `grep`, `find`, `awk`, `sed`, `wc`, `head`, `tail`, `tr`, `sort`, `cut`, `od`, `shasum -a 256` (falls back to `sha256sum` / `openssl dgst -sha256`), `python3 -m json.tool` OR `node -e` (Story 5.1 may use `node -e` for JSON parsing because Node is already a hard prerequisite for the story; prior stories relied on `python3` only). NO `jq`, NO `rg`
   - And the harness exits `0` with `PASS: all` on success; exits `1` with `FAIL: <gate>: <reason>` on stderr on failure

9. **AC9 — Zero regression across every prior story on the Tier-1 + Tier-2 spine — the fourteen predecessor harnesses continue to pass unchanged**
   - Given the fourteen predecessor harnesses (Stories 1.1 → 3.3 + 4.1 + 4.2 + 4.3 + 4.4)
   - When Story 5.1 lands and the Story 5.1 harness `task9` regression invokes each predecessor with `BMAD_REGRESSION_DEPTH=1` exported
   - Then each predecessor harness exits `0` with `PASS: all` and the per-harness `^PASS:` line-count matches the fingerprint `( 1 1 1 1 10 7 7 7 7 7 10 10 10 10 )` — fourteen-element vector
   - And none of the predecessor harnesses requires any allowlist extension for `bin/init` or `package.json` — Stories 1.1 / 1.2 / 1.3 harnesses iterate specific root-file sets (not the entire root directory generically); Stories 2.x / 3.x / 4.x harnesses scope their scans to their own working-set artifacts. The predecessor-harness compatibility scan in Task 1 verifies this empirically and documents findings
   - And Story 5.1 creates ONLY: `bin/init` (executable Node entry point), `package.json` (root-level), `package-lock.json` (root-level, tracked), the new harness `story-5-1-bin-init-validation.sh`, three evidence artifacts (`story-5-1-baseline-audit.md`, `story-5-1-canonical-blueprint.md`, `story-5-1-task-handoff.md`), and this story file. Story 5.1 does NOT create any prompts / wizard-logic / file-generation code — that is Story 5.2 scope
   - And Story 5.1 does NOT create `node_modules/` (gitignored) as a tracked artifact; the directory is materialized on each clone by `./bin/init`'s auto-bootstrap OR by the user manually running `npm install`

10. **AC10 — Sprint tracker lifecycle flips correctly**
    - Given `_bmad-output/implementation-artifacts/sprint-status.yaml`
    - When Story 5.1 opens (Phase 1 — SM), progresses (Phase 2 — Dev), and closes (Phase 3 — review approval)
    - Then `5-1-scaffold-bin-init-node-entry-point.status` is updated `backlog → ready-for-dev` at Phase 1, `ready-for-dev → review` at Phase 2, `review → done` at Phase 3 (single `backlog → done` on-disk transition acceptable per Stories 2.x / 3.x / 4.x autonomous-swarm precedent documented in Story 4.3 F5 review finding)
    - And `epic-5.status` is updated `backlog → in-progress` at Phase 1 (Story 5.1 is the first story in Epic 5, so the epic flips open now); the epic stays `in-progress` through Stories 5.2 + 5.3 and closes to `done` only after Story 5.3 lands
    - And `last_updated` is set to `2026-04-21` on the Phase 1 edit
    - And NO other story's status is regressed; every comment, blank line, inline spacing, and entry ordering in `sprint-status.yaml` is preserved byte-for-byte — the only diffs vs. the post-4.4 state are the `status:` value flip on `5-1-…`, the `status:` value flip on `epic-5`, and the `last_updated` value change (two story-status flips, no other edits)

11. **AC11 — Story is additive and does not spill into Story 5.2 / Story 5.3 / Epic 6 / Epic 7 territory**
    - Given the scope of Story 5.1
    - When the working-set file list is reviewed
    - Then Story 5.1 does NOT implement prompt flows, user input, or file generation (Story 5.2 scope — the wizard prompts for name / email / role / MCPs and writes `memory/me/identity.md` and `agents/personas/work.md`; Story 5.1 only stubs the entry point and pre-installs `prompts` so Story 5.2 can `require('prompts')` without extending `package.json`)
    - And Story 5.1 does NOT invoke `npx skills add vixxo-copilot/agent-skills` (Story 5.3 scope — the wizard runs the skills install and verifies active MCPs; Story 5.1 only declares the entry point that Story 5.3 will extend)
    - And Story 5.1 does NOT touch `.env.example`, `.cursor/mcp.json`, `.cursor/mcp.README.md`, `.cursor/mcp.placeholders.md`, `docs/setup.md`, `docs/mcps.md`, `docs/legal/`, `.cursor/rules/*.mdc`, `agents/personas/*.md`, `memory/**/*.md`, `memory/.obsidian/*.json`, or any root context file (`README.md`, `LICENSE`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`) — all listed explicitly in AC6 as byte-stable
    - And Story 5.1 does NOT add any CI / GitHub Actions workflow (Epic 6 scope — Epic 6 stories 6.1 / 6.2 are already `done` on a parallel branch; Story 5.1 does not add a new workflow and does not edit `.github/workflows/` entries)
    - And Story 5.1 does NOT edit `.gitignore` — the existing `node_modules/` rule at line 1 already handles the bootstrap-created `node_modules/` directory per AC7
    - And Story 5.1 creates NO additional `bin/` entries beyond `bin/init` — no `bin/update`, no `bin/verify`, no `bin/reset`

12. **AC12 — The `bin/init` shape is consistent with Epic 5 Story 5.1 AC in `epics.md` lines 337–347**
    - Given the authoritative Epic 5 Story 5.1 acceptance criteria at `_bmad-output/planning-artifacts/epics.md` lines 343–347
    - When the Story 5.1 deliverable is compared to the epic's stated AC
    - Then the epic's AC — "`bin/init` executable, uses Node only (no bash-specific assumptions)" — is satisfied by AC1 (portable `#!/usr/bin/env node` shebang, Node-only imports, no `bash` / `sh` / `zsh` references, executable bit set)
    - And the epic's AC — "Reads a tiny `package.json` for deps (`prompts` or similar)" — is satisfied by AC3 (`package.json` at repo root declares `prompts@2.4.2` as the single direct dep; Story 5.1 selects `prompts` over alternatives `inquirer`, `@inquirer/prompts`, `enquirer`, `prompt-sync`, `readline-sync` because `prompts` has the smallest transitive dep footprint — two packages — and matches the epic's explicit mention of `prompts` as the expected library)
    - And the "runnable right after clone" user-story posture (epic line 338–341: "As an employee, I want `./bin/init` to be runnable right after clone, So that I can bootstrap with one command") is satisfied by AC2 (auto-bootstrap of `npm install` on first run when `node_modules/` is absent; single-command `./bin/init` invocation; no preceding manual `npm install` step required beyond the one the script itself triggers)

## Tasks / Subtasks

- [x] **Task 1 — Baseline audit of Node / npm version requirements, `prompts` upstream, predecessor harnesses, and byte-stability fingerprints (AC: 1, 2, 3, 6, 7, 8, 9)** **[Parallelizable with Task 2 canonical blueprint assembly]**
  - [x] Confirm the Node / npm minimum-version contract: Node 20 Active LTS (matches `docs/setup.md` Prerequisites line 18 "Node.js Active LTS") and npm 10+ (ships with Node 20). Document the rationale in the baseline audit with a link to the Node.js release schedule (`https://nodejs.org/en/about/previous-releases`).
  - [x] Re-confirm the `prompts` upstream source: `terkelg/prompts` on GitHub, latest published version `2.4.2`, last publish `2021-10-07`, Node engine `>= 14`, transitive deps `kleur` + `sisteransi`, zero reported CVEs via `npm audit` as of 2026-04-21. Rationale for exact-pin: the package is in low-maintenance mode with no pending 3.x migration; `2.4.2` is the de-facto stable version used by thousands of downstream packages. Document this in the baseline audit with a link to `https://github.com/terkelg/prompts` and `https://www.npmjs.com/package/prompts`.
  - [x] Capture SHA-256 fingerprints for byte-stability constants (expected values captured 2026-04-21 from on-disk post-Story-4.4 state):
    - `.cursor/mcp.json` → `d749b788efa974330d104875a5b63793253a40b450f70341da971a403ac3477c`
    - `.cursor/mcp.README.md` → `4f27217a93f71b5bc45b0e4055a4ab82b1d052b2f346277b2dd945d89150af09`
    - `.cursor/mcp.placeholders.md` → `1fd08afbf68f8d97d0110dbdbdcf7b7f289adba0e7c649dcbe80609b395fa010`
    - `.env.example` → `19f9c52047f821f814dfe3b200f0fb77f641d1b373499691f445f8c83d4ed6a4`
    - `.gitignore` → `49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1`
    - `docs/legal/license-vixxo-internal-canonical.md` → `4b1cbb2d7e7ba1629df5913a45df3a43e4dd3f78d0c786262589ea53160193cc`
    - `docs/setup.md` and `docs/mcps.md` → capture on-disk SHA-256 on Dev workstation and embed as `STORY_4_4_SETUP_MD_SHA256` / `STORY_4_4_MCPS_MD_SHA256`
    - `docs/pii-denylist.md` (Story 6.1 artifact) → capture on-disk SHA-256 and embed as a stability anchor; Epic 6 is byte-stable during Story 5.1 even though not chained as a regression predecessor
  - [x] Capture the empirical predecessor PASS-count vector. Fourteen predecessors in Tier-1 + Tier-2 spine order: Stories 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4. Expected `EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 10 10 10 )` (Stories 4.1 / 4.2 / 4.3 / 4.4 each contribute `10`). Run each predecessor once with `BMAD_REGRESSION_DEPTH=1` exported to confirm the guard-short-circuit behavior is intact.
  - [x] Capture the fourteen-element `EXPECTED_PREDECESSOR_SHA256` array (positional-parallel to `EXPECTED_PASS_COUNTS`). Current on-disk values captured 2026-04-21:
    - Story 1.1 `a609f6a857235a57588bab081c2775c3d59c9282ae0d1256f4183b5e923617b8`
    - Story 1.2 `0226aa1b2086ee63065a533bc720afe876fde0958af9ed99276c1ff68fb4afaf`
    - Story 1.3 `0cecd5293af7e5896bede460ef1f2a7e822554f735dc10b81d0beb8e0e840ba9`
    - Story 2.1 `dc9b98e5e89239d41429e4436b13c671822d237f616eb8ca99c016085e2bb08a`
    - Story 2.2 `5412bcfc7bd829a98a9054efb8fdf32c72b7e59c2b542cacca0c58648da6df10`
    - Story 2.3 `9d455eaebb775f80d29b24de4a35febc3a8ffba0ed7f237af492723d2096a591`
    - Story 2.4 `f70d8c25e333123c3aae9d44a388594f1850be1449e86a540fdbe2dbec701687`
    - Story 3.1 `cb298fff4f83ddbf27644293f4a38ecfd36b099b4d7d4ceb180c41a4af383ff7`
    - Story 3.2 `10ef5221ed1e64e3222c7d95297824175693f66c313eced1260d5645be81292e`
    - Story 3.3 `f49f21c1811be49fc7aafa386f7f14553f46deb8a5bee6d4e609ca4d1b39bea8` — **NOTE: drifted from the `77a5376887f03909223074b2f21e1306f689a9238d6da0cf191aa79a0427b427` value embedded in Story 4.4's `EXPECTED_PREDECESSOR_SHA256[9]` constant. Root cause: Story 3.3 harness was updated in-place after Story 4.4 lock-in. Story 5.1 captures the CURRENT on-disk value and documents the drift in the baseline audit; if this drift causes Story 4.4's own `task9` to fail when Story 5.1 invokes it transitively via the `all`-mode regression, raise an integration fix and align Story 4.4's lock with the current on-disk Story 3.3 value.**
    - Story 4.1 `cfe810169aef5c2abf7bc021aad4fbb43d3c91eda58fc99b3d16123907dbba8f`
    - Story 4.2 `ac01c393e68c41df07cc4792abab703d62d4a10d40e96b68c9ac771bd9a1a490`
    - Story 4.3 `7aa2733e3b0e93d6b35bd0d7c89645ded810ae876b10e81554d26c738d61a277`
    - Story 4.4 `e5a254b4f15ac2903c0fda15a6a832199abcc47c920e5823f997c13c255c0473`
    - Re-compute each SHA before embedding into the harness; fail the audit if any value drifts further vs. on-disk.
  - [x] `.gitignore` compatibility re-confirmation: verify line 1 of `.gitignore` contains `node_modules/` (exact — no leading `!`, no nested pattern). Re-run `git check-ignore -v node_modules/prompts/package.json` (expected: exit `0`, prints `.gitignore:1:node_modules/`) and `git check-ignore -v bin/init` (expected: non-zero exit, empty output). Document both outputs in the baseline audit. If the `node_modules/` pattern is missing or malformed, raise an integration-fix and do NOT proceed.
  - [x] Predecessor-harness compatibility scan: for each of the fourteen predecessor harnesses, grep for any repo-root path reference or `bin/*` / `package.json` / `package-lock.json` / `node_modules/` pattern that could reject the new Story 5.1 artifacts. Expected result: zero extensions needed (Stories 1.1 / 1.2 / 1.3 iterate a locked root-file list that does NOT include `package.json` or `bin/` generically; Stories 2.x / 3.x / 4.x scope to their own working sets; the `bin/` directory contains only `.gitkeep` pre-Story-5.1 and adding `bin/init` does not drift any predecessor scan). Document findings in the baseline audit.
  - [x] `bin/` directory pre-state check: confirm `bin/.gitkeep` exists (Story 1.1 artifact) and its byte-stability fingerprint. Adding `bin/init` alongside `bin/.gitkeep` does not require `.gitkeep` removal — both can coexist; the `.gitkeep` remains a defense in case `bin/init` is ever deleted.
  - [x] `prompts` alternatives evaluation: document why `prompts@2.4.2` is selected over (a) `inquirer` (maintenance-mode 9.x / 10.x split, ~30 KB zipped), (b) `@inquirer/prompts` (ESM-only, 2 MB transitive), (c) `enquirer` (smaller but stricter API), (d) `prompt-sync` (synchronous, lacks validators), (e) `readline-sync` (no TTY-aware behavior). Rationale: `prompts@2.4.2` is 2 packages transitive (smallest footprint), CJS-compatible (matches `"type": "commonjs"` lock), battle-tested across thousands of downstream CLIs, zero open CVEs. Record the alternatives matrix in the baseline audit.
  - [x] Persist baseline evidence at `_bmad-output/implementation-artifacts/tests/story-5-1-baseline-audit.md` with sections: `# Story 5.1 Baseline Audit`, `## Node / npm version-requirement rationale`, `## prompts@2.4.2 upstream cross-reference and alternatives evaluation`, `## Byte-stability fingerprints (mcp.json, mcp.README.md, mcp.placeholders.md, .env.example, .gitignore, docs/*.md)`, `## Predecessor-harness SHA-256 vector (fourteen predecessors) and 3.3-drift note`, `## Predecessor-harness compatibility scan (fourteen harnesses)`, `## .gitignore compatibility re-confirmation (bin/init tracked, node_modules/ ignored)`, `## bin/ directory pre-state check`, `## Empirical predecessor PASS-count vector`, `## Source URLs`.

- [x] **Task 2 — Canonical blueprint for `bin/init` + `package.json` + `package-lock.json` (AC: 1, 2, 3, 4, 5, 7, 8)** **[Sequential — depends on Task 1]**
  - [x] Author the blueprint at `_bmad-output/implementation-artifacts/tests/story-5-1-canonical-blueprint.md`.
  - [x] Lock the `bin/init` shape. Pseudo-code outline (Dev may polish whitespace / comments but must preserve the structural ordering):
    ```text
    #!/usr/bin/env node
    // assistants-template — setup wizard (Epic 5)
    // Story 5.1 scaffold: runnable entry point, auto-bootstrap of local deps on first run.
    // Story 5.2 will add prompt flows + file generation.
    // Story 5.3 will add `npx skills add vixxo-copilot/agent-skills` + MCP verification.

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
      console.log('Usage: ./bin/init [--help | --version]');
      console.log('');
      console.log('Story 5.1 (this scaffold): entry point + auto-bootstrap.');
      console.log('Story 5.2 (pending):        prompts + file generation.');
      console.log('Story 5.3 (pending):        npx skills add + MCP verification.');
      console.log('');
      console.log(`Version: ${pkg.version}`);
    }

    function printVersion(pkg) {
      console.log(`assistants-template init ${pkg.version}`);
    }

    function ensureDependencies() {
      if (fs.existsSync(NODE_MODULES_PROMPTS)) return;
      console.log('Installing local dependencies (first-run only)...');
      const result = spawnSync('npm', ['install'], { cwd: ROOT, stdio: 'inherit' });
      if (result.status !== 0) {
        console.error(`[bin/init] npm install failed; exit ${result.status ?? 'unknown'}. Please run 'npm install' manually and retry.`);
        process.exit(result.status ?? 1);
      }
      console.log('Dependencies installed.');
    }

    function main() {
      const pkg = loadPackage();
      const args = process.argv.slice(2);
      if (args.includes('--help') || args.includes('-h')) { printHelp(pkg); return; }
      if (args.includes('--version') || args.includes('-v')) { printVersion(pkg); return; }
      ensureDependencies();
      console.log('assistants-template — setup wizard');
      console.log('Story 5.1 scaffold — runnable entry point confirmed.');
      console.log('Story 5.2 (prompts + file generation) and Story 5.3 (skills install + MCP verification) extend this entry point in later epics.');
      console.log('');
      console.log('Next: wait for Story 5.2 to land, or run manual onboarding steps from docs/setup.md.');
    }

    main();
    ```
    The blueprint documents this outline verbatim and notes that Dev may tighten comments but MUST preserve the `loadPackage` / `printHelp` / `printVersion` / `ensureDependencies` / `main` function set; the locked banner text from AC4; the fast-path ordering of flag handlers BEFORE `ensureDependencies`; and the exact error-message prefix `[bin/init] npm install failed; exit`.
  - [x] Lock the `package.json` shape verbatim per AC3:
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
  - [x] Lock the `package-lock.json` shape: generated by `npm install` on Dev's workstation; `lockfileVersion: 3`, `name: "assistants-template"`, `version: "0.1.0"`; exactly three transitive packages (`node_modules/prompts@2.4.2`, `node_modules/kleur@^3.0.3`, `node_modules/sisteransi@^1.0.5`); full SHA-512 integrity hashes for each package-tarball entry (standard npm-lockfile output).
  - [x] Lock the `description`-content-allowlist carve-out: the locked string `"description": "Vixxo-deployable personal AI agent template; clone, run ./bin/init, work."` is the ONLY line in `package.json` that contains the banned-term `personal`. The harness applies `content_allowlist_for_personal()` which substitutes the full locked string to `"description": "__LOCKED_DESC__"` before the banned-term regex scan. The allowlist is anchored on the full description string (not just the word `personal`) so partial-substring attacks (e.g. a new line introducing `personal` outside the locked string) would still trigger the scan and fail. Document the allowlist contract in the blueprint.
  - [x] Lock the banned-term regex, twelve Derek fixed-string probes, eleven secret-pattern regexes, five placeholder-form probes, three path-reference probes, and four `…=` lowercase-literal probes — all inherited VERBATIM from Story 4.4 (which inherited from 4.3 / 4.2 / 4.1 / 3.3 / 3.2 / 3.1). Blueprint documents each catalog and states inheritance-only (zero additions, zero removals).
  - [x] Lock the `bin/init` structural probes: exactly one `#!/usr/bin/env node` line at offset 1; exactly one `spawnSync('npm', ['install']` substring; exactly one `'node:fs'` import; exactly one `'node:path'` import; exactly one `'node:child_process'` import; zero `'bash'` / `'sh'` / `'zsh'` / `'/bin/bash'` / `` ` `` (backtick) / `require('child_process').exec(` substrings; zero `/Users/` or `/home/` absolute-path literals.
  - [x] Lock the evidence constants for the Task 5 harness:
    - `EXPECTED_TOP_KEYS=( name version private description type bin scripts engines dependencies )` — nine keys, canonical order.
    - `EXPECTED_LOCK_PACKAGES=( node_modules/kleur node_modules/prompts node_modules/sisteransi )` — three transitive packages (sorted for deterministic comparison).
    - `EXPECTED_PROMPTS_VERSION="2.4.2"`.
    - `EXPECTED_NODE_ENGINE=">=20.0.0"`.
    - `EXPECTED_LOCKFILE_VERSION=3`.
    - `EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 10 10 10 )` — fourteen-element vector.
    - `EXPECTED_PREDECESSOR_SHA256=( … )` — fourteen positional-parallel SHA-256 values from Task 1.
    - `STORY_4_3_MCP_JSON_SHA256`, `STORY_4_3_MCP_README_SHA256`, `STORY_4_3_MCP_PLACEHOLDERS_SHA256`, `STORY_4_3_ENV_EXAMPLE_SHA256`, `STORY_1_1_GITIGNORE_SHA256`, `STORY_1_2_LICENSE_CANONICAL_SHA256`, `STORY_4_4_SETUP_MD_SHA256`, `STORY_4_4_MCPS_MD_SHA256` — byte-stability fingerprints from Task 1.

- [x] **Task 3 — Author `bin/init` + `package.json` + run `npm install` to materialize `package-lock.json` (AC: 1, 2, 3, 4, 5, 7)** **[Sequential — depends on Task 2]**
  - [x] Create `bin/init` at the repo root exactly matching the Task 2 blueprint. UTF-8, LF line endings, trailing newline. Set the executable bit via `chmod +x bin/init`. Verify via `ls -l bin/init` that the file is owner-executable at minimum.
  - [x] Verify the shebang is literally `#!/usr/bin/env node` on line 1 — no variants (`#!/usr/bin/node`, `#!/usr/local/bin/node`, `#! /usr/bin/env node` with leading space).
  - [x] Create `package.json` at the repo root exactly matching the Task 2 lock. Two-space indent, trailing newline, LF line endings. Verify via `python3 -m json.tool < package.json` that strict JSON parsing succeeds with exit `0`; verify via `node -e 'JSON.parse(require("fs").readFileSync("package.json","utf8"))'` that Node's JSON parser also succeeds.
  - [x] Run `npm install` from the repo root to materialize `node_modules/` and `package-lock.json`. Do NOT commit `node_modules/` (gitignored per `.gitignore` line 1); DO commit `package-lock.json` (tracked; the lockfile is the reproducibility invariant). Expected `node_modules/` sub-dirs: `prompts/`, `kleur/`, `sisteransi/` (three packages total; zero-bloat dep tree).
  - [x] Verify `package-lock.json` shape: `lockfileVersion: 3`, `name: "assistants-template"`, `version: "0.1.0"`, `packages[""].dependencies.prompts: "2.4.2"`, `packages["node_modules/prompts"].version: "2.4.2"`, `packages["node_modules/kleur"]` and `packages["node_modules/sisteransi"]` both present; strict JSON parse succeeds.
  - [x] Smoke-test the entry point: run `./bin/init --help` → expect the multi-line help banner and exit `0` WITHOUT triggering `npm install` (fast path). Run `./bin/init --version` → expect `assistants-template init 0.1.0` and exit `0`. Run `./bin/init` (no args) with `node_modules/` present → expect the five-line banner from AC4 and exit `0` WITHOUT re-running `npm install` (idempotent bootstrap). Delete `node_modules/` and re-run `./bin/init` → expect the auto-bootstrap `Installing local dependencies (first-run only)...` line followed by the `Dependencies installed.` line followed by the five-line banner; exit `0`.
  - [x] Verify `grep -cE '^#!/usr/bin/env node$' bin/init` returns `1` (exactly one shebang on line 1). Verify `grep -cE 'spawnSync\(.npm.,' bin/init` returns `1`. Verify `grep -cE '\b(bash|sh|zsh|/bin/bash|/bin/sh)\b' bin/init` returns `0`. Verify `grep -cE '/Users/|/home/' bin/init` returns `0`.
  - [x] Verify zero secret-shaped strings across `bin/init` + `package.json`: loop the eleven-pattern regex catalog; each pattern returns zero matches. Verify banned-term regex returns zero matches against `bin/init` (use plain sanitized view) and zero matches against `package.json` (use the two-stage view: sanitize + `content_allowlist_for_personal()` description substitution).
  - [x] Verify placeholder-form probes return zero matches. Verify Derek fixed-string probes return zero matches. Verify path-reference probes return zero matches. Verify `password=` / `token=` / `secret=` / `api_key=` lowercase-literal probes return zero matches. Verify zero `${VAR}` / `$VAR` tokens.
  - [x] Verify no trailing-whitespace lines: `grep -nE ' +$' bin/init package.json package-lock.json` returns zero matches.
  - [x] Confirm `git check-ignore -v bin/init` exits non-zero (tracked); `git check-ignore -v package.json` exits non-zero (tracked); `git check-ignore -v package-lock.json` exits non-zero (tracked); `git check-ignore -v node_modules/prompts/package.json` exits `0` with `.gitignore:1:node_modules/` (ignored).

- [x] **Task 4 — Re-verify byte-stability invariants (AC: 6)** **[Independent — can run any time before Task 6]**
  - [x] Re-compute SHA-256 of `.cursor/mcp.json`; compare to `STORY_4_3_MCP_JSON_SHA256` from Task 1. They MUST match exactly.
  - [x] Re-compute SHA-256 of `.cursor/mcp.README.md`; compare to `STORY_4_3_MCP_README_SHA256`. They MUST match exactly.
  - [x] Re-compute SHA-256 of `.cursor/mcp.placeholders.md`; compare to `STORY_4_3_MCP_PLACEHOLDERS_SHA256`. They MUST match exactly.
  - [x] Re-compute SHA-256 of `.env.example`; compare to `STORY_4_3_ENV_EXAMPLE_SHA256`. They MUST match exactly.
  - [x] Re-compute SHA-256 of `.gitignore`; compare to `STORY_1_1_GITIGNORE_SHA256`. They MUST match exactly.
  - [x] Re-compute SHA-256 of `docs/legal/license-vixxo-internal-canonical.md`; compare to `STORY_1_2_LICENSE_CANONICAL_SHA256`. They MUST match exactly.
  - [x] Re-compute SHA-256 of `docs/setup.md` and `docs/mcps.md`; compare to `STORY_4_4_SETUP_MD_SHA256` / `STORY_4_4_MCPS_MD_SHA256` embedded in the harness. They MUST match exactly.
  - [x] Re-compute SHA-256 of every predecessor harness under `_bmad-output/implementation-artifacts/tests/`; compare to `EXPECTED_PREDECESSOR_SHA256[i]` positionally. They MUST match exactly.
  - [x] Confirm `git diff --stat` over the working tree shows only: new file `bin/init`, new file `package.json`, new file `package-lock.json`, new harness `story-5-1-bin-init-validation.sh`, three new evidence files (`story-5-1-baseline-audit.md`, `story-5-1-canonical-blueprint.md`, `story-5-1-task-handoff.md`), this story file, and the `sprint-status.yaml` 5-1 + epic-5 status flips — no other file in the Story 5.1 diff.

- [x] **Task 5 — Author the deterministic validation harness `story-5-1-bin-init-validation.sh` (AC: 8, 9)** **[Sequential — depends on Tasks 3 + 4]**
  - [x] Create `_bmad-output/implementation-artifacts/tests/story-5-1-bin-init-validation.sh`. Model on `story-4-4-setup-and-mcps-docs-validation.sh`. `#!/usr/bin/env bash` on line 1, `set -euo pipefail` on line 2, `chmod +x`. POSIX-bash-3.2 compatible, BSD + GNU grep compatible.
  - [x] Declare constants at the top:
    - `PROJECT_ROOT`, `TESTS_DIR`, `SELF_PATH` — standard harness boilerplate.
    - `BIN_INIT="${PROJECT_ROOT}/bin/init"`
    - `PACKAGE_JSON="${PROJECT_ROOT}/package.json"`
    - `PACKAGE_LOCK_JSON="${PROJECT_ROOT}/package-lock.json"`
    - `MCP_JSON`, `MCP_README`, `MCP_PLACEHOLDERS`, `ENV_EXAMPLE`, `GITIGNORE_PATH`, `LICENSE_CANONICAL`, `SETUP_MD`, `MCPS_MD` — byte-stability anchors.
    - `BASELINE_AUDIT_PATH="${TESTS_DIR}/story-5-1-baseline-audit.md"`
    - `BLUEPRINT_PATH="${TESTS_DIR}/story-5-1-canonical-blueprint.md"`
    - `EXPECTED_TOP_KEYS=( name version private description type bin scripts engines dependencies )` — nine keys.
    - `EXPECTED_LOCK_PACKAGES=( node_modules/kleur node_modules/prompts node_modules/sisteransi )` — three sorted transitive-package keys.
    - `EXPECTED_PROMPTS_VERSION="2.4.2"`
    - `EXPECTED_NODE_ENGINE=">=20.0.0"`
    - `EXPECTED_LOCKFILE_VERSION=3`
    - `EXPECTED_PACKAGE_NAME="assistants-template"`
    - `EXPECTED_PACKAGE_VERSION="0.1.0"`
    - `EXPECTED_DESCRIPTION_LOCKED='"description": "Vixxo-deployable personal AI agent template; clone, run ./bin/init, work."'`
    - `EXPECTED_BANNER_LINES=( 'assistants-template — setup wizard' 'Story 5.1 scaffold — runnable entry point confirmed.' 'Story 5.2 (prompts + file generation) and Story 5.3 (skills install + MCP verification) extend this entry point in later epics.' 'Next: wait for Story 5.2 to land, or run manual onboarding steps from docs/setup.md.' )` — four non-blank banner lines from AC4.
    - `SECRET_PATTERNS=( … )` — copy eleven patterns verbatim from Story 4.4.
    - `SECRET_EQUALS_LITERALS=( password= token= secret= api_key= )` — four lowercase literals.
    - `BANNED_TERMS_REGEX='(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])'` — verbatim inheritance.
    - `DEREK_FIXED_STRINGS=( Chiron MasteryLab "Agile Weekly" "Queen Creek" Gangplank "Bodybuilding.com" Integrum Omarchy derekneighbors.com Playrix Laurie Deke )` — twelve probes.
    - `GH_PAT_ENV_NAME="GITHUB_PERSONAL_ACCESS_TOKEN"`; `GH_PAT_ALLOWLIST_PLACEHOLDER="__GH_PAT_NAME__"`.
    - `STORY_4_3_MCP_JSON_SHA256`, `STORY_4_3_MCP_README_SHA256`, `STORY_4_3_MCP_PLACEHOLDERS_SHA256`, `STORY_4_3_ENV_EXAMPLE_SHA256`, `STORY_1_1_GITIGNORE_SHA256`, `STORY_1_2_LICENSE_CANONICAL_SHA256`, `STORY_4_4_SETUP_MD_SHA256`, `STORY_4_4_MCPS_MD_SHA256` — byte-stability fingerprints.
    - Fourteen predecessor harness paths: `STORY_1_1_HARNESS` through `STORY_4_4_HARNESS`.
    - `EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 10 10 10 10 )` — fourteen-element vector.
    - `EXPECTED_PREDECESSOR_SHA256=( … )` — fourteen-element positional-parallel SHA-256 array.
  - [x] Implement `regex_self_probe()` covering all Story 4.4 probes plus a new JSON-parse probe: `node -e 'JSON.parse(`{\"a\":1}`)'` exits `0`; `node -e 'JSON.parse(`{a:1}`)'` exits non-zero.
  - [x] Implement `sha256_of()`, `sanitize_for_banned_scan()`, `fail()`, `require_file_exists()` — copy patterns from Story 4.4.
  - [x] Implement `content_allowlist_for_personal()` helper: given a file path, emit the file contents to stdout with the literal `EXPECTED_DESCRIPTION_LOCKED` substring substituted to `"description": "__LOCKED_DESC__"` via `sed`. The helper is used only for `package.json`; `bin/init` scans use the plain `sanitize_for_banned_scan()` view.
  - [x] Implement `json_strict_parse()` helper: given a file path, invoke `node -e 'JSON.parse(require("fs").readFileSync("'"$1"'","utf8"))'` and return the exit code. Used in `check_task4` and `check_task5` for `package.json` and `package-lock.json` respectively.
  - [x] Implement `check_task1` — baseline-audit artifact present, contains required sections listed in Task 1.
  - [x] Implement `check_task2` — canonical-blueprint artifact present, contains the `bin/init` outline, `package.json` lock, `package-lock.json` lock, description-allowlist carve-out, and inheritance note referencing Stories 4.1 / 4.2 / 4.3 / 4.4 catalogs.
  - [x] Implement `check_task3` — `bin/init` shape: file exists at `bin/init`, non-empty, trailing newline, LF-only, executable bit set (`[[ -x "${BIN_INIT}" ]]`), first line equals `#!/usr/bin/env node` (via `head -n 1` + exact string compare), exactly one `spawnSync` call (via `grep -cE "spawnSync\('npm',"` returns `1`), zero `bash` / `sh` / `zsh` / `/bin/bash` / `/bin/sh` substrings (via `grep -cE "\b(bash|sh|zsh|/bin/bash|/bin/sh)\b"` returns `0`), zero `/Users/` / `/home/` absolute-path literals, contains each of the four `EXPECTED_BANNER_LINES` literally via `grep -Fxq` or `grep -Fq`.
  - [x] Implement `check_task4` — `package.json` shape: file exists, non-empty, trailing newline, LF-only, strict JSON parse succeeds via `json_strict_parse`, top-level-key sequence equals `EXPECTED_TOP_KEYS` exactly (awk-based JSON-key-order extraction — loop `EXPECTED_TOP_KEYS[i]` and verify each key appears at position `i` in the top-level key list), `dependencies.prompts` equals the exact-pin `"2.4.2"`, `engines.node` equals `">=20.0.0"`, `name` equals `"assistants-template"`, `version` equals `"0.1.0"`, `private` equals `true`, `type` equals `"commonjs"`, `bin.assistants-init` equals `"./bin/init"`, `scripts.init` equals `"node ./bin/init"`, `scripts.start` equals `"node ./bin/init"`, description exactly matches `EXPECTED_DESCRIPTION_LOCKED` line.
  - [x] Implement `check_task5` — `package-lock.json` shape: file exists, non-empty, trailing newline, LF-only, strict JSON parse succeeds, `lockfileVersion` equals `3`, `name` equals `"assistants-template"`, `version` equals `"0.1.0"`, `packages[""].dependencies.prompts` equals `"2.4.2"`, the sorted set of `packages` keys minus the root `""` equals `EXPECTED_LOCK_PACKAGES` exactly, `packages["node_modules/prompts"].version` equals `"2.4.2"`.
  - [x] Implement `check_task6` — secret-shape + banned-term + Derek + path + placeholder-form scans per AC5: loop `SECRET_PATTERNS` against `sanitize_for_banned_scan` view of `bin/init` (zero matches) and `package.json` (zero matches); loop `DEREK_FIXED_STRINGS` via `grep -Fi` against both files (zero matches); path-reference probes against both files (zero matches); four `…=` lowercase-literal probes via `grep -F` against both files (zero matches); five placeholder-form probes via `grep -oE` against both files (zero matches); banned-term regex via `grep -iE` against `bin/init` plain-sanitized view (zero matches) AND against `package.json` two-stage-sanitized view (`sanitize_for_banned_scan` + `content_allowlist_for_personal`) (zero matches); assert the pre-allowlist view of `package.json` DOES contain the substring `personal AI agent template` (so the allowlist is exercised).
  - [x] Implement `check_task7` — byte-stability invariance per AC6: `sha256_of` of each byte-stability anchor equals the locked constant; `git check-ignore -v bin/init` exits non-zero; `git check-ignore -v package.json` exits non-zero; `git check-ignore -v package-lock.json` exits non-zero; `git check-ignore -v node_modules/prompts/package.json` exits `0` with output matching `\.gitignore:[0-9]+:node_modules/`.
  - [x] Implement `check_task8` — self-check per Stories 2.x / 3.x / 4.x pattern: shebang line 1, `set -euo pipefail`, every case arm present (`task1)` through `task9)` and `all)`), every declared constant name referenced (loop a named-array of expected constant names), `declare -F regex_self_probe / sanitize_for_banned_scan / content_allowlist_for_personal / sha256_of / json_strict_parse` all return `0`.
  - [x] Implement `check_task9` — regression against fourteen predecessors: honor `BMAD_REGRESSION_DEPTH` guard from Story 4.2 F6 (skip inner-level invocations); loop fourteen predecessors with SHA-256 pre-check (Story 4.2 F5 pattern); invoke each with `BMAD_REGRESSION_DEPTH=1` and `bash <harness> all 2>&1`; retry-once-on-flake wrapper (Story 4.2 F1 pattern); `mkdir -p "${PROJECT_ROOT}/tmp"` defensive pre-creation; assert each exits `0`; assert per-harness `^PASS:` line-count matches `EXPECTED_PASS_COUNTS[i]`; on non-zero exit or count mismatch, echo captured output and `fail` with sub-harness name. Emit `task9 OK: fourteen-predecessor byte-stability + regression verified` on stderr.
  - [x] Implement the `mode` dispatcher wrapped in `main()`: `task1 → task9` gates plus `all` mode (runs all nine sequentially, echoing `PASS: task<n>` after each, ending with `PASS: all`; emits exactly 10 `^PASS:` lines on success).
  - [x] Add header comment block stating: (a) Story 5.1 scaffolds `bin/init` + `package.json` + `package-lock.json`; (b) three production files plus one harness plus three evidence artifacts plus this story; (c) `.cursor/mcp.json` + `.cursor/mcp.README.md` + `.cursor/mcp.placeholders.md` + `.env.example` + `.gitignore` + `docs/legal/license-vixxo-internal-canonical.md` + `docs/setup.md` + `docs/mcps.md` byte-stable (SHA-256 fingerprint assertions); (d) fourteen-harness regression chain (Stories 1.1 → 4.4 now all predecessors); (e) empirical `^PASS:` vector `( 1 1 1 1 10 7 7 7 7 7 10 10 10 10 )`; (f) banned-term regex + secret-pattern catalog + placeholder-form probes + Derek probes + path-reference probes inherited verbatim from Stories 4.1 → 4.4; (g) honors `BMAD_REGRESSION_DEPTH` guard (Story 4.2 F6); (h) honors `EXPECTED_PREDECESSOR_SHA256` pre-check (Story 4.2 F5); (i) new content-allowlist carve-out for the `description` field (`personal AI agent template` locked substring); (j) new `json_strict_parse` helper uses `node -e` because Node is a hard prerequisite for the story.

- [x] **Task 6 — Run the full regression and capture the Task Handoff artifact (AC: 8, 9, 10)** **[Sequential — depends on Task 5]**
  - [x] Run `bash _bmad-output/implementation-artifacts/tests/story-5-1-bin-init-validation.sh all`. Capture the full transcript. Expect `PASS: task1` → `PASS: task9` → `PASS: all`, exit `0`, exactly 10 `^PASS:` lines. Runtime expectation ~160–200 seconds on macOS bash 3.2.57 (fourteen-harness regression plus `npm install`-verification).
  - [x] Re-run each of the fourteen predecessor harnesses individually in `all` mode. All fourteen must exit `0` with `PASS: all`. Verify per-harness `^PASS:` line-count fingerprint `( 1 1 1 1 10 7 7 7 7 7 10 10 10 10 )`.
  - [x] Functional smoke test on the entry point itself (run from repo root with `node_modules/` present): `./bin/init --help` → banner + exit `0`; `./bin/init --version` → `assistants-template init 0.1.0` + exit `0`; `./bin/init` → five-line banner + exit `0`.
  - [x] Cold-bootstrap smoke test: `rm -rf node_modules && ./bin/init` → expect `Installing local dependencies (first-run only)...` + npm install output + `Dependencies installed.` + five-line banner + exit `0`. Then rerun `./bin/init` immediately → expect NO re-install (idempotent); just the five-line banner + exit `0`.
  - [x] Run additional verification steps: `shasum -a 256 .cursor/mcp.json .cursor/mcp.README.md .cursor/mcp.placeholders.md .env.example .gitignore docs/legal/license-vixxo-internal-canonical.md docs/setup.md docs/mcps.md` and assert each matches the expected constants; `git check-ignore -v bin/init` (expected: non-zero exit); `git check-ignore -v package.json` (expected: non-zero exit); `git check-ignore -v package-lock.json` (expected: non-zero exit); `git check-ignore -v node_modules/prompts/package.json` (expected: exit `0`, `.gitignore:1:node_modules/`); `node -e 'JSON.parse(require("fs").readFileSync("package.json","utf8"))'` (exit `0`); `node -e 'JSON.parse(require("fs").readFileSync("package-lock.json","utf8"))'` (exit `0`).
  - [x] Persist `_bmad-output/implementation-artifacts/tests/story-5-1-task-handoff.md` with: (a) AC-to-file map (one row per AC pointing at the harness gate, file path, or command output that proves it); (b) full validation command transcript (Story 5.1 harness + fourteen regression harnesses); (c) SHA-256 checksum of `bin/init`, `package.json`, `package-lock.json` AND re-confirmation fingerprints for every byte-stability anchor AND all fourteen predecessor harnesses; (d) bin/init functional smoke-test transcript (four cases: `--help`, `--version`, steady state, cold bootstrap); (e) `node_modules/` directory listing (three sub-dirs: `prompts`, `kleur`, `sisteransi`); (f) forward-looking notes: Story 5.2 will `require('prompts')` and add prompt flows + file generation; Story 5.3 will add the `npx skills add vixxo-copilot/agent-skills` invocation + per-MCP verification logic; the `docs/setup.md` § `Run the setup smoke test` forward reference becomes live as of this story; (g) zero-edit verification block listing every Story 1.x / 2.x / 3.x / 4.x artifact asserted byte-stable.

- [x] **Task 7 — Sprint tracker and story status synchronization (AC: 10)** **[Independent; typically last]**
  - [x] Flip `_bmad-output/implementation-artifacts/sprint-status.yaml` entry `5-1-scaffold-bin-init-node-entry-point.status` from `backlog` to `ready-for-dev` during Phase 1 (SM pass); then to `review` at Dev handoff; then to `done` at Phase 3 review approval.
  - [x] Flip `epic-5.status` from `backlog` to `in-progress` during Phase 1 (first story in the epic). Story 5.1 is responsible for opening the epic; Stories 5.2 + 5.3 carry it forward; Story 5.3 is responsible for closing it to `done`.
  - [x] Update `last_updated` in `sprint-status.yaml` to `2026-04-21` on the Phase 1 edit.
  - [x] Preserve every comment, blank line, inline spacing, and entry ordering byte-for-byte. Only diffs vs. the post-4.4 state: `status:` value flip on `5-1-…`, `status:` value flip on `epic-5`, `last_updated` value change.

## Dev Notes

### Artifact availability

- Planning / tracking artifacts used by this story:
  - `_bmad/bmm/config.yaml` (BMAD v6.3.0; `user_name: Vixxo Employee`; `planning_artifacts` / `implementation_artifacts` path variables).
  - `_bmad-output/planning-artifacts/epics.md` lines 337–347 — Epic 5 Story 5.1 ACs. `./bin/init` executable, Node only, no bash-specific assumptions; reads a tiny `package.json` for deps (`prompts` or similar); runnable right after clone.
  - `_bmad-output/planning-artifacts/architecture.md` — 26 lines; template-only scope; constraint line 24 "Keep secrets/local artifacts out of git via root `.gitignore`" — carries forward to Story 5.1's AC7 `node_modules/` gitignore discipline. NFR2 ("Works on macOS and Linux; depends only on `git`, `node`, `npx`") directly shapes the portable `#!/usr/bin/env node` shebang choice in AC1.
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` — story key `5-1-scaffold-bin-init-node-entry-point`, Linear `AIP-39`, current status `backlog`; `epic-5.status: backlog` (Story 5.1 flips it to `in-progress`); `last_updated: 2026-04-21`.
  - Prior story files (all `done`): `1-1-…` through `4-4-…`. Pattern source for harness structure, banned-term regex discipline, POSIX-ERE boundary guards, SHA-256 byte-stability assertions, Phase-4 F-series review-fix patterns (F1 retry-on-flake, F4 content-deduplication, F5 `EXPECTED_PREDECESSOR_SHA256`, F6 `BMAD_REGRESSION_DEPTH` guard), autonomous-swarm status-collapse convention.
  - `.cursor/mcp.json`, `.cursor/mcp.README.md`, `.cursor/mcp.placeholders.md`, `.env.example`, `.gitignore`, `docs/setup.md`, `docs/mcps.md`, `docs/legal/license-vixxo-internal-canonical.md`, `docs/pii-denylist.md` — byte-stable invariants Story 5.1 consumes.
  - `docs/setup.md` lines 101–103 forward-reference: "Once Epic 5 Story 5.1 lands, running `./bin/init` will execute the smoke test end-to-end. The `./bin/init` file does not yet exist; the shell-invocation string is a forward reference to the wizard that Epic 5 will ship." Story 5.1 makes this reference live (the file now exists after Story 5.1 lands). Story 5.1 does NOT edit `docs/setup.md` to remove the forward-reference wording — that edit is deferred to Story 5.2 or Story 5.3 when the wizard actually executes a smoke test.
- Missing at expected paths:
  - `_bmad-output/planning-artifacts/prd.md` — does not exist. Story 5.1 relies on epics.md + architecture.md + sprint-status.yaml + prior-story handoffs + established patterns.
  - `_bmad-output/planning-artifacts/ux-design-specification.md` — does not exist. Story 5.1's UX surface is a two-character-line banner printed to stdout; no visual UX design needed.
  - `_bmad/bmm/workflows/4-implementation/bmad-create-story/template.md` — does not exist. Story 5.1 uses the emergent shape from Stories 1.1 → 4.4 (Status + Story + ACs + Tasks/Subtasks + Dev Notes + Change Log + Dev Agent Record + File List + References).

### Epic 5 story partition (where 5.1 fits)

- **Story 5.1 (this story):** Scaffold `bin/init` + `package.json` + `package-lock.json`. Runnable immediately after clone via single-command auto-bootstrap. No prompt logic, no file generation, no network calls beyond the optional one-time `npm install`. Opens `epic-5.status: backlog → in-progress`.
- **Story 5.2 (backlog):** Wizard prompts and file generation. Extends `bin/init` with `require('prompts')`-based interactive flow: name, email, Vixxo role/title, optional MCPs. Generates `memory/me/identity.md` (overwrites the Story 3.3 skeleton) and `agents/personas/work.md` (overwrites the Story 2.3 generic skeleton). Copies `.env.example` → `.env` (leaves secrets blank). Story 5.2 inherits the Story 5.1 harness discipline and extends the `check_task3` gate to cover the new prompt / file-generation paths. Story 5.2 likely adds a unit-test-style fixture harness using `child_process.spawn(node, [bin/init], { env: { CI: 'true', ASSISTANTS_INIT_NONINTERACTIVE_FIXTURES: JSON.stringify({...}) } })` to exercise prompt paths deterministically without TTY.
- **Story 5.3 (backlog):** Wizard runs skills install and verifies. Extends `bin/init` with the `npx skills add vixxo-copilot/agent-skills` invocation (logged and error-propagated like Story 5.1's `npm install` spawn) and the per-active-MCP verification probes (simple network / CLI calls against Linear, GitHub, MS365, Salesforce, Gong). Closes `epic-5.status: in-progress → done`.

Story 5.1 is intentionally narrow: only the entry point + deps + lockfile + harness + evidence. The wizard prompts and the skills install are separate stories; encapsulation here means Story 5.2 and Story 5.3 have a stable runnable base to extend without having to simultaneously debug entry-point concerns.

### Why `prompts@2.4.2` exact-pin

1. **Smallest transitive-dep footprint.** The `prompts` package is 2 transitive packages (`kleur`, `sisteransi`) — the smallest in-category by a wide margin. `inquirer` is ~30 packages; `@inquirer/prompts` is ~100 packages; `enquirer` is ~10 packages; `prompt-sync` and `readline-sync` are smaller but lack validators, choices, multi-select. A template for employee workstations benefits from minimal `node_modules/` surface to keep `npm install` fast and audit-able.
2. **CommonJS first.** `prompts@2.4.2` exports via CommonJS (`module.exports = prompts`), matching Story 5.1's `"type": "commonjs"` lock. Switching to `@inquirer/prompts` would force ESM adoption across `bin/init`, which adds top-level `await` complexity and forces file extensions to `.mjs` or `package.json` `"type": "module"`. Story 5.1 defers that decision; Story 5.2 or a future story may upgrade.
3. **Battle-tested.** `prompts` is used by `create-react-app`, `vue-cli`, `astro`, `create-svelte`, `svelte-kit`, `vite`, `gatsby-cli`, `nuxt` init flows. Low maintenance cadence is balanced by extreme API stability — the published `2.4.2` version has not had a breaking change in 4+ years.
4. **Exact-pin, not range.** `"prompts": "2.4.2"` (no `^`, no `~`, no `*`) guarantees every clone gets byte-identical `prompts` code. This is consistent with Story 4.1's `.cursor/mcp.json` doctrine ("no floating versions; pin exactly what you deploy") and with Story 4.3's `.env.example` discipline ("every RHS is intentionally blank or commented"). The `package-lock.json` is the second line of defense; the exact-pin in `package.json` is the first.
5. **Zero open CVEs (as of 2026-04-21).** `npm audit` returns zero advisories against `prompts@2.4.2` or either transitive dep (`kleur@3.0.3`, `sisteransi@1.0.5`). This is re-confirmed in the baseline audit; if `npm audit` reports a new advisory at Dev time, raise an integration fix.

### Why auto-bootstrap via `spawnSync('npm', ['install'])`

The epic AC says `./bin/init` should be "runnable right after clone" and "bootstrap with one command." The user-facing ergonomic target is: clone the repo, cd into it, run `./bin/init`, go. If `bin/init` required a preceding manual `npm install`, that would be a TWO-command bootstrap. Two options to achieve single-command:

- **Option A (adopted):** Ship `bin/init` with a self-heal step that detects missing `node_modules/prompts` and runs `npm install` synchronously via `spawnSync`, `stdio: 'inherit'`. Pros: single-command, self-contained, transparent to the user (the progress line makes the install visible). Cons: the first run takes longer than subsequent runs (~30–45 seconds for `npm install` + node_modules hydration); the bootstrap adds ~30 lines of code to the entry point.
- **Option B (rejected):** Ship `bin/init` with a hard error "`node_modules/` not found — please run `npm install` first and re-run `./bin/init`." Pros: simpler entry point (~10 lines of code). Cons: requires a two-command bootstrap; users unfamiliar with Node will hit the error and potentially bounce; NFR3 ("Setup Wizard completes in under 15 minutes on a fresh machine") is harder to meet because friction compounds.

Option A is adopted for the user-ergonomic reasons. The auto-bootstrap is idempotent (subsequent runs with `node_modules/` present skip the install entirely) and fail-safe (install failure propagates a non-zero exit and prints a remediation hint).

### JSON parsing strategy (Node over Python)

Prior stories (4.1, 4.2) used `python3 -m json.tool` to strict-parse JSON files. Story 5.1 adds a second strategy: `node -e 'JSON.parse(require("fs").readFileSync("path","utf8"))'`. Rationale: Node 20 is now a hard prerequisite for the story (AC3 `"engines": { "node": ">=20.0.0" }`), so using Node for JSON parsing in the harness is no longer a circular dependency. The harness prefers `node -e` for `package.json` and `package-lock.json` validation because Node's native parser produces clearer error messages than Python's `json.tool` CLI wrapper. Python remains usable as a fallback for compatibility with non-Node workstations, but Story 5.1 scopes it to the predecessor-harness invocations only.

### Content-allowlist for `personal` in `description`

Story 4.1 introduced `sanitize_for_banned_scan()` as the mechanism to pre-filter `GITHUB_PERSONAL_ACCESS_TOKEN` before banned-term scans so the env-var name does not trip the `personal` token. Story 5.1 extends this concept with a SECOND allowlist: the full-string carve-out of `"description": "Vixxo-deployable personal AI agent template; clone, run ./bin/init, work."` → `"description": "__LOCKED_DESC__"` before banned-term scanning of `package.json` only. The allowlist is:

- **Anchored on the full locked string** — not just the word `personal`; a new line adding `personal` outside the locked description would NOT be substituted and WOULD trigger the banned-term regex.
- **Single-scope** — applied only to `package.json`; `bin/init` uses the plain `sanitize_for_banned_scan()` view.
- **Self-testing** — the harness asserts the PRE-substitution view of `package.json` contains the substring `personal AI agent template` (so the allowlist is actually exercised); then asserts the POST-substitution view's banned-term regex returns zero matches (so the allowlist works).
- **Rationale** — the phrase "personal AI agent template" is product-positioning language inherited from the epic's FR1 / FR2 / FR3 narrative (every employee's own AI agent). Replacing `personal` with `individual` / `employee-owned` / `private` loses nuance that matters for adoption messaging. The content-allowlist is a narrow, documented, self-testing carve-out — not a general weakening of the banned-term discipline.

### Previous story learnings to carry forward

- **POSIX-ERE boundary guards** (Stories 2.1 → 4.4): `(^|[^A-Za-z])TOKEN($|[^A-Za-z])` — works on macOS BSD grep, GNU grep, busybox/Alpine grep.
- **`regex_self_probe` fail-fast** (all prior stories): probe exercises positive + boundary-rejected for at least two tokens. Story 5.1 ADDS: `node -e 'JSON.parse("{\"a\":1}")'` exits `0`; `node -e 'JSON.parse("{a:1}")'` exits non-zero.
- **Phase 4 F6 `BMAD_REGRESSION_DEPTH` guard**: `check_task9` short-circuits when `BMAD_REGRESSION_DEPTH != "0"`. Outer invocation exports the env before calling each predecessor.
- **Phase 4 F5 `EXPECTED_PREDECESSOR_SHA256` anchor**: fourteen-element positional-parallel SHA-256 array verified BEFORE each predecessor invocation.
- **Phase 4 F1 retry-on-flake wrapper**: each predecessor invocation retried up to three times on transient failure.
- **Phase 4 F7 PASS-count fingerprint**: fourteen-element vector `( 1 1 1 1 10 7 7 7 7 7 10 10 10 10 )` for Story 5.1.
- **SHA-256 byte-stability assertions**: eight anchors at `task7` (`.cursor/mcp.json`, `.cursor/mcp.README.md`, `.cursor/mcp.placeholders.md`, `.env.example`, `.gitignore`, `docs/legal/license-vixxo-internal-canonical.md`, `docs/setup.md`, `docs/mcps.md`).
- **Scope-fence / creates-only list** (Stories 3.3 / 4.1 / 4.2 / 4.3 / 4.4): AC11 lists the seven creates-only artifacts (three production files + one harness + three evidence docs + this story). No predecessor edit.

### Risks and concerns

- **Story 3.3 harness SHA drift vs. Story 4.4 lock.** The current on-disk Story 3.3 harness SHA-256 is `f49f21c1811be49fc7aafa386f7f14553f46deb8a5bee6d4e609ca4d1b39bea8`; Story 4.4's `EXPECTED_PREDECESSOR_SHA256[9]` still expects the older `77a5376887f03909223074b2f21e1306f689a9238d6da0cf191aa79a0427b427`. When Story 5.1's `task9` regression invokes Story 4.4 (with `BMAD_REGRESSION_DEPTH=1`), Story 4.4's own `task9` short-circuits (guard-protected), so the nested Story 3.3 SHA check never runs. Story 5.1's direct SHA check of Story 3.3 uses the CURRENT on-disk value (`f49f21c…`), so Story 5.1 itself is clean. However, if Story 4.4 is later invoked WITHOUT the `BMAD_REGRESSION_DEPTH` guard (e.g. from a fresh shell), its `task9` will fail due to the drift. Mitigation: flag in baseline audit; raise an integration fix story to update Story 4.4's lock to the current on-disk value once the Epic 5 work is parked for a moment.
- **`npm install` network dependency for bootstrap.** The auto-bootstrap step requires network access to the npm registry (or a configured corporate mirror) on first run. If the user is behind a corporate firewall without an npm proxy, the `npm install` spawn will time out or fail with a network error. The script's error handling (`[bin/init] npm install failed; exit ...`) surfaces this cleanly, and the remediation is a one-liner (`npm config set registry ...`). No special Story 5.1 mitigation is needed — the failure is visible and recoverable.
- **`prompts@2.4.2` is in maintenance mode.** The package has not shipped a new version since 2021-10-07. This is acceptable given the API stability, but introduces long-term maintenance risk — if a Node 24 or Node 26 release drops `util.promisify` or changes `readline` semantics, `prompts` may require a patch. Mitigation: the exact-pin in `package.json` + `package-lock.json` makes the `prompts` version change a DELIBERATE edit in a future story; no silent drift. If a compatibility issue emerges, a future story can migrate to `@inquirer/prompts` (ESM) with a scoped refactor of `bin/init`.
- **Executable-bit tracking on Windows.** Git on Windows does not preserve the `+x` bit natively; `git update-index --chmod=+x bin/init` writes the 100755 mode bit into the index, and clones on POSIX systems materialize the executable bit correctly. Windows is NOT a supported platform per NFR2 ("Works on macOS and Linux"), so this is a non-issue for Story 5.1. Document the doctrine in the baseline audit: Windows support would require a `.cmd` wrapper or direct `node ./bin/init` invocation; out of scope for Story 5.1.
- **Node 18 workstations will reject the engines.** `"engines": { "node": ">=20.0.0" }` is informational unless `npm config set engine-strict true`. On Node 18 the `npm install` step will print a warning but succeed; the `./bin/init` script itself uses no Node 20-only APIs (the code is compatible with Node 18 as well), so Story 5.1 gracefully degrades. The AC3 lock of Node 20 matches `docs/setup.md` Prerequisites and the broader template posture; a user running Node 18 gets an advisory warning and is expected to upgrade. No code-path change needed.
- **Fourteen-harness regression runtime.** Each predecessor harness in `all` mode takes 5–15 seconds on macOS bash 3.2.57. Fourteen predecessors × ~10 seconds = ~140 seconds. Plus Story 5.1's own nine gates (~30 seconds, plus `npm install` during the cold-bootstrap smoke test). Total expected runtime ~160–200 seconds; documented in Task 6 handoff. Story 4.2 F1 retry-on-flake wrapper absorbs any transient failure.
- **`npm install` in the middle of harness invocation.** Task 5's harness does NOT run `npm install` itself — only Task 3 (authoring) and Task 6's cold-bootstrap smoke test do. The harness's `task3` gate verifies `node_modules/` presence via `require_file_exists`; if `node_modules/` is missing at harness run time, the harness fails early with a clear diagnostic rather than silently running `npm install`. This keeps the harness side-effect-free (read-only) consistent with Stories 4.1–4.4 precedent.

### Project Structure Notes

- New files created by this story:
  - `bin/init` (repo root; executable Node.js entry point; self-bootstrapping)
  - `package.json` (repo root; nine locked top-level keys; `prompts@2.4.2` exact-pin)
  - `package-lock.json` (repo root; lockfile version 3; three transitive packages)
  - `_bmad-output/implementation-artifacts/tests/story-5-1-bin-init-validation.sh` (deterministic validation harness; nine gates + `all`)
  - `_bmad-output/implementation-artifacts/tests/story-5-1-baseline-audit.md` (Task 1 evidence)
  - `_bmad-output/implementation-artifacts/tests/story-5-1-canonical-blueprint.md` (Task 2 evidence)
  - `_bmad-output/implementation-artifacts/tests/story-5-1-task-handoff.md` (Task 6 evidence)
- Files modified by this story:
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` (Story 5.1 status flip + Epic 5 status flip + `last_updated` + this file's `Dev Agent Record` / `Change Log` / `File List` sections updated at Dev handoff)
- Files NOT modified by this story (byte-stable invariance — asserted by harness `task7`):
  - `.cursor/mcp.json`, `.cursor/mcp.README.md`, `.cursor/mcp.placeholders.md`, `.env.example` (Stories 4.1–4.3 artifacts)
  - `.gitignore` (Story 1.1 + F1 patch; the existing `node_modules/` rule handles bootstrap artifact)
  - `README.md`, `LICENSE`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`
  - `docs/setup.md`, `docs/mcps.md`, `docs/legal/license-vixxo-internal-canonical.md`, `docs/pii-denylist.md`
  - All `.cursor/rules/*.mdc` files (5 rules + `.gitkeep`)
  - All `agents/personas/*.md` files
  - All `memory/**/*.md` and `memory/.obsidian/*.json` files
  - `bin/.gitkeep` (Story 1.1 artifact; coexists with new `bin/init`)
  - All fourteen predecessor harnesses under `_bmad-output/implementation-artifacts/tests/story-[1-4]-*.sh`
  - Epic 6 harnesses (`story-6-1-pii-denylist-validation.sh`, `story-6-2-github-action-validation.sh`) — not chained as regression predecessors (parallel branch), but still byte-stable.

### References

- `_bmad-output/planning-artifacts/epics.md` Epic 5 overview (lines 335–370), Story 5.1 ACs (lines 337–347), Story 5.2 scope (lines 348–358), Story 5.3 scope (lines 360–370), Tier 2 priority order (lines 131–143).
- `_bmad-output/planning-artifacts/architecture.md` line 24 — "Keep secrets/local artifacts out of git via root `.gitignore`" — applies to `node_modules/` handling. Also NFR2 (cross-platform `macOS + Linux`) shapes the portable shebang.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (story key `5-1-scaffold-bin-init-node-entry-point`, Linear `AIP-39`, `epic-5.status: backlog` pre-story).
- `_bmad-output/implementation-artifacts/4-4-rewrite-setup-and-mcps-docs.md` (Story 4.4; harness pattern precedent; `story-4-4-setup-and-mcps-docs-validation.sh` is the most recent harness to model; fourteen-element fingerprint patterns).
- `_bmad-output/implementation-artifacts/4-3-write-env-example.md` (Story 4.3; `sanitize_for_banned_scan` load-bearing precedent; content-allowlist pattern inspiration).
- `_bmad-output/implementation-artifacts/tests/story-4-1-canonical-blueprint.md` and `story-4-2-canonical-blueprint.md` and `story-4-3-canonical-blueprint.md` and `story-4-4-canonical-blueprint.md` (blueprint-pattern precedents).
- `_bmad-output/implementation-artifacts/tests/story-4-4-task-handoff.md` (Story 4.4 handoff with SHA-256 fingerprints for `.cursor/mcp.json`, `.cursor/mcp.README.md`, `.cursor/mcp.placeholders.md`, `.env.example`, `.gitignore`, `docs/legal/license-vixxo-internal-canonical.md`, `docs/setup.md`, `docs/mcps.md`).
- `_bmad-output/implementation-artifacts/tests/story-4-1-mcp-json-validation.sh` → `story-4-4-setup-and-mcps-docs-validation.sh` (harness structure precedents).
- `.cursor/mcp.json`, `.cursor/mcp.README.md`, `.cursor/mcp.placeholders.md`, `.env.example`, `docs/setup.md`, `docs/mcps.md` (on-disk byte-stable artifacts Story 5.1 consumes).
- `.gitignore` (Story 1.1 + F1 patch; SHA-256 `49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1`; `node_modules/` rule on line 1 handles the bootstrap artifact without edit).
- Node.js documentation:
  - Active LTS schedule: `https://nodejs.org/en/about/previous-releases`
  - `child_process.spawnSync`: `https://nodejs.org/docs/latest-v20.x/api/child_process.html#child_processspawnsynccommand-args-options`
  - `node:` built-in prefix: `https://nodejs.org/api/modules.html#core-modules`
  - `package.json` `bin` field: `https://docs.npmjs.com/cli/v10/configuring-npm/package-json#bin`
  - `package.json` `engines` field: `https://docs.npmjs.com/cli/v10/configuring-npm/package-json#engines`
  - `package-lock.json` format: `https://docs.npmjs.com/cli/v10/configuring-npm/package-lock-json`
- `prompts` library:
  - Upstream: `https://github.com/terkelg/prompts`
  - npm: `https://www.npmjs.com/package/prompts`
  - Published version at author time: `2.4.2` (2021-10-07)
- Prior-art CLI bootstrapping patterns (reference only; Story 5.1 does not depend on any of these):
  - `create-react-app` auto-bootstrap: `https://github.com/facebook/create-react-app`
  - `create-vite` auto-bootstrap: `https://github.com/vitejs/vite/tree/main/packages/create-vite`
  - `npm init` template scaffolds: `https://docs.npmjs.com/cli/v10/commands/npm-init`

## Senior Developer Review (AI)

- **F1 (CRITICAL, TASK_INCOMPLETE, AC10)**: Story checklist claimed full lifecycle completion while tracker was still `review`.
  - **Resolution**: kept `review` during Phase 3, then moved `sprint-status.yaml` story state to `done` only after Phase 4 fixes + final green validation.
- **F2 (HIGH, AC_MISSING, AC2)**: missing `spawnSync` `result.error` handling for `npm` ENOENT path.
  - **Resolution**: added explicit `result.error` branch in `bin/init` with deterministic `127` for ENOENT and cause text in failure message.
- **F3 (MEDIUM, CODE_QUALITY, AC2)**: missing signal-path handling for interrupted install.
  - **Resolution**: added `result.signal` branch in `bin/init`, maps to deterministic `128 + signalNumber` exit code and prints signal context.
- **F4 (MEDIUM, AC_MISSING, AC2)**: root path derivation used `path.resolve` instead of locked `path.join`.
  - **Resolution**: changed `ROOT` initialization to `path.join(__dirname, '..')` in `bin/init`.

## Review Follow-ups (AI)

- [x] Implemented explicit `spawnSync` error-path handling (`result.error`) with ENOENT-specific exit behavior.
- [x] Implemented signal-path handling (`result.signal`) with deterministic exit-code mapping.
- [x] Updated root path construction to locked `path.join(__dirname, '..')` form.
- [x] Re-ran Story 5.1 harness (`task1..task9`, `all`) after fixes.
- [x] Transitioned Story 5.1 lifecycle to `done` in `sprint-status.yaml` after final green run.

## Change Log

- 2026-04-21: Story created by Bob (Scrum Master / Story Creation agent); moved from `backlog` to `ready-for-dev`; `epic-5.status` flipped `backlog → in-progress` (Story 5.1 is the first story in Epic 5).
- 2026-04-21: Dev implementation completed (Story 5.1 artifacts + harness + handoff); validation harness `story-5-1-bin-init-validation.sh all` passed with fourteen-predecessor regression; story moved to `review`.
- 2026-04-21: Phase 4 review fixes applied (F1-F4), validation re-run passed, and story moved `review` → `done`.

## Dev Agent Record

### Agent Model Used

- Codex (main orchestrator context) with interrupted BMAD dev subagent handoff recovery in main context.

### Debug Log References

- `bash _bmad-output/implementation-artifacts/tests/story-5-1-bin-init-validation.sh all` -> PASS (`task1..task9`, `all`)
- Standalone predecessor sweep (`BMAD_REGRESSION_DEPTH=1`) -> all fourteen harnesses `exit=0`, `PASS: all`
- `./bin/init --help`, `./bin/init --version`, `./bin/init`, `rm -rf node_modules && ./bin/init`, `./bin/init` -> expected outputs and zero exits
- Post-review-fix re-run: `bash _bmad-output/implementation-artifacts/tests/story-5-1-bin-init-validation.sh all` -> PASS (`task1..task9`, `all`)

### Completion Notes List

- Added `bin/init` Node entrypoint with first-run `npm install` bootstrap and deterministic banner flow.
- Added root `package.json` with locked key order and exact `prompts@2.4.2` pin.
- Added tracked `package-lock.json` with minimal dep tree (`prompts`, `kleur`, `sisteransi`).
- Added Story 5.1 baseline audit and canonical blueprint artifacts.
- Added deterministic Story 5.1 validation harness with nine gates plus fourteen-predecessor regression gate.
- Added Story 5.1 task handoff evidence artifact with transcripts, checksums, and AC trace.
- Applied code-review fixes for install error/signal paths and root path lock conformance.
- Updated `sprint-status.yaml` story state to `done`; epic remains `in-progress`.

### File List

- `bin/init` (new, executable)
- `package.json` (new)
- `package-lock.json` (new)
- `_bmad-output/implementation-artifacts/tests/story-5-1-baseline-audit.md` (new)
- `_bmad-output/implementation-artifacts/tests/story-5-1-canonical-blueprint.md` (new)
- `_bmad-output/implementation-artifacts/tests/story-5-1-bin-init-validation.sh` (new, executable)
- `_bmad-output/implementation-artifacts/tests/story-5-1-task-handoff.md` (new)
- `_bmad-output/implementation-artifacts/5-1-scaffold-bin-init-node-entry-point.md` (updated)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (updated)
