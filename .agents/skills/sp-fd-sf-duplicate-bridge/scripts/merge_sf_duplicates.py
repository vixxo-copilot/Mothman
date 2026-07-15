#!/usr/bin/env python3
"""Build and execute SF duplicate merge/close plans by request-type bucket.

Groups open Cases by bucket (COI, rate change, VixxoLink, voicemail, etc.),
selects a primary Case per group, copies files to primary, posts a Case comment,
creates an audit Task, and closes newer duplicates.

Default is dry-run. Pass --execute after operator approval.

Usage
-----
    python merge_sf_duplicates.py \\
      --sf-cache .tmp/sf-cases-window-coi-20260707.json \\
      --output .tmp/sf-merge-plan-20260708.json

    python merge_sf_duplicates.py \\
      --scan-input .tmp/sf-duplicate-scan-20260708.json \\
      --buckets coi_federated,vixxolink_support,voicemail \\
      --dry-run

    python merge_sf_duplicates.py \\
      --plan .tmp/sf-merge-plan-20260708.json \\
      --execute \\
      --group-id coi_federated:30201157|12345
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from scan_duplicates import FD_TICKET_RE, load_sf_cases, norm_email
from scan_sf_duplicates import case_entry, pick_primary
from sf_case_buckets import (
    ALL_BUCKETS,
    AUTO_MERGE_BUCKETS,
    BUCKET_COI_FEDERATED,
    BUCKET_COI_UPDATE,
    BUCKET_VOICEMAIL,
    classify_case,
    coi_routing_soql,
    extract_sp_name,
    merge_group_key,
    normalize_sp_key,
    voicemail_sp_captured,
)
from sf_merge_primary import (
    enrich_owner_fields,
    is_actively_worked,
    is_new,
    is_open,
    pick_best,
    pick_merge_primary,
)
from sf_case_activity import apply_touch_fields, fetch_last_touches
from voicemail_match import find_open_work_targets, parse_voicemail_description
from sf_cli import (
    close_case,
    copy_case_files,
    create_completed_task,
    post_case_comment,
    sf_query,
)

SKILL_DIR = Path(__file__).resolve().parents[1]
SKIP_AGENT_BATCH_RE = re.compile(r"agent cert batch|batch certificate", re.I)


def case_row(case: dict, touch_map: dict | None = None) -> dict:
    base = case_entry(case)
    enrich_owner_fields(base, case)
    if touch_map:
        apply_touch_fields(base, touch_map)
    elif base.get("last_modified_at"):
        base["last_touch_at"] = base["last_modified_at"]
        base["last_touch_sources"] = ["case_modified"]
    return base


def enrich_records(
    records: list[dict], org: str, skip_touch: bool
) -> tuple[list[dict], dict[str, dict]]:
    touch_map: dict[str, dict] = {}
    if records and not skip_touch:
        ids = [r.get("Id") for r in records if r.get("Id")]
        touch_map = fetch_last_touches(ids, org, records)
    rows = [case_row(r, touch_map) for r in records]
    return rows, touch_map


def apply_touch_to_pool(cases: list[dict], touch_map: dict[str, dict]) -> list[dict]:
    out = []
    for c in cases:
        row = dict(c)
        apply_touch_fields(row, touch_map)
        out.append(row)
    return out


def bucket_group_id(bucket: str, sp_key: str, email: str) -> str:
    return f"{bucket}:{sp_key or 'unknown'}:{email or 'no-email'}"


def resolve_voicemail_work_target(
    cases: list[dict], all_records: list[dict]
) -> dict | None:
    """Find an open, actively-worked Case matching voicemail description/transcript."""
    best: dict | None = None
    for case in cases:
        hits = find_open_work_targets(case, all_records, min_score=4)
        if not hits:
            continue
        top = hits[0]
        if best is None or top["score"] > best["score"]:
            best = top
    if not best:
        return None
    if not best.get("actively_worked") and not best.get("case"):
        return None
    return best


def build_group_plan(
    bucket: str,
    sp_key: str,
    email: str,
    cases: list[dict],
    all_records: list[dict],
    source: str = "bucket_group",
) -> dict | None:
    open_cases = [c for c in cases if is_open(c)]
    if len(open_cases) <= 1:
        return None

    work_target = None
    primary = None
    review_reason = None
    confidence = "high"

    if bucket == BUCKET_VOICEMAIL:
        work_target = resolve_voicemail_work_target(open_cases, all_records)

    primary, review_reason = pick_merge_primary(open_cases)

    if work_target and work_target.get("actively_worked"):
        wt = work_target["case"]
        if primary is None or is_new(primary) or not is_actively_worked(primary):
            primary = wt
            review_reason = None
            confidence = "high"
    elif primary is None and work_target:
        primary = work_target["case"]
        review_reason = "work_target_new_only"
        confidence = "medium"

    if primary is None:
        recommended = pick_best(open_cases)
        return {
            "group_id": bucket_group_id(bucket, sp_key, email),
            "source": source,
            "bucket": bucket,
            "sp_key": sp_key,
            "requester_email": email or None,
            "sp_name": extract_sp_name(open_cases[0].get("subject"), open_cases[0].get("description")),
            "confidence": "manual",
            "manual_review_reason": review_reason,
            "recommended_primary": recommended,
            "case_count": len(cases),
            "open_count": len(open_cases),
            "primary": None,
            "merge_candidates": [],
            "manual_review_cases": open_cases,
            "coi_route": None,
            "work_target": None,
        }

    merge = [c for c in open_cases if c["id"] != primary["id"]]
    if not merge:
        return None

    subj_blob = " ".join(c.get("subject") or "" for c in cases)
    if SKIP_AGENT_BATCH_RE.search(subj_blob):
        confidence = "low"
    if bucket == BUCKET_VOICEMAIL and not all(
        voicemail_sp_captured(c.get("subject"), c.get("description")) for c in cases
    ):
        confidence = "medium"

    plan: dict = {
        "group_id": bucket_group_id(bucket, sp_key, email),
        "source": source,
        "bucket": bucket,
        "sp_key": sp_key,
        "requester_email": email or None,
        "sp_name": primary.get("sp_name") or extract_sp_name(primary.get("subject"), primary.get("description")),
        "confidence": confidence,
        "manual_review_reason": review_reason,
        "case_count": len(cases),
        "open_count": len(open_cases),
        "primary": primary,
        "primary_last_touch_at": primary.get("last_touch_at"),
        "primary_last_touch_detail": primary.get("last_touch_detail"),
        "merge_candidates": merge,
        "coi_route": None,
        "work_target": None,
    }

    if work_target:
        plan["work_target"] = {
            "case_number": work_target["case"].get("case_number"),
            "case_id": work_target["case"].get("id"),
            "intent_bucket": work_target.get("intent_bucket"),
            "target_bucket": work_target.get("target_bucket"),
            "match_reasons": work_target.get("match_reasons"),
            "score": work_target.get("score"),
            "actively_worked": work_target.get("actively_worked"),
            "last_touch_at": work_target["case"].get("last_touch_at"),
            "last_touch_detail": work_target["case"].get("last_touch_detail"),
            "signals": work_target.get("signals"),
            "cross_bucket": work_target.get("target_bucket") != bucket,
        }
        if review_reason:
            plan["confidence"] = "manual"
    elif review_reason:
        plan["confidence"] = "manual"

    if bucket == BUCKET_VOICEMAIL:
        vm = parse_voicemail_description(open_cases[0].get("description"))
        plan["voicemail_signals"] = {
            "category": vm.get("category"),
            "intent_bucket": vm.get("intent_bucket"),
            "company": vm.get("company"),
            "caller": vm.get("caller"),
            "callback": vm.get("callback"),
            "transcript_excerpt": (vm.get("transcript") or "")[:160],
        }

    return plan


def analyze_bucket_groups(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Group Cases by bucket; return (auto_plans, manual_review)."""
    groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)

    for row in rows:
        key = merge_group_key(
            {
                "Subject": row.get("subject"),
                "Description": row.get("description"),
                "ContactEmail": row.get("contact_email"),
                "SuppliedEmail": row.get("supplied_email"),
            }
        )
        if not key:
            continue
        groups[key].append(row)

    plans: list[dict] = []
    manual: list[dict] = []
    for (bucket, sp_key, email), cases in sorted(groups.items()):
        if len(cases) <= 1:
            continue
        plan = build_group_plan(bucket, sp_key, email, cases, rows)
        if not plan:
            continue
        if plan.get("confidence") == "manual" or plan.get("manual_review_reason"):
            manual.append(plan)
        if plan.get("primary") and plan.get("merge_candidates"):
            plans.append(plan)
    return plans, manual


