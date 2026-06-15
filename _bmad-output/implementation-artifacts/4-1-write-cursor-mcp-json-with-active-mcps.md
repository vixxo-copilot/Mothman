# Story 4.1: Write `.cursor/mcp.json` with Active MCPs

Status: done

## Story

As a new Vixxo employee who has just cloned the `assistants-template` repository and is about to run the Epic 5 setup wizard (`bin/init`),
I want a project-local `.cursor/mcp.json` that wires the five active Vixxo work MCPs — **Linear**, **GitHub**, **Microsoft 365**, **Salesforce**, **Gong** — with credentials referenced only via environment variables (never hardcoded),
so that (a) Cursor and Cursor CLI auto-discover the correct active MCP lineup on first open, (b) the identity rule (`.cursor/rules/agent-identity.mdc`) and work persona (`agents/personas/work.md`) "Available MCPs" lists resolve to a working configuration, (c) Story 4.2 has a stable JSON file it can extend with commented-out placeholders (via a companion placeholder doc, since strict JSON forbids inline comments), (d) Story 4.3 `.env.example` has a deterministic credential surface to document, and (e) no secret ever enters version control.

## Acceptance Criteria

1. **AC1 — `.cursor/mcp.json` exists at the repo root as strict, well-formed JSON**
   - Given the cloned `assistants-template` repository after Story 4.1 lands
   - When `.cursor/mcp.json` is inspected
   - Then the file exists at path `.cursor/mcp.json` (not at `~/.cursor/mcp.json`, not at repo-root `mcp.json`, not at `mcp.config.json`) — project-local location per Cursor docs
   - And the file is valid strict JSON: `python3 -m json.tool .cursor/mcp.json` exits `0`, and `node -e "JSON.parse(require('fs').readFileSync(process.argv[1],'utf8'))" .cursor/mcp.json` exits `0` — both parsers used because strict-JSON parsers differ subtly on edge cases and a PR that breaks one will break the other
   - And the file is non-empty, UTF-8 encoded, ends with a trailing newline (last byte `0x0a`), uses LF line endings (no CRLF — `grep -c $'\r' .cursor/mcp.json` returns `0`)
   - And the file contains NO JavaScript-style `// …` line comments or `/* … */` block comments and NO trailing commas (both are JSON5/JSONC extensions; Cursor's 2026 parser rejects them silently per Cursor forum guidance) — `grep -nE '^\s*//|/\*|,\s*[}\]]' .cursor/mcp.json` returns zero matches
   - And the file root is a single JSON object whose only top-level key is `mcpServers` (string) whose value is a JSON object (the "servers dict" shape)

2. **AC2 — `mcpServers` contains entries for exactly the five active Vixxo MCPs, in canonical order**
   - Given the `mcpServers` object in `.cursor/mcp.json`
   - When the object keys are listed
   - Then the key set equals exactly `{"linear", "github", "microsoft-365", "salesforce", "gong"}` — five keys, all lowercase, hyphen-separated where multi-word — and the keys appear in that canonical order in the file (stable ordering matches how Cursor's settings UI renders them and lets Story 4.2 insert placeholder keys alphabetically without re-sorting actives)
   - And the key count is exactly `5` (`jq '.mcpServers | keys | length' .cursor/mcp.json` returns `5`; for the strict-JSON-only project constraint we use `python3 -c "import json,sys; print(len(json.load(open('.cursor/mcp.json'))['mcpServers']))"` returning `5`)
   - And each of the five keys maps to a JSON object (not `null`, not a string, not an array)
   - And NO other keys exist under `mcpServers` (no `freshdesk`, `dynamics`, `vixxonow`, `vixxolink`, `gateway`, `zoominfo`, `hubspot`, `aws-connect`, `chatfpt`, `elastic`, `introspection`, `agent-skills`, `slack`, `notion`, `gmail`, `google-calendar`, `obsidian`, `linkedin`) — Story 4.2 placeholders are its own responsibility and must not leak here; absence enforced by an explicit deny-list scan in the harness

3. **AC3 — Each active MCP entry has a Cursor-schema-valid shape: either `command+args` (stdio local) or `url` (remote HTTP/SSE)**
   - Given each of the five entries under `mcpServers`
   - When the entry is inspected
   - Then the entry contains EITHER the stdio-local shape (`command: string`, `args: array-of-string`, optional `env: object-of-string-to-string`) OR the remote shape (`url: string`, optional `headers: object-of-string-to-string`) — these are the two shapes Cursor's 2026 mcp.json schema accepts; an entry that mixes both (has both `command` and `url`) MUST fail this AC
   - And for the canonical locked shape per server (documented in Task 2 blueprint):
     - `linear` — **remote URL shape**: `{ "url": "https://mcp.linear.app/mcp" }`. Linear's official hosted server handles OAuth 2.1 interactively via Cursor; no local command, no env block, no bearer header in the file (users log in through Cursor's MCP UI)
     - `github` — **local Docker stdio shape**: `{ "command": "docker", "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"] }`. The `-e GITHUB_PERSONAL_ACCESS_TOKEN` Docker flag (bare name, no `=value`) inherits the variable from the calling process's environment — Cursor passes its own env through to the spawned `docker` command, so whatever the user exported in their shell before launching Cursor flows through without the value ever being in the JSON file. NO `env` block in the JSON — the `env` block would require hardcoded values or `${VAR}` expansion (which Cursor does not perform per 2026 docs)
     - `microsoft-365` — **local npx stdio shape**: `{ "command": "npx", "args": ["-y", "@softeria/ms-365-mcp-server@latest"] }`. Auth is device-code interactive on first run; optional `MS365_MCP_CLIENT_ID` / `MS365_MCP_TENANT_ID` env vars are inherited from shell — NOT declared in the JSON file
     - `salesforce` — **local npx stdio shape**: `{ "command": "npx", "args": ["-y", "@salesforce/mcp@latest", "--orgs", "DEFAULT_TARGET_ORG", "--toolsets", "orgs,metadata,data,users"] }`. Auth relies on the user having run `sf org login web` out of band; the Salesforce CLI `sf` stores its session in the user's home directory
     - `gong` — **local npx stdio shape**: `{ "command": "npx", "args": ["-y", "github:kenazk/gong-mcp"] }`. Requires `GONG_ACCESS_KEY` and `GONG_ACCESS_KEY_SECRET` environment variables set in the user's shell before launching Cursor (inherited, not embedded). The community `kenazk/gong-mcp` package is NOT published to npm (registry 404 — Story 4.1 F1 review confirmation); `github:kenazk/gong-mcp` is npm's git-install path that installs directly from the public GitHub repo. The official Gong MCP server is listed as "coming soon" in Gong docs as of April 2026; when Gong publishes its official package, Epic 4 (or a follow-up ticket) will flip the package reference — the key name `gong` stays stable
   - And no entry contains any other top-level key beyond `{command, args, env, url, headers}` — the Cursor schema ignores unknown keys but accepting them lets drift in silently; the harness asserts exact key allowlisting per shape
   - And for every `args` value, each element is a string (not a number, not an object)

4. **AC4 — Credentials referenced only via environment variables; ZERO secret-shaped strings in the file**
   - Scan scope: `.cursor/mcp.json` only. The eleven secret-pattern regexes and the four `password=/token=/secret=/api_key=` literal-substring probes apply exclusively to the JSON file; the companion `.cursor/mcp.README.md` legitimately documents example prefixes (`ghp_…`, `Bearer <token>`, etc.) in prose and would false-positive these scanners. Banned-term and Derek-fixed-string scans (AC7) continue to cover both files.
   - Given `.cursor/mcp.json`
   - When the file is scanned for secret-shaped strings
   - Then NO substring matches any of these secret-pattern regexes (case-sensitive, fixed anchor-free):
     - `sk-[A-Za-z0-9_-]{20,}` — OpenAI-style keys (Linear may rotate to this; be defensive)
     - `ghp_[A-Za-z0-9]{20,}` — GitHub classic PAT prefix
     - `gho_[A-Za-z0-9]{20,}` — GitHub OAuth token prefix
     - `ghs_[A-Za-z0-9]{20,}` — GitHub server token prefix
     - `github_pat_[A-Za-z0-9_]{20,}` — GitHub fine-grained PAT prefix
     - `xox[baprs]-[A-Za-z0-9-]{10,}` — Slack token prefix family (defensive — Slack is not in active set but this catches copy-paste accidents)
     - `eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}` — JWT (three base64url-ish segments joined by `.`)
     - `Bearer [A-Za-z0-9_.-]{20,}` — inline bearer header with literal token
     - `AKIA[0-9A-Z]{16}` — AWS access-key ID prefix
     - `AIza[A-Za-z0-9_-]{35}` — Google API key prefix
     - `[A-Fa-f0-9]{32,}` — any hex string 32+ chars (catches most API secrets — intentionally broad; the file should have ZERO long hex runs)
   - And no value in the file contains a literal `${VAR}` or `$VAR` shell-expansion token — Cursor's 2026 mcp.json parser does NOT expand these (verified via community forum guidance); a file that references `${GITHUB_PERSONAL_ACCESS_TOKEN}` in an `env` block would ship a literal `${GITHUB_PERSONAL_ACCESS_TOKEN}` value to the spawned process, NOT the resolved secret. The only env-inheritance mechanism that works is the Docker `-e NAME` form in `args` (used for `github`) OR shell-exported variables inherited by Cursor's subprocess (used for `gong` / `microsoft-365` — see Task 2 blueprint)
   - And no value contains `password=`, `token=`, `secret=`, `api_key=` literal substrings (defensive; legitimate usage would put these in an `env` block with a value, which is also banned here)
   - And the file contains ZERO `env` blocks — none of the five entries has an `env` key. This is deliberate: an `env` block's values are literal strings passed to the spawned process; we cannot write `{"env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"}}` because the value is not expanded; we cannot write `{"env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_real_secret"}}` because that commits a secret. Therefore we route ALL env-var passing through either shell inheritance (default) or Docker's `-e NAME` form (used only for `github`). Absence of `env` blocks is the safest invariant

5. **AC5 — Companion `.cursor/mcp.README.md` documents each active MCP (purpose, required env vars, auth flow, wiki link)**
   - Given strict JSON cannot carry inline `//` comments documenting each server
   - When `.cursor/mcp.README.md` is inspected
   - Then the file exists at `.cursor/mcp.README.md`, is a markdown document with YAML frontmatter `type: mcp-readme`, `scope: work`, and body containing:
     - An H1 `# Active MCPs (.cursor/mcp.json)`
     - A one-paragraph preamble stating the file documents the five active MCPs wired in `.cursor/mcp.json` and that placeholder MCPs live in a separate Story-4.2 file (forward reference)
     - Exactly five per-server H2 sections, one per active MCP, followed by the two support H2 sections `## Env Variable Handling Convention` and `## Forward References` (seven H2 sections total), in the canonical order **Linear → GitHub → Microsoft 365 → Salesforce → Gong**. Each per-server H2 section contains: (1) a one-sentence purpose line; (2) a `**Transport:**` line stating `remote URL` or `local stdio (npx)` or `local stdio (docker)`; (3) a `**Auth:**` line stating `OAuth 2.1 (interactive via Cursor)` or `Environment variable: NAME` or `Local CLI session (sf org login web)`; (4) a `**Required env vars:**` bulleted list (may be `None — interactive OAuth` for Linear, `GITHUB_PERSONAL_ACCESS_TOKEN` for GitHub, `None — device-code flow` for M365, `None — Salesforce CLI session` for Salesforce, `GONG_ACCESS_KEY` and `GONG_ACCESS_KEY_SECRET` for Gong); (5) a `**Wiring link:**` line pointing to an internal Vixxo wiki placeholder (`TODO: Vixxo internal wiki entry`) or the upstream project README
   - And the file ends with a section `## Env Variable Handling Convention` explaining the three env-passing patterns used (shell inheritance, Docker `-e NAME`, interactive auth) and explicitly stating that Cursor's 2026 mcp.json parser does NOT expand `${VAR}` and therefore `.cursor/mcp.json` never contains an `env` block
   - And the file ends with a `## Forward References` section noting: (a) Story 4.2 will add pending-MCP placeholders in a separate `.cursor/mcp.placeholders.md` companion file (NOT in `.cursor/mcp.json` — keeping active JSON strict and valid); (b) Story 4.3 will add per-MCP `.env.example` sections enumerating the env vars above; (c) Story 4.4 will rewrite `docs/mcps.md` with the broader MCP catalog and wiki cross-links
   - And the file contains ZERO banned personal terms (17-token lock inherited from Stories 3.1 / 3.2 / 3.3 — `derek`, `neighbors`, `revivago`, `benji`, `flowtopic`, `gtd-life`, `gtdlife`, `wyoming`, `cheyenne`, `family`, `home`, `blog`, `wife`, `son`, `daughter`, `dog`, `personal`) and ZERO Derek-specific fixed strings (`Chiron`, `MasteryLab`, `Agile Weekly`, `Queen Creek`, `Gangplank`, `Bodybuilding.com`, `Integrum`, `Omarchy`, `derekneighbors.com`, `Playrix`, `Laurie`, `Deke`)
   - And the file ends with a single-line `<!-- Why: strict JSON forbids comments; this README documents each entry in .cursor/mcp.json per Epic 4 story 4.1 AC5. -->` terminator matching the Epic 2 / 3 convention

6. **AC6 — `.cursor/mcp.json` is tracked in git and NOT gitignored**
   - Given the root `.gitignore` and the current git working tree
   - When `git check-ignore -v .cursor/mcp.json` is run
   - Then it exits non-zero with empty output (the file is NOT ignored)
   - And `git ls-files --error-unmatch .cursor/mcp.json` exits `0` after the story lands (the file is tracked)
   - And `.gitignore` receives NO new patterns matching `.cursor/mcp.json`, `*.json`, `.cursor/*.json`, or `.cursor/mcp*` — AC6 is verified both as a gitignore-behavior assertion and as a byte-level `.gitignore` diff check (the root `.gitignore` from Story 1.1 + Story 1.1 F1 patch `!.env.example` must be the only content; no Story-4.1 edit)
   - And the companion `.cursor/mcp.README.md` is ALSO tracked and NOT ignored (same checks applied)

7. **AC7 — ZERO PII, Derek-identifying content, or Vixxo-employee real names in either file**
   - Given `.cursor/mcp.json` and `.cursor/mcp.README.md`
   - When the 17-token boundary-guarded banned-term regex is run across each file (`grep -iE '(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])'`)
   - Then zero matches in each file
   - And fixed-string scans for `Chiron`, `MasteryLab`, `Agile Weekly`, `Queen Creek`, `Gangplank`, `Bodybuilding.com`, `Integrum`, `Omarchy`, `derekneighbors.com`, `Playrix`, `Laurie`, `Deke`, `/Users/`, `Public/gtd-life`, `@gmail.com` return zero matches in each file
   - And no real employee names, email addresses (no `@`-joined mailbox+domain pattern), phone numbers, Microsoft Graph UPNs, or Teams `chatId` strings appear in either file
   - And the `mcp.README.md` placeholder-token discipline forbids any `{{…}}` tokens — the README is descriptive prose, not a template; the Story 5.2 wizard does not rewrite this file

8. **AC8 — Env-var-handling decision is documented and Story 4.2 placeholder strategy is locked**
   - Given the architectural decision in AC3 / AC4 / AC5 that Cursor's 2026 mcp.json parser does NOT expand `${VAR}` and therefore `.cursor/mcp.json` contains ZERO `env` blocks
   - When `.cursor/mcp.README.md` `## Env Variable Handling Convention` is read
   - Then it explicitly enumerates the three allowed env-passing patterns (shell inheritance, Docker `-e NAME` bare-form, interactive OAuth / CLI session) and states that any future MCP added in Story 4.2 or later MUST use one of these three patterns
   - And it explicitly locks the Story 4.2 placeholder convention: **placeholders live in `.cursor/mcp.placeholders.md` (a separate markdown companion), NOT as "commented-out JSON blocks" inside `.cursor/mcp.json`**. The rationale stated in the README: strict JSON forbids comments; a partially-commented `.cursor/mcp.json` would either be invalid JSON (Cursor silently rejects the whole file) or would require switching to JSON5 (non-standard; Cursor's parser status with JSON5 is inconsistent per 2026 forum reports)
   - And the Story 4.2 placeholder-file convention locked here specifies: `.cursor/mcp.placeholders.md` will contain one H2 section per pending MCP (Freshdesk, Dynamics, VixxoNow, VixxoLink, Gateway, ZoomInfo, HubSpot, AWS Connect, ChatFPT, Elastic, agent-skills Introspection MCP — eleven pending MCPs per Epic 4 Story 4.2 scope), each with a fenced `json` code block showing the canonical active-shape the placeholder would take when wired, followed by `// TODO: wiring; see <wiki link or issue>` as a markdown comment (not inside the JSON)
   - And this AC is satisfied by presence of the relevant section in `.cursor/mcp.README.md`; it is ALSO satisfied by Story 4.1's Dev Notes section that this story file explicitly records the decision; Story 4.2 MUST honor the locked convention or propose a change via an explicit correct-course

9. **AC9 — Deterministic validation harness exists and passes; regression chain extends cleanly**
   - Given the existing harness family under `_bmad-output/implementation-artifacts/tests/`
   - When Story 4.1 lands
   - Then a new harness `story-4-1-mcp-json-validation.sh` exists at `_bmad-output/implementation-artifacts/tests/story-4-1-mcp-json-validation.sh`, is marked executable (`chmod +x`), uses `#!/usr/bin/env bash` on line 1 and `set -euo pipefail` on line 2
   - And the harness implements gates:
     - `task1` — baseline-audit artifact `story-4-1-baseline-audit.md` present with required sections
     - `task2` — canonical-blueprint artifact `story-4-1-canonical-blueprint.md` present with the five per-server subsections plus placeholder-decision lock
     - `task3` — JSON shape verification: file exists, non-empty, trailing newline, LF-only, parses via `python3 -m json.tool`, root object has single key `mcpServers`, `mcpServers` contains exactly five keys in canonical order, each value is an object, each value has one of the two allowed shapes (stdio or remote), each value's key set is a subset of `{command, args, env, url, headers}`, no `env` blocks present, no `${VAR}` / `$VAR` substrings
     - `task4` — per-server shape locks per AC3 (Linear URL literal, GitHub Docker args literal, M365 npx args literal, Salesforce npx args literal, Gong npx args literal)
     - `task5` — secret-shaped-string scan per AC4 (all eleven secret-pattern regexes plus the ENV-expansion-token scan; the `[A-Fa-f0-9]{32,}` broad-hex probe and the `password=|token=|secret=|api_key=` equals-form probe) returns zero matches; deny-list scan for placeholder keys under `mcpServers` returns zero matches
     - `task6` — README presence + shape per AC5 (file exists, frontmatter, five H2 subsections in canonical order, env-var-handling section, forward-references section, banned-term regex yields zero matches, fixed-string scans yield zero matches, zero `{{…}}` tokens, "why" terminator)
     - `task7` — gitignore behavior per AC6 (`git check-ignore -v` returns non-zero for both `.cursor/mcp.json` and `.cursor/mcp.README.md`; root `.gitignore` byte-stable vs Story 1.1 handoff)
     - `task8` — self-check per Stories 2.1 / 3.1 / 3.3 pattern (shebang, `set -euo pipefail`, all case arms, all declared constants, `regex_self_probe` definition via `declare -F`)
     - `task9` — regression: invoke all ten predecessor harnesses (Stories 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3) in `all` mode and assert each exits `0` with `PASS: all`; assert per-harness `^PASS:` line-count fingerprint matches the expected vector (empirical — read from the Story 3.3 Task 6 handoff file and any later adjustments; if Story 3.3's fingerprint was `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7` for Stories 1.1 → 3.2, then Story 4.1 appends Story 3.3's own `PASS:` count measured during Task 1 baseline)
     - `all` dispatcher — runs task1 → task9 sequentially, prints `PASS: task<n>` after each, ends with `PASS: all`; emits exactly 10 `^PASS:` lines on success
   - And the harness implements `regex_self_probe()` that exercises: (a) the 17-token banned-term regex against `derek` (positive) and `derekson` (boundary-rejected); (b) the `ghp_[A-Za-z0-9]{20,}` secret-pattern regex against a synthetic `ghp_aaaabbbbccccddddeeee1234` (positive) and `ghp_short` (rejected for length); (c) a `${VAR}` probe against `${FOO}` (positive) and `$foo` (positive) and `dollar sign` (negative)
   - And the harness is BSD-grep and GNU-grep compatible, POSIX-bash-3.2 compatible, uses only `bash`, `grep`, `find`, `awk`, `sed`, `wc`, `head`, `tail`, `tr`, `sort`, `cut`, `od`, `python3 -m json.tool`, and shell built-ins (no `jq` — single-key / keyset assertions use `python3 -c '…'` one-liners, a pattern consistent with allowing Python in the test harness while keeping the production repo jq-free)
   - And the harness exits `0` with `PASS: all` on success; exits `1` with `FAIL: <gate>: <reason>` on stderr on failure

10. **AC10 — Zero regression across every prior-story artifact**
    - Given the ten predecessor stories' file-invariance expectations (root context files, rule pack, persona, memory templates, Obsidian config, me/ scaffold) and their harnesses
    - When Story 4.1 lands
    - Then ZERO bytes change in: `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `README.md`, `LICENSE`, `.gitignore`, `agents/personas/work.md`, the five `.cursor/rules/*.mdc` files from Stories 2.1 + 2.2 (`agent-identity.mdc`, `outbound-messaging-guardrail.mdc`, `memory-vault-protection.mdc`, `teams-dm-formatting.mdc`, `email-triage-thread-defaults.mdc`), the nine Story 3.1 memory-template files, the seven Story 3.2 `.obsidian/` JSON files, `memory/me/identity.md`, `memory/me/preferences.md`, `memory/.gitkeep`
    - And ZERO bytes change in any of the ten predecessor harnesses under `_bmad-output/implementation-artifacts/tests/` (`story-1-1-*` through `story-3-3-*`) — Story 4.1 is additive only; if any harness needs an allowlist extension (e.g. Story 1.1's `.cursor/` subdirectory allowlist must admit `mcp.json` + `mcp.README.md` beyond the already-admitted `rules`, `skills`), that extension MUST be codified explicitly in this AC as an integration-fix exception following the Story 2.1 commit `0db273b` / Story 3.1 F1 / Story 3.2 AC13 precedent. **Pre-story baseline check required:** during Task 1, verify whether `story-1-1-scaffold-validation.sh` (or any other predecessor harness) inspects `.cursor/` contents in a way that would reject new files at `.cursor/mcp.json` and `.cursor/mcp.README.md`. If yes, codify the minimum additive extension here and update this AC before Phase 2. If no, assert zero-edit invariance for all predecessor harnesses.
    - And Story 4.1 creates ONLY: `.cursor/mcp.json`, `.cursor/mcp.README.md`, the new harness `story-4-1-mcp-json-validation.sh`, three evidence artifacts (`story-4-1-baseline-audit.md`, `story-4-1-canonical-blueprint.md`, `story-4-1-task-handoff.md`), and this story file

11. **AC11 — Sprint tracker lifecycle flips correctly**
    - Given `_bmad-output/implementation-artifacts/sprint-status.yaml`
    - When Story 4.1 opens (Phase 1 — SM), progresses (Phase 2 — Dev), and closes (Phase 3 — review approval)
    - Then `4-1-write-cursor-mcp-json-with-active-mcps.status` is updated `backlog → ready-for-dev` at Phase 1, `ready-for-dev → review` at Phase 2, `review → done` at Phase 3 (single `backlog → review` on-disk transition acceptable per Stories 2.x / 3.x autonomous-swarm precedent)
    - And `epic-4.status` is updated `backlog → in-progress` at Phase 1 (the first Epic 4 story opening flips the epic per the workflow semantics at sprint-status.yaml lines 12 and 26)
    - And `epic-4.status` remains `in-progress` at Phase 3 (Stories 4.2, 4.3, 4.4 remain `backlog` at Story 4.1 close; epic does NOT yet flip to `done`)
    - And `last_updated` is set to `2026-04-21` on the Phase 1 edit
    - And no other story's status is regressed; every comment, blank line, inline spacing, and entry ordering in `sprint-status.yaml` is preserved byte-for-byte — the only diffs between pre-edit and post-edit files are the `status:` value flip on `4-1-…` plus the `epic-4.status` flip at Phase 1 plus the `last_updated` value change

12. **AC12 — Story is additive and does not spill into Epic 4.2 / 4.3 / 4.4 / Epic 5 territory**
    - Given the scope of Story 4.1
    - When the working-set file list is reviewed
    - Then Story 4.1 does NOT create `.cursor/mcp.placeholders.md` (Story 4.2 scope), does NOT create or edit `.env.example` (Story 4.3 scope), does NOT rewrite `docs/setup.md` or `docs/mcps.md` (Story 4.4 scope), does NOT edit `bin/init` or add any setup-wizard code (Epic 5 scope), does NOT add any CI / GitHub Actions workflow (Epic 6 scope), does NOT add any `agent-skills` Introspection MCP wiring (external project; Story 4.2 placeholder tracks it)
    - And Story 4.1 does NOT edit `.cursor/rules/*.mdc`, `agents/personas/work.md`, `memory/me/*.md`, or any root context file — the new `.cursor/mcp.json` is forward-referenced from `.cursor/rules/agent-identity.mdc` line 47–55's "Available Tools (overview)" block but that rule file already names the five active MCPs in prose and does not need to be updated to reference the new JSON path (per Story 2.1 Task 2 blueprint that locked the rule body as generic-prose-only)
    - And Story 4.1 creates NO `bin/` or `scripts/` code, NO `.github/workflows/` files, NO TypeScript / JavaScript / Python source files outside the validation harness

13. **AC13 — Active package/URL references are launch-verified as of commit date**
    - Given the five active MCP entries in `.cursor/mcp.json`
    - When each resolution target is probed
    - Then as of the Story 4.1 commit date: (a) `https://mcp.linear.app/mcp` returns a valid Cursor-compatible MCP handshake on HEAD probe, (b) `ghcr.io/github/github-mcp-server` resolves via `docker manifest inspect`, (c) `@softeria/ms-365-mcp-server@latest` resolves via `npm view @softeria/ms-365-mcp-server version`, (d) `@salesforce/mcp@latest` resolves via `npm view @salesforce/mcp version`, (e) `github:kenazk/gong-mcp` resolves via `curl -sI https://github.com/kenazk/gong-mcp` returning 200
    - And any future pin bump MUST re-run this probe before landing
    - Note: this AC is evidence-only; not gated by the harness (the harness is offline-safe by design)

## Tasks / Subtasks

- [x] **Task 1 — Baseline audit of Cursor mcp.json schema + canonical per-server configs (AC: 1, 3, 4)** **[Parallelizable with Task 2a–2e per-server research sub-tasks]**
  - [x] Confirm current state: `.cursor/mcp.json` does NOT yet exist; `.cursor/mcp.README.md` does NOT yet exist; `.cursor/rules/` exists with six files (`.gitkeep` + five rules) per Stories 1.1 / 2.1 / 2.2; `.cursor/skills/` exists from pre-template-swarm state.
  - [x] Capture Cursor 2026 mcp.json schema canonical form (root `mcpServers: {…}`; per-server either `{command, args, env?}` stdio-local shape OR `{url, headers?}` remote-HTTP shape; strict JSON — no comments, no trailing commas; `${VAR}` NOT expanded in `env` blocks per community forum guidance). Record the source URLs (Cursor docs, TrueFoundry 2026 guide, Cursor community forum "How to use environment variables in mcp.json").
  - [x] Per-server canonical-config research (parallelizable — may delegate to sub-agents):
    - Linear: `https://mcp.linear.app/mcp` remote URL, OAuth 2.1 interactive (no env vars). Source: `linear.app/docs/mcp`. Alternative: `Authorization: Bearer ${LINEAR_API_KEY}` header + `LINEAR_API_KEY` env — reject this in favor of OAuth because `${}` expansion is not supported and shell-exporting a bearer for a remote-URL header is not a clean pattern.
    - GitHub: Official `github/github-mcp-server` (repo `github/github-mcp-server`). Two transports: remote `https://api.githubcopilot.com/mcp/` with bearer header (bearer has same expansion problem) OR local Docker stdio `ghcr.io/github/github-mcp-server` with `-e GITHUB_PERSONAL_ACCESS_TOKEN` env-name-inheritance flag. **Choose local Docker stdio** for Story 4.1 because the bare-name `-e NAME` form cleanly inherits from shell without any JSON env block. Deprecated legacy npm package `@modelcontextprotocol/server-github` must NOT be used (archived as of April 2025 per GitHub docs).
    - Microsoft 365: Community `@softeria/ms-365-mcp-server` (most widely adopted per npm / GitHub research). Run via `npx -y @softeria/ms-365-mcp-server@latest`; interactive device-code auth on first run. Optional env `MS365_MCP_CLIENT_ID` / `MS365_MCP_TENANT_ID` — user exports in shell if needed; NOT declared in the JSON. Alternative: `@pnp/cli-microsoft365-mcp-server` — reject in favor of softeria because softeria wraps Graph directly while the pnp version wraps the `m365` CLI (adds an extra prereq).
    - Salesforce: Official `@salesforce/mcp` (package `@salesforce/mcp` per salesforcecli/mcp). Run via `npx -y @salesforce/mcp@latest --orgs DEFAULT_TARGET_ORG --toolsets orgs,metadata,data,users`. Requires user to have Salesforce CLI (`sf`) installed and authenticated via `sf org login web` out of band — the CLI session file in `~/.sf/` is how auth flows through. No env vars in the JSON.
    - Gong: Official Gong MCP "coming soon" per help.gong.io/docs/gong-mcp-server (target April 2026). Interim: community `kenazk/gong-mcp` (Node.js). After Story 4.1 F1 review confirmed `@kenazk/gong-mcp` is NOT on npm (registry 404), the canonical literal is `npx -y github:kenazk/gong-mcp` — `npx`'s git-install path resolves directly from the public GitHub repo. Requires `GONG_ACCESS_KEY` and `GONG_ACCESS_KEY_SECRET` env vars exported in shell before launching Cursor. If Gong ships its official server during this sprint, update the package reference in a follow-up commit.
  - [x] Capture the `.gitignore` content (Story 1.1 + F1 patch: `node_modules/`, `.env`, `.env.*`, `!.env.example`, `*.log`, `tmp/`) and confirm neither `.cursor/mcp.json` nor `.cursor/mcp.README.md` matches any ignore pattern. If a match is discovered, DO NOT edit `.gitignore` — raise an AC10 integration-fix exception and update this story before Phase 2.
  - [x] Confirm whether predecessor harnesses inspect `.cursor/` contents in a way that would reject new files. Grep each harness for `.cursor/` path references. If any harness has a deny-list for `.cursor/*` non-rule/non-skill files, document the minimum additive allowlist extension and update AC10.
  - [x] Persist baseline evidence at `_bmad-output/implementation-artifacts/tests/story-4-1-baseline-audit.md` with sections: `# Story 4.1 Baseline Audit`, `## Cursor mcp.json 2026 schema`, `## Per-server canonical config`, `## Env-var handling decision (no env blocks; shell inheritance + Docker -e NAME form)`, `## Secret-pattern regex set (eleven patterns)`, `## Gitignore invariance`, `## Predecessor-harness compatibility scan`, `## Source URLs`.

- [x] **Task 2 — Canonical blueprint for `.cursor/mcp.json` and `.cursor/mcp.README.md` (AC: 2, 3, 5, 8)** **[Sequential — depends on Task 1]**
  - [x] Author the blueprint at `_bmad-output/implementation-artifacts/tests/story-4-1-canonical-blueprint.md`.
  - [x] Lock the `.cursor/mcp.json` exact shape:
    ```json
    {
      "mcpServers": {
        "linear": {
          "url": "https://mcp.linear.app/mcp"
        },
        "github": {
          "command": "docker",
          "args": [
            "run",
            "-i",
            "--rm",
            "-e",
            "GITHUB_PERSONAL_ACCESS_TOKEN",
            "ghcr.io/github/github-mcp-server"
          ]
        },
        "microsoft-365": {
          "command": "npx",
          "args": [
            "-y",
            "@softeria/ms-365-mcp-server@latest"
          ]
        },
        "salesforce": {
          "command": "npx",
          "args": [
            "-y",
            "@salesforce/mcp@latest",
            "--orgs",
            "DEFAULT_TARGET_ORG",
            "--toolsets",
            "orgs,metadata,data,users"
          ]
        },
        "gong": {
          "command": "npx",
          "args": [
            "-y",
            "github:kenazk/gong-mcp"
          ]
        }
      }
    }
    ```
    (File ends with a trailing newline; 2-space indent; LF line endings; valid strict JSON.)
  - [x] Lock the `.cursor/mcp.README.md` frontmatter:
    ```yaml
    ---
    type: mcp-readme
    scope: work
    created: 2026-04-21
    updated: 2026-04-21
    tags: [mcp, work]
    ---
    ```
  - [x] Lock the `.cursor/mcp.README.md` body section order: `# Active MCPs (.cursor/mcp.json)` (H1), preamble paragraph, `## Linear`, `## GitHub`, `## Microsoft 365`, `## Salesforce`, `## Gong`, `## Env Variable Handling Convention`, `## Forward References`, `<!-- Why: … -->` terminator.
  - [x] Lock the per-server H2 template (five fields per section): `**Purpose:**`, `**Transport:**`, `**Auth:**`, `**Required env vars:**`, `**Wiring link:**`.
  - [x] Lock the per-server content:
    - Linear — Purpose: `Vixxo work task and project management (issues, projects, cycles).`; Transport: `remote URL (HTTP)`; Auth: `OAuth 2.1 interactive via Cursor's MCP UI`; env vars: `None — interactive OAuth on first connect`; Wiring link: `TODO: Vixxo internal wiki — Linear MCP onboarding`.
    - GitHub — Purpose: `Source control, code review, repository documentation, PR automation.`; Transport: `local stdio (docker)`; Auth: `Environment variable: GITHUB_PERSONAL_ACCESS_TOKEN`; env vars: `GITHUB_PERSONAL_ACCESS_TOKEN — export in shell before launching Cursor; Docker \`-e\` bare-name flag inherits from Cursor's subprocess env`; Wiring link: `https://github.com/github/github-mcp-server`.
    - Microsoft 365 — Purpose: `Outlook email and calendar; OneDrive; Teams chat; Graph API coverage.`; Transport: `local stdio (npx)`; Auth: `Device-code flow (interactive on first run); token cached in OS keychain`; env vars: `None required — MS365_MCP_CLIENT_ID / MS365_MCP_TENANT_ID optional for multi-tenant scenarios`; Wiring link: `https://github.com/softeria/ms-365-mcp-server`.
    - Salesforce — Purpose: `CRM, pipeline, accounts, contacts, Apex execution, SOQL queries.`; Transport: `local stdio (npx)`; Auth: `Salesforce CLI session — run \`sf org login web\` out of band`; env vars: `None required — session file in ~/.sf/`; Wiring link: `https://github.com/salesforcecli/mcp`.
    - Gong — Purpose: `Call recordings, transcripts, deal intelligence.`; Transport: `local stdio (npx)`; Auth: `Environment variables (inherited from shell)`; env vars: `GONG_ACCESS_KEY and GONG_ACCESS_KEY_SECRET — export in shell before launching Cursor`; Wiring link: `https://github.com/kenazk/gong-mcp` (interim until Gong publishes its official server per help.gong.io/docs/gong-mcp-server).
  - [x] Lock the `## Env Variable Handling Convention` body: three named patterns (shell inheritance, Docker `-e NAME` bare-form, interactive auth); explicit statement that Cursor does NOT expand `${VAR}` in `env` blocks per 2026 forum guidance; explicit statement that `.cursor/mcp.json` contains ZERO `env` blocks.
  - [x] Lock the `## Forward References` body: pointers to Story 4.2 (`.cursor/mcp.placeholders.md` convention), Story 4.3 (`.env.example`), Story 4.4 (`docs/mcps.md`).
  - [x] Lock the secret-pattern regex catalog (eleven patterns documented in AC4) and the banned-term catalog (17 tokens + 12 Derek-fixed-string probes) — direct carryover from Stories 3.1 / 3.2 / 3.3.
  - [x] Lock the Story 4.2 placeholder convention (AC8): separate `.cursor/mcp.placeholders.md` markdown file with per-pending-MCP H2 sections + fenced `json` code blocks. Document why commented JSON in `.cursor/mcp.json` is rejected (strict JSON; Cursor 2026 parser silently fails on any comment attempt).

- [x] **Task 3 — Author `.cursor/mcp.json` (AC: 1, 2, 3, 4)** **[Parallelizable with Task 4 once Task 2 blueprint is locked]**
  - [x] Create `.cursor/mcp.json` exactly matching the Task 2 blueprint shape. Verify via `python3 -m json.tool .cursor/mcp.json > /dev/null` (exits 0) and `node -e "JSON.parse(require('fs').readFileSync('.cursor/mcp.json','utf8'))"` (exits 0).
  - [x] Verify no comment syntax present: `grep -nE '^\s*//|/\*|\*/' .cursor/mcp.json` returns zero matches.
  - [x] Verify no trailing commas: `python3 -m json.tool` would reject them; additionally `grep -nE ',\s*[}\]]' .cursor/mcp.json` returns zero matches.
  - [x] Verify no `env` blocks: `python3 -c "import json; d=json.load(open('.cursor/mcp.json')); assert all('env' not in v for v in d['mcpServers'].values())"` exits 0.
  - [x] Verify no `${VAR}` or `$VAR` substrings: `grep -nE '\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]+' .cursor/mcp.json` returns zero matches.
  - [x] Verify key count and canonical order: `python3 -c "import json; d=json.load(open('.cursor/mcp.json')); keys=list(d['mcpServers'].keys()); assert keys == ['linear','github','microsoft-365','salesforce','gong'], keys"` exits 0.
  - [x] Verify trailing newline (`tail -c 1 .cursor/mcp.json | od -An -tx1 | tr -d '[:space:]'` equals `0a`) and LF-only line endings (`grep -c $'\r' .cursor/mcp.json` returns 0).
  - [x] Run the eleven secret-pattern probes from AC4 against `.cursor/mcp.json`; each must return zero matches.
  - [x] Confirm `git check-ignore -v .cursor/mcp.json` exits non-zero (file is NOT ignored) without editing `.gitignore`.

- [x] **Task 4 — Author `.cursor/mcp.README.md` (AC: 5, 7, 8)** **[Parallelizable with Task 3 once Task 2 blueprint is locked]**
  - [x] Create `.cursor/mcp.README.md` exactly matching the Task 2 blueprint shape.
  - [x] Verify frontmatter shape (`head -c 3` equals `---`; first block has the five required keys in canonical order per the blueprint).
  - [x] Verify body sections in order: H1 `# Active MCPs (.cursor/mcp.json)`, preamble, five H2 sections in canonical MCP order, `## Env Variable Handling Convention`, `## Forward References`, `<!-- Why: … -->` terminator.
  - [x] Verify each H2 section contains the five required `**Field:**` lines (Purpose, Transport, Auth, Required env vars, Wiring link).
  - [x] Run the 17-token banned-term regex and the twelve Derek fixed-string probes against `.cursor/mcp.README.md`; each must return zero matches.
  - [x] Run the placeholder-form probes: `{{…}}`, `{x}`, `<x>`, `%x%`, `${x}` — each must return zero matches in this file (README is descriptive prose, not templated).
  - [x] Confirm `git check-ignore -v .cursor/mcp.README.md` exits non-zero (file is NOT ignored) without editing `.gitignore`.

- [x] **Task 5 — Author the deterministic validation harness `story-4-1-mcp-json-validation.sh` (AC: 9, 10)** **[Sequential — depends on Tasks 3 + 4 files existing]**
  - [x] Create `_bmad-output/implementation-artifacts/tests/story-4-1-mcp-json-validation.sh`. Model on `story-3-3-identity-preferences-validation.sh`. `#!/usr/bin/env bash` on line 1, `set -euo pipefail` on line 2, `chmod +x`. POSIX-bash-3.2 compatible, BSD + GNU grep compatible.
  - [x] Declare constants at the top:
    - `PROJECT_ROOT`, `TESTS_DIR`, `SELF_PATH` — standard harness boilerplate
    - `MCP_JSON="${PROJECT_ROOT}/.cursor/mcp.json"`
    - `MCP_README="${PROJECT_ROOT}/.cursor/mcp.README.md"`
    - `BASELINE_AUDIT_PATH="${TESTS_DIR}/story-4-1-baseline-audit.md"`
    - `BLUEPRINT_PATH="${TESTS_DIR}/story-4-1-canonical-blueprint.md"`
    - `EXPECTED_SERVER_KEYS=( linear github microsoft-365 salesforce gong )` — five keys in canonical order
    - `DENY_LIST_SERVER_KEYS=( freshdesk dynamics vixxonow vixxolink gateway zoominfo hubspot aws-connect chatfpt elastic introspection agent-skills slack notion gmail google-calendar obsidian linkedin )` — eighteen deny-list keys (Story 4.2 placeholders + speculative accidental keys)
    - `SECRET_PATTERNS=( 'sk-[A-Za-z0-9_-]{20,}' 'ghp_[A-Za-z0-9]{20,}' 'gho_[A-Za-z0-9]{20,}' 'ghs_[A-Za-z0-9]{20,}' 'github_pat_[A-Za-z0-9_]{20,}' 'xox[baprs]-[A-Za-z0-9-]{10,}' 'eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}' 'Bearer [A-Za-z0-9_.-]{20,}' 'AKIA[0-9A-Z]{16}' 'AIza[A-Za-z0-9_-]{35}' '[A-Fa-f0-9]{32,}' )` — eleven secret-pattern regexes (documented in AC4)
    - `BANNED_TERMS_REGEX='(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])'` — 17-token lock identical to Stories 3.1 / 3.2 / 3.3
    - `DEREK_FIXED_STRINGS=( Chiron MasteryLab "Agile Weekly" "Queen Creek" Gangplank "Bodybuilding.com" Integrum Omarchy derekneighbors.com Playrix Laurie Deke )` — twelve fixed-string probes
    - Ten prior-harness paths: `STORY_1_1_HARNESS` through `STORY_3_3_HARNESS`
    - `EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 )` — ten entries (add Story 3.3's count to the Story 3.3 chain of nine; value `7` matches Story 3.3's `task1`–`task6` + `all`). **Dev must verify during Task 5 implementation** by running each predecessor harness once in `all` mode and recording the actual `^PASS:` line count. If any differs from `7` for Story 3.3, update this array and document the discrepancy.
  - [x] Implement `regex_self_probe()` per AC9 — exercises banned-term regex positive + boundary-rejected, `ghp_` secret-pattern positive + short-rejected, `${VAR}` probe positive + negative. `fail "regex probe: …"` on mismatch.
  - [x] Implement `check_task1` — require `BASELINE_AUDIT_PATH` exists, contains title `# Story 4.1 Baseline Audit`, contains each required section header (Cursor mcp.json 2026 schema, Per-server canonical config, Env-var handling decision, Secret-pattern regex set, Gitignore invariance, Predecessor-harness compatibility scan, Source URLs).
  - [x] Implement `check_task2` — require `BLUEPRINT_PATH` exists, contains title `# Story 4.1 Canonical Blueprint`, contains one subsection per server (five) plus env-var-handling lock plus Story 4.2 placeholder decision lock plus secret-pattern + banned-term catalog.
  - [x] Implement `check_task3` — JSON shape verification: `[[ -f "${MCP_JSON}" ]]`, `[[ -s "${MCP_JSON}" ]]`, trailing newline, LF-only, `python3 -m json.tool "${MCP_JSON}" >/dev/null` exits 0, root has single key `mcpServers` (via `python3 -c`), five canonical keys in order, each value is an object, each value's key set is a subset of `{command, args, env, url, headers}`, no `env` blocks present, no `${VAR}` / `$VAR` substrings.
  - [x] Implement `check_task4` — per-server shape locks per AC3: Linear URL literal equals `https://mcp.linear.app/mcp`; GitHub `command` equals `docker` and `args` equals the six-element literal array; M365 `command` equals `npx` and `args` equals the two-element literal array; Salesforce `command` equals `npx` and `args` equals the seven-element literal array; Gong `command` equals `npx` and `args` equals the two-element literal array.
  - [x] Implement `check_task5` — secret-shape scan: loop `SECRET_PATTERNS` and for each run `grep -E` on both `MCP_JSON` and `MCP_README`; assert zero matches per pattern per file. Also assert zero `${VAR}` substrings in both files. Also assert zero deny-list-server-key occurrences as top-level `mcpServers` keys (via `python3 -c` key-membership check).
  - [x] Implement `check_task6` — README shape: `[[ -f "${MCP_README}" ]]`, frontmatter first three bytes `---`, frontmatter keys in canonical order via awk line-walk, body section headings in canonical order (H1 then five H2s then env-var-handling H2 then forward-references H2), five required `**Field:**` lines per per-server H2 section, banned-term regex + Derek fixed-string probes yield zero matches, placeholder-form probes yield zero matches, `<!-- Why: …-->` terminator present on last non-blank line.
  - [x] Implement `check_task7` — gitignore behavior: `git check-ignore -v "${MCP_JSON}"` exits non-zero; `git check-ignore -v "${MCP_README}"` exits non-zero. Also assert `.gitignore` byte-stability: `sha256sum .gitignore` equals the Story 1.1 F1-patch handoff fingerprint (Dev records fingerprint during Task 1 baseline).
  - [x] Implement `check_task8` — self-check per Stories 2.x / 3.x pattern: `head -n 1` equals `#!/usr/bin/env bash`; `grep -Fq 'set -euo pipefail'`; every case arm present (`task1)` through `task9)` and `all)`); every declared constant name appears (loop across a named array); `declare -F regex_self_probe >/dev/null 2>&1`.
  - [x] Implement `check_task9` — regression: loop ten predecessor harnesses, `require_file_exists`, invoke `bash "${harness}" all 2>&1`, capture combined stdout/stderr, count `^PASS:` lines via `grep -c '^PASS:'`, compare to `EXPECTED_PASS_COUNTS[$i]`; echo captured output on non-zero exit or count mismatch; `fail` with sub-harness name on any violation.
  - [x] Implement the `mode` dispatcher: `task1 → task9` gates plus `all` mode that runs task1 through task9 sequentially, echoing `PASS: task<n>` after each and `PASS: all` at the end. Under `all` mode emits exactly 10 `^PASS:` lines.
  - [x] Add header comment block stating: (a) Story 4.1 writes `.cursor/mcp.json` with the five active Vixxo MCPs and a companion README; (b) strict JSON forbids comments so documentation lives in `.cursor/mcp.README.md`; (c) `env` blocks are intentionally absent to avoid `${VAR}`-expansion pitfalls; (d) regression chain extends Story 3.3's nine-harness chain by one (adds Story 3.3 as the tenth predecessor); (e) Story 4.2 placeholder convention locked in the blueprint and README.

- [x] **Task 6 — Run the full regression and capture the Task Handoff artifact (AC: 9, 10, 11)** **[Sequential — depends on Task 5]**
  - [x] Run `bash _bmad-output/implementation-artifacts/tests/story-4-1-mcp-json-validation.sh all`. Capture the full transcript. Expect `PASS: task1` → `PASS: task9` → `PASS: all`, exit 0, exactly 10 `^PASS:` lines.
  - [x] Re-run each of the ten predecessor harnesses individually in `all` mode (`1.1`, `1.2`, `1.3`, `2.1`, `2.2`, `2.3`, `2.4`, `3.1`, `3.2`, `3.3`). All ten must exit `0` with `PASS: all`. Verify per-harness `^PASS:` line-count fingerprint.
  - [x] Run the three additional verification steps from the JSON-validity doctrine: `python3 -m json.tool .cursor/mcp.json`, `node -e "JSON.parse(require('fs').readFileSync('.cursor/mcp.json','utf8'))"`, and `git check-ignore -v .cursor/mcp.json` (expected: non-zero). Capture output.
  - [x] Persist `_bmad-output/implementation-artifacts/tests/story-4-1-task-handoff.md` with: (a) AC-to-file map (one row per AC pointing at the harness gate, file path, or grep output that proves it); (b) full validation command transcript (Story 4.1 harness + ten regression harnesses — eleven harnesses total); (c) SHA-256 checksums of `.cursor/mcp.json` and `.cursor/mcp.README.md` (for future drift detection); (d) forward-looking notes: Story 4.2 will add `.cursor/mcp.placeholders.md`, Story 4.3 will add `.env.example`, Story 4.4 will rewrite `docs/mcps.md`, Epic 5 Story 5.3 will call each active MCP to verify connectivity; (e) zero-edit verification block listing every Story 1.x / 2.x / 3.x artifact and harness asserted byte-stable.

- [x] **Task 7 — Sprint tracker and story status synchronization (AC: 11)** **[Independent; typically last]**
  - [x] Flip `_bmad-output/implementation-artifacts/sprint-status.yaml` entry `4-1-write-cursor-mcp-json-with-active-mcps.status` from `backlog` to `ready-for-dev` during Phase 1 (SM pass); then to `review` at Dev handoff; then to `done` at Phase 3 review approval.
  - [x] Flip `epic-4.status` from `backlog` to `in-progress` during Phase 1 (first Epic 4 story opening).
  - [x] Preserve `epic-4.status` at `in-progress` through Phases 2 and 3 (Stories 4.2 / 4.3 / 4.4 remain `backlog` at Story 4.1 close; epic closes only after all four stories land).
  - [x] Update `last_updated` in `sprint-status.yaml` to `2026-04-21` on the Phase 1 edit.
  - [x] Preserve every comment, blank line, inline spacing, and entry ordering byte-for-byte. Only diffs: `status:` value flips on `4-1-…` plus `epic-4.status: backlog → in-progress` plus `last_updated` value change.

## Dev Notes

### Artifact availability

- Planning / tracking artifacts used by this story:
  - `_bmad/bmm/config.yaml` (BMAD v6.3.0; `user_name: Vixxo Employee`; `planning_artifacts` / `implementation_artifacts` path variables).
  - `_bmad-output/planning-artifacts/epics.md` lines 288–300 — Epic 4 overview; Story 4.1 ACs at lines 290–300. Story 4.2 scope (placeholder list of eleven MCPs) at lines 302–310. Story 4.3 scope at lines 312–321. Story 4.4 scope at lines 323–334.
  - `_bmad-output/planning-artifacts/architecture.md` — 26 lines total. Confirms template-only scope, `{{employee_name}}` / `{{employee_role}}` placeholder-driven identity convention, secrets-via-.gitignore discipline (NFR4 — `.env` is gitignored, `.env.example` is allowlisted per Story 1.1 F1 patch).
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` — story key `4-1-write-cursor-mcp-json-with-active-mcps`, Linear `AIP-40`, current status `backlog`; `epic-4.status: backlog` (no Epic 4 story has opened yet); `last_updated: "2026-04-20"`.
  - Prior story files (all `done`): `1-1-…` through `3-3-…`. Pattern source for harness structure, banned-term regex discipline, POSIX-ERE boundary guards, Phase-4 F-series review-fix pattern, autonomous-swarm status-collapse convention.
  - `.gitignore` content (Story 1.1 + F1 patch): `node_modules/`, `.env`, `.env.*`, `!.env.example`, `*.log`, `tmp/`. Byte-stable during Story 4.1.
- Missing at expected paths:
  - `_bmad-output/planning-artifacts/prd.md` — does not exist. Story 4.1 relies on epics.md + architecture.md + sprint-status.yaml + prior-story-file patterns.
  - `_bmad-output/planning-artifacts/ux-design-specification.md` — does not exist. Story 4.1 has no UX surface (JSON + markdown only).
  - `_bmad/bmm/workflows/4-implementation/bmad-create-story/template.md` — does not exist. Story 4.1 uses the emergent shape from Stories 1.1 → 3.3 (Status + Story + ACs + Tasks/Subtasks + Dev Notes + Change Log + Dev Agent Record + File List + References).

### Epic 4 story partition (why 4.1 is "active MCPs only, placeholders and env example come later")

- **Story 4.1 (this story):** Write `.cursor/mcp.json` with the five active Vixxo MCPs (Linear, GitHub, Microsoft 365, Salesforce, Gong) as strict valid JSON referencing env vars only via (a) Docker `-e NAME` bare-form, (b) shell inheritance, or (c) interactive OAuth / CLI session. Add `.cursor/mcp.README.md` companion documenting each server (purpose, transport, auth, env vars, wiring link). Lock the Story 4.2 placeholder convention (`.cursor/mcp.placeholders.md`). Flip `epic-4.status` to `in-progress`.
- **Story 4.2 (backlog):** Add `.cursor/mcp.placeholders.md` with eleven pending MCPs (Freshdesk, Dynamics, VixxoNow, VixxoLink, Gateway, ZoomInfo, HubSpot, AWS Connect, ChatFPT, Elastic, agent-skills Introspection MCP). Each entry gets an H2 with a fenced `json` code block showing the wiring shape + a `// TODO:` markdown comment (not inside the JSON — this keeps `.cursor/mcp.json` strict and valid).
- **Story 4.3 (backlog):** Write `.env.example` with per-MCP sections. Active-MCP sections enumerate the env vars from Story 4.1 README (`GITHUB_PERSONAL_ACCESS_TOKEN`, `GONG_ACCESS_KEY`, `GONG_ACCESS_KEY_SECRET`, optional `MS365_MCP_CLIENT_ID` / `MS365_MCP_TENANT_ID`). Placeholder-MCP sections come from Story 4.2 with `status: placeholder` marker per Epic 4 Story 4.3 AC. `.env.example` is allowlisted by the Story 1.1 F1 `.gitignore` patch; `.env` remains gitignored.
- **Story 4.4 (backlog):** Rewrite `docs/setup.md` + `docs/mcps.md` with self-serve onboarding. `docs/mcps.md` gets a catalog table (MCP, status, env vars, wiring link); `docs/setup.md` walks through clone → `bin/init` → verify.
- **Epic 5 Story 5.3 (backlog):** Wizard attempts a simple call against each active MCP and reports PASS/FAIL. `.cursor/mcp.json` is the wizard's configuration source.

Story 4.1 is intentionally narrow: only the active JSON + companion README + harness + evidence artifacts. The placeholder strategy, env-example, and onboarding docs are separate stories.

### Env-var handling — the architectural decision

**Cursor's 2026 mcp.json parser does NOT perform shell-style variable expansion inside `env` blocks.** This is confirmed by multiple 2026 community forum threads and is the root of most "my MCP won't start" support tickets.

Concretely: a file that declares `"env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"}` passes the literal string `${GITHUB_PERSONAL_ACCESS_TOKEN}` to the spawned process — which is wrong. The server authenticates with a literal 23-character string that starts with `$`, the GitHub API rejects it, and the MCP appears broken.

The three patterns that DO work cleanly:

1. **Shell inheritance** — Cursor inherits the shell env from the process that launched it (macOS: via `launchctl` env or the shell from which you ran `cursor`; Linux: similar). Any env var exported in the user's shell (e.g. `export GONG_ACCESS_KEY=…` in `~/.zshrc` or `~/.bashrc`) flows through to MCP subprocesses IF no explicit `env` block overrides it. Used by: Gong (`GONG_ACCESS_KEY`, `GONG_ACCESS_KEY_SECRET`), Microsoft 365 (`MS365_MCP_CLIENT_ID`, `MS365_MCP_TENANT_ID`) — though M365 uses device-code auth by default and doesn't strictly need env vars.

2. **Docker `-e NAME` bare-form** — When the command is `docker run … -e GITHUB_PERSONAL_ACCESS_TOKEN … image`, the bare-name form (NO `=value`) instructs Docker to read the variable from its own environment at spawn time. Docker's environment is inherited from Cursor, which is inherited from shell. Net effect: the GitHub PAT exported in shell flows through shell → Cursor → Docker → the MCP server inside the container. The JSON file holds only the flag `-e GITHUB_PERSONAL_ACCESS_TOKEN` — no secret, no expansion token, just a variable name. Used by: GitHub.

3. **Interactive auth / external CLI session** — Linear uses OAuth 2.1 via Cursor's MCP UI (no env var needed). Salesforce uses the local `sf` CLI session file in `~/.sf/` (no env var needed; user runs `sf org login web` once out of band). Microsoft 365 uses device-code flow on first `npx` run (token cached in OS keychain; no env var needed for single-tenant scenarios). Used by: Linear, Salesforce, Microsoft 365.

**Consequence for `.cursor/mcp.json`:** ZERO `env` blocks in the file. This is the invariant that AC4 enforces. Any future MCP added (Story 4.2 placeholders becoming actives, or new MCPs post-Epic-4) MUST choose one of the three patterns above.

### JSON-validity doctrine

- Strict JSON: no comments (`//`, `/* */`), no trailing commas, no JSON5 / JSONC extensions, no YAML, no HCL. This is what Cursor's 2026 parser accepts; a file that violates this is silently rejected (whole file disabled, not just the offending server).
- Validation uses BOTH `python3 -m json.tool` and `node -e "JSON.parse(…)"` — these are the two most commonly available strict-JSON parsers and they catch slightly different edge cases (Python is stricter on Unicode escapes; Node is stricter on lone surrogate pairs). Both must pass.
- Indentation: 2-space. Line endings: LF. Trailing newline required.
- Key ordering: Cursor's settings UI renders servers in file order (not alphabetical), so the canonical order `linear → github → microsoft-365 → salesforce → gong` is preserved to keep UI stable.

### Secret-pattern regex catalog (eleven patterns)

The catalog is defensive: it includes patterns for secret families we don't currently use (OpenAI, Slack, AWS, Google) to catch copy-paste accidents from unrelated docs. The broad `[A-Fa-f0-9]{32,}` probe is intentionally over-matching — the file should have ZERO long hex runs, so any hit is worth investigating. Eleven patterns total, documented verbatim in AC4 and in `.cursor/mcp.README.md` `## Env Variable Handling Convention`.

Why not just rely on existing PII scanners? Because this specific file class (`.cursor/mcp.json`) is a known ingress point for AI-agent credentials, and the standard Vixxo PII denylist (Epic 6 Story 6.1) is oriented toward personal-content leakage, not API-secret leakage. Story 6.1's deny-list will reference this regex catalog as the "secret-pattern family" complementary to the "PII-token family" — both scanned in the Epic 6 CI gate.

### Banned-term regex discipline (17 tokens; inherited verbatim)

Story 4.1 inherits the Stories 3.1 / 3.2 / 3.3 Phase-4-locked 17-token banned-term set. Zero new tokens added; zero tokens removed. Boundary-guarded regex: `(^|[^A-Za-z])TOKEN($|[^A-Za-z])`, case-insensitive via `grep -iE`. Fixed-string Derek probes identical to Story 3.3 (twelve probes: `Chiron`, `MasteryLab`, `Agile Weekly`, `Queen Creek`, `Gangplank`, `Bodybuilding.com`, `Integrum`, `Omarchy`, `derekneighbors.com`, `Playrix`, `Laurie`, `Deke`).

### Package-version discipline

Every package name / repository URL referenced in `.cursor/mcp.json` is pinned via `@latest` rather than a fixed version. Rationale:

- Vixxo employees clone the template and expect the latest compatible MCP server versions (employees don't want to chase version bumps).
- `@latest` floats; if a breaking change lands upstream, employees feel it immediately and the fix is a coordinated template update. This is preferable to silently-outdated behavior.
- Alternative: pin specific versions (e.g. `@salesforce/mcp@0.12.3`). Rejected because the template owner (Vixxo's AI cohort lead) would need to bump versions continuously; Vixxo's cadence is "update when something breaks," not "every Tuesday."
- The ONE exception: the GitHub Docker image `ghcr.io/github/github-mcp-server` does NOT carry a tag — Docker defaults to `latest`. Equivalent behavior to npm `@latest`.

### Previous story learnings to carry forward

- **POSIX-ERE boundary guards** (Stories 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2 / 3.3): `(^|[^A-Za-z])TOKEN($|[^A-Za-z])` works on macOS BSD grep, GNU grep, and busybox/Alpine grep identically. Do NOT use `\b`, `\<`, `\>`, or Perl-compatible regex.
- **`regex_self_probe` fail-fast** (all prior stories): probe exercises positive + boundary-rejected for at least two tokens AND at least one secret-pattern positive + short-rejected AND at least one env-expansion-token positive + negative.
- **Phase 4 F6 sub-harness capture** (Story 2.2): `check_task9` regression gate captures combined stdout/stderr via `2>&1`, echoes captured output on non-zero exit, fails with sub-harness name.
- **Phase 4 F7 PASS-count fingerprint** (Stories 3.1 / 3.2 / 3.3): `check_task9` asserts exact `^PASS:` line count per sub-harness. Dev verifies counts during Task 5 by running each predecessor harness once and recording.
- **Phase 4 F1 allowlist-exception codification** (Stories 3.1 / 3.2): when a predecessor harness needs a one-line additive extension, the extension is codified as an integration fix following Story 2.1 commit `0db273b` precedent. **Story 4.1 Task 1 includes an explicit "predecessor-harness compatibility scan" step** (check each predecessor for `.cursor/` allowlist/denylist patterns). If any scan finds a pattern that rejects the new `.cursor/mcp.json` or `.cursor/mcp.README.md`, codify the minimum extension and update AC10 before Phase 2. If no scan finds such a pattern (expected outcome — the predecessor harnesses inspect `.cursor/rules/` contents, not `.cursor/*` generically), assert zero-edit invariance.
- **Story 3.3 AC12 scope fence** (Story 3.3): story-creates-ONLY list used to prevent scope creep. Story 4.1 AC12 inherits the pattern — creates ONLY the seven artifacts listed (two production files + one harness + three evidence docs + this story).
- **Story 3.3 additive-vs-integration-fix** (Story 3.3 AC10): Story 4.1 is ADDITIVE; no predecessor edits expected. If an unexpected integration fix surfaces during dev, follow the F1 codification pattern.

### Risks and concerns

- **Gong MCP package availability** — As of April 2026, Gong's official MCP server is listed as "coming soon." The interim `kenazk/gong-mcp` (or `@kenazk/gong-mcp` npm scope) may not be published to npm. Dev must verify during Task 1 and document either (a) a working npm install path, or (b) a local-clone fallback pattern in `.cursor/mcp.README.md` with a TODO to swap when Gong ships its official server. If neither works, propose a correct-course to defer Gong to a later story.
- **Docker dependency for GitHub** — Using the Docker-based GitHub MCP requires employees to have Docker Desktop installed. This is documented in `.cursor/mcp.README.md` `## GitHub` section. Alternative: the remote `https://api.githubcopilot.com/mcp/` URL — rejected for Story 4.1 because the remote URL requires a `Bearer <TOKEN>` header and Cursor doesn't expand `${VAR}` in headers either; the user would have to paste a literal PAT into the JSON file, violating AC4. If Docker proves unpopular among employees, Story 4.4 can document the trade-off or a later story can introduce an `envmcp`-style wrapper.
- **M365 device-code flow** — First-run `@softeria/ms-365-mcp-server` pops a device-code URL in the MCP server's logs. If the Vixxo tenant has conditional-access policies that block device-code flow, the MCP will never authenticate. This is a Vixxo-tenant configuration issue, not an MCP issue; the README documents it as a known risk and points to the softeria project's issue tracker.
- **Salesforce CLI prerequisite** — Employees must install the `sf` CLI (`npm install -g @salesforce/cli` or the Mac installer) before the Salesforce MCP works. Documented in README. Epic 5 wizard may install the CLI automatically in a later story.
- **Env-var inheritance on macOS** — Cursor launched from Finder (double-click) on macOS may not inherit shell env vars from `~/.zshrc` because Finder-launched apps get `launchctl`'s environment, not the shell's. Employees who launch Cursor from `cursor` in a terminal see shell env flow through; employees who launch from Finder may see `GITHUB_PERSONAL_ACCESS_TOKEN` / `GONG_ACCESS_KEY` missing. Workaround: `launchctl setenv GITHUB_PERSONAL_ACCESS_TOKEN "…"` or the `launchd.conf` equivalent. Documented in README with a link to the Cursor community thread.
- **JSON parser version skew between `python3 -m json.tool` and `node -e`** — Rare edge case: a file that parses in Python 3.12 may fail in Node 20 on very specific Unicode escape sequences. Unlikely to affect a clean-authored `.cursor/mcp.json`, but the harness runs both parsers as defense in depth.

### Project Structure Notes

- New files created by this story:
  - `.cursor/mcp.json` (project-local MCP configuration; five active servers; strict JSON)
  - `.cursor/mcp.README.md` (companion documentation — purpose of each server + env-var convention)
  - `_bmad-output/implementation-artifacts/tests/story-4-1-mcp-json-validation.sh` (deterministic validation harness; nine gates + `all`)
  - `_bmad-output/implementation-artifacts/tests/story-4-1-baseline-audit.md` (Task 1 evidence)
  - `_bmad-output/implementation-artifacts/tests/story-4-1-canonical-blueprint.md` (Task 2 evidence)
  - `_bmad-output/implementation-artifacts/tests/story-4-1-task-handoff.md` (Task 6 evidence)
  - `_bmad-output/implementation-artifacts/4-1-write-cursor-mcp-json-with-active-mcps.md` (this file)
- Files modified by this story:
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` (Story 4.1 status flips + `epic-4.status: backlog → in-progress` + `last_updated` + this file's `Dev Agent Record` / `Change Log` / `File List` sections updated at Dev handoff)
- Files NOT modified by this story (byte-stable invariance):
  - `.gitignore`, `README.md`, `LICENSE`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`
  - All `.cursor/rules/*.mdc` (six files including `.gitkeep`)
  - All `agents/personas/*.md` (one file plus `.gitkeep`)
  - All `memory/**/*.md` files (nine Story 3.1 templates + Story 3.3 identity/preferences)
  - All `memory/.obsidian/*.json` files (seven Story 3.2 config files)
  - All ten predecessor harnesses under `_bmad-output/implementation-artifacts/tests/story-[1-3]-*.sh`

### References

- `_bmad-output/planning-artifacts/epics.md` Epic 4 overview (lines 288–300), Story 4.1 ACs (lines 290–300), Story 4.2 placeholder scope (lines 302–310), Story 4.3 env.example scope (lines 312–321), Story 4.4 docs scope (lines 323–334), Tier 1 priority order (lines 117–130).
- `_bmad-output/planning-artifacts/architecture.md` (26 lines — template-only architecture, placeholder-driven identity fields, secrets-via-.gitignore discipline).
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (story key `4-1-write-cursor-mcp-json-with-active-mcps`, Linear `AIP-40`, `epic-4.status: backlog` pre-story).
- Story 3.3 file `_bmad-output/implementation-artifacts/3-3-seed-empty-identity-and-preferences.md` (harness structure precedent; 17-token banned-term lock; Derek fixed-string discipline; regex self-probe discipline).
- Story 1.1 file `_bmad-output/implementation-artifacts/1-1-scaffold-directory-structure-and-root-files.md` and its F1 review-fix (`.env.example` allowlist; relevant because `.cursor/mcp.json` must similarly NOT be gitignored).
- Story 2.1 file `_bmad-output/implementation-artifacts/2-1-port-agent-identity-rule-generic.md` (identity-rule "Available Tools" lists the five active MCPs — Story 4.1 does NOT edit the rule but cross-references it).
- Story 2.3 file `_bmad-output/implementation-artifacts/2-3-create-single-generic-work-persona.md` (work persona "Available MCPs" table — Story 4.1 does NOT edit the persona but cross-references it).
- `.cursor/rules/agent-identity.mdc` lines 47–55 (identity rule "Available Tools (overview)" active MCP list: Linear, GitHub, Microsoft 365, Salesforce, Gong).
- `agents/personas/work.md` (work persona "Available MCPs" table: same five entries).
- Cursor MCP documentation: `https://cursor.com/docs/cli/mcp` (CLI MCP config); Cursor forum thread `https://forum.cursor.com/t/how-to-use-environment-variables-in-mcp-json/79296` (confirms `${VAR}` NOT expanded in 2026; workarounds documented).
- Cursor MCP 2026 guide: `https://www.truefoundry.com/blog/mcp-servers-in-cursor-setup-configuration-and-security-guide` (schema reference; strict-JSON guidance).
- Cursor MCP 2026 guide: `https://www.nxcode.io/resources/news/cursor-mcp-servers-complete-guide-2026` (project-local `.cursor/mcp.json` vs global `~/.cursor/mcp.json`).
- Linear MCP docs: `https://linear.app/docs/mcp` (official hosted remote server at `https://mcp.linear.app/mcp`; OAuth 2.1; no env vars required).
- Linear MCP changelog: `https://linear.app/changelog/2025-05-01-mcp` (remote URL launch announcement).
- GitHub MCP repo: `https://github.com/github/github-mcp-server` (official server; Docker image `ghcr.io/github/github-mcp-server`; `GITHUB_PERSONAL_ACCESS_TOKEN` env var).
- GitHub MCP Cursor install guide: `https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-cursor.md` (project-local `.cursor/mcp.json` example; remote URL alternative).
- Microsoft 365 MCP npm: `https://www.npmjs.com/package/%40softeria%2Fms-365-mcp-server` (community package `@softeria/ms-365-mcp-server`; device-code flow; optional `MS365_MCP_CLIENT_ID` / `MS365_MCP_TENANT_ID`).
- Microsoft 365 MCP repo: `https://github.com/softeria/ms-365-mcp-server`.
- Salesforce MCP npm: `https://www.npmjs.com/package/%40salesforce/mcp` (official `@salesforce/mcp`; requires Salesforce CLI `sf` session; `--orgs DEFAULT_TARGET_ORG`).
- Salesforce MCP repo: `https://github.com/salesforcecli/mcp`.
- Gong MCP "coming soon": `https://help.gong.io/docs/gong-mcp-server` (official Gong MCP target April 2026; interim community packages).
- Gong MCP community repo (Node.js): `https://github.com/kenazk/gong-mcp` (interim package; `GONG_ACCESS_KEY` + `GONG_ACCESS_KEY_SECRET` env vars).
- Gong MCP announcement: `https://www.gong.io/press/gong-introduces-model-context-protocol-mcp-support-to-unify-enterprise-ai-agents-from-hubspot-microsoft-salesforce-and-others` (Gong's MCP strategy; enterprise positioning).

## Change Log

- 2026-04-21: Story created; moved from `backlog` to `ready-for-dev`; `epic-4.status` flipped from `backlog` to `in-progress`.
- 2026-04-21: Dev handoff — Tasks 1–7 complete; `.cursor/mcp.json` + `.cursor/mcp.README.md` + `story-4-1-mcp-json-validation.sh` + three evidence artifacts authored. Full harness exits `0` with 10 `^PASS:` lines; all ten predecessor harnesses regress clean. Story status flipped `ready-for-dev` → `review`.

## Dev Agent Record

### Agent Model Used

Amelia (autonomous Developer agent, BMAD Method v6) running on Claude Opus 4.7.

### Debug Log References

- `_bmad-output/implementation-artifacts/tests/story-4-1-baseline-audit.md` — Task 1 evidence; schema research, per-server canonical configs, env-var handling decision, secret-pattern catalog, gitignore invariance, predecessor-harness compatibility scan, source URLs, and the underscore-aware banned-term boundary Dev decision.
- `_bmad-output/implementation-artifacts/tests/story-4-1-canonical-blueprint.md` — Task 2 evidence; exact JSON shape, README section order, per-server content, env-handling body, forward-references body, banned-term lock, secret-pattern lock, forbidden-form lock, Story 4.2 placeholder-convention lock.
- `_bmad-output/implementation-artifacts/tests/story-4-1-task-handoff.md` — Task 6 evidence; AC-to-file map, validation transcripts, SHA-256 fingerprints, Dev decisions differing from story file, zero-edit verification block.
- Full harness run (`bash story-4-1-mcp-json-validation.sh all`) emitted `PASS: task1` → `PASS: task9` → `PASS: all`; exit `0`; 10 `^PASS:` lines. Predecessor regression vector `(1 1 1 1 10 7 7 7 7 7)` matches expected.

### Completion Notes List

- **`@kenazk/gong-mcp` not on npm — pin moved to `github:kenazk/gong-mcp` (F1 review fix, 2026-04-21).** Verified via WebSearch + upstream `package.json` (name is unscoped `gong-mcp`) + registry probe (`npm view @kenazk/gong-mcp` returns E404). Original draft pinned `@kenazk/gong-mcp@latest` as a stable lock-point; Story 4.1 senior review flagged that `npx -y @kenazk/gong-mcp@latest` would fail fetch on clean hosts, so the canonical literal is now `npx -y github:kenazk/gong-mcp` — `npx`'s git-install path resolves directly from the public GitHub repo (requires the upstream `package.json` build step to succeed on install). When Gong publishes its official MCP server this pin will flip.
- **F1 codification — banned-term regex × `GITHUB_PERSONAL_ACCESS_TOKEN`.** AC7's 17-token regex contains `personal`; the GitHub canonical env var name contains `_PERSONAL_` which trips the `(^|[^A-Za-z])(...|personal)($|[^A-Za-z])` boundary guard. The story-inherited regex is preserved verbatim (Stories 3.1/3.2/3.3 compatibility). The Story 4.1 harness introduces `sanitize_for_banned_scan()` that `sed` substitutes the literal `GITHUB_PERSONAL_ACCESS_TOKEN` → `__GH_PAT_NAME__` on each file before the banned-term grep runs. `regex_self_probe` exercises both the raw positive trip and the sanitized negative pass to prove the sanitizer works. Any other `personal` / `_personal_` / `_PERSONAL_` substring remains caught. Precedent: Story 2.1 commit `0db273b` / Story 3.1 F1 / Story 3.2 AC13. No modification to `BANNED_TERMS_REGEX` required; zero predecessor-harness edit.
- **Dollar-brace `${…}` scan scope.** AC4 scopes the `${VAR}` scan to `.cursor/mcp.json`; the README legitimately documents the broken `${GITHUB_PERSONAL_ACCESS_TOKEN}` pitfall in prose. The harness applies the dollar-brace scan strictly per-file: JSON must have ZERO `${VAR}` hits; README is permitted to contain the documented pitfall examples. Placeholder-form probes (`{{…}}`, `<name>`, `%name%`) target the README exclusively (AC7 — README is prose, not a template).
- **Task-1 harness-compatibility scan finding (AC10 invariance).** Zero predecessor harnesses have deny-list patterns that reject `.cursor/mcp.json` or `.cursor/mcp.README.md`. Story 1.1 harness iterates `.cursor/rules` only, not `.cursor/` generically. No allowlist extension needed; no predecessor harness edited; Story 1.1 harness SHA-256 `a609f6a857235a57588bab081c2775c3d59c9282ae0d1256f4183b5e923617b8` matches the Story 3.3 `STORY_1_1_HARNESS_SHA256` constant.
- **Sprint tracker.** `4-1-…status: backlog → review`; `epic-4.status: backlog → in-progress`; `last_updated: 2026-04-20 → 2026-04-21`. Single-transition on-disk collapse acceptable per AC11 + Stories 2.x / 3.x autonomous-swarm precedent. No other story's status changed; every comment, blank line, ordering, and inline spacing preserved byte-for-byte apart from those three diffs.
- **AC13 resolution probes (F5 review fix, 2026-04-21).** All five active MCP references launch-verified on commit date: Linear MCP URL returns HTTP/2 401 + `www-authenticate: Bearer realm="OAuth"` (valid Cursor-compatible OAuth handshake); `ghcr.io/github/github-mcp-server` manifest resolves HTTP/2 200 (OCI image index digest `sha256:3cbaa5d2...`); `npm view @softeria/ms-365-mcp-server version` returns `0.85.0`; `npm view @salesforce/mcp version` returns `0.30.5`; `curl -sI https://github.com/kenazk/gong-mcp` returns HTTP/2 200. Full command transcript (including exit codes and headers) captured in `story-4-1-task-handoff.md` § `AC13 resolution-probe transcript`.

### File List

Files created:

- `.cursor/mcp.json`
- `.cursor/mcp.README.md`
- `_bmad-output/implementation-artifacts/tests/story-4-1-mcp-json-validation.sh` (chmod +x)
- `_bmad-output/implementation-artifacts/tests/story-4-1-baseline-audit.md`
- `_bmad-output/implementation-artifacts/tests/story-4-1-canonical-blueprint.md`
- `_bmad-output/implementation-artifacts/tests/story-4-1-task-handoff.md`

Files modified:

- `_bmad-output/implementation-artifacts/4-1-write-cursor-mcp-json-with-active-mcps.md` (this file — Status flip, Task checkboxes, Change Log + Dev Agent Record populated)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (`4-1-…status: ready-for-dev → review`)

Files NOT modified (byte-stable invariance confirmed by harness task9 regression):

- `.gitignore`, `README.md`, `LICENSE`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`
- All `.cursor/rules/*.mdc` files (5 rules + `.gitkeep`)
- `agents/personas/work.md`, `agents/personas/.gitkeep`
- `memory/me/identity.md`, `memory/me/preferences.md`, `memory/.gitkeep`
- Nine Story 3.1 `memory/**/_template*.md` files
- Seven Story 3.2 `memory/.obsidian/*.json` files
- All ten predecessor harnesses under `_bmad-output/implementation-artifacts/tests/story-[1-3]-*.sh`
