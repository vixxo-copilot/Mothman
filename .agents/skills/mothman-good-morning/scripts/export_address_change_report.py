#!/usr/bin/env python3
"""Export Address Change Cases to Mothman HTML (mine or org-wide)."""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
import webbrowser
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
REPO_ROOT = SKILL_ROOT.parents[2]
HELPERS = SKILL_ROOT.parent / "sf-case-email-sync" / "scripts"
sys.path.insert(0, str(HELPERS))
sys.path.insert(0, str(SCRIPT_DIR))

from sf_helpers import resolve_user_id, sf_query  # noqa: E402
from render_good_morning_html import BRAND_IMG_REL, FONT_LINKS, THEME_CSS  # noqa: E402

OUTPUT_DIR = REPO_ROOT / ".tmp" / "mothman-good-morning"
DEFAULT_OWNER = "Crystal.Gagner@vixxo.com"
LIGHTNING = "https://vixxo.lightning.force.com/lightning/r"
FIELDS = (
    "SELECT Id, CaseNumber, Subject, Status, IsClosed, Priority, Type, Origin, "
    "CreatedDate, LastModifiedDate, ClosedDate, Owner.Name, RecordType.Name, "
    "Account.Name, Account.Service_Provider_Number__c "
    "FROM Case "
)
TYPE_OR_SUBJECT = (
    "(Type = 'Address Change' "
    "OR Subject LIKE '%Address Change%' "
    "OR Subject LIKE '%change of address%')"
)


def _chicago_now() -> datetime:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo("America/Chicago"))
    except Exception:
        return datetime.now()


def _esc(v: Any) -> str:
    return html.escape("" if v is None else str(v))


def _dt(val: Any) -> str:
    if not val:
        return ""
    return str(val)[:10]


def _age_days(created: str, today: date) -> int | None:
    if not created:
        return None
    try:
        return (today - date.fromisoformat(created[:10])).days
    except ValueError:
        return None


def _link(url: str | None, label: str) -> str:
    if not url:
        return _esc(label)
    return f"<a href='{_esc(url)}' target='_blank' rel='noopener'>{_esc(label)}</a>"


def _pri_tag(priority: str | None) -> str:
    p = (priority or "").lower()
    if p == "high" or "p1" in p:
        return "<span class='tag'>High</span>"
    if p == "medium" or "p2" in p:
        return "<span class='tag fyi'>Medium</span>"
    if "tbd" in p:
        return "<span class='tag fyi'>TBD</span>"
    return "<span class='tag ok'>Normal</span>"


def fetch_cases(*, org: str, owner_id: str | None, include_closed: bool) -> list[dict]:
    if owner_id and not include_closed:
        where = f"OwnerId = '{owner_id}' AND IsClosed = false AND {TYPE_OR_SUBJECT}"
    elif owner_id:
        where = f"OwnerId = '{owner_id}' AND {TYPE_OR_SUBJECT}"
    elif include_closed:
        where = (
            "(Type = 'Address Change' OR "
            "(IsClosed = false AND (Subject LIKE '%Address Change%' "
            "OR Subject LIKE '%change of address%')))"
        )
    else:
        where = f"IsClosed = false AND {TYPE_OR_SUBJECT}"
    soql = FIELDS + "WHERE " + where + " ORDER BY IsClosed ASC, CreatedDate ASC"
    return sf_query(soql, org=org)