def scan_group_to_plan(
    group: dict,
    bucket: str | None = None,
    all_records: list[dict] | None = None,
    touch_map: dict[str, dict] | None = None,
) -> dict | None:
    merge = group.get("merge_candidates") or []
    if not merge:
        return None
    primary = group.get("primary")
    if not primary:
        return None

    pool = apply_touch_to_pool([primary, *merge], touch_map or {})
    open_pool = [c for c in pool if is_open(c)]
    if len(open_pool) < 2:
        return None

    dup_type = group.get("dup_type", "")
    if dup_type == "federated_coi_req_id":
        b = BUCKET_COI_FEDERATED
        gid = f"coi_federated:{group.get('policy_id')}|{group.get('req_id')}"
    else:
        b = bucket or classify_case(primary.get("subject"), primary.get("description"))
        sp = normalize_sp_key(group.get("provider")) or ""
        email = group.get("requester_email") or ""
        gid = bucket_group_id(b, sp, email)

    work_target = None
    review_reason = None
    confidence = "high" if dup_type == "federated_coi_req_id" else "medium"

    if b == BUCKET_VOICEMAIL and all_records:
        work_target = resolve_voicemail_work_target(open_pool, all_records)

    primary, review_reason = pick_merge_primary(open_pool)

    if work_target and work_target.get("actively_worked"):
        wt = work_target["case"]
        if primary is None or is_new(primary) or not is_actively_worked(primary):
            primary = wt
            review_reason = None
            confidence = "high"
    elif primary is None and work_target:
        primary = work_target["case"]
        review_reason = "work_target_new_only"
        confidence = "medium"

    if review_reason and confidence != "high":
        confidence = "manual"

    if primary is None:
        return {
            "group_id": gid,
            "source": "scan_json",
            "bucket": b,
            "dup_type": dup_type,
            "confidence": "manual",
            "manual_review_reason": review_reason,
            "manual_review_cases": open_pool,
            "primary": None,
            "merge_candidates": [],
            "policy_id": group.get("policy_id"),
            "req_id": group.get("req_id"),
        }

    merge = [c for c in open_pool if c["id"] != primary["id"]]
    if not merge:
        return None

    plan = {
        "group_id": gid,
        "source": "scan_json",
        "bucket": b,
        "dup_type": dup_type,
        "sp_key": normalize_sp_key(group.get("provider")),
        "requester_email": group.get("requester_email"),
        "sp_name": group.get("provider"),
        "confidence": confidence,
        "manual_review_reason": review_reason,
        "case_count": group.get("case_count"),
        "open_count": len(open_pool),
        "primary": primary,
        "merge_candidates": merge,
        "coi_route": None,
        "policy_id": group.get("policy_id"),
        "req_id": group.get("req_id"),
        "work_target": None,
    }
    if work_target:
        plan["work_target"] = {
            "case_number": work_target["case"].get("case_number"),
            "match_reasons": work_target.get("match_reasons"),
            "actively_worked": work_target.get("actively_worked"),
            "cross_bucket": work_target.get("target_bucket") != b,
        }
    return plan


