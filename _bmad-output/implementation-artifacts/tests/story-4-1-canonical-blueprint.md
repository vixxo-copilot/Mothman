# Story 4.1 Canonical Blueprint

Task 2 evidence artifact. Locks the exact shape of `.cursor/mcp.json` and `.cursor/mcp.README.md` before Tasks 3 + 4 materialize the files and before Task 5 encodes the byte-level invariants in the validation harness. Blueprint captured 2026-04-21.

## `.cursor/mcp.json` — exact shape

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

- Indentation: 2-space.
- Line endings: LF. Trailing newline required (last byte `0x0a`).
- Validates under `python3 -m json.tool` AND `node -e "JSON.parse(...)"`.
- Exactly one top-level key `mcpServers`. Exactly five server keys in canonical order.
- Zero `env` blocks. Zero `${VAR}` / `$VAR` tokens. Zero comments. Zero trailing commas.

## Blueprint — `linear`

- Shape: remote URL only.
- Literal: `"url": "https://mcp.linear.app/mcp"` — no `headers`, no `env`.
- Auth: OAuth 2.1 interactive via Cursor's MCP UI on first connect.
- Env vars required: none.

## Blueprint — `github`

- Shape: stdio local (`command: docker`).
- Literal `command`: `"docker"`.
- Literal `args` (six elements, order-locked): `["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"]`.
- Env inheritance: Docker `-e NAME` bare form — the `-e GITHUB_PERSONAL_ACCESS_TOKEN` flag (NO `=value`) instructs `docker run` to read the variable from its inherited env at spawn.
- Auth: `GITHUB_PERSONAL_ACCESS_TOKEN` exported in shell prior to launching Cursor.

## Blueprint — `microsoft-365`

- Shape: stdio local (`command: npx`).
- Literal `command`: `"npx"`.
- Literal `args` (two elements): `["-y", "@softeria/ms-365-mcp-server@latest"]`.
- Auth: device-code flow on first run; token cached in OS keychain.
- Env vars required: none (optional `MS365_MCP_CLIENT_ID` / `MS365_MCP_TENANT_ID` documented in README for multi-tenant scenarios, exported in shell, never in the JSON).

## Blueprint — `salesforce`

- Shape: stdio local (`command: npx`).
- Literal `command`: `"npx"`.
- Literal `args` (seven elements, order-locked): `["-y", "@salesforce/mcp@latest", "--orgs", "DEFAULT_TARGET_ORG", "--toolsets", "orgs,metadata,data,users"]`.
- Auth: Salesforce CLI (`sf`) session in `~/.sf/`. User runs `sf org login web` out of band.
- Env vars required: none.

## Blueprint — `gong`

- Shape: stdio local (`command: npx`).
- Literal `command`: `"npx"`.
- Literal `args` (two elements): `["-y", "github:kenazk/gong-mcp"]`.
- Auth: `GONG_ACCESS_KEY` + `GONG_ACCESS_KEY_SECRET` env vars inherited from shell.
- **Package install note:** `@kenazk/gong-mcp` is NOT published to npm (registry returns 404 — baseline-audit Task 1 finding + Story 4.1 F1 review confirmation). The JSON uses `npx`'s git-install path `github:kenazk/gong-mcp`, which installs directly from the public GitHub repo; requires the upstream `package.json` build step to succeed on install. When Gong ships its official MCP server (target April 2026 per `help.gong.io/docs/gong-mcp-server`) this pin will flip.

## `.cursor/mcp.README.md` — exact shape

### Frontmatter (lock)

```yaml
---
type: mcp-readme
scope: work
created: 2026-04-21
updated: 2026-04-21
tags: [mcp, work]
---
```

Key order locked: `type`, `scope`, `created`, `updated`, `tags`. All five keys required. Values literal as shown.

### Body section order (lock)

