# Story 6.2 Baseline Audit

Baseline measurements captured at the start of Story 6.2 (Task 1) to fix the
exact pre-authoring state of the worktree. All numbers below are ACTUAL
command output — no values carried forward from the story file without
measurement.

- **Worktree root:** `/Users/dneighbors/.cursor/worktrees/assistants-template/iapu`
- **Measurement date:** 2026-04-21
- **Dev agent:** Amelia (autonomous)

## Pre-existing workflow inventory

`.github/` directory currently contains ONE file and ZERO subdirectories.
`.github/workflows/` does NOT exist at baseline — Story 6.2 will create it.

```
$ ls -la .github/
-rw-r--r--  2669  pii-denylist.txt

$ ls .github/workflows 2>&1
ls: .github/workflows: No such file or directory
```

Collision check: no pre-existing workflow file named `pii-denylist.yml` (or
anything else) exists. Story 6.2's new `.github/workflows/pii-denylist.yml`
lands on a clean path.

## 11-harness regression fingerprint (measured)

Each predecessor harness invoked in `all` mode from the worktree root, stdout
+ stderr captured, exit code recorded, `^PASS:` line count measured with
`grep -c '^PASS:'`. All eleven exited `0`.

| # | Story | Harness path | Exit | `^PASS:` count | Expected |
|---|-------|---------------|------|-----------------|----------|
| 1 | 1.1 | `tests/story-1-1-scaffold-validation.sh` | 0 | 1 | 1 |
| 2 | 1.2 | `tests/story-1-2-root-files-validation.sh` | 0 | 1 | 1 |
| 3 | 1.3 | `tests/story-1-3-root-context-validation.sh` | 0 | 1 | 1 |
| 4 | 2.1 | `tests/story-2-1-agent-identity-validation.sh` | 0 | 1 | 1 |
| 5 | 2.2 | `tests/story-2-2-guardrail-and-formatting-validation.sh` | 0 | 10 | 10 |
| 6 | 2.3 | `tests/story-2-3-work-persona-validation.sh` | 0 | 7 | 7 |
| 7 | 2.4 | `tests/story-2-4-benji-inbox-absence-validation.sh` | 0 | 7 | 7 |
| 8 | 3.1 | `tests/story-3-1-memory-template-tree-validation.sh` | 0 | 7 | 7 |
| 9 | 3.2 | `tests/story-3-2-obsidian-config-validation.sh` | 0 | 7 | 7 |
| 10 | 3.3 | `tests/story-3-3-identity-preferences-validation.sh` | 0 | 7 | 7 |
| 11 | 6.1 | `tests/story-6-1-pii-denylist-validation.sh` | 0 | 7 | 7 |

**Measured `REGRESSION_PASS_COUNTS` fingerprint:** `( 1 1 1 1 10 7 7 7 7 7 7 )`

This is the authoritative array the Task 4 harness will encode in
`REGRESSION_PASS_COUNTS`. The measured values match the expected fingerprint
declared in AC11 (Story 6.2).

Timing note: Story 6.1's `check_task6` re-invokes the ten earlier harnesses
before returning, so its wall-clock is ~4.4 minutes on this machine; the
other ten harnesses run in seconds to tens of seconds. This is consistent
with the Story 6.1 handoff note.

## Deny-list byte-stability verification

`.github/pii-denylist.txt` is BYTE-IDENTICAL to the Story 6.1 authored file.
No drift between 6.1 and 6.2.

```
$ wc -c .github/pii-denylist.txt
    2669 .github/pii-denylist.txt

$ shasum -a 256 .github/pii-denylist.txt
b5b11a2c9d7da38308a9f8a1e95de5e89eb2111d2aa3a9e3ff7663bb434d681c  .github/pii-denylist.txt
```

| Property | Expected (Story 6.1 handoff) | Measured | Status |
|----------|------------------------------|----------|--------|
| Byte count | 2669 | 2669 | MATCH |
| SHA-256 | `b5b11a2c9d7da38308a9f8a1e95de5e89eb2111d2aa3a9e3ff7663bb434d681c` | `b5b11a2c9d7da38308a9f8a1e95de5e89eb2111d2aa3a9e3ff7663bb434d681c` | MATCH |

