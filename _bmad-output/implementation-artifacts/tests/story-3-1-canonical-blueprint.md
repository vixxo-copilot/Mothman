# Story 3.1 Canonical Blueprint

Locked design for the nine memory-vault template files ported in Tasks 3a–3f. Every lock in this document maps to one or more ACs in Story 3.1 and is enforced by the Task 4 validation harness (`story-3-1-memory-template-tree-validation.sh`). Follows the Story 2.3 canonical-blueprint precedent.

This document is a pure specification. It defines the exact frontmatter shape, heading structure, placeholder vocabulary, and banned-term rules. It does not contain the full body prose of any template — that prose is authored verbatim-with-scrubs from the gtd-life source in Tasks 3a–3f, constrained by the locks below.

Conventions used throughout:

- **Frontmatter key lock:** the listed keys appear in the listed order inside the YAML frontmatter block opened by `---` on line 1 and closed by `---` on a subsequent line. No extra keys. No reordering.
- **Heading lock:** each listed H1/H2/H3 heading appears verbatim in the body, in the listed order. No extra sibling headings at the same depth unless explicitly noted.
- **Placeholder lock:** only the placeholders listed in the `## Placeholder vocabulary lock` section at the bottom of this document may appear in any template file. Forms `{single}`, `<angle>`, `%percent%`, and `${dollar}` are forbidden everywhere.
- **Banned-term lock:** no token in the `## Banned-term lock` set may appear in any template file, under the boundary-guarded POSIX-ERE regex `(^|[^A-Za-z])TOKEN($|[^A-Za-z])` (case-insensitive).
- **Trailing newline:** every template file ends with a single `\n`. LF only, no CRLF.
- **Encoding:** every template file is valid UTF-8.

---

## Blueprint — `memory/meetings/_template/meeting.md`

Maps to AC1, AC7, AC8.

### Frontmatter keys (in order)

1. `type: meeting`
2. `date: YYYY-MM-DD`
3. `time: "HH:MM"`
4. `attendees: []`
5. `context: ""`
6. `location: ""`
7. `join_url: ""`
8. `organizer: ""`
9. `recurring: false`
10. `action_items: []`
11. `created: YYYY-MM-DD`
12. `updated: YYYY-MM-DD`
13. `tags: []`

### Body headings (in order)

1. `# {{Meeting Title}}` (H1)
2. `## Summary` (H2)
3. `## Notes` (H2)
4. `## Decisions` (H2)
5. `## Action Items` (H2)

### Required body elements

- A doc-link table with three cells linking to sibling files. Required literal substrings (each must appear at least once):
  - `[prep.md](prep.md)`
  - `[agenda.md](agenda.md)`
  - `[transcript.md](transcript.md)`
- Each H2 section may contain an HTML-comment hint (e.g. `<!-- ... -->`) or be empty. No prose that hard-codes a meeting topic.

### Scrub / repair rules

- If the gtd-life source carries the inline comment `# vixxo | revivago | personal` on the `context:` line, rewrite it to `# e.g. vixxo | customer | internal` OR remove the comment entirely. The `context:` VALUE must remain `""` (empty string).
- No other content changes during the port.

### Allowed placeholders in this file

- `{{Meeting Title}}`

Plus the literal tokens `YYYY-MM-DD` and `HH:MM` in frontmatter only.

---

## Blueprint — `memory/meetings/_template/agenda.md`

Maps to AC1, AC7, AC8.

### Frontmatter keys (in order)

No YAML frontmatter required for this file (the gtd-life source is headless). If frontmatter is present, it must open with `---` and close with `---` and contain no banned terms. The harness does NOT require a frontmatter block for `agenda.md`.

### Body headings (in order)

1. `# Agenda -- {{Meeting Title}}` (H1)
2. `## Topics` (H2)
3. `## Parking Lot` (H2)

### Required body elements

- At least one checkbox line under `## Topics` using the exact placeholder triplet `{{topic}}`, `{{owner}}`, `{{estimated minutes}}`. Canonical form:

  ```
  - [ ] {{topic}} ({{owner}}, {{estimated minutes}})
  ```

### Allowed placeholders in this file

- `{{Meeting Title}}`
- `{{topic}}`
- `{{owner}}`
- `{{estimated minutes}}`

---

## Blueprint — `memory/meetings/_template/prep.md`

Maps to AC1, AC7, AC8.

### Frontmatter keys (in order)

No YAML frontmatter required. Same rule as `agenda.md`: if present, must be well-formed; if absent, harness does not fail.