1. H1: `# Active MCPs (.cursor/mcp.json)`
2. One-paragraph preamble stating the file documents the five active MCPs wired in `.cursor/mcp.json`, and that placeholder / pending MCPs live in a separate Story 4.2 file (`.cursor/mcp.placeholders.md`).
3. H2 `## Linear`
4. H2 `## GitHub`
5. H2 `## Microsoft 365`
6. H2 `## Salesforce`
7. H2 `## Gong`
8. H2 `## Env Variable Handling Convention`
9. H2 `## Forward References`
10. Single-line `<!-- Why: … -->` terminator on the last non-blank line.

### Per-server H2 body template (five fields, order-locked)

- `**Purpose:**` — one sentence describing what the MCP enables in the Vixxo work context.
- `**Transport:**` — one of `remote URL (HTTP)`, `local stdio (npx)`, `local stdio (docker)`.
- `**Auth:**` — one sentence describing the auth mechanism.
- `**Required env vars:**` — bulleted list; may state "None — ..." when not applicable.
- `**Wiring link:**` — URL or wiki placeholder.

### Per-server content (lock)

- **Linear** — Purpose: `Vixxo work task and project management (issues, projects, cycles).` Transport: `remote URL (HTTP)`. Auth: `OAuth 2.1 interactive via Cursor's MCP UI`. Env vars: `None — interactive OAuth on first connect`. Wiring link: `TODO: Vixxo internal wiki — Linear MCP onboarding`.
- **GitHub** — Purpose: `Source control, code review, repository documentation, PR automation.` Transport: `local stdio (docker)`. Auth: `Environment variable: GITHUB_PERSONAL_ACCESS_TOKEN`. Env vars: one bullet for `GITHUB_PERSONAL_ACCESS_TOKEN` explaining shell export + Docker bare-name inheritance. Wiring link: `https://github.com/github/github-mcp-server`.
- **Microsoft 365** — Purpose: `Outlook email and calendar, OneDrive, Teams chat, Graph API coverage.` Transport: `local stdio (npx)`. Auth: `Device-code flow (interactive on first run); token cached in OS keychain`. Env vars: `None required — MS365_MCP_CLIENT_ID / MS365_MCP_TENANT_ID optional for multi-tenant scenarios, exported in shell if needed`. Wiring link: `https://github.com/softeria/ms-365-mcp-server`.
- **Salesforce** — Purpose: `CRM, pipeline, accounts, contacts, Apex execution, SOQL queries.` Transport: `local stdio (npx)`. Auth: `Salesforce CLI session — run \`sf org login web\` out of band`. Env vars: `None required — session file in ~/.sf/`. Wiring link: `https://github.com/salesforcecli/mcp`.
- **Gong** — Purpose: `Call recordings, transcripts, deal intelligence.` Transport: `local stdio (npx)`. Auth: `Environment variables (inherited from shell)`. Env vars: two bullets for `GONG_ACCESS_KEY` and `GONG_ACCESS_KEY_SECRET` with a shell-export instruction. Wiring link: `https://github.com/kenazk/gong-mcp` plus a "coming soon" note referencing `help.gong.io/docs/gong-mcp-server` and the npm-publish-status fallback (see Baseline Audit Task 1).

### `## Env Variable Handling Convention` body (lock)

Three patterns enumerated:

1. **Shell inheritance** — exported in `~/.zshrc` / `~/.bashrc`; flows shell → Cursor → spawned MCP subprocess.
2. **Docker `-e NAME` bare-form** — used by GitHub; the JSON holds only the flag + name, Docker reads the value from its inherited env.
3. **Interactive auth / external CLI session** — Linear OAuth 2.1, Salesforce `sf` session, Microsoft 365 device-code + keychain-cached token.

Explicit statement: Cursor's 2026 parser does NOT expand `${VAR}` in `env` blocks (Cursor forum 79296, 79639). Therefore `.cursor/mcp.json` contains ZERO `env` blocks. Any future MCP added MUST choose one of the three patterns above. macOS Finder-launched Cursor caveat: Finder-launched apps inherit `launchctl`'s env, not the shell's — use `launchctl setenv …` or launch Cursor from a terminal.

