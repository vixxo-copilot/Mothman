# SP Account Review Pack — Workflow

## Operator checklist

1. Collect SP name, SP#, primary operating state(s).
2. Confirm vetting mode:
   - **Run** (default) → invoke `service-provider-vetting-analyst`
   - **Bypass** → user said skip/bypass / supplied finished vetting PDF only
3. Scan communications (M365 MCP):
   - Mail: `"Company Name"`, contact names, emails, SP#
   - Teams chatMessage search for same terms
   - Calendar/event search; verify attendees before claiming a meeting
4. Accept optional phone-log screenshots; transcribe into structured rows
   (date, time, number, direction, duration).
5. Gather on-disk PDFs to merge (vetting, license cards, HIC, coverage, etc.).
6. Build communications timeline PDF (`render_comms_timeline_pdf.py`) when
   thread volume warrants a standalone section.
7. Build license-scope appendix PDF for requested states
   (`render_license_scope_appendix.py` + `license-scope-appendices.md`).
8. Combine with `combine_account_review_pdf.py`.
9. Hand user the Downloads path + TOC page map.

## Naming

```text
Account Review - {SP Name} {SP#}.pdf
```

Sanitize filesystem-unsafe characters in `{SP Name}` (`/\:*?"<>|`).

## False-positive hygiene

- Calendar hits that match a substring of the company name but have no SP
  attendees are **not** meetings with the SP — document as excluded.
- Teams hits that are internal status chatter are **internal mentions**, not
  meetings with the SP — put in a separate subsection.
- Supplier-diversity or mass mail that only mentions the SP in an attachment
  list may be excluded unless the user wants exhaustive search hits.

## Bypass vetting cover note

When vetting is bypassed, cover page must include:

```text
Vetting: bypassed at operator request
```

If a prior vetting PDF is still merged, label that section
`Full SP Vetting Report (supplied — not re-run)`.