def load_plans_from_scan(
    scan_path: Path,
    bucket_filter: set[str] | None,
    all_records: list[dict] | None = None,
    touch_map: dict[str, dict] | None = None,
) -> tuple[list[dict], list[dict]]:
    data = json.loads(scan_path.read_text(encoding="utf-8"))
    auto: list[dict] = []
    manual: list[dict] = []
    for g in data.get("federated_duplicates") or []:
        plan = scan_group_to_plan(g, all_records=all_records, touch_map=touch_map)
        if plan:
            (manual if plan.get("confidence") == "manual" else auto).append(plan)
    for g in data.get("subject_duplicates") or []:
        subj = g.get("subject_key") or ""
        bucket = classify_case(subj)
        plan = scan_group_to_plan(g, bucket=bucket, all_records=all_records, touch_map=touch_map)
        if plan:
            (manual if plan.get("confidence") == "manual" else auto).append(plan)

    if bucket_filter:
        auto = [p for p in auto if p["bucket"] in bucket_filter]
        manual = [p for p in manual if p["bucket"] in bucket_filter]
    return dedupe_plans(auto), manual


def dedupe_plans(plans: list[dict]) -> list[dict]:
    """Keep highest-confidence plan per duplicate Case id."""
    by_dup: dict[str, dict] = {}
    order = {"high": 0, "medium": 1, "low": 2}
    for plan in plans:
        for dup in plan.get("merge_candidates") or []:
            did = dup.get("id")
            if not did:
                continue
            existing = by_dup.get(did)
            if not existing or order.get(plan["confidence"], 9) < order.get(
                existing["confidence"], 9
            ):
                by_dup[did] = plan
    seen: set[str] = set()
    out: list[dict] = []
    for plan in plans:
        gid = plan["group_id"]
        if gid in seen:
            continue
        seen.add(gid)
        out.append(plan)
    return sorted(out, key=lambda p: (p["bucket"], p.get("sp_name") or ""))


