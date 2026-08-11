#!/usr/bin/env python3
"""Render full Shell Account needs-manual review list (Case # + subject)."""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from render_sf_duplicate_report_html import (  # noqa: E402
    BRAND_REL,
    FONT_LINKS,
    THEME_CSS,
    case_link,
    esc,
    open_html_in_chrome,
    render_table,
    stat_card,
)

RUN_DATE = os.environ.get("RUN_DATE", datetime.now(timezone.utc).strftime("%Y%m%d"))
TMP = SCRIPTS.parent / ".tmp"


def _path(env_key: str, default: Path) -> Path:
    v = os.environ.get(env_key)
    return Path(v) if v else default


VET_JSON = _path("VET_JSON_PATH", TMP / f"shell-account-vet-allorg-{RUN_DATE}.json")
OUT_HTML = _path(
    "NEEDS_MANUAL_HTML_PATH",
    TMP / f"shell-needs-manual-allorg-{RUN_DATE}.html",
)
OUT_MD = _path(
    "NEEDS_MANUAL_MD_PATH",
    TMP / f"shell-needs-manual-allorg-{RUN_DATE}.md",
)

MANUAL_STATUSES = frozenset(
    {
        "needs_manual",
        "needs_manual_pdf_insured",
        "needs_manual_pdf_insured_only",
    }
)


def manual_reason(c: dict) -> str:
    vs = c.get("vet_status") or ""
    coi = c.get("coi_pdf") or {}
    if vs == "needs_manual_pdf_insured" or coi.get("legal_insured"):
        insured = coi.get("legal_insured") or ""
        return f"PDF insured found ({insured[:50]}) — no confident SF Account" if insured else "PDF insured path — needs Account match"
    hints = c.get("hints") or {}
    company = hints.get("company") or hints.get("provider")
    if company and "@" in str(company):
        return f"Sender/email only ({company}) — open COI attachment for SP name"
    if company:
        cands = c.get("account_search_candidates") or []
        if not cands:
            return "Company hint present — SF Account search returned no match"
        return "Company hint present — multiple/low-confidence SF hits"
    if hints.get("email_domain"):
        return f"Broker/carrier sender ({hints['email_domain']}) — no SP name in subject; check attachment"
    if hints.get("sr_number"):
        return "SR reference only — needs SR routing review"
    return "Insufficient identity signals — review email + attachments"


def collect_manual(vet: dict) -> list[dict]:
    rows = []
    for c in vet.get("cases") or []:
        vs = c.get("vet_status") or ""
        if vs not in MANUAL_STATUSES:
            continue
        rows.append(c)
    rows.sort(key=lambda x: (x.get("created_date") or "", x.get("case_number") or ""))
    return rows


def write_markdown(rows: list[dict], vet: dict, path: Path) -> None:
    lines = [
        "# Shell Account — Needs Manual Review",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Source:** `{VET_JSON.name}`",
        f"**Count:** {len(rows)}",
        "",
        "| Case | Status | Created | Subject | Contact / domain | Reason |",
        "|------|--------|---------|---------|------------------|--------|",
    ]
    for c in rows:
        hints = c.get("hints") or {}
        contact = c.get("contact_email") or hints.get("email_domain") or "—"
        subj = (c.get("subject") or "").replace("|", "\\|")
        lines.append(
            f"| {c.get('case_number')} | `{c.get('status')}` | "
            f"{(c.get('created_date') or '')[:10]} | {subj[:90]} | {contact} | "
            f"{manual_reason(c)} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_html(rows: list[dict], vet: dict) -> str:
    by_domain = Counter(
        ((c.get("hints") or {}).get("email_domain") or "unknown") for c in rows
    )
    table_rows = []
    for c in rows:
        hints = c.get("hints") or {}
        contact = c.get("contact_email") or hints.get("email_domain") or "—"
        coi = c.get("coi_pdf") or {}
        insured = coi.get("legal_insured") or hints.get("provider") or hints.get("company") or "—"
        table_rows.append(
            [
                case_link(c),
                esc(c.get("status")),
                esc((c.get("created_date") or "")[:10]),
                esc((c.get("subject") or "")[:100]),
                esc(str(contact)[:50]),
                esc(str(insured)[:45]),
                esc(manual_reason(c)[:90]),
            ]
        )

    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>Shell Needs Manual Review — Mothman</title>",
        FONT_LINKS,
        f"<style>{THEME_CSS}</style></head><body>",
        "<span class='ember' aria-hidden='true'></span>",
        "<main class='page-shell'>",
        "<div class='hero'>",
        f"<img src='{BRAND_REL}' alt='Mothman' width='72' height='72'>",
        "<div class='titles'>",
        "<h1>Shell <span class='ember-text'>Needs Manual</span> Review</h1>",
        f"<p class='meta'>Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · "
        f"{len(rows)} Cases · source {esc(VET_JSON.name)}</p>",
        "</div></div>",
        "<h2>Summary</h2><div class='card'><div class='stats'>",
        stat_card("Needs manual", len(rows), "warn"),
        stat_card("Shell open (vet)", vet.get("shell_open_count", len(vet.get("cases") or []))),
        stat_card("Top sender domains", len(by_domain)),
        "</div>",
        "<p class='warn-box'>Open COI / certificate PDF attachments to identify the SP when the "
        "subject is broker noise (e.g. <code>Re: REVISED Certificate of Insurance</code>). "
        "Do not trust email-as-company matches.</p></div>",
        "<h2>Full list</h2><div class='card'>",
        render_table(
            ["Case", "Status", "Created", "Subject", "Contact / domain", "SP hint", "Why manual"],
            table_rows,
        ),
        "</div>",
        "<p class='footer'>Mothman · Shell needs-manual · report only</p>",
        "</main></body></html>",
    ]
    return "".join(parts)


def main() -> int:
    vet = json.loads(VET_JSON.read_text(encoding="utf-8"))
    rows = collect_manual(vet)
    write_markdown(rows, vet, OUT_MD)
    OUT_HTML.write_text(render_html(rows, vet), encoding="utf-8")
    print(json.dumps({"needs_manual": len(rows), "html": str(OUT_HTML.resolve())}, indent=2))
    if os.environ.get("OPEN_REPORT", "1") != "0":
        open_html_in_chrome(OUT_HTML)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
