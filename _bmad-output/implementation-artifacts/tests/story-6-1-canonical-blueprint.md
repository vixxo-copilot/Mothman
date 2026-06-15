# Story 6.1 Canonical Blueprint

Locked design for the shared PII deny-list file produced by Task 3 (`.github/pii-denylist.txt`) and its companion doc produced by Task 5 (`docs/pii-denylist.md`). Every lock in this document maps to one or more ACs in Story 6.1 and is enforced by the Task 4 validation harness (`story-6-1-pii-denylist-validation.sh`). Follows the Story 3.3 `canonical-blueprint.md` precedent (shape, tone, lock vocabulary, cross-AC map).

This document is a pure specification. It defines the exact file shape, the verbatim header comment block, the verbatim six-section category template (including token ordering per category), the per-category token inventory with rationale, the safe-to-publish policy restatement, the forward-referenced CI-consumption contract for Story 6.2, the AC5 negative-scan probes, and the H2 section list for the companion `docs/pii-denylist.md`. It does not author the real file contents — Task 3 does that by applying the template verbatim, and Task 5 authors the doc from the section-shape lock below.

Conventions used throughout:

- **File-shape lock:** the deny-list is a plain-text UTF-8 file with LF line endings only, a single trailing newline, no tabs, no trailing spaces, every physical line ≤ 200 bytes. Lines are either (a) a comment line starting with `#` in column 1, (b) a blank line (zero bytes before the `\n`), or (c) a pattern line — a single non-empty token with no leading or trailing whitespace.
- **Header lock:** the first contiguous block of `#` lines at the top of the file (before the first blank line) contains the five labeled sections plus the `# SAFE-TO-PUBLISH deny-list` sentinel verbatim as shown in `## Header comment block (exact labeled sections)`.
- **Category lock:** exactly six `# === CATEGORY: <name> ===` sections appear in canonical order, with the exact token list and exact intra-category ordering shown in `## Category section format and ordering`.
- **Safe-to-publish lock:** the file contains ZERO raw home addresses, ZERO five-digit US zip codes, ZERO minor children's first names, ZERO phone numbers, and ZERO `@` characters (AC5). Enforced by the probes in `## Negative-scan patterns (AC5 content-scrub probes)`.
- **Doc lock:** `docs/pii-denylist.md` contains exactly the seven H2 sections in `## Doc file shape (docs/pii-denylist.md H2 sections)`, in the listed order.

---

## Deny-list file shape

Target file: `.github/pii-denylist.txt`.

### Physical file attributes

- **Encoding:** UTF-8. Harness asserts `file -b --mime-encoding` returns `utf-8` or `us-ascii` (ASCII is a subset of UTF-8 and acceptable).
- **Line endings:** LF only. Harness asserts `grep -c $'\r' .github/pii-denylist.txt` equals `0`.
- **Trailing newline:** last byte `0x0a`. Harness asserts `tail -c 1 .github/pii-denylist.txt | od -An -tx1 | tr -d ' \n'` equals `0a`.
- **Non-empty:** `[[ -s .github/pii-denylist.txt ]]` is true. `wc -c` returns a non-zero integer.
- **Line-length budget:** every physical line ≤ 200 bytes. Harness asserts `awk 'length > 200' .github/pii-denylist.txt | wc -l | tr -d ' '` equals `0`.
- **No tabs:** `grep -c $'\t' .github/pii-denylist.txt` equals `0`.
- **No trailing spaces:** `grep -cE ' $' .github/pii-denylist.txt` equals `0`.
- **Git-tracked:** `git ls-files .github/pii-denylist.txt` returns the path; exit `0`. The `.github/` directory is a new top-level directory introduced by Story 6.1; no `.gitkeep` sentinel is needed because the deny-list file itself makes the directory trackable.

### Logical file structure (top-to-bottom)

1. **Header comment block** — contiguous `#` lines (see `## Header comment block (exact labeled sections)`), terminated by a single blank line.
2. **Category section 1 — `Names`** — `# === CATEGORY: Names ===` header, one-line description comment, pattern lines, terminated by a single blank line.
3. **Category section 2 — `Home Address`** — marker-comment structure + fork-local sentinel, terminated by a single blank line.
4. **Category section 3 — `Family`** — marker-comment structure + fork-local sentinel, terminated by a single blank line.
5. **Category section 4 — `Businesses`** — header, description, alphabetized pattern lines, terminated by a single blank line.
6. **Category section 5 — `Blog & Public Content`** — header, description, pattern lines, terminated by a single blank line.
7. **Category section 6 — `Personal Scope Words`** — header, description, alphabetized pattern lines, terminated by the final newline (no trailing blank line after the last category is required, but a single terminating blank line is permitted).

### Line-kind classification rule