### `## Forward References` body (lock)

- Story 4.2 → `.cursor/mcp.placeholders.md` (separate markdown file; per-pending-MCP H2 sections + fenced `json` code blocks).
- Story 4.3 → `.env.example` enumerates per-MCP env vars (`GITHUB_PERSONAL_ACCESS_TOKEN`, `GONG_ACCESS_KEY`, `GONG_ACCESS_KEY_SECRET`, optional `MS365_MCP_CLIENT_ID` / `MS365_MCP_TENANT_ID`).
- Story 4.4 → `docs/mcps.md` rewrite with the broader MCP catalog; `docs/setup.md` walkthrough (clone → `bin/init` → verify).
- Epic 5 Story 5.3 → wizard calls each active MCP and reports PASS / FAIL.

### `<!-- Why: … -->` terminator (lock)

Final non-blank line of the file:

```
<!-- Why: strict JSON forbids comments; this README documents each entry in .cursor/mcp.json per Epic 4 Story 4.1 AC5. -->
```

## Story 4.2 Placeholder Convention (lock)

**Placeholders live in `.cursor/mcp.placeholders.md`, a separate markdown companion** — NOT as commented-out JSON blocks inside `.cursor/mcp.json`. Rationale:

- Strict JSON forbids `//` and `/* … */` comments; a partially-commented `.cursor/mcp.json` is invalid and Cursor silently rejects the WHOLE file (all MCPs unavailable, not just the commented one).
- Switching `.cursor/mcp.json` to JSON5 to support comments is rejected — Cursor's 2026 parser status with JSON5 is inconsistent per multiple community-forum reports; the safest invariant is strict JSON.
- `.cursor/mcp.placeholders.md` is markdown: each pending MCP gets an H2, a fenced ```` ```json ```` code block showing the intended canonical shape, and a `// TODO: wiring; see <wiki link or issue>` **markdown comment** (not inside the JSON block).
- Story 4.2 scope: eleven pending MCPs — Freshdesk, Dynamics, VixxoNow, VixxoLink, Gateway, ZoomInfo, HubSpot, AWS Connect, ChatFPT, Elastic, agent-skills Introspection MCP.
- Story 4.1 itself does NOT create `.cursor/mcp.placeholders.md`; Story 4.2 is responsible. Story 4.1 only locks the convention.

## Banned-term lock

17-token set inherited from Stories 3.1 / 3.2 / 3.3 (zero tokens added or removed). The regex itself is preserved **verbatim** from Stories 3.1 / 3.2 / 3.3 — the boundary class still rejects only non-letter characters (no underscore-aware extension):

```
(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])
```

Collision with the GitHub canonical env var `GITHUB_PERSONAL_ACCESS_TOKEN` (literal `_PERSONAL_` substring trips the `personal` token under the inherited regex) is handled in the harness by a **sanitize-before-scan** pre-filter: `sanitize_for_banned_scan()` runs `sed -E "s/GITHUB_PERSONAL_ACCESS_TOKEN/__GH_PAT_NAME__/g"` on the target file's contents before piping through `grep -iE "${BANNED_TERMS_REGEX}"`. This replaces the one legitimate `_PERSONAL_` collision with a neutral token while leaving every other `personal` / `PERSONAL_…` substring visible to the grep. The regex is untouched; the catch-surface is preserved (`personal note` still matches; `personally` still rejects; `PERSONAL_HOBBY_TOKEN` still trips).

Applied case-insensitively (`grep -iE`) across the sanitized views of both `.cursor/mcp.json` and `.cursor/mcp.README.md`. Zero matches expected on the sanitized output. `regex_self_probe` exercises the raw positive trip (`GITHUB_PERSONAL_ACCESS_TOKEN` un-sanitized DOES match the regex) and the sanitized negative pass (after `sed`, it does NOT) to prove the sanitizer behaves as intended.

