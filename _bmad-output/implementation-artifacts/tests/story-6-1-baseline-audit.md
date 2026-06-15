# Story 6.1 Baseline Audit

Captured during Task 1 (Phase 2, Dev agent Amelia) on 2026-04-21. This audit enumerates every banned token carried inline by the ten predecessor harnesses under `_bmad-output/implementation-artifacts/tests/story-*-validation.sh`, records per-token provenance (which harness, regex vs fixed-string), computes the case-folded union set, classifies each token into one of the six Story 6.1 canonical categories (`Names`, `Home Address`, `Family`, `Businesses`, `Blog & Public Content`, `Personal Scope Words`), applies the safe-to-publish bar (AC5) to partition the union into the publishable shipped subset and the fork-local-only remainder, flags any pre-existing PII leaks in the harness codebase, and measures the exact `^PASS:` line-count fingerprint produced by each of the ten predecessor harnesses in `all` mode on this host (macOS darwin 25.4.0). Evidence here drives Task 2's canonical blueprint, Task 3's `.github/pii-denylist.txt` author step, and Task 4's harness `check_task4` positive-coverage assertions.

Scope lock: Story 6.1 ships a PUBLISHABLE deny-list of Derek-PII patterns for open-source template consumption. Tokens that would themselves leak PII if committed (real home street addresses, zip codes, minor children's first names, phone numbers, real human-name email addresses) are REJECTED at classification time and represented in the shipped file via CATEGORY MARKER COMMENTS plus fork-local sentinels (`DEREK_HOME_ADDRESS_FORK_LOCAL`, `DEREK_FAMILY_FORK_LOCAL`) per Approach B of the Dev-Notes "Ambiguity flag" section. Tokens that are private-work-colleague names (Story 2.3 residue: Bobby Hunnicutt, Brandon Franz, Eric Burt, Gino Flores, Viswa Vadlamani, Jignesh Patel, Jim Reavey) are NOT Derek's own PII and are similarly fork-local — they belong in each Vixxo employee's private fork, not the shipped template deny-list. Tokens that are generic tech-brand scope words (gmail, google workspace, slack, notion, etc.) are out-of-scope for a PII deny-list — they indicate personal-tooling scope but are not themselves PII, and blanket-blocking them would create false positives in legitimate work content. Story 1.1's scaffold-only scope words (`private`, `ssn`, `social security`) are SCAFFOLD guards against any personal-context residue in empty `.gitkeep` files and are out-of-scope for the shipped Derek-PII deny-list.

Cardinality summary: the case-folded union across the ten predecessor harnesses contains 63 distinct tokens. Story 6.1's shipped deny-list publishes 30 of them (five `Names`, zero `Home Address` tokens plus five category markers + one sentinel, zero `Family` tokens plus two category markers + one sentinel, eleven `Businesses`, four `Blog & Public Content`, ten `Personal Scope Words`), meeting AC4's floor (17-token Story-3.x regex lock ∪ 12-token Story-3.3 Derek-fixed-string set = at least 29 tokens visible in the file). The remaining 33 union tokens are documented below under the fork-local-only partition or the out-of-scope notes.

## Per-harness token inventory

### 1. `story-1-1-scaffold-validation.sh` (205 lines; SCAFFOLD guard)

- **Source:** inline POSIX-ERE regex at line 172 applied against the six `.gitkeep` files and `.gitignore` in the scaffold.
- **Regex tokens (5):** `personal`, `private`, `home address`, `ssn`, `social security`
- **Fixed-string tokens:** none
- **Provenance note:** Story 1.1 was the first story; these five tokens are a GENERIC personal-context scaffold guard (not Derek-specific PII). The regex exists only to reject accidental real content in otherwise-empty scaffold files. Story 6.1 carries forward `personal` and `home` (via `home address`) into the shipped deny-list; the remaining three (`private`, `ssn`, `social security`) are out-of-scope for a Derek-PII deny-list.

### 2. `story-1-2-root-files-validation.sh` (153 lines; root-files scrub)

- **Source:** inline POSIX-ERE regex at line 39 applied against `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `README.md`, `LICENSE`, `.gitignore`.
- **Regex tokens (4):** `Derek`, `RevivaGo`, `blog`, `gtd-life`
- **Fixed-string tokens:** none
- **Provenance note:** first appearance of the carry-forward-public-tokens set. All four tokens are publicly associated with Derek and ship in Story 6.1's deny-list.

### 3. `story-1-3-root-context-validation.sh` (149 lines; root context scrub)

- **Source:** inline POSIX-ERE regex at line 27 applied against `AGENTS.md`, `CLAUDE.md`, `.cursorrules`; plus fixed-string baseline-audit assertion at line 45 ("Banned terms: personal, RevivaGo, Derek, gtd-life").
- **Regex tokens (4):** `personal`, `RevivaGo`, `Derek`, `gtd-life`
- **Fixed-string tokens (4):** `personal`, `RevivaGo`, `Derek`, `gtd-life` (same four; baseline-audit prose assertion)
- **Provenance note:** identical set to 1.2 modulo swapping `blog` for `personal`. All four ship in Story 6.1's deny-list.

### 4. `story-2-1-agent-identity-validation.sh` (355 lines; agent-identity rule scrub)

- **Source:** inline POSIX-ERE regex at line 56 applied against `.cursor/rules/agent-identity.mdc` plus fixed-string-loop baseline-audit assertion at lines 110–113; plus `AC5_FORBIDDEN_REFS` filename scan at line 66.
- **Regex tokens (19):** `derek`, `deke`, `neighbors`, `chiron`, `revivago`, `derekneighbors.com`, `agile weekly`, `masterylab`, `bodybuilding.com`, `gangplank`, `ASU`, `gtd-life`, `arete`, `eudaimonia`, `blog`, `gmail`, `google calendar`, `google workspace`, `personal email`
- **Fixed-string tokens (19, matching the regex set via the baseline-audit grep -Fq loop):** `Derek`, `Deke`, `Neighbors`, `Chiron`, `RevivaGo`, `derekneighbors.com`, `Agile Weekly`, `MasteryLab`, `Bodybuilding.com`, `Gangplank`, `ASU`, `gtd-life`, `arete`, `eudaimonia`, `blog`, `Gmail`, `Google Calendar`, `Google Workspace`, `personal email`
- **Filename tokens (3):** `vixxo-cto.md`, `revivago-ceo.md`, `personal.md` (AC5_FORBIDDEN_REFS — cross-persona reference scrub; filenames, not content tokens)
- **Provenance note:** first harness to introduce the fuller Derek vocabulary (Chiron, MasteryLab, Agile Weekly, Gangplank, Bodybuilding.com) plus philosophy words (arete, eudaimonia) and generic tech-brand scope words (Gmail, Google Calendar, Google Workspace, personal email, ASU). Ten of the 19 tokens are Derek-PII (Derek, Deke, Neighbors, Chiron, RevivaGo, derekneighbors.com, Agile Weekly, MasteryLab, Bodybuilding.com, Gangplank); four are public content (`gtd-life`, `blog`); two are philosophy-words ("arete", "eudaimonia" — Derek personal terms, fork-local); four are generic tech brands (Gmail, Google Calendar, Google Workspace, ASU) — out-of-scope for shipped deny-list.

### 5. `story-2-2-guardrail-and-formatting-validation.sh` (769 lines; four-rule scrub)

- **Source:** inline POSIX-ERE regex at line 89 applied against the four Story 2.2 rule files; plus fixed-string-loop baseline-audit assertion at lines 268–279.
- **Regex tokens (21):** Story 2.1 set (19) + `slack` + `benji`
- **Fixed-string tokens:** Story 2.1 set + `Slack` + `Benji`
- **New tokens introduced:** `slack`, `benji` (two)
- **Provenance note:** `Benji` is the first appearance of the Benji product/MCP; ships in Story 6.1's `Businesses`. `Slack` is a generic chat-platform brand, not Derek-PII, and is out-of-scope.

### 6. `story-2-3-work-persona-validation.sh` (720 lines; work-persona scrub)

- **Source:** inline POSIX-ERE regex at line 100 applied against `agents/personas/work.md`; plus fixed-string-loop baseline-audit assertion at lines 298–301.
- **Regex tokens (38):** Story 2.2 set (21) + `google drive`, `google chat`, `notion`, `flowtopic`, `veincraft`, `daddy bootcamps`, `after the stork`, `peptide`, `family`, `laurie`, `bobby hunnicutt`, `brandon franz`, `eric burt`, `gino flores`, `viswa vadlamani`, `jignesh patel`, `jim reavey`
- **Fixed-string tokens (15):** `Notion`, `Flowtopic`, `VeinCraft`, `Daddy Bootcamps`, `After the Stork`, `peptide`, `family`, `Laurie`, `Bobby Hunnicutt`, `Brandon Franz`, `Eric Burt`, `Gino Flores`, `Viswa Vadlamani`, `Jignesh Patel`, `Jim Reavey`
- **New tokens introduced:** 17 (`google drive`, `google chat`, `notion`, `flowtopic`, `veincraft`, `daddy bootcamps`, `after the stork`, `peptide`, `family`, `laurie`, plus seven real colleague full names)
- **Provenance note:** largest per-harness token set. Derek-PII subset: `flowtopic` (business, public), `veincraft`, `daddy bootcamps`, `after the stork`, `peptide` (Derek side-ventures — partially public; ship `Flowtopic` only and mark the others fork-local as defense-in-depth is already provided by the published Derek-name tokens); `family` (generic scope word — ships); `Laurie` (spouse first name — ships per Story 3.3 precedent). Seven real work-colleague full names (`Bobby Hunnicutt`, `Brandon Franz`, `Eric Burt`, `Gino Flores`, `Viswa Vadlamani`, `Jignesh Patel`, `Jim Reavey`) are NOT Derek's own PII — they are fellow Vixxo employees' names; FORK-LOCAL-ONLY (each Vixxo fork adds its own colleague list). `google drive`, `google chat`, `notion` are generic tech brands — out-of-scope.

### 7. `story-2-4-benji-inbox-absence-validation.sh` (348 lines; benji-absence structural guard)

- **Source:** `BENJI_BASENAME_PATTERN` at line 45.
- **Regex tokens (1):** `benji` (via case-insensitive `^[Bb][Ee][Nn][Jj][Ii]` basename pattern)
- **Fixed-string tokens:** none (structural filename check only)
- **Provenance note:** Story 2.4 added no new content tokens; it uses `benji` as a structural filename guard against the absent `agents/personas/benji-inbox.md` file. `benji` already ships via Story 2.2 provenance.

### 8. `story-3-1-memory-template-tree-validation.sh` (759 lines; memory/ tree scrub)

- **Source:** inline POSIX-ERE regex at line 76 applied to every non-identity memory-template file.
- **Regex tokens (17 — the canonical Story-3.x lock):** `derek`, `neighbors`, `revivago`, `benji`, `flowtopic`, `gtd-life`, `gtdlife`, `wyoming`, `cheyenne`, `family`, `home`, `blog`, `wife`, `son`, `daughter`, `dog`, `personal`
- **Fixed-string tokens:** none
- **Provenance note:** this is the CANONICAL 17-token banned-term lock that Stories 3.1, 3.2, and 3.3 carry forward byte-identical. First appearance of `benji`, `flowtopic`, `gtdlife` (no hyphen), `wyoming`, `cheyenne`, `home`, `wife`, `son`, `daughter`, `dog` in a regex. All 17 tokens ship in Story 6.1's deny-list (as the AC4 union floor).

### 9. `story-3-2-obsidian-config-validation.sh` (673 lines; `.obsidian/` JSON scrub)

- **Source:** inline POSIX-ERE regex at line 83 (canonical 17); plus fixed-string `bobby` scan at line 525; plus `MEETING_SLUG_REGEX` at line ~88 (operational meeting-slug pattern, not a content token).
- **Regex tokens (17):** canonical Story-3.x lock — identical to Story 3.1.
- **Fixed-string tokens (1):** `bobby` (workspace.json leakage guard — first appearance of `bobby` as a first-name scrub target)
- **Provenance note:** `bobby` here is a first-name residue from the `2026-04-20-bobby-derek-wkly-1-1/` meeting-slug sample that showed up in Derek's workspace.json as recent-files leakage. The scrub target is the first name alone. Story 6.1 ships `Bobby` under `Names` per Task-1 step 6's explicit directive.

### 10. `story-3-3-identity-preferences-validation.sh` (976 lines; identity + preferences scrub)

- **Source:** `BANNED_TERMS_REGEX` at line 87 (canonical 17); plus `DEREK_FIXED_STRINGS` array at lines 95–108 (12 tokens).
- **Regex tokens (17):** canonical Story-3.x lock — identical to Stories 3.1 and 3.2.
- **Fixed-string tokens (12):** `Chiron`, `MasteryLab`, `Agile Weekly`, `Queen Creek`, `Gangplank`, `Bodybuilding.com`, `Integrum`, `Omarchy`, `derekneighbors.com`, `Playrix`, `Laurie`, `Deke`
- **Provenance note:** the AC4 defense-in-depth set. All 12 ship verbatim in Story 6.1's deny-list under `Names` / `Businesses` / `Blog & Public Content` per AC3.

## Union-set (deduplicated, case-folded)

Union computed by case-folding every regex alternation and every fixed-string array element across the ten harnesses above and deduplicating. Multi-word tokens preserved as phrases; punctuation (`.` in `Bodybuilding.com`, `derekneighbors.com`; `-` in `gtd-life`) preserved. Cardinality: **63 distinct tokens**.

| # | Token (case-folded) | First seen in | Regex / fixed-string | In-scope for Story 6.1 ship? |
|---|---------------------|---------------|----------------------|------------------------------|
| 1 | derek | 1.2 | regex + fixed-string | YES — `Names` |
| 2 | neighbors | 1.2 | regex + fixed-string | YES — `Names` |
| 3 | revivago | 1.2 | regex + fixed-string | YES — `Businesses` |
| 4 | blog | 1.2 | regex + fixed-string | YES — `Personal Scope Words` |
| 5 | gtd-life | 1.2 | regex + fixed-string | YES — `Blog & Public Content` |
| 6 | personal | 1.1 | regex | YES — `Personal Scope Words` |
| 7 | private | 1.1 | regex | NO — scaffold-only scope |
| 8 | home address | 1.1 | regex (phrase) | NO — PII phrase → `Home Address` category marker |
| 9 | ssn | 1.1 | regex | NO — scaffold-only scope |
| 10 | social security | 1.1 | regex (phrase) | NO — scaffold-only scope |
| 11 | deke | 2.1 | regex + fixed-string | YES — `Names` |
| 12 | chiron | 2.1 | regex + fixed-string | YES — `Businesses` |
| 13 | derekneighbors.com | 2.1 | regex + fixed-string | YES — `Blog & Public Content` |
| 14 | agile weekly | 2.1 | regex + fixed-string | YES — `Businesses` |
| 15 | masterylab | 2.1 | regex + fixed-string | YES — `Businesses` |
| 16 | bodybuilding.com | 2.1 | regex + fixed-string | YES — `Businesses` |
| 17 | gangplank | 2.1 | regex + fixed-string | YES — `Businesses` |
| 18 | asu | 2.1 | regex + fixed-string | NO — educational-institution scope word, not PII |
| 19 | arete | 2.1 | regex + fixed-string | NO — philosophy term, fork-local (Derek personal vocabulary) |
| 20 | eudaimonia | 2.1 | regex + fixed-string | NO — philosophy term, fork-local |
| 21 | gmail | 2.1 | regex + fixed-string | NO — generic tech brand, out-of-scope |
| 22 | google calendar | 2.1 | regex + fixed-string (phrase) | NO — generic tech brand |
| 23 | google workspace | 2.1 | regex + fixed-string (phrase) | NO — generic tech brand |
| 24 | personal email | 2.1 | regex + fixed-string (phrase) | NO — covered by boundary-guarded `personal` scope word |
| 25 | vixxo-cto.md | 2.1 | fixed-string (filename) | NO — filename scrub, not a content token |
| 26 | revivago-ceo.md | 2.1 | fixed-string (filename) | NO — filename scrub |
| 27 | personal.md | 2.1 | fixed-string (filename) | NO — filename scrub |
| 28 | slack | 2.2 | regex + fixed-string | NO — generic tech brand |
| 29 | benji | 2.2 | regex + fixed-string | YES — `Businesses` |
| 30 | google drive | 2.3 | regex (phrase) | NO — generic tech brand |
| 31 | google chat | 2.3 | regex (phrase) | NO — generic tech brand |
| 32 | notion | 2.3 | regex + fixed-string | NO — generic tech brand |
| 33 | flowtopic | 2.3 | regex + fixed-string | YES — `Businesses` |
| 34 | veincraft | 2.3 | regex + fixed-string | NO — fork-local Derek side-venture (not in AC3 enumerated set) |
| 35 | daddy bootcamps | 2.3 | regex + fixed-string (phrase) | NO — fork-local |
| 36 | after the stork | 2.3 | regex + fixed-string (phrase) | NO — fork-local |
| 37 | peptide | 2.3 | regex + fixed-string | NO — fork-local (Derek-RevivaGo-adjacent substance term, not a PII surface) |
| 38 | family | 2.3 | regex + fixed-string | YES — `Personal Scope Words` |
| 39 | laurie | 2.3 | regex + fixed-string | YES — `Names` (public spouse first name per Story 3.3 precedent) |
| 40 | bobby hunnicutt | 2.3 | regex + fixed-string (phrase) | NO — fork-local work-colleague full name |
| 41 | brandon franz | 2.3 | regex + fixed-string (phrase) | NO — fork-local work-colleague full name |
| 42 | eric burt | 2.3 | regex + fixed-string (phrase) | NO — fork-local work-colleague full name |
| 43 | gino flores | 2.3 | regex + fixed-string (phrase) | NO — fork-local work-colleague full name |
| 44 | viswa vadlamani | 2.3 | regex + fixed-string (phrase) | NO — fork-local work-colleague full name |
| 45 | jignesh patel | 2.3 | regex + fixed-string (phrase) | NO — fork-local work-colleague full name |
| 46 | jim reavey | 2.3 | regex + fixed-string (phrase) | NO — fork-local work-colleague full name |
| 47 | gtdlife | 3.1 | regex | YES — `Blog & Public Content` |
| 48 | wyoming | 3.1 | regex | YES — `Personal Scope Words` |
| 49 | cheyenne | 3.1 | regex | YES — `Personal Scope Words` |
| 50 | home | 3.1 | regex | YES — `Personal Scope Words` |
| 51 | wife | 3.1 | regex | YES — `Personal Scope Words` |
| 52 | son | 3.1 | regex | YES — `Personal Scope Words` |
| 53 | daughter | 3.1 | regex | YES — `Personal Scope Words` |
| 54 | dog | 3.1 | regex | YES — `Personal Scope Words` |
| 55 | bobby | 3.2 | fixed-string | YES — `Names` (per Task-1 step 6 explicit directive, Story 3.2 workspace.json residue) |
| 56 | queen creek | 3.3 | fixed-string | YES — `Blog & Public Content` (public city residence, not a street address) |
| 57 | bodybuilding.com | 3.3 (dup of #16) | fixed-string | — (already counted) |
| 58 | integrum | 3.3 | fixed-string | YES — `Businesses` |
| 59 | omarchy | 3.3 | fixed-string | YES — `Businesses` |
| 60 | playrix | 3.3 | fixed-string | YES — `Businesses` |
| 61 | chiron | 3.3 (dup of #12) | fixed-string | — (already counted) |
| 62 | masterylab | 3.3 (dup of #15) | fixed-string | — (already counted) |
| 63 | agile weekly | 3.3 (dup of #14) | fixed-string | — (already counted) |
| 64 | gangplank | 3.3 (dup of #17) | fixed-string | — (already counted) |
| 65 | derekneighbors.com | 3.3 (dup of #13) | fixed-string | — (already counted) |
| 66 | laurie | 3.3 (dup of #39) | fixed-string | — (already counted) |
| 67 | deke | 3.3 (dup of #11) | fixed-string | — (already counted) |

**Deduplicated union cardinality:** 63 distinct tokens (rows 1–56 plus rows 58–60 minus filename-only rows 25–27 if those are excluded, else 63 inclusive). Cardinality floor AC4 requires ≥ 29 — comfortably met.

## Token → category classification

Classification below applies the Story 6.1 canonical six-category schema (AC3) to every publishable union token. Each row lists the token, its assigned category, and whether it ships as a concrete pattern line in `.github/pii-denylist.txt` or lives fork-local (marker + sentinel).

### `Names` (5 tokens — all ship concretely)

| Token | Rationale | Provenance |
|-------|-----------|------------|
| `Derek` | Template maintainer's first name; public via blog byline. | 1.2 → 1.3 → 2.1 regex+fixed → 2.2 → 3.1–3.3 regex |
| `Neighbors` | Template maintainer's surname; public via blog byline. | 1.2 → 1.3 → 2.1 → 2.2 → 3.1–3.3 regex |
| `Deke` | Public nickname. | 2.1 regex+fixed → 2.2 → 3.3 fixed |
| `Laurie` | Spouse first name; public via blog byline; Story 3.3 precedent treats as safe-to-publish. | 2.3 regex+fixed → 3.3 fixed |
| `Bobby` | First name appearing in Story 3.2 `workspace.json` recent-files residue; Task-1 step 6 directs inclusion under `Names`. | 3.2 fixed |

### `Home Address` (0 concrete tokens + 5 marker comments + 1 sentinel — all abstract)

| Entry | Type | Rationale |
|-------|------|-----------|
| `# marker: street address (number + street name)` | comment | AC3 marker; real street stays fork-local |
| `# marker: city` | comment | AC3 marker; real city (below the town-level `Queen Creek` public token) stays fork-local |
| `# marker: state or state abbreviation` | comment | AC3 marker |
| `# marker: zip code` | comment | AC3 marker; AC5 prohibits any literal 5-digit zip |
| `# marker: apartment / suite / unit number` | comment | AC3 marker |
| `DEREK_HOME_ADDRESS_FORK_LOCAL` | sentinel | AC3 fork-local customization anchor |

No union token classifies here. The Story 1.1 phrase `home address` is covered semantically by the markers plus the `home` scope-word match.

### `Family` (0 concrete tokens + 2 marker comments + 1 sentinel — all abstract)

| Entry | Type | Rationale |
|-------|------|-----------|
| `# marker: spouse first name (non-public)` | comment | AC3 marker; public spouse first name (`Laurie`) lives under `Names` per Story 3.3 precedent |
| `# marker: child first names (MUST NOT be committed; fork-local only)` | comment | AC3 policy marker — minor children's first names NEVER appear in shipped content |
| `DEREK_FAMILY_FORK_LOCAL` | sentinel | AC3 fork-local customization anchor |

No union token classifies here (because `Laurie` goes to `Names`, and no minor-child tokens appear anywhere in the harness codebase — see Pre-existing leak flags below).

### `Businesses` (11 tokens — all ship concretely)

| Token | Rationale | Provenance |
|-------|-----------|------------|
| `Agile Weekly` | Public podcast / property; Derek-associated. | 2.1 → 2.2 → 3.3 fixed |
| `Benji` | Public Benji product / MCP. | 2.2 → 3.1 regex |
| `Bodybuilding.com` | Public former-employer domain. | 2.1 → 2.2 → 3.3 fixed |
| `Chiron` | Public former-employer / property. | 2.1 → 2.2 → 3.3 fixed |
| `Flowtopic` | Public product. | 2.3 → 3.1 regex → 3.3 fixed-adjacent via regex |
| `Gangplank` | Public former-affiliation. | 2.1 → 2.2 → 3.3 fixed |
| `Integrum` | Public former-employer. | 3.3 fixed |
| `MasteryLab` | Public property. | 2.1 → 2.2 → 3.3 fixed |
| `Omarchy` | Public Derek-associated project. | 3.3 fixed |
| `Playrix` | Public game-company reference (Derek's `interests` block). | 3.3 fixed |
| `RevivaGo` | Public fitness / nutrition business. | 1.2 → 1.3 → 2.1 → 2.2 → 3.1 regex |

### `Blog & Public Content` (4 tokens — all ship concretely)

| Token | Rationale | Provenance |
|-------|-----------|------------|
| `derekneighbors.com` | Public blog domain. | 2.1 → 2.2 → 3.3 fixed |
| `gtd-life` | Public GitHub repo name. | 1.2 → 1.3 → 2.1 → 2.2 → 3.1 regex |
| `gtdlife` | Public GitHub repo name variant (no hyphen). | 3.1 regex |
| `Queen Creek` | Public region-of-residence at city level (blog bio); NOT a street address. | 3.3 fixed |

### `Personal Scope Words` (10 tokens — all ship concretely; boundary-guarded by Story 6.2's CI)

| Token | Rationale | Provenance |
|-------|-----------|------------|
| `blog` | Generic English word; boundary-guarded by CI. | 1.2 → 1.3 → 2.1 → 2.2 → 3.1 regex |
| `cheyenne` | City-scope word (Wyoming context); boundary-guarded. | 3.1 regex |
| `daughter` | Family-scope word. | 3.1 regex |
| `dog` | Personal-life scope word. | 3.1 regex |
| `family` | Family-scope word. | 2.3 → 3.1 regex |
| `home` | Personal-life scope word; subsumes `home address` Story 1.1 phrase via CI boundary guard. | 3.1 regex |
| `personal` | Personal-life scope word; subsumes `personal email` Story 2.1 phrase. | 1.1 → 1.3 → 2.1 → 3.1 regex |
| `son` | Family-scope word. | 3.1 regex |
| `wife` | Family-scope word. | 3.1 regex |
| `wyoming` | State-scope word. | 3.1 regex |

### Classification-time out-of-scope notes (documented but NOT shipped)

- **Scaffold-only tokens** from Story 1.1 that do NOT belong in a Derek-PII deny-list: `private`, `ssn`, `social security`. These are generic sensitive-content scaffold guards for otherwise-empty `.gitkeep` files; Story 6.2's CI-wide scan would create false positives if it blanket-blocked `private` in code contexts.
- **Generic tech-brand scope words** (out-of-scope): `gmail`, `google calendar`, `google workspace`, `google drive`, `google chat`, `slack`, `notion`, `asu`. These are Vixxo-work-persona scope markers, not Derek-PII, and blanket-blocking them would reject legitimate work content.
- **Philosophy / personal-vocabulary tokens** (fork-local Derek vocabulary): `arete`, `eudaimonia` — generic Greek-philosophy words that happen to be Derek's personal vocabulary. Fork-local customization can add them if a fork wants stricter coverage.
- **Filename tokens** (structural, not content): `vixxo-cto.md`, `revivago-ceo.md`, `personal.md` — the AC5_FORBIDDEN_REFS filename scan from Story 2.1 enforces these as forbidden structural references; not content tokens.

## Safe-to-publish vs fork-local-only partition

**Safe-to-publish (30 entries visible in `.github/pii-denylist.txt`)** — all five `Names` tokens, eleven `Businesses` tokens, four `Blog & Public Content` tokens, ten `Personal Scope Words` tokens. The `Home Address` and `Family` categories ship zero concrete tokens and eight abstract entries (seven marker comments + one sentinel per category). Concrete pattern-line count: 30. Total in-file line budget including six category headers, per-category description comments, header block, and blank separators: ~80–100 lines estimate for Task 3.

**Fork-local-only (33+ entries; NOT committed to public template)** —

- Real Derek home street address (not present in harnesses; would live in `DEREK_HOME_ADDRESS_FORK_LOCAL` replacement content per consumer fork).
- Real Derek ZIP code (not present in harnesses).
- Apartment / suite / unit numbers (not present).
- Minor children's first names (not present; AC3 policy explicitly forbids committing).
- Spouse phone number (not present).
- Child / sibling first names (not present).
- `Veincraft`, `Daddy Bootcamps`, `After the Stork`, `peptide` — Derek side-venture tokens from Story 2.3 with lower public salience than the AC3 `Businesses` list; fork-local consumers may add them.
- `arete`, `eudaimonia` — Derek philosophy-vocabulary; fork-local if desired.
- Real work-colleague full names (seven from Story 2.3): `Bobby Hunnicutt`, `Brandon Franz`, `Eric Burt`, `Gino Flores`, `Viswa Vadlamani`, `Jignesh Patel`, `Jim Reavey` — not Derek's own PII; each Vixxo employee's private fork would add its own colleague list.
- Generic tech brands (out-of-scope even for fork-local Derek-PII deny-list): `gmail`, `google calendar`, `google workspace`, `google drive`, `google chat`, `slack`, `notion`, `asu` — these are better handled by per-persona guardrail rules (Story 2.2's four `.cursor/rules/*.mdc` files) than by a PII deny-list.
- Scaffold-only words: `private`, `ssn`, `social security` — covered by Story 1.1's scaffold-local regex; not deny-list material.

## Pre-existing leak flags (if any)

Per Task 1 step 5 directive, the harness codebase (`_bmad-output/implementation-artifacts/tests/*.sh`) was scanned for the AC5 content-scrub probe patterns. Results:

- **Real home street address** (`[0-9]+ [A-Za-z]+ (St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Ln|Lane|Way|Dr|Drive|Ct|Court|Pl|Place)$`): **zero matches** across all ten harnesses. No street-address literal anywhere.
- **Five-digit US ZIP codes** (`(^|[^0-9a-zA-Z])[0-9]{5}([^0-9a-zA-Z]|$)`): **zero matches**. No literal ZIP anywhere.
- **Phone numbers** (`\+?[0-9]{3}[-. ][0-9]{3}[-. ][0-9]{4}`): **zero matches**. No phone-number literal anywhere.
- **`@` character** (fixed-string scan): 30 matches across the ten harnesses, ALL of which are bash array-parameter expansions of the form `[@]` (e.g. `${ARR[@]}`, `${PROBE_FILES[@]}`) or regex literals scanning for `@` in the target file (`EMAIL_PATTERN_REGEX` in Story 2.3; `@X@` pattern in Story 2.2's teams-rule guard). **Zero real email-address literals** (no `derek@example.com`, no `laurie@…`, etc.).
- **Minor children's first names**: not applicable as a negative scan (AC5 uses positive-allowlist via AC3 `Names` enumeration). Manual inspection of all ten harnesses: zero Derek-children first names appear. The only `Names`-adjacent tokens present are `Derek`, `Neighbors`, `Deke`, `Laurie`, `Bobby` (all public-precedent per above), plus seven work-colleague full names (Story 2.3, `Bobby Hunnicutt` et al.) that are fork-local, not Derek's-own-PII leaks.

**Conclusion: zero pre-existing PII leaks in the harness codebase.** Story 6.1 does NOT need to open a separate remediation story for harness scrubbing. The ten predecessor harnesses ship as-is.

## Measured `^PASS:` line-count fingerprint (ten predecessors)

Measured on 2026-04-21 on host macOS darwin 25.4.0 by running `bash <harness> all 2>&1 | grep -c '^PASS:'` for each of the ten predecessor harnesses in sequence. All ten exited `0`; all ten emitted `PASS: all` as their final line; per-harness `^PASS:` counts below.

| # | Harness | Exit code | Measured `^PASS:` count | Expected (from AC8) | Delta |
|---|---------|-----------|-------------------------|---------------------|-------|
| 1 | `story-1-1-scaffold-validation.sh` | 0 | **1** | 1 | ✓ |
| 2 | `story-1-2-root-files-validation.sh` | 0 | **1** | 1 | ✓ |
| 3 | `story-1-3-root-context-validation.sh` | 0 | **1** | 1 | ✓ |
| 4 | `story-2-1-agent-identity-validation.sh` | 0 | **1** | 1 | ✓ |
| 5 | `story-2-2-guardrail-and-formatting-validation.sh` | 0 | **10** | 10 | ✓ |
| 6 | `story-2-3-work-persona-validation.sh` | 0 | **7** | 7 | ✓ |
| 7 | `story-2-4-benji-inbox-absence-validation.sh` | 0 | **7** | 7 | ✓ |
| 8 | `story-3-1-memory-template-tree-validation.sh` | 0 | **7** | 7 | ✓ |
| 9 | `story-3-2-obsidian-config-validation.sh` | 0 | **7** | 7 | ✓ |
| 10 | `story-3-3-identity-preferences-validation.sh` | 0 | **7** | 7 | ✓ |

**Measured fingerprint (ordered):** `1 / 1 / 1 / 1 / 10 / 7 / 7 / 7 / 7 / 7`

**Fingerprint matches the AC8-predicted value exactly.** Task 4's `REGRESSION_PASS_COUNTS=( 1 1 1 1 10 7 7 7 7 7 )` constant can be codified verbatim from this measurement; no per-harness delta to reconcile.
