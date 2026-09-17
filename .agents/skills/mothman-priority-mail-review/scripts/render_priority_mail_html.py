#!/usr/bin/env python3
"""Render priority-mail JSON as Mothman-themed HTML."""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parents[1] / "mothman-good-morning" / "scripts"))

from render_good_morning_html import FONT_LINKS, THEME_CSS  # noqa: E402

# From .tmp/mothman-priority-mail/*.html → repo assets/
BRAND_IMG_REL = "../../assets/mothman-profile.png"
OUTPUT_ROOT = Path.cwd() / ".tmp" / "mothman-priority-mail"


def _esc(v: Any) -> str:
    return html.escape("" if v is None else str(v))


def _link(url: str | None, label: str) -> str:
    if not url:
        return _esc(label)
    return f"<a href='{_esc(url)}' target='_blank' rel='noopener'>{_esc(label)}</a>"


def _urg_tag(urgency: str | None) -> str:
    u = (urgency or "fyi").lower()
    cls = {
        "urgent": "tag",
        "today": "tag",
        "this_week": "tag fyi",
        "fyi": "tag ok",
        "archive": "tag fyi",
    }.get(u, "tag fyi")
    label = u.replace("_", " ")
    return f"<span class='{cls}'>{_esc(label)}</span>"


def _table(headers: list[str], rows: list[list[str]], empty: str = "None.") -> str:
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


def _item_rows(items: list[dict], include_folder: bool = False) -> list[list[str]]:
    rows = []
    for it in items:
        subj = _link(it.get("web_link"), (it.get("subject") or "")[:110])
        if it.get("has_attachments"):
            subj += " <span class='muted'>att</span>"
        row = [
            _esc(it.get("received") or ""),
            _esc(it.get("from_name") or ""),
            subj,
            _urg_tag(it.get("urgency")),
            _esc(it.get("tag") or ""),
            _esc(it.get("status") or ""),
            _esc((it.get("preview") or "")[:140]),
        ]
        if include_folder:
            row.insert(1, _esc(it.get("folder") or ""))
        rows.append(row)
    return rows


def render_html(data: dict[str, Any]) -> str:
    summary = data.get("summary") or {}
    stats = [
        ("Unread", summary.get("unread_total", 0)),
        ("Priority", summary.get("priority_count", 0)),
        ("Urgent", summary.get("urgent", 0)),
        ("Today", summary.get("today", 0)),
        ("This week", summary.get("this_week", 0)),
    ]
    stat_html = "".join(
        f"<div class='stat'><div class='n'>{_esc(n)}</div><div class='l'>{_esc(l)}</div></div>"
        for l, n in stats
    )

    pri_headers = [
        "Received",
        "Box",
        "From",
        "Subject",
        "Urgency",
        "Tag",
        "Status",
        "Preview",
    ]
    box_headers = [
        "Received",
        "From",
        "Subject",
        "Urgency",
        "Tag",
        "Status",
        "Preview",
    ]

    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>Priority Mail — {_esc(data.get('date_label', ''))}</title>",
        FONT_LINKS,
        f"<style>{THEME_CSS}</style></head><body>",
        "<span class='ember'></span><span class='ember'></span><span class='ember'></span>",
        "<main class='page-shell'>",
        "<div class='hero'>",
        f"<img src='{BRAND_IMG_REL}' alt='Mothman' width='72' height='72'>",
        "<div class='titles'>",
        "<h1>Priority <span class='ember-text'>Mail Review</span></h1>",
        f"<p class='meta'>{_esc(data.get('date_label', ''))} · "
        f"generated {_esc(data.get('generated_at', ''))}</p>",
        "</div></div>",
        f"<p class='lead'>{_esc(data.get('lead', ''))}</p>",
        f"<div class='card stats'>{stat_html}</div>",
        "<h2>Higher priority</h2>",
        _table(
            pri_headers,
            _item_rows(data.get("priority_items") or [], include_folder=True),
            "No urgent / today / this-week asks.",
        ),
        "<h2>First moves</h2><ol>",
    ]
    for move in data.get("first_moves") or []:
        parts.append(f"<li>{_esc(move)}</li>")
    parts.append("</ol>")

    for box in data.get("boxes") or []:
        label = box.get("label") or box.get("id")
        count = box.get("unread_count", 0)
        path = box.get("folder_path") or box.get("folder_name") or ""
        parts.append(f"<h2>{_esc(label)} <span class='muted'>({count} unread)</span></h2>")
        if not box.get("found"):
            parts.append(
                f"<p class='muted'>{_esc(box.get('error') or 'Folder not found.')}</p>"
            )
            continue
        if path:
            parts.append(f"<p class='muted'>{_esc(path)}</p>")
        noise = box.get("noise_groups") or []
        if noise:
            parts.append("<h3 class='subheading'>Noise (collapsed)</h3><ul>")
            for g in noise:
                parts.append(
                    "<li>"
                    f"{_esc(g.get('from_name'))} — {g.get('count')} messages "
                    f"({_esc(g.get('first_received'))} → {_esc(g.get('last_received'))})"
                    f"<br><span class='muted'>{_esc(g.get('sample_subject'))}</span>"
                    "</li>"
                )
            parts.append("</ul>")
        listed = box.get("items") or []
        parts.append("<h3 class='subheading'>Oldest to newest</h3>")
        parts.append(
            _table(
                box_headers,
                _item_rows(listed),
                "No unread in this box.",
            )
        )

    parts.append(
        "<p class='footer'>Mothman · priority mail review · read-only · no mail sent</p>"
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
    parser = argparse.ArgumentParser(description="Render priority mail HTML")
    parser.add_argument("data_json", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    if not args.data_json.is_file():
        print(f"ERROR: not found: {args.data_json}", file=sys.stderr)
        return 2

    data = json.loads(args.data_json.read_text(encoding="utf-8"))
    date_iso = data.get("date") or "report"
    out = args.output or (OUTPUT_ROOT / f"priority-mail-{date_iso}.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(data), encoding="utf-8")
    print(out.resolve())
    if args.open:
        _open_chrome(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