Every physical line must match one of the following three kinds, with no exceptions:

| Kind | Regex | Purpose |
| --- | --- | --- |
| Comment | `^#` | Header sections, category headers, description prose, marker comments. |
| Blank | `^$` | Section terminator / visual separator. |
| Pattern | `^[^#[:space:]].*[^[:space:]]$` (or single-char token `^[^#[:space:]]$`) | Literal substring token, no leading/trailing whitespace, non-empty. |

Patterns are treated as **literal substrings** by Story 6.1. Story 6.2's CI workflow wraps each pattern in a POSIX-ERE boundary-guard regex at scan time (`(^|[^A-Za-z])TOKEN($|[^A-Za-z])`); Story 6.1's file does NOT pre-escape regex metacharacters.

---

## Header comment block (exact labeled sections)

The file opens with the following contiguous `#` block, verbatim. Five labeled comment lines plus the `# SAFE-TO-PUBLISH deny-list` sentinel. Order is locked. Each labeled line appears on its own single physical line (long prose content on one line is acceptable up to the 200-byte per-line budget; see the CI-contract line for the operative case).

```
# Purpose: This file is the single source of truth for banned personal patterns. Do not duplicate.
# CI contract: Each line is a literal substring. Story 6.2's workflow wraps each pattern in a POSIX-ERE boundary-guard regex (^|[^A-Za-z])TOKEN($|[^A-Za-z]) at scan time, case-insensitive. Blank lines and lines starting with `#` are ignored. This file itself is excluded from the scan.
# How to extend: Add the new token in alphabetical order under the correct `# === CATEGORY: <name> ===` section, in a PR against main, with a one-line commit message explaining why the token belongs on the list.
# Mirror: This file is mirrored in the companion `agent-skills` repository at the same path (.github/pii-denylist.txt). Drift between the two repos is a policy violation; synchronization is an operational concern for the `agent-skills` maintainers and is out of scope for this repository's CI.
# Safe-to-publish policy: This shipped deny-list contains ZERO raw home addresses, ZERO zip codes, ZERO minor children's names, and ZERO phone numbers. Home-address and family-minor categories use marker comments + fork-local sentinels so that consumer forks can add their real tokens locally without committing PII to the public template.
# SAFE-TO-PUBLISH deny-list
```

### Labeled-section enumeration (harness constant `HEADER_LABELS`)

The Task 4 harness's `check_task3` gate iterates the following five labels and asserts each appears as a comment-line prefix somewhere in the header block:

1. `# Purpose:`
2. `# CI contract:`
3. `# How to extend:`
4. `# Mirror:`
5. `# Safe-to-publish policy:`

### Sentinel line (harness constant `SAFE_PUBLISH_SENTINEL`)

The literal comment line `# SAFE-TO-PUBLISH deny-list` MUST appear exactly once in the file, inside the header comment block, as the final `#` line before the first blank line. Harness probe: `grep -Fq '# SAFE-TO-PUBLISH deny-list' .github/pii-denylist.txt` matches; the sentinel does NOT appear in any pattern line (`grep -vE '^(#|$)' .github/pii-denylist.txt | grep -Fq 'SAFE-TO-PUBLISH'` returns exit 1).

### Byte budget (header block)

No explicit upper bound beyond the 200-byte-per-line cap. The header is typically 6–12 physical lines (five labels + sentinel, with optional blank-line padding if desired). Task 3's author emits the block verbatim as shown above — six physical lines of content, no padding between labels.

---

## Category section format and ordering

The file contains exactly six category sections, in this canonical order: `Names`, `Home Address`, `Family`, `Businesses`, `Blog & Public Content`, `Personal Scope Words` (AC3). Each section header matches the regex `^# === CATEGORY: <name> ===$`. Harness probe: `grep -c '^# === CATEGORY: ' .github/pii-denylist.txt` equals `6`.

The Task 3 author emits the six sections verbatim as the template below. Token ordering inside each section is locked (alphabetical within `Businesses` and `Personal Scope Words`; public-precedent ordering for `Names` and `Blog & Public Content`; marker-comment structure for `Home Address` and `Family`).

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

### Category-order enforcement (harness constant `EXPECTED_CATEGORIES`)

```
Names
Home Address
Family
Businesses
Blog & Public Content
Personal Scope Words
```

Task 4's `check_task3` gate walks the file with `awk`, records the sequence of `# === CATEGORY: <name> ===` headers encountered, and asserts the recorded sequence equals `EXPECTED_CATEGORIES` verbatim (six entries, exact spelling, exact case).

### Intra-category ordering rules