def resolve_coi_routing(plan: dict, org: str) -> dict:
    """When COI dup has no strong primary, prefer open onboarding Case for SP."""
    if plan["bucket"] not in {BUCKET_COI_FEDERATED, BUCKET_COI_UPDATE}:
        return plan
    sp = plan.get("sp_name") or plan.get("sp_key")
    if not sp or len(sp) < 3:
        return plan

    hits = sf_query(coi_routing_soql(sp), org=org)
    if not hits:
        return plan

    def _row(h: dict) -> dict:
        return {"status": h.get("Status"), "owner": h.get("Owner", {}).get("Username") if isinstance(h.get("Owner"), dict) else None}

    active_hits = [h for h in hits if is_actively_worked(_row(h))]
    assigned_hits = [h for h in hits if _row(h).get("owner")]
    target = (active_hits or assigned_hits or hits)[0]
    plan = dict(plan)
    plan["coi_route"] = {
        "target_case_id": target.get("Id"),
        "target_case_number": target.get("CaseNumber"),
        "target_subject": target.get("Subject"),
        "reason": "open_onboarding_or_lead_case",
    }
    primary = dict(plan["primary"])
    primary["id"] = target["Id"]
    primary["case_number"] = target["CaseNumber"]
    primary["subject"] = target.get("Subject")
    plan["primary"] = primary
    plan["confidence"] = "medium"
    return plan


def merge_comment(primary: dict, dup: dict, plan: dict) -> str:
    bucket = plan.get("bucket", "duplicate")
    lines = [
        f"Duplicate Case consolidated ({bucket}).",
        f"Merged Case {dup.get('case_number')} into this Case.",
        f"Subject: {dup.get('subject', '')[:200]}",
    ]
    if plan.get("coi_route"):
        lines.append(
            f"COI routed to onboarding Case per SP match "
            f"({plan['coi_route'].get('target_case_number')})."
        )
    wt = plan.get("work_target") or {}
    if wt.get("case_number"):
        lines.append(
            f"Matched open work Case {wt['case_number']} via "
            f"{', '.join(wt.get('match_reasons') or [])}."
        )
    fd = FD_TICKET_RE.search(dup.get("description") or "")
    if fd:
        lines.append(f"Freshdesk cross-ref: #{fd.group(1)}")
    return " ".join(lines)


def duplicate_close_comment(primary: dict, dup: dict, plan: dict) -> str:
    """Case comment posted on the duplicate before close."""
    bucket = plan.get("bucket", "duplicate")
    return (
        f"Closed Reason: Duplicate. This Case was consolidated into "
        f"Case {primary.get('case_number')} ({bucket}). "
        f"Refer to Case {primary.get('case_number')} for ongoing work."
    )


def task_description(primary: dict, dup: dict, plan: dict, file_results: list) -> str:
    copied = sum(1 for r in file_results if r.get("ok"))
    return (
        f"SF duplicate merge — bucket={plan.get('bucket')}\n"
        f"Closed duplicate Case {dup.get('case_number')} → primary {primary.get('case_number')}\n"
        f"Files linked to primary: {copied}\n"
        f"Group: {plan.get('group_id')}"
    )