def to_row(rec: dict, today: date) -> dict[str, Any]:
    cid = rec.get("Id") or ""
    created = rec.get("CreatedDate") or ""
    acct = rec.get("Account") if isinstance(rec.get("Account"), dict) else {}
    rt = rec.get("RecordType") if isinstance(rec.get("RecordType"), dict) else {}
    owner = rec.get("Owner") if isinstance(rec.get("Owner"), dict) else {}
    typ = rec.get("Type") or ""
    subj = rec.get("Subject") or ""
    typed = typ.strip().lower() == "address change"
    closed = bool(rec.get("IsClosed"))
    return {
        "id": cid,
        "number": (rec.get("CaseNumber") or "").lstrip("0") or rec.get("CaseNumber"),
        "subject": subj,
        "status": rec.get("Status") or "",
        "is_closed": closed,
        "priority": rec.get("Priority") or "",
        "type": typ,
        "owner": (owner or {}).get("Name") or "",
        "origin": rec.get("Origin") or "",
        "record_type": rt.get("Name") or "",
        "account": (acct or {}).get("Name") or "",
        "sp_number": (acct or {}).get("Service_Provider_Number__c") or "",
        "created": _dt(created),
        "closed": _dt(rec.get("ClosedDate")),
        "modified": _dt(rec.get("LastModifiedDate")),
        "age_days": _age_days(created, today),
        "typed": typed,
        "url": f"{LIGHTNING}/Case/{cid}/view" if cid else "",
    }


def _case_rows(items: list[dict[str, Any]], *, show_closed: bool) -> str:
    rows = []
    for c in items:
        age = c.get("age_days")
        age_html = (
            f"<span class='age-hot'>{age}</span>"
            if isinstance(age, int) and age >= 30 and not c.get("is_closed")
            else _esc(age if age is not None else "—")
        )
        match = "Type" if c.get("typed") else "Subject"
        extra = f"<td>{_esc(c.get('closed') or '—')}</td>" if show_closed else ""
        rows.append(
            "<tr>"
            f"<td>{_link(c.get('url'), 'Case ' + str(c.get('number')))}</td>"
            f"<td>{_esc(c.get('owner') or '—')}</td>"
            f"<td>{_pri_tag(c.get('priority'))}</td>"
            f"<td>{_esc(c.get('status'))}</td>"
            f"<td>{_esc(c.get('type') or '—')}</td>"
            f"<td>{_esc(match)}</td>"
            f"<td>{_esc(c.get('account') or '—')}</td>"
            f"<td>{_esc(c.get('sp_number') or '—')}</td>"
            f"<td>{_esc(c.get('created') or '—')}</td>"
            + extra
            + f"<td>{age_html}</td>"
            f"<td>{_esc((c.get('subject') or '')[:120])}</td>"
            "</tr>"
        )
    closed_th = "<th>Closed</th>" if show_closed else ""
    span = 12 if show_closed else 11
    return (
        "<table><thead><tr>"
        "<th>Case</th><th>Owner</th><th>Priority</th><th>Status</th><th>Type</th><th>Match</th>"
        f"<th>Account</th><th>SP #</th><th>Created</th>{closed_th}<th>Age</th><th>Subject</th>"
        "</tr></thead><tbody>"
        + ("".join(rows) if rows else f"<tr><td colspan='{span}'>None.</td></tr>")
        + "</tbody></table>"
    )


