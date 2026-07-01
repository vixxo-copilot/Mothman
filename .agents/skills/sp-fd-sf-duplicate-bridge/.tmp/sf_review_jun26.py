#!/usr/bin/env python3
"""SF Case review export — CreatedDate >= 2026-06-26."""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import scan_duplicates as sd  # noqa: E402

OPEN = {"new", "working", "open", "pending", "escalated", "on hold", "compliance in progress"}
SHELL = "Service Provider Support Shell Account"
CACHE = Path(__file__).resolve().parent / "sf-cases-window-jun26-20260701.json"
OUT_JSON = Path(__file__).resolve().parent / "sf-review-jun26-20260701.json"
OUT_MD = Path(__file__).resolve().parent / "sf-review-jun26-20260701.md"


def load_records() -> list[dict]:
    data = json.loads(CACHE.read_text(encoding="utf-8"))
    return data["records"] if isinstance(data, dict) else data


def coi_dupes(records: list[dict]) -> list[dict]:
    by_req: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for c in records:
        fields = sd.extract_federated_coi_fields(c.get("Subject") or "")
        key = sd.coi_req_key(fields)
        if not key:
            continue
        by_req[key].append(c)
    groups = []
    for (policy_id, req_id), cases in sorted(by_req.items(), key=lambda x: (x[0][0], int(x[0][1]))):
        if len(cases) <= 1:
            continue
        cases.sort(key=lambda x: x.get("CreatedDate") or "")
        open_cases = [c for c in cases if (c.get("Status") or "").lower() in OPEN]
        primary = open_cases[0] if open_cases else cases[0]
        fields = sd.extract_federated_coi_fields(primary.get("Subject") or "")
        groups.append(
            {
                "policy_id": policy_id,
                "req_id": req_id,
                "provider": fields["provider"] if fields else None,
                "case_count": len(cases),
                "open_count": len(open_cases),
                "primary": {
                    "CaseNumber": primary.get("CaseNumber"),
                    "Status": primary.get("Status"),
                    "Account": (primary.get("Account") or {}).get("Name"),
                    "Owner": (primary.get("Owner") or {}).get("Name"),
                },
                "cases": [
                    {
                        "CaseNumber": c.get("CaseNumber"),
                        "Status": c.get("Status"),
                        "Account": (c.get("Account") or {}).get("Name"),
                        "Owner": (c.get("Owner") or {}).get("Name"),
                        "CreatedDate": c.get("CreatedDate"),
                        "Subject": (c.get("Subject") or "")[:80],
                        "is_primary": c.get("CaseNumber") == primary.get("CaseNumber"),
                        "shell_account": (c.get("Account") or {}).get("Name") == SHELL,
                    }
                    for c in cases
                ],
            }
        )
    return groups


def fd_cross_ref(records: list[dict]) -> list[dict]:
    out = []
    for c in records:
        desc = (c.get("Description") or "") + " " + (c.get("Subject") or "")
        m = sd.FD_TICKET_RE.search(desc)
        if m:
            out.append({"CaseNumber": c.get("CaseNumber"), "fd_ticket": m.group(1), "Subject": c.get("Subject")})
    return out


def shell_cases(records: list[dict]) -> list[dict]:
    return [
        {
            "CaseNumber": c.get("CaseNumber"),
            "Status": c.get("Status"),
            "Owner": (c.get("Owner") or {}).get("Name"),
            "Subject": (c.get("Subject") or "")[:70],
            "CreatedDate": (c.get("CreatedDate") or "")[:10],
        }
        for c in records
        if (c.get("Account") or {}).get("Name") == SHELL and (c.get("Status") or "").lower() in OPEN
    ]


def coi_cases(records: list[dict]) -> list[dict]:
    out = []
    for c in records:
        if sd.extract_federated_coi_fields(c.get("Subject") or ""):
            out.append(c)
    return out


