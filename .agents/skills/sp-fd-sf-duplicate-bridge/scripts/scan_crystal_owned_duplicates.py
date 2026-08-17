#!/usr/bin/env python3
"""Duplicate review seeded from Crystal-owned open Cases only.

Shows each of Crystal's Cases that has an open duplicate sibling
(owned by anyone, including Crystal). Does not list org-wide clusters
where Crystal is not an owner of at least one member.

Morning cascade (after case window export):

  python .agents/skills/sp-fd-sf-duplicate-bridge/scripts/scan_crystal_owned_duplicates.py \\
    --sf-cache .agents/skills/sp-fd-sf-duplicate-bridge/.tmp/sf-cases-window-crystal-queue-YYYYMMDD.json \\
    --open
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SKILL_TMP = SCRIPTS.parent / ".tmp"
sys.path.insert(0, str(SCRIPTS))

import scan_sf_duplicates as scan  # noqa: E402
from render_sf_duplicate_report_html import (  # noqa: E402
    BRAND_REL,
    FONT_LINKS,
    THEME_CSS,
    case_link,
    esc,
    open_html_in_chrome,
)
from sf_cli import sf_query  # noqa: E402

DEFAULT_OWNER_ID = "005TS000009gWazYAE"
DEFAULT_OWNER_NAME = "Crystal Gagner"

SHELL_ACCOUNT_NAMES = {
    "vixxo corporation",
    "service provider support shell account",
    "shell account",
}


def is_mine(c: dict, owner_id: str, owner_name: str) -> bool:
    own = c.get("Owner") or {}
    return own.get("Id") == owner_id or own.get("Name") == owner_name


def summary_is_mine(s: dict, owner_name: str) -> bool:
    return (s.get("owner") or "") == owner_name or (
        s.get("owner_username") or ""
    ).lower().startswith("crystal.gagner")


def pick_group_primary(members: list[dict], owner_name: str) -> dict:
    """Prefer Crystal-owned Working, then oldest Crystal open, else oldest."""
    mine = [c for c in members if summary_is_mine(c, owner_name)]
    pool = mine or members
    working = [c for c in pool if (c.get("status") or "").lower() == "working"]
    pool = working or pool
    return sorted(pool, key=lambda c: c.get("created_date") or "")[0]


def _is_shell_account(name: str | None) -> bool:
    return (name or "").strip().lower() in SHELL_ACCOUNT_NAMES


def pick_group_sp(members: list[dict]) -> tuple[str, str]:
    scored: list[tuple[int, str, str]] = []
    for c in members:
        name = (c.get("sp_name") or c.get("account") or "").strip()
        num = (c.get("sp_number") or "").strip()
        if not name and not num:
            continue
        score = 0
        if num:
            score += 4
        if name and not _is_shell_account(name):
            score += 2
        if name:
            score += 1
        scored.append((score, name, num))
    if not scored:
        return ("", "")
    scored.sort(key=lambda x: (-x[0], x[1], x[2]))
    _, name, num = scored[0]
    return (name, num)


def enrich_rows_with_sp(rows: list[dict]) -> None:
    ids: list[str] = []
    for r in rows:
        for c in [r.get("yours"), *(r.get("others") or []), r.get("other")]:
            if c and c.get("id"):
                ids.append(c["id"])
    ids = sorted(set(ids))
    by_id: dict[str, dict] = {}
    chunk = 80
    for i in range(0, len(ids), chunk):
        batch = ids[i : i + chunk]
        id_list = ",".join(f"'{x}'" for x in batch)
        soql = (
            "SELECT Id, CaseNumber, Account.Name, Account.Service_Provider_Number__c "
            f"FROM Case WHERE Id IN ({id_list})"
        )
        for rec in sf_query(soql):
            acct = rec.get("Account") or {}
            by_id[rec["Id"]] = {
                "sp_name": acct.get("Name") or "",
                "sp_number": acct.get("Service_Provider_Number__c") or "",
                "account": acct.get("Name") or "",
            }

    def apply(c: dict | None) -> None:
        if not c:
            return
        info = by_id.get(c.get("id") or "")
        if not info:
            c.setdefault("sp_name", c.get("account") or "")
            c.setdefault("sp_number", "")
            return
        c["sp_name"] = info["sp_name"]
        c["sp_number"] = info["sp_number"]
        if info["account"]:
            c["account"] = info["account"]

    for r in rows:
        apply(r.get("yours"))
        apply(r.get("other"))
        for c in r.get("others") or []:
            apply(c)
        members = [r.get("yours"), *(r.get("others") or [])]
        if r.get("other"):
            members.append(r["other"])
        members = [m for m in members if m]
        sp_name, sp_number = pick_group_sp(members)
        r["sp_name"] = sp_name
        r["sp_number"] = sp_number


def collapse_subject_email_pairs(
    pairs: list[dict], owner_name: str
) -> list[dict]:
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    by_num: dict[str, dict] = {}
    edge_meta: list[dict] = []
    for p in pairs:
        a = p.get("recommended_primary") or {}
        b = p.get("merge_candidate") or {}
        if not (summary_is_mine(a, owner_name) or summary_is_mine(b, owner_name)):
            continue
        an, bn = a.get("case_number"), b.get("case_number")
        if not an or not bn:
            continue
        by_num[an] = a
        by_num[bn] = b
        union(an, bn)
        edge_meta.append(p)

    groups: dict[str, set[str]] = defaultdict(set)
    for cn in by_num:
        groups[find(cn)].add(cn)

    rows: list[dict] = []
    for members_nums in groups.values():
        members = [by_num[n] for n in members_nums]
        primary = pick_group_primary(members, owner_name)
        peers = [
            c for c in members if c.get("case_number") != primary.get("case_number")
        ]
        if not peers:
            continue
        sims = [
            float(p.get("subject_similarity") or 0)
            for p in edge_meta
            if (p.get("recommended_primary") or {}).get("case_number") in members_nums
            and (p.get("merge_candidate") or {}).get("case_number") in members_nums
        ]
        emails = {
            p.get("shared_email")
            for p in edge_meta
            if (p.get("recommended_primary") or {}).get("case_number") in members_nums
            and (p.get("merge_candidate") or {}).get("case_number") in members_nums
            and p.get("shared_email")
        }
        rows.append(
            {
                "signal": "subject_email",
                "similarity": max(sims) if sims else None,
                "shared_email": ", ".join(sorted(emails)),
                "yours": primary,
                "others": peers,
                "other_is_external": any(
                    not summary_is_mine(c, owner_name) for c in peers
                ),
                "peer_count": len(peers),
            }
        )
    return rows


def build_seeded_pairs(
    records: list[dict],
    *,
    sf_cache: Path,
    owner_id: str,
    owner_name: str,
) -> dict:
    mine_open = [
        r
        for r in records
        if is_mine(r, owner_id, owner_name) and scan.is_open_status(r.get("Status"))
    ]

    full = scan.build_scan_result(
        records,
        sf_cache=str(sf_cache),
        scope=(
            f"Seeded from Crystal open Cases ({len(mine_open)}); "
            "duplicates may be owned by others; one row per duplicate group"
        ),
        open_only=True,
    )

    rows: list[dict] = []
    rows.extend(
        collapse_subject_email_pairs(
            full.get("subject_email_duplicates") or [], owner_name
        )
    )

    for g in full.get("phone_duplicates") or []:
        phone = scan.norm_phone(str(g.get("phone") or ""))
        if phone and phone in scan.IGNORE_CLUSTER_PHONES:
            continue
        cases = g.get("cases") or []
        mine_members = [c for c in cases if summary_is_mine(c, owner_name)]
        if not mine_members:
            continue
        primary = pick_group_primary(cases, owner_name)
        if not summary_is_mine(primary, owner_name) and mine_members:
            primary = pick_group_primary(mine_members, owner_name)
        peers = [c for c in cases if c.get("id") != primary.get("id")]
        if not peers:
            continue
        rows.append(
            {
                "signal": "voicemail_phone",
                "phone": g.get("phone"),
                "company": g.get("company"),
                "yours": primary,
                "others": peers,
                "other_is_external": any(
                    not summary_is_mine(c, owner_name) for c in peers
                ),
                "peer_count": len(peers),
            }
        )

    for g in full.get("coi_duplicates") or []:
        cases = g.get("cases") or []
        mine_members = [c for c in cases if summary_is_mine(c, owner_name)]
        if not mine_members:
            continue
        primary = pick_group_primary(mine_members, owner_name)
        peers = [c for c in cases if c.get("id") != primary.get("id")]
        if not peers:
            continue
        rows.append(
            {
                "signal": "coi_req",
                "yours": primary,
                "others": peers,
                "other_is_external": any(
                    not summary_is_mine(c, owner_name) for c in peers
                ),
                "peer_count": len(peers),
            }
        )

    seen: dict[tuple, dict] = {}
    deduped: list[dict] = []
    for r in rows:
        members = [(r.get("yours") or {}).get("case_number")]
        if r.get("others"):
            members.extend(c.get("case_number") for c in r["others"])
        elif r.get("other"):
            members.append((r.get("other") or {}).get("case_number"))
        key = (r["signal"], tuple(sorted(m for m in members if m)))
        if key in seen:
            prev = seen[key]
            phones = {p for p in (prev.get("phone"), r.get("phone")) if p}
            if phones:
                prev["phone"] = ", ".join(sorted(phones))
            emails = {
                e.strip()
                for e in (
                    (prev.get("shared_email") or "").split(",")
                    + (r.get("shared_email") or "").split(",")
                )
                if e.strip()
            }
            if emails:
                prev["shared_email"] = ", ".join(sorted(emails))
            continue
        seen[key] = r
        deduped.append(r)

    def sort_key(r: dict):
        ext = 0 if r.get("other_is_external") else 1
        sim = -(float(r.get("similarity") or 0))
        cn = (r.get("yours") or {}).get("case_number") or ""
        return (ext, 0 if r["signal"] == "subject_email" else 1, sim, cn)

    deduped.sort(key=sort_key)
    enrich_rows_with_sp(deduped)

    crystal_case_nums = sorted(
        {
            (r.get("yours") or {}).get("case_number")
            for r in deduped
            if summary_is_mine(r.get("yours") or {}, owner_name)
        }
        | {
            c.get("case_number")
            for r in deduped
            for c in (r.get("others") or [])
            if summary_is_mine(c, owner_name)
        }
    )

    return {
        "scan": "sf-intra-duplicates-crystal-owned-seed",
        "generated": datetime.now(timezone.utc).isoformat(),
        "sf_cache": str(sf_cache),
        "scope": (
            f"Crystal Gagner open Cases only as seed ({len(mine_open)}); "
            "one row per duplicate group; voicemail clusters use transcript "
            "caller/SP (not forwarded AP/Vixxo phones)"
        ),
        "crystal_open_cases": len(mine_open),
        "crystal_cases_with_duplicates": len(crystal_case_nums),
        "duplicate_rows": len(deduped),
        "with_external_owner": sum(1 for r in deduped if r.get("other_is_external")),
        "subject_email_rows": sum(1 for r in deduped if r["signal"] == "subject_email"),
        "phone_rows": sum(1 for r in deduped if r["signal"] == "voicemail_phone"),
        "coi_rows": sum(1 for r in deduped if r["signal"] == "coi_req"),
        "crystal_case_numbers": crystal_case_nums,
        "rows": deduped,
        "crystal_open_summaries": [scan.case_summary(r) for r in mine_open],
    }


def render_md(data: dict) -> str:
    lines = [
        "# SF Duplicate Review — Your Cases (seeded)",
        "",
        f"**Generated:** {data['generated'][:16].replace('T', ' ')} UTC",
        f"**Scope:** {data['scope']}",
        "",
        "## Summary",
        "",
        f"| Your open Cases | {data['crystal_open_cases']} |",
        f"| Your Cases with ≥1 open duplicate | {data['crystal_cases_with_duplicates']} |",
        f"| Duplicate groups (1 row each) | {data['duplicate_rows']} |",
        f"| Groups with other-owner sibling | {data['with_external_owner']} |",
        f"| Subject+email | {data['subject_email_rows']} |",
        f"| Voicemail phone | {data['phone_rows']} |",
        f"| COI Req | {data['coi_rows']} |",
        "",
        "## Duplicate groups",
        "",
        "| Primary (yours) | Status | SP Name | SP # | Subject | Signal | Matches | Notes |",
        "|-----------------|--------|---------|------|---------|--------|---------|-------|",
    ]
    for r in data["rows"]:
        yours = r["yours"]
        others = r.get("others") or ([r["other"]] if r.get("other") else [])
        peer_bits = "; ".join(
            f"{c.get('case_number')} — {c.get('owner')} ({c.get('status')})"
            for c in others
        )
        notes = []
        if r.get("similarity") is not None:
            notes.append(f"sim={r.get('similarity')}")
        if r.get("shared_email"):
            notes.append(str(r.get("shared_email")))
        if r.get("company"):
            notes.append(f"sp/company={r.get('company')}")
        if r.get("phone"):
            notes.append(f"callback={r.get('phone')}")
        lines.append(
            f"| **{yours.get('case_number')}** | {yours.get('status')} | "
            f"{r.get('sp_name') or '—'} | {r.get('sp_number') or '—'} | "
            f"{(yours.get('subject') or '')[:50]} | {r['signal']} | "
            f"{peer_bits} | {'; '.join(notes)} |"
        )
    lines.append("")
    lines.append("## Your open Cases in these groups")
    lines.append("")
    for cn in data["crystal_case_numbers"]:
        lines.append(f"- {cn}")
    lines.append("")
    return "\n".join(lines)


def render_seeded_html(data: dict, date_stamp: str) -> str:
    rows_html = []
    for r in data["rows"]:
        yours = r["yours"]
        ylink = case_link(yours)
        others = r.get("others") or ([r["other"]] if r.get("other") else [])
        peers = "<br>".join(
            f"{case_link(c)} — {esc(c.get('owner'))} ({esc(c.get('status'))})"
            for c in others
        )
        ext = "Yes" if r.get("other_is_external") else "No (you)"
        notes = []
        if r.get("similarity") is not None:
            notes.append(f"sim={esc(r.get('similarity'))}")
        if r.get("shared_email"):
            notes.append(esc(r.get("shared_email")))
        if r.get("company"):
            notes.append(esc(f"sp/company={r.get('company')}"))
        if r.get("phone"):
            notes.append(f"callback={esc(r.get('phone'))}")
        notes.append(f"n={len(others)}")
        sp_name = r.get("sp_name") or "—"
        sp_num = r.get("sp_number") or "—"
        rows_html.append(
            "<tr>"
            f"<td>{ylink}</td>"
            f"<td>{esc(yours.get('status'))}</td>"
            f"<td>{esc(sp_name)}</td>"
            f"<td>{esc(sp_num)}</td>"
            f"<td>{esc((yours.get('subject') or '')[:70])}</td>"
            f"<td>{esc(r['signal'])}</td>"
            f"<td>{peers}</td>"
            f"<td>{esc(ext)}</td>"
            f"<td>{'<br>'.join(notes)}</td>"
            "</tr>"
        )

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<title>SF Dupes — Crystal owned seed {esc(date_stamp)}</title>
{FONT_LINKS}
<style>{THEME_CSS}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
th, td {{ border-bottom: 1px solid #e5e0ea; padding: 8px 10px; text-align: left; vertical-align: top; }}
th {{ background: #1a1228; color: #f0e6f6; }}
.cards {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 16px 0; }}
.card {{ background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 12px 16px; min-width: 140px; }}
.card b {{ display: block; font-size: 22px; }}
.muted {{ color: #666; }}
</style></head><body>
<header style="display:flex;gap:16px;align-items:center;margin-bottom:12px">
  <img src="{BRAND_REL}" alt="Mothman" width="56" height="56"/>
  <div>
    <h1 style="margin:0">Duplicate review — your Cases</h1>
    <p class="muted" style="margin:4px 0 0">{esc(data['scope'])}</p>
  </div>
</header>
<div class="cards">
  <div class="card"><span class="muted">Your open</span><b>{data['crystal_open_cases']}</b></div>
  <div class="card"><span class="muted">In dupe groups</span><b>{data['crystal_cases_with_duplicates']}</b></div>
  <div class="card"><span class="muted">Groups (1 row each)</span><b>{data['duplicate_rows']}</b></div>
  <div class="card"><span class="muted">Other-owner sibling</span><b>{data['with_external_owner']}</b></div>
</div>
<table>
<thead><tr>
  <th>Primary</th><th>Status</th><th>SP Name</th><th>SP #</th><th>Subject</th><th>Signal</th>
  <th>Matches</th><th>Other owner?</th><th>Notes</th>
</tr></thead>
<tbody>
{''.join(rows_html)}
</tbody></table>
<p class="muted">Generated {esc(data['generated'])} · report-only (no merges)</p>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="SF duplicate review seeded from Crystal-owned open Cases"
    )
    parser.add_argument(
        "--sf-cache",
        type=Path,
        required=True,
        help="SF Case window JSON (must include Crystal Cases + sibling candidates)",
    )
    parser.add_argument("--owner-id", default=DEFAULT_OWNER_ID)
    parser.add_argument("--owner-name", default=DEFAULT_OWNER_NAME)
    parser.add_argument(
        "--date",
        default=datetime.now(timezone.utc).strftime("%Y%m%d"),
        help="YYYYMMDD stamp for output filenames",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=SKILL_TMP,
        help="Directory for JSON/MD/HTML outputs",
    )
    parser.add_argument("--open", action="store_true", help="Open HTML report")
    args = parser.parse_args()

    if not args.sf_cache.is_file():
        print(f"ERROR: sf-cache not found: {args.sf_cache}", file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = args.date
    out_json = args.output_dir / f"sf-intra-duplicate-scan-crystal-owned-{stamp}.json"
    out_md = args.output_dir / f"sf-intra-duplicate-report-crystal-owned-{stamp}.md"
    out_html = args.output_dir / f"sf-intra-duplicate-scan-crystal-owned-{stamp}.html"

    records = scan.load_records(args.sf_cache)
    data = build_seeded_pairs(
        records,
        sf_cache=args.sf_cache,
        owner_id=args.owner_id,
        owner_name=args.owner_name,
    )
    out_json.write_text(json.dumps(data, indent=2), encoding="utf-8")
    out_md.write_text(render_md(data), encoding="utf-8")
    out_html.write_text(render_seeded_html(data, stamp), encoding="utf-8")

    if args.open:
        os.environ["OPEN_REPORT"] = "1"
        open_html_in_chrome(out_html)

    print(
        json.dumps(
            {
                "crystal_open_cases": data["crystal_open_cases"],
                "crystal_cases_with_duplicates": data["crystal_cases_with_duplicates"],
                "duplicate_rows": data["duplicate_rows"],
                "with_external_owner": data["with_external_owner"],
                "html": str(out_html),
                "md": str(out_md),
                "json": str(out_json),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