Twelve Derek-specific fixed-string probes (defence-in-depth; `grep -Fi`): `Chiron`, `MasteryLab`, `Agile Weekly`, `Queen Creek`, `Gangplank`, `Bodybuilding.com`, `Integrum`, `Omarchy`, `derekneighbors.com`, `Playrix`, `Laurie`, `Deke`. Zero matches expected.

Additional path-reference fixed-string probes: `/Users/`, `Public/gtd-life`, `@gmail.com` — zero matches expected in either file.

## Secret-pattern catalog lock

Eleven regex patterns (POSIX ERE, case-sensitive); zero matches expected against either file:

1. `sk-[A-Za-z0-9_-]{20,}`
2. `ghp_[A-Za-z0-9]{20,}`
3. `gho_[A-Za-z0-9]{20,}`
4. `ghs_[A-Za-z0-9]{20,}`
5. `github_pat_[A-Za-z0-9_]{20,}`
6. `xox[baprs]-[A-Za-z0-9-]{10,}`
7. `eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}`
8. `Bearer [A-Za-z0-9_.-]{20,}`
9. `AKIA[0-9A-Z]{16}`
10. `AIza[A-Za-z0-9_-]{35}`
11. `[A-Fa-f0-9]{32,}`

Plus `password=`, `token=`, `secret=`, `api_key=` literal-substring scans. Plus the `${VAR}` / `$VAR` shell-expansion-token scan. Plus the `env`-block-absence assertion (via `python3 -c` iteration over `mcpServers.values()`).

## Forbidden-form lock (README placeholder discipline)

`.cursor/mcp.README.md` is descriptive prose — not a template. It must contain ZERO placeholder tokens in any of these forms:

- `{{name}}` (double-brace) — reserved for Story 3.3 `memory/me/identity.md` only.
- `{name}` (single-brace) — reserved for code.
- `<name>` (angle-bracket) — reserved for URL placeholders and HTML tags (the HTML-comment `<!-- Why: … -->` terminator is exempt by being a full comment, not a bare `<name>` form).
- `%name%` (percent-wrapped) — reserved for Windows env vars.
- `${name}` (dollar-brace) — banned from `.cursor/mcp.json` entirely and from this README.

Caveat for the angle-bracket probe: the HTML-comment terminator and URL formats like `<https://…>` are legitimate content. The harness implements angle-bracket probe as the specific form `<[A-Za-z_][A-Za-z0-9_]*>` — this matches `<name>` but NOT `<!-- … -->` (starts with `<!`) nor `<https://…>` (starts with `<h` followed by `:` disrupting the identifier match). The probe is conservative and will not flag the README's legitimate HTML-comment terminator.

## Evidence constants fed into Task 5 harness

- `EXPECTED_SERVER_KEYS=( linear github microsoft-365 salesforce gong )` — five keys, canonical order.
- `DENY_LIST_SERVER_KEYS=( freshdesk dynamics vixxonow vixxolink gateway zoominfo hubspot aws-connect chatfpt elastic introspection agent-skills slack notion gmail google-calendar obsidian linkedin )` — eighteen keys.
- `EXPECTED_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 )` — empirical, Story 1.1 → Story 3.3.
- Story 1.1 harness fingerprint — bytes `6215`, SHA-256 `a609f6a857235a57588bab081c2775c3d59c9282ae0d1256f4183b5e923617b8`.
- `.gitignore` fingerprint — SHA-256 `49fa451f69ff42a866880d8c962f9239b7d651b374f9a0fd91dda3ce3556cae1`.

<!-- Why: Task 2 evidence artifact. Locks the byte-level shape of .cursor/mcp.json and .cursor/mcp.README.md so Tasks 3, 4, and 5 have a single source of truth to build and assert against. -->