def extract_fd_ticket(description: str | None) -> str | None:
    m = FD_TICKET_RE.search(description or "")
    return m.group(1) if m else None


def maybe_sync_voicemail_wav(
    dup: dict, primary: dict, org: str, dry_run: bool
) -> dict | None:
    fd_id = extract_fd_ticket(dup.get("description"))
    if not fd_id:
        return None
    if dry_run:
        return {"dry_run": True, "fd_ticket_id": fd_id, "sf_case_number": primary.get("case_number")}
    script = SKILL_DIR / "scripts" / "sync_attachments_to_sf.py"
    cmd = [
        sys.executable,
        str(script),
        "--fd-ticket-id",
        fd_id,
        "--sf-case-number",
        primary.get("case_number"),
        "--policy",
        "voicemail-wav",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return {
        "fd_ticket_id": fd_id,
        "ok": proc.returncode == 0,
        "stdout": proc.stdout[-500:],
        "stderr": proc.stderr[-500:],
    }


def execute_merge(plan: dict, dup: dict, org: str, dry_run: bool, sync_voicemail: bool) -> dict:
    primary = plan["primary"]
    result = {
        "group_id": plan["group_id"],
        "bucket": plan["bucket"],
        "primary_case_number": primary.get("case_number"),
        "duplicate_case_number": dup.get("case_number"),
        "dry_run": dry_run,
        "steps": [],
    }

    comment = merge_comment(primary, dup, plan)
    dup_comment = duplicate_close_comment(primary, dup, plan)
    task_subj = f"Duplicate merge — {dup.get('case_number')} → {primary.get('case_number')}"

    if dry_run:
        fd_id = extract_fd_ticket(dup.get("description"))
        result["steps"] = [
            {"action": "copy_files", "from": dup["id"], "to": primary["id"]},
            {"action": "case_comment_primary", "body": comment[:300]},
            {"action": "case_comment_duplicate", "body": dup_comment[:300]},
            {
                "action": "close_case",
                "case_number": dup.get("case_number"),
                "closed_reason": "Duplicate",
            },
            {"action": "audit_task", "subject": task_subj},
        ]
        if sync_voicemail and plan["bucket"] == BUCKET_VOICEMAIL and fd_id:
            result["steps"].append(
                {"action": "sync_voicemail_wav", "fd_ticket_id": fd_id}
            )
        return result

    file_results = copy_case_files(dup["id"], primary["id"], org=org)
    result["steps"].append({"action": "copy_files", "results": file_results})

    comment_r = post_case_comment(primary["id"], comment, org=org)
    result["steps"].append({"action": "case_comment_primary", "result": comment_r})

    dup_comment_r = post_case_comment(dup["id"], dup_comment, org=org)
    result["steps"].append({"action": "case_comment_duplicate", "result": dup_comment_r})

    if sync_voicemail and plan["bucket"] == BUCKET_VOICEMAIL:
        sync_r = maybe_sync_voicemail_wav(dup, primary, org, dry_run=False)
        if sync_r:
            result["steps"].append({"action": "sync_voicemail_wav", "result": sync_r})

    task_r = create_completed_task(
        primary["id"],
        task_subj,
        task_description(primary, dup, plan, file_results),
        org=org,
    )
    result["steps"].append({"action": "audit_task", "result": task_r})

    close_r = close_case(dup["id"], org=org)
    result["steps"].append({"action": "close_case", "result": close_r})

    result["ok"] = all(
        s.get("result", {}).get("ok", True)
        for s in result["steps"]
        if "result" in s
    )
    return result


def write_manual_review_report(manual: list[dict], path: Path) -> None:
    lines = [
        "# SF Merge — Manual Review",
        "",
        f"**Groups requiring operator decision:** {len(manual)}",
        "",
        "| Reason | SP / bucket | Cases | Notes |",
        "|--------|-------------|-------|-------|",
    ]
    reason_labels = {
        "multiple_new_unassigned": "Multiple New, queue-owned (no comments/history)",
        "multiple_new_assigned": "Multiple New, different assignees",
        "multiple_new_recent_activity": "Multiple New with competing recent touches",
        "all_closed": "All Cases closed",
        "work_target_new_only": "Only New-status work match found",
    }
    for plan in manual:
        reason = reason_labels.get(
            plan.get("manual_review_reason") or "",
            plan.get("manual_review_reason") or "manual",
        )
        cases = plan.get("manual_review_cases") or plan.get("merge_candidates") or []
        nums = ", ".join(c.get("case_number") or "?" for c in cases[:8])
        notes = ""
        if plan.get("voicemail_signals"):
            sig = plan["voicemail_signals"]
            notes = f"{sig.get('company') or '—'} / {sig.get('caller') or '—'}"
        lines.append(
            f"| {reason} | {plan.get('sp_name') or plan.get('bucket')} | {nums} | {notes} |"
        )
    lines.append("")
    for plan in manual:
        lines.append(f"## {plan.get('group_id')}")
        lines.append("")
        lines.append(f"**Reason:** {plan.get('manual_review_reason')}")
        rec = plan.get("recommended_primary")
        if rec:
            lines.append(
                f"**Suggested primary:** {rec.get('case_number')} "
                f"({rec.get('status')}) last touch {rec.get('last_touch_at') or '—'}"
            )
            if rec.get("last_touch_detail"):
                lines.append(f"**Last touch:** {rec.get('last_touch_detail')}")
        if plan.get("voicemail_signals"):
            sig = plan["voicemail_signals"]
            lines.append(f"**Company:** {sig.get('company') or '—'}")
            lines.append(f"**Caller:** {sig.get('caller') or '—'}")
            lines.append(f"**Transcript:** {sig.get('transcript_excerpt') or '—'}")
        lines.append("")
        for c in plan.get("manual_review_cases") or []:
            touch = c.get("last_touch_at") or "—"
            detail = c.get("last_touch_detail") or ""
            lines.append(
                f"- **{c.get('case_number')}** ({c.get('status')}) "
                f"owner={c.get('owner') or 'queue'} last_touch={touch} {detail}"
            )
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_plan(
    sf_cache: Path | None,
    scan_input: Path | None,
    buckets: set[str] | None,
    resolve_coi: bool,
    org: str,
    skip_touch: bool = False,
) -> dict:
    plans: list[dict] = []
    manual_review: list[dict] = []
    total_cases = 0
    records: list[dict] = []
    enriched: list[dict] = []
    touch_map: dict[str, dict] = {}

    if sf_cache and sf_cache.is_file():
        records = load_sf_cases(sf_cache)
        total_cases = len(records)
        enriched, touch_map = enrich_records(records, org, skip_touch)

    if scan_input and scan_input.is_file():
        scan_plans, scan_manual = load_plans_from_scan(
            scan_input, buckets, enriched or None, touch_map
        )
        plans.extend(scan_plans)
        manual_review.extend(scan_manual)

    if enriched:
        bucket_plans, bucket_manual = analyze_bucket_groups(enriched)
        if buckets:
            bucket_plans = [p for p in bucket_plans if p["bucket"] in buckets]
            bucket_manual = [p for p in bucket_manual if p["bucket"] in buckets]
        plans.extend(bucket_plans)
        manual_review.extend(bucket_manual)

    plans = dedupe_plans(plans)
    if buckets:
        plans = [p for p in plans if p["bucket"] in buckets]

    if resolve_coi:
        plans = [resolve_coi_routing(p, org) for p in plans]

    auto_eligible = [p for p in plans if p["bucket"] in AUTO_MERGE_BUCKETS]
    skip_low = [p for p in plans if p.get("confidence") == "low"]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_cases_scanned": total_cases,
        "bucket_filter": sorted(buckets) if buckets else None,
        "merge_group_count": len(plans),
        "manual_review_count": len(manual_review),
        "touch_lookup": "skipped" if skip_touch else "live",
        "auto_eligible_groups": len(auto_eligible),
        "low_confidence_groups": len(skip_low),
        "plans": plans,
        "manual_review": manual_review,
    }