def write_md(result: dict, path: Path) -> None:
    lines = [
        "# Salesforce Case Review — Created ≥ 2026-06-26",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Source:** live SOQL (`CreatedDate >= 2026-06-26T00:00:00Z`)",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|------:|",
        f"| Total Cases | {result['total']} |",
        f"| Open (actionable) | {result['open_total']} |",
        f"| Federated COI (Req id parsed) | {result['coi_count']} |",
        f"| COI duplicate Req groups | {result['coi_dupe_groups']} |",
        f"| Excess COI Cases (merge candidates) | {result['coi_excess']} |",
        f"| Open on Shell Account | {result['shell_open_count']} |",
        f"| FD cross-ref in Description | {result['fd_xref_count']} |",
        "",
        "### By RecordType",
        "",
        "| RecordType | Count | Open |",
        "|------------|------:|-----:|",
    ]
    for rt, cnt in result["by_record_type"]:
        lines.append(f"| {rt} | {cnt} | {result['open_by_rt'].get(rt, 0)} |")

    lines.extend(["", "### By Status", "", "| Status | Count |", "|--------|------:|"])
    for st, cnt in result["by_status"]:
        lines.append(f"| {st} | {cnt} |")

    if result["coi_duplicates"]:
        lines.extend(
            [
                "",
                "## Federated COI — intra-SF duplicates (same policy + Req id)",
                "",
                "Consolidate to **primary**; close/archive others.",
                "",
                "| Provider | Req key | Cases | Open | Primary | Merge/close |",
                "|----------|---------|------:|-----:|---------|-------------|",
            ]
        )
        for g in result["coi_duplicates"]:
            merge = ", ".join(
                c["CaseNumber"] for c in g["cases"] if not c["is_primary"]
            )
            p = g["primary"]
            lines.append(
                f"| {g['provider']} | `{g['policy_id']} Req {g['req_id']}` | "
                f"{g['case_count']} | {g['open_count']} | **{p['CaseNumber']}** ({p['Status']}) | {merge} |"
            )
        lines.append("")
        for g in result["coi_duplicates"]:
            lines.append(f"### {g['provider']} — Req {g['req_id']}")
            lines.append("")
            lines.append("| Case | Status | Account | Owner | Created | Subject |")
            lines.append("|------|--------|---------|-------|---------|---------|")
            for c in g["cases"]:
                flags = []
                if c["is_primary"]:
                    flags.append("primary")
                if c["shell_account"]:
                    flags.append("shell ⚠")
                flag = f" ({', '.join(flags)})" if flags else ""
                lines.append(
                    f"| {c['CaseNumber']}{flag} | {c['Status']} | {c['Account']} | "
                    f"{c['Owner']} | {c['CreatedDate'][:10]} | {c['Subject']} |"
                )
            lines.append("")

    if result["shell_open"]:
        lines.extend(
            [
                "## Open Cases on Shell Account (fix Account)",
                "",
                "| Case | Status | Owner | Created | Subject |",
                "|------|--------|-------|---------|---------|",
            ]
        )
        for c in result["shell_open"]:
            lines.append(
                f"| {c['CaseNumber']} | {c['Status']} | {c['Owner']} | {c['CreatedDate']} | {c['Subject']} |"
            )
        lines.append("")

    if result["fd_xrefs"]:
        lines.extend(
            [
                "## Freshdesk cross-refs (Description contains Freshdesk #)",
                "",
                "| SF Case | FD ticket | Subject |",
                "|---------|-----------|---------|",
            ]
        )
        for x in result["fd_xrefs"]:
            lines.append(f"| {x['CaseNumber']} | #{x['fd_ticket']} | {(x['Subject'] or '')[:60]} |")
        lines.append("")

    lines.extend(
        [
            "## All open Federated COI Cases (single + duplicate)",
            "",
            "| Case | Status | Account | Owner | Req | Provider |",
            "|------|--------|---------|-------|-----|----------|",
        ]
    )
    for c in result["open_coi_list"]:
        lines.append(
            f"| {c['CaseNumber']} | {c['Status']} | {c['Account']} | {c['Owner']} | "
            f"Req {c['req_id']} | {c['provider']} |"
        )

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    records = load_records()
    coi = coi_cases(records)
    dupes = coi_dupes(records)
    shell = shell_cases(records)
    xrefs = fd_cross_ref(records)

    open_records = [r for r in records if (r.get("Status") or "").lower() in OPEN]
    rt_counter = Counter((r.get("RecordType") or {}).get("Name", "?") for r in records)
    st_counter = Counter(r.get("Status") for r in records)
    open_rt = Counter((r.get("RecordType") or {}).get("Name", "?") for r in open_records)

    open_coi_list = []
    for c in coi:
        if (c.get("Status") or "").lower() not in OPEN:
            continue
        f = sd.extract_federated_coi_fields(c.get("Subject") or "")
        open_coi_list.append(
            {
                "CaseNumber": c.get("CaseNumber"),
                "Status": c.get("Status"),
                "Account": (c.get("Account") or {}).get("Name"),
                "Owner": (c.get("Owner") or {}).get("Name"),
                "req_id": f["req_id"] if f else "?",
                "provider": f["provider"] if f else "?",
            }
        )
    open_coi_list.sort(key=lambda x: (x["provider"] or "", x["req_id"]))

    result = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "window_start": "2026-06-26T00:00:00Z",
        "total": len(records),
        "open_total": len(open_records),
        "coi_count": len(coi),
        "coi_dupe_groups": len(dupes),
        "coi_excess": sum(g["case_count"] - 1 for g in dupes),
        "shell_open_count": len(shell),
        "fd_xref_count": len(xrefs),
        "by_record_type": rt_counter.most_common(),
        "by_status": st_counter.most_common(),
        "open_by_rt": dict(open_rt),
        "coi_duplicates": dupes,
        "shell_open": shell,
        "fd_xrefs": xrefs,
        "open_coi_list": open_coi_list,
    }
    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_md(result, OUT_MD)
    print(json.dumps({k: v for k, v in result.items() if k not in ("coi_duplicates", "shell_open", "fd_xrefs", "open_coi_list")}, indent=2))
    print(f"REPORT: {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