- **`Names`** (5 tokens): public-precedent ordering — template maintainer's first + last + nickname, then spouse first name, then secondary nickname. Order: `Derek`, `Neighbors`, `Deke`, `Laurie`, `Bobby`.
- **`Home Address`** (0 real tokens + 1 sentinel): five marker comments in spatial-address order (street → city → state → zip → apartment) followed by the fork-local sentinel `DEREK_HOME_ADDRESS_FORK_LOCAL`.
- **`Family`** (0 real tokens + 1 sentinel): two marker comments (spouse → children) followed by the fork-local sentinel `DEREK_FAMILY_FORK_LOCAL`.
- **`Businesses`** (11 tokens): alphabetized. Order: `Agile Weekly`, `Benji`, `Bodybuilding.com`, `Chiron`, `Flowtopic`, `Gangplank`, `Integrum`, `MasteryLab`, `Omarchy`, `Playrix`, `RevivaGo`.
- **`Blog & Public Content`** (4 tokens): domain-first, source-repo variants next, public location last. Order: `derekneighbors.com`, `gtd-life`, `gtdlife`, `Queen Creek`.
- **`Personal Scope Words`** (10 tokens): alphabetized. Order: `blog`, `cheyenne`, `daughter`, `dog`, `family`, `home`, `personal`, `son`, `wife`, `wyoming`.

---

## Per-category token inventory

Maps to AC3 + AC4 + the Dev Notes "Category → token mapping rationale" block. Total real tokens: 30 pattern lines (5 + 0 + 0 + 11 + 4 + 10 = 30) plus 2 fork-local sentinels (`DEREK_HOME_ADDRESS_FORK_LOCAL`, `DEREK_FAMILY_FORK_LOCAL`) = 32 pattern lines total. The sentinels are fork-customization anchors; they are pattern lines structurally but are not expected to match real content in the shipped template.

### `Names` (5 tokens)

| # | Token | Category rationale | Provenance |
| --- | --- | --- | --- |
| 1 | `Derek` | Template maintainer's first name, already public via blog byline. Covers AC4 `derek` (case-folded). | Story 2.1 banned-term regex. |
| 2 | `Neighbors` | Template maintainer's last name, already public via blog byline. Covers AC4 `neighbors`. | Story 2.1 banned-term regex. |
| 3 | `Deke` | Template maintainer's nickname, already public. Defence-in-depth backstop. | Story 3.3 fixed-string scrub set. |
| 4 | `Laurie` | Spouse first name, already public via blog byline (Story 3.3 precedent — explicitly marked safe-to-publish). NOT in `Family` category because public-precedent is already set. | Story 3.3 fixed-string scrub set. |
| 5 | `Bobby` | Spouse first-name variant referenced in Story 3.2 workspace.json exclusion commentary. Public-precedent already set. | Story 3.2 harness residue scrub. |

### `Home Address` (0 real tokens + 1 sentinel)

No real tokens. Category contains five marker comments enumerating expected sub-categories (`# marker: street address (number + street name)`, `# marker: city`, `# marker: state or state abbreviation`, `# marker: zip code`, `# marker: apartment / suite / unit number`) plus one fork-local customization comment and one sentinel pattern line:

| # | Token | Role |
| --- | --- | --- |
| 1 | `DEREK_HOME_ADDRESS_FORK_LOCAL` | Fork-customization anchor. Not a real token. Consumer forks replace this with their real street / city / zip tokens locally. |

Rationale: a real home street address in the deny-list file would itself be a PII leak — the very thing the deny-list is meant to prevent. See `## Safe-to-publish policy restatement` below.

### `Family` (0 real tokens + 1 sentinel)

No real tokens. Category contains two marker comments (`# marker: spouse first name (non-public)`, `# marker: child first names (MUST NOT be committed; fork-local only)`) plus one fork-local customization comment and one sentinel pattern line:

| # | Token | Role |
| --- | --- | --- |
| 1 | `DEREK_FAMILY_FORK_LOCAL` | Fork-customization anchor. Not a real token. Consumer forks replace this with their real non-public family tokens locally. |

Rationale: minor children's first names in the deny-list file would be a PII leak. Spouse first name (`Laurie`) is listed in `Names` category because public-precedent is already set via the blog byline.

### `Businesses` (11 tokens, alphabetized)