def filter_plans(plan_doc: dict, group_id: str | None, skip_low: bool, include_manual: bool) -> list[dict]:
    plans = plan_doc.get("plans") or []
    if group_id:
        plans = [p for p in plans if p.get("group_id") == group_id]
    if skip_low:
        plans = [p for p in plans if p.get("confidence") not in ("low", "manual")]
    elif not include_manual:
        plans = [p for p in plans if p.get("confidence") != "manual"]
    return [p for p in plans if p.get("primary") and p.get("merge_candidates")]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sf-cache", type=Path, help="SF Cases JSON export")
    parser.add_argument("--scan-input", type=Path, help="Output from scan_sf_duplicates.py")
    parser.add_argument("--plan", type=Path, help="Existing merge plan JSON")
    parser.add_argument("--output", type=Path, help="Write merge plan JSON")
    parser.add_argument(
        "--buckets",
        default="",
        help=f"Comma-separated buckets (default: all auto-merge). Known: {','.join(sorted(ALL_BUCKETS))}",
    )
    parser.add_argument("--group-id", help="Execute or preview a single merge group")
    parser.add_argument(
        "--resolve-coi-onboarding",
        action="store_true",
        help="Route COI dupes to open onboarding Case for SP when found",
    )
    parser.add_argument(
        "--sync-voicemail",
        action="store_true",
        help="Sync .wav from Freshdesk when duplicate is voicemail bucket",
    )
    parser.add_argument("--org", default="vixxo")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Perform SF writes (default: dry-run only)",
    )
    parser.add_argument(
        "--include-low-confidence",
        action="store_true",
        help="Include agent-batch and other low-confidence groups",
    )
    parser.add_argument(
        "--include-manual-review",
        action="store_true",
        help="Include manual-review groups in execute/dry-run output",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Write manual-review markdown report",
    )
    parser.add_argument(
        "--skip-touch-lookup",
        action="store_true",
        help="Use cache LastModifiedDate only; skip CaseComment/History/Task SOQL",
    )
    args = parser.parse_args(argv)

    if not args.sf_cache and not args.scan_input and not args.plan:
        parser.error("Provide --sf-cache, --scan-input, and/or --plan")

    bucket_filter: set[str] | None = None
    if args.buckets.strip():
        bucket_filter = {b.strip() for b in args.buckets.split(",") if b.strip()}
    elif not args.plan:
        bucket_filter = set(AUTO_MERGE_BUCKETS)

    if args.plan and args.plan.is_file():
        plan_doc = json.loads(args.plan.read_text(encoding="utf-8"))
    else:
        plan_doc = build_plan(
            args.sf_cache,
            args.scan_input,
            bucket_filter,
            args.resolve_coi_onboarding,
            args.org,
            skip_touch=args.skip_touch_lookup,
        )
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(plan_doc, indent=2), encoding="utf-8")
        report_path = args.report or (
            args.output.with_name(args.output.stem + "-manual-review.md") if args.output else None
        )
        if report_path and plan_doc.get("manual_review"):
            write_manual_review_report(plan_doc["manual_review"], report_path)

    plans = filter_plans(
        plan_doc,
        args.group_id,
        skip_low=not args.include_low_confidence,
        include_manual=args.include_manual_review,
    )
    dry_run = not args.execute

    executions: list[dict] = []
    seen_dup_ids: set[str] = set()
    for plan in plans:
        for dup in plan.get("merge_candidates") or []:
            dup_id = dup.get("id")
            if dup_id and dup_id in seen_dup_ids:
                continue
            if not is_open(dup) and not args.execute:
                continue
            if dup_id:
                seen_dup_ids.add(dup_id)
            executions.append(
                execute_merge(
                    plan,
                    dup,
                    args.org,
                    dry_run=dry_run,
                    sync_voicemail=args.sync_voicemail,
                )
            )

    summary = {
        "mode": "execute" if args.execute else "dry_run",
        "groups": len(plans),
        "merge_actions": len(executions),
        "manual_review_groups": len(plan_doc.get("manual_review") or []),
        "generated_at": plan_doc.get("generated_at"),
    }
    print(json.dumps(summary, indent=2))
    for ex in executions[:20]:
        print(json.dumps(ex, indent=2))
    if len(executions) > 20:
        print(f"... and {len(executions) - 20} more actions")

    if args.output and not args.plan:
        print(f"PLAN: {args.output.resolve()}")

    if dry_run and executions:
        print("\nDRY-RUN: pass --execute after operator approval to apply merges.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
