# Story 3.1 Baseline Audit

Captured during Task 1 (Phase 2, Dev agent Amelia). This audit records the upstream `~/Public/gtd-life/memory/` template-file contents that Story 3.1 ports into the generic `assistants-template` vault, plus the per-file frontmatter/heading maps, banned-term scan of the source files, known defects that must be repaired (not copied) during the port, out-of-scope directories, placeholder vocabulary across source files, and the source-path → target-path mapping. Evidence here drives Task 2's canonical blueprint and Task 4's cross-file scrub. Source templates live outside this repository at `~/Public/gtd-life/memory/` and are read-only reference material — structure is ported verbatim with only the three specified repairs (see "Known defects requiring repair during port").

Scope lock: Story 3.1 targets exactly nine template files (four under `memory/meetings/_template/`, five as single `_template.md` files under `memory/{people,decisions,reference,inbox,appreciations}/`). The audit below enumerates those nine sources only.

## gtd-life source inventory

Enumerated on 2026-04-20 from `~/Public/gtd-life/memory/` (host: macOS darwin 25.4.0). All nine in-scope source files are plain UTF-8 Markdown.

| # | Source path | Bytes | Lines |
|---|-------------|-------|-------|
| 1 | `~/Public/gtd-life/memory/meetings/_template/meeting.md` | 823 | 41 |
| 2 | `~/Public/gtd-life/memory/meetings/_template/agenda.md` | 250 | 13 |
| 3 | `~/Public/gtd-life/memory/meetings/_template/prep.md` | 513 | 29 |
| 4 | `~/Public/gtd-life/memory/meetings/_template/transcript.md` | 306 | 10 |
| 5 | `~/Public/gtd-life/memory/people/_template.md` | 561 | 34 |
| 6 | `~/Public/gtd-life/memory/decisions/_template.md` | 588 | 36 |
| 7 | `~/Public/gtd-life/memory/reference/_template.md` | 506 | 26 |
| 8 | `~/Public/gtd-life/memory/inbox/_template.md` | 97 | 8 |
| 9 | `~/Public/gtd-life/memory/appreciations/_template.md` | 79 | 7 |

`~/Public/gtd-life/memory/_templates/` also exists (alternate single-file layout: `decision.md`, `inbox.md`, `meeting.md`, `person.md`, `reference.md`). This alternate tree is OUT OF SCOPE for Story 3.1 (see "Out-of-scope directories" below).

## Per-file frontmatter + heading map

### 1. `memory/meetings/_template/meeting.md`

