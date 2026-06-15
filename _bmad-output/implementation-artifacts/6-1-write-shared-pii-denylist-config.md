# Story 6.1: Write shared PII deny-list config

Status: done

## Story

As the template maintainer for `assistants-template` (and by extension for the companion `agent-skills` repository, which mirrors the same deny-list),
I want a single, publishable, human-editable source of truth for the banned personal patterns that must never appear in shipped template content,
so that Story 6.2's GitHub Action can consume it in CI, the Stories 1.x / 2.x / 3.x validation harnesses align against the same banned-term vocabulary, and every downstream consumer fork (every Vixxo employee clone and the mirrored `agent-skills` repo) enforces an identical first-line-of-defence policy against Derek's personal PII — names, home address, family members, RevivaGo / other personal businesses, blog content, and personal-life scope words — leaking back into the shipped template via PRs.

## Acceptance Criteria

1. **AC1 — `.github/pii-denylist.txt` exists at the canonical path and is committed to git**
   - Given a fresh clone of `assistants-template` after Story 6.1 lands
   - When `.github/pii-denylist.txt` is inspected
   - Then the file exists at the repository root path `.github/pii-denylist.txt` (directory `.github/` and file `pii-denylist.txt`; lowercase; exact spelling per Epic 6 Story 6.1 AC)
   - And the file is tracked by git (`git ls-files .github/pii-denylist.txt` returns the path, exit `0`)
   - And the file is non-empty (`wc -c < .github/pii-denylist.txt` returns a non-zero integer)
   - And the file uses UTF-8 encoding with LF line endings only (`grep -c $'\r' .github/pii-denylist.txt` returns `0`)
   - And the file ends with a single trailing newline (last byte `0x0a` — `tail -c 1 .github/pii-denylist.txt | od -An -tx1 | tr -d ' \n'` equals `0a`)
   - And the `.github/` directory may contain other files (e.g. a future Story 6.2 workflow under `.github/workflows/`), but Story 6.1 itself creates ONLY `.github/pii-denylist.txt` (plus a `.gitkeep`-equivalent is NOT needed since the deny-list file itself makes the directory trackable)

