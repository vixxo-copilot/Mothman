#!/usr/bin/env python3
"""Render SF task breakdown JSON as Mothman-themed HTML."""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from render_good_morning_html import BRAND_IMG_REL, FONT_LINKS, THEME_CSS  # noqa: E402

OUTPUT_ROOT = Path.cwd() / ".tmp" / "mothman-good-morning"
_DATE_STEM = re.compile(r"sf-task-breakdown-(\d{4}-\d{2}-\d{2})$")


def _esc(v: Any) -> str:
    return html.escape("" if v is None else str(v))


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


def _table(
    headers: list[str],
    rows: list[list[str]],
    empty: str = "None.",
) -> str:
    if not rows:
        return f"<p class='muted'>{_esc(empty)}</p>"
    parts = ["<table><thead><tr>"]
    for h in headers:
        parts.append(f"<th>{_esc(h)}</th>")
    parts.append("</tr></thead><tbody>")
    for row in rows:
        parts.append("<tr>")
        for cell in row:
            parts.append(f"<td>{cell}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def _item_row(item: dict[str, Any]) -> list[str]:
    kind = item.get("kind") or "Item"
    num = item.get("number") or item.get("what_name") or ""
    subj = item.get("subject") or item.get("name") or ""
    label = f"{kind}"
    if num:
        label += f" {num}"
    if item.get("company"):
        label += f" — {item['company']}"
    link = item.get("url") or item.get("case_url")
    return [
        _esc(item.get("tier") or item.get("reason") or ""),
        _link(link, label),
        _pri_tag(item.get("priority")),
        _esc(item.get("status") or "—"),
        _esc(item.get("created") or "—"),
        _esc(item.get("due") or item.get("last_modified") or "—"),
        _esc((item.get("subject") or item.get("name") or "")[:100]),
    ]


def _case_rows(cases: list[dict]) -> list[list[str]]:
    out = []
    for c in cases:
        out.append(
            [
                _link(c.get("url"), f"Case {c.get('number')}"),
                _pri_tag(c.get("priority")),
                _esc(c.get("record_type")),
                _esc(c.get("status")),
                _esc(c.get("created")),
                _esc((c.get("subject") or "")[:110]),
            ]
        )
    return out


def _task_rows(tasks: list[dict]) -> list[list[str]]:
    out = []
    for t in tasks:
        flags = []
        if t.get("overdue"):
            flags.append("<span class='tag'>Overdue</span>")
        if t.get("due_today"):
            flags.append("<span class='tag fyi'>Due today</span>")
        subj = _esc(t.get("subject") or "")
        if flags:
            subj += " " + "".join(flags)
        out.append(
            [
                _link(t.get("url"), "Task"),
                _esc(t.get("status")),
                _esc(t.get("created")),
                _esc(t.get("due") or "—"),
                _esc(t.get("what_name") or t.get("what_type") or "—"),
                subj,
            ]
        )
    return out


def render_html(data: dict[str, Any]) -> str:
    summary = data.get("summary") or {}
    lead = (
        f"Open Tasks {summary.get('tasks_total', 0)} "
        f"({summary.get('tasks_overdue', 0)} overdue) · "
        f"High Cases {summary.get('cases_high', 0)} · "
        f"Medium {summary.get('cases_medium', 0)} · "
        f"Rate New {summary.get('rate_new', 0)} · "
        f"New Cases (3d) {summary.get('cases_new_3d', 0)}."
    )

    stats = [
        ("Tasks", summary.get("tasks_total", 0)),
        ("Overdue", summary.get("tasks_overdue", 0)),
        ("High Cases", summary.get("cases_high", 0)),
        ("Rate New", summary.get("rate_new", 0)),
        ("Leads", summary.get("leads_open", 0)),
    ]
    stat_html = "".join(
        f"<div class='stat'><div class='n'>{_esc(n)}</div><div class='l'>{_esc(l)}</div></div>"
        for l, n in stats
    )

    pri_rows = [_item_row(i) for i in data.get("priority_items") or []]

    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>SF Task Breakdown — {_esc(data.get('date_label', ''))}</title>",
        FONT_LINKS,
        f"<style>{THEME_CSS}</style></head><body>",
        "<span class='ember'></span><span class='ember'></span><span class='ember'></span>",
        "<main class='page-shell'>",
        "<div class='hero'>",
        f"<img src='{BRAND_IMG_REL}' alt='Mothman' width='72' height='72'>",
        "<div class='titles'>",
        "<h1>SF <span class='ember-text'>Task Breakdown</span></h1>",
        f"<p class='meta'>{_esc(data.get('date_label', ''))} · "
        f"generated {_esc(data.get('generated_at', ''))}</p>",
        "</div></div>",
        f"<p class='lead'>{_esc(lead)}</p>",
        f"<div class='card stats'>{stat_html}</div>",
        "<h2>Priority queue</h2>",
        _table(
            ["Tier", "Item", "Priority", "Status", "Created", "Due / Modified", "Subject"],
            pri_rows,
            "No priority-flagged items.",
        ),
        "<h2>High &amp; medium Cases</h2>",
        "<h3 class='subheading'>High priority</h3>",
        _table(
            ["Case", "Priority", "Type", "Status", "Created", "Subject"],
            _case_rows(data.get("high_cases") or []),
        ),
        "<h3 class='subheading'>Medium priority</h3>",
        _table(
            ["Case", "Priority", "Type", "Status", "Created", "Subject"],
            _case_rows(data.get("medium_cases") or []),
        ),
        "<h2>New assignments (last 3 days)</h2>",
        _table(
            ["Case", "Priority", "Type", "Status", "Created", "Subject"],
            _case_rows(data.get("new_cases_last_3_days") or []),
        ),
        "<h2>Rate Changes — New</h2>",
        _table(
            ["Case", "Priority", "Type", "Status", "Created", "Subject"],
            _case_rows(data.get("rate_new_cases") or []),
            "No New rate cases.",
        ),
        "<h2>Open Leads</h2>",
        _table(
            ["Lead", "Status", "Created", "Company", "Name"],
            [
                [
                    _link(l.get("url"), l.get("company") or l.get("name") or "Lead"),
                    _esc(l.get("status")),
                    _esc(l.get("created")),
                    _esc(l.get("company")),
                    _esc(l.get("name")),
                ]
                for l in data.get("open_leads") or []
            ],
            "No open Leads.",
        ),
    ]

    bucket_order = [
        "Duplicate / merge",
        "Follow-up / callback",
        "Rate / negotiation",
        "COI / insurance",
        "Onboarding / vetting",
        "AP / payment",
        "Other",
        "Voicemail / 4046",
    ]
    buckets = data.get("task_buckets") or {}
    parts.append("<h2>Open Tasks by bucket</h2>")
    for b in bucket_order:
        items = buckets.get(b) or []
        if not items:
            continue
        parts.append(f"<h3 class='subheading'>{_esc(b)} ({len(items)})</h3>")
        show = items if b != "Voicemail / 4046" else items[:12]
        parts.append(
            _table(
                ["Task", "Status", "Created", "Due", "Related", "Subject"],
                _task_rows(show),
            )
        )
        if b == "Voicemail / 4046" and len(items) > 12:
            parts.append(
                f"<p class='muted'>+ {len(items) - 12} more voicemail triage tasks "
                "(see full queue in Salesforce).</p>"
            )

    parts.append(
        "<p class='footer'>Mothman · SF task breakdown · read-only snapshot</p>"
        "</main></body></html>"
    )
    return "".join(parts)


def _open_chrome(path: Path) -> None:
    chrome = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    if chrome.is_file():
        subprocess.Popen([str(chrome), str(path.resolve())])
    else:
        webbrowser.open(path.as_uri())


def main() -> int:
    parser = argparse.ArgumentParser(description="Render SF task breakdown HTML")
    parser.add_argument("data_json", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    if not args.data_json.is_file():
        print(f"ERROR: not found: {args.data_json}", file=sys.stderr)
        return 2

    data = json.loads(args.data_json.read_text(encoding="utf-8"))
    m = _DATE_STEM.match(args.data_json.stem)
    date_iso = m.group(1) if m else "report"
    out = args.output or (OUTPUT_ROOT / f"sf-task-breakdown-{date_iso}.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(data), encoding="utf-8")
    print(out.resolve())
    if args.open:
        _open_chrome(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
