#!/usr/bin/env python3
"""Analyze SF Case export for Federated COI Req-id duplicate groups."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Allow import from sibling scripts/
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import scan_duplicates as sd  # noqa: E402

OPEN_STATUSES = {"new", "working", "open", "pending", "escalated", "on hold"}
SHELL = "Service Provider Support Shell Account"


def load_records(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "records" in data:
        return data["records"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Unexpected JSON shape: {path}")


def fmt_dt(s: str | None) -> str:
    if not s:
        return "—"
    try:
        return s[:10]
    except Exception:
        return s


def analyze(records: list[dict]) -> dict:
    by_req: dict[tuple[str, str], list[dict]] = defaultdict(list)
    unparsed: list[dict] = []

    for c in records:
        fields = sd.extract_federated_coi_fields(c.get("Subject") or "")
        key = sd.coi_req_key(fields)
        entry = {
            "case_number": c.get("CaseNumber"),
            "id": c.get("Id"),
            "subject": c.get("Subject"),
            "status": c.get("Status"),
            "account": (c.get("Account") or {}).get("Name"),
            "created": c.get("CreatedDate"),
            "owner": (c.get("Owner") or {}).get("Username"),
            "provider": fields["provider"] if fields else None,
            "policy_id": fields["policy_id"] if fields else None,
            "req_id": fields["req_id"] if fields else None,
        }
        if key:
            by_req[key].append(entry)
        else:
            unparsed.append(entry)

    dup_groups = []
    for (policy_id, req_id), cases in sorted(
        by_req.items(), key=lambda x: (x[0][0], int(x[0][1]))
    ):
        if len(cases) <= 1:
            continue
        cases.sort(key=lambda x: x.get("created") or "")
        open_cases = [
            c for c in cases if (c.get("status") or "").lower() in OPEN_STATUSES
        ]
        shell_cases = [c for c in cases if c.get("account") == SHELL]
        dup_groups.append(
            {
                "policy_id": policy_id,
                "req_id": req_id,
                "provider": cases[0].get("provider"),
                "case_count": len(cases),
                "open_count": len(open_cases),
                "shell_count": len(shell_cases),
                "cases": cases,
                "recommended_primary": open_cases[0] if open_cases else cases[0],
                "merge_candidates": [
                    c for c in cases if c != (open_cases[0] if open_cases else cases[0])
                ],
            }
        )

    singles = sum(1 for v in by_req.values() if len(v) == 1)
    return {
        "total_cases": len(records),
        "parsed_federated": sum(len(v) for v in by_req.values()),
        "unique_req_keys": len(by_req),
        "single_case_req_keys": singles,
        "duplicate_req_groups": dup_groups,
        "duplicate_group_count": len(dup_groups),
        "duplicate_case_count": sum(g["case_count"] for g in dup_groups),
        "excess_cases": sum(g["case_count"] - 1 for g in dup_groups),
        "unparsed_subjects": unparsed,
    }


def write_markdown(result: dict, path: Path, title: str) -> None:
    lines = [
        f"# {title}",
        "",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|------:|",
        f"| Total SF Cases in export | {result['total_cases']} |",
        f"| Parsed Federated COI (Req id) | {result['parsed_federated']} |",
        f"| Unique Req keys | {result['unique_req_keys']} |",
        f"| Req keys with duplicates | {result['duplicate_group_count']} |",
        f"| Excess Cases (could merge/close) | {result['excess_cases']} |",
        "",
    ]

    if result["duplicate_req_groups"]:
        lines.extend(
            [
                "## Duplicate groups — same `(policy_id, Req id)`",
                "",
                "Each row is one Federated request that spawned multiple SF Cases.",
                "Prefer the **recommended primary** (oldest open); close or merge others.",
                "",
            ]
        )
        for g in result["duplicate_req_groups"]:
            primary = g["recommended_primary"]
            lines.append(
                f"### {g['provider']} — `{g['policy_id']} Req {g['req_id']}` "
                f"({g['case_count']} Cases, {g['open_count']} open)"
            )
            lines.append("")
            lines.append(
                f"**Recommended primary:** {primary['case_number']} "
                f"({primary['status']}, {primary['account']}, {fmt_dt(primary['created'])})"
            )
            lines.append("")
            lines.append("| Case | Status | Account | Created | Owner | Subject |")
            lines.append("|------|--------|---------|---------|-------|---------|")
            for c in g["cases"]:
                subj = (c.get("subject") or "")[:55]
                mark = " **← primary**" if c["case_number"] == primary["case_number"] else ""
                shell = " ⚠ shell" if c.get("account") == SHELL else ""
                lines.append(
                    f"| {c['case_number']}{mark}{shell} | {c['status']} | "
                    f"{c.get('account') or '—'} | {fmt_dt(c['created'])} | "
                    f"{(c.get('owner') or '').split('@')[0]} | {subj} |"
                )
            lines.append("")

    # Angeles Plumbing spotlight
    ap_groups = [
        g
        for g in result["duplicate_req_groups"]
        if g.get("provider") and "angeles plumbing" in g["provider"].lower()
    ]
    ap_singles = [
        (k, v)
        for k, v in [
            (g["policy_id"], g)
            for g in result["duplicate_req_groups"]
            if g.get("provider") and "angeles plumbing" in g["provider"].lower()
        ]
    ]
    lines.extend(["## Angeles Plumbing LLC spotlight", ""])
    if ap_groups:
        for g in ap_groups:
            lines.append(
                f"- **Req {g['req_id']}:** {g['case_count']} SF Cases "
                f"({g['open_count']} open) — primary **{g['recommended_primary']['case_number']}**"
            )
    else:
        lines.append("No duplicate Req-id groups in export (each Req has one SF Case).")
    lines.append("")
    lines.append(
        "Angeles Plumbing Cases in export (all Req ids): see duplicate table above "
        "and FD↔SF scan report."
    )
    lines.append("")

    if result["unparsed_subjects"]:
        lines.extend(
            [
                f"## Unparsed COI subjects ({len(result['unparsed_subjects'])})",
                "",
                "Non-Federated pattern or missing Req id — not grouped.",
                "",
            ]
        )
        for c in result["unparsed_subjects"][:15]:
            lines.append(
                f"- {c['case_number']} — {(c.get('subject') or '')[:70]}"
            )
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    cache = Path(__file__).resolve().parent / "sf-cases-federated-coi-20260701.json"
    if not cache.is_file():
        print(f"Missing cache: {cache}", file=sys.stderr)
        return 1
    records = load_records(cache)
    result = analyze(records)
    out_json = cache.with_suffix(".dup-analysis.json")
    out_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    out_md = Path(__file__).resolve().parent / "sf-federated-coi-duplicate-report-20260701.md"
    write_markdown(
        result,
        out_md,
        "Salesforce Federated COI Duplicate Report",
    )
    print(json.dumps({k: result[k] for k in result if k not in ("duplicate_req_groups", "unparsed_subjects")}, indent=2))
    print(f"REPORT: {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