| # | Token | Category rationale | Provenance |
| --- | --- | --- | --- |
| 1 | `Agile Weekly` | Derek's past community / meetup, publicly documented. Two-word token including common English adjective. | Story 3.3 fixed-string scrub set. |
| 2 | `Benji` | Personal task-management tool / project, publicly associated with Derek. Covers AC4 `benji`. | Story 2.3 / 2.4 banned-term regex. |
| 3 | `Bodybuilding.com` | Derek's former employer, publicly on LinkedIn. Dotted-domain token (special case — `.` metacharacter does not affect Story 6.1's literal-substring semantics; Story 6.2 escapes at scan time). | Story 3.3 fixed-string scrub set. |
| 4 | `Chiron` | Derek's personal AI-agent naming convention. Mythological name. | Story 3.3 fixed-string scrub set. |
| 5 | `Flowtopic` | Derek's personal project. Covers AC4 `flowtopic`. | Story 2.2 banned-term regex. |
| 6 | `Gangplank` | Derek's past co-working community. | Story 3.3 fixed-string scrub set. |
| 7 | `Integrum` | Derek's past employer. Latin-derived word. | Story 3.3 fixed-string scrub set. |
| 8 | `MasteryLab` | Derek's past business / product. | Story 3.3 fixed-string scrub set. |
| 9 | `Omarchy` | Linux distro tied to Derek's personal setup. Neologism. | Story 3.3 fixed-string scrub set. |
| 10 | `Playrix` | Game company Derek references. | Story 3.3 fixed-string scrub set. |
| 11 | `RevivaGo` | Derek's fitness / nutrition business. Covers AC4 `revivago`. | Story 2.2 banned-term regex. |

### `Blog & Public Content` (4 tokens)

