#!/usr/bin/env python3
"""Export Crystal's priority-mail unread JSON (Inbox + named boxes)."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, tzinfo
from pathlib import Path
from typing import Any

try:
    from zoneinfo import ZoneInfo

    TZ = ZoneInfo("America/Chicago")
except Exception:

    class _USCentralFallback(tzinfo):
        def utcoffset(self, dt: datetime | None) -> timedelta:
            return timedelta(hours=-5)

        def dst(self, dt: datetime | None) -> timedelta:
            return timedelta(0)

        def tzname(self, dt: datetime | None) -> str:
            return "CDT"

    TZ = _USCentralFallback()

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
REPO_ROOT = SKILL_ROOT.parents[2]
GRAPH_JS = SCRIPT_DIR / "graph_unread_mail.mjs"
OUTPUT_DIR = REPO_ROOT / ".tmp" / "mothman-priority-mail"

NOISE_ADDR = {
    "noreply@vixxo.com",
    "please-reply@info.navan.com",
    "hi@cursor.com",
    "quickbooks@notification.intuit.com",
}
NOISE_NAME_SUB = ("affordable solutions by brian",)
NOISE_SUBJECT_SUB = (
    "message from 2nd floor",
    "complete your profile",
    "you now have access to",
    "finish your payment to affordable",
    "new payment request from affordable",
    "reminder: invoice",
    "estimate from affordable",
)
CLOSED_SUB = (
    "high fives",
    "that works fantastic",
    "gracias",
    "we can work with that",
    "approved.  thanks",
    "approved. thanks",
)
ASK_RE = re.compile(
    r"\b(please|can you|could you|need you|need to have|attached is|"
    r"transferred to you|past due|when (to|should)|start submitting|"
    r"revised contract|welcome to vixxo|coverage|zip code)\b",
    re.I,
)
URGENT_RE = re.compile(
    r"\b(urgent|past due|same.?day|blocking|will not accept work|"
    r"payment issues|payment state|transferred to you)\b",
    re.I,
)


def _addr(msg: dict) -> str:
    return ((msg.get("from") or {}).get("emailAddress") or {}).get("address") or ""


def _from_name(msg: dict) -> str:
    return ((msg.get("from") or {}).get("emailAddress") or {}).get("name") or ""


def _parse_dt(iso: str | None) -> datetime | None:
    if not iso:
        return None
    raw = iso.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)


def _fmt_local(iso: str | None) -> str:
    dt = _parse_dt(iso)
    if not dt:
        return iso or ""
    return f"{dt.strftime('%b')} {dt.day}, {dt.strftime('%I:%M %p').lstrip('0')} CT"


def _is_noise(msg: dict) -> bool:
    addr = _addr(msg).lower()
    name = _from_name(msg).lower()
    subj = (msg.get("subject") or "").lower()
    if addr in NOISE_ADDR:
        return True
    if any(s in name for s in NOISE_NAME_SUB):
        return True
    if any(s in subj for s in NOISE_SUBJECT_SUB):
        return True
    return False


def _looks_closed(msg: dict) -> bool:
    blob = f"{msg.get('subject') or ''} {msg.get('bodyPreview') or ''}".lower()
    return any(s in blob for s in CLOSED_SUB)


def classify(msg: dict, today: date) -> dict[str, Any]:
    dt = _parse_dt(msg.get("receivedDateTime"))
    age = (today - dt.date()).days if dt else 999
    preview = (msg.get("bodyPreview") or "").replace("\r", " ").replace("\n", " ")
    preview = re.sub(r"\s+", " ", preview).strip()
    blob = f"{msg.get('subject') or ''} {preview}"
    importance = (msg.get("importance") or "normal").lower()
    noise = _is_noise(msg)
    ask = bool(ASK_RE.search(blob))
    urgent_lang = bool(URGENT_RE.search(blob))
    receipt_only = bool(re.search(r"^receipt\s*#", msg.get("subject") or "", re.I))

    if noise:
        urgency, tag, status = "archive", "FYI", "Archive"
    elif receipt_only:
        urgency, tag, status = "fyi", "FYI", "Open"
    elif _looks_closed(msg) and not ask:
        urgency, tag, status = "fyi", "FYI", "Closed"
    elif (urgent_lang or (importance == "high" and ask)) and age <= 14:
        urgency, tag, status = "urgent", "Ask", "Open"
    elif ask and age <= 0:
        urgency, tag, status = "urgent", "Ask", "Open"
    elif ask and age <= 2:
        urgency, tag, status = "today", "Ask", "Open"
    elif ask and age <= 21:
        urgency, tag, status = "this_week", "Ask", "Open"
    elif ask:
        urgency, tag, status = "this_week", "Ask", "Stale"
    elif age <= 2 and not noise:
        urgency, tag, status = "today", "FYI", "Open"
    elif age > 21:
        urgency, tag, status = "fyi", "FYI", "Stale"
    else:
        urgency, tag, status = "fyi", "FYI", "Open"

    snippet = preview[:220]
    return {
        "id": msg.get("id"),
        "subject": msg.get("subject") or "(no subject)",
        "from_name": _from_name(msg) or _addr(msg),
        "from_address": _addr(msg),
        "received": _fmt_local(msg.get("receivedDateTime")),
        "received_iso": msg.get("receivedDateTime"),
        "age_days": age,
        "has_attachments": bool(msg.get("hasAttachments")),
        "importance": importance,
        "conversation_id": msg.get("conversationId"),
        "web_link": msg.get("webLink"),
        "preview": snippet,
        "urgency": urgency,
        "tag": tag,
        "status": status,
        "noise": noise,
    }


def _collapse_noise(items: list[dict]) -> tuple[list[dict], list[dict]]:
    noise = [i for i in items if i.get("noise")]
    live = [i for i in items if not i.get("noise")]
    groups: dict[str, list[dict]] = {}
    for n in noise:
        key = (n.get("from_address") or n.get("from_name") or "noise").lower()
        groups.setdefault(key, []).append(n)
    collapsed = []
    for key, rows in groups.items():
        first, last = rows[0], rows[-1]
        collapsed.append(
            {
                "from_name": first.get("from_name"),
                "from_address": first.get("from_address"),
                "count": len(rows),
                "first_received": first.get("received"),
                "last_received": last.get("received"),
                "sample_subject": first.get("subject"),
            }
        )
    return live, collapsed


def _first_moves(priority: list[dict]) -> list[str]:
    moves = []
    for item in priority[:5]:
        moves.append(
            f"{item['urgency'].replace('_', ' ').title()}: "
            f"{item['from_name']} — {item['subject'][:90]}"
        )
    if not moves:
        moves.append("No urgent/today asks in the four boxes.")
    return moves


def build_payload(raw: dict[str, Any], as_of: datetime) -> dict[str, Any]:
    today = as_of.date()
    boxes_out = []
    all_priority: list[dict] = []
    unread_total = 0
    for box in raw.get("boxes") or []:
        classified = [classify(m, today) for m in box.get("messages") or []]
        live, noise_groups = _collapse_noise(classified)
        unread_total += len(classified)
        for item in live:
            item["folder"] = box.get("label")
            item["folder_path"] = box.get("folder_path") or box.get("label")
            if item["urgency"] in ("urgent", "today", "this_week"):
                all_priority.append(item)
        boxes_out.append(
            {
                "id": box.get("id"),
                "label": box.get("label"),
                "found": box.get("found", False),
                "folder_name": box.get("folder_name"),
                "folder_path": box.get("folder_path"),
                "unread_count": len(classified),
                "unread_folder_count": box.get("unread_folder_count"),
                "error": box.get("error"),
                "items": classified,
                "noise_groups": noise_groups,
            }
        )

    rank = {"urgent": 0, "today": 1, "this_week": 2}
    all_priority.sort(
        key=lambda x: (
            rank.get(x["urgency"], 9),
            x.get("received_iso") or "",
        )
    )
    counts = {
        "urgent": sum(1 for i in all_priority if i["urgency"] == "urgent"),
        "today": sum(1 for i in all_priority if i["urgency"] == "today"),
        "this_week": sum(1 for i in all_priority if i["urgency"] == "this_week"),
    }
    return {
        "report_kind": "priority_mail_review",
        "date": today.isoformat(),
        "date_label": as_of.strftime("%A, %B %d, %Y").replace(" 0", " "),
        "generated_at": as_of.strftime("%Y-%m-%d %H:%M %Z"),
        "timezone": "America/Chicago",
        "lead": (
            f"{unread_total} unread across the four boxes · "
            f"{counts['urgent']} urgent · {counts['today']} today · "
            f"{counts['this_week']} this week."
        ),
        "summary": {
            "unread_total": unread_total,
            "priority_count": len(all_priority),
            **counts,
            "boxes": {
                b["id"]: b["unread_count"] for b in boxes_out
            },
        },
        "first_moves": _first_moves(all_priority),
        "priority_items": all_priority,
        "boxes": boxes_out,
    }


def run_graph(extra_folders: list[str], max_per: int) -> dict[str, Any]:
    cmd = ["node", str(GRAPH_JS), "--max", str(max_per)]
    for name in extra_folders:
        cmd.extend(["--extra-folder", name])
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(err or f"graph_unread_mail.mjs exited {proc.returncode}")
    return json.loads(proc.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export priority mail JSON")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--render", action="store_true", help="Also write HTML")
    parser.add_argument("--open", action="store_true", help="Render HTML and open Chrome")
    parser.add_argument("--max", type=int, default=120)
    parser.add_argument("--extra-folder", action="append", default=[])
    args = parser.parse_args()

    as_of = datetime.now(TZ)
    raw = run_graph(args.extra_folder, args.max)
    payload = build_payload(raw, as_of)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_json = OUTPUT_DIR / f"priority-mail-{payload['date']}.json"
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    html_path = None
    if args.render or args.open:
        render = SCRIPT_DIR / "render_priority_mail_html.py"
        cmd = [sys.executable, str(render), str(out_json)]
        if args.open:
            cmd.append("--open")
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr or proc.stdout or "render failed")
        html_path = proc.stdout.strip().splitlines()[-1] if proc.stdout else None

    summary = {
        "ok": True,
        "path": str(out_json),
        "html": html_path,
        "summary": payload["summary"],
        "lead": payload["lead"],
    }
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(out_json)
        if html_path:
            print(html_path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        raise SystemExit(1)
