#!/usr/bin/env python3
"""Render SF intra-duplicate scan JSON as Mothman-themed HTML."""

from __future__ import annotations

import html
import json
import sys
import webbrowser
from pathlib import Path

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
.page-shell{width:min(1100px,100%);flex:1 0 auto;align-self:stretch;max-width:1100px;margin:0 auto;\
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
.meta{color:var(--lavender);font-size:0.9rem;margin:0 0 8px;opacity:0.85;}\
.card{background:rgba(42,31,61,0.55);border:1px solid rgba(196,181,216,0.12);\
border-radius:12px;padding:16px 18px;margin:12px 0;}\
.stats{display:flex;flex-wrap:wrap;gap:12px;}\
.stat{flex:1 1 120px;background:rgba(13,11,20,0.55);border:1px solid rgba(230,62,62,0.22);\
border-radius:8px;padding:12px;text-align:center;}\
.stat .n{font-size:1.6rem;font-weight:700;color:var(--ember);font-family:Cinzel,Georgia,serif;}\
.stat .l{font-size:0.85rem;color:var(--lavender);}\
.stat.warn .n{color:var(--warn);}\
.stat.ok .n{color:var(--ok);}\
table{width:100%;border-collapse:collapse;font-size:0.92rem;}\
th,td{border:1px solid rgba(196,181,216,0.15);padding:8px 10px;text-align:left;vertical-align:top;}\
th{background:rgba(230,62,62,0.2);color:var(--moon);font-family:Cinzel,Georgia,serif;\
font-size:0.8rem;letter-spacing:0.04em;text-transform:uppercase;}\
tr:nth-child(even) td{background:rgba(13,11,20,0.35);}\
.primary{font-weight:700;color:var(--moon);}\
.tag{font-size:0.72rem;background:rgba(230,62,62,0.2);color:var(--moon);\
padding:2px 7px;border-radius:4px;border:1px solid rgba(230,62,62,0.35);\
text-transform:uppercase;letter-spacing:0.03em;display:inline-block;}\
.tag.ok{background:rgba(107,203,138,0.2);border-color:rgba(107,203,138,0.4);color:var(--ok);}\
.tag.warn{background:rgba(230,184,74,0.12);border-color:rgba(230,184,74,0.45);color:var(--warn);}\
.warn-box{background:rgba(230,184,74,0.12);border:1px solid rgba(230,184,74,0.45);\
padding:10px 14px;border-radius:8px;color:var(--warn);margin:12px 0;}\
.muted{color:var(--lavender);font-style:italic;opacity:0.7;}\
.footer{margin-top:36px;padding-top:14px;border-top:1px solid rgba(196,181,216,0.12);\
font-size:0.8rem;opacity:0.65;text-align:center;}\
.num{text-align:right;font-variant-numeric:tabular-nums;}\
a{color:var(--moon);text-decoration:underline;text-decoration-color:rgba(240,230,246,0.45);\
text-underline-offset:2px;}\
a:hover{color:#fff;text-decoration-color:var(--gold);}\
a:visited{color:#e8d8f8;}\
td a,th a{color:#faf5ff;font-weight:600;}\
.case-link{color:#fff;font-weight:700;letter-spacing:0.02em;\
text-decoration:underline;text-decoration-color:rgba(212,168,75,0.7);}\
.case-link:hover{color:var(--gold);text-decoration-color:var(--gold);}\
.ext-link{color:#f5eeff;font-weight:600;}\
.ext-link:hover{color:var(--gold);}"""

LIGHTNING = "https://vixxo.lightning.force.com/lightning/r/Case/{case_id}/view"
BRAND_REL = "../../../../assets/mothman-profile.png"


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def case_link(case: dict) -> str:
    num = esc(case.get("case_number") or "")
    cid = case.get("id")
    if cid:
        return (
            f"<a class='case-link' href='{LIGHTNING.format(case_id=esc(cid))}' "
            f"target='_blank' rel='noopener'>{num}</a>"
        )
    return num


def stat_card(label: str, value: object, css: str = "") -> str:
    cls = f"stat {css}".strip()
    return f"<div class='{cls}'><div class='n'>{esc(value)}</div><div class='l'>{esc(label)}</div></div>"


def render_table(headers: list[str], rows: list[list[str]], num_cols: set[int] | None = None) -> str:
    num_cols = num_cols or set()
    parts = ["<table><thead><tr>"]
    for h in headers:
        parts.append(f"<th>{esc(h)}</th>")
    parts.append("</tr></thead><tbody>")
    for row in rows:
        parts.append("<tr>")
        for i, cell in enumerate(row):
            cls = " class='num'" if i in num_cols else ""
            parts.append(f"<td{cls}>{cell}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def high_confidence_pairs(data: dict) -> list[tuple[dict, dict, str]]:
    out: list[tuple[dict, dict, str]] = []
    seen: set[frozenset[str]] = set()

    for group in data.get("phone_duplicates") or []:
        primary = group.get("recommended_primary") or {}
        others = group.get("merge_candidates") or group.get("others") or []
        if not primary or not others:
            continue
        key = frozenset(
            [primary.get("case_number", "")] + [o.get("case_number", "") for o in others]
        )
        if key in seen:
            continue
        seen.add(key)
        out.append((primary, others[0], "Voicemail / phone match"))

    for pair in data.get("subject_email_duplicates") or []:
        sim = float(pair.get("subject_similarity") or pair.get("similarity") or 0)
        if sim < 1.0:
            continue
        email = (pair.get("shared_email") or pair.get("email") or "").lower()
        if "fedcerts" in email or "fedins.com" in email or "csr24" in email:
            continue
        primary = pair.get("recommended_primary") or {}
        other = pair.get("merge_candidate") or pair.get("other") or {}
        key = frozenset([primary.get("case_number", ""), other.get("case_number", "")])
        if key in seen:
            continue
        seen.add(key)
        out.append((primary, other, f"Identical subject ({sim:.0%})"))
    return out


def render_html(data: dict) -> str:
    generated = esc(data.get("generated", ""))
    scope = esc(data.get("scope", ""))
    merges = high_confidence_pairs(data)

    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>SF Duplicate Scan — Mothman</title>",
        FONT_LINKS,
        f"<style>{THEME_CSS}</style></head><body>",
        "<span class='ember' aria-hidden='true'></span>",
        "<span class='ember' aria-hidden='true'></span>",
        "<span class='ember' aria-hidden='true'></span>",
        "<main class='page-shell'>",
        "<div class='hero'>",
        f"<img src='{BRAND_REL}' alt='Mothman' width='72' height='72'>",
        "<div class='titles'>",
        "<h1>SF <span class='ember-text'>Duplicate</span> Scan</h1>",
        f"<p class='meta'>Generated {generated} · {scope}</p>",
        "</div></div>",
        "<h2>Summary</h2><div class='card'><div class='stats'>",
        stat_card("Total Cases", data.get("total_cases", 0)),
        stat_card("Open", data.get("open_total", 0)),
        stat_card("COI Req dupes", data.get("coi_dupe_groups", 0), "ok"),
        stat_card("Phone dupes", data.get("phone_groups", 0)),
        stat_card("Subject+email pairs", data.get("subject_email_pairs", 0)),
        stat_card("Shell Account (open)", data.get("shell_open_count", 0), "warn"),
        "</div></div>",
    ]

    if merges:
        rows = []
        for primary, other, reason in merges:
            rows.append(
                [
                    f"<span class='tag ok'>High</span>",
                    case_link(primary),
                    case_link(other),
                    esc((primary.get("subject") or "")[:70]),
                    esc(reason),
                ]
            )
        parts.append("<h2>High-confidence merge candidates</h2><div class='card'>")
        parts.append(
            render_table(
                ["Confidence", "Primary", "Close", "Subject", "Reason"],
                rows,
            )
        )
        parts.append("</div>")

    phone_rows = []
    for group in data.get("phone_duplicates") or []:
        primary = group.get("recommended_primary") or {}
        others = ", ".join(
            case_link(o) for o in (group.get("merge_candidates") or group.get("others") or [])
        )
        phone_rows.append(
            [
                esc(group.get("phone")),
                esc(group.get("case_count")),
                case_link(primary),
                others,
            ]
        )
    if phone_rows:
        parts.append("<h2>Voicemail phone duplicates</h2><div class='card'>")
        parts.append(
            render_table(["Phone", "Cases", "Primary", "Others"], phone_rows, {1})
        )
        parts.append("</div>")

    subject_rows = []
    for pair in data.get("subject_email_duplicates") or []:
        primary = pair.get("recommended_primary") or {}
        other = pair.get("merge_candidate") or pair.get("other") or {}
        sim = float(pair.get("subject_similarity") or pair.get("similarity") or 0)
        email = pair.get("shared_email") or pair.get("email") or ""
        subject_rows.append(
            [
                esc(email),
                esc(f"{sim:.2f}"),
                case_link(primary),
                case_link(other),
                esc((primary.get("subject") or "")[:55]),
            ]
        )
    if subject_rows:
        parts.append("<h2>Subject + email likely duplicates</h2><div class='card'>")
        parts.append(
            render_table(
                ["Email", "Similarity", "Primary", "Other", "Subject"],
                subject_rows,
                {1},
            )
        )
        extra = len(data.get("subject_email_duplicates") or []) - len(subject_rows)
        if extra > 0:
            parts.append(f"<p class='muted'>… and {extra} more pairs in JSON.</p>")
        parts.append(
            "<p class='warn-box'>Federated batch-sender pairs are contact collisions — "
            "do not merge unless same Req id / same thread.</p>"
        )
        parts.append("</div>")

    shell = data.get("shell_open") or []
    if shell:
        shell_rows = []
        for case in shell[:30]:
            shell_rows.append(
                [
                    case_link(case),
                    esc(case.get("status")),
                    esc((case.get("created_date") or "")[:10]),
                    esc((case.get("subject") or "")[:65]),
                ]
            )
        parts.append("<h2>Shell Account blockers</h2><div class='card'>")
        parts.append(
            "<p class='warn-box'>Fix Account before merge/close decisions.</p>"
        )
        parts.append(
            render_table(["Case", "Status", "Created", "Subject"], shell_rows)
        )
        if len(shell) > 30:
            parts.append(f"<p class='muted'>… and {len(shell) - 30} more in JSON.</p>")
        parts.append("</div>")

    parts.append(
        "<p class='footer'>Mothman · SF intra-duplicate scan · report only — no merges applied</p>"
    )
    parts.append("</main></body></html>")
    return "".join(parts)


def main() -> int:
    scan_path = Path(__file__).resolve().parent / "sf-intra-duplicate-scan-20260729.json"
    out_path = scan_path.with_suffix(".html")
    if len(sys.argv) > 1:
        scan_path = Path(sys.argv[1])
        out_path = scan_path.with_suffix(".html")
    data = json.loads(scan_path.read_text(encoding="utf-8"))
    out_path.write_text(render_html(data), encoding="utf-8")
    resolved = out_path.resolve()
    print(resolved)
    webbrowser.open(resolved.as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
