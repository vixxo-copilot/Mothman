#!/usr/bin/env python3
"""Render mothman-good-morning briefing data as a cryptid-themed HTML page.

Stdlib only. Collect data via MCPs, write JSON, then:

  python render_good_morning_html.py path/to/data.json
  python render_good_morning_html.py path/to/data.json --open
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import webbrowser
from datetime import date, datetime, timedelta, tzinfo
from pathlib import Path
from typing import Any

try:
    from zoneinfo import ZoneInfo

    TZ = ZoneInfo("America/Chicago")
except Exception:

    def _nth_sunday(year: int, month: int, n: int) -> datetime:
        first = datetime(year, month, 1)
        day = 1 + (6 - first.weekday()) % 7 + 7 * (n - 1)
        return datetime(year, month, day)

    def _is_central_dst(dt: datetime) -> bool:
        local = dt.replace(tzinfo=None)
        start = _nth_sunday(dt.year, 3, 2).replace(hour=2)
        end = _nth_sunday(dt.year, 11, 1).replace(hour=2)
        return start <= local < end

    class _USCentralFallback(tzinfo):
        def utcoffset(self, dt: datetime | None) -> timedelta:
            if dt is None:
                return timedelta(hours=-6)
            return timedelta(hours=-5 if _is_central_dst(dt) else -6)

        def dst(self, dt: datetime | None) -> timedelta:
            if dt is None:
                return timedelta(0)
            return timedelta(hours=1) if _is_central_dst(dt) else timedelta(0)

        def tzname(self, dt: datetime | None) -> str:
            if dt is None:
                return "CST"
            return "CDT" if _is_central_dst(dt) else "CST"

    TZ = _USCentralFallback()

OUTPUT_ROOT = Path.cwd() / ".tmp" / "mothman-good-morning"
LIGHTNING_BASE = "https://vixxo.lightning.force.com/lightning/r"
# From .tmp/mothman-good-morning/*.html → repo assets/
BRAND_IMG_REL = "../../assets/mothman-profile.png"

FONT_LINKS = (
    "<link rel='preconnect' href='https://fonts.googleapis.com'>"
    "<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>"
    "<link href='https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700"
    "&family=Nunito:wght@400;600;700&display=swap' rel='stylesheet'>"
)

THEME_CSS = """\
:root{--void:#0d0b14;--plume:#1a1228;--mist:#2a1f3d;--ember:#e63e3e;--ember-dim:#a82828;\
--lavender:#c4b5d8;--moon:#f0e6f6;--gold:#d4a84b;--ok:#6bcb8a;--warn:#e6b84a;\
--shadow:0 16px 48px rgba(0,0,0,0.55);--glow:0 0 24px rgba(230,62,62,0.35);}\
html,body{min-height:100%;}\
body{font-family:Nunito,Segoe UI,system-ui,sans-serif;margin:0;padding:0;color:var(--lavender);\
min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:2.5rem 1.25rem 3rem;\
position:relative;overflow-x:hidden;background-color:var(--void);\
background-image:radial-gradient(ellipse at 20% 10%,rgba(230,62,62,0.12) 0%,transparent 40%),\
radial-gradient(ellipse at 80% 90%,rgba(106,63,160,0.18) 0%,transparent 45%),\
linear-gradient(165deg,#0d0b14 0%,#15101f 50%,#0a0810 100%);\
background-repeat:no-repeat;background-size:cover;background-attachment:fixed;}\
body::before,body::after{content:'';position:fixed;border-radius:50%;pointer-events:none;\
filter:blur(40px);opacity:0.4;}\
body::before{width:180px;height:180px;top:12%;left:8%;background:rgba(230,62,62,0.25);}\
body::after{width:220px;height:220px;bottom:8%;right:6%;background:rgba(74,45,122,0.35);}\
.ember{position:fixed;width:4px;height:4px;border-radius:50%;background:var(--ember);\
box-shadow:0 0 8px var(--ember);opacity:0.55;pointer-events:none;}\
.ember:nth-of-type(1){top:22%;right:16%;}\
.ember:nth-of-type(2){top:58%;left:12%;width:3px;height:3px;}\
.ember:nth-of-type(3){bottom:28%;right:24%;}\
.page-shell{width:min(960px,100%);flex:1 0 auto;align-self:stretch;max-width:960px;margin:0 auto;\
background:linear-gradient(180deg,var(--plume) 0%,#140f1f 100%);\
border:1px solid rgba(230,62,62,0.35);border-radius:18px;box-shadow:var(--shadow),var(--glow);\
padding:28px 32px 48px;position:relative;z-index:1;min-height:calc(100vh - 5.5rem);\
box-sizing:border-box;}\
.hero{display:flex;align-items:center;gap:18px;margin-bottom:8px;}\
.hero img{width:72px;height:72px;border-radius:50%;object-fit:cover;\
border:2px solid var(--ember);box-shadow:0 0 16px rgba(230,62,62,0.45);}\
.hero .titles{flex:1;}\
h1{font-family:Cinzel,Georgia,serif;color:var(--moon);margin:0 0 4px;font-size:1.7rem;font-weight:700;\
letter-spacing:0.02em;}\
h1 .ember-text{color:var(--ember);}\
h2{font-family:Cinzel,Georgia,serif;color:var(--moon);font-size:1.05rem;margin:28px 0 10px;\
border-bottom:1px solid rgba(230,62,62,0.35);padding-bottom:6px;letter-spacing:0.04em;\
text-transform:uppercase;font-weight:600;}\
h3.subheading{color:var(--lavender);font-size:0.95rem;margin:14px 0 6px;opacity:0.9;}\
.meta{color:var(--lavender);font-size:0.9rem;margin:0 0 8px;opacity:0.85;}\
.lead{color:var(--moon);font-size:1.05rem;margin:0 0 20px;line-height:1.45;}\
.card{background:rgba(42,31,61,0.55);border:1px solid rgba(196,181,216,0.12);\
border-radius:12px;padding:16px 18px;margin:12px 0;}\
.stats{display:flex;flex-wrap:wrap;gap:12px;}\
.stat{flex:1 1 140px;background:rgba(13,11,20,0.55);border:1px solid rgba(230,62,62,0.22);\
border-radius:8px;padding:12px;text-align:center;}\
.stat .n{font-size:1.6rem;font-weight:700;color:var(--ember);font-family:Cinzel,Georgia,serif;}\
.stat .l{font-size:0.85rem;color:var(--lavender);}\
table{width:100%;border-collapse:collapse;font-size:0.92rem;}\
th,td{border:1px solid rgba(196,181,216,0.15);padding:8px 10px;text-align:left;vertical-align:top;}\
th{background:rgba(230,62,62,0.2);color:var(--moon);font-family:Cinzel,Georgia,serif;\
font-size:0.8rem;letter-spacing:0.04em;text-transform:uppercase;}\
tr:nth-child(even) td{background:rgba(13,11,20,0.35);}\
a{color:#e8a0a0;}a:hover{color:var(--ember);}\
ul,ol{margin:8px 0;padding-left:1.2rem;}li{margin:6px 0;}\
.tag{font-size:0.72rem;background:rgba(230,62,62,0.2);color:var(--moon);\
padding:2px 7px;border-radius:4px;margin-left:6px;border:1px solid rgba(230,62,62,0.35);\
text-transform:uppercase;letter-spacing:0.03em;}\
.tag.fyi{background:rgba(106,63,160,0.35);border-color:rgba(196,181,216,0.25);}\
.tag.ok{background:rgba(107,203,138,0.2);border-color:rgba(107,203,138,0.4);color:var(--ok);}\
.muted{color:var(--lavender);font-style:italic;opacity:0.7;}\
.warn{background:rgba(230,184,74,0.12);border:1px solid rgba(230,184,74,0.45);\
padding:10px 14px;border-radius:8px;color:var(--warn);}\
.ok-banner{background:rgba(107,203,138,0.1);border:1px solid rgba(107,203,138,0.4);\
padding:10px 14px;border-radius:8px;color:var(--ok);}\
.moves li{font-weight:600;color:var(--moon);}\
.glance-list{margin:0;padding-left:1.1rem;}\
.footer{margin-top:36px;padding-top:14px;border-top:1px solid rgba(196,181,216,0.12);\
font-size:0.8rem;opacity:0.65;text-align:center;}"""

WMO_LABELS = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Fog",
    51: "Drizzle",
    61: "Rain",
    63: "Rain",
    65: "Heavy rain",
    71: "Snow",
    80: "Showers",
    95: "Thunderstorm",
}


def _esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _weather_label(code: Any) -> str:
    if code is None:
        return "—"
    try:
        n = int(code)
    except (TypeError, ValueError):
        return "—"
    return WMO_LABELS.get(n, f"Code {code}")


_DATE_FROM_STEM = re.compile(r"^data-(\d{4}-\d{2}-\d{2})$")


def _briefing_date_iso(data: dict[str, Any], data_json: Path | None = None) -> str:
    snap = data.get("metrics_snapshot") or {}
    if snap.get("date"):
        return str(snap["date"])
    if data_json is not None:
        m = _DATE_FROM_STEM.match(data_json.stem)
        if m:
            return m.group(1)
    return datetime.now(TZ).date().isoformat()


def _format_date_label(iso_date: str) -> str:
    d = date.fromisoformat(iso_date)
    return f"{d.strftime('%A, %B')} {d.day}, {d.year}"


def _case_link(case_id: str | None = None, case_number: str | None = None) -> str | None:
    if case_id:
        return f"{LIGHTNING_BASE}/Case/{case_id}/view"
    return None


def _render_meetings(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p class='muted'>No meetings today — clear airspace.</p>"
    parts = [
        "<table><thead><tr><th>Time</th><th>Subject</th><th>Notes</th></tr></thead><tbody>"
    ]
    for row in rows:
        start = _esc(row.get("start") or row.get("start_local") or "")
        end = _esc(row.get("end") or row.get("end_local") or "")
        subject = _esc(row.get("subject") or "")
        notes = _esc(row.get("notes") or row.get("location") or "")
        join_url = row.get("join_url") or row.get("joinUrl")
        if join_url:
            notes = (
                f"<a href='{_esc(join_url)}' target='_blank' rel='noopener'>"
                "Teams join</a>"
            )
        parts.append(
            f"<tr><td>{start}–{end}</td><td>{subject}</td><td>{notes}</td></tr>"
        )
    parts.append("</tbody></table>")
    return "".join(parts)


def _render_mail_rows(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p class='muted'>None</p>"
    parts = ["<ul class='mail-list'>"]
    for row in rows:
        sender = _esc(row.get("from") or row.get("sender") or "")
        subject = _esc(row.get("subject") or "")
        tag = (row.get("tag") or "").strip()
        tag_cls = " tag fyi" if tag.upper() == "FYI" else " tag"
        tag_html = f"<span class='{tag_cls.strip()}'>{_esc(tag)}</span>" if tag else ""
        parts.append(
            f"<li><strong>{sender}</strong> — {subject}{tag_html}</li>"
        )
    parts.append("</ul>")
    return "".join(parts)


def _render_case_sample(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    parts = [
        "<h3 class='subheading'>Recent open cases</h3>",
        "<table><thead><tr><th>Case</th><th>Subject</th><th>Status</th>"
        "<th>Priority</th></tr></thead><tbody>",
    ]
    for row in rows:
        num = _esc(row.get("CaseNumber") or row.get("case_number") or "")
        cid = row.get("Id") or row.get("id")
        subject = _esc(row.get("Subject") or row.get("subject") or "")
        status = _esc(row.get("Status") or row.get("status") or "")
        priority = _esc(row.get("Priority") or row.get("priority") or "")
        link = _case_link(str(cid) if cid else None)
        case_cell = (
            f"<a href='{_esc(link)}' target='_blank' rel='noopener'>{num}</a>"
            if link
            else num
        )
        parts.append(
            f"<tr><td>{case_cell}</td><td>{subject}</td>"
            f"<td>{status}</td><td>{priority}</td></tr>"
        )
    parts.append("</tbody></table>")
    return "".join(parts)


def _fmt_created(value: Any) -> str:
    """Format ISO / SF datetime to YYYY-MM-DD for CreatedDate display."""
    if value is None or value == "":
        return "—"
    text = str(value).strip()
    if "T" in text:
        text = text.split("T", 1)[0]
    return text[:10] if len(text) >= 10 else text


def _render_case_type_breakdown(types: list[dict[str, Any]]) -> str:
    """Render RecordType subsections; Rate Changes first when present."""
    if not types:
        return ""
    parts: list[str] = []
    for block in types:
        label = _esc(block.get("label") or block.get("record_type") or "Other")
        total = _esc(block.get("total", "—"))
        new_count = block.get("new_count")
        if new_count is None:
            new_count = block.get("not_started_count")
        new_esc = _esc(new_count if new_count is not None else "—")
        oldest = _fmt_created(
            block.get("oldest_new_created") or block.get("oldest_created")
        )
        newest = _fmt_created(
            block.get("newest_new_created") or block.get("newest_created")
        )
        priority = bool(block.get("priority"))
        heading = f"★ {label}" if priority else label
        parts.append(f"<h3 class='subheading'>{heading}</h3>")
        parts.append("<div class='card'>")
        parts.append(
            f"<p><strong>Open:</strong> {total} · "
            f"<strong>New / not started:</strong> {new_esc}"
        )
        if oldest != "—" or newest != "—":
            range_bit = _esc(oldest)
            if newest != "—" and newest != oldest:
                range_bit = f"{range_bit} → {_esc(newest)}"
            parts.append(f" · <strong>New created:</strong> {range_bit}")
        parts.append("</p>")
        statuses = block.get("status_breakdown") or {}
        if isinstance(statuses, dict) and statuses:
            bits = [f"{_esc(k)}: {_esc(v)}" for k, v in statuses.items()]
            parts.append(f"<p class='muted'>{' · '.join(bits)}</p>")
        cases = block.get("new_cases") or block.get("cases") or []
        if cases:
            parts.append(
                "<table><thead><tr><th>Case</th><th>Subject</th>"
                "<th>Status</th><th>Created</th></tr></thead><tbody>"
            )
            for row in cases:
                num = _esc(row.get("CaseNumber") or row.get("case_number") or "")
                subject = _esc(row.get("Subject") or row.get("subject") or "")
                status = _esc(row.get("Status") or row.get("status") or "New")
                created = _esc(
                    _fmt_created(row.get("CreatedDate") or row.get("created"))
                )
                cid = row.get("Id") or row.get("id")
                link = _case_link(str(cid) if cid else None)
                case_cell = (
                    f"<a href='{_esc(link)}' target='_blank' rel='noopener'>{num}</a>"
                    if link
                    else num
                )
                parts.append(
                    f"<tr><td>{case_cell}</td><td>{subject}</td>"
                    f"<td>{status}</td><td>{created}</td></tr>"
                )
            parts.append("</tbody></table>")
        parts.append("</div>")
    return "".join(parts)


def _render_sync_cases(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p class='ok-banner'>No cases needing mail sync.</p>"
    parts = [
        "<table><thead><tr><th>Case</th><th>Subject</th>"
        "<th>Missing</th></tr></thead><tbody>"
    ]
    for row in rows:
        num = _esc(row.get("case_number") or row.get("CaseNumber") or "")
        subject = _esc(row.get("subject") or row.get("Subject") or "")
        missing = _esc(row.get("missing_count") or row.get("missing") or "—")
        url = row.get("url")
        case_cell = (
            f"<a href='{_esc(url)}' target='_blank' rel='noopener'>{num}</a>"
            if url
            else num
        )
        parts.append(
            f"<tr><td>{case_cell}</td><td>{subject}</td><td>{missing}</td></tr>"
        )
    parts.append("</tbody></table>")
    return "".join(parts)


def _render_account_rows(rows: list[dict[str, Any]], *, kind: str) -> str:
    if not rows:
        return "<p class='muted'>None</p>"
    parts = ["<ul>"]
    for row in rows:
        num = _esc(row.get("case_number") or "")
        keep = _esc(row.get("keep_account") or row.get("current_account") or "")
        reason = _esc(row.get("reason") or row.get("suggested") or "")
        if kind == "do_not_apply":
            parts.append(
                f"<li><strong>Case {num}</strong> — keep {keep}"
                f"{f' <span class=\"muted\">({reason})</span>' if reason else ''}</li>"
            )
        else:
            suggested = _esc(row.get("suggested_account") or row.get("suggested") or "")
            parts.append(
                f"<li><strong>Case {num}</strong> — {keep or 'current?'}"
                f"{f' → {_esc(suggested)}' if suggested else ''}"
                f"{f' <span class=\"muted\">({reason})</span>' if reason else ''}</li>"
            )
    parts.append("</ul>")
    return "".join(parts)


def _render_follow_ups(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p class='muted'>None queued.</p>"
    parts = ["<ul>"]
    for row in rows:
        if isinstance(row, str):
            parts.append(f"<li>{_esc(row)}</li>")
            continue
        item = _esc(row.get("item") or "")
        owner = _esc(row.get("owner") or "")
        when = _esc(row.get("when") or "")
        meta = " · ".join(x for x in (owner, when) if x)
        parts.append(
            f"<li>{item}"
            f"{f'<span class=\"meta\"> — {meta}</span>' if meta else ''}</li>"
        )
    parts.append("</ul>")
    return "".join(parts)


def render_html(data: dict[str, Any]) -> str:
    if data.get("date_label"):
        date_label = _esc(data["date_label"])
    else:
        iso = (data.get("metrics_snapshot") or {}).get("date")
        if iso:
            date_label = _esc(_format_date_label(str(iso)))
        else:
            dt_now = datetime.now(TZ)
            date_label = _esc(
                f"{dt_now.strftime('%A, %B')} {dt_now.day}, {dt_now.year}"
            )
    generated = _esc(
        data.get("generated_at") or datetime.now(TZ).strftime("%Y-%m-%d %H:%M %Z")
    )

    weather = data.get("weather") or {}
    sf = data.get("salesforce") or {}
    inbox = data.get("inbox") or {}
    sync = data.get("case_mail_sync") or {}
    acct = data.get("account_corrections") or {}
    glance = data.get("glance") or {}
    skipped = data.get("skipped") or []
    first_moves = data.get("first_moves") or []
    blockers = data.get("blockers") or []
    follow_ups = data.get("follow_ups") or []
    lead = data.get("lead") or ""

    w_code = weather.get("weather_code")
    brand_src = _esc(data.get("brand_image") or BRAND_IMG_REL)

    # Prefer °F; fall back to °C fields if only those present
    temp = weather.get("temp_f")
    feels = weather.get("feels_like_f")
    high = weather.get("high_f")
    low = weather.get("low_f")
    wind = weather.get("wind_mph")
    unit_t, unit_w = "°F", "mph"
    if temp is None and weather.get("temp_c") is not None:
        temp = weather.get("temp_c")
        feels = weather.get("feels_like_c")
        high = weather.get("high_c")
        low = weather.get("low_c")
        wind = weather.get("wind_kmh")
        unit_t, unit_w = "°C", "km/h"

    parts: list[str] = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        f"<title>Good Morning, Crystal — {date_label}</title>",
        FONT_LINKS,
        f"<style>{THEME_CSS}</style></head><body>",
        "<span class='ember' aria-hidden='true'></span>",
        "<span class='ember' aria-hidden='true'></span>",
        "<span class='ember' aria-hidden='true'></span>",
        "<main class='page-shell'>",
        "<div class='hero'>",
        f"<img src='{brand_src}' alt='Mothman' width='72' height='72'>",
        "<div class='titles'>",
        "<h1>Good Morning, <span class='ember-text'>Crystal</span></h1>",
        f"<p class='meta'>{date_label} · Generated {generated} · CST</p>",
        "</div></div>",
    ]

    if lead:
        parts.append(f"<p class='lead'>{_esc(lead)}</p>")

    if skipped:
        parts.append("<div class='warn'><strong>Partial run:</strong> ")
        parts.append(_esc("; ".join(str(s) for s in skipped)))
        parts.append("</div>")

    # Glance
    if glance:
        parts.append("<h2>Today at a glance</h2><div class='card'>")
        if glance.get("meeting_count") is not None:
            parts.append(
                f"<p><strong>Meetings:</strong> {_esc(glance['meeting_count'])}</p>"
            )
        hard = glance.get("hard_stops") or []
        if hard:
            parts.append("<p><strong>Hard stops:</strong></p><ul class='glance-list'>")
            for item in hard:
                parts.append(f"<li>{_esc(item)}</li>")
            parts.append("</ul>")
        if glance.get("coverage"):
            parts.append(
                f"<p><strong>Coverage:</strong> {_esc(glance['coverage'])}</p>"
            )
        parts.append("</div>")

    # Weather
    parts.append("<h2>Weather — Wichita, KS</h2><div class='card'>")
    parts.append(
        f"<p><strong>Now:</strong> {_esc(temp)}{unit_t}"
        f" (feels {_esc(feels)}{unit_t}) · "
        f"{_esc(_weather_label(w_code))} · "
        f"Wind {_esc(wind)} {unit_w}</p>"
    )
    parts.append(
        f"<p><strong>Today:</strong> high {_esc(high)}{unit_t} / "
        f"low {_esc(low)}{unit_t} · "
        f"Precip chance {_esc(weather.get('precip_pct'))}%</p>"
    )
    if weather.get("summary"):
        parts.append(f"<p class='muted'>{_esc(weather['summary'])}</p>")
    parts.append("</div>")

    # Meetings
    meetings = data.get("meetings") or []
    parts.append(f"<h2>Today's meetings ({len(meetings)})</h2>")
    parts.append(_render_meetings(meetings))

    # Salesforce
    parts.append("<h2>Salesforce — open workload</h2><div class='card'><div class='stats'>")
    for key, label in (
        ("total_open", "Total open"),
        ("cases", "Cases"),
        ("leads", "Leads"),
        ("tasks", "Tasks"),
    ):
        parts.append(
            f"<div class='stat'><div class='n'>{_esc(sf.get(key, '—'))}</div>"
            f"<div class='l'>{label}</div></div>"
        )
    parts.append("</div></div>")
    case_types = sf.get("case_types") or []
    if case_types:
        parts.append("<h2>Open Cases by type</h2>")
        parts.append(
            "<p class='muted'>Rate Changes first. New / not started = Status New. "
            "Created dates are Case CreatedDate (Central calendar day).</p>"
        )
        parts.append(_render_case_type_breakdown(case_types))
    else:
        parts.append("<div class='card'>")
        parts.append(_render_case_sample(sf.get("open_cases_sample") or []))
        parts.append("</div>")

    qwb = sf.get("queue_workbook") or {}
    if qwb.get("path"):
        parts.append("<h2>SF queue Excel</h2><div class='card'>")
        parts.append(
            f"<p><strong>{_esc(qwb.get('total_open', '—'))}</strong> open cases · "
            f"by type × status · oldest CreatedDate at top of each status</p>"
        )
        parts.append(
            f"<p>Stable workbook: <code>{_esc(qwb['path'])}</code></p>"
        )
        if qwb.get("dated_path"):
            parts.append(
                f"<p class='muted'>Dated copy: <code>{_esc(qwb['dated_path'])}</code></p>"
            )
        if qwb.get("note"):
            parts.append(f"<p class='muted'>{_esc(qwb['note'])}</p>")
        parts.append("</div>")

    # Case mail sync
    needing = sync.get("cases_needing_sync")
    if needing is None:
        needing = len(sync.get("cases") or [])
    parts.append(f"<h2>SF case mail to sync ({_esc(needing)})</h2>")
    if sync.get("note"):
        parts.append(f"<p class='muted'>{_esc(sync['note'])}</p>")
    parts.append(_render_sync_cases(sync.get("cases") or []))

    # Account corrections
    parts.append("<h2>Account corrections</h2><div class='card'>")
    if acct.get("note"):
        parts.append(f"<p class='muted'>{_esc(acct['note'])}</p>")
    dna = acct.get("do_not_apply") or []
    rec = acct.get("recommended") or []
    rev = acct.get("review") or []
    if dna:
        parts.append("<h3 class='subheading'>Do not apply (confirmed / false positives)</h3>")
        parts.append(_render_account_rows(dna, kind="do_not_apply"))
    if rec:
        parts.append("<h3 class='subheading'>Recommended (review before write)</h3>")
        parts.append(_render_account_rows(rec, kind="recommended"))
    if rev:
        parts.append("<h3 class='subheading'>Needs review</h3>")
        parts.append(_render_account_rows(rev, kind="review"))
    if not dna and not rec and not rev:
        parts.append("<p class='ok-banner'>No account corrections flagged.</p>")
    parts.append("</div>")

    # Inbox
    parts.append("<h2>Inbox highlights</h2><div class='card'>")
    parts.append(
        f"<p><strong>Unread:</strong> {_esc(inbox.get('unread', 0))} · "
        f"<strong>Needs action:</strong> {_esc(inbox.get('needs_action_count', 0))}</p>"
    )
    parts.append(_render_mail_rows(inbox.get("needs_action") or []))
    if inbox.get("no_action_summary"):
        parts.append(
            f"<p><strong>Noise / FYI:</strong> {_esc(inbox['no_action_summary'])}</p>"
        )
    parts.append("</div>")

    # Blockers
    parts.append("<h2>Blockers and risks</h2>")
    if blockers:
        parts.append("<ul>")
        for b in blockers:
            parts.append(f"<li>{_esc(b)}</li>")
        parts.append("</ul>")
    else:
        parts.append("<p class='muted'>None flagged.</p>")

    # Follow-ups
    parts.append("<h2>Follow-ups</h2>")
    parts.append(_render_follow_ups(follow_ups))

    # Day-over-day
    dod = data.get("day_over_day") or {}
    if dod.get("available") and dod.get("rows"):
        prior_label = dod.get("prior_date_label") or dod.get("prior_date") or "Prior"
        parts.append(f"<h2>Day-over-day — vs {_esc(prior_label)}</h2>")
        parts.append("<div class='card'><table><thead><tr>")
        parts.append("<th>Metric</th><th>Prior</th><th>Today</th><th>Change</th>")
        parts.append("</tr></thead><tbody>")
        for row in dod["rows"]:
            delta = row.get("delta")
            if delta is None:
                delta_s = "—"
            elif delta > 0:
                delta_s = f"+{delta}"
            elif delta < 0:
                delta_s = str(delta)
            else:
                delta_s = "—"
            parts.append(
                "<tr>"
                f"<td>{_esc(row.get('metric', ''))}</td>"
                f"<td>{_esc(row.get('prior', '—'))}</td>"
                f"<td>{_esc(row.get('today', '—'))}</td>"
                f"<td>{_esc(delta_s)}</td>"
                "</tr>"
            )
        parts.append("</tbody></table>")
        if dod.get("summary"):
            parts.append(
                f"<p><strong>Read:</strong> {_esc(dod['summary'])}</p>"
            )
        parts.append("</div>")
    elif dod.get("available") is False:
        parts.append(
            "<h2>Day-over-day</h2>"
            "<p class='muted'>No prior snapshot — baseline set today.</p>"
        )

    # First moves
    parts.append("<h2>First moves</h2><ol class='moves'>")
    for move in first_moves:
        parts.append(f"<li>{_esc(move)}</li>")
    if not first_moves:
        parts.append("<li class='muted'>—</li>")
    parts.append("</ol>")

    parts.append(
        "<p class='footer'>Mothman · work briefing · dry-run sync &amp; audit only</p>"
    )
    parts.append("</main></body></html>")
    return "".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render Good Morning, Crystal HTML (Mothman theme)"
    )
    parser.add_argument("data_json", type=Path, help="JSON payload from the agent run")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output HTML path (default: .tmp/mothman-good-morning/good-morning-YYYY-MM-DD.html)",
    )
    parser.add_argument("--open", action="store_true", help="Open HTML in default browser")
    args = parser.parse_args()

    if not args.data_json.is_file():
        print(f"ERROR: data file not found: {args.data_json}", file=sys.stderr)
        sys.exit(2)

    data = json.loads(args.data_json.read_text(encoding="utf-8"))
    briefing_date = _briefing_date_iso(data, args.data_json)
    out = args.output or OUTPUT_ROOT / f"good-morning-{briefing_date}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(data), encoding="utf-8")
    print(out.resolve())

    if args.open:
        webbrowser.open(out.as_uri())


if __name__ == "__main__":
    main()