| # | Token | Category rationale | Provenance |
| --- | --- | --- | --- |
| 1 | `derekneighbors.com` | Derek's personal blog domain. Public URL. | Story 3.3 fixed-string scrub set. |
| 2 | `gtd-life` | Public GitHub repo name (template's personal ancestor). Covers AC4 `gtd-life`. | Story 2.3 banned-term regex. |
| 3 | `gtdlife` | Repo-name variant without the hyphen. Covers AC4 `gtdlife`. | Story 2.3 banned-term regex. |
| 4 | `Queen Creek` | Derek's city-level region of residence, already public in blog bio. NOT a street address. Two-word token. | Story 3.3 fixed-string scrub set. |

Post slugs and article titles are deliberately excluded — too numerous, too many false-positive compounds. If a specific blog-post title becomes problematic, it can be added in a follow-up one-line PR.

### `Personal Scope Words` (10 tokens, alphabetized)

| # | Token | Category rationale | Provenance |
| --- | --- | --- | --- |
| 1 | `blog` | Personal-output-channel scope word. Covers AC4 `blog`. | Story 2.3 banned-term regex. |
| 2 | `cheyenne` | Example PII geography token (Wyoming city). Covers AC4 `cheyenne`. | Story 2.2 banned-term regex. |
| 3 | `daughter` | Family scope word. Covers AC4 `daughter`. | Story 2.3 banned-term regex. |
| 4 | `dog` | Family / personal-life scope word. Covers AC4 `dog`. | Story 2.3 banned-term regex. |
| 5 | `family` | Personal-life scope word. Covers AC4 `family`. | Story 2.3 banned-term regex. |
| 6 | `home` | Personal-life scope word. Covers AC4 `home`. | Story 2.3 banned-term regex. |
| 7 | `personal` | Scope-enumeration scope word. Covers AC4 `personal`. Defence-in-depth against `scope: personal` or `tags: [..., personal]`. | Story 3.1 Phase-4 F4 addition. |
| 8 | `son` | Family scope word. Covers AC4 `son`. | Story 2.3 banned-term regex. |
| 9 | `wife` | Family scope word. Covers AC4 `wife`. | Story 2.3 banned-term regex. |
| 10 | `wyoming` | Example PII geography token (state). Covers AC4 `wyoming`. | Story 2.2 banned-term regex. |

All ten require boundary-guarded matching in CI (Story 6.2) so `homepage` does not false-match `home`, `personality` does not false-match `personal`, `familiar` does not false-match `family`, etc.

### Canonical 17-token coverage audit (harness constant `CANONICAL_17_TOKENS`)

The 17-token Stories 2.1 / 2.2 / 2.3 / 2.4 / 3.1 / 3.2 / 3.3 regex set MUST be covered by the union of pattern lines (case-folded, whitespace-trimmed, comments and blanks excluded). Coverage table:

| Canonical token (case-folded) | Covered by pattern line | Category |
| --- | --- | --- |
| `derek` | `Derek` | Names |
| `neighbors` | `Neighbors` | Names |
| `revivago` | `RevivaGo` | Businesses |
| `benji` | `Benji` | Businesses |
| `flowtopic` | `Flowtopic` | Businesses |
| `gtd-life` | `gtd-life` | Blog & Public Content |
| `gtdlife` | `gtdlife` | Blog & Public Content |
| `wyoming` | `wyoming` | Personal Scope Words |
| `cheyenne` | `cheyenne` | Personal Scope Words |
| `family` | `family` | Personal Scope Words |
| `home` | `home` | Personal Scope Words |
| `blog` | `blog` | Personal Scope Words |
| `wife` | `wife` | Personal Scope Words |
| `son` | `son` | Personal Scope Words |
| `daughter` | `daughter` | Personal Scope Words |
| `dog` | `dog` | Personal Scope Words |
| `personal` | `personal` | Personal Scope Words |

Harness `check_task4` iterates `CANONICAL_17_TOKENS` and asserts `grep -Fiq "${token}" .github/pii-denylist.txt` returns exit 0 for every token (case-insensitive fixed-string match against the whole file).

### Defence-in-depth 12-token coverage (AC4 second-bullet set)

| Token | Category |
| --- | --- |
| `Chiron` | Businesses |
| `MasteryLab` | Businesses |
| `Agile Weekly` | Businesses |
| `Gangplank` | Businesses |
| `Integrum` | Businesses |
| `Omarchy` | Businesses |
| `Playrix` | Businesses |
| `derekneighbors.com` | Blog & Public Content |
| `Queen Creek` | Blog & Public Content |
| `Deke` | Names |
| `Laurie` | Names |
| `Bobby` | Names |

Harness `check_task4` asserts each of these 12 fixed-string tokens matches via `grep -Fq`.

### Total denied-vocabulary cardinality

`17 ∪ 12 = 29` distinct tokens (case-folded), consistent with AC4's "at least 29" threshold. Plus `Bodybuilding.com` (Businesses, AC3 list-member) for a total of 30 real tokens visible across the six categories. Plus 2 fork-local sentinels = 32 pattern lines in the shipped file.

---

## Safe-to-publish policy restatement

The shipped deny-list at `.github/pii-denylist.txt` is committed to the public open-source template. Anything in the file is therefore itself public. The deny-list is a list of patterns that MUST NOT appear elsewhere in the shipped template — so the deny-list must not paradoxically leak PII by containing it.

### Zero-PII-in-the-denylist-itself invariants (AC5)

- **ZERO real home street addresses.** No number-space-word-space-`<street-suffix>` pattern in any pattern line. Probe: `grep -vE '^(#|$)' .github/pii-denylist.txt | grep -E '^[0-9]+ [A-Za-z]+ (St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Ln|Lane|Way|Dr|Drive|Ct|Court|Pl|Place)$' | wc -l` equals `0`.
- **ZERO five-digit US zip codes.** Probe: `grep -vE '^(#|$)' .github/pii-denylist.txt | grep -E '^[0-9]{5}(-[0-9]{4})?$' | wc -l` equals `0`.
- **ZERO minor children's first names.** Enforced by positive allowlist (the `Names` section lists exactly `Derek`, `Neighbors`, `Deke`, `Laurie`, `Bobby` — known public tokens). The kids' names are deliberately not written anywhere in the file; there is no negative-scan probe because the kids' names are not a deterministic set enumerable in a public harness.
- **ZERO raw phone numbers.** Probe: `grep -E '\+?[0-9]{3}[-. ][0-9]{3}[-. ][0-9]{4}' .github/pii-denylist.txt | wc -l` equals `0`.
- **ZERO `@` characters.** Probe: `grep -Fq '@' .github/pii-denylist.txt` returns exit 1. No email addresses anywhere — not even the public blog domain is written as `derek@derekneighbors.com`. Public domains `derekneighbors.com` and `Bodybuilding.com` are written without the `@` prefix.

### In-file self-documenting sentence

The explicit sentence `# SAFE-TO-PUBLISH deny-list` appears inside the header comment block so auditors and future BMAD agents can confirm the no-PII-in-this-file policy with a single `grep -Fq '# SAFE-TO-PUBLISH deny-list' .github/pii-denylist.txt`. Both the sentence presence AND the negative-scan invariants above must hold.

### Category-marker + fork-local-sentinel rationale

For `Home Address` and `Family`, the categories of tokens that would themselves leak PII if committed, Story 6.1 ships:

1. **Marker comments** enumerating the sub-categories (e.g. `# marker: zip code`, `# marker: child first names (MUST NOT be committed; fork-local only)`). These document the intent to future maintainers so no one "helpfully" fills in real tokens.
2. **Fork-local customization comment** (`# Fork-local customization: replace the sentinel below with real tokens in a private fork.`).
3. **Fork-local sentinel pattern line** (`DEREK_HOME_ADDRESS_FORK_LOCAL`, `DEREK_FAMILY_FORK_LOCAL`) as a grep-visible anchor for consumer-fork extension workflows.

Consumer forks (Vixxo employee clones, mirrored `agent-skills` checkout) add their real address / family tokens in their private fork by replacing the sentinel with real tokens in a local `.gitignore`-d override file, or via Actions secrets, or via a private-fork maintenance branch. That extension mechanism is out of scope for Story 6.1 and will be addressed in a follow-up story if Vixxo needs centralized fork inheritance.

### Why this approach (Approach B) over concrete-tokens-in-shipped-file (Approach A)

The SM considered Approach A (concrete real tokens shipped in every category) and rejected it: shipping real home addresses and minor children's names in the public template IS a PII leak, and would force every consumer fork to inherit Derek's PII. Approach B preserves the safe-to-publish policy while still providing day-1 CI coverage for the publicly-known Derek-associated tokens (names, businesses, blog domains, scope words) that constitute the majority of the risk surface. Fork-local Home Address / Family coverage is the consumer's responsibility.

This decision is codified in AC3 (categories with markers), AC5 (no raw PII), AC6 (header policy block), and AC9 (`## What does NOT belong in this file` in the doc). Any future reversal requires a separate story with its own AC set.

---

## CI consumption contract (forward reference to Story 6.2)

Story 6.1 does NOT implement the CI workflow. Story 6.2 owns `.github/workflows/pii-scan.yml` (or similarly named). Story 6.1 fixes the contract below so Story 6.2 has a deterministic consumption surface.

### Pattern loading

Story 6.2 loads the pattern set via:

```
grep -vE '^(#|$)' .github/pii-denylist.txt
```

This strips comment lines (starting with `#` in column 1) and blank lines, yielding one literal substring per line. Expected cardinality at Story 6.1 freeze: 32 pattern lines (30 real tokens + 2 fork-local sentinels).

### Per-pattern regex wrapping

For each loaded pattern `P`, Story 6.2 constructs the POSIX-ERE regex:

```
(^|[^A-Za-z])P($|[^A-Za-z])
```

This is the Stories 2.1–3.3 harness-internal boundary-guard idiom, now externalized. Invoked with `grep -iE` for case-insensitive matching. BSD-grep and GNU-grep compatible. No `\b`, `\<`, `\>`, or PCRE.

### Regex-metacharacter handling

Pattern lines in Story 6.1's file may contain regex metacharacters (notably `.` in `derekneighbors.com` and `Bodybuilding.com`). Story 6.2's workflow is responsible for escaping metacharacters before wrapping in the boundary guard. Story 6.1's file does NOT pre-escape — that would reduce human readability and complicate future edits. The contract line in the header states this explicitly: "Each line is a literal substring."

### Scan scope and exclusions

Story 6.2's workflow scans the PR diff (preferred) or the full tree (fallback) with `grep -riE` or equivalent. Exclusions:

- `.git/` (not a real concern — GitHub-hosted scan will not see `.git/` history).
- `.github/pii-denylist.txt` itself (the deny-list MUST NOT match itself).
- `docs/pii-denylist.md` (the policy doc also contains token references as documentation).
- `_bmad-output/implementation-artifacts/**/*.md` that discuss Derek-audit prose as part of story-file evidence (explicit token enumerations are policy-documentation, not PII leaks).
- `_bmad-output/implementation-artifacts/tests/*.sh` harnesses (contain explicit token regex sets).
- `node_modules/` if present.

Final exclusion list is Story 6.2's to finalize. Story 6.1's file format does NOT encode the exclusion set — that belongs in the workflow file.

### Failure mode

On any match, Story 6.2's workflow fails with a non-zero exit, prints the offending file + line + matched pattern to the workflow log, and blocks the PR merge (standard GitHub-Actions required-status-check mechanism).

### Performance budget

Story 6.2's workflow MUST complete in under 30 seconds (Epic 6 Story 6.2 AC). The deny-list's simplicity (≤ 32 pattern lines, sub-200-byte lines, no regex metacharacters pre-embedded) makes this trivial — a full-tree `grep -riE` across ~100 files with ~32 boundary-guarded patterns completes in single-digit seconds on `ubuntu-latest`.

### Header-block restatement

The `# CI contract:` labeled line in the header comment block (see `## Header comment block (exact labeled sections)`) restates points (1)–(5) above in compressed form so any future reviewer can understand the file's contract without opening Story 6.2's workflow.

---

## Negative-scan patterns (AC5 content-scrub probes)

Task 4's `check_task4` gate applies the following four negative-scan probes to the deny-list file. All four MUST return zero matches (or exit 1 for the presence-check probe). Listed verbatim:

### Probe 1 — Street addresses (must return zero matches)

```
grep -Eq '^[0-9]+ [A-Za-z]+ (St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Ln|Lane|Way|Dr|Drive|Ct|Court|Pl|Place)$'
```

Applied to the stripped pattern-lines stream (`grep -vE '^(#|$)' .github/pii-denylist.txt`). The probe matches patterns like `123 Main St`, `456 Elm Road`, etc. Zero matches in any pattern line of the shipped file.

### Probe 2 — US zip codes (must return zero matches)

```
grep -Eq '^[0-9]{5}(-[0-9]{4})?$'
```

Applied to the stripped pattern-lines stream. The probe matches five-digit zip codes and ZIP+4 extensions. Zero matches in any pattern line of the shipped file.

### Probe 3 — Phone numbers (must return zero matches)

```
grep -Eq '\+?[0-9]{3}[-. ][0-9]{3}[-. ][0-9]{4}'
```

Applied to the whole file (not just the stripped pattern-lines stream, because a phone number in a comment would also be a leak). The probe matches North-American-style phone numbers with `-`, `.`, or space separators, optional `+` country-code prefix. Zero matches anywhere in the shipped file.

### Probe 4 — Email `@` symbol (must return zero matches)

```
grep -Fq '@' .github/pii-denylist.txt
```

Applied to the whole file. MUST return exit `1` (no match anywhere in the file). The public business/blog domain tokens `derekneighbors.com` and `Bodybuilding.com` are written without any `@` prefix; no email addresses appear anywhere, not even in comments or header prose.

### Additional assertions (fold-in with the four negative-scan probes)

- **Safe-to-publish sentinel presence** (inverse of negative-scan): `grep -Fq '# SAFE-TO-PUBLISH deny-list' .github/pii-denylist.txt` MUST match.
- **Anti-self-match guard on the sentinel**: `grep -vE '^(#|$)' .github/pii-denylist.txt | grep -Fq 'SAFE-TO-PUBLISH'` MUST return exit 1 — confirms the sentinel lives only in the header comment block, never in a pattern line (where it would then match itself during Story 6.2's scan and cause a false positive).
- **Positive coverage (17 tokens)**: iterate `CANONICAL_17_TOKENS` — each token MUST resolve to at least one pattern-line hit via `grep -Fiq "${token}" .github/pii-denylist.txt`.
- **Defence-in-depth coverage (12 tokens)**: iterate the `Chiron`, `MasteryLab`, `Agile Weekly`, `Gangplank`, `Integrum`, `Omarchy`, `Playrix`, `derekneighbors.com`, `Queen Creek`, `Deke`, `Laurie`, `Bobby` set — each MUST match via `grep -Fq`.

---

## Doc file shape (docs/pii-denylist.md H2 sections)

Target file: `docs/pii-denylist.md`. Maps to AC9 + AC10. UTF-8, LF, trailing newline, non-empty. Byte budget: 1–4 KB target, no hard upper bound.

### Canonical H2 section list (7 sections, in canonical order)

1. `## Purpose`
2. `## File location and format`
3. `## Categories`
4. `## CI consumption (Story 6.2 preview)`
5. `## How to extend`
6. `` ## Relationship to the mirrored `agent-skills` repo ``
7. `## What does NOT belong in this file`

Harness probe (`check_task3`): `grep -c '^## ' docs/pii-denylist.md` equals `7`; each of the seven H2 headings matches verbatim via `grep -Fxq`.

### Per-section content requirements

- **`## Purpose`**: one-paragraph statement of the single-source-of-truth intent. Restates the header comment block's `# Purpose:` line in prose, with cross-references to Epic 6 Story 6.1 + Story 6.2 and to NFR1 "No Derek PII in any shipped content".
- **`## File location and format`**: restates the AC2 format contract — comments starting with `#`, blank lines allowed, one literal substring per pattern line, category headers in the exact `# === CATEGORY: <name> ===` form. A fenced code block showing the category-header shape + a pattern line is encouraged for readability. References `.github/pii-denylist.txt` as the canonical path.
- **`## Categories`**: enumerates all six AC3 categories with a one-line description per category. The descriptions MAY restate the per-category section descriptions from the deny-list file verbatim but should be human-readable prose. Order MUST match `EXPECTED_CATEGORIES`.
- **`## CI consumption (Story 6.2 preview)`**: forward-references Story 6.2's workflow. Restates the five-point CI contract from `## CI consumption contract (forward reference to Story 6.2)` above in prose. Notes that Story 6.1 does NOT implement the workflow — only the deny-list file.
- **`## How to extend`**: restates the header comment block's `# How to extend:` line as a step-by-step procedure: (1) identify correct category, (2) add token in alphabetical order within the category, (3) open PR against `main`, (4) write one-line commit message explaining why, (5) any NEW category requires bumping AC3 in a future story.
- **`` ## Relationship to the mirrored `agent-skills` repo ``**: restates the header comment block's `# Mirror:` line in prose. Notes that the mirror is maintained by the `agent-skills` maintainers operationally; this repo's CI does NOT enforce mirror synchronization.
- **`## What does NOT belong in this file`**: restates AC5's safe-to-publish policy — no raw addresses, no zip codes, no minor children's names, no phone numbers, no `@`-containing email addresses, no secrets / credentials (secrets belong in `.gitignore` + `.env.example`, not here). Explicitly notes the category-marker + fork-local-sentinel approach for `Home Address` and `Family`.

### Doc-file-itself safe-to-publish invariant

The doc file MUST satisfy the same AC5 bar as the deny-list file: zero real home addresses, zero zip codes, zero minor children's names, zero phone numbers, zero `@` characters. Harness probe (`check_task3`): the four AC5 probes applied to `docs/pii-denylist.md` return zero matches.

### README.md cross-reference (AC10)

`README.md` contains a one-line (or up to 5-line) addition under the existing `## Help` section, or a new `## Guardrails` H2 after `## Help`, that mentions BOTH `.github/pii-denylist.txt` AND `docs/pii-denylist.md`. Line format is Dev's choice — example: "PII guardrail: see `.github/pii-denylist.txt` (deny-list file) and `docs/pii-denylist.md` (policy doc). Enforced in CI by Story 6.2's workflow." README line count MUST NOT decrease; grows by 1–5 lines.

Harness probe (`check_task3`): `grep -Fq '.github/pii-denylist.txt' README.md` matches AND `grep -Fq 'docs/pii-denylist.md' README.md` matches.

---

## Cross-AC coverage map

| AC | Lock |
| --- | --- |
| AC1 | `## Deny-list file shape` (existence + non-empty + LF + trailing newline + git-tracked). |
| AC2 | `## Deny-list file shape` (line-kind classification rule, 200-byte line budget, no tabs, no trailing spaces) + `## Header comment block (exact labeled sections)` (header block with `# === CATEGORY: <name> ===` micro-syntax documented). |
| AC3 | `## Category section format and ordering` (six canonical categories in order) + `## Per-category token inventory` (per-category required tokens with rationale) + `## Safe-to-publish policy restatement` (category-marker structure for `Home Address` and `Family`). |
| AC4 | `## Per-category token inventory` (17-token coverage audit + 12-token defence-in-depth coverage — total ≥ 29 distinct tokens). |
| AC5 | `## Safe-to-publish policy restatement` (zero-PII-in-the-denylist-itself invariants) + `## Negative-scan patterns (AC5 content-scrub probes)` (four verbatim probes) + safe-to-publish sentinel presence + anti-self-match guard. |
| AC6 | `## Header comment block (exact labeled sections)` (five labeled sections + sentinel line, verbatim). |
| AC7 | `## CI consumption contract (forward reference to Story 6.2)` (contract the Task 4 harness validates) — harness implementation itself is Task 4 scope, not Task 2 blueprint scope. |
| AC8 | Referenced via `## CI consumption contract (forward reference to Story 6.2)` regression invocation — the ten-predecessor regression chain is Task 6 scope; the blueprint only establishes the contract. |
| AC9 | `## Doc file shape (docs/pii-denylist.md H2 sections)` (seven canonical H2 sections in order + per-section content requirements + doc-file safe-to-publish invariant). |
| AC10 | `## Doc file shape (docs/pii-denylist.md H2 sections)` (README.md cross-reference sub-section). |
| AC11 | N/A at blueprint level; `sprint-status.yaml` edit is Task 7 scope. |

---

## Task 4 harness probes (consumed from this blueprint)

Task 4's `check_task2` gate MUST assert the following about this blueprint file (`_bmad-output/implementation-artifacts/tests/story-6-1-canonical-blueprint.md`):

- File exists, non-empty, LF-only, trailing newline.
- Title `# Story 6.1 Canonical Blueprint` appears on line 1.
- Each of the following H2 sections appears verbatim via `grep -Fxq`:
  - `## Deny-list file shape`
  - `## Header comment block (exact labeled sections)`
  - `## Category section format and ordering`
  - `## Per-category token inventory`
  - `## Safe-to-publish policy restatement`
  - `## CI consumption contract (forward reference to Story 6.2)`
  - `## Negative-scan patterns (AC5 content-scrub probes)`
  - `## Doc file shape (docs/pii-denylist.md H2 sections)`
- The verbatim header-block fenced code in `## Header comment block (exact labeled sections)` contains the five labeled prefixes (`# Purpose:`, `# CI contract:`, `# How to extend:`, `# Mirror:`, `# Safe-to-publish policy:`) and the sentinel `# SAFE-TO-PUBLISH deny-list`.
- The verbatim category template in `## Category section format and ordering` contains all six `# === CATEGORY: <name> ===` headers in canonical order.

The blueprint is consumed as locked input by Task 3 (deny-list authoring) and Task 5 (doc authoring). Any deviation between this blueprint and the files authored in Tasks 3 / 5 is a bug and fails the Task 4 harness.
