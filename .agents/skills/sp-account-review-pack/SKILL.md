---
name: sp-account-review-pack
description: >-
  Builds a consolidated Account Review PDF pack for a named Vixxo service
  provider (SP name + SP number). Runs Service Provider Vetting Analyst by
  default (user may bypass), gathers Outlook/Teams/calendar communications,
  optional phone-log screenshots, merges related PDFs with cover/TOC/bookmarks,
  and appends state license-scope notes (MA Construction Supervisor License
  fully cited; other states stubbed). Use when the user asks for an SP account
  review pack, communications timeline PDF, combined vetting/licensing PDF,
  or "Account Review - {SP} {SP#}" deliverable.
---

# SP Account Review Pack

Work-only skill that produces a single downloadable **Account Review** PDF for
a named service provider.

Default output path:

```text
~/Downloads/Account Review - {SP Legal or Trade Name} {SP#}.pdf
```

Example: `Account Review - Ezzi Property Group KS69888.pdf`

## When to use

- "Build an account review pack for {SP}"
- "Combine vetting + email timeline into one PDF"
- "Account review PDF for {SP#}"
- Communications timeline + phone logs + license appendices for an SP
- Follow-up after license/LOS disputes (e.g. CSL vs licensed trades)

## Required inputs

Ask only for what is missing:

| Field | Required | Notes |
| --- | --- | --- |
| SP name | Yes | Legal or trade name used in mail/search |
| SP number | Yes | e.g. `KS69888` |
| Primary state(s) | Yes for license-scope appendix | Determines which appendix stubs/full notes to include |
| Contact emails / phones | Optional | Improves mail/Teams/phone matching |
| Bypass vetting? | Optional | Default **no** (run vetting) |
| Extra PDFs to merge | Optional | Paths already on disk (licenses, coverage exports, prior vetting PDFs) |
| Phone-log screenshots | Optional | Image paths to embed in timeline section |

## Vetting step (default on, bypassable)

**Default:** Run [service-provider-vetting-analyst](../service-provider-vetting-analyst/SKILL.md)
for the named company/state and include its PDF/markdown outputs in the pack.

**Bypass** when the user says any of:

- "bypass vetting"
- "skip vetting"
- "vetting already done"
- "use existing vetting PDF"
- supplies a finished vetting PDF and asks not to re-run

When bypassed:

1. Note `Vetting: bypassed` on the cover page.
2. Still merge any user-supplied vetting PDF if provided.
3. Do not invent grades or license findings.

When not bypassed:

1. Follow `service-provider-vetting-analyst` exactly (source-backed; "Not Found" when unverified).
2. Export/save the vetting report PDF into the working set before combine.
3. Prefer Downloads or skill `.tmp/` for intermediate artifacts.

## Workflow

Follow [reference/workflow.md](reference/workflow.md). Summary:

1. **Confirm inputs** — SP name, SP#, state(s), vetting on/bypass, extras.
2. **Vetting** — run or bypass per above.
3. **Communications scan** (Microsoft 365 Graph / MCP only):
   - Outlook: company name, contact names, emails, SP#
   - Teams chat search: same terms (note internal mentions vs meetings)
   - Calendar / event search: attendees and subjects; discard false positives
   - Optional: phone screenshots → structured call-attempt table
4. **License artifacts** — include user-supplied license PDFs; do not fabricate.
5. **License-scope appendix** — include full note for MA CSL when Massachusetts
   is in scope; include stubs for other requested states using
   [reference/license-scope-appendices.md](reference/license-scope-appendices.md).
   Full MA citations:
   [reference/ma-csl-scope.md](reference/ma-csl-scope.md).
6. **Combine** — cover + TOC + bookmarks via
   `scripts/combine_account_review_pdf.py`.
7. **Deliver** — open/save the Account Review PDF; report page map.

## Section order (default pack)

1. Cover & Table of Contents  
2. Full SP Vetting Report *(omit section if bypassed and no PDF supplied)*  
3. License Vetting / license artifacts *(if present)*  
4. Email / Teams / phone Communication Timeline  
5. Supporting license images/PDFs (HIC, trade cards, etc.)  
6. Appendix — License Scope Notes (state-specific)

Reorder only if the user asks.

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/combine_account_review_pdf.py` | Cover + TOC + merge PDFs + bookmarks → Downloads |
| `scripts/render_comms_timeline_pdf.py` | Communications timeline PDF from JSON |
| `scripts/render_license_scope_appendix.py` | MA CSL appendix and/or state stubs → PDF |

Dependencies: `reportlab`, `pypdf` (Python 3).

### Combine example

```bash
python .agents/skills/sp-account-review-pack/scripts/combine_account_review_pdf.py \
  --sp-name "Ezzi Property Group" \
  --sp-number KS69888 \
  --section "Full SP Vetting Report=C:/Users/…/Downloads/Ezzi Property Group - KS69888 - Full SP Vetting Report.pdf" \
  --section "License Vetting=C:/Users/…/Downloads/Ezzi Property Group - KS69888 - License Vetting.pdf" \
  --section "Email Communication Timeline=C:/Users/…/Downloads/Ezzi-Property-Group-Email-Timeline.pdf" \
  --section "MA HIC License=C:/Users/…/Downloads/Ezzi Property Group - KS69888 - MA HIC License exp 2028-01-16.pdf" \
  --appendix-states MA \
  --out "$USERPROFILE/Downloads/Account Review - Ezzi Property Group KS69888.pdf"
```

## Guardrails

- Work context only. No outbound email/Teams sends unless explicitly approved
  (draft-then-approve).
- Do not invent licenses, meetings, or call logs. Cite Graph results and
  provided screenshots only.
- CSL / GC-style credentials ≠ proof of self-perform licensed trades — use the
  license-scope appendix pattern; expand stubs with official sources before
  treating them as complete.
- Prefer existing official URLs from
  `service-provider-vetting-analyst/reference/` when filling stubs.
- Keep intermediate files under skill `.tmp/` or Downloads; do not commit
  PII-heavy dumps to git.

## Related skills

- [service-provider-vetting-analyst](../service-provider-vetting-analyst/SKILL.md) — default vetting engine
- Contractor licensing references under that skill for board URLs by state