def render_html(data: dict[str, Any]) -> str:
    cases = data.get("cases") or []
    summary = data.get("summary") or {}
    stats = [
        ("Open", summary.get("open", summary.get("total", 0))),
        ("Closed", summary.get("closed", 0)),
        ("Type set", summary.get("typed", 0)),
        ("Subject only", summary.get("subject_only", 0)),
        ("Owners", summary.get("owner_count", 0)),
        ("Oldest open", summary.get("oldest_age_days") or 0),
    ]
    stat_html = "".join(
        f"<div class='stat'><div class='n'>{_esc(n)}</div><div class='l'>{_esc(l)}</div></div>"
        for l, n in stats
    )
    open_cases = [c for c in cases if not c.get("is_closed")]
    closed_cases = [c for c in cases if c.get("is_closed")]
    scope = data.get("scope") or "mine"
    lead = (
        f"{summary.get('open', 0)} open Address Change Cases"
        + (" org-wide" if scope == "all" else " on Crystal's queue")
        + (
            f"; {summary.get('closed', 0)} closed with Type = Address Change."
            if closed_cases
            else "."
        )
        + f" {summary.get('typed', 0)} have Type set; {summary.get('subject_only', 0)} subject-only."
    )
    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>Address Changes — {_esc(data.get('date_label', ''))}</title>",
        FONT_LINKS,
        f"<style>{THEME_CSS}</style></head><body>",
        "<span class='ember'></span><span class='ember'></span><span class='ember'></span>",
        "<main class='page-shell'>",
        "<div class='hero'>",
        f"<img src='{BRAND_IMG_REL}' alt='Mothman' width='72' height='72'>",
        "<div class='titles'>",
        "<h1><span class='ember-text'>Address Changes</span></h1>",
        f"<p class='meta'>{_esc(data.get('date_label', ''))} · "
        f"generated {_esc(data.get('generated_at', ''))}</p>",
        "</div></div>",
        f"<p class='lead'>{_esc(lead)}</p>",
        f"<div class='card stats'>{stat_html}</div>",
        f"<h2>Open ({len(open_cases)})</h2>",
        "<p class='muted'>Type Address Change or subject match. Oldest CreatedDate first.</p>",
        _case_rows(open_cases, show_closed=False),
    ]
    if closed_cases:
        parts.extend(
            [
                f"<h2>Closed ({len(closed_cases)})</h2>",
                "<p class='muted'>Type = Address Change only. Oldest CreatedDate first.</p>",
                _case_rows(closed_cases, show_closed=True),
            ]
        )
    parts.extend(
        [
            "<p class='footer'>Mothman · Address Change queue · read-only snapshot</p>",
            "</main></body></html>",
        ]
    )
    return "".join(parts)


def _open_chrome(path: Path) -> None:
    chrome = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    if chrome.is_file():
        subprocess.Popen([str(chrome), str(path.resolve())])
    else:
        webbrowser.open(path.as_uri())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--org", default="vixxo")
    parser.add_argument("--owner-email", default=DEFAULT_OWNER)
    parser.add_argument("--scope", choices=("mine", "all"), default="mine")
    parser.add_argument("--include-closed", action="store_true")
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    now = _chicago_now()
    today = now.date()
    owner_id = None
    if args.scope == "mine":
        owner_id = resolve_user_id(args.org, args.owner_email)
    records = fetch_cases(
        org=args.org, owner_id=owner_id, include_closed=args.include_closed
    )
    cases = [to_row(r, today) for r in records]
    open_cases = [c for c in cases if not c["is_closed"]]
    closed_cases = [c for c in cases if c["is_closed"]]
    typed = sum(1 for c in cases if c["typed"])
    owners = sorted({c["owner"] for c in cases if c.get("owner")})
    open_ages = [c["age_days"] for c in open_cases if isinstance(c["age_days"], int)]
    payload = {
        "report_kind": "address_change",
        "scope": args.scope,
        "include_closed": args.include_closed,
        "date_label": today.strftime("%A, %B %d, %Y"),
        "generated_at": now.strftime("%Y-%m-%d %H:%M %Z") or now.strftime("%Y-%m-%d %H:%M"),
        "owner_email": args.owner_email if args.scope == "mine" else None,
        "summary": {
            "total": len(cases),
            "open": len(open_cases),
            "closed": len(closed_cases),
            "typed": typed,
            "subject_only": len(cases) - typed,
            "owner_count": len(owners),
            "owners": owners,
            "status_breakdown": dict(Counter(c["status"] or "(blank)" for c in cases)),
            "oldest_created": open_cases[0]["created"] if open_cases else None,
            "oldest_age_days": max(open_ages) if open_ages else 0,
        },
        "cases": cases,
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    iso = today.isoformat()
    stem = f"address-changes-all-{iso}" if args.scope == "all" else f"address-changes-{iso}"
    json_path = OUTPUT_DIR / f"{stem}.json"
    html_path = OUTPUT_DIR / f"{stem}.html"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    html_path.write_text(render_html(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "html": str(html_path.resolve()),
                "json": str(json_path.resolve()),
                "summary": payload["summary"],
            }
        )
    )
    if args.open:
        _open_chrome(html_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
