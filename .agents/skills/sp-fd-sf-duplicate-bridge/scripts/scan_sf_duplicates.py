#!/usr/bin/env python3
"""Scan Salesforce Case export for intra-SF duplicate clusters.

Requires a pre-exported SF Case JSON (MCP run_soql_query output saved to disk).

Usage
-----
    python scan_sf_duplicates.py \\
      --sf-cache .tmp/sf-cases-window-20260729.json \\
      --output .tmp/sf-intra-duplicate-scan-20260729.json \\
      --report .tmp/sf-intra-duplicate-report-20260729.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scan_duplicates as sd  # noqa: E402

OPEN = {
    "new",
    "working",
    "open",
    "pending",
    "escalated",
    "on hold",
    "compliance in progress",
}
SHELL = "Service Provider Support Shell Account"
VOICEMAIL_RE = re.compile(r"voicemail[_\s-]*(\d{10,11})", re.I)
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}")


def load_records(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "records" in data:
        return data["records"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Unexpected SF cache shape in {path}")


def norm_phone(raw: str | None) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return None
    return digits


def extract_phones(case: dict) -> set[str]:
    phones: set[str] = set()
    blob = " ".join(
        str(case.get(k) or "")
        for k in ("Subject", "Description")
    )
    for m in VOICEMAIL_RE.finditer(blob):
        p = norm_phone(m.group(1))
        if p:
            phones.add(p)
    for m in PHONE_RE.finditer(blob):
        p = norm_phone(m.group(0))
        if p:
            phones.add(p)
    return phones


def case_summary(c: dict) -> dict:
    return {
        "id": c.get("Id"),
        "case_number": c.get("CaseNumber"),
        "subject": c.get("Subject"),
        "status": c.get("Status"),
        "account": (c.get("Account") or {}).get("Name"),
        "owner": (c.get("Owner") or {}).get("Name"),
        "owner_username": (c.get("Owner") or {}).get("Username"),
        "created_date": c.get("CreatedDate"),
        "contact_email": c.get("ContactEmail"),
        "supplied_email": c.get("SuppliedEmail"),
        "record_type": (c.get("RecordType") or {}).get("Name"),
    }


def is_open_status(status: str | None) -> bool:
    return (status or "").lower() in OPEN


def pick_primary(cases: list[dict]) -> dict:
    cases = sorted(cases, key=lambda x: x.get("CreatedDate") or "")
    open_cases = [c for c in cases if is_open_status(c.get("Status"))]
    if open_cases:
        substantive = [
            c
            for c in open_cases
            if "auto reply" not in (c.get("Subject") or "").lower()
            and not (c.get("Subject") or "").lower().startswith("re:")
        ]
        return substantive[0] if substantive else open_cases[0]
    return cases[0]


def pick_primary_summary(cases: list[dict]) -> dict:
    cases = sorted(cases, key=lambda x: x.get("created_date") or "")
    substantive = [
        c
        for c in cases
        if "auto reply" not in (c.get("subject") or "").lower()
        and not (c.get("subject") or "").lower().startswith("re:")
    ]
    return substantive[0] if substantive else cases[0]


def filter_group_open_only(group: dict) -> dict | None:
    """Keep duplicate clusters with at least two open/new Cases."""
    open_cases = [c for c in group.get("cases") or [] if is_open_status(c.get("status"))]
    if len(open_cases) < 2:
        return None
    primary = pick_primary_summary(open_cases)
    pid = primary.get("id")
    return {
        **group,
        "cases": open_cases,
        "case_count": len(open_cases),
        "open_count": len(open_cases),
        "recommended_primary": primary,
        "merge_candidates": [c for c in open_cases if c.get("id") != pid],
    }


def filter_email_pairs_open_only(pairs: list[dict]) -> list[dict]:
    """Keep subject+email pairs where both Cases are open/new."""
    out: list[dict] = []
    for pair in pairs:
        primary = pair.get("recommended_primary") or {}
        other = pair.get("merge_candidate") or {}
        if is_open_status(primary.get("status")) and is_open_status(other.get("status")):
            out.append(pair)
    return out


def apply_open_only_filter(result: dict) -> dict:
    """Restrict duplicate findings to open/new Cases only."""
    coi = [g for g in (filter_group_open_only(g) for g in result.get("coi_duplicates") or []) if g]
    fd = [g for g in (filter_group_open_only(g) for g in result.get("fd_xref_duplicates") or []) if g]
    phone = [g for g in (filter_group_open_only(g) for g in result.get("phone_duplicates") or []) if g]
    email = filter_email_pairs_open_only(result.get("subject_email_duplicates") or [])

    filtered = dict(result)
    filtered["filter"] = "open_new_only"
    filtered["coi_duplicates"] = coi
    filtered["fd_xref_duplicates"] = fd
    filtered["phone_duplicates"] = phone
    filtered["subject_email_duplicates"] = email
    filtered["coi_dupe_groups"] = len(coi)
    filtered["coi_excess"] = sum(g["case_count"] - 1 for g in coi)
    filtered["fd_xref_groups"] = len(fd)
    filtered["phone_groups"] = len(phone)
    filtered["subject_email_pairs"] = len(email)
    scope = filtered.get("scope") or ""
    if "open/new only" not in scope.lower():
        filtered["scope"] = f"{scope} · open/new duplicate matches only"
    return filtered


def coi_duplicate_groups(records: list[dict]) -> list[dict]:
    by_req: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for c in records:
        fields = sd.extract_federated_coi_fields(c.get("Subject") or "")
        key = sd.coi_req_key(fields)
        if not key:
            continue
        by_req[key].append(c)

    groups = []
    for (policy_id, req_id), cases in sorted(
        by_req.items(), key=lambda x: (x[0][0], int(x[0][1]))
    ):
        if len(cases) <= 1:
            continue
        primary = pick_primary(cases)
        fields = sd.extract_federated_coi_fields(primary.get("Subject") or "")
        open_cases = [c for c in cases if (c.get("Status") or "").lower() in OPEN]
        groups.append(
            {
                "cluster_type": "federated_coi_req_id",
                "policy_id": policy_id,
                "req_id": req_id,
                "provider": fields["provider"] if fields else None,
                "case_count": len(cases),
                "open_count": len(open_cases),
                "recommended_primary": case_summary(primary),
                "merge_candidates": [
                    case_summary(c)
                    for c in cases
                    if c.get("Id") != primary.get("Id")
                ],
                "cases": [case_summary(c) for c in cases],
            }
        )
    return groups


def fd_xref_duplicate_groups(records: list[dict]) -> list[dict]:
    by_fd: dict[str, list[dict]] = defaultdict(list)
    for c in records:
        blob = (c.get("Description") or "") + " " + (c.get("Subject") or "")
        for m in sd.FD_TICKET_RE.finditer(blob):
            by_fd[m.group(1)].append(c)

    groups = []
    for fd_id, cases in sorted(by_fd.items(), key=lambda x: int(x[0])):
        if len(cases) <= 1:
            continue
        primary = pick_primary(cases)
        groups.append(
            {
                "cluster_type": "freshdesk_xref",
                "fd_ticket_id": fd_id,
                "case_count": len(cases),
                "recommended_primary": case_summary(primary),
                "merge_candidates": [
                    case_summary(c)
                    for c in cases
                    if c.get("Id") != primary.get("Id")
                ],
                "cases": [case_summary(c) for c in cases],
            }
        )
    return groups


def phone_duplicate_groups(records: list[dict]) -> list[dict]:
    by_phone: dict[str, list[dict]] = defaultdict(list)
    for c in records:
        subj = (c.get("Subject") or "").lower()
        if "voicemail" not in subj and "voicemail" not in (c.get("Description") or "").lower():
            continue
        for phone in extract_phones(c):
            by_phone[phone].append(c)

    groups = []
    for phone, cases in sorted(by_phone.items()):
        unique_ids = {c["Id"] for c in cases}
        if len(unique_ids) <= 1:
            continue
        deduped = list({c["Id"]: c for c in cases}.values())
        primary = pick_primary(deduped)
        groups.append(
            {
                "cluster_type": "voicemail_phone",
                "phone": phone,
                "case_count": len(deduped),
                "recommended_primary": case_summary(primary),
                "merge_candidates": [
                    case_summary(c)
                    for c in deduped
                    if c.get("Id") != primary.get("Id")
                ],
                "cases": [case_summary(c) for c in deduped],
            }
        )
    return groups


def subject_email_pairs(records: list[dict]) -> list[dict]:
    """Likely duplicate pairs: shared external email + subject similarity >= 0.5."""
    pairs: list[dict] = []
    seen: set[tuple[str, str]] = set()
    indexed: list[tuple[dict, str | None, set[str]]] = []
    for c in records:
        email = sd.norm_email(c.get("ContactEmail") or c.get("SuppliedEmail"))
        tokens = sd.subject_tokens(c.get("Subject") or "")
        indexed.append((c, email, tokens))

    for i, (a, email_a, tok_a) in enumerate(indexed):
        if not email_a:
            continue
        for b, email_b, tok_b in indexed[i + 1 :]:
            if email_a != email_b:
                continue
            sim = sd.jaccard(tok_a, tok_b)
            if sim < 0.5:
                continue
            key = tuple(sorted([a["Id"], b["Id"]]))
            if key in seen:
                continue
            seen.add(key)
            primary = pick_primary([a, b])
            other = b if primary["Id"] == a["Id"] else a
            pairs.append(
                {
                    "cluster_type": "subject_email_pair",
                    "shared_email": email_a,
                    "subject_similarity": round(sim, 3),
                    "recommended_primary": case_summary(primary),
                    "merge_candidate": case_summary(other),
                }
            )
    return pairs


def write_markdown(result: dict, path: Path) -> None:
    lines = [
        "# Salesforce Intra-SF Duplicate Scan",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Source:** `{result['sf_cache']}`",
        f"**Scope:** {result['scope']}",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|------:|",
        f"| Total Cases in export | {result['total_cases']} |",
        f"| Open (actionable) | {result['open_total']} |",
        f"| Federated COI (Req id parsed) | {result['coi_parsed']} |",
        f"| COI duplicate Req groups | {result['coi_dupe_groups']} |",
        f"| COI excess Cases | {result['coi_excess']} |",
        (
            f"| FD cross-ref duplicate groups | {result['fd_xref_groups']} |"
            if result.get("include_fd_xref")
            else "| FD cross-ref duplicate groups | skipped (SF-only default) |"
        ),
        f"| Voicemail phone duplicate groups | {result['phone_groups']} |",
        f"| Subject+email likely pairs | {result['subject_email_pairs']} |",
        f"| Open on Shell Account | {result['shell_open_count']} |",
        "",
    ]

    if result["coi_duplicates"]:
        lines.extend(
            [
                "## Federated COI — same `(policy_id, Req id)`",
                "",
                "Scan/report only — merge/close requires explicit approval.",
                "",
                "| Provider | Req key | Cases | Open | Primary | Merge candidates |",
                "|----------|---------|------:|-----:|---------|------------------|",
            ]
        )
        for g in result["coi_duplicates"]:
            primary = g["recommended_primary"]["case_number"]
            merge = ", ".join(c["case_number"] for c in g["merge_candidates"])
            lines.append(
                f"| {g.get('provider') or '—'} | `{g['policy_id']} Req {g['req_id']}` | "
                f"{g['case_count']} | {g['open_count']} | **{primary}** | {merge or '—'} |"
            )
        lines.append("")

    if result.get("include_fd_xref") and result.get("fd_xref_duplicates"):
        lines.extend(
            [
                "## Freshdesk cross-ref duplicates (opt-in)",
                "",
                "Multiple SF Cases reference the same Freshdesk ticket id.",
                "",
                "| FD ticket | Cases | Primary | Others |",
                "|-----------|------:|---------|--------|",
            ]
        )
        for g in result["fd_xref_duplicates"]:
            primary = g["recommended_primary"]["case_number"]
            others = ", ".join(c["case_number"] for c in g["merge_candidates"])
            lines.append(
                f"| #{g['fd_ticket_id']} | {g['case_count']} | **{primary}** | {others} |"
            )
        lines.append("")

    if result["phone_duplicates"]:
        lines.extend(
            [
                "## Voicemail phone duplicates",
                "",
                "| Phone | Cases | Primary | Others |",
                "|-------|------:|---------|--------|",
            ]
        )
        for g in result["phone_duplicates"]:
            primary = g["recommended_primary"]["case_number"]
            others = ", ".join(c["case_number"] for c in g["merge_candidates"])
            lines.append(
                f"| {g['phone']} | {g['case_count']} | **{primary}** | {others} |"
            )
        lines.append("")

    if result["subject_email_duplicates"]:
        lines.extend(
            [
                "## Subject + email likely duplicates",
                "",
                "| Email | Similarity | Primary | Other |",
                "|-------|----------:|---------|-------|",
            ]
        )
        for p in result["subject_email_duplicates"][:25]:
            lines.append(
                f"| {p['shared_email']} | {p['subject_similarity']} | "
                f"**{p['recommended_primary']['case_number']}** | "
                f"{p['merge_candidate']['case_number']} |"
            )
        if len(result["subject_email_duplicates"]) > 25:
            lines.append("")
            lines.append(
                f"_… and {len(result['subject_email_duplicates']) - 25} more pairs in JSON._"
            )
        lines.append("")

    if result["shell_open"]:
        lines.extend(
            [
                "## Open Cases on Shell Account (blockers)",
                "",
                "Fix Account before merge/close decisions.",
                "",
                "| Case | Status | Created | Subject |",
                "|------|--------|---------|---------|",
            ]
        )
        for c in result["shell_open"][:30]:
            lines.append(
                f"| {c['case_number']} | {c['status']} | "
                f"{(c.get('created_date') or '')[:10]} | "
                f"{(c.get('subject') or '')[:55]} |"
            )
        if len(result["shell_open"]) > 30:
            lines.append("")
            lines.append(f"_… and {len(result['shell_open']) - 30} more in JSON._")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_scan_result(
    records: list[dict],
    *,
    sf_cache: str = "",
    scope: str = "",
    open_only: bool = False,
    include_fd_xref: bool = False,
) -> dict:
    """Build SF-only duplicate-scan payload (reusable from unified triage).

    Default excludes Freshdesk cross-ref clustering. FD pairing is a separate
    opt-in (``include_fd_xref`` / ``--include-fd-xref``) — use for AP-related
    SF Cases via ``scan_duplicates.py``, not as part of the default SF scan.
    """
    coi_dupes = coi_duplicate_groups(records)
    fd_dupes = fd_xref_duplicate_groups(records) if include_fd_xref else []
    phone_dupes = phone_duplicate_groups(records)
    email_pairs = subject_email_pairs(records)

    open_records = [r for r in records if is_open_status(r.get("Status"))]
    coi_parsed = sum(
        1 for r in records if sd.extract_federated_coi_fields(r.get("Subject") or "")
    )
    shell_open = [
        case_summary(c)
        for c in records
        if (c.get("Account") or {}).get("Name") == SHELL
        and (c.get("Status") or "").lower() in OPEN
    ]

    result = {
        "scan": "sf-intra-duplicates",
        "generated": datetime.now(timezone.utc).isoformat(),
        "sf_cache": sf_cache,
        "scope": scope,
        "include_fd_xref": include_fd_xref,
        "total_cases": len(records),
        "open_total": len(open_records),
        "coi_parsed": coi_parsed,
        "coi_dupe_groups": len(coi_dupes),
        "coi_excess": sum(g["case_count"] - 1 for g in coi_dupes),
        "fd_xref_groups": len(fd_dupes),
        "phone_groups": len(phone_dupes),
        "subject_email_pairs": len(email_pairs),
        "shell_open_count": len(shell_open),
        "by_record_type": Counter(
            (r.get("RecordType") or {}).get("Name", "?") for r in records
        ).most_common(),
        "by_status": Counter(r.get("Status") for r in records).most_common(),
        "coi_duplicates": coi_dupes,
        "fd_xref_duplicates": fd_dupes,
        "phone_duplicates": phone_dupes,
        "subject_email_duplicates": email_pairs,
        "shell_open": shell_open,
    }
    if open_only:
        result = apply_open_only_filter(result)
    return result


def duplicate_member_ids(scan: dict) -> set[str]:
    """Case Ids appearing in any duplicate cluster."""
    ids: set[str] = set()
    keys = ["coi_duplicates", "phone_duplicates"]
    if scan.get("include_fd_xref") or scan.get("fd_xref_duplicates"):
        keys.append("fd_xref_duplicates")
    for key in keys:
        for g in scan.get(key) or []:
            for c in g.get("cases") or []:
                if c.get("id"):
                    ids.add(c["id"])
    for p in scan.get("subject_email_duplicates") or []:
        for side in ("case_a", "case_b"):
            cid = (p.get(side) or {}).get("id")
            if cid:
                ids.add(cid)
    return ids


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sf-cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument(
        "--scope",
        default="Owner.Username = crystal.gagner@vixxo.com, CreatedDate >= 2026-06-26",
    )
    parser.add_argument(
        "--include-closed",
        action="store_true",
        help="Include closed Cases in duplicate clusters (default: open/new only)",
    )
    parser.add_argument(
        "--include-fd-xref",
        action="store_true",
        help=(
            "Opt-in: cluster SF Cases that share a Freshdesk # in Description. "
            "Off by default — SF-only scan does not compare to Freshdesk. "
            "For AP-related SF Cases, run scan_duplicates.py separately."
        ),
    )
    args = parser.parse_args(argv)

    records = load_records(args.sf_cache)
    open_only = not args.include_closed
    result = build_scan_result(
        records,
        sf_cache=str(args.sf_cache),
        scope=args.scope,
        open_only=open_only,
        include_fd_xref=args.include_fd_xref,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    report_path = args.report or args.output.with_suffix(".md")
    write_markdown(result, report_path)

    summary = {
        k: result[k]
        for k in (
            "total_cases",
            "open_total",
            "coi_dupe_groups",
            "coi_excess",
            "fd_xref_groups",
            "phone_groups",
            "subject_email_pairs",
            "shell_open_count",
        )
    }
    print(json.dumps(summary, indent=2))
    print(f"OUTPUT: {args.output.resolve()}")
    print(f"REPORT: {report_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