### Body headings (in order)

1. `# Prep -- {{Meeting Title}}` (H1)
2. `## My Objectives` (H2)
3. `## Questions to Raise` (H2)
4. `## Attendee Context` (H2)
5. `## Prior Meeting History` (H2)
6. `## Related Tasks` (H2)
7. `## Commercial Context` (H2)

### Required body elements

- Each H2 section may contain an HTML-comment hint or guidance prose.
- Generic references to `memory/people/` (for attendee context) and to CRM / deal context (for commercial context) are allowed. Do NOT reference a specific CRM product name if it is not already in the gtd-life source; do NOT introduce new product names beyond what the source carries.

### Allowed placeholders in this file

- `{{Meeting Title}}`

---

## Blueprint — `memory/meetings/_template/transcript.md`

Maps to AC1, AC7, AC8.

### Frontmatter keys (in order)

No YAML frontmatter required.

### Body headings (in order)

1. `# Transcript -- {{Meeting Title}}` (H1)

### Required body elements (in order)

- A `**Source:**` line (bold-label line). Values may enumerate neutral transcription-tool names carried from the gtd-life source (`gong | teams | manual | otter | none` acceptable; the enumeration is tool-name-only and contains zero banned tokens).
- A `**Recording:**` line (bold-label line).
- A horizontal rule line consisting of exactly `---` on its own line, separating the header from the transcript body placeholder.
- An HTML-comment placeholder below the rule indicating where the raw transcript text lands (e.g. `<!-- paste raw transcript here -->`).

### Allowed placeholders in this file

- `{{Meeting Title}}`

---

## Blueprint — `memory/people/_template.md`

Maps to AC2, AC7, AC8.

### Frontmatter keys (in order)

1. `type: person`
2. `company: ""`
3. `role: ""`
4. `email: ""`
5. `last_1on1: ""`
6. `open_action_items: []`
7. `created: YYYY-MM-DD`
8. `updated: YYYY-MM-DD`
9. `tags: []`

### Body headings (in order)

1. `# {{Name}}` (H1)
2. `## Overview` (H2)
3. `## 1-on-1 History` (H2)
4. `## Action Items` (H2)
5. `## Notes` (H2)

### Required body elements

- Under `## Overview`, the following bold-label lines must each appear at least once (order as listed):
  - `**Company**` (value may be a placeholder such as `{{company}}`)
  - `**Role**` (value may be a placeholder such as `{{role}}`)
  - `**Reports to**` (value may be a placeholder such as `{{manager or "N/A"}}`)
  - `**Direct reports**` (value may be a placeholder such as `{{count or "N/A"}}`)
- Under `## 1-on-1 History`, an HTML comment or bulleted guidance referencing `{{person}}`, `{{date}}`, and/or recurring-note structure is permitted.
- Under `## Action Items`, a checkbox placeholder using `{{action item}}` is permitted.

### Allowed placeholders in this file

- `{{Name}}`
- `{{company}}`
- `{{role}}`
- `{{manager or "N/A"}}`
- `{{count or "N/A"}}`
- `{{person}}`
- `{{action item}}`
- `{{date}}`

Note: the literal text `1-on-1` is NOT a banned token — it contains no banned-term substring under the boundary-guarded regex. It is preserved from the gtd-life source as-is.

---

## Blueprint — `memory/decisions/_template.md`

Maps to AC3, AC7, AC8.

### Frontmatter keys (in order)

1. `type: decision`
2. `status: open`
3. `date: YYYY-MM-DD`
4. `context: ""`
5. `stakeholders: []`
6. `created: YYYY-MM-DD`
7. `updated: YYYY-MM-DD`
8. `tags: []`

### Body headings (in order)

1. `# {{Decision Title}}` (H1)
2. `## Context` (H2)
3. `## Alternatives` (H2)
4. `### Option A: {{name}}` (H3, under `## Alternatives`)
5. `### Option B: {{name}}` (H3, under `## Alternatives`)
6. `## Decision` (H2)
7. `## Rationale` (H2)
8. `## Implications` (H2)

### Allowed placeholders in this file

- `{{Decision Title}}`
- `{{name}}`

---

## Blueprint — `memory/reference/_template.md`

Maps to AC4, AC7, AC8.

### Frontmatter keys (in order)

1. `type: reference`
2. `created: YYYY-MM-DD`
3. `updated: YYYY-MM-DD`
4. `context: ""`
5. `related_to: []`
6. `tags: []`