2. **AC2 — File-format contract is explicit, grep-compatible, and consumer-fork-extensible**
   - Given `.github/pii-denylist.txt`
   - When its content is parsed line by line
   - Then every physical line is one of: (a) a comment line that starts with `#` in column 1, (b) a blank line (zero bytes before the newline), or (c) a pattern line — a single non-empty token with no leading or trailing whitespace
   - And no line contains a literal tab character (`\t`), no line ends with trailing spaces, and no line is longer than 200 bytes
   - And pattern lines are treated as **literal substrings** for the purposes of Story 6.1 (the CI scan in Story 6.2 will wrap each pattern in its own POSIX-ERE boundary-guard regex; Story 6.1's file does NOT pre-escape regex metacharacters — keep it human-readable)
   - And category section headers MUST use the exact format `# === CATEGORY: <name> ===` on a single comment line so that `grep -E '^# === CATEGORY: ' .github/pii-denylist.txt` enumerates every section (machine-discoverable), and the category-header comment line is followed by an optional single-line description comment (`# <prose>`) and then the pattern lines for that category, terminated by a single blank line before the next section header
   - And the file opens with a header comment block (contiguous `#` lines at the top, before the first blank line) that states: purpose, CI consumption contract, how to extend, the mirror relationship with `agent-skills`, and the sensitivity-policy reminder (no raw home addresses or minor children's names in this file — those must live in per-fork-local overrides, never in the shipped template deny-list)

3. **AC3 — Required category sections exist, in canonical order, covering every Epic 6 AC facet**
   - Given the set of `# === CATEGORY: <name> ===` headers in the file
   - When the canonical ordering is verified
   - Then the file contains exactly these six category sections in this order: `Names`, `Home Address`, `Family`, `Businesses`, `Blog & Public Content`, `Personal Scope Words`
   - And the `Names` section enumerates at minimum these literal tokens (case preserved as shown; CI matching is case-insensitive): `Derek`, `Neighbors`, `Deke`, `Laurie`, `Bobby` (the carried-forward-public-tokens set that has appeared in every prior story harness's banned-term lock — these are the PUBLIC-SAFE name tokens; no additional real first/last names are introduced by Story 6.1)
   - And the `Home Address` section contains ZERO literal street addresses, ZERO literal city/state/zip tokens, and ZERO real postal data — instead it contains category MARKER COMMENTS enumerating the expected sub-categories (`# marker: street address (number + street name)`, `# marker: city`, `# marker: state or state abbreviation`, `# marker: zip code`, `# marker: apartment / suite / unit number`) plus a single sentinel pattern line `DEREK_HOME_ADDRESS_FORK_LOCAL` whose purpose is to document in-file that consumer forks add their real tokens below this sentinel (the sentinel itself is a fork-customization anchor, not a token to match real content)
   - And the `Family` section contains ZERO real family first-names (spouse first name `Laurie` is listed instead under `Names` as a public-precedent token; no kids / minors' names appear anywhere in the file) — the section uses the same marker-comment + sentinel pattern as Home Address: `# marker: spouse first name (non-public)`, `# marker: child first names (MUST NOT be committed; fork-local only)`, plus sentinel `DEREK_FAMILY_FORK_LOCAL`
   - And the `Businesses` section enumerates the Derek-associated business / product tokens that are publicly-known and safe-to-publish: `RevivaGo`, `MasteryLab`, `Agile Weekly`, `Gangplank`, `Integrum`, `Flowtopic`, `Benji`, `Chiron`, `Playrix`, `Omarchy`, `Bodybuilding.com` (eleven tokens, matching the Story-3.3 Derek-specific fixed-string scrub set plus Story 3.2 / 3.3 businesses already referenced in shipped story files)
   - And the `Blog & Public Content` section enumerates the public blog + source-repo tokens: `derekneighbors.com`, `gtd-life`, `gtdlife`, `Queen Creek` (the only public-location token retained from Story-3.3's list; kept because it appears in the public blog and is not a private residence indicator)
   - And the `Personal Scope Words` section enumerates the generic English words that mark personal-life scope and must be boundary-matched by CI: `family`, `home`, `wife`, `son`, `daughter`, `dog`, `blog`, `personal`, `wyoming`, `cheyenne` (ten tokens — exactly the Story-3.x 17-token lock minus the seven that live in `Names` / `Businesses` / `Blog & Public Content` sections above, preserving the 17-token union)

4. **AC4 — 17-token Story-3.x banned-term lock is preserved as a UNION across the sections**
   - Given the Stories 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2 / 3.3 canonical 17-token banned-term lock (`derek`, `neighbors`, `revivago`, `benji`, `flowtopic`, `gtd-life`, `gtdlife`, `wyoming`, `cheyenne`, `family`, `home`, `blog`, `wife`, `son`, `daughter`, `dog`, `personal`)
   - When the union of pattern lines from `.github/pii-denylist.txt` is taken (case-folded, whitespace-trimmed, comments and blanks excluded)
   - Then every one of the 17 tokens appears at least once in the file (exact token spelling; case-folded comparison — e.g. `Derek` in `Names` satisfies `derek`, `RevivaGo` in `Businesses` satisfies `revivago`, `gtd-life` in `Blog & Public Content` satisfies `gtd-life`)
   - And the file also contains at minimum the seven Story-3.3 Derek-specific fixed-string scrub tokens: `Chiron`, `MasteryLab`, `Agile Weekly`, `Gangplank`, `Integrum`, `Omarchy`, `Playrix` (distributed across `Businesses`) plus `derekneighbors.com`, `Queen Creek` (in `Blog & Public Content`) plus `Deke`, `Laurie`, `Bobby` (in `Names`) — these twelve defense-in-depth tokens extend the 17-token regex set to a total denied vocabulary of at least 29 distinct tokens (17 ∪ 12) visible in the file

5. **AC5 — File contains ZERO sensitive personal data (safe to publish in open-source template)**
   - Given the committed `.github/pii-denylist.txt`
   - When the file is scanned for content that would itself leak PII
   - Then the file contains ZERO real home street addresses (no number-space-word-space-(`St`|`Ave`|`Rd`|`Blvd`|`Ln`|`Way`|`Dr`) pattern; verify via `grep -E '^[0-9]+ [A-Za-z]+ (St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Ln|Lane|Way|Dr|Drive|Ct|Court|Pl|Place)$'` returns zero matches)
   - And contains ZERO five-digit US zip codes (verify via `grep -E '^[0-9]{5}(-[0-9]{4})?$' ` returns zero matches on pattern lines)
   - And contains ZERO minor children's first names (no tokens matching the Derek-kids-first-name set known to the SM — this is enforced by the positive allowlist of AC3 `Names` rather than a negative scan since the kids' names are deliberately not written down in this file)
   - And contains ZERO raw phone numbers (`grep -E '\+?[0-9]{3}[-. ][0-9]{3}[-. ][0-9]{4}'` returns zero matches)
   - And contains ZERO email addresses containing a real human name (`grep -E '@[a-z0-9.-]+\.[a-z]{2,}'` returns zero matches — the only dotted-domain tokens allowed are the explicit public blog / business domains `derekneighbors.com` and `Bodybuilding.com`, both already on the public internet; no `@` character appears anywhere in the file)
   - And contains the explicit in-file self-documenting sentence `# SAFE-TO-PUBLISH deny-list` inside the header comment block so that both auditors and future BMAD agents can quickly confirm the "no raw PII in this file" policy via `grep -Fq '# SAFE-TO-PUBLISH deny-list' .github/pii-denylist.txt`

6. **AC6 — Header comment block explicitly documents: purpose, CI contract, extensibility, and mirror relationship**
   - Given the header comment block at the top of `.github/pii-denylist.txt` (contiguous `#` lines before the first non-`#` line)
   - When the block is read
   - Then the header contains at minimum these labeled sections on their own comment lines (case preserved exactly): `# Purpose:`, `# CI contract:`, `# How to extend:`, `# Mirror:`, `# Safe-to-publish policy:`
   - And the `# Purpose:` section states the single-source-of-truth intent (one line: "This file is the single source of truth for banned personal patterns. Do not duplicate.")
   - And the `# CI contract:` section states that (a) each pattern line is a literal substring, (b) CI in Story 6.2 wraps each pattern in a POSIX-ERE boundary guard `(^|[^A-Za-z])TOKEN($|[^A-Za-z])` at scan time, (c) CI matching is case-insensitive (`grep -iE`), (d) comment lines (`^#`) and blank lines are ignored during pattern loading, (e) `.github/pii-denylist.txt` itself is excluded from the scan (the deny-list MUST NOT match itself)
   - And the `# How to extend:` section states the canonical extension procedure: add the token under the correct `# === CATEGORY: <name> ===` section in alphabetical order within the category, in a PR that opens against `main`, with a one-line commit justification; any NEW category requires bumping AC3 in a future story
   - And the `# Mirror:` section states that this file is mirrored in the companion `agent-skills` repository at the same path (`.github/pii-denylist.txt`), and that drift between the two repos is a policy violation — but the mirror synchronization is a separate, out-of-scope operational concern for the `agent-skills` maintainers (Story 6.1 does NOT attempt to edit, clone, or otherwise touch the companion repo; it only declares the mirror contract in the header)
   - And the `# Safe-to-publish policy:` section states the reasoning behind the category-marker approach for `Home Address` / `Family` (see AC3) — raw home addresses and minor-family-member names would themselves be PII if committed, so the shipped deny-list uses category markers + sentinels, and consumer forks are expected to add their fork-local real tokens via git-ignored overrides or private-fork maintenance

7. **AC7 — Deterministic validation harness exists and is wired into the harness family**
   - Given the existing harness family under `_bmad-output/implementation-artifacts/tests/`
   - When Story 6.1 lands
   - Then a new harness exists at `_bmad-output/implementation-artifacts/tests/story-6-1-pii-denylist-validation.sh`, is marked executable (mode `0755`), uses `#!/usr/bin/env bash` on line 1 and `set -euo pipefail` on line 2
   - And the harness implements gates `task1` (baseline-audit evidence present and structured — `story-6-1-baseline-audit.md`), `task2` (canonical-blueprint evidence present and structured — `story-6-1-canonical-blueprint.md`), `task3` (deny-list file shape — existence, non-empty, LF-only, trailing newline, line-length ≤ 200 bytes, no tabs, no trailing spaces, header comment block present with all five labeled sections per AC6, safe-to-publish sentinel comment present per AC5, six category headers present in canonical order per AC3, every AC4 union token present), `task4` (content-scrub gate — AC5 negative scans: zero street-address patterns, zero five-digit zips, zero phone numbers, zero `@` characters, plus the positive-coverage check that every one of the 17 Story-3.x canonical tokens resolves to at least one pattern line via case-folded match), `task5` (self-check: shebang, `set -euo pipefail`, all case arms, all declared constants, helper function presence via `declare -F`), `task6` (regression: invokes the ten prior harnesses — Stories 1.1 / 1.2 / 1.3 / 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2 / 3.3 — in `all` mode and asserts each exits zero with the expected per-harness `^PASS:` line-count fingerprint), plus an `all` dispatcher
   - And the harness exits `0` with `PASS: all` on success; exits `1` and emits `FAIL: <gate>: <reason>` on stderr on failure — matching the Stories 2.1–3.3 harness contract
   - And the harness is BSD-grep and GNU-grep compatible, POSIX-bash-3.2 compatible, and uses only `bash`, `grep`, `find`, `awk`, `sed`, `wc`, `head`, `tail`, `tr`, `sort`, `cut`, `od`, and shell built-ins (no `rg`, no `jq`, no `yq`, no Python, no Node)
   - And when invoked in `all` mode, the harness emits exactly 7 lines matching `^PASS:` on stdout (`PASS: task1` → `PASS: task6` → `PASS: all`) — fingerprint compatible with the Stories 3.1 / 3.2 / 3.3 pass-count convention

8. **AC8 — Regression runs all ten predecessor harnesses cleanly (extends Story 3.3's nine-harness chain by one)**
   - Given all prior harnesses in `_bmad-output/implementation-artifacts/tests/` (Stories 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3 — ten predecessors)
   - When the Story 6.1 regression gate (`task6`) runs
   - Then `bash story-1-1-scaffold-validation.sh all`, `bash story-1-2-root-files-validation.sh all`, `bash story-1-3-root-context-validation.sh all`, `bash story-2-1-agent-identity-validation.sh all`, `bash story-2-2-guardrail-and-formatting-validation.sh all`, `bash story-2-3-work-persona-validation.sh all`, `bash story-2-4-benji-inbox-absence-validation.sh all`, `bash story-3-1-memory-template-tree-validation.sh all`, `bash story-3-2-obsidian-config-validation.sh all`, and `bash story-3-3-identity-preferences-validation.sh all` each exit `0` with `PASS: all`
   - And the per-harness `^PASS:` line-count fingerprint is `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7 / 7` respectively (measurement captured 2026-04-20 — Dev MUST re-measure at Task-1 baseline-audit time and codify the exact fingerprint; the harness fails if any sub-harness emits a different count)
   - And zero bytes are changed in any of those ten prior harnesses during Story 6.1 execution (Story 6.1 is PURE ADDITION to the test tree — no predecessor-harness line-155 allowlist extension needed because `.github/` is already a legitimate top-level directory and is not covered by the `memory/` subdir allowlist)
   - And zero bytes are changed in `.cursor/rules/agent-identity.mdc`, the four Story 2.2 rule files, `agents/personas/work.md`, the root context files (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`), `README.md`, `LICENSE`, `.gitignore`, `memory/.gitkeep`, any of the nine Story 3.1 template files under `memory/`, any of the seven Story 3.2 `.obsidian/` JSON files, or `memory/me/identity.md` / `memory/me/preferences.md` — Story 6.1 is additive only (`.github/pii-denylist.txt` + harness + evidence artifacts + docs + README one-line insert + sprint-status flip + this story file)

9. **AC9 — `docs/pii-denylist.md` documents the file for human consumers**
   - Given the documentation tree under `docs/`
   - When Story 6.1 lands
   - Then a new file exists at `docs/pii-denylist.md`, UTF-8, LF line endings, trailing newline, non-empty
   - And the doc contains at minimum these H2 sections in order: `## Purpose`, `## File location and format`, `## Categories`, `## CI consumption (Story 6.2 preview)`, `## How to extend`, `## Relationship to the mirrored `agent-skills` repo`, `## What does NOT belong in this file`
   - And `## File location and format` restates the AC2 format contract (comments `#`, blanks allowed, one literal substring per pattern line, category headers `# === CATEGORY: <name> ===`)
   - And `## Categories` enumerates all six AC3 categories with a one-line description per category
   - And `## What does NOT belong in this file` restates AC5's safe-to-publish policy — no raw addresses, no zip codes, no minor children's names, no phone numbers, no `@`-containing email addresses, no secrets/credentials (secrets belong in `.gitignore` + `.env.example`, not here)
   - And the doc contains ZERO real PII by the same bar as AC5 applied to the deny-list file itself

10. **AC10 — `README.md` references the PII guardrail with a one-line mention**
    - Given the root `README.md`
    - When Story 6.1 lands
    - Then `README.md` contains a one-line addition under the existing `## Help` section (or a new `## Guardrails` section if the Dev deems it cleaner) that points to `.github/pii-denylist.txt` and `docs/pii-denylist.md` — the line format is Dev's choice but must mention BOTH paths (e.g. "PII guardrail: see `.github/pii-denylist.txt` (deny-list file) and `docs/pii-denylist.md` (policy doc). Enforced in CI by Story 6.2's workflow.")
    - And the existing README content is otherwise byte-stable — no reorganization, no rewrite of `## Quickstart`, `## Prerequisites`, or the existing bootstrap instructions
    - And the total README line count does not decrease (readme grows by 1–5 lines, never shrinks)

11. **AC11 — Sprint tracker lifecycle reflects the story transition and epic-6 flips to `in-progress`**
    - Given `_bmad-output/implementation-artifacts/sprint-status.yaml`
    - When Story 6.1 opens at Phase 1 (SM pass) and later transitions at Phase 2 (Dev handoff) and Phase 3 (review approval)
    - Then `6-1-write-shared-pii-denylist-config.status` is updated `backlog → ready-for-dev` at Phase 1, `ready-for-dev → review` at Phase 2, and `review → done` at Phase 3 (the autonomous-swarm lifecycle may collapse interim states per Stories 2.1–3.3 precedent)
    - And `epic-6.status` is updated `backlog → in-progress` at Phase 1 (Story 6.1 is the FIRST Epic 6 story — this is the epic-opening flip)
    - And `epic-6.status` remains `in-progress` through Story 6.1's entire lifecycle (Story 6.2 must also reach `done` before `epic-6.status` flips to `done`)
    - And `last_updated` is set to `2026-04-21` on the Phase 1 edit
    - And no other story's status is regressed; every comment, blank line, inline spacing, and entry ordering in `sprint-status.yaml` is preserved byte-for-byte (the only diffs are the two `status:` value changes — `6-1-…status` and `epic-6.status` — and the `last_updated` value change)

## Tasks / Subtasks

- [x] Task 1 — Baseline audit: enumerate every banned token from the existing harness family + public-safe subset determination (AC: 3, 4, 5) **[Parallelizable with Task 2]**
  - [ ] Read each of the ten predecessor harnesses at `_bmad-output/implementation-artifacts/tests/story-*-validation.sh` and extract every token contained in their banned-term regex sets and fixed-string scrub arrays. Record per-token provenance: which harness introduced the token, the section it appears in (regex vs fixed-string), and the original story file ID.
  - [ ] Compute the union set across all ten harnesses. Deduplicate by case-folded token. Expected cardinality: at least 29 tokens (17 Story-3.x regex tokens ∪ 12 Story-3.3 fixed-string defense-in-depth tokens). Actual cardinality may differ — Dev records the exact number.
  - [ ] Classify each token in the union into one of the six canonical Story 6.1 categories (`Names`, `Home Address`, `Family`, `Businesses`, `Blog & Public Content`, `Personal Scope Words`). Apply the safe-to-publish bar at this step: a token is safe to include verbatim iff it is (a) already publicly associated with Derek via the internet (business names, blog domain, public-internet residue of prior roles), or (b) a generic English word that only becomes PII-adjacent when boundary-matched (`family`, `home`, `wife`, etc. — clearly not a real PII string on its own). Tokens that would leak sensitive data (real home street, minor children's names, private phone numbers) are REJECTED at classification time and flagged in the audit as "fork-local-only — represented by category marker in the shipped file".
  - [ ] Document the twelve Story-3.3 Derek-specific fixed-string tokens by category:
    - `Names`: `Deke`, `Laurie` (note: `Laurie` is Derek's spouse's first name; documented in Story 3.3 as a fixed-string scrub token. It IS on public record via Derek's blog byline, so it is safe-to-publish in the deny-list file. Story 6.1 follows Story 3.3's precedent and does NOT treat `Laurie` as minor-PII.)
    - `Businesses`: `Chiron`, `MasteryLab`, `Agile Weekly`, `Gangplank`, `Integrum`, `Omarchy`, `Playrix`, `Bodybuilding.com`
    - `Blog & Public Content`: `derekneighbors.com`, `Queen Creek`
    - Pickup `Bobby` from Story 3.2 harness residue scrub (not in Story 3.3 list but present in Story 3.2 workspace.json exclusion commentary) into `Names`.
  - [ ] Confirm there are NO raw home-address strings, NO zip codes, NO minor children's names, NO phone numbers, NO `@`-emails anywhere in the harness codebase. If any such content is found in a predecessor harness, FLAG IT in the audit as a pre-existing PII leak requiring a separate remediation story — Story 6.1's scope is to CREATE the deny-list, not to scrub the harnesses retroactively.
  - [ ] Persist findings at `_bmad-output/implementation-artifacts/tests/story-6-1-baseline-audit.md` with sections: `# Story 6.1 Baseline Audit`, `## Per-harness token inventory`, `## Union-set (deduplicated, case-folded)`, `## Token → category classification`, `## Safe-to-publish vs fork-local-only partition`, `## Pre-existing leak flags (if any)`, `## Measured `^PASS:` line-count fingerprint (ten predecessors)`.

- [x] Task 2 — Canonical blueprint for the deny-list file + doc + harness (AC: 2, 3, 4, 5, 6) **[Parallelizable with Task 1]**
  - [ ] Author `_bmad-output/implementation-artifacts/tests/story-6-1-canonical-blueprint.md` modeled on `story-3-3-canonical-blueprint.md`. Include sections: `# Story 6.1 Canonical Blueprint`, `## Deny-list file shape`, `## Header comment block (exact labeled sections)`, `## Category section format and ordering`, `## Per-category token inventory`, `## Safe-to-publish policy restatement`, `## CI consumption contract (forward reference to Story 6.2)`, `## Negative-scan patterns (AC5 content-scrub probes)`, `## Doc file shape (`docs/pii-denylist.md` H2 sections)`.
  - [ ] Specify the EXACT header comment block template (five labeled sections per AC6) with placeholder language the Dev will finalize in Task 3:
    ```
    # Purpose: This file is the single source of truth for banned personal patterns. Do not duplicate.
    # CI contract: Each line is a literal substring. Story 6.2's workflow wraps each pattern in a POSIX-ERE boundary-guard regex (^|[^A-Za-z])TOKEN($|[^A-Za-z]) at scan time, case-insensitive. Blank lines and lines starting with `#` are ignored. This file itself is excluded from the scan.
    # How to extend: Add the new token in alphabetical order under the correct `# === CATEGORY: <name> ===` section, in a PR against main, with a one-line commit message explaining why the token belongs on the list.
    # Mirror: This file is mirrored in the companion `agent-skills` repository at the same path (.github/pii-denylist.txt). Drift between the two repos is a policy violation; synchronization is an operational concern for the `agent-skills` maintainers and is out of scope for this repository's CI.
    # Safe-to-publish policy: This shipped deny-list contains ZERO raw home addresses, ZERO zip codes, ZERO minor children's names, and ZERO phone numbers. Home-address and family-minor categories use marker comments + fork-local sentinels so that consumer forks can add their real tokens locally without committing PII to the public template.
    # SAFE-TO-PUBLISH deny-list
    ```
  - [ ] Specify the EXACT category section template per AC3:
    ```
    # === CATEGORY: Names ===
    # Public-safe name tokens associated with the current template maintainer.
    Derek
    Neighbors
    Deke
    Laurie
    Bobby

    # === CATEGORY: Home Address ===
    # marker: street address (number + street name)
    # marker: city
    # marker: state or state abbreviation
    # marker: zip code
    # marker: apartment / suite / unit number
    # Fork-local customization: replace the sentinel below with real tokens in a private fork.
    DEREK_HOME_ADDRESS_FORK_LOCAL

    # === CATEGORY: Family ===
    # marker: spouse first name (non-public)
    # marker: child first names (MUST NOT be committed; fork-local only)
    # Fork-local customization: replace the sentinel below with real tokens in a private fork.
    DEREK_FAMILY_FORK_LOCAL

    # === CATEGORY: Businesses ===
    # Publicly-known business / product tokens associated with the template maintainer.
    Agile Weekly
    Benji
    Bodybuilding.com
    Chiron
    Flowtopic
    Gangplank
    Integrum
    MasteryLab
    Omarchy
    Playrix
    RevivaGo

    # === CATEGORY: Blog & Public Content ===
    # Public blog domain, source-repo, and notable public-content tokens.
    derekneighbors.com
    gtd-life
    gtdlife
    Queen Creek

    # === CATEGORY: Personal Scope Words ===
    # Generic English words that mark personal-life scope. CI word-boundary enforcement
    # prevents false positives on unrelated compounds (e.g. "homepage" won't match `home`).
    blog
    cheyenne
    daughter
    dog
    family
    home
    personal
    son
    wife
    wyoming
    ```
  - [ ] Document the `docs/pii-denylist.md` blueprint: H2 sections per AC9, with one-paragraph description per section and a cross-reference to `.github/pii-denylist.txt` wherever appropriate.
  - [ ] Document the AC5 negative-scan regex probes verbatim for use in the Task-4 harness `check_task4`:
    - Street: `grep -Eq '^[0-9]+ [A-Za-z]+ (St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Ln|Lane|Way|Dr|Drive|Ct|Court|Pl|Place)$'` → zero matches on pattern lines
    - Zip: `grep -Eq '^[0-9]{5}(-[0-9]{4})?$'` → zero
    - Phone: `grep -Eq '\+?[0-9]{3}[-. ][0-9]{3}[-. ][0-9]{4}'` → zero
    - `@` email: `grep -Fq '@' .github/pii-denylist.txt` → zero
  - [ ] Lock the canonical 17-token assertion set for `check_task3` / `check_task4` coverage: `derek, neighbors, revivago, benji, flowtopic, gtd-life, gtdlife, wyoming, cheyenne, family, home, blog, wife, son, daughter, dog, personal` — case-folded membership assertion against the union of non-comment, non-blank pattern lines.

- [x] Task 3 — Author `.github/pii-denylist.txt` (AC: 1, 2, 3, 4, 5, 6) **[Sequential — depends on Task 2 blueprint]**
  - [ ] Create the `.github/` directory (`mkdir -p .github`). The directory has NOT previously been created in this repo (confirmed via `ls .github` returning "No such file or directory" at baseline-audit time).
  - [ ] Author `.github/pii-denylist.txt` per the Task-2 blueprint. Emit the header comment block exactly as specified (five labeled sections plus the `# SAFE-TO-PUBLISH deny-list` sentinel), then emit each of the six category sections in canonical order with the exact token lists from the blueprint (tokens alphabetized within each category where shown in the blueprint).
  - [ ] End the file with a single trailing newline. Use LF line endings only. No tabs. No trailing spaces. Every pattern line is ≤ 200 bytes.
  - [ ] Manual verification before moving on: `head -n 15 .github/pii-denylist.txt` shows the header block; `grep -c '^# === CATEGORY: ' .github/pii-denylist.txt` returns `6`; `grep -Fq '# SAFE-TO-PUBLISH deny-list' .github/pii-denylist.txt`; `grep -Fq 'RevivaGo' .github/pii-denylist.txt`; `grep -Fq 'gtd-life' .github/pii-denylist.txt`; `tail -c 1 .github/pii-denylist.txt | od -An -tx1 | tr -d ' \n'` equals `0a`; `grep -c $'\r' .github/pii-denylist.txt` returns `0`; `grep -Fq '@' .github/pii-denylist.txt` returns exit `1` (no match).

- [x] Task 4 — Author the deterministic validation harness (AC: 7, 8) **[Sequential — depends on Task 3 deny-list existing]**
  - [ ] Create `_bmad-output/implementation-artifacts/tests/story-6-1-pii-denylist-validation.sh`, `chmod +x` to 0755. Shebang `#!/usr/bin/env bash`, `set -euo pipefail`. Model on `story-3-3-identity-preferences-validation.sh`.
  - [ ] Declare constants at the top:
    - Standard boilerplate: `PROJECT_ROOT`, `TESTS_DIR`, `SELF_PATH`.
    - `DENYLIST_PATH="${PROJECT_ROOT}/.github/pii-denylist.txt"`
    - `DOC_PATH="${PROJECT_ROOT}/docs/pii-denylist.md"`
    - `README_PATH="${PROJECT_ROOT}/README.md"`
    - `BASELINE_AUDIT_PATH="${TESTS_DIR}/story-6-1-baseline-audit.md"`
    - `BLUEPRINT_PATH="${TESTS_DIR}/story-6-1-canonical-blueprint.md"`
    - Ten prior-harness paths: `STORY_1_1_HARNESS` through `STORY_3_3_HARNESS`.
    - `CANONICAL_17_TOKENS=( derek neighbors revivago benji flowtopic gtd-life gtdlife wyoming cheyenne family home blog wife son daughter dog personal )` — case-folded.
    - `EXPECTED_CATEGORIES=( Names 'Home Address' Family Businesses 'Blog & Public Content' 'Personal Scope Words' )` — exactly six in canonical order.
    - `HEADER_LABELS=( '# Purpose:' '# CI contract:' '# How to extend:' '# Mirror:' '# Safe-to-publish policy:' )` — five labels.
    - `SAFE_PUBLISH_SENTINEL='# SAFE-TO-PUBLISH deny-list'`
    - `REGRESSION_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 )` — per-harness expected `^PASS:` line counts in order (Dev MUST verify these at Task-1 baseline-audit time and update if measured values differ).
    - `MAX_LINE_BYTES=200`
  - [ ] Implement `regex_self_probe()` that exercises:
    - Street-address negative pattern against a synthetic positive input (`123 Main St` matches; `# street marker` does NOT match) — assert regex works.
    - Zip negative pattern (`85298` matches `^[0-9]{5}$`; `Derek` does not).
    - Canonical-token case-folded membership: `DEREK` (uppercase) resolves to `derek` in `CANONICAL_17_TOKENS` after case-fold.
    - Fail-fast `fail` on mismatch.
  - [ ] `check_task1` — require `BASELINE_AUDIT_PATH` exists, contains title `# Story 6.1 Baseline Audit`, and contains each required H2/H3 section header per Task 1 spec.
  - [ ] `check_task2` — require `BLUEPRINT_PATH` exists, contains title `# Story 6.1 Canonical Blueprint`, contains all required H2 sections per Task 2 spec (including the verbatim header block template and the six category-section templates).
  - [ ] `check_task3` — deny-list file shape:
    - `[[ -f "${DENYLIST_PATH}" ]]`, `[[ -s "${DENYLIST_PATH}" ]]`, trailing-newline byte `0a`, `grep -c $'\r' = 0`, `awk 'length > 200' | wc -l = 0`, `grep -P '\t' = 0` (or fallback `grep -c $'\t'`), no trailing-space lines (`grep -nE ' $' = 0`).
    - Header comment block: iterate `HEADER_LABELS`, assert each label appears on its own line via `grep -Fxq` or `grep -Fq` depending on exact-match strategy.
    - `SAFE_PUBLISH_SENTINEL` present.
    - Category headers: `grep -c '^# === CATEGORY: ' .github/pii-denylist.txt = 6`; iterate `EXPECTED_CATEGORIES` and assert each appears in `# === CATEGORY: <name> ===` form via `grep -Fq`.
    - Category order: use `awk` to walk the file, record the sequence of category names encountered, and assert the sequence equals the `EXPECTED_CATEGORIES` order verbatim.
    - Per-category required tokens (from the AC3 + Task-2 blueprint): iterate a category → token-list mapping and assert `grep -Fq <token>` for each required token within its category section (bounded by awk line-walk between the category header and the next blank line or category header).
    - `README_PATH` references the deny-list path and doc path (AC10 satisfaction): `grep -Fq '.github/pii-denylist.txt' "${README_PATH}"` AND `grep -Fq 'docs/pii-denylist.md' "${README_PATH}"`.
    - `DOC_PATH` exists with all seven H2 sections per AC9.
  - [ ] `check_task4` — content scrub (AC5):
    - Build a stripped pattern-lines stream (`grep -vE '^(#|$)' "${DENYLIST_PATH}"`). Run each AC5 negative-scan probe against this stripped stream: street, zip, phone, `@` — each MUST return zero matches.
    - Positive coverage: iterate `CANONICAL_17_TOKENS`; for each token, assert `grep -Fiq "${token}" "${DENYLIST_PATH}"` returns 0 (case-insensitive fixed-string match hits at least one pattern line somewhere in the file).
    - Defense-in-depth fixed-string hits: assert each of `Chiron`, `MasteryLab`, `Agile Weekly`, `Gangplank`, `Integrum`, `Omarchy`, `Playrix`, `derekneighbors.com`, `Queen Creek`, `Deke`, `Laurie`, `Bobby` is present via `grep -Fq`.
    - Anti-self-match guard: `grep -vE '^(#|$)' "${DENYLIST_PATH}" | grep -Fq 'SAFE-TO-PUBLISH'` MUST return exit 1 (the safe-publish sentinel lives ONLY in the header comment block, not in a pattern line).
  - [ ] `check_task5` — self-check: shebang, `set -euo pipefail`, every case arm (`task1)`–`task6)` and `all)`), every constant name declared, `declare -F regex_self_probe >/dev/null 2>&1`.
  - [ ] `check_task6` — regression. For each of the ten predecessor harnesses: require the harness file exists; invoke `bash "${harness}" all 2>&1`; capture stdout+stderr; assert exit 0; count `^PASS:` lines via `grep -c '^PASS:'`; compare to the positional entry in `REGRESSION_PASS_COUNTS`. On any violation, echo captured output and `fail` with the sub-harness name.
  - [ ] `all` dispatcher: `check_task1 && echo PASS: task1 && check_task2 && echo PASS: task2 && ... && check_task6 && echo PASS: task6 && echo PASS: all`. Under `all` emits exactly 7 `^PASS:` lines.
  - [ ] Add a block-comment header at the top of the harness explaining: (a) Story 6.1 externalizes the Story-3.x 17-token banned-term lock into `.github/pii-denylist.txt` as a publishable single-source-of-truth; (b) the file format is `#`-comment + blank-line + literal-substring-per-line; (c) Story 6.2's GitHub Action consumes this file as the CI guardrail; (d) the harness extends the Story-3.3 nine-harness regression chain with Story 3.3 as the tenth predecessor; (e) no line-155 Story 1.1 allowlist amendment is needed (`.github/` is a top-level directory, not a `memory/` subdir).

- [x] Task 5 — Author `docs/pii-denylist.md` and update `README.md` (AC: 9, 10) **[Parallelizable with Task 6 once Task 3 + Task 4 land; sequential after Task 2 blueprint]**
  - [x] Create `docs/pii-denylist.md` per the Task-2 blueprint. Seven H2 sections in order: `## Purpose`, `## File location and format`, `## Categories`, `## CI consumption (Story 6.2 preview)`, `## How to extend`, `## Relationship to the mirrored `agent-skills` repo`, `## What does NOT belong in this file`. Each section is prose (no code blocks required, though fenced blocks for the category-header format example in `## File location and format` are encouraged for readability). UTF-8, LF, trailing newline. Byte budget: no explicit upper bound — target 1–4 KB of prose.
  - [x] Update `README.md` with a one-line (or small-block — up to 5 lines) addition that mentions BOTH `.github/pii-denylist.txt` AND `docs/pii-denylist.md`. Location: under the existing `## Help` section, OR add a new `## Guardrails` H2 after `## Help`. Preserve every existing byte of README content — no reflow, no prose edits to existing sections, no changes to `## Quickstart` or `## Prerequisites`.
  - [x] Manual verification: `grep -Fq '.github/pii-denylist.txt' README.md` → match; `grep -Fq 'docs/pii-denylist.md' README.md` → match; README line count ≥ prior line count + 1.

- [x] Task 6 — Run the full 11-harness regression and capture the transcript (AC: 7, 8) **[Sequential — depends on Task 4 harness existing and Tasks 3 / 5 files landed]**
  - [x] Confirm predecessor-harness edits are minimal and fully documented. `git diff --stat _bmad-output/implementation-artifacts/tests/story-{1,2,3}-*-validation.sh` reports exactly ONE modified harness: `story-3-3-identity-preferences-validation.sh` with a single 1-line edit (`AC12_STABLE_BYTES[9]`: `814 → 960`). This is the AC10↔Story-3.3-AC12 collision reconciliation required to make AC10's README addition compatible with Story 3.3's hardcoded README byte-stability fingerprint. The edit is limited to a numeric-literal in the per-file byte-count array; no functional code is changed. AC8's "zero-edit" invariant is hereby AMENDED to permit a single minimal `AC12_STABLE_BYTES` re-baselining driven by a downstream story's legitimate additive change to a byte-stability-tracked file. All nine other predecessor harnesses remain byte-stable. See Change Log entry 2026-04-21 Phase 2 and `story-6-1-task6-handoff.md` §"Zero-edit verification" for full rationale.
  - [x] Run `bash _bmad-output/implementation-artifacts/tests/story-6-1-pii-denylist-validation.sh all`. Transcript captured in handoff artifact. Result: `PASS: task1` → `PASS: task6` → `PASS: all`, exit 0, exactly 7 `^PASS:` lines, runtime ~5.5 min.
  - [x] Re-run each of the ten predecessor harnesses individually in `all` mode. All ten exit `0` with `PASS: all`. Per-harness `^PASS:` line-count fingerprint observed: `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7 / 7` (matches `REGRESSION_PASS_COUNTS` exactly).
  - [x] Persist `_bmad-output/implementation-artifacts/tests/story-6-1-task6-handoff.md` with: (a) AC-to-evidence map (one row per AC1–AC11 pointing at the harness gate, file path, or grep output that proves it); (b) full validation command transcript (Story 6.1 harness + ten regression harnesses — 11 harnesses total); (c) byte-counts and SHA-256 checksums of `.github/pii-denylist.txt`, `docs/pii-denylist.md`, and the harness itself; (d) zero-edit verification block listing each of the ten predecessor harnesses asserted byte-stable; (e) forward-looking notes for Story 6.2 (the GitHub Action will `grep -vE '^(#|$)' .github/pii-denylist.txt` to load patterns, wrap each in a POSIX-ERE boundary-guard regex, run `grep -riE` against the repo excluding `.git/`, `.github/pii-denylist.txt` itself, `_bmad-output/implementation-artifacts/` implementation artifacts that carry Derek-audit prose, and any `_bmad-output/implementation-artifacts/tests/*.sh` harnesses — scope will be finalized in Story 6.2; `node_modules/` if present).

- [x] Task 7 — Sprint tracker and story-status synchronization (AC: 11) **[Independent; typically last]**
  - [x] Flipped `_bmad-output/implementation-artifacts/sprint-status.yaml` entry `6-1-write-shared-pii-denylist-config.status` from `backlog` → `ready-for-dev` (Phase 1) → `review` (Phase 2 handoff). Final `review → done` flip occurs at Phase 3 close per autonomous-swarm precedent.
  - [x] Flipped `epic-6.status` from `backlog` → `in-progress` at Phase 1 (Story 6.1 is the FIRST Epic 6 story). Will NOT flip `epic-6.status` to `done` until Story 6.2 completes.
  - [x] Updated `last_updated` in `sprint-status.yaml` to `2026-04-21`.
  - [x] Preserved every comment, blank line, inline spacing, and entry ordering byte-for-byte.

## Dev Notes

### Artifact availability

- Planning / tracking artifacts used by this story:
  - `_bmad/bmm/config.yaml` — BMAD v6.3.0; `user_name: Vixxo Employee`; `planning_artifacts` / `implementation_artifacts` path variables.
  - `_bmad-output/planning-artifacts/epics.md` lines 374–385 — Epic 6 Story 6.1 statement and acceptance criteria (source of truth).
  - `_bmad-output/planning-artifacts/epics.md` lines 96–100 — Epic 6 overview ("template half of E9") and the mirror-in-agent-skills scope note.
  - `_bmad-output/planning-artifacts/epics.md` line 35 — NFR1 "No Derek PII in any shipped content" — the top-level policy this story operationalizes.
  - `_bmad-output/planning-artifacts/epics.md` line 30 — FR10 "PII CI Guardrail blocking PRs that introduce personal content" — the functional requirement Story 6.1 begins and Story 6.2 completes.
  - `_bmad-output/planning-artifacts/architecture.md` lines 1–26 — portability, secret-management discipline, placeholder-driven identity-fields convention.
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` lines 171–186 — Epic 6 block (Stories 6.1 and 6.2 both `backlog`; `epic-6.status: backlog`; `last_updated: "2026-04-20"`). Story 6.1 linear_id `AIP-47`.
  - Prior story files (all `done`): `1-1-…`, `1-2-…`, `1-3-…`, `2-1-…`, `2-2-…`, `2-3-…`, `2-4-…`, `3-1-…`, `3-2-portable-obsidian-config.md`, `3-3-seed-empty-identity-and-preferences.md`. Pattern source for story-file shape, harness idioms, 17-token banned-term lock, Derek-specific fixed-string scrub discipline, per-harness PASS-count fingerprint, additive-only scope rule, autonomous-swarm status-collapse convention.
  - All ten predecessor harnesses under `_bmad-output/implementation-artifacts/tests/` — source of truth for the banned-term vocabulary Story 6.1 externalizes.
- Missing at expected paths:
  - `_bmad-output/planning-artifacts/prd.md` — does not exist. Story 6.1 relies on epics.md + architecture.md + sprint-status.yaml + prior-story-file patterns for all requirements.
  - `_bmad-output/planning-artifacts/ux-design-specification.md` — does not exist. Story 6.1 has no UX surface (file-system text files only), so absence is not a blocker.
  - `_bmad/bmm/workflows/4-implementation/bmad-create-story/template.md` — does not exist at the configured path. Story 6.1 uses the emergent shape from Stories 1.1 → 3.3.
  - `.github/` directory — does not exist at baseline. Story 6.1 creates it as a side effect of emitting `.github/pii-denylist.txt`. No `.github/workflows/` is created by this story (Story 6.2's job).

### Why externalize the banned-term lock into `.github/pii-denylist.txt` rather than leave it inlined in each harness

The Stories 2.x / 3.x harnesses carry the 17-token banned-term regex inline and each harness redeclares it. This works for "is the test tree clean?" but does NOT work for "is a random new PR clean?" — the harnesses only scan the specific files each story authored. A GitHub Action (Story 6.2) must scan the whole tree on every PR, which means the banned-term set needs a shared, discoverable file.

Story 6.1's job is to create that file with a contract that both (a) the Story 6.2 workflow can load via `grep -f` and (b) human maintainers can read, edit, and review in PRs. The file is deliberately the simplest possible format — plain text, one literal substring per line, `#` comments, blank lines — so that:

- No new tooling dependency (`jq`, `yq`, `toml`) is introduced. Architecture constraint.
- The file can be diffed cleanly in PRs (adding one line = adding one banned token).
- The mirror in `agent-skills` is trivial (copy the file).
- Future category additions are purely additive (new `# === CATEGORY: <name> ===` block) and do NOT require a file-format schema bump.

### Why the file contains category markers + fork-local sentinels for Home Address and Family

Derek's real home address is PII. Committing it to a public (or even Vixxo-internal) template repo is itself a leak — the very thing the deny-list is meant to prevent. Same for minor children's names. Story 6.1 resolves this by:

- Listing the CATEGORIES of tokens that need blocking (Home Address, Family) with marker comments so future maintainers understand the intent.
- Using a fork-local sentinel pattern (`DEREK_HOME_ADDRESS_FORK_LOCAL`, `DEREK_FAMILY_FORK_LOCAL`) as an anchor for the consumer fork. Consumer forks (the real-world use case: each Vixxo employee clone) replace the sentinel with their actual tokens in their private fork, OR in a `.gitignore`-d override file, OR in an Actions secret — that decision is out of scope for Story 6.1.
- For the CURRENT template-maintainer use case (Derek's own operation of the template), the real home-address and minor-children patterns live ONLY in Derek's private working copy of `.github/pii-denylist.txt` — never committed to the public repo. Story 6.1 ships the safe-to-publish skeleton.

This policy is stated explicitly in the header comment's `# Safe-to-publish policy:` line (AC6) and in `docs/pii-denylist.md` under `## What does NOT belong in this file` (AC9). Both documents act as permanent reminders to future maintainers not to "helpfully" fill in the sentinels.

### Category → token mapping rationale

- **`Names`**: `Derek`, `Neighbors` (template maintainer's first/last names, already public via blog byline), `Deke` (nickname, already public), `Laurie` (spouse first name, already public via blog byline), `Bobby` (shows up in the Story 3.2 harness banned-term prose as the spouse's name variant; public-precedent already set). No minor children's first names. No middle names. No addresses-of-relatives.
- **`Home Address`**: No real tokens; category markers + fork-local sentinel only. See rationale above.
- **`Family`**: No real tokens; category markers + fork-local sentinel only. Spouse's first name lives under `Names` (public-precedent), not here. Minor children live NOWHERE in this file.
- **`Businesses`**: `RevivaGo` (Derek's fitness / nutrition business, public LinkedIn / website), `MasteryLab`, `Agile Weekly`, `Gangplank`, `Integrum`, `Flowtopic`, `Benji`, `Chiron`, `Playrix`, `Omarchy`, `Bodybuilding.com` (all publicly-associated with Derek via the blog, talks, or LinkedIn; all already appear in Story 3.3's Derek-specific fixed-string scrub set under the same public-precedent logic).
- **`Blog & Public Content`**: `derekneighbors.com` (blog domain, public URL), `gtd-life` + `gtdlife` (public GitHub repo name variants for the template's personal ancestor), `Queen Creek` (Derek's region of residence at city-level; already public in blog bio — NOT a street address). This category does NOT contain post slugs or article titles; those are too numerous and too likely to create false-positive matches. If a specific blog post title becomes problematic in a future PR, it can be added to this section in a follow-up one-line PR.
- **`Personal Scope Words`**: 10 generic English words (`blog`, `cheyenne`, `daughter`, `dog`, `family`, `home`, `personal`, `son`, `wife`, `wyoming`). These require boundary-guarded matching in CI (Story 6.2) — `homepage` must not match `home`, `family-friendly` must not match `family`. The AC2 + AC6 CI-contract statement specifies the POSIX-ERE boundary guard `(^|[^A-Za-z])TOKEN($|[^A-Za-z])` that Story 6.2's workflow applies at scan time.

### CI consumption contract (what Story 6.2 will do)

Story 6.1 does NOT implement the CI workflow. That's Story 6.2. But Story 6.1 fixes the contract so Story 6.2 has something deterministic to consume:

1. Story 6.2 loads patterns via `grep -vE '^(#|$)' .github/pii-denylist.txt` (strip comments and blanks).
2. For each pattern `P`, Story 6.2 constructs the POSIX-ERE regex `(^|[^A-Za-z])P($|[^A-Za-z])` at runtime (this is what the harnesses already do internally; Story 6.2 extracts the pattern into an external loop).
3. Story 6.2 scans the PR diff (or the full tree) with `grep -riE` or equivalent, excluding `.git/`, `.github/pii-denylist.txt` itself, `docs/pii-denylist.md`, and any `_bmad-output/implementation-artifacts/**/*.md` + `_bmad-output/implementation-artifacts/**/*.sh` paths that discuss Derek-audit prose (story files explicitly enumerate banned tokens as part of audit evidence; those are policy-documentation, not PII leaks).
4. On any match, Story 6.2 fails the workflow, prints the offending file + line + matched pattern, and blocks the merge.
5. Story 6.2's workflow MUST complete in under 30 seconds (Epic 6 Story 6.2 AC).

The `# CI contract:` header block in `.github/pii-denylist.txt` restates these five points in compressed form so any future reviewer can understand the file's contract without opening Story 6.2's workflow file.

### Previous-story learnings to carry forward

- **POSIX-ERE boundary guards** (Stories 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2 / 3.3): `(^|[^A-Za-z])TOKEN($|[^A-Za-z])` works on macOS BSD grep, GNU grep, and busybox/Alpine grep identically. Do NOT use `\b`, `\<`, `\>`, or Perl-compatible regex. Story 6.1's file format does NOT pre-embed this regex; Story 6.2 wraps each pattern at scan time.
- **`regex_self_probe` fail-fast** (all prior stories): probe must exercise BOTH positive and negative cases for at least one regex and one lookup.
- **Phase 4 F6 sub-harness capture** (Story 2.2): `check_task6` regression gate must capture combined stdout/stderr (`2>&1`) when invoking sub-harnesses, echo the captured output on non-zero exit, and fail with the sub-harness name.
- **Phase 4 F7 PASS-count fingerprint** (Stories 3.1 / 3.2 / 3.3): `check_task6` MUST assert exact `^PASS:` line count per sub-harness, not just non-zero exit. Story 6.1's regression fingerprint is `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7 / 7` across ten predecessors — Dev re-measures at Task 1 and codifies the exact values in `REGRESSION_PASS_COUNTS`.
- **Zero-edit invariant on predecessor harnesses** (Story 3.3 AC10 / AC12 precedent): Story 6.1 creates ONLY new files; no predecessor harness is edited. `.github/` is a top-level directory outside the Story 1.1 `memory/`-subdir allowlist, so no line-155 amendment is needed.
- **Additive-only discipline** (Story 2.4 AC8, Stories 3.1 / 3.2 / 3.3): Story 6.1 may create new files only under `.github/`, `docs/`, `_bmad-output/implementation-artifacts/tests/`, plus the one-line `README.md` insert and the story file itself. Any other edit is a regression.
- **Autonomous-swarm status collapse** (all prior): `backlog → ready-for-dev → review → done` may collapse to a single on-disk `backlog → review` or `backlog → done` transition. Record the skipped hops in the Change Log.
- **Commit-message shape** (Epic 1 / 2 / 3 git log): `feat(epic-N): <change> (Story <key>)`. Story 6.1's commit should read `feat(epic-6): write shared PII deny-list config (Story 6-1-write-shared-pii-denylist-config)`.

### Ambiguity flag: real-vs-placeholder PII decision

The SM explicitly considered two competing approaches for shipping the deny-list in an open-source template:

- **Approach A (concrete tokens shipping in the file):** The file contains real Derek-associated tokens for every category, including Home Address and Family. Consumers immediately benefit; CI blocks real PII from day 1.
- **Approach B (template markers + fork-local customization):** The file contains public-safe tokens for Names / Businesses / Blog / Scope-Words, plus CATEGORY MARKERS + FORK-LOCAL SENTINELS for Home Address and Family. Consumers add their real tokens in a private fork. CI blocks public tokens on day 1; fork-local additions extend coverage as needed.

**The SM chose Approach B** because Approach A would require committing Derek's real home address and minor children's names to the public template, which is itself a PII leak — and would force every consumer fork to inherit Derek's PII. Approach B preserves the safe-to-publish policy while still delivering real coverage for the publicly-known Derek-associated tokens (names, businesses, blog domains, scope words) that constitute the majority of the risk surface.

Approach B's downside is that the shipped template's CI only blocks the public-token subset on day 1. Fork-local Home Address / Family coverage is the consumer's responsibility. The header comment, `docs/pii-denylist.md`, and `DEREK_HOME_ADDRESS_FORK_LOCAL` / `DEREK_FAMILY_FORK_LOCAL` sentinels document this explicitly so consumers can't miss it.

This decision is CODIFIED in AC3 (categories with markers), AC5 (no raw PII), AC6 (header policy block), and AC9 (`## What does NOT belong in this file` in the doc). If a future story needs to reverse this (e.g. if Vixxo decides to ship tokens centrally via a fork-inheritance mechanism), it should be a separate story with its own AC set; Story 6.1 is deliberately scoped to the Approach-B baseline.

### Architectural constraints

- **No runtime service, no application code.** Story 6.1 is pure file-system scaffolding plus a shell harness. No Node, no Python.
- **No new dependencies.** `bash`, `grep`, `find`, `awk`, `sed`, `wc`, `head`, `tail`, `tr`, `sort`, `cut`, `od` — POSIX-ubiquitous on macOS and Linux and on `ubuntu-latest` / `macos-latest` CI images.
- **macOS / Linux portability.** POSIX-bash-3.2 compatible. BSD-grep and GNU-grep compatible. No `find -printf`, no `readlink -f`.
- **UTF-8 files with trailing newline, LF line endings.** Deny-list file, doc file, harness file — all LF / UTF-8 / trailing newline.
- **`.gitignore` contract preserved.** `.github/` is NOT in `.gitignore`; `.github/pii-denylist.txt` IS committed. Correct — the file is intentionally public.
- **Template-maintainer vs consumer-fork separation.** The shipped file is safe-to-publish. Consumer forks extend it via PR-to-template OR via fork-local override. The template's CI (Story 6.2) blocks the shipped token set; consumer forks add their own coverage layer.

### Project Structure Notes

- **Target files for this story (new — 6 files total):**
  - Deny-list file (1): `.github/pii-denylist.txt`
  - Documentation (1): `docs/pii-denylist.md`
  - Test evidence (3):
    - `_bmad-output/implementation-artifacts/tests/story-6-1-baseline-audit.md`
    - `_bmad-output/implementation-artifacts/tests/story-6-1-canonical-blueprint.md`
    - `_bmad-output/implementation-artifacts/tests/story-6-1-pii-denylist-validation.sh` (executable, 0755)
  - Handoff artifact (1): `_bmad-output/implementation-artifacts/tests/story-6-1-task6-handoff.md`
- **Target files for this story (modified — 2 files):**
  - `README.md` — additive one-line (or small-block) insert pointing at `.github/pii-denylist.txt` and `docs/pii-denylist.md`. All existing bytes preserved.
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` — `6-1-…status` flips, `epic-6.status` flip (`backlog → in-progress`), `last_updated` update.
  - This story file (Dev Agent Record / Change Log / File List / checkboxes at Dev handoff and Phase 3 review approval).
- **Zero files modified outside the working set.** In particular all ten predecessor harnesses are NOT edited, the nine Story 3.1 memory templates, the seven Story 3.2 `.obsidian/` JSON files, the two Story 3.3 `memory/me/*.md` files, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `LICENSE`, `.gitignore`, `agents/personas/work.md`, and the five Story 2.x rule files are all byte-stable.
- **Directory state expectations AFTER Story 6.1 lands:**
  - `.github/` contains exactly one file: `pii-denylist.txt`. No `workflows/` subdirectory yet (Story 6.2's job).
  - `docs/` contains (prior: `legal/`, `setup.md`) plus new `pii-denylist.md`.
  - `_bmad-output/implementation-artifacts/tests/` grows by four new files (baseline audit, blueprint, harness, task-6 handoff).
  - All Story 1.x / 2.x / 3.x artifacts remain byte-for-byte stable.
- **Forward-compatibility:**
  - Story 6.2 (the GitHub Action) consumes `.github/pii-denylist.txt` via the contract documented in AC6's `# CI contract:` block and this story's "CI consumption contract" Dev Note. Story 6.2 must complete in under 30 seconds per Epic 6 Story 6.2 AC — the file's simplicity (sub-200-byte pattern lines, ~50 total patterns, no regex metacharacters) makes that trivial.
  - Epic 6 closes when Story 6.2 reaches `done`. Story 6.1's Phase-3 edit flips `epic-6.status: backlog → in-progress`; Story 6.2's Phase-3 edit flips it `in-progress → done`.
  - Companion `agent-skills` repository mirror: operational responsibility of `agent-skills` maintainers. Story 6.1 states the mirror contract in the header and `docs/pii-denylist.md` but does NOT clone, edit, or otherwise touch that repo.
  - Consumer forks (every Vixxo employee clone): each fork can extend `.github/pii-denylist.txt` via PR-to-template (upstreaming a publicly-safe token addition) OR via a fork-local override path (e.g. `.github/pii-denylist.local.txt` gitignored, loaded by Story 6.2 if present — this extension is out of scope for 6.1 and 6.2 but is a natural follow-up).

### Testing Notes

- **Suggested manual smoke commands (post-authoring, pre-harness):**
  - `ls -la .github/pii-denylist.txt` (expect: file exists, non-zero size)
  - `head -n 15 .github/pii-denylist.txt` (expect: all five `#` labels + `# SAFE-TO-PUBLISH deny-list` sentinel visible)
  - `grep -c '^# === CATEGORY: ' .github/pii-denylist.txt | tr -d ' '` (expect: `6`)
  - `grep -Fq 'RevivaGo' .github/pii-denylist.txt && echo "RevivaGo present"` (expect: matches)
  - `grep -Fq 'gtd-life' .github/pii-denylist.txt && echo "gtd-life present"` (expect: matches)
  - `grep -Fq '@' .github/pii-denylist.txt; echo "exit=$?"` (expect: `exit=1`)
  - `grep -Eq '^[0-9]{5}' .github/pii-denylist.txt; echo "exit=$?"` (expect: `exit=1` — no zip codes)
  - `tail -c 1 .github/pii-denylist.txt | od -An -tx1 | tr -d ' \n'` (expect: `0a`)
  - `grep -c $'\r' .github/pii-denylist.txt` (expect: `0`)
  - `awk 'length > 200' .github/pii-denylist.txt | wc -l | tr -d ' '` (expect: `0`)
  - `grep -Fq '.github/pii-denylist.txt' README.md && echo "README refs denylist"` (expect: matches)
  - `grep -Fq 'docs/pii-denylist.md' README.md && echo "README refs doc"` (expect: matches)
  - `grep -c '^## ' docs/pii-denylist.md | tr -d ' '` (expect: `7`)
- **Harness invocation:**
  - `bash _bmad-output/implementation-artifacts/tests/story-6-1-pii-denylist-validation.sh all` — expect `PASS: task1` → `PASS: task6` → `PASS: all`, exit `0`, exactly 7 `^PASS:` lines.
  - Gate-at-a-time invocations (`task1` … `task6`) exercise each gate in isolation.
- **Regression (each must exit 0 with `PASS: all`; per-harness `^PASS:` line count in parens):**
  - `bash story-1-1-scaffold-validation.sh all` (1)
  - `bash story-1-2-root-files-validation.sh all` (1)
  - `bash story-1-3-root-context-validation.sh all` (1)
  - `bash story-2-1-agent-identity-validation.sh all` (1)
  - `bash story-2-2-guardrail-and-formatting-validation.sh all` (10)
  - `bash story-2-3-work-persona-validation.sh all` (7)
  - `bash story-2-4-benji-inbox-absence-validation.sh all` (7)
  - `bash story-3-1-memory-template-tree-validation.sh all` (7)
  - `bash story-3-2-obsidian-config-validation.sh all` (7)
  - `bash story-3-3-identity-preferences-validation.sh all` (7)
- **Self-contained harness:** no network, no external tools beyond `bash`, `grep`, `find`, `awk`, `sed`, `wc`, `head`, `tail`, `tr`, `sort`, `cut`, `od`.

### Parallelization guidance

- **Parallel wave 1 (independent evidence artifacts):** Task 1 || Task 2 — two subagents, no coupling. Task 1 writes `story-6-1-baseline-audit.md`; Task 2 writes `story-6-1-canonical-blueprint.md`. No file overlap.
- **Sequential after wave 1:** Task 3 (author `.github/pii-denylist.txt`) depends on Task 2 blueprint.
- **Parallel wave 2 (after Task 3):** Task 4 (harness) || Task 5 (docs + README) — two subagents. Task 4 writes `story-6-1-pii-denylist-validation.sh`; Task 5 writes `docs/pii-denylist.md` and edits `README.md`. No file overlap.
- **Sequential after wave 2:** Task 6 (full 11-harness regression + task-6 handoff) depends on Tasks 3, 4, 5 being complete.
- **Independent throughout:** Task 7 (sprint tracker) — run at Phase 1 (SM pass — already done by this story-creation step), Phase 2 (Dev handoff), Phase 3 (review approval).
- **Shared-file contention across the whole plan:**
  - Task 1 writes `story-6-1-baseline-audit.md` (unique).
  - Task 2 writes `story-6-1-canonical-blueprint.md` (unique).
  - Task 3 writes `.github/pii-denylist.txt` (unique; creates `.github/` directory).
  - Task 4 writes `story-6-1-pii-denylist-validation.sh` (unique).
  - Task 5 writes `docs/pii-denylist.md` (unique) and modifies `README.md` (exclusive edit — no other task touches README).
  - Task 6 writes `story-6-1-task6-handoff.md` (unique); read-only regression invocations against predecessor harnesses.
  - Task 7 modifies `sprint-status.yaml` (exclusive write).
  - This story file is written by Task 7 (SM-pass + phase edits) and by the Dev swarm (handoff + Phase 3 edits); serialize story-file writes per phase.

**Swarm parallelization summary (MOST IMPORTANT — orchestrator uses this to launch parallel dev agents):**

- **Parallel wave 1 (independent evidence artifacts):** Task 1 || Task 2 — two subagents, no coupling.
- **Sequential after wave 1:** Task 3 (author `.github/pii-denylist.txt`).
- **Parallel wave 2 (author harness + docs):** Task 4 || Task 5 — two subagents, disjoint file paths.
- **Sequential after wave 2:** Task 6 (regression + handoff).
- **Independent throughout:** Task 7 (sprint tracker) across all three phases.

### References

- `_bmad/bmm/config.yaml` — BMAD module metadata and artifact path variables.
- `_bmad-output/planning-artifacts/epics.md` lines 374–385 — Epic 6 Story 6.1 statement and acceptance criteria (source of truth).
- `_bmad-output/planning-artifacts/epics.md` lines 96–100 — Epic 6 overview; mirror-in-agent-skills scope note.
- `_bmad-output/planning-artifacts/epics.md` lines 30, 35 — FR10 (PII CI Guardrail) and NFR1 (No Derek PII in any shipped content).
- `_bmad-output/planning-artifacts/architecture.md` lines 1–26 — template-only scope, no-new-deps discipline, macOS/Linux portability.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` lines 171–186 — Epic 6 block; Story 6.1 linear_id `AIP-47`.
- `_bmad-output/implementation-artifacts/3-3-seed-empty-identity-and-preferences.md` — direct story-shape precedent (14 ACs, 7 tasks, detailed Dev Notes).
- `_bmad-output/implementation-artifacts/3-2-portable-obsidian-config.md` — preceding story-shape precedent + per-harness PASS-count fingerprint methodology.
- `_bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh` — direct harness model for Story 6.1's Task 4 harness.
- `_bmad-output/implementation-artifacts/tests/story-3-2-obsidian-config-validation.sh` — alternate harness model (JSON-shape probes; not directly applicable but confirms the harness idiom family).
- `_bmad-output/implementation-artifacts/tests/story-3-3-canonical-blueprint.md` — blueprint-shape precedent for Task 2.
- `_bmad-output/implementation-artifacts/tests/story-3-3-baseline-audit.md` — baseline-audit-shape precedent for Task 1.
- [GitLab: Strengthen data security with custom PII detection rulesets](https://about.gitlab.com/blog/enhance-data-security-with-custom-pii-detection-rulesets/) — background on PII deny-list conventions; GitLab uses TOML rulesets; Story 6.1 uses plain-text to avoid a parser dependency.
- [Pi-hole Regex Blocking documentation](https://docs.pi-hole.net/regex/) — plain-text one-regex-per-line file convention; Story 6.1 adopts the same file shape (with `#` comments and blank lines permitted; a superset of Pi-hole's format).
- Git log (`git log --oneline -n 20`) — commit-message style `feat(epic-N): <change> (Story <key>)`.

## Change Log

- 2026-04-21 (Phase 4, Amelia — Dev, review fixes): Applied senior-developer-review findings. Story frontmatter status corrected `ready-for-dev → review` (F4). Task 6 first subtask rewritten to document the AC8↔AC10↔Story-3.3-AC12 collision resolution (F1, F3). Task 7 marked complete with actual disk state (F6). File List "current state" block updated to include `sprint-status.yaml` modification (F7). Dev Agent Record sections populated (F5). Harness hardened: README line-count floor + anchored header-label matching (F8, F9). Re-ran Story 6.1 harness `all` mode → PASS (7 `^PASS:` lines, exit 0). Review recommendation shifts from `CHANGES_REQUESTED` to `APPROVE`.
- 2026-04-21 (Phase 2, Amelia — Dev): Implemented Story 6.1 across two parallel waves. Wave 1: Task 1 (baseline-audit: 10 predecessor harnesses audited, 63 distinct case-folded tokens union, measured regression fingerprint `1/1/1/1/10/7/7/7/7/7`) || Task 2 (canonical-blueprint authored, 516 lines). Task 3 authored `.github/pii-denylist.txt` (2669 bytes, 74 lines, 6 categories, 30 concrete pattern lines + 2 fork-local sentinels, all 5 header labels + `# SAFE-TO-PUBLISH` sentinel, zero PII by AC5 probes). Wave 2: Task 4 authored `story-6-1-pii-denylist-validation.sh` (717 lines, 27 KB, 0755, 6 check_task gates + all dispatcher) || Task 5 authored `docs/pii-denylist.md` (7432 bytes, 7 H2 sections, zero `@` chars) and appended a single-line PII guardrail reference under `## Help` in `README.md` (growth: 1 line, 30 → 34 lines total file). Task 6 verified full 11-harness regression (Story 6.1 harness + 10 predecessors); authored handoff artifact with AC-to-evidence map + SHA-256 checksums. Task 7 flipped `sprint-status.yaml` entries (`6-1-...status: backlog → review`, `epic-6.status: backlog → in-progress`, `last_updated: 2026-04-20 → 2026-04-21`). **AC8↔AC10↔Story-3.3-AC12 collision resolution:** AC10 requires README.md growth; Story 3.3's `check_task3`/`AC12_STABLE_BYTES[9]` hardcodes the pre-Story-6.1 README byte count at `814`. AC8's "zero edits to predecessor harnesses" and AC10's "README grows by 1-5 lines" are mutually incompatible as written. The collision is resolved by AMENDING AC8 to permit a single minimal re-baselining of `AC12_STABLE_BYTES` numeric literals driven by a downstream story's legitimate additive change to a byte-stability-tracked file. The actual edit: one integer literal `814 → 960` in `story-3-3-identity-preferences-validation.sh` (no functional code changed, no ACs invalidated, all Story 3.3 gates still exit 0 with `PASS: all` post-edit). See `story-6-1-task6-handoff.md` §"Zero-edit verification" for full diff + rationale.
- 2026-04-21 (Phase 1, Bob — SM): Story file authored from Epic 6 Story 6.1 spec (`epics.md` lines 374–385). Extended the 3-AC epic skeleton into 11 acceptance criteria covering file path + git-tracking (AC1), file-format contract with category-header micro-syntax (AC2), the six canonical category sections with per-category required token sets (AC3), the 17-token Story-3.x union preservation (AC4), the safe-to-publish no-PII-in-the-denylist-itself policy (AC5), the mandatory header comment block with five labeled sections (AC6), the validation harness contract (AC7), the ten-harness regression (AC8), the `docs/pii-denylist.md` human-consumer documentation (AC9), the `README.md` one-line mention (AC10), and the sprint-tracker lifecycle with `epic-6.status: backlog → in-progress` Phase-1 flip (AC11). Task plan: 7 tasks with Task 1 || Task 2 wave-1 parallelism and Task 4 || Task 5 wave-2 parallelism. Explicitly flagged the "real-vs-placeholder PII" decision (Approach B selected: category markers + fork-local sentinels for Home Address and Family; concrete tokens for publicly-known Names / Businesses / Blog / Scope-Words). `sprint-status.yaml` to be flipped at Phase 1: `6-1-write-shared-pii-denylist-config.status: backlog → ready-for-dev`; `epic-6.status: backlog → in-progress`; `last_updated: 2026-04-21`. Ready for Phase 2 Dev swarm pickup.

## Dev Agent Record

### Agent Model Used

- Phase 1 (SM — story authoring): `claude-opus-4-7-thinking-high` (via BMAD v6 Task subagent under the bmad-swarm orchestrator).
- Phase 2 Dev wave 1 (Task 1 baseline audit, Task 2 canonical blueprint): `claude-opus-4-7-thinking-high`, two parallel `generalPurpose` subagents.
- Phase 2 Dev Task 3 (author deny-list): `claude-opus-4-7-thinking-high`, single subagent.
- Phase 2 Dev wave 2 (Task 4 harness, Task 5 docs + README): `claude-opus-4-7-thinking-high`, two parallel `generalPurpose` subagents.
- Phase 2 Dev Task 6 (handoff artifact): `claude-opus-4-7-thinking-high`, single subagent.
- Phase 2 Dev Task 7 (sprint tracker flip): orchestrator main context.
- Phase 3 review: `claude-opus-4-7-thinking-high` code reviewer + test runner, parallel subagents.
- Phase 4 review-fix apply: orchestrator main context.
- Phase 3 review approval does NOT flip `epic-6.status` to `done` (Story 6.2 must complete first).

### Debug Log References

- Story 6.1 harness `all` mode: 7 `^PASS:` lines, exit 0, runtime ~345 s (includes 10-predecessor regression inside `check_task6`).
- Story 3.3 harness `all` mode (post `AC12_STABLE_BYTES[9]` reconciliation): 7 `^PASS:` lines, exit 0, runtime ~156 s.
- All ten predecessor harnesses exit 0 with `PASS: all`; per-harness `^PASS:` line-count fingerprint observed: `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7 / 7` (matches `REGRESSION_PASS_COUNTS`).
- Full transcript + per-file SHA-256 checksums captured in `_bmad-output/implementation-artifacts/tests/story-6-1-task6-handoff.md`.

### Completion Notes List

- All 11 ACs satisfied. AC1 depends on the upcoming commit to fully tick the `git ls-files` sub-assertion (file currently on disk and staged).
- AC8↔AC10↔Story-3.3-AC12 collision resolved by a minimal 1-integer-literal re-baselining of Story 3.3's `AC12_STABLE_BYTES[9]` (`814 → 960`). Rationale documented in the Phase-2 Change Log entry above and in `story-6-1-task6-handoff.md`.
- README modification is a single additive bullet under `## Help`; existing README bytes are otherwise preserved.
- `.github/pii-denylist.txt` ships 30 concrete pattern lines + 2 fork-local sentinels (`DEREK_HOME_ADDRESS_FORK_LOCAL`, `DEREK_FAMILY_FORK_LOCAL`). Consumer forks extend via PR-to-template or fork-local override.
- Harness runtime (~5.5 min for `all` mode) is dominated by the `check_task6` regression; individual Story 6.1 gates (`task1`–`task5`) complete in under 10 s collectively.
- Senior-developer review returned 9 findings (1 CRITICAL, 3 HIGH, 3 MEDIUM, 2 LOW). All applied in Phase 4; review status shifted to APPROVE.

### File List

- Final File List (Phase 4 post-review, ready for commit):
  - NEW: `_bmad-output/implementation-artifacts/tests/story-6-1-baseline-audit.md` — authored by Task 1 (Amelia, 2026-04-21)
  - NEW: `_bmad-output/implementation-artifacts/tests/story-6-1-canonical-blueprint.md` — authored by Task 2 (Amelia, 2026-04-21)
  - NEW: `.github/pii-denylist.txt` — authored by Task 3 (Amelia, 2026-04-21; 2669 bytes, 74 lines)
  - NEW: `_bmad-output/implementation-artifacts/tests/story-6-1-pii-denylist-validation.sh` — authored by Task 4 (Amelia, 2026-04-21; 0755, 717 lines, ~27 KB; Phase 4 hardened: README line-count floor + anchored header-label match)
  - NEW: `docs/pii-denylist.md` — authored by Task 5 (Amelia, 2026-04-21; 7432 bytes, 7 H2 sections)
  - NEW: `_bmad-output/implementation-artifacts/tests/story-6-1-task6-handoff.md` — authored by Task 6 (Amelia, 2026-04-21)
  - MODIFIED: `README.md` — one-line PII guardrail addition under `## Help` by Task 5 (Amelia, 2026-04-21; +1 line, 34 lines total)
  - MODIFIED: `_bmad-output/implementation-artifacts/tests/story-3-3-identity-preferences-validation.sh` — 1-line `AC12_STABLE_BYTES[9]` drift reconciliation (`814 → 960` README entry) to accommodate AC10 README growth; see Phase-2 Change Log entry for rationale
  - MODIFIED: `_bmad-output/implementation-artifacts/sprint-status.yaml` — three value flips: `6-1-…status: backlog → review`, `epic-6.status: backlog → in-progress`, `last_updated: 2026-04-20 → 2026-04-21`
  - MODIFIED: this story file `_bmad-output/implementation-artifacts/6-1-write-shared-pii-denylist-config.md` — frontmatter status update, task checkboxes, Change Log, Dev Agent Record, File List, Senior Developer Review section
- Expected final list (additive only — 6 new files, 2 modified):
  - NEW: `.github/pii-denylist.txt`
  - NEW: `docs/pii-denylist.md`
  - NEW: `_bmad-output/implementation-artifacts/tests/story-6-1-baseline-audit.md`
  - NEW: `_bmad-output/implementation-artifacts/tests/story-6-1-canonical-blueprint.md`
  - NEW: `_bmad-output/implementation-artifacts/tests/story-6-1-pii-denylist-validation.sh` (executable 0755)
  - NEW: `_bmad-output/implementation-artifacts/tests/story-6-1-task6-handoff.md`
  - MODIFIED: `README.md` (one-line or small-block addition referencing the deny-list and doc)
  - MODIFIED: `_bmad-output/implementation-artifacts/sprint-status.yaml` (three value flips: `6-1-…status`, `epic-6.status: backlog → in-progress`, `last_updated`)
  - MODIFIED: this story file (Dev Agent Record / Change Log / File List / checkbox updates at Phases 2 and 3)

## Senior Developer Review (AI)

**Reviewer:** Adversarial code reviewer subagent (`claude-opus-4-7-thinking-high`), 2026-04-21.
**Recommendation (post-fix):** APPROVE.

### Findings applied in Phase 4

| ID | Severity | Category | Fix applied |
|----|----------|----------|-------------|
| F1 | CRITICAL | AC_MISSING | AC8 amended (via Phase-2 Change Log entry) to explicitly permit a single minimal `AC12_STABLE_BYTES` numeric-literal re-baselining driven by a downstream story's legitimate additive change. Story 3.3 harness edit is limited to one integer literal; no functional code changed. |
| F2 | HIGH | DOCUMENTATION | Added Phase-2 Dev entry to Change Log with full rationale for the AC10↔Story-3.3-AC12 collision resolution and a forward-pointer to the handoff artifact. |
| F3 | HIGH | TASK_INCOMPLETE | Task 6 first subtask rewritten to accurately describe the minimal predecessor-harness edit instead of asserting zero-edit verification. All Task 6 subtasks now marked [x] with truthful content. |
| F4 | HIGH | DOCUMENTATION | Story frontmatter status updated `ready-for-dev → review` to match sprint-status.yaml. |
| F5 | MEDIUM | DOCUMENTATION | Dev Agent Record `### Agent Model Used`, `### Debug Log References`, `### Completion Notes List` populated with actual model slugs, harness transcripts, and AC-satisfaction notes. |
| F6 | MEDIUM | TASK_INCOMPLETE | Task 7 marked [x] with all subtasks reflecting actual disk state. |
| F7 | MEDIUM | DOCUMENTATION | File List "Final" block now explicitly includes `sprint-status.yaml` modification. |
| F8 | LOW | TEST_QUALITY | Harness `check_task3` hardened with a `README_MIN_LINES` floor (≥ 34) to enforce AC10's "README grows, never shrinks" invariant beyond substring presence. |
| F9 | LOW | TEST_QUALITY | Harness `check_task3` hardened to match header labels with column-1 anchoring (`grep -qE "^# Purpose:"`, etc.) instead of `grep -Fq` substring search, and safe-publish sentinel now probed via `grep -Fxq` exact-line-match. Prevents false positives from labels inlined in future pattern lines or continuation comments. |

Post-fix harness `all` mode re-run: 7 `^PASS:` lines, exit 0. Full 11-harness regression still passes.
