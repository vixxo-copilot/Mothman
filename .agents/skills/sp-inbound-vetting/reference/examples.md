# Examples

## Batch summary (top of run)

```markdown
# SP Inbound Vetting — 2026-06-16

| # | FD # | Inbox | Company | Posture | SP # | SF | cf_sp updated | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 51234 | ksonboarding | Apex HVAC LLC | Known SP | 1044555 | Lead | Yes | complete |
| 2 | 51235 | aphelp | NewCo Electric | Prospect | — | Lead | Yes | complete |
| 3 | 47896 | spm-invoice-concerns | LockPro LLC | Known SP | KS101347 | — | Yes | complete |
| 4 | 51236 | aphelp | (missing) | Unknown | — | — | No | partial |

**Counts:** 4 vetted | 0 skipped | 2 Known SP | 1 Prospect | 1 Unknown
```

## Single packet — Known SP

```markdown
## SP Inbound Vetting — FD #51234

| Field | Value |
| --- | --- |
| **Inbox** | ksonboarding@vixxo.com |
| **Company** | Apex HVAC LLC |
| **Posture** | Known SP |
| **Gateway SP** | 1044555 — KS - Apex HVAC LLC |
| **Salesforce** | Lead 00Q… (Working) |
| **cf_sp** | `1044555 - KS - Apex HVAC LLC` |

### Actions taken
- Internal note: posted
- cf_sp + tags: updated
- SF Lead Task: posted
- SF Case Task: N/A
```

## Single packet — Unknown company

When company cannot be extracted, still post the internal note with posture
`Unknown`, set `cf_sp` to `Unknown` only if the field is empty, and flag for
manual company identification in **Open questions**.
