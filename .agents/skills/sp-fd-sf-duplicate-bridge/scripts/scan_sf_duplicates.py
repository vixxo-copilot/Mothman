#!/usr/bin/env python3
"""Scan Salesforce Cases for intra-org duplicates (SF-only review).

Groups Cases by Federated COI Req id and by normalized subject + requester email.
Does not call Freshdesk.

Usage
-----
    python scan_sf_duplicates.py \\
      --sf-cache .tmp/sf-cases-window-coi-20260707.json \\
      --output .tmp/sf-duplicate-scan-20260708.json \\
      --report .tmp/sf-duplicate-report-20260708.md
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from scan_duplicates import (
    extract_federated_coi_fields,
    coi_req_key,
    load_sf_cases,
    norm_email,
)
from sf_merge_primary import enrich_owner_fields, pick_merge_primary

OPEN_STATUSES = {"new", "working", "open", "pending", "escalated", "on hold"}
SHELL_ACCOUNT = "Service Provider Support Shell Account"
SUBJECT_PREFIX_RE = re.compile(r"^(?:re|fw|fwd):\s*", re.I)


def normalize_subject(subject: str | None) -> str:
    s = (subject or "").strip()
    while SUBJECT_PREFIX_RE.match(s):
        s = SUBJECT_PREFIX_RE.sub("", s.strip())
    return re.sub(r"\s+", " ", s).strip().lower()


def case_email(case: dict) -> str | None:
    return norm_email(case.get("ContactEmail")) or norm_email(case.get("SuppliedEmail"))


def _duplicate_group_entry(
    cases: list[dict],
    *,
    dup_type: str,
    extra: dict,
) -> dict:
    primary, review_reason = pick_merge_primary(cases)
    if primary is None and review_reason == "all_closed":
        primary = sorted(cases, key=lambda c: c.get("created_at") or "")[0]
        review_reason = None

    open_cases = [c for c in cases if (c.get("status") or "").lower() in OPEN_STATUSES]
    group = {
        "dup_type": dup_type,
        "case_count": len(cases),
        "open_count": len(open_cases),
        "primary": primary,
        "merge_candidates": [c for c in cases if primary and c["id"] != primary["id"]],
        **extra,
    }
    if review_reason:
        group["manual_review_reason"] = review_reason
        group["manual_review_cases"] = open_cases or cases
    return group


def case_entry(case: dict) -> dict:
    fields = extract_federated_coi_fields(case.get("Subject") or "")
    acct = case.get("Account")
    account_name = acct.get("Name") if isinstance(acct, dict) else None
    owner = case.get("Owner")
    owner_name = owner.get("Username") if isinstance(owner, dict) else None
    owner_type = owner.get("Type") if isinstance(owner, dict) else None
    entry = {
        "id": case.get("Id"),
        "case_number": case.get("CaseNumber"),
        "subject": case.get("Subject") or "",
        "description": case.get("Description") or "",
        "status": case.get("Status") or "",
        "created_at": case.get("CreatedDate"),
        "last_modified_at": case.get("LastModifiedDate"),
        "contact_email": case.get("ContactEmail"),
        "supplied_email": case.get("SuppliedEmail"),
        "account": account_name,
        "owner": owner_name,
        "owner_type": owner_type,
        "provider": fields["provider"] if fields else None,
        "policy_id": fields["policy_id"] if fields else None,
        "req_id": fields["req_id"] if fields else None,
    }
    return enrich_owner_fields(entry, case)


def analyze(records: list[dict]) -> dict:
    entries = [case_entry(c) for c in records]
    by_id = {e["id"]: e for e in entries if e.get("id")}

    fed_groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for e in entries:
        key = coi_req_key(
            extract_federated_coi_fields(e.get("subject") or "")
        )
        if key:
            fed_groups[key].append(e)

    federated_duplicates = []
    federated_case_ids: set[str] = set()
    for (policy_id, req_id), cases in sorted(
        fed_groups.items(), key=lambda x: (x[0][0], int(x[0][1]))
    ):
        if len(cases) <= 1:
            continue
        for c in cases:
            federated_case_ids.add(c["id"])
        federated_duplicates.append(
            _duplicate_group_entry(
                cases,
                dup_type="federated_coi_req_id",
                extra={
                    "provider": cases[0].get("provider") or "—",
                    "policy_id": policy_id,
                    "req_id": req_id,
                },
            )
        )

    subject_groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for e in entries:
        if e["id"] in federated_case_ids:
            continue
        email = case_email(
            {
                "ContactEmail": e.get("contact_email"),
                "SuppliedEmail": e.get("supplied_email"),
            }
        )
        norm_subj = normalize_subject(e.get("subject"))
        if not email or not norm_subj or len(norm_subj) < 8:
            continue
        subject_groups[(norm_subj, email)].append(e)

    subject_duplicates = []
    for (norm_subj, email), cases in sorted(subject_groups.items(), key=lambda x: x[0]):
        if len(cases) <= 1:
            continue
        group = _duplicate_group_entry(
            cases,
            dup_type="subject_email",
            extra={
                "provider": _provider_from_subject(cases[0]["subject"]),
                "subject_key": cases[0]["subject"][:120],
                "requester_email": email,
            },
        )
        if group.get("primary"):
            group["provider"] = group["primary"].get("provider") or group["provider"]
        subject_duplicates.append(group)

    by_provider: dict[str, list[dict]] = defaultdict(list)
    for group in federated_duplicates + subject_duplicates:
        label = group.get("provider") or group.get("requester_email") or "Unknown"
        by_provider[label].append(group)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_cases": len(records),
        "federated_req_group_count": len(fed_groups),
        "federated_duplicate_groups": len(federated_duplicates),
        "subject_duplicate_groups": len(subject_duplicates),
        "excess_federated_cases": sum(g["case_count"] - 1 for g in federated_duplicates),
        "excess_subject_cases": sum(g["case_count"] - 1 for g in subject_duplicates),
        "federated_duplicates": federated_duplicates,
        "subject_duplicates": subject_duplicates,
        "by_provider": dict(sorted(by_provider.items(), key=lambda x: x[0].lower())),
        "case_index": {cid: by_id[cid] for cid in by_id},
    }


def _provider_from_subject(subject: str) -> str:
    m = re.match(r"^ks\s*-\s*(.+?)\s*-\s*", subject, re.I)
    if m:
        return m.group(1).strip()
    if len(subject) <= 80:
        return subject.strip()
    return subject[:77].strip() + "..."


def write_report(result: dict, path: Path, window_note: str) -> None:
    lines = [
        "# Salesforce Duplicate Review (SF-only)",
        "",
        f"**Generated:** {result['generated_at']}",
        window_note,
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|------:|",
        f"| SF Cases in export | {result['total_cases']} |",
        f"| Federated COI Req groups | {result['federated_req_group_count']} |",
        f"| Federated duplicate groups | {result['federated_duplicate_groups']} |",
        f"| Subject+email duplicate groups | {result['subject_duplicate_groups']} |",
        f"| Excess Cases (Federated) | {result['excess_federated_cases']} |",
        f"| Excess Cases (subject+email) | {result['excess_subject_cases']} |",
        "",
        "## One ticket per SP",
        "",
        "| SP / provider | Groups | Primary Case(s) | Merge / close |",
        "|---------------|-------:|-----------------|---------------|",
    ]
    for provider, groups in result["by_provider"].items():
        primaries = ", ".join(
            f"**{g['primary']['case_number']}**"
            if g.get("primary")
            else "— (manual review)"
            for g in groups
        )
        merges = ", ".join(
            c["case_number"]
            for g in groups
            for c in g["merge_candidates"]
        )
        lines.append(
            f"| {provider} | {len(groups)} | {primaries} | {merges or '—'} |"
        )
    lines.append("")

    if result["federated_duplicates"]:
        lines.extend(["## Federated COI — same Req id", ""])
        for g in result["federated_duplicates"]:
            lines.append(
                f"### {g['provider']} — `{g['policy_id']} Req {g['req_id']}` "
                f"({g['case_count']} Cases)"
            )
            lines.append("")
            p = g["primary"]
            if p:
                lines.append(
                    f"**Primary:** {p['case_number']} ({p['status']}, {p.get('account') or '—'})"
                )
            else:
                lines.append(
                    f"**Primary:** — ({g.get('manual_review_reason', 'manual review')})"
                )
            lines.append("")
            if p:
                for c in g["merge_candidates"]:
                    lines.append(
                        f"- Close/merge **{c['case_number']}** ({c['status']}) → {p['case_number']}"
                    )
            else:
                for c in g.get("manual_review_cases") or []:
                    lines.append(f"- **{c['case_number']}** ({c['status']}) — manual review")
            lines.append("")

    if result["subject_duplicates"]:
        lines.extend(["## Same subject + requester email", ""])
        for g in result["subject_duplicates"]:
            lines.append(f"### {g['provider']}")
            lines.append("")
            lines.append(f"**Subject:** {g['subject_key']}")
            p = g["primary"]
            if p:
                lines.append(f"**Primary:** {p['case_number']} ({p['status']})")
            else:
                lines.append(
                    f"**Primary:** — ({g.get('manual_review_reason', 'manual review')})"
                )
            lines.append("")
            if p:
                for c in g["merge_candidates"]:
                    lines.append(f"- **{c['case_number']}** ({c['status']})")
            else:
                for c in g.get("manual_review_cases") or []:
                    lines.append(f"- **{c['case_number']}** ({c['status']}) — manual review")
            lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sf-cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument(
        "--window-note",
        default="",
        help="Optional line for report header (e.g. CreatedDate window)",
    )
    args = parser.parse_args(argv)

    records = load_sf_cases(args.sf_cache)
    result = analyze(records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")

    report_path = args.report or args.output.with_suffix(".md")
    window = args.window_note or f"**Source:** `{args.sf_cache.name}`"
    write_report(result, report_path, window)

    summary = {
        k: result[k]
        for k in result
        if k not in ("federated_duplicates", "subject_duplicates", "by_provider", "case_index")
    }
    print(json.dumps(summary, indent=2))
    print(f"OUTPUT: {args.output.resolve()}")
    print(f"REPORT: {report_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
