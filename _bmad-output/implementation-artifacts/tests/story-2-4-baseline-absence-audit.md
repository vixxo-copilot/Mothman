# Story 2.4 Baseline Absence Audit

Story: `2-4-confirm-benji-inbox-default-not-ported`
Linear: AIP-32
Date: 2026-04-20

This baseline absence audit documents the state of `.cursor/rules/` prior to
Story 2.4 landing, identifies the gtd-life source-of-record that is
intentionally NOT ported into the `assistants-template` work template, and
locks the absence-assertion scope (file-level) that Story 2.4's harness
enforces. It is the read-only companion to the deterministic bash harness at
`_bmad-output/implementation-artifacts/tests/story-2-4-benji-inbox-absence-validation.sh`.

Source story file:
`_bmad-output/implementation-artifacts/2-4-confirm-benji-inbox-default-not-ported.md`
(Acceptance Criteria AC1–AC8; Tasks 1–7; Dev Notes and References).

Absence assertion (one-line summary): `.cursor/rules/benji-inbox-default.mdc`
MUST NOT exist in this repository; no file under `.cursor/rules/` may have a
basename whose prefix matches `benji` (case-insensitive); no `benji*.mdc`
(or `.md` / `.markdown`) file may appear anywhere under the repository root
outside the `_bmad-output/` and `.git/` evidence paths. The `_bmad/`
exclusion mentioned in earlier drafts was removed per review fix F3 to
realign the harness with AC1 verbatim (independently verified — `_bmad/`
contains zero `benji*` files).

## Current .cursor/rules/ inventory

Enumerated live via `ls .cursor/rules/` on the `assistants-template` working
tree at Story 2.4 Phase 2 start (prior to any Story 2.4 edit):

- `.gitkeep` — Story 1.1 scaffold sentinel (zero-byte; preserved by Stories 2.1/2.2 per the Story 1.1 allowlist-by-extension invariant)
- `agent-identity.mdc` — Story 2.1 output (identity + scope + MCP overview + persona pointer)
- `email-triage-thread-defaults.mdc` — Story 2.2 output
- `memory-vault-protection.mdc` — Story 2.2 output
- `outbound-messaging-guardrail.mdc` — Story 2.2 output
- `teams-dm-formatting.mdc` — Story 2.2 output

Review fix F2: earlier drafts of this audit incorrectly stated the
`.gitkeep` sentinel had been superseded. It was not — the sentinel remains
zero-byte and is preserved by the Story 1.1 scaffold harness. Story 2.4
does not touch it.

`benji-inbox-default.mdc` is **NOT** in the list. This is the positive
baseline evidence that Story 2.4 locks via the harness: the file does not
exist today, and Story 2.4's job is to install a deterministic assertion
that catches any future accidental re-introduction.

Persona directory cross-reference: `agents/personas/` contains `work.md`
(Story 2.3 output) plus a zero-byte `.gitkeep` sentinel (Story 1.1
scaffold). Story 2.4 does not touch either file.

## gtd-life source (reference only — not ported)

Source of record: `~/Public/gtd-life/.cursor/rules/benji-inbox-default.mdc`

Relevant shape observed at audit time:

- Filename: `benji-inbox-default.mdc`
- Frontmatter keys/values:
  - `description: Default Benji todos to inbox`
  - `alwaysApply: true`
- Body contains explicit Derek reference: "unless Derek explicitly says not
  to put the task in inbox" (personal context — Derek's gtd-life task
  system).
