#!/usr/bin/env python3
"""Render Shell Account review lists: SP identified vs true needs-manual."""

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

# Clear SP — create/link Account; not an identity mystery
IDENTIFIED_STATUSES = frozenset({"sp_identified", "gateway_match"})

# Still unclear after signals
MANUAL_STATUSES = frozenset(
    {
        "needs_manual",
        "needs_manual_pdf_insured",
        "needs_manual_pdf_insured_only",
    }
)


def sp_name(c: dict) -> str:
    coi = c.get("coi_pdf") or {}
    hints = c.get("hints") or {}
    return (
        coi.get("legal_insured")
        or hints.get("provider")
        or hints.get("company")
        or c.get("gateway_name")
        or "—"
    )


def identity_label(c: dict) -> str:
    conf = c.get("identity_confidence") or (c.get("coi_pdf") or {}).get("identity_confidence")
    signals = c.get("identity_signals") or (c.get("coi_pdf") or {}).get("identity_signals") or []
    bits = []
    if conf:
        bits.append(str(conf))
    if signals:
        bits.append("+".join(signals))
    gw = c.get("gateway_sp") or (c.get("coi_pdf") or {}).get("gateway_sp")
    if gw:
        bits.append(f"GW {gw}")
    return " · ".join(bits) if bits else "—"


def manual_reason(c: dict) -> str:
    vs = c.get("vet_status") or ""
    coi = c.get("coi_pdf") or {}
    if vs in IDENTIFIED_STATUSES:
        name = sp_name(c)
        if vs == "gateway_match":
            return f"SP clear ({name[:40]}) — Gateway hit; link/create SF Account"
        return f"SP clear ({name[:40]}) — subject/PDF agree; no SF Account yet"
    if vs == "needs_manual_pdf_insured" or coi.get("legal_insured"):
        insured = coi.get("legal_insured") or ""
        return (
            f"PDF insured found ({insured[:50]}) — weak consensus / no Account"
            if insured
            else "PDF insured path — needs Account match"
        )
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
        return (
            f"Broker/carrier sender ({hints['email_domain']}) — "
            "no SP name in subject; check attachment"
        )
    if hints.get("sr_number"):
        return "SR reference only — needs SR routing review"
    return "Insufficient identity signals — review email + attachments"


def collect_by_status(vet: dict, statuses: frozenset[str]) -> list[dict]:
    rows = [c for c in vet.get("cases") or [] if (c.get("vet_status") or "") in statuses]
    rows.sort(key=lambda x: (x.get("created_date") or "", x.get("case_number") or ""))
    return rows


def _md_table(rows: list[dict], *, include_identity: bool) -> list[str]:
    if include_identity:
        lines = [
            "| Case | SP name | Confidence | Created | Subject | Next step |",
            "|------|---------|------------|---------|---------|-----------|",
        ]
        for c in rows:
            subj = (c.get("subject") or "").replace("|", "\\|")
            lines.append(
                f"| {c.get('case_number')} | {sp_name(c)[:50]} | {identity_label(c)} | "
                f"{(c.get('created_date') or '')[:10]} | {subj[:70]} | "
                f"{manual_reason(c)} |"
            )
        return lines
    lines = [
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
    return lines


def write_markdown(identified: list[dict], manual: list[dict], path: Path) -> None:
    lines = [
        "# Shell Account — Review Queue",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Source:** `{VET_JSON.name}`",
        f"**SP identified (clear):** {len(identified)}",
        f"**Needs detective work:** {len(manual)}",
        "",
        "## SP identified — create / link Account",
        "",
        "Subject + PDF (and/or Gateway) agree. These are **not** identity mysteries.",
        "",
    ]
    lines.extend(_md_table(identified, include_identity=True))
    lines.extend(["", "## Needs manual (unclear)", ""])
    lines.extend(_md_table(manual, include_identity=False))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _table_identified(rows: list[dict]) -> list[list[str]]:
    out = []
    for c in rows:
        out.append(
            [
                case_link(c),
                esc(str(sp_name(c))[:50]),
                esc(identity_label(c)[:60]),
                esc((c.get("created_date") or "")[:10]),
                esc((c.get("subject") or "")[:90]),
                esc(manual_reason(c)[:100]),
            ]
        )
    return out


def _table_manual(rows: list[dict]) -> list[list[str]]:
    out = []
    for c in rows:
        hints = c.get("hints") or {}
        contact = c.get("contact_email") or hints.get("email_domain") or "—"
        out.append(
            [
                case_link(c),
                esc(c.get("status")),
                esc((c.get("created_date") or "")[:10]),
                esc((c.get("subject") or "")[:100]),
                esc(str(contact)[:50]),
                esc(str(sp_name(c))[:45]),
                esc(manual_reason(c)[:90]),
            ]
        )
    return out


def render_html(identified: list[dict], manual: list[dict], vet: dict) -> str:
    by_domain = Counter(
        ((c.get("hints") or {}).get("email_domain") or "unknown") for c in manual
    )
    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>Shell Account Review — Mothman</title>",
        FONT_LINKS,
        f"<style>{THEME_CSS}</style></head><body>",
        "<span class='ember' aria-hidden='true'></span>",
        "<main class='page-shell'>",
        "<div class='hero'>",
        f"<img src='{BRAND_REL}' alt='Mothman' width='72' height='72'>",
        "<div class='titles'>",
        "<h1>Shell Account <span class='ember-text'>Review</span></h1>",
        f"<p class='meta'>Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · "
        f"source {esc(VET_JSON.name)}</p>",
        "</div></div>",
        "<h2>Summary</h2><div class='card'><div class='stats'>",
        stat_card("SP identified", len(identified), "ok"),
        stat_card("Needs detective work", len(manual), "warn"),
        stat_card("Shell open (vet)", vet.get("shell_open_count", len(vet.get("cases") or []))),
        stat_card("Unclear sender domains", len(by_domain)),
        "</div>",
        "<p class='warn-box'><strong>SP identified</strong> = subject / PDF / filename agree "
        "(or Gateway SP #). Apply or create the Account — do not re-hunt the name.<br>"
        "<strong>Needs detective work</strong> = broker noise, email-as-company, "
        "or weak consensus. Open the COI PDF.</p></div>",
        "<h2>SP identified — create / link Account</h2><div class='card'>",
        render_table(
            ["Case", "SP name", "Confidence", "Created", "Subject", "Next step"],
            _table_identified(identified),
        )
        if identified
        else "<p>None this run.</p>",
        "</div>",
        "<h2>Needs detective work</h2><div class='card'>",
        render_table(
            ["Case", "Status", "Created", "Subject", "Contact / domain", "SP hint", "Why manual"],
            _table_manual(manual),
        )
        if manual
        else "<p>None this run.</p>",
        "</div>",
        "<p class='footer'>Mothman · Shell review · report only</p>",
        "</main></body></html>",
    ]
    return "".join(parts)


def main() -> int:
    vet = json.loads(VET_JSON.read_text(encoding="utf-8"))
    identified = collect_by_status(vet, IDENTIFIED_STATUSES)
    manual = collect_by_status(vet, MANUAL_STATUSES)
    write_markdown(identified, manual, OUT_MD)
    OUT_HTML.write_text(render_html(identified, manual, vet), encoding="utf-8")
    print(
        json.dumps(
            {
                "sp_identified": len(identified),
                "needs_manual": len(manual),
                "html": str(OUT_HTML.resolve()),
            },
            indent=2,
        )
    )
    if os.environ.get("OPEN_REPORT", "1") != "0":
        open_html_in_chrome(OUT_HTML)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
