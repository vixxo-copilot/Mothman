#!/usr/bin/env python3
"""Analyze full SF window export for Federated COI Req-id duplicates."""
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import scan_duplicates as sd  # noqa: E402

OPEN = {"new", "working", "open", "pending", "escalated", "on hold"}
SHELL = "Service Provider Support Shell Account"


def main() -> int:
    cache = Path(__file__).resolve().parent / "sf-cases-federated-coi-20260701.json"
    records = json.loads(cache.read_text(encoding="utf-8"))["records"]
    by_req: dict[tuple[str, str], list[dict]] = defaultdict(list)

    for c in records:
        f = sd.extract_federated_coi_fields(c.get("Subject") or "")
        k = sd.coi_req_key(f)
        if not k:
            continue
        acct = c.get("Account")
        account_name = acct.get("Name") if isinstance(acct, dict) else None
        by_req[k].append(
            {
                "case_number": c.get("CaseNumber"),
                "status": c.get("Status"),
                "account": account_name,
                "created": (c.get("CreatedDate") or "")[:10],
                "provider": f["provider"] if f else None,
                "subject": c.get("Subject"),
            }
        )

    dupes = {k: v for k, v in by_req.items() if len(v) > 1}
    lines = [
        "# Salesforce Federated COI Duplicate Report (YTD 2026)",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Source:** `sf-cases-federated-coi-20260701.json` ({len(records)} Cases, Federated `Certificate Of Insurance - … Req …` YTD 2026)",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|------:|",
        f"| SF Cases in window | {len(records)} |",
        f"| Parsed Federated COI (Req id) | {sum(len(v) for v in by_req.values())} |",
        f"| Unique Req keys | {len(by_req)} |",
        f"| Req keys with duplicates | {len(dupes)} |",
        f"| Excess Cases (merge/close candidates) | {sum(len(v) - 1 for v in dupes.values())} |",
        "",
    ]

    if dupes:
        lines.extend(
            [
                "## Duplicate groups — same `(policy_id, Req id)`",
                "",
                "| Provider | Req key | Cases | Open | Recommended primary | Merge/close |",
                "|----------|---------|------:|-----:|---------------------|-------------|",
            ]
        )
        for k, cases in sorted(dupes.items(), key=lambda x: (x[0][0], int(x[0][1]))):
            cases.sort(key=lambda x: x.get("created") or "")
            open_cases = [c for c in cases if (c.get("status") or "").lower() in OPEN]
            primary = open_cases[0] if open_cases else cases[0]
            merge = [c["case_number"] for c in cases if c["case_number"] != primary["case_number"]]
            req_label = f"{k[0]} Req {k[1]}"
            lines.append(
                f"| {cases[0]['provider']} | `{req_label}` | {len(cases)} | "
                f"{len(open_cases)} | **{primary['case_number']}** ({primary['status']}) | "
                f"{', '.join(merge)} |"
            )
        lines.append("")
        lines.extend(["## Detail by duplicate group", ""])
        for k, cases in sorted(dupes.items(), key=lambda x: (x[0][0], int(x[0][1]))):
            cases.sort(key=lambda x: x.get("created") or "")
            open_cases = [c for c in cases if (c.get("status") or "").lower() in OPEN]
            primary = open_cases[0] if open_cases else cases[0]
            lines.append(f"### {cases[0]['provider']} — `{k[0]} Req {k[1]}`")
            lines.append("")
            lines.append(f"**Primary:** {primary['case_number']} ({primary['status']}, {primary['account']})")
            lines.append("")
            lines.append("| Case | Status | Account | Created | Subject |")
            lines.append("|------|--------|---------|---------|---------|")
            for c in cases:
                mark = " **← primary**" if c["case_number"] == primary["case_number"] else ""
                shell = " ⚠" if c.get("account") == SHELL else ""
                subj = (c.get("subject") or "")[:55]
                lines.append(
                    f"| {c['case_number']}{mark}{shell} | {c['status']} | "
                    f"{c.get('account') or '—'} | {c['created']} | {subj} |"
                )
            lines.append("")

    out = Path(__file__).resolve().parent / "sf-federated-coi-duplicate-report-full-20260701.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Parsed: {sum(len(v) for v in by_req.values())}, dup groups: {len(dupes)}")
    print(f"REPORT: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