- Body references the Benji task system by name ("When creating Benji
  todos...", "If Derek also asks for a Benji list...").

The file is therefore BOTH structurally personal (the rule file itself is
specific to Derek's personal Benji task manager) AND content-level personal
(Derek + Benji tokens inside the body). This is why it is excluded:

- There is no Vixxo work equivalent of the Benji task manager — the work
  template routes task creation to Linear (per Story 2.3 persona lock:
  `## Task System` = "Linear (Vixxo work task system).").
- Even a token-scrubbed variant of this rule would still impose personal
  GTD semantics (an `alwaysApply: true` default-to-inbox behavior) that has
  no place in a generic Vixxo work assistant.

The file is therefore NOT ported. Reference here is evidence-only; the
gtd-life source must never be copied into `assistants-template`.

## Absence-assertion scope

Story 2.4 enforces absence at three layers, all file-level (complementary
to Story 2.3's content-level scrub of `agents/personas/work.md`):

1. **File-level primary (AC1):** `.cursor/rules/benji-inbox-default.mdc` does
   NOT exist as a real file, a zero-byte placeholder, or a symlink. The
   harness uses `[[ ! -e "${BANNED_RULE_PATH}" ]]` which covers all three
   forms (regular file, symlink, directory).

2. **Pattern-level under `.cursor/rules/` (AC2):** The basename of every
   entry matching `.cursor/rules/*.mdc`, `.cursor/rules/*.md`, and
   `.cursor/rules/*.markdown` is case-insensitively compared against
   `^[Bb][Ee][Nn][Jj][Ii]` (ERE prefix match). A belt-and-suspenders glob
   loop over `.cursor/rules/*benji*` covers the general "contains `benji`"
   shape (e.g. `my-benji-rule.mdc`, `rule-benji-inbox.mdc`). Any match
   fails the gate.

3. **Repository-wide outside evidence paths (AC2 belt-and-suspenders):**
   `find "${PROJECT_ROOT}" -type f -name 'benji*.mdc' -not -path '...'`
   excluding `_bmad-output/`, `_bmad/`, and `.git/` must produce zero
   output. A future contributor who hides the banned file at a different
   path (e.g. `memory/companies/gtd-life/benji-inbox-default.mdc`) cannot
   bypass the Story 2.4 assertion — the repository-wide scan would catch
   it.

Evidence paths that legitimately reference the banned filename and are
therefore explicitly EXCLUDED from Story 2.4's find-based scan:

- `_bmad-output/` — planning artifacts (epics.md line 241–250), sprint
  tracker, prior story files, this story file, the handoff artifact, the
  baseline audit you are reading, and the harness itself all reference the
  banned filename in spec/evidence/comment form. These must NOT be flagged.
- `_bmad/` — BMAD method module source; may reference the banned filename
  only incidentally if at all.
- `.git/` — git internal objects that may legitimately encode the banned
  filename in the history record of this file creation itself.

## Complement to Story 2.3 content scrub

Two independent assertions operate as defense-in-depth; neither supersedes
the other:

- **Story 2.3 content scrub (already landed, owned by Story 2.3):**
  `agents/personas/work.md` contains zero occurrences of the literal
  token `benji` under the boundary-guarded POSIX-ERE regex
  `(^|[^A-Za-z])benji($|[^A-Za-z])`. This catches content-level leakage
  such as a copy-pasted gtd-life paragraph that mentions "Benji inbox" or
  "Benji task" — but it does NOT prevent a file named `benji-inbox-default.mdc`
  from appearing in the repository (the persona content scan doesn't enumerate
  rule-pack filenames).

- **Story 2.4 file-level absence (this story):** No file with a `benji`-prefixed
  basename appears under `.cursor/rules/`, and no `benji*.mdc` file appears
  anywhere in the repository outside the evidence directories. This catches
  file-level leakage such as a port-everything script that copies the entire
  gtd-life `.cursor/rules/` tree. It does NOT prevent a content-level
  reference inside, e.g., `agents/personas/work.md` (that remains Story 2.3's
  domain).

Together: content + file = defense-in-depth. Each scan catches leakage the
other would miss.

Story 2.4 additionally performs a harness-local `regex_self_probe` against
the same `(^|[^A-Za-z])benji($|[^A-Za-z])` boundary-guard Story 2.3 uses,
with synthetic positive (`benji inbox` must match) and negative (`benjiman`
must NOT match) test cases. This is NOT a duplicate of the Story 2.3 content
scan over `agents/personas/work.md` — it is a fail-fast guard that catches a
mis-parsing host grep on systems without GNU regex before any other Story
2.4 gate runs. Story 2.3 owns content-level `benji` scrub of the persona;
Story 2.4 owns file-level `benji` absence + a host-regex-sanity probe.

## Banned-filename pattern lock

The Story 2.4 harness locks the following POSIX-ERE basename prefix pattern
in the `BENJI_BASENAME_PATTERN` constant:

```
^[Bb][Ee][Nn][Jj][Ii]
```

Rationale for the case-explicit bracket form (vs `grep -i` or
`shopt -s nocaseglob`):

- `shopt -s nocaseglob` mutates global shell state and would leak into any
  downstream glob in the harness — reject.
- `grep -i` with a plain `^benji` pattern is fine for the content probe
  but is less auditable when the assertion is a basename shape lock; the
  bracketed form makes the case-insensitivity explicit at the pattern
  level and documents intent.

The pattern is intentionally a PREFIX match, not a substring match, because:

- AC2 specifies basename PREFIX (`begins with benji`) as the primary
  assertion, with a belt-and-suspenders substring check (`-benji-`,
  `_benji_`, `benji-inbox`, `benji_inbox`) covered by the glob loop over
  `.cursor/rules/*benji*`.
- A pure substring match would false-positive on perfectly legitimate
  filenames that happen to contain `benji` as a substring in some future
  epic — the prefix+glob combo is the tighter lock.

The Story 2.4 harness additionally locks the content-scrub parity regex:

```
(^|[^A-Za-z])benji($|[^A-Za-z])
```

under the `BENJI_BOUNDARY_REGEX` constant, reused verbatim from Story 2.2 /
2.3 for the `regex_self_probe` fail-fast guard (NOT for a duplicate content
scan of any file — the probe exercises the host grep on synthetic input only).

## Rule-pack integrity invariant

Story 2.4's harness verifies that the following five rule files exist and
are non-empty (zero-edit verification that Story 2.4 did not accidentally
remove the allowed pack while installing the absence assertion):

1. `.cursor/rules/agent-identity.mdc` (Story 2.1)
2. `.cursor/rules/outbound-messaging-guardrail.mdc` (Story 2.2)
3. `.cursor/rules/memory-vault-protection.mdc` (Story 2.2)
4. `.cursor/rules/teams-dm-formatting.mdc` (Story 2.2)
5. `.cursor/rules/email-triage-thread-defaults.mdc` (Story 2.2)

Plus the Story 2.3 persona artifact:

- `agents/personas/work.md`

Plus a zero-edit guard that the Story 2.1 identity rule still points at the
Story 2.3 persona:

- `grep -Fq 'agents/personas/work.md' .cursor/rules/agent-identity.mdc` must
  succeed.

These together establish that Story 2.4's additive-only contract is honored:
nothing in the Story 2.1 / 2.2 / 2.3 rule pack is removed or mutated by
Story 2.4.
