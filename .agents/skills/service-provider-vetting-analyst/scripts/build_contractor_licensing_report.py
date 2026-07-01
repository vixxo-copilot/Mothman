#!/usr/bin/env python3
"""Build single consolidated contractor licensing report (MD + PDF)."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from export_contractor_licensing_pdf import GuidePDF, md_to_pdf_lines, render_lines

BASE = Path(__file__).resolve().parent.parent / "reference"
TABLE_MD = BASE / "contractor-licensing-quick-lookup-table.md"
GUIDE_MD = BASE / "contractor-licensing-us-states-territories.md"
SPECIALTY_MD = BASE / "contractor-licensing-specialty-trades.md"
REPORT_MD = BASE / "contractor-licensing-complete-report.md"
REPORT_PDF = BASE / "contractor-licensing-complete-report.pdf"

REVIEW_DATE = "2026-06-30"


def strip_leading_h1(md: str) -> str:
    """Remove first top-level heading and following metadata block before first ---."""
    lines = md.splitlines()
    out: list[str] = []
    skipped_h1 = False
    past_meta = False
    for line in lines:
        if not skipped_h1 and line.startswith("# "):
            skipped_h1 = True
            continue
        if skipped_h1 and not past_meta:
            if line.strip() == "---":
                past_meta = True
            continue
        out.append(line)
    return "\n".join(out).lstrip("\n")


def executive_summary() -> str:
    return f"""# US Contractor Licensing — Complete Reference Report

**Last reviewed:** {REVIEW_DATE}  
**Audience:** Service provider vetting (Vixxo operations)  
**Coverage:** 50 states · Washington D.C. · 5 U.S. territories · specialty trades

> **Disclaimer:** Official agency websites are the source of truth. This report is a
> vetting starting point, not legal advice. Always verify status, classification, and
> scope at the official portal on the date of review.

---

## Table of contents

