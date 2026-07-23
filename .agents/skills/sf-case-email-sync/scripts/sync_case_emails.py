#!/usr/bin/env python3
"""Sync Outlook email threads and attachments onto Salesforce Cases.

Default is dry-run. Pass --execute to write .eml files, attachments, and
EmailMessage records to Salesforce.

Examples
--------
    python sync_case_emails.py --owner-me
    python sync_case_emails.py --case-number 6911 --execute
    python sync_case_emails.py --case-number 6911 --sr 1-6574285042 --execute
    python sync_case_emails.py --owner-me --days 14 --output .tmp/sf-email-sync-plan.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sf_helpers import (
    case_file_titles,
    case_message_identifiers,
    resolve_user_id,
    sf_auth,
    sf_post,
    sf_query,
    title_exists,
    upload_file,
)

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_DIR.parents[2]
OUTLOOK = SKILL_DIR / "scripts" / "outlook_mail.mjs"
OUT_DEFAULT = REPO_ROOT / ".tmp" / "sf-case-email-sync"

SR_RE = re.compile(r"1-\d{10}")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
STOP_WORDS = {
    "case",
    "vixxo",
    "support",
    "request",
    "service",
    "provider",
    "from",
    "with",
    "your",
    "the",
    "and",
    "for",
}


def read_json_text(text: str) -> dict:
    raw = text.encode("utf-8") if isinstance(text, str) else text
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        text = raw.decode("utf-16")
    else:
        text = raw.decode("utf-8-sig")
    return json.loads(text)


def run_outlook(args: list[str]) -> dict | bytes:
    proc = subprocess.run(
        ["node", str(OUTLOOK), *args],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace") or proc.stdout.decode("utf-8", errors="replace")
        raise RuntimeError(err.strip() or "outlook_mail.mjs failed")
    if args and args[0] in {"download-attachment", "download-mime"}:
        return proc.stdout
    return read_json_text(proc.stdout.decode("utf-8"))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sync M365 mail onto Salesforce Cases")
    p.add_argument("--org", default=os.environ.get("SF_TARGET_ORG", "vixxo"))
    p.add_argument("--owner-me", action="store_true", help="Scan Cases owned by current SF user")
    p.add_argument("--owner-email", help="Owner email (default: sf org username)")
    p.add_argument("--case-id", help="Single Case Salesforce Id")
    p.add_argument("--case-number", help="Single Case number (e.g. 6911)")
    p.add_argument("--sr", help="Override SR search key (1-##########)")
    p.add_argument("--status", default="open", choices=["open", "all"], help="Case status filter")
    p.add_argument("--days", type=int, default=30, help="Mail lookback window")
    p.add_argument("--limit", type=int, default=25, help="Max Cases to scan in batch mode")
    p.add_argument(
        "--execute",
        action="store_true",
        help="Upload files and create EmailMessages (default is dry-run plan only)",
    )
    p.add_argument("--skip-email-message", action="store_true", help="Upload files only")
    p.add_argument("--output", type=Path, help="Write JSON plan/report path")
    p.add_argument("--account-audit", action="store_true", help="Run Case Account audit before email sync plan")
    p.add_argument("--quiet", action="store_true", help="Suppress JSON report on stdout")
    p.add_argument("--work-dir", type=Path, default=OUT_DEFAULT, help="Download staging dir")
    return p.parse_args()


def fetch_cases(
    org: str,
    *,
    owner_id: str | None,
    case_id: str | None,
    case_number: str | None,
    status: str,
    limit: int,
) -> list[dict]:
    fields = (
        "Id, CaseNumber, Subject, Description, Status, ContactEmail, SuppliedEmail, "
        "CreatedDate, LastModifiedDate"
    )
    if case_id:
        soql = f"SELECT {fields} FROM Case WHERE Id = '{case_id}' LIMIT 1"
    elif case_number:
        num = case_number.lstrip("0")
        soql = (
            f"SELECT {fields} FROM Case WHERE CaseNumber = '{num}' "
            f"OR CaseNumber = '{case_number.zfill(8)}' LIMIT 1"
        )
    else:
        if not owner_id:
            raise RuntimeError("--owner-me or --owner-email required for batch mode")
        status_clause = " AND IsClosed = false" if status == "open" else ""
        soql = (
            f"SELECT {fields} FROM Case WHERE OwnerId = '{owner_id}'{status_clause} "
            f"ORDER BY LastModifiedDate DESC LIMIT {limit}"
        )
    return sf_query(soql, org=org)


def extract_search_keys(case: dict, sr_override: str | None) -> dict:
    text = " ".join(
        filter(
            None,
            [case.get("Subject") or "", case.get("Description") or "", case.get("CaseNumber") or ""],
        )
    )
    srs = sorted(set(SR_RE.findall(text)))
    if sr_override and sr_override not in srs:
        srs.insert(0, sr_override)
    case_num = str(case.get("CaseNumber") or "").lstrip("0")
    emails = []
    for field in ("ContactEmail", "SuppliedEmail"):
        val = (case.get(field) or "").strip().lower()
        if val and val not in emails and not val.endswith("@vixxo.com"):
            emails.append(val)
    for match in EMAIL_RE.findall(text):
        addr = match.lower()
        if addr.endswith("@vixxo.com"):
            continue
        if addr not in emails:
            emails.append(addr)
    subject_tokens = {
        tok.lower()
        for tok in re.findall(r"[A-Za-z0-9]{4,}", case.get("Subject") or "")
        if tok.lower() not in STOP_WORDS
    }
    return {
        "sr_numbers": srs,
        "case_number": case_num,
        "emails": emails,
        "subject_tokens": sorted(subject_tokens),
    }


def within_days(msg: dict, days: int) -> bool:
    raw = msg.get("receivedDateTime") or msg.get("sentDateTime") or ""
    if not raw:
        return True
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return dt >= cutoff


def message_confidence(msg: dict, keys: dict) -> tuple[str, list[str]]:
    hay = " ".join(
        [
            msg.get("subject") or "",
            msg.get("bodyPreview") or "",
            ((msg.get("from") or {}).get("emailAddress") or {}).get("address") or "",
        ]
    ).lower()
    reasons: list[str] = []
    for sr in keys["sr_numbers"]:
        if sr.lower() in hay:
            reasons.append(f"sr:{sr}")
            return "high", reasons
    cn = keys["case_number"]
    if cn and re.search(rf"\b0*{re.escape(cn)}\b", hay):
        reasons.append(f"case_number:{cn}")
        return "high", reasons
    from_addr = ((msg.get("from") or {}).get("emailAddress") or {}).get("address") or ""
    from_addr = from_addr.lower()
    if from_addr and from_addr in keys["emails"]:
        overlap = [t for t in keys["subject_tokens"] if t in hay]
        if overlap:
            reasons.append(f"email:{from_addr}")
            reasons.extend(f"token:{t}" for t in overlap[:3])
            return "medium", reasons
    return "low", reasons


def search_mail(keys: dict, days: int) -> list[dict]:
    queries: list[str] = []
    queries.extend(keys["sr_numbers"])
    if keys["case_number"]:
        queries.append(keys["case_number"])
    for email in keys["emails"][:2]:
        queries.append(email)
    for token in keys["subject_tokens"][:2]:
        queries.append(token)

    seen: dict[str, dict] = {}
    for query in queries:
        if not query:
            continue
        try:
            data = run_outlook(["search", "--query", query, "--top", "50"])
        except RuntimeError as exc:
            if "Invalid" in str(exc):
                continue
            raise
        for msg in data.get("value") or []:
            mid = msg.get("id")
            if not mid or not within_days(msg, days):
                continue
            seen[mid] = msg
    return list(seen.values())


def eml_title(case: dict, msg: dict) -> str:
    dt = (msg.get("sentDateTime") or msg.get("receivedDateTime") or "")[:16]
    dt = dt.replace("T", " ").replace(":", "")
    from_field = msg.get("from")
    if isinstance(from_field, str):
        sender = from_field.split("@")[0].replace(".", " ")
    else:
        sender = ((from_field or {}).get("emailAddress") or {}).get("name") or "Unknown"
    subject = msg.get("subject") or "No Subject"
    kind = "FW" if subject.upper().startswith("FW:") else "RE"
    cn = str(case.get("CaseNumber") or "Case").lstrip("0")
    return f"Case {cn} - {dt} - {sender} - {kind}"


def operator_email() -> str:
    try:
        me = run_outlook(["whoami"])
        return ((me.get("mail") or me.get("userPrincipalName") or "")).lower()
    except RuntimeError:
        return ""


def create_email_message(token: str, instance_url: str, case_id: str, mail: dict, operator: str) -> dict:
    from_addr = ((mail.get("from") or {}).get("emailAddress") or {}).get("address") or ""
    incoming = from_addr.lower() != operator if operator else from_addr.lower().endswith("@vixxo.com") is False
    body = ((mail.get("body") or {}).get("content")) or ""
    to_addrs = [
        r["emailAddress"]["address"]
        for r in mail.get("toRecipients") or []
        if r.get("emailAddress", {}).get("address")
    ]
    cc_addrs = [
        r["emailAddress"]["address"]
        for r in mail.get("ccRecipients") or []
        if r.get("emailAddress", {}).get("address")
    ]
    payload = {
        "ParentId": case_id,
        "Subject": mail.get("subject") or "(no subject)",
        "FromName": ((mail.get("from") or {}).get("emailAddress") or {}).get("name") or from_addr,
        "FromAddress": from_addr,
        "ToAddress": to_addrs[0] if len(to_addrs) == 1 else "; ".join(to_addrs),
        "CcAddress": "; ".join(cc_addrs) if cc_addrs else None,
        "TextBody": body,
        "HtmlBody": f"<pre>{escape(body)}</pre>",
        "Incoming": incoming,
        "Status": "0" if incoming else "3",
        "MessageDate": mail.get("receivedDateTime") if incoming else mail.get("sentDateTime"),
        "MessageIdentifier": mail.get("internetMessageId"),
    }
    payload = {k: v for k, v in payload.items() if v}
    return sf_post(token, instance_url, "EmailMessage", payload)


def sync_message(
    *,
    case: dict,
    msg_summary: dict,
    titles: set[str],
    msg_ids: set[str],
    org: str,
    work_dir: Path,
    execute: bool,
    skip_email_message: bool,
    token: str | None,
    instance_url: str | None,
    operator: str,
) -> dict:
    case_id = case["Id"]
    message_id = msg_summary["id"]
    title = eml_title(case, msg_summary)
    eml_name = f"{title}.eml"
    result = {
        "message_id": message_id,
        "subject": msg_summary.get("subject"),
        "title": title,
        "actions": [],
        "errors": [],
    }

    mail = run_outlook(["get-message", "--message-id", message_id])
    internet_id = mail.get("internetMessageId")

    if execute and token and instance_url and not skip_email_message:
        if internet_id and internet_id in msg_ids:
            result["actions"].append("skip_email_message_exists")
        else:
            try:
                em = create_email_message(token, instance_url, case_id, mail, operator)
                result["actions"].append(f"email_message:{em.get('id')}")
                if internet_id:
                    msg_ids.add(internet_id)
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                result["errors"].append(f"email_message:{detail[:500]}")
                result["actions"].append("email_message_failed_files_only")
    elif not execute:
        if internet_id and internet_id in msg_ids:
            result["actions"].append("would_skip_email_message_exists")
        else:
            result["actions"].append("would_create_email_message")

    if title_exists(eml_name, titles) or title_exists(title, titles):
        result["actions"].append("skip_file_exists")
    elif execute:
        dest = work_dir / eml_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        raw = run_outlook(["download-mime", "--message-id", message_id])
        dest.write_bytes(raw)
        upload_file(case_id, dest, title, org=org)
        result["actions"].append(f"upload_eml:{title}")
        titles.add(title)
        titles.add(eml_name)
    else:
        result["actions"].append("would_upload_eml")

    if mail.get("hasAttachments"):
        att_data = run_outlook(["list-attachments", "--message-id", message_id])
        for att in att_data.get("value") or []:
            name = att.get("name") or "attachment"
            att_title = Path(name).stem
            if title_exists(name, titles) or title_exists(att_title, titles):
                result["actions"].append(f"skip_attachment:{name}")
                continue
            if execute:
                dest = work_dir / name
                raw = run_outlook(
                    ["download-attachment", "--message-id", message_id, "--attachment-id", att["id"]]
                )
                dest.write_bytes(raw)
                upload_file(case_id, dest, att_title, org=org)
                result["actions"].append(f"upload_attachment:{name}")
                titles.add(att_title)
                titles.add(name)
            else:
                result["actions"].append(f"would_upload_attachment:{name}")

    return result


def plan_case(case: dict, sr_override: str | None, days: int) -> dict:
    keys = extract_search_keys(case, sr_override)
    candidates = search_mail(keys, days)
    matched: list[dict] = []
    manual_review: list[dict] = []
    for msg in candidates:
        confidence, reasons = message_confidence(msg, keys)
        entry = {
            "id": msg.get("id"),
            "subject": msg.get("subject"),
            "from": ((msg.get("from") or {}).get("emailAddress") or {}).get("address"),
            "receivedDateTime": msg.get("receivedDateTime"),
            "confidence": confidence,
            "reasons": reasons,
        }
        if confidence == "low":
            manual_review.append(entry)
        else:
            matched.append(entry)
    matched.sort(key=lambda m: m.get("receivedDateTime") or "")
    return {
        "case_id": case.get("Id"),
        "case_number": case.get("CaseNumber"),
        "subject": case.get("Subject"),
        "status": case.get("Status"),
        "search_keys": keys,
        "matched_messages": matched,
        "manual_review": manual_review,
    }


def main() -> int:
    args = parse_args()
    execute = bool(args.execute)
    dry_run = not execute

    owner_id = None
    if args.owner_me or (not args.case_id and not args.case_number):
        owner_id = resolve_user_id(args.org, args.owner_email)

    cases = fetch_cases(
        args.org,
        owner_id=owner_id,
        case_id=args.case_id,
        case_number=args.case_number,
        status=args.status,
        limit=args.limit,
    )
    if not cases:
        print(json.dumps({"ok": False, "error": "No cases found"}, indent=2))
        return 1

    account_audits = None
    if args.account_audit:
        from account_audit import audit_case, summarize_audits  # noqa: WPS433

        query_fn = lambda soql: sf_query(soql, org=args.org)  # noqa: E731
        audits = [audit_case(case, query_fn) for case in cases]
        account_audits = summarize_audits(audits)

    operator = operator_email()
    token = instance_url = None
    if execute:
        token, instance_url = sf_auth(args.org)

    report = {
        "mode": "dry-run" if dry_run else "execute",
        "org": args.org,
        "operator_email": operator,
        "cases_scanned": len(cases),
        "lookback_days": args.days,
        "account_audit": account_audits,
        "cases": [],
        "summary": {"matched_messages": 0, "synced": 0, "errors": 0},
    }

    for case in cases:
        plan = plan_case(case, args.sr, args.days)
        case_id = case["Id"]
        titles = case_file_titles(case_id, args.org)
        msg_ids = case_message_identifiers(case_id, args.org)
        work_dir = args.work_dir / f"case-{plan['case_number']}"
        sync_results: list[dict] = []

        for msg in plan["matched_messages"]:
            report["summary"]["matched_messages"] += 1
            try:
                sync_results.append(
                    sync_message(
                        case=case,
                        msg_summary=msg,
                        titles=titles,
                        msg_ids=msg_ids,
                        org=args.org,
                        work_dir=work_dir,
                        execute=execute,
                        skip_email_message=args.skip_email_message,
                        token=token,
                        instance_url=instance_url,
                        operator=operator,
                    )
                )
                if execute:
                    report["summary"]["synced"] += 1
            except Exception as exc:  # noqa: BLE001 - report per-message failures
                report["summary"]["errors"] += 1
                sync_results.append(
                    {"subject": msg.get("subject"), "errors": [str(exc)], "actions": ["failed"]}
                )

        plan["sync_results"] = sync_results
        report["cases"].append(plan)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if not args.quiet:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