### Body headings (in order)

1. `# {{Reference Title}}` (H1)
2. `## Summary` (H2)
3. `## Details` (H2)
4. `## Links` (H2)
5. `## Related notes` (H2)

### Required body elements

- An inline HTML comment under `## Related notes` explaining cross-linking via the `related_to` frontmatter field is permitted and preserved from source. The comment must contain zero banned tokens.

### Allowed placeholders in this file

- `{{Reference Title}}`

---

## Blueprint — `memory/inbox/_template.md`

Maps to AC5, AC7, AC8.

### Frontmatter keys (in order)

1. `type: inbox`
2. `created: YYYY-MM-DD`
3. `context: ""`
4. `tags: []`

### Body headings (in order)

1. `# Thought` (H1, literal — no placeholder)

### Scrub / repair rules

- The gtd-life source carries `context: vixxo | revivago | personal` as a VALUE (not a comment). REWRITE to `context: ""`. An optional inline comment `# e.g. vixxo | customer | internal` is allowed but not required.
- The `context:` value in the emitted file MUST be the empty string `""`. The personal-enumeration value from the source is forbidden.

### Allowed placeholders in this file

None. This is a minimal-capture template with a literal `# Thought` heading and no body placeholders.

Plus the literal token `YYYY-MM-DD` in frontmatter only.

---

## Blueprint — `memory/appreciations/_template.md` (REPAIRED shape)

Maps to AC6, AC7, AC8. This file REPAIRS a malformed gtd-life source; the port MUST NOT copy the defect.

### Frontmatter keys (in order) — properly-formed

1. `type: appreciation`
2. `date: YYYY-MM-DD`
3. `recipient: ""`
4. `context: ""`
5. `tags: []`

Frontmatter MUST open with `---` on line 1 and close with `---` on a subsequent line BEFORE the first body heading. A properly-formed emission looks like:

```
---
type: appreciation
date: YYYY-MM-DD
recipient: ""
context: ""
tags: []
---

# {{Recipient or Moment}}

## What

<!-- What are you appreciating? -->

## Why it mattered

<!-- Why is this worth capturing? -->
```

### Body headings (in order)

1. `# {{Recipient or Moment}}` (H1)
2. `## What` (H2)
3. `## Why it mattered` (H2)

### Repair rules (mandatory, not optional)

- The gtd-life source opens with `---` and then writes `## type: appreciation` as a Markdown H2 heading inside the (unclosed) frontmatter block. This is a YAML syntax error in the source. The port MUST:
  - Emit `type: appreciation` as a YAML KEY inside the frontmatter block (no `##` prefix).
  - Close the frontmatter with `---` before any H1 heading.
  - Emit the H1 `# {{Recipient or Moment}}` after the closing `---` and one blank line.
- The emitted file MUST NOT contain the line `## type: appreciation` (this is the "repaired, not copied" assertion the harness enforces in `check_task3`).

### Allowed placeholders in this file

- `{{Recipient or Moment}}`

Plus the literal token `YYYY-MM-DD` in frontmatter only.

---

## Banned-term lock

The harness MUST reject any of the following 17 tokens, case-insensitive, under the boundary-guarded POSIX-ERE regex `(^|[^A-Za-z])TOKEN($|[^A-Za-z])`, across every one of the nine ported template files.

Tokens (newline-separated, lowercase canonical form):

```
derek
neighbors
revivago
benji
flowtopic
gtd-life
gtdlife
wyoming
cheyenne
family
home
blog
wife
son
daughter
dog
personal
```

### Composite boundary-guarded regex (for harness reuse)

```
(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog|personal)($|[^A-Za-z])
```

Invoked as `grep -iE` for case-insensitivity.

### Additional path-reference scrub

Beyond the boundary-guarded regex, the harness runs a fixed-string scan (`grep -Fq`) for:

