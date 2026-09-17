---
name: mothman-skills-catalog
description: >-
  Regenerates Crystal Gagner's Mothman skills catalog PDF from top-level
  .agents/skills/*/SKILL.md frontmatter, with a featured section for skills
  Crystal planned specifically. Use when the user asks to list skills we
  developed, export the skills catalog, refresh the skills PDF, or update
  the periodic skills inventory.
---

# Mothman Skills Catalog

Work-only inventory of skills in this workspace. Reads each top-level
`SKILL.md` (name + description) and writes a dated PDF. Nested copies
inside a skill folder (`.check-work`, `.tmp`) are ignored.

## When to use

- "List the skills we've developed"
- "Export skills catalog to PDF"
- "Refresh / update the skills PDF"
- "I can't find the skills catalog PDF"

## Refresh command

```bash
python .agents/skills/mothman-skills-catalog/scripts/export_skills_catalog.py
```

Default outputs (same file, two copies):

- `~/Downloads/Mothman Skills Catalog.pdf`
- `~/Desktop/Mothman Skills Catalog.pdf`
- `.tmp/mothman-skills-catalog/Mothman Skills Catalog.pdf` (workspace copy)

## Sections

1. **Planned specifically** — Crystal/Mothman-authored skills (`planned-skills.json` plus auto-detect: `mothman-*`, `provenance: mothman`, Crystal author)
2. **Other workspace skills** — remaining non-BMAD skills
3. **Inherited BMAD** — `bmad-*` from the assistants template

Do not send the PDF outbound unless Crystal explicitly approves.