- Frontmatter keys (in source order): `type`, `date`, `time`, `attendees`, `context`, `location`, `join_url`, `organizer`, `recurring`, `action_items`, `created`, `updated`, `tags`
- Frontmatter values: `type: meeting`, `date: YYYY-MM-DD`, `time: "HH:MM"`, `attendees: []`, `context: "" # vixxo | revivago | personal` **(DEFECT — inline comment enumerates banned context; see Defect #3 below)**, `location: ""`, `join_url: ""`, `organizer: ""`, `recurring: false`, `action_items: []`, `created: YYYY-MM-DD`, `updated: YYYY-MM-DD`, `tags: []`
- H1: `# {{Meeting Title}}`
- Doc-link table: `| Doc | Link |` with rows `| Prep | [prep.md](prep.md) |`, `| Agenda | [agenda.md](agenda.md) |`, `| Transcript | [transcript.md](transcript.md) |`
- H2 sections (in order): `## Summary`, `## Notes`, `## Decisions`, `## Action Items`
- Body placeholders: `{{Meeting Title}}`, `{{person}}`, `{{action}}`, `{{date}}` (one checkbox line: `- [ ] {{person}}: {{action}} (due: {{date}})`)

### 2. `memory/meetings/_template/agenda.md`

- No frontmatter (body-only template).
- H1: `# Agenda -- {{Meeting Title}}`
- H2 sections (in order): `## Topics`, `## Parking Lot`
- Body placeholders: `{{Meeting Title}}`, `{{topic}}`, `{{owner}}`, `{{estimated minutes}}`
- Checkbox line: `- [ ] {{topic}} ({{owner}}, {{estimated minutes}})`

### 3. `memory/meetings/_template/prep.md`

- No frontmatter (body-only template).
- H1: `# Prep -- {{Meeting Title}}`
- H2 sections (in order): `## My Objectives`, `## Questions to Raise`, `## Attendee Context`, `## Prior Meeting History`, `## Related Tasks`, `## Commercial Context`
- Body placeholders: `{{Meeting Title}}`
- Contains generic references to `memory/people/` (under `## Attendee Context`) and `Salesforce / deal context` (under `## Commercial Context`) — generic and portable; preserve.

### 4. `memory/meetings/_template/transcript.md`

- No frontmatter (body-only template).
- H1: `# Transcript -- {{Meeting Title}}`
- Header lines: `**Source:** <!-- gong | teams | manual | otter | none -->`, `**Recording:** <!-- URL or path if available -->`
- Horizontal rule `---` separates header from transcript body.
- Body placeholders: `{{Meeting Title}}`
- Note: the `Source:` enumeration (`gong | teams | manual | otter | none`) names neutral tool brands; none are banned tokens.

### 5. `memory/people/_template.md`

- Frontmatter keys (in source order): `type`, `company`, `role`, `email`, `last_1on1`, `open_action_items`, `created`, `updated`, `tags`
- Frontmatter values: `type: person`, `company: ""`, `role: ""`, `email: ""`, `last_1on1: ""`, `open_action_items: []`, `created: YYYY-MM-DD`, `updated: YYYY-MM-DD`, `tags: []`
- H1: `# {{Name}}`
- H2 sections (in order): `## Overview`, `## 1-on-1 History`, `## Action Items`, `## Notes`
- Bold-label lines inside `## Overview`: `**Company**: {{company}}`, `**Role**: {{role}}`, `**Reports to**: {{manager or "N/A"}}`, `**Direct reports**: {{count or "N/A"}}`
- Body placeholders: `{{Name}}`, `{{company}}`, `{{role}}`, `{{manager or "N/A"}}`, `{{count or "N/A"}}`, `{{action item}}`

### 6. `memory/decisions/_template.md`

- Frontmatter keys (in source order): `type`, `status`, `date`, `context`, `stakeholders`, `created`, `updated`, `tags`
- Frontmatter values: `type: decision`, `status: open`, `date: YYYY-MM-DD`, `context: ""`, `stakeholders: []`, `created: YYYY-MM-DD`, `updated: YYYY-MM-DD`, `tags: []`
- H1: `# {{Decision Title}}`
- H2 sections (in order): `## Context`, `## Alternatives`, `## Decision`, `## Rationale`, `## Implications`
- H3 sections inside `## Alternatives` (in order): `### Option A: {{name}}`, `### Option B: {{name}}`
- Body placeholders: `{{Decision Title}}`, `{{name}}`

### 7. `memory/reference/_template.md`

- Frontmatter keys (in source order): `type`, `created`, `updated`, `context`, `related_to`, `tags`
- Frontmatter values: `type: reference`, `created: YYYY-MM-DD`, `updated: YYYY-MM-DD`, `context: ""`, `related_to: []`, `tags: []`
- H1: `# {{Reference Title}}`
- H2 sections (in order): `## Summary`, `## Details`, `## Links`, `## Related notes`
- Body placeholders: `{{Reference Title}}`
- Contains an inline explanatory comment under `## Related notes` that references generic siblings (`memory/people`, `memory/meetings`, `memory/companies`, `memory/decisions`). All generic; preserve.

### 8. `memory/inbox/_template.md`

- Frontmatter keys (in source order): `type`, `created`, `context`, `tags`
- Frontmatter values: `type: inbox`, `created: YYYY-MM-DD`, **`context: vixxo | revivago | personal` (DEFECT — see Defect #2 below)**, `tags: []`
- H1: `# Thought` (single heading, empty body)
- No placeholders.

### 9. `memory/appreciations/_template.md`

- **MALFORMED** frontmatter (see Defect #1 below). Source bytes literally:
  ```
  ---

  ## type: appreciation

  date: YYYY-MM-DD
  recipient: ""
  context: ""
  tags: []
  ```
- The `---` opener is present but the closing `---` is missing. `type: appreciation` is rendered as an H2 Markdown heading (`## type: appreciation`), not a YAML key. Keys `date`, `recipient`, `context`, `tags` appear as orphaned plain text inside the un-closed frontmatter region — not parseable as YAML.
- No H1, no body, no placeholders in the source.
- The port MUST emit a properly-formed file with closed `---` frontmatter, `type: appreciation` as a YAML key, H1 `# {{Recipient or Moment}}`, and H2 sections `## What` and `## Why it mattered`.

## Banned-term scan of source files

Regex: `(^|[^A-Za-z])(derek|neighbors|revivago|benji|flowtopic|gtd-life|gtdlife|wyoming|cheyenne|family|home|blog|wife|son|daughter|dog)($|[^A-Za-z])`, case-insensitive via `grep -iE`. Executed on 2026-04-20 against each of the nine source files.

| # | Source file | Hit count | Hits |
|---|-------------|-----------|------|
| 1 | `memory/meetings/_template/meeting.md` | 1 | line 6: `context: "" # vixxo | revivago | personal` (matches `revivago`) |
| 2 | `memory/meetings/_template/agenda.md` | 0 | clean |
| 3 | `memory/meetings/_template/prep.md` | 0 | clean |
| 4 | `memory/meetings/_template/transcript.md` | 0 | clean |
| 5 | `memory/people/_template.md` | 0 | clean (boundary-guarded regex correctly does not match `1-on-1`, `Direct reports`, `Notes`) |
| 6 | `memory/decisions/_template.md` | 0 | clean |
| 7 | `memory/reference/_template.md` | 0 | clean |
| 8 | `memory/inbox/_template.md` | 1 | line 4: `context: vixxo | revivago | personal` (matches `revivago`) |
| 9 | `memory/appreciations/_template.md` | 0 | clean |

**Summary:** two source files carry banned content (`revivago`, plus implicit `personal` enumeration) in `context:` scope markers — one as a comment (meeting.md) and one as a YAML value (inbox.md). Both must be scrubbed during the port. No occurrences of `derek`, `neighbors`, `benji`, `flowtopic`, `gtd-life`, `gtdlife`, `wyoming`, `cheyenne`, `family`, `home`, `blog`, `wife`, `son`, `daughter`, or `dog` in any of the nine in-scope source files.

Literal `gtd-life` string scan (`grep -F 'gtd-life'`): zero hits across all nine files. No source file references its own repository path.

## Known defects requiring repair during port

Three defects MUST be repaired (not copied) during the Story 3.1 port:

### Defect #1 — `appreciations/_template.md` malformed YAML frontmatter (STRUCTURAL REPAIR)

**Source bytes** (lines 1–7, 79 bytes, no closing `---`):
```
---

## type: appreciation

date: YYYY-MM-DD
recipient: ""
context: ""
tags: []
```

**Problems:** (a) `---` opens a YAML frontmatter block but never closes (no terminating `---`); (b) `## type: appreciation` is written as a Markdown H2 heading inside the would-be frontmatter region, not as a YAML key; (c) `date`, `recipient`, `context`, `tags` are orphaned plain text, not parseable YAML; (d) there is no H1, no body sections, and no trailing newline.

**Required port output:** a properly-formed file with `---` frontmatter opened on line 1 and closed on a subsequent line, `type: appreciation` emitted as a YAML key (no `##` prefix inside the frontmatter region), an H1 `# {{Recipient or Moment}}` body heading, and at least two H2 sections (`## What`, `## Why it mattered`) giving the template a useful shape. The ported file MUST NOT contain a line matching `^## type: appreciation$` — the harness's `check_task3` gate asserts this "repaired, not copied" property.

### Defect #2 — `inbox/_template.md` frontmatter has banned-scope VALUE (SCRUB)

**Source bytes** (line 4):
```
context: vixxo | revivago | personal
```

**Problems:** (a) the value enumerates `revivago` (banned) and `personal` (banned under AC7 Epic-3-added tokens); (b) pipe-or semantics are not valid YAML — YAML reads the whole string as `"vixxo | revivago | personal"`, not as a choice set.

**Required port output:** `context: ""` (empty string). An optional work-scoped inline comment is permitted (e.g. `# e.g. vixxo | customer | internal`) but must not enumerate `revivago`, `personal`, or any gtd-life-specific context value.

### Defect #3 — `meetings/_template/meeting.md` frontmatter has banned-scope inline COMMENT (SCRUB)

**Source bytes** (line 6):
```
context: "" # vixxo | revivago | personal
```

**Problems:** the VALUE is correctly the empty string but the INLINE COMMENT enumerates `revivago` and `personal` — both banned tokens under the Story 3.1 banned-term set.

**Required port output:** either remove the comment entirely (leaving `context: ""`), or rewrite the comment to a work-scoped enumeration such as `# e.g. vixxo | customer | internal`. Under no circumstances may the comment contain `revivago`, `personal`, or any other banned token.

## Out-of-scope directories

The following gtd-life `memory/` subdirectories are explicitly OUT OF SCOPE for Story 3.1. The port MUST NOT create matching directories or files in the assistants-template repo as part of this story:

| gtd-life directory | Reason OUT OF SCOPE for Story 3.1 |
|--------------------|-----------------------------------|
| `~/Public/gtd-life/memory/_templates/` | Alternate top-level single-file layout (`decision.md`, `inbox.md`, `meeting.md`, `person.md`, `reference.md`). Story 3.1 enforces the per-directory `_template.md` / `_template/` convention, not this alternate tree. |
| `~/Public/gtd-life/memory/daily/` | Daily-notes directory; template and workflow are owned by Story 3.2 (`.obsidian/` Daily Notes plugin config). |
| `~/Public/gtd-life/memory/companies/` | Company-context content; not in any current Epic 3 story. |
| `~/Public/gtd-life/memory/blog-ideas/` | Personal output channel; `blog` is a Story 3.1 banned token. Not portable. |
| `~/Public/gtd-life/memory/vixxo/` | Company-specific Vixxo content (org-chart, people, decisions, meetings with real attendees). Content, not template. Not in scope for any Story 3.x. |
| `~/Public/gtd-life/memory/me/` | Identity + preferences for the operator. Story 3.3 populates `memory/me/identity.md` and `memory/me/preferences.md` with `scope: work` frontmatter and placeholder bodies. Story 3.1 does not create `memory/me/`. |
| `~/Public/gtd-life/memory/.obsidian/` | Obsidian app config directory. Story 3.2 ports a portable subset (Templates plugin, Daily Notes, graph view) without Derek's workspace cache. Out of scope for 3.1. |

No Story 3.1 target file or directory should reference any of the above paths.

## Placeholder vocabulary across source files

Aggregated `{{...}}` placeholder extraction across the nine in-scope source files (regex `grep -oE '\{\{[^}]+\}\}'`, deduplicated):

| Placeholder | Present in source file(s) |
|-------------|---------------------------|
| `{{Meeting Title}}` | meeting.md, agenda.md, prep.md, transcript.md |
| `{{person}}` | meeting.md |
| `{{action}}` | meeting.md |
| `{{date}}` | meeting.md |
| `{{topic}}` | agenda.md |
| `{{owner}}` | agenda.md |
| `{{estimated minutes}}` | agenda.md |
| `{{Name}}` | people/_template.md |
| `{{company}}` | people/_template.md |
| `{{role}}` | people/_template.md |
| `{{manager or "N/A"}}` | people/_template.md |
| `{{count or "N/A"}}` | people/_template.md |
| `{{action item}}` | people/_template.md |
| `{{Decision Title}}` | decisions/_template.md |
| `{{name}}` | decisions/_template.md (Option A/B names) |
| `{{Reference Title}}` | reference/_template.md |
| `{{Recipient or Moment}}` | **NOT PRESENT** in source `appreciations/_template.md` (malformed source has no body); the port MUST add this placeholder as the H1 of the repaired file. |

**Form compliance:** every placeholder in every in-scope source file uses the double-curly-brace form `{{…}}`. Scans for forbidden forms in the source:
- single-brace `{placeholder}` — zero hits across all nine source files (`grep -oE '(^|[^{])\{[^{][^}]*\}' ...`)
- XML-style `<placeholder>` — zero hits (HTML comments `<!-- ... -->` are the only `<...>` constructs; they are comments, not placeholders)
- percent-wrapped `%placeholder%` — zero hits
- shell-style `${placeholder}` — zero hits
- forbidden identity placeholders `{{employee_name}}` / `{{employee_role}}` — zero hits (those belong to `.cursor/rules/agent-identity.mdc` and `agents/personas/work.md`, not to memory templates)

**Literal date/time tokens** (`YYYY-MM-DD`, `HH:MM`) are present in frontmatter values across meeting.md, people, decisions, reference, inbox, and (after repair) appreciations — these are canonical ISO-8601-shaped placeholder literals, explicitly allowed by AC8.

The Story 3.1 placeholder allowlist (per AC8 / Task 2 blueprint) is the union of the allowed placeholders above plus `YYYY-MM-DD` and `HH:MM`. The harness `check_task4` gate enforces this allowlist by extracting all `{{…}}` tokens from every ported file and failing on any token not in the list.

## Mapping: source path → target path

| # | Source path (read-only reference) | Target path (ported into assistants-template) | Port mode |
|---|-----------------------------------|-----------------------------------------------|-----------|
| 1 | `~/Public/gtd-life/memory/meetings/_template/meeting.md` | `memory/meetings/_template/meeting.md` | port-verbatim + scrub Defect #3 (inline `context:` comment) |
| 2 | `~/Public/gtd-life/memory/meetings/_template/agenda.md` | `memory/meetings/_template/agenda.md` | port-verbatim (source is already clean) |
| 3 | `~/Public/gtd-life/memory/meetings/_template/prep.md` | `memory/meetings/_template/prep.md` | port-verbatim (source is already clean) |
| 4 | `~/Public/gtd-life/memory/meetings/_template/transcript.md` | `memory/meetings/_template/transcript.md` | port-verbatim (source is already clean) |
| 5 | `~/Public/gtd-life/memory/people/_template.md` | `memory/people/_template.md` | port-verbatim (source is already clean) |
| 6 | `~/Public/gtd-life/memory/decisions/_template.md` | `memory/decisions/_template.md` | port-verbatim (source is already clean) |
| 7 | `~/Public/gtd-life/memory/reference/_template.md` | `memory/reference/_template.md` | port-verbatim (source is already clean) |
| 8 | `~/Public/gtd-life/memory/inbox/_template.md` | `memory/inbox/_template.md` | port-verbatim + scrub Defect #2 (frontmatter `context:` VALUE) |
| 9 | `~/Public/gtd-life/memory/appreciations/_template.md` | `memory/appreciations/_template.md` | REPAIR Defect #1 (malformed frontmatter) + author body (H1 + `## What` + `## Why it mattered`) |

All nine target paths are new files (none exist in `assistants-template` yet — confirmed by `find memory -name '_template*' -type f` at audit time returning empty). No file-replacement, no merge, no pre-existing content collision. Trailing newlines, UTF-8 encoding, and LF line endings are required per AC1 / Dev Notes "Architectural constraints".

---

End of Story 3.1 Baseline Audit. Task 2 (canonical blueprint) consumes the frontmatter/heading maps and placeholder allowlist above. Tasks 3a–3f consume the source → target mapping and the three defect repairs.