- `gtd-life` (catches the hyphenated path reference that the boundary guard's alpha-class treats as a match already, but fixed-string is a defense-in-depth check)
- `~/Public/gtd-life` (source-repo filesystem path)
- `/gtd-life/` (source-repo embedded path)

Any match of any of these literal strings FAILS the scrub.

### Rationale summary (carried forward from Story 2.1 → 2.4, extended by Story 3.1)

- `derek`, `neighbors` — operator's real name (Story 2.1)
- `revivago`, `flowtopic` — personal business tokens (Story 2.2)
- `benji` — personal task-system token (Story 2.3 / 2.4)
- `gtd-life`, `gtdlife` — source-repo reference (Story 2.3)
- `wyoming`, `cheyenne` — example PII geography tokens; templates must not encode any specific location
- `family`, `wife`, `son`, `daughter`, `dog` — family / personal-life tokens; work-only scope
- `home` — personal-life token
- `blog` — personal output channel; gtd-life has `memory/blog-ideas/` and the template must not reference it
- `personal` — Phase-4 F4 review fix; defence-in-depth against residual `personal` scope enumerations in inline comments or placeholder copy (frontmatter VALUES already scrubbed via Defect #2 / Defect #3 repairs in the port, but this token catches any later regression)

---

## Placeholder vocabulary lock

### Allowlist (tokens that MAY appear in any ported template file)

Only the following `{{...}}` tokens are permitted, across all nine files. Any `{{...}}` token extracted from a ported file that is not in this set FAILS the placeholder-vocabulary gate.

```
{{Meeting Title}}
{{Name}}
{{topic}}
{{owner}}
{{estimated minutes}}
{{person}}
{{action}}
{{action item}}
{{date}}
{{company}}
{{role}}
{{manager or "N/A"}}
{{count or "N/A"}}
{{Decision Title}}
{{Reference Title}}
{{Recipient or Moment}}
{{name}}
```

### Additional literal tokens (non-placeholder, allowed in frontmatter only)

- `YYYY-MM-DD` — date shape token
- `HH:MM` — time shape token

These are NOT `{{...}}` placeholders; they are literal plaintext tokens indicating the expected value shape inside double-quoted or unquoted YAML scalar values. They may appear in any frontmatter and are not extracted by the `grep -oE '\{\{[^}]+\}\}'` placeholder enumeration.

### Forbidden placeholder forms (ALL files)

- Single-brace `{placeholder}` — confusable with shell-variable interpolation
- Angle-bracket `<placeholder>` — confusable with XML/HTML tags
- Percent-wrapped `%placeholder%` — confusable with Windows environment variables
- Dollar-brace `${placeholder}` — confusable with shell-variable interpolation

The harness runs targeted regex probes for each forbidden form and fails if any match.

### Forbidden specific placeholder names (even in `{{...}}` form)

- `{{employee_name}}` — identity-file placeholder (owned by `.cursor/rules/agent-identity.mdc`, `agents/personas/work.md`, and Story 3.3's `memory/me/identity.md`). Memory-vault templates describe the shape of a future note instance, not the operator's identity.
- `{{employee_role}}` — same rationale.
- `{{employee_department}}` — same rationale.
- `{{employee_manager}}` — same rationale.
- `{{employee_email}}` — same rationale (Story 5.2 wizard scope).

Any occurrence of these five tokens in a ported template file FAILS the placeholder-vocabulary gate.

---

## Cross-AC coverage map

| AC | Lock |
| --- | --- |
| AC1 | `meeting.md` / `agenda.md` / `prep.md` / `transcript.md` blueprints (frontmatter + headings + doc-link table + bold-label lines + horizontal rule) |
| AC2 | `memory/people/_template.md` blueprint (frontmatter + headings + `## Overview` bold-label lines) |
| AC3 | `memory/decisions/_template.md` blueprint (frontmatter + headings + two H3 option sub-sections) |
| AC4 | `memory/reference/_template.md` blueprint (frontmatter + headings) |
| AC5 | `memory/inbox/_template.md` blueprint (frontmatter + `# Thought` heading + `context: ""` scrub) |
| AC6 | `memory/appreciations/_template.md` blueprint (REPAIRED properly-formed frontmatter + `## What` / `## Why it mattered` H2s + "repaired-not-copied" assertion) |
| AC7 | `## Banned-term lock` section + composite POSIX-ERE boundary-guarded regex + path-reference scrub |
| AC8 | `## Placeholder vocabulary lock` section (allowlist + literal tokens + forbidden forms + forbidden specific names) |
| AC9 | N/A at blueprint level; harness `check_task3` asserts file presence without introducing new `.gitkeep` sentinels |
| AC10 | Every section of this blueprint is consumed by the harness's `check_task2` (existence + required headers) and `check_task3` / `check_task4` (shape + scrub) gates |
| AC11 | N/A at blueprint level; harness `check_task6` invokes predecessor harnesses in `all` mode |
| AC12 | N/A at blueprint level; sprint-status lifecycle handled by Task 7 |
| AC13 | Blueprint scope is exactly nine template files + evidence artifacts + harness + sprint-status flip + this story file; any file outside that set is out of scope |