1. [Executive summary](#executive-summary)
2. [Quick lookup — all jurisdictions](#part-2--quick-lookup-all-jurisdictions)
3. [Specialty trades — backflow, fire, pest, locksmith / low voltage](#part-3--specialty-trades)
4. [Jurisdiction detail — states, territories, municipal follow-up](#part-4--jurisdiction-detail)

---

## Executive summary

### At a glance

| Metric | Value |
| --- | --- |
| Jurisdictions covered | 56 (50 states + DC + GU, PR, VI, CNMI, AS) |
| Statewide GC license regimes (A) | ~24 states + DC + several territories |
| Trade-only / local GC regimes (B) | ~19 states |
| No statewide GC license (C) | 7 states: CO, IL, IN, MO, NY, PA, WY |
| Dual-state-portal states | OR (CCB + BCD), IA (DIAL + PMSB), MT (DLI + POL), PR (DACO + PCS) |
| Municipal follow-up required | All Regime C states + most Regime B + registration-heavy states |

### Three licensing regimes

| Regime | Meaning | Vetting implication |
| --- | --- | --- |
| **A — Statewide GC** | State board issues general contractor licenses with classifications | Verify state GC portal first; then trade boards for self-performed work |
| **B — Trade-only** | State licenses trades; GC often local or not required statewide | State trade lookup + **city/county** for GC and sometimes trades |
| **C — Local-only GC** | No state GC competency license | **Municipal** portal is primary for GC and most trades |

### Registration is not licensure

These states (and others) require **registration** without a competency exam. An active
registration record does **not** prove trade authorization or municipal permit eligibility.

| State | Registration type | Still verify |
| --- | --- | --- |
| OR | CCB registration (all construction) | BCD trade license for electrical, plumbing, HVAC, etc. |
| IA | Contractor registration | PMSB trade licenses |
| NE | Contractor registration | State electrical + Omaha/Lincoln local trades |
| NJ | HIC registration (NJHIC#) | State trade licenses + municipal |
| PA | HIC registration (residential) | Local GC/trades |
| CT | HIC / NHCC registration | State trade licenses + municipal |
| WA | Contractor registration (L&I) | State trade certifications + municipal |
| RI | CRLB registration | Specialty trade licenses |
| VT | Residential contractor registration | DPS trades |
| MT | Contractor registration (ICEC) | POL trade licenses + municipal |
| AK | Construction contractor registration | Anchorage municipal when applicable |
| PR | DACO contractor registration | Dept. of State trade licenses + municipio |

**Four-layer rule (registration states):** (1) state registration → (2) state trade
license → (3) municipal license → (4) permit eligibility at project address.

### Municipal-first states (Regime C)

No statewide GC license — verify at **project city/county** in addition to any state credential:

| State | State-level trades | Primary municipal portals |
| --- | --- | --- |
| **IL** | Roofing, plumbing (state) | Chicago DOB, DuPage Accela, Naperville, Aurora |
| **IN** | Plumbing (state) | Indianapolis, Fort Wayne, Evansville, South Bend |
| **NY** | None statewide | NYC DCWP/DOB, Nassau, Suffolk, Buffalo, Rochester |
| **MO** | Electrical optional (state) | Kansas City CompassKC, St. Louis, Springfield |
| **PA** | HIC Reg (residential) | Philadelphia L&I, Pittsburgh, Allentown |
| **CO** | Electrical, plumbing (state) | Denver, Colorado Springs, Aurora |
| **WY** | Electrical (state) | Cheyenne, Casper, Laramie |

### Oregon — dual verification (critical)

| Layer | Portal |
| --- | --- |
| CCB registration (all paid construction) | https://search.ccb.state.or.us/search/ |
| BCD trade license (elec, plumb, HVAC, etc.) | https://www.oregon.gov/bcd/licensing/pages/search.aspx |

Active CCB **does not** authorize trade work. Active BCD **does not** replace CCB.

### Specialty trades summary

GC, plumbing, or electrical licenses **do not** cover these scopes. Verify the **specific**
specialty credential.

| Specialty | Regulator pattern | Common mistake |
| --- | --- | --- |
| **Backflow testing/repair** | Health/env/water utility; TX TCEQ BPAT; many local purveyor lists | Assuming plumber license covers BPAT testing |
| **Fire sprinkler** | State Fire Marshal, contractor board (C-16 in CA) | Confusing with fire **alarm** license |
| **Fire alarm** | SFMO, alarm board, electrical board | Using sprinkler license for alarm work |
| **Pest control** | Dept. of Agriculture (DEC/DEP in NY/NJ) | Company Reg without certified applicator |
| **Locksmith** | BSIS, state police, locksmith board | Locksmith alone for access control/CCTV |
| **Low voltage / CCTV / access** | Alarm board, C-7/SP-FA/LV, limited energy | Standard electrical without alarm/LV class |

**High-signal specialty portals:** TX (TCEQ BPAT + TDI SFMO), CA (BSIS + CSLB C-7/C-16),
FL (CFO SFM + DBPR alarm), NC (NCAGR pest + SP-FA/LV), SC (LLR fire + alarm), WA (DOH BAT + WSDA pest).

### Verification sequence

1. Identify **project state and municipality** (not SP headquarters).
2. Look up **state** registration, GC license, or trade license at official portal.
3. Run **second state portal** if trades split across boards (OR, IA, MT, PR).
4. Look up **municipal** GC/trade license for project address (Regime B/C and Reg states).
5. For specialty scope, verify at **specialty board** (not GC/plumbing/electrical alone).
6. Confirm **Active** status, **classification matches scope**, **name matches contract**.
7. Document lookup date, portal URL, and result (screenshot or saved record).

### Minimum fields to capture

| Field | Why |
| --- | --- |
| License/registration number | Primary lookup key |
| Legal business name | Must match contract and payee |
| Status | Active vs expired, suspended, revoked |
| Classification / endorsement | Scope must match work |
| Expiration date | Lapsed = no permit path |
| Bond / insurance / workers' comp | When shown on board record |
| Disciplinary history | Pattern matters |
| Qualifying party / RMO | Business licensed through a person on many boards |

### Red flags

- License number format wrong for jurisdiction or board
- Name mismatch between board, contract, and invoice (DBA vs legal entity)
- Classification does not cover proposed scope (plumbing ≠ GC; sprinkler ≠ alarm)
- Expired or suspended status with "will renew" explanation only
- Out-of-state license presented for in-state work without reciprocity
- Registration shown where competency license required
- Only GC verified when SP self-performs regulated trades
- Specialty work verified only against general contractor or trade license

### Vetting checklist (SP report)

- [ ] Verify all licenses directly with licensing boards (not SP-provided PDF only)
- [ ] Confirm status, expiration, and disciplinary history
- [ ] Municipal lookup completed when regime is B, C, or registration-heavy
- [ ] Oregon: both CCB and BCD verified when trades involved
- [ ] Specialty credentials verified for backflow, fire, pest, locksmith/LV when in scope
- [ ] Secretary of State entity status checked (entity ≠ contractor license)
- [ ] Document "Not Found" with board searched and date

---

## Part 2 — Quick lookup (all jurisdictions)

"""


def build_report_md() -> str:
    parts = [
        executive_summary(),
        strip_leading_h1(TABLE_MD.read_text(encoding="utf-8")),
        "\n\n---\n\n## Part 3 — Specialty trades\n\n",
        strip_leading_h1(SPECIALTY_MD.read_text(encoding="utf-8")),
        "\n\n---\n\n## Part 4 — Jurisdiction detail\n\n",
        strip_leading_h1(GUIDE_MD.read_text(encoding="utf-8")),
    ]
    return "".join(parts)


def export_pdf(md: str, pdf_path: Path) -> None:
    pdf = GuidePDF(orientation="L", unit="mm", format="Letter")
    pdf.alias_nb_pages()
    pdf.set_margins(12, 12, 12)
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()
    render_lines(pdf, md_to_pdf_lines(md))
    pdf.output(str(pdf_path))


def main() -> None:
    report_md = build_report_md()
    REPORT_MD.write_text(report_md, encoding="utf-8")
    export_pdf(report_md, REPORT_PDF)
    print(
        json.dumps(
            {
                "report_md": str(REPORT_MD),
                "report_pdf": str(REPORT_PDF),
                "generated": date.today().isoformat(),
                "sources": {
                    "table": str(TABLE_MD),
                    "specialty": str(SPECIALTY_MD),
                    "guide": str(GUIDE_MD),
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
