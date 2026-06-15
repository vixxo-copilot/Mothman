# PM survey review packet

## Purpose

Use this packet after the survey PDF and its before/after photos have been
read (SKILL.md Steps 2-3) and scored against
[`quality-rubric.md`](./quality-rubric.md). The packet answers one operating
question: **is this PM survey good enough to trust, and what follow-on work or
correction does it create?**

Keep every field tied to evidence: quote the survey's own words, name the
specific photo. Do not collapse fields into a prose paragraph.

## Verdict taxonomy

### Survey verdict (Field 1)

Use exactly one survey verdict per survey.

| Verdict | Meaning |
|---|---|
| `pass` | Required data complete, before/after photo coverage present and legible, additional-repairs section answered (even if "none"). Trustworthy as-is. |
| `pass-with-gaps` | Substantively complete and trustworthy, but one or more minor gaps (a missing reading, one weak photo, a soft recommendation) worth noting. |
| `data-incomplete` | Required survey fields are missing or blank (asset id, readings, dates, technician, checklist marks, signature). Cannot fully trust the survey. |
| `photos-insufficient` | Data may be fine, but before/after photo coverage is missing, partial, illegible, mislabeled, or does not show the asset/condition. |
| `fail` | Multiple core gaps, internal contradiction, or evidence the survey does not reflect work actually performed. Send back. |

When both data and photos fail, use `fail`. When exactly one dimension fails,
use the matching specific verdict (`data-incomplete` or `photos-insufficient`).

### Photo coverage (Field 3)

Use exactly one per survey.

| Coverage | Meaning |
|---|---|
| `complete` | Before AND after photos present for the work performed, each legible, in focus, and clearly showing the asset/condition. |
| `partial` | Some required shots present, but missing a before/after pair, or some shots are weak (blurry, dark, wrong subject). |
| `missing` | No usable before/after photos. Photos absent, or all present photos are illegible / not of the asset. |

### Additional-repairs detail (per item in Field 4)

For each additional repair the survey identifies, tag whether it is actionable.

| Tag | Meaning |
|---|---|
| `actionable` | Enough detail to scope/quote: what, where, asset, severity, and (ideally) a photo. |
| `needs-detail` | A repair is named but lacks the detail to action (no location, no asset, no severity, no photo). |
| `none-stated` | The survey states no additional repairs are needed. |

## Per-survey packet

```markdown
PM survey review - SR <number> | <customer> | <site> | <trade> | survey completed <YYYY-MM-DD>

0. Survey completed: <YYYY-MM-DD> (the survey submission/completion date - STANDARD field; source: the pmSurvey attachment createdDate, or the survey PDF's creationDate metadata, which equals the submission timestamp)
1. Survey verdict: <pass | pass-with-gaps | data-incomplete | photos-insufficient | fail>
2. Data completeness: <present: ...; missing: ...> (asset id, readings/measurements, date, technician, checklist marks, signature)
3. Before/after photos: <complete | partial | missing> - <quality note: legible? in focus? shows the asset/condition? before+after paired?>
4. Additional repairs flagged:
   - <repair 1> - <actionable | needs-detail> - <one-line evidence quote from the survey>
   - <repair 2> - ...
   - (or "none-stated")
5. Discrepancies: <survey says X but photos/data show Y; or "none found">
6. Owner and next action: <named person/role> - <the exact correction or follow-on, with check-back>
7. Confidence and evidence gaps: <high | medium | low> - <what was unreadable/unavailable that would change the verdict>
```

## Field rules

- **Field 0 (survey completed date) is standard on every packet and every
  report row.** It is the date the survey was actually submitted/completed.
  Source, in order of preference: the `pmSurvey` attachment's `createdDate`
  from the VixxoLink attachment listing; or, if working from a downloaded PDF,
  the survey PDF's `creationDate` metadata (which equals the submission
  timestamp). Always populate it; never leave it blank when the survey exists.
- **Field 1 is the survey-quality verdict only.** It judges the survey, not the
  field work. A complete survey of a unit that still needs a repair is a `pass`
  with an `actionable` item in Field 4.
- **Field 2 lists specifics, not a grade.** Name the present fields and the
  missing fields. "Missing: discharge temp reading, technician signature" beats
  "incomplete."
- **Field 3 must judge the photo, not just count it.** A blurry or wrong-subject
  photo is not coverage. If a photo is labeled "after" but shows a before
  condition, say so and treat coverage as `partial` or `missing`.
- **Field 4 separates the repair finding from the survey verdict.** List every
  additional repair the survey identifies, each with the actionable tag and a
  literal quote. If the survey states none, write `none-stated`.
- **Field 5 catches contradictions.** Survey checkbox says "pass" but the photo
  shows a failed/corroded part; readings out of spec but marked OK; "after"
  photo identical to "before." If none, say "none found."
- **Field 6 must be actionable.** Name the owner by role when no person is
  available (Facilities Lead (FL) for additional-repair scope/quotes; PM
  program team for survey-quality verification incl. empty/zeroed and
  weak-photo surveys; CSM / account owner for customer decisions; asset master
  owner for asset-data write-back). Note: the SPM does **not** chase the SP for
  repair scope — route follow-on repairs to the FL. Every owner gets a
  check-back: next business day for a failed survey blocking close, 3 business
  days for medium, 1 week for low.
- **Field 7 calibrates confidence.** Low confidence means the next action is to
  get a readable artifact (re-pull the PDF, request better photos), not to
  trust the verdict.

## Owner defaults

| Finding | Default owner |
|---|---|
| Incomplete / illegible / empty / zeroed survey (verify PM performed) | PM program team / PM coordinator |
| Missing or weak before/after photos | PM program team (SP to re-supply) |
| Additional repair needing a quote / return visit | Facilities Lead (FL) |
| Customer decision or approval | CSM / account owner |
| Asset-data gap (no asset id, no readings baseline) | Asset master owner |
| Recurring survey-quality pattern across an SP | PM program team / SP scorecard owner |

> The SPM does not follow up with the SP for repair scope. Repair scope and
> quote conversion route to the **Facilities Lead (FL)**; survey-quality and
> "was the PM actually done" verification route to the **PM program team**.

## Cohort summary

Start (or end) multi-survey runs with this block.

```markdown
PM survey review - cohort summary

Scope: <customer / trade / SP / date window>
Surveys reviewed: <n>
Verdicts: pass <n>, pass-with-gaps <n>, data-incomplete <n>, photos-insufficient <n>, fail <n>
Photo coverage: complete <n>, partial <n>, missing <n>
Additional repairs: <n> surveys with actionable items, <n> with needs-detail, <n> none-stated
Top repeated gaps: <top 3-5 gaps with counts, e.g. "missing after-photo: 6 surveys">
Recommended action capture: <actions with owner/check-back, or "none">
SP / account signal: <durable pattern worth a scorecard or onboarding conversation, or "none">
```

## Escalation threshold

Escalate the cohort, not just the survey, when any gap repeats across 3 or more
surveys in the run, when a single SP produces repeated `fail` / `data-incomplete`
verdicts, or when actionable additional repairs are being surfaced but not
converted into follow-on SRs/quotes.
