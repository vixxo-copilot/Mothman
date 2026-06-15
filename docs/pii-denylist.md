# PII Deny-list

This document describes the shared PII deny-list shipped at `.github/pii-denylist.txt`. The deny-list is the single source of truth for banned personal patterns that must never appear in shipped template content. It is consumed by the Story 6.2 GitHub Action (the CI guardrail) and by any downstream consumer fork that needs an identical first-line-of-defence policy.

## Purpose

`.github/pii-denylist.txt` is the single source of truth for banned personal patterns in `assistants-template`. The list operationalizes Epic 6's NFR1 ("No Derek PII in any shipped content") and FR10 ("PII CI Guardrail blocking PRs that introduce personal content"). Story 6.1 ships the file. Story 6.2 ships the GitHub Action that consumes it. Every downstream fork (every Vixxo employee clone, plus the mirrored `agent-skills` repo) inherits the same deny-list, so the banned-term vocabulary is centralized and does not drift across repos or stories.

## File location and format

- Canonical path: `.github/pii-denylist.txt` (committed, UTF-8, LF line endings, trailing newline, non-empty).
- Every physical line is one of three kinds:
  - A comment line that starts with `#` in column 1.
  - A blank line (zero bytes before the newline).
  - A pattern line: a single non-empty token with no leading or trailing whitespace, treated as a literal substring.
- Category sections are introduced by a header of the exact form `# === CATEGORY: <name> ===` on a single comment line, followed by an optional one-line description comment, the pattern lines for that category, and a single blank line before the next section.
- No tabs, no trailing spaces, no line longer than 200 bytes. Pattern lines are NOT pre-escaped for regex metacharacters: Story 6.2's workflow wraps each pattern in a POSIX-ERE boundary guard at scan time. Keep the file human-readable and grep-compatible.

Example (shape only — see the real file for the full content):

```
# === CATEGORY: Names ===
# Public-safe name tokens associated with the current template maintainer.
Derek
Neighbors
```

## Categories

The deny-list contains exactly six canonical category sections, in this order:

1. `Names` — public-safe name tokens associated with the current template maintainer (first, last, nicknames, publicly-precedented spouse first name).
2. `Home Address` — marker comments plus one fork-local sentinel (`DEREK_HOME_ADDRESS_FORK_LOCAL`). Contains ZERO real street / city / zip tokens; consumer forks add real tokens locally.
3. `Family` — marker comments plus one fork-local sentinel (`DEREK_FAMILY_FORK_LOCAL`). Contains ZERO real family tokens; minor children's names live nowhere in this file.
4. `Businesses` — publicly-known business and product tokens associated with the maintainer, alphabetized.
5. `Blog & Public Content` — public blog domain, source-repo name variants, and notable public-content tokens.
6. `Personal Scope Words` — generic English words that mark personal-life scope (`family`, `home`, `wife`, etc.). CI word-boundary enforcement prevents false positives on unrelated compounds such as `homepage`.

## CI consumption

See [.github/workflows/pii-denylist.yml](../.github/workflows/pii-denylist.yml) for the production implementation.

Story 6.1 does not implement the CI workflow. Story 6.2 does. The deny-list file fixes the following contract so that Story 6.2 has a deterministic consumption surface:

1. Pattern loading: `grep -vE '^(#|$)' .github/pii-denylist.txt` yields one literal substring per line (comments and blanks stripped).
2. Per-pattern regex wrapping: each loaded pattern `P` is wrapped in the POSIX-ERE boundary guard `(^|[^A-Za-z])P($|[^A-Za-z])` at scan time. Invoked with `grep -iE` for case-insensitive matching. BSD-grep and GNU-grep compatible.
3. Metacharacter escaping: pattern lines may contain regex metacharacters (for example, `.` in `derekneighbors.com`). The workflow escapes metacharacters before wrapping in the boundary guard. The deny-list file itself does NOT pre-escape.
4. Scan scope and exclusions: the workflow scans the PR diff or the full tree, excluding `.git/`, `.github/pii-denylist.txt` itself (the deny-list must not match itself), `docs/pii-denylist.md` (this policy doc), and the `_bmad-output/implementation-artifacts/` evidence tree (which intentionally enumerates banned tokens as audit prose).
5. Failure mode: on any match, the workflow fails with a non-zero exit, prints the offending file plus line plus matched pattern, and blocks the PR merge. Performance budget: under 30 seconds end-to-end.

## How to extend

1. Identify the correct category (one of the six listed above).
2. Add the new token in alphabetical order within that category section.
3. Open a PR against `main` containing the one-line deny-list diff.
4. Write a one-line commit message that explains why the token belongs on the list (for example: "add `NewBiz` to Businesses: publicly-associated with maintainer via LinkedIn").
5. If a NEW category is needed (beyond the six canonical sections), that is a file-format change and requires a follow-up story that bumps AC3 explicitly. Do not add a seventh category section in an ad-hoc PR.

Any token added MUST be safe to publish in the open-source template (see the final section of this doc). If the token would itself leak PII, add it via a fork-local override, not via this file.

## Relationship to the mirrored `agent-skills` repo

`.github/pii-denylist.txt` is mirrored in the companion `agent-skills` repository at the same path. Drift between the two repos is a policy violation: the shared deny-list is meant to be identical on both sides so downstream consumers inherit the same banned-term vocabulary regardless of which repo they clone from. Synchronization between the two files is an operational concern for the `agent-skills` maintainers. This repository's CI (Story 6.2) does NOT enforce mirror synchronization. If you edit `.github/pii-denylist.txt` here, coordinate the identical edit in `agent-skills` in the same PR cycle.

## What does NOT belong in this file

The deny-list ships publicly. Anything written into it is itself public. To avoid paradoxically leaking PII by listing it, the following kinds of content MUST NOT appear in `.github/pii-denylist.txt`:

- Raw home street addresses (no number-space-street-name-space-suffix patterns). The `Home Address` category uses marker comments plus a fork-local sentinel instead.
- Five-digit US zip codes (including ZIP+4 extensions).
- Minor children's first names. The `Family` category uses marker comments plus a fork-local sentinel; consumer forks add their real family tokens in a private fork, never here.
- Raw phone numbers in any common separator format (hyphen, dot, or space).
- Email addresses. The file contains zero email characters: public business and blog domains are written as bare domains (for example, `derekneighbors.com`, `Bodybuilding.com`) with no local-part prefix.
- Secrets or credentials. Those belong in `.gitignore`-d environment files and in `.env.example` placeholders, never in this deny-list.

The same bar applies to this policy doc. `docs/pii-denylist.md` itself contains zero raw addresses, zero zip codes, zero minor children's names, zero phone numbers, and zero email characters. The only public dotted domains named anywhere in either file are the explicit public references (`derekneighbors.com`, `Bodybuilding.com`) that are already on the public internet via the maintainer's blog bio and LinkedIn profile respectively.
