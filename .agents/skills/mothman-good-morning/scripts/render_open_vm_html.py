#!/usr/bin/env python3
"""Render Crystal's open voicemail Case JSON as Mothman-themed HTML."""

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
_DATE_STEM = re.compile(r"open-voicemail-(\d{4}-\d{2}-\d{2})$")


def _esc(v: Any) -> str:
    return html.escape("" if v is None else str(v))


def _link(url: str | None, label: str) -> str:
    if not url:
        return _esc(label)
    return f"<a href='{_esc(url)}' target='_blank' rel='noopener'>{_esc(label)}</a>"


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


def _case_rows(cases: list[dict[str, Any]]) -> list[list[str]]:
    out: list[list[str]] = []
    for c in cases:
        out.append(
            [
                _link(c.get("url"), f"Case {c.get('number')}"),
                _esc(c.get("status")),
                _esc(c.get("type_picklist") or "—"),
                _esc(c.get("intake")),
                _esc(c.get("created")),
                _esc(c.get("age_days") if c.get("age_days") is not None else "—"),
                _esc(c.get("account") or "—"),
                _esc((c.get("subject") or "")[:120]),
            ]
        )
    return out


def render_html(data: dict[str, Any]) -> str:
    summary = data.get("summary") or {}
    lead = (
        f"Open voicemail Cases {summary.get('total_open', 0)} · "
        f"untriaged {summary.get('untriaged', 0)} · "
        f"rewritten {summary.get('triaged', 0)} · "
        f"not Crystal {summary.get('not_crystal', 0)}."
    )
    stats = [
        ("Open VM", summary.get("total_open", 0)),
        ("Untriaged", summary.get("untriaged", 0)),
        ("Rewritten", summary.get("triaged", 0)),
        ("Not Crystal", summary.get("not_crystal", 0)),
    ]
    stat_html = "".join(
        f"<div class='stat'><div class='n'>{_esc(n)}</div>"
        f"<div class='l'>{_esc(label)}</div></div>"
        for label, n in stats
    )
    headers = [
        "Case",
        "Status",
        "Type",
        "Intake",
        "Created",
        "Age",
        "Account",
        "Subject",
    ]
    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>Open Voicemail Cases — {_esc(data.get('date_label', ''))}</title>",
        FONT_LINKS,
        f"<style>{THEME_CSS}</style></head><body>",
        "<span class='ember'></span><span class='ember'></span><span class='ember'></span>",
        "<main class='page-shell'>",
        "<div class='hero'>",
        f"<img src='{BRAND_IMG_REL}' alt='Mothman' width='72' height='72'>",
        "<div class='titles'>",
        "<h1>Open <span class='ember-text'>Voicemail</span> Cases</h1>",
        f"<p class='meta'>{_esc(data.get('date_label', ''))} · "
        f"generated {_esc(data.get('generated_at', ''))} · "
        f"{_esc(data.get('owner_email', ''))}</p>",
        "</div></div>",
        f"<p class='lead'>{_esc(lead)}</p>",
        f"<div class='card stats'>{stat_html}</div>",
        "<h2>Untriaged (generic subject)</h2>",
        _table(headers, _case_rows(data.get("untriaged") or []), "None untriaged."),
        "<h2>Rewritten / triaged (still open on your queue)</h2>",
        _table(headers, _case_rows(data.get("triaged") or []), "None still open."),
        "<h2>Not Crystal — Prospect SP / onboarding</h2>",
        f"<p class='muted'>{_esc(data.get('not_crystal_note') or '')}</p>",
        _table(
            ["Case", "Why", "Type", "Status", "Created", "Subject"],
            [
                [
                    _link(c.get("url"), f"Case {c.get('number')}"),
                    _esc(c.get("not_crystal_reason") or ""),
                    _esc(c.get("type_picklist") or "—"),
                    _esc(c.get("status")),
                    _esc(c.get("created")),
                    _esc((c.get("subject") or "")[:110]),
                ]
                for c in data.get("not_crystal") or []
            ],
            "None flagged.",
        ),
        "<p class='footer'>Mothman · Open voicemail Cases · Crystal queue · recreate after triage</p>",
        "</main></body></html>",
    ]
    return "".join(parts)


def _open_chrome(path: Path) -> None:
    chrome = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    if chrome.is_file():
        subprocess.Popen([str(chrome), str(path.resolve())])
    else:
        webbrowser.open(path.as_uri())


def main() -> int:
    parser = argparse.ArgumentParser(description="Render open voicemail HTML")
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
    out = args.output or (OUTPUT_ROOT / f"open-voicemail-{date_iso}.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(data), encoding="utf-8")
    print(out.resolve())
    if args.open:
        _open_chrome(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
