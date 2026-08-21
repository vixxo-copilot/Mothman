#!/usr/bin/env python3
"""Merge SOS registered-agent results into vetting report and export PDF."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from fpdf import FPDF

BASE = Path(__file__).resolve().parent
SOS_JSON = BASE / "sc_sos_playwright_results.json"
MD_OUT = BASE / "sp-vetting-report-midlands-sc-20260626.md"
PDF_OUT = BASE / "sp-vetting-report-midlands-sc-20260626.pdf"

SOS_SECTION = """
## SC Secretary of State — Registered Agent Search (Primary Source)

**Search date:** 2026-06-26  
**Portal:** [SC SOS Registered Agent Search](https://businessfilings.sc.gov/BusinessFiling/Entity/AgentSearch)  
**Query used:** `Edward Randall Ramsey` (exact full name; partial variants returned no rows)

### Entities where Edward Randall Ramsey is registered agent

| Entity Name | Entity ID | Type | Status | Effective Date | Agent Address | Profile |
| --- | --- | --- | --- | --- | --- | --- |
| **CORLEY LOCK & SAFE COMPANY LLC** | **00523975** | Limited Liability Company | **Good Standing** | **03/04/2015** | 160 Kingship Dr, Chapin, SC 29036 | [SOS Profile](https://businessfilings.sc.gov/BusinessFiling/Entity/Profile/74018c58-be5b-4261-9b6b-5d03d1ebf926) |
| **KEYSTONE CONSULTING GROUP L.L.C.** | **00577113** | Limited Liability Company | **Good Standing** | **10/08/2013** | 1704 Quail Valley West, Columbia, SC 29212 | [SOS Profile](https://businessfilings.sc.gov/BusinessFiling/Entity/Profile/b331fe99-d712-4b48-9ff4-50e7b317b593) |

**Total SOS hits for this agent name:** 2

### Entities NOT returned under Edward Randall Ramsey (registered agent search)

The following requested vetting subjects did **not** appear as entities for which Edward Randall Ramsey is the registered agent:

- **Security Lock & Safe Co / Security Lock and Safe Co Inc.**
- **Elite Security & Maintenance**
- **Corley Security Systems Inc.**

This does not prove Ramsey has no ownership or officer role; it means he is **not the listed registered agent** on file for those names in this search.

### Related address signal

**Keystone Consulting Group L.L.C.** uses registered-agent address **1704 Quail Valley West, Columbia, SC 29212** — the same address listed for Security Lock & Safe in directory records. **Corley Lock & Safe Company LLC** uses **160 Kingship Dr, Chapin** — shared with Security Lock & Safe directory listings. These overlaps support a **common Chapin/Midlands operating network** but do not by themselves establish a single legal entity.

### Business name search limitation

[SC SOS Business Name Search](https://businessfilings.sc.gov/BusinessFiling/Entity/Search) returned a **captcha gate** for entity-name queries in this automated run. Entity profiles for Security Lock and Safe, Elite Security & Maintenance, and Corley Security Systems Inc. were **not retrieved** from business-name search. Manual business-name search or document purchase may still be required for those legal names.

### Updated Edward Randall Ramsey assessment (post-SOS)

| Role | Security Lock & Safe | Corley Lock & Safe | Elite Security & Maintenance |
| --- | --- | --- | --- |
| **Registered agent (SOS)** | **Not Found** | **Confirmed** — Corley Lock & Safe Company LLC (00523975) | **Not Found** |
| **Related SOS entity** | Possible link via Keystone Consulting Group LLC (00577113) at shared Columbia address | **Confirmed** primary SOS tie | **Not Found** |
| **Officer / member titles** | **Not Found** on SOS profiles reviewed | **Not Found** on SOS profiles reviewed | **Not Found** |
| **Confidence** | Medium-low | **High** for registered-agent role | Low |

**Bottom line (updated):** Edward Randall Ramsey is **confirmed on SC SOS** as registered agent for **Corley Lock & Safe Company LLC** (Good Standing, formed 2015) and **Keystone Consulting Group L.L.C.** (Good Standing, formed 2013). He is **not** the registered agent of record for Security Lock & Safe or Elite Security & Maintenance under this search. Officer/member designations were not shown on the public profile pages retrieved.
"""


def load_prior() -> str:
    prior = (BASE / "prior_report.md").read_text(encoding="utf-8")
    prior = re.sub(
        r"\*\*Research note:\*\* SC Secretary of State entity search could not be completed.*?marked \*\*Not Found\*\*\.\n",
        "**Research note:** SC SOS **registered agent search completed 2026-06-26** (primary source). Business-name entity search remained captcha-blocked for several targets; see SOS section below. Other items not directly verified remain **Not Found**.\n",
        prior,
        count=1,
        flags=re.S,
    )
    prior = prior.replace(
        "| **Corley Lock & Safe Company, LLC** | Secondary sources report Edward Randall Ramsey as **registered agent**; entity ID **00523975** cited in aggregator data — **not re-verified on SOS in this run** |",
        "| **Corley Lock & Safe Company, LLC** | **SOS confirmed:** Edward Randall Ramsey is **registered agent**; Entity ID **00523975**; **Good Standing**; effective **03/04/2015**; agent address **160 Kingship Dr, Chapin, SC 29036** |",
        1,
    )
    prior = prior.replace(
        "| **Elite Security & Maintenance** | **No primary-source officer listing** for Edward Randall Ramsey found |",
        "| **Elite Security & Maintenance** | **No SOS registered-agent listing** for Edward Randall Ramsey; officer role **Not Found** |",
        1,
    )
    prior = prior.replace(
        "| **Tie to Security Lock & Safe** | YellowBook associates this Chapin Edward Ramsey with email domain **@996lock.com**, matching Security Lock & Safe’s **803-996-5625** line and **996lock.com** domain (registered to Randy Ramsey per domain records) |",
        "| **Tie to Security Lock & Safe** | YellowBook **@996lock.com** email association; possible SOS link via **Keystone Consulting Group L.L.C.** (00577113) at **1704 Quail Valley West** — same address as Security Lock directory listing; Edward Ramsey **not** listed as registered agent for Security Lock entity name |",
        1,
    )
    prior = re.sub(
        r"\| Registered agent \| \*\*Edward Randall Ramsey\*\*, Chapin area \(secondary sources\) \|",
        "| Registered agent | **Edward Randall Ramsey** — **SOS confirmed**; 160 Kingship Dr, Chapin, SC 29036 |",
        prior,
        count=1,
    )
    prior = re.sub(
        r"\| Entity ID \| \*\*00523975\*\* cited in aggregators — \*\*Not Found\*\* on SOS directly \|",
        "| Entity ID | **00523975** — **SOS confirmed** |",
        prior,
        count=1,
    )
    prior = re.sub(
        r"\| Status \| Reported \*\*good standing\*\* in aggregators — \*\*Not Found\*\* on SOS directly \|",
        "| Status | **Good Standing** — **SOS confirmed** (effective 03/04/2015) |",
        prior,
        count=1,
    )
    prior = re.sub(
        r"\| Officers \| Edward Randall Ramsey — \*\*registered agent only confirmed in secondary sources\*\*; manager/member titles \*\*Not Found\*\* \|",
        "| Officers | Edward Randall Ramsey — **registered agent confirmed on SOS**; manager/member titles **Not Found** on public profile |",
        prior,
        count=1,
    )
    prior = re.sub(
        r"\*\*Edward Randall Ramsey\*\* was \*\*not found\*\* as an officer of Corley Security Systems Inc\. on BBB\.",
        "**Edward Randall Ramsey** was **not found** as an officer of Corley Security Systems Inc. on BBB, and is **not** the SOS registered agent for that entity name in the agent search completed here.",
        prior,
        count=1,
    )
    prior = re.sub(
        r"\| \*\*Confidence grade\*\* \| \*\*C\*\* \| “Corley Lock & Safe” LLC vs\. “Corley Security Systems Inc\.” split lowers certainty; Edward Ramsey’s exact officer role beyond registered-agent reports is unconfirmed on primary SOS\. \|",
        "| **Confidence grade** | **B** | SOS now confirms Edward Randall Ramsey as registered agent for Corley Lock & Safe Company LLC; split from Corley Security Systems Inc. remains, and officer titles beyond registered agent are still **Not Found**. |",
        prior,
        count=1,
    )
    prior = re.sub(
        r"## Combined Assessment — Edward Randall Ramsey \(Owner/Officer\)\n\n\| Role \|.*?\n\n\*\*Bottom line:\*\* Edward Randall Ramsey appears credibly tied.*?before onboarding\.\n",
        "",
        prior,
        count=1,
        flags=re.S,
    )
    prior = re.sub(
        r"\| Corley Lock & Safe / Corley Security \| \*\*B\*\* \| \*\*C\*\* \|",
        "| Corley Lock & Safe / Corley Security | **B** | **B** |",
        prior,
        count=1,
    )
    prior = re.sub(
        r"1\. Run \[SC SOS entity search\].*?\n2\. Confirm which \*\*single legal entity\*\*.*?\n3\. Clarify whether \*\*Corley Lock & Safe LLC\*\*.*?\n\nI can run the SOS registered-agent search and produce an updated report with entity IDs and officer lists if you want that next\.\n",
        "1. Complete manual [SC SOS business name search](https://businessfilings.sc.gov/BusinessFiling/Entity/Search) for Security Lock and Safe, Elite Security & Maintenance, and Corley Security Systems Inc. (captcha blocked automated entity search).\n2. Confirm which **single legal entity** would hold the Vixxo SP agreement (538 Chapin Rd + Keystone Consulting LLC address overlap suggests a related operating group).\n3. Clarify whether **Corley Lock & Safe LLC** (Chapin/Ramsey, SOS confirmed) is affiliated with **Corley Security Systems Inc.** (Columbia/Corley family) or a separate vendor.\n",
        prior,
        count=1,
        flags=re.S,
    )
    insert_at = prior.find("---\n\n# Service Provider Vetting Report: Security Lock")
    if insert_at == -1:
        insert_at = prior.find("---\n\n## Cross-Entity Summary")
        end = prior.find("\n---\n\n# Service Provider Vetting Report: Security Lock")
        if end != -1:
            prior = prior[:end] + "\n" + SOS_SECTION + prior[end:]
    else:
        prior = prior[:insert_at] + SOS_SECTION + "\n---\n\n" + prior[insert_at + 5 :]
    prior = prior.replace(
        "- [ ] Confirm legal entity name against Secretary of State records.",
        "- [x] Confirm legal entity name against Secretary of State records (Corley Lock & Safe Company LLC — SOS confirmed).",
        1,
    )
    prior = prior.replace(
        "- [ ] Confirm active status and formation date.",
        "- [x] Confirm active status and formation date (Corley Lock & Safe Company LLC — Good Standing, 03/04/2015).",
        1,
    )
    prior = prior.replace(
        "- [ ] Confirm registered agent and principal office.",
        "- [x] Confirm registered agent and principal office (Edward Randall Ramsey / 160 Kingship Dr — SOS confirmed).",
        1,
    )
    footer = (
        f"\n\n---\n\n*Report regenerated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} "
        f"with SC SOS registered agent search results. Source JSON: `{SOS_JSON.name}`*\n"
    )
    return prior.rstrip() + footer


class ReportPDF(FPDF):
    def header(self) -> None:
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(80, 80, 80)
        self.cell(0, 8, "Vixxo - Service Provider Vetting Report", align="R", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def safe_text(text: str) -> str:
    text = text.replace("\u2014", "-").replace("\u2013", "-").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    return text.encode("latin-1", errors="replace").decode("latin-1")


def write_block(pdf: ReportPDF, text: str, h: float = 5) -> None:
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, h, safe_text(text))


def md_to_pdf_lines(md: str) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            lines.append(("blank", ""))
            continue
        if line.startswith("# "):
            lines.append(("h1", line[2:].strip()))
        elif line.startswith("## "):
            lines.append(("h2", line[3:].strip()))
        elif line.startswith("### "):
            lines.append(("h3", line[4:].strip()))
        elif line.startswith("| ") and "---" not in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            lines.append(("row", " | ".join(re.sub(r"\*\*", "", c) for c in cells)))
        elif line.startswith("- [x]"):
            lines.append(("bullet", "[x] " + line[6:].strip()))
        elif line.startswith("- [ ]"):
            lines.append(("bullet", "[ ] " + line[6:].strip()))
        elif line.startswith("- "):
            lines.append(("bullet", line[2:].strip()))
        elif line.startswith("**") and line.endswith("**"):
            lines.append(("bold", line.strip("*")))
        else:
            clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
            clean = re.sub(r"\*\*([^*]+)\*\*", r"\1", clean)
            lines.append(("body", clean))
    return lines


def export_pdf(md: str) -> None:
    pdf = ReportPDF()
    pdf.alias_nb_pages()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    for kind, text in md_to_pdf_lines(md):
        if kind == "blank":
            pdf.ln(2)
            continue
        if kind == "h1":
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(10, 10, 10)
            write_block(pdf, text, 8)
            pdf.ln(2)
        elif kind == "h2":
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(20, 20, 20)
            write_block(pdf, text, 7)
            pdf.ln(1)
        elif kind == "h3":
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(30, 30, 30)
            write_block(pdf, text, 6)
        elif kind == "bold":
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 30, 30)
            write_block(pdf, text, 5)
        elif kind == "row":
            pdf.set_font("Courier", "", 8)
            pdf.set_text_color(20, 20, 20)
            write_block(pdf, text, 4)
        elif kind == "bullet":
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(30, 30, 30)
            write_block(pdf, f"  - {text}", 4)
        else:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(30, 30, 30)
            write_block(pdf, text, 4)
    pdf.output(str(PDF_OUT))


def main() -> None:
    if SOS_JSON.exists():
        json.loads(SOS_JSON.read_text(encoding="utf-8"))
    md = load_prior()
    MD_OUT.write_text(md, encoding="utf-8")
    export_pdf(md)
    print(json.dumps({"markdown": str(MD_OUT), "pdf": str(PDF_OUT)}, indent=2))


if __name__ == "__main__":
    main()