Story 6.2's scanner contract (load patterns read-only from this file) is
safe to encode against this hash.

## Loaded pattern count (post-sentinel-filter)

Patterns stripped of comments, blanks, and the two fork-local audit anchors
(`DEREK_HOME_ADDRESS_FORK_LOCAL`, `DEREK_FAMILY_FORK_LOCAL`):

```
$ grep -vE '^(#|$)' .github/pii-denylist.txt \
    | grep -vFx 'DEREK_HOME_ADDRESS_FORK_LOCAL' \
    | grep -vFx 'DEREK_FAMILY_FORK_LOCAL' \
    | wc -l
      30
```

- **Measured count:** 30
- **Sanity floor (AC3 / AC10):** ≥ 25 — PASS
- **Story-authored expectation:** 28 (AC3 narrative)
- **Delta:** +2 vs. the story narrative (NOT a blocker — AC3 explicitly
  defers to "Dev records the actual measured count at implementation time
  and asserts it is ≥ 25")

The +2 delta reflects the Story 6.1 deny-list as authored on-disk: the file
contains 32 non-comment / non-blank lines (30 banned tokens + 2 fork-local
sentinels) rather than 30 (28 + 2). The higher count is safer — more
coverage, same semantics. The Task 4 harness MUST codify
`PATTERN_COUNT_FLOOR=25` (not 28) to match AC3's stated floor.

### Raw pattern lines (for blueprint authoring)

```
Derek
Neighbors
Deke
Laurie
Bobby
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
derekneighbors.com
gtd-life
gtdlife
Queen Creek
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

### Anti-self-match guard re-verification (AC9 mirror)

```
$ grep -vE '^(#|$)' .github/pii-denylist.txt | grep -Fq 'SAFE-TO-PUBLISH'
$ echo "exit=$?"
exit=1
```

Exit code 1 (NO match) — the `SAFE-TO-PUBLISH` sentinel lives ONLY in the
header comment block, NOT in any pattern line. The Story 6.1 harness
`check_task4` guard and the Story 6.2 AC9 pre-flight guard both hold
against the current deny-list.

## Full-tree dry-run scan (zero-match assertion)

Combined POSIX-ERE boundary-guard alternation regex built locally per AC3
(strip comments/blanks → strip sentinels → `sed` escape regex metacharacters
per pattern → wrap in `(^|[^A-Za-z])(ALT)($|[^A-Za-z])`):

```
(^|[^A-Za-z])(Derek|Neighbors|Deke|Laurie|Bobby|Agile Weekly|Benji|Bodybuilding\.com|Chiron|Flowtopic|Gangplank|Integrum|MasteryLab|Omarchy|Playrix|RevivaGo|derekneighbors\.com|gtd-life|gtdlife|Queen Creek|blog|cheyenne|daughter|dog|family|home|personal|son|wife|wyoming)($|[^A-Za-z])
```

Regex length: 285 B (one line, written to `/tmp/story-6-2-baseline/combined-regex.txt`).

Scan enumeration: `find . -type f` minus the AC4 exclusion set (verbatim):

- `./.git/*`
- `./node_modules/*`
- `./.github/pii-denylist.txt`
- `./docs/pii-denylist.md`
- `./_bmad/*`
- `./_bmad-output/implementation-artifacts/*.md`
- `./_bmad-output/implementation-artifacts/tests/*.md`
- `./_bmad-output/implementation-artifacts/tests/*.sh`
- `./_bmad-output/planning-artifacts/*`
- `./.github/workflows/pii-denylist.yml`

Files scanned after exclusion: **548**

Scanner: `grep -inE "$REGEX" <file> --with-filename` (case-insensitive,
with filenames and line numbers), aggregated into
`/tmp/story-6-2-baseline/scan-matches.txt`.

**Matches: 31 (NOT zero — see next section for pre-existing leak flags).**

The zero-match assertion demanded by AC4 / Task 1 subtask 6 does NOT hold
against the current exclusion set. Task 2 / Task 3 MUST either (a) expand
the AC4 exclusion set, or (b) remediate the matching lines, or (c) accept
that these matches can only fire in CI if a future PR touches these files
(which is the case today — the workflow scans the PR DIFF, not the
full tree; see Story 6.2 Dev Note "Why the GitHub Action scans only
changed files (not the full tree)"). Details in the next section.

## Pre-existing leak flags (if any)

**31 pre-existing matches found in 17 non-excluded files.** Breakdown by
match token (best-effort; token extracted from match line via
case-insensitive scan):

| Count | Token |
|-------|-------|
| 20 | `personal` |
| 6  | `blog` |
| 3  | `family` |
| 2  | `gtd-life` |
| 2  | `Benji` |
| 1  | `home` |

Breakdown by file:

| Count | File |
|-------|------|
| 8 | `./_bmad-output/implementation-artifacts/sprint-status.yaml` |
| 3 | `./.cursor/skills/bmad-create-epics-and-stories/steps/step-03-create-stories.md` |
| 3 | `./.claude/skills/bmad-create-epics-and-stories/steps/step-03-create-stories.md` |
| 2 | `./.cursor/skills/bmad-brainstorming/steps/step-02b-ai-recommended.md` |
| 2 | `./.cursor/rules/agent-identity.mdc` |
| 2 | `./.claude/skills/bmad-brainstorming/steps/step-02b-ai-recommended.md` |
| 1 | `./.cursor/skills/bmad-review-adversarial-general/SKILL.md` |
| 1 | `./.cursor/skills/bmad-market-research/steps/step-04-customer-decisions.md` |
| 1 | `./.cursor/skills/bmad-distillator/resources/distillate-format-reference.md` |
| 1 | `./.cursor/skills/bmad-brainstorming/steps/step-04-idea-organization.md` |
| 1 | `./.cursor/skills/bmad-brainstorming/brain-methods.csv` |
| 1 | `./.cursor/rules/outbound-messaging-guardrail.mdc` |
| 1 | `./.claude/skills/bmad-review-adversarial-general/SKILL.md` |
| 1 | `./.claude/skills/bmad-market-research/steps/step-04-customer-decisions.md` |
| 1 | `./.claude/skills/bmad-distillator/resources/distillate-format-reference.md` |
| 1 | `./.claude/skills/bmad-brainstorming/steps/step-04-idea-organization.md` |
| 1 | `./.claude/skills/bmad-brainstorming/brain-methods.csv` |

### Verbatim match dump

```
./.cursor/rules/outbound-messaging-guardrail.mdc:29:> Personal messaging surfaces (SMS, iMessage, personal chat apps) are
./.cursor/rules/agent-identity.mdc:20:- Out of scope: personal life, home, family, hobbies, side ventures, or any
./.cursor/rules/agent-identity.mdc:40:`assistants-template` is a Vixxo-deployable personal AI agent template. It ships
./.cursor/skills/bmad-market-research/steps/step-04-customer-decisions.md:155:_Peer Influence: [How friends and family influence decisions]_
./.cursor/skills/bmad-review-adversarial-general/SKILL.md:10:**Your Role:** You are a cynical, jaded reviewer with zero patience for sloppy work. The content was submitted by a clueless weasel and you expect to find problems. Be skeptical of everything. Look for what's missing, not just what's wrong. Use a precise, professional tone — no profanity or personal attacks.
./.cursor/skills/bmad-distillator/resources/distillate-format-reference.md:132:- Transforms BMAD from dev-only methodology into open platform for any domain (creative, therapeutic, educational, personal)
./.cursor/skills/bmad-brainstorming/steps/step-04-idea-organization.md:270:✅ User successfully prioritized ideas based on personal criteria
./.cursor/skills/bmad-brainstorming/steps/step-02b-ai-recommended.md:64:- Personal Insight → introspective_delight category
./.cursor/skills/bmad-brainstorming/steps/step-02b-ai-recommended.md:71:- Emotional/Personal Topic → introspective_delight techniques
./.cursor/skills/bmad-brainstorming/brain-methods.csv:28:introspective_delight,Values Archaeology,"Excavate deep personal values driving decisions to clarify authentic priorities - dig to bedrock motivations by asking what really matters, why you care, what's non-negotiable, and what core values guide your choices"
./.cursor/skills/bmad-create-epics-and-stories/steps/step-03-create-stories.md:106:- Story 2.1: Create New Blog Post
./.cursor/skills/bmad-create-epics-and-stories/steps/step-03-create-stories.md:107:- Story 2.2: Edit Existing Blog Post
./.cursor/skills/bmad-create-epics-and-stories/steps/step-03-create-stories.md:108:- Story 2.3: Publish Blog Post
./_bmad-output/implementation-artifacts/sprint-status.yaml:35:# - linear_team: AI Personal Agent - Skills
./_bmad-output/implementation-artifacts/sprint-status.yaml:47:linear_team: "AI Personal Agent - Skills"
./_bmad-output/implementation-artifacts/sprint-status.yaml:93:  2-4-confirm-benji-inbox-default-not-ported:
./_bmad-output/implementation-artifacts/sprint-status.yaml:96:    linear_url: "https://linear.app/vixxo/issue/AIP-32/story-24-confirm-benji-inbox-defaultmdc-is-not-ported"
./_bmad-output/implementation-artifacts/sprint-status.yaml:107:  3-1-port-template-trees-from-gtd-life-memory:
./_bmad-output/implementation-artifacts/sprint-status.yaml:110:    linear_url: "https://linear.app/vixxo/issue/AIP-31/story-31-port-template-trees-from-gtd-life-memory"
./_bmad-output/implementation-artifacts/sprint-status.yaml:203:  7-3-personal-agents-teams-channel-and-feedback-loop:
./_bmad-output/implementation-artifacts/sprint-status.yaml:206:    linear_url: "https://linear.app/vixxo/issue/AIP-46/story-73-stand-up-personal-agents-teams-channel-and-feedback-loop"
./.claude/skills/bmad-market-research/steps/step-04-customer-decisions.md:155:_Peer Influence: [How friends and family influence decisions]_
./.claude/skills/bmad-review-adversarial-general/SKILL.md:10:**Your Role:** You are a cynical, jaded reviewer with zero patience for sloppy work. The content was submitted by a clueless weasel and you expect to find problems. Be skeptical of everything. Look for what's missing, not just what's wrong. Use a precise, professional tone — no profanity or personal attacks.
./.claude/skills/bmad-distillator/resources/distillate-format-reference.md:132:- Transforms BMAD from dev-only methodology into open platform for any domain (creative, therapeutic, educational, personal)
./.claude/skills/bmad-brainstorming/steps/step-04-idea-organization.md:270:✅ User successfully prioritized ideas based on personal criteria
./.claude/skills/bmad-brainstorming/steps/step-02b-ai-recommended.md:64:- Personal Insight → introspective_delight category
./.claude/skills/bmad-brainstorming/steps/step-02b-ai-recommended.md:71:- Emotional/Personal Topic → introspective_delight techniques
./.claude/skills/bmad-brainstorming/brain-methods.csv:28:introspective_delight,Values Archaeology,"Excavate deep personal values driving decisions to clarify authentic priorities - dig to bedrock motivations by asking what really matters, why you care, what's non-negotiable, and what core values guide your choices"
./.claude/skills/bmad-create-epics-and-stories/steps/step-03-create-stories.md:106:- Story 2.1: Create New Blog Post
./.claude/skills/bmad-create-epics-and-stories/steps/step-03-create-stories.md:107:- Story 2.2: Edit Existing Blog Post
./.claude/skills/bmad-create-epics-and-stories/steps/step-03-create-stories.md:108:- Story 2.3: Publish Blog Post
```

### Triage categories and forward-looking guidance for Task 2

The 17 flagged files cluster into four buckets. NONE are Derek-PII leaks.
All are legitimate uses of personal-scope English words (`personal`,
`home`, `family`, `blog`) or self-referential BMAD/sprint-tracking tokens
(`Benji`, `gtd-life`).

1. **BMAD framework skill copies** (14 matches across 12 files) —
   `./.cursor/skills/bmad-*/**/*.{md,csv,SKILL.md}` and the mirror under
   `./.claude/skills/`. These are copies of BMAD module internals that the
   Cursor and Claude skill surfaces consume. AC4 already excludes `_bmad/`
   (the source tree); the `.cursor/skills/` and `.claude/skills/` copies
   were NOT in the AC4-authored exclusion list. Tokens that match are
   `personal`, `family`, `blog` used as generic English — for example,
   `bmad-brainstorming/brain-methods.csv` references "personal values" in
   a brainstorming method description; `bmad-create-epics-and-stories`
   illustrates story-creation with the phrase "Create New Blog Post".
   **Recommendation for Task 2 blueprint author:** extend the AC4 exclusion
   set in the Task-3 workflow to include `.cursor/skills/bmad-` and
   `.claude/skills/bmad-` (or the parent `.cursor/skills/` and
   `.claude/skills/` directories wholesale, matching the `_bmad/`
   rationale — upstream framework, not Vixxo-authored). Note that AC4 as
   currently authored would ship a workflow that misses these paths,
   which is acceptable for diff-scoped CI (see Dev Note "Why the GitHub
   Action scans only changed files"), but is a latent time bomb the
   moment a future PR edits any bmad skill file.

2. **`.cursor/rules/` policy language** (3 matches across 2 files) —
   `agent-identity.mdc:20,40` and `outbound-messaging-guardrail.mdc:29`.
   These lines use `personal`, `home`, `family` as LEGITIMATE policy
   language defining what the agent's scope is (e.g. "Out of scope:
   personal life, home, family, hobbies, side ventures"). Removing the
   words would neuter the policy statements. **Recommendation:** either
   add `.cursor/rules/` to the AC4 exclusion set, OR rewrite the three
   lines to avoid the banned words (e.g. "non-work life" instead of
   "personal life") — Story 2.1 / 2.2 authors intended these lines to
   define the work/non-work boundary, so rephrasing is low-risk but
   requires coordination with those stories' byte-stability invariants.

3. **`sprint-status.yaml` self-reference** (8 matches in 1 file) —
   the Linear team name literal `"AI Personal Agent - Skills"` and Linear
   URLs embedding story slugs like `2-4-confirm-benji-inbox-default`,
   `3-1-port-template-trees-from-gtd-life-memory`,
   `7-3-personal-agents-teams-channel-and-feedback-loop`. These tokens
   are immutable external identifiers (Linear team names, issue URLs).
   AC4 already excludes `*.md` under `implementation-artifacts/` but NOT
   `*.yaml` under the same directory. **Recommendation:** extend the AC4
   exclusion set to cover
   `_bmad-output/implementation-artifacts/sprint-status.yaml`
   (or more broadly, `_bmad-output/implementation-artifacts/*.yaml`) so
   that the sprint tracker can retain its legitimate Linear identifiers
   without being flagged.

4. **No `gtd-life` source-repo leaks in real content.** The two `gtd-life`
   matches are both embedded in the Linear issue URL slug
   `story-31-port-template-trees-from-gtd-life-memory` inside
   `sprint-status.yaml` — covered by bucket 3.

### Decision for Task 1 completion

Per Task 1 subtask 6: "If any match is found in a non-excluded file, STOP
and flag — this is a pre-existing leak that must be triaged before Story
6.2 can ship without false CI failures."

**Status:** flagged in this document, not remediated. All 31 matches are
non-Derek-PII English words used in framework-internal or policy
documentation contexts, or immutable external identifiers in the sprint
tracker. Task 2 (blueprint) and Task 3 (workflow authoring) MUST address
the AC4 exclusion set BEFORE the workflow file is committed, either by
adding the four forward-looking exclusions recommended above
(`.cursor/skills/bmad-*`, `.claude/skills/bmad-*`, `.cursor/rules/`,
`_bmad-output/implementation-artifacts/*.yaml`) or by remediating the
`.cursor/rules/` policy language directly.

This is NOT a Story 6.1 contract violation — the Story 6.1 deny-list is
byte-identical and the Story 6.1 harness anti-self-match guard still
holds. It IS a Story 6.2 scope discovery that requires Task 2 attention
before Task 3 can ship a workflow that does not fire false-positive CI
failures against the steady-state repo.

Baseline audit COMPLETE. Proceed to Task 2.
