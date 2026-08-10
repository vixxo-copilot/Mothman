#!/usr/bin/env python3
"""Crystal daily ops report — SF queue + Outlook + Teams, 5-day DoD HTML.

Stdlib only. See SKILL.md and reference.md in the parent skill folder.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parents[2]
SNAPSHOT_ROOT = SKILL_ROOT / "snapshots"
OUTPUT_ROOT = REPO_ROOT / ".tmp" / "mothman-daily-ops"
GM_DIR = REPO_ROOT / ".tmp" / "mothman-good-morning"

OWNER_EMAIL = "Crystal.Gagner@vixxo.com"
SF_ORG = "vixxo"
VIXXO_DOMAIN = "vixxo.com"
GRAPH = "https://graph.microsoft.com/v1.0"

try:
    from zoneinfo import ZoneInfo

    TZ = ZoneInfo("America/Chicago")
except Exception:
    TZ = timezone(timedelta(hours=-5), name="America/Chicago")


def _die(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def now_local() -> datetime:
    return datetime.now(TZ)


def day_bounds_utc(d: date) -> tuple[datetime, datetime]:
    start_local = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=TZ)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def rolling_days(end: date, count: int) -> list[date]:
    return [end - timedelta(days=i) for i in range(count - 1, -1, -1)]


def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def snapshot_dir(d: date) -> Path:
    return SNAPSHOT_ROOT / d.isoformat()


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def captured_at() -> str:
    return now_local().isoformat(timespec="seconds")


# ── Salesforce ──────────────────────────────────────────────────────────────


def sf_path() -> str:
    env = os.environ.get("SF_CLI_PATH", "").strip()
    if env:
        return env
    npm_sf = Path(os.environ.get("APPDATA", "")) / "npm" / "sf.cmd"
    if npm_sf.is_file():
        return str(npm_sf)
    return "sf"


def sf_query(soql: str) -> list[dict[str, Any]]:
    cmd = [sf_path(), "data", "query", "--query", soql, "--target-org", SF_ORG, "--json"]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    try:
        data = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"sf query JSON error: {exc}\n{proc.stdout[:400]}") from exc
    if proc.returncode != 0 or data.get("status", 0) != 0:
        raise RuntimeError(data.get("message") or proc.stderr or proc.stdout[:500])
    return ((data.get("result") or {}).get("records") or [])


def resolve_owner_id() -> str:
    soql = (
        "SELECT Id, Name, Email FROM User "
        f"WHERE Email = '{OWNER_EMAIL}' AND IsActive = true LIMIT 1"
    )
    rows = sf_query(soql)
    if not rows:
        _die(f"No active Salesforce user for {OWNER_EMAIL}")
    return rows[0]["Id"]


def _type_name(rec: dict[str, Any]) -> str:
    rt = rec.get("RecordType") or {}
    name = rt.get("Name") if isinstance(rt, dict) else None
    return name or "(none)"


def _bucket_by_type(records: list[dict[str, Any]]) -> dict[str, int]:
    c: Counter[str] = Counter(_type_name(r) for r in records)
    return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def _bucket_by_status(records: list[dict[str, Any]]) -> dict[str, int]:
    c: Counter[str] = Counter((r.get("Status") or "(none)") for r in records)
    return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def good_morning_json_paths(d: date) -> list[tuple[str, Path]]:
    """Prefer afternoon snapshot, then morning (same dir as mothman-good-morning)."""
    iso = d.isoformat()
    return [
        ("afternoon", GM_DIR / f"data-afternoon-{iso}.json"),
        ("morning", GM_DIR / f"data-{iso}.json"),
    ]


def open_from_good_morning(d: date) -> tuple[dict[str, Any], str] | None:
    """Build an open-Cases block from Good Morning / Afternoon JSON if present."""
    for kind, path in good_morning_json_paths(d):
        data = load_json(path)
        if not data:
            continue
        sf = data.get("salesforce") or {}
        snap = data.get("metrics_snapshot") or {}
        cases = sf.get("cases")
        if cases is None:
            cases = snap.get("salesforce_cases")
        if cases is None:
            continue
        try:
            total = int(cases)
        except (TypeError, ValueError):
            continue

        by_type: dict[str, int] = {}
        by_status: Counter[str] = Counter()
        for ct in sf.get("case_types") or []:
            if not isinstance(ct, dict):
                continue
            label = (ct.get("record_type") or ct.get("label") or "(none)").strip()
            try:
                n = int(ct.get("total") or 0)
            except (TypeError, ValueError):
                n = 0
            if label and n:
                by_type[label] = by_type.get(label, 0) + n
            for st, cnt in (ct.get("status_breakdown") or {}).items():
                try:
                    by_status[str(st)] += int(cnt)
                except (TypeError, ValueError):
                    continue

        # Prefer case_types sum when it matches; otherwise keep GM cases total
        type_sum = sum(by_type.values())
        if type_sum and type_sum != total:
            # Keep GM cases total as source of truth; still show type breakdown
            pass

        block = {
            "total": total,
            "by_type": dict(sorted(by_type.items(), key=lambda kv: (-kv[1], kv[0]))),
            "by_status": dict(sorted(by_status.items(), key=lambda kv: (-kv[1], kv[0]))),
            "point_in_time": True,
            "source": f"good-{kind}",
            "source_path": str(path.as_posix()),
        }
        return block, kind
    return None


def ensure_sf_open(
    snap: dict[str, Any],
    d: date,
    *,
    persist: bool = True,
) -> dict[str, Any]:
    """Attach open Cases from GM/GA when missing; optionally rewrite salesforce.json."""
    if snap.get("open") and snap["open"].get("total") is not None:
        return snap
    filled = open_from_good_morning(d)
    if not filled:
        return snap
    block, kind = filled
    snap = dict(snap)
    snap["open"] = block
    if persist:
        path = snapshot_dir(d) / "salesforce.json"
        write_json(path, snap)
        print(f"SF open backfill {d.isoformat()} from good-{kind}")
    return snap


def fetch_salesforce_day(owner_id: str, d: date, *, include_open: bool) -> dict[str, Any]:
    start, end = day_bounds_utc(d)
    start_s, end_s = iso_z(start), iso_z(end)

    closed = sf_query(
        "SELECT Id, CaseNumber, Status, RecordType.Name, ClosedDate FROM Case "
        f"WHERE OwnerId = '{owner_id}' AND IsClosed = true "
        f"AND ClosedDate >= {start_s} AND ClosedDate < {end_s}"
    )
    created = sf_query(
        "SELECT Id, CaseNumber, Status, RecordType.Name, CreatedDate FROM Case "
        f"WHERE OwnerId = '{owner_id}' "
        f"AND CreatedDate >= {start_s} AND CreatedDate < {end_s}"
    )

    open_block: dict[str, Any] | None = None
    if include_open:
        open_recs = sf_query(
            "SELECT Id, CaseNumber, Status, RecordType.Name FROM Case "
            f"WHERE OwnerId = '{owner_id}' AND IsClosed = false"
        )
        open_block = {
            "total": len(open_recs),
            "by_type": _bucket_by_type(open_recs),
            "by_status": _bucket_by_status(open_recs),
            "point_in_time": True,
            "source": "live",
        }

    payload: dict[str, Any] = {
        "day": d.isoformat(),
        "captured_at": captured_at(),
        "source": "salesforce",
        "closed": {"total": len(closed), "by_type": _bucket_by_type(closed)},
        "new": {"total": len(created), "by_type": _bucket_by_type(created)},
    }
    if open_block is not None:
        payload["open"] = open_block
    elif (existing := load_json(snapshot_dir(d) / "salesforce.json")) and existing.get("open"):
        payload["open"] = existing["open"]
    else:
        filled = open_from_good_morning(d)
        if filled:
            payload["open"] = filled[0]
    return payload


# ── Microsoft Graph ─────────────────────────────────────────────────────────


def _read_env_file_token(name: str) -> str:
    env_path = REPO_ROOT / ".env"
    if not env_path.is_file():
        return ""
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith(f"{name}="):
            continue
        val = line.split("=", 1)[1].strip().strip('"').strip("'")
        if val.lower().startswith("bearer "):
            val = val[7:].strip()
        return val
    return ""


def get_graph_token() -> str:
    for key in ("MS_GRAPH_ACCESS_TOKEN", "MS365_MCP_OAUTH_TOKEN"):
        val = os.environ.get(key, "").strip()
        if val.lower().startswith("bearer "):
            val = val[7:].strip()
        if val:
            return val
        val = _read_env_file_token(key)
        if val:
            return val
    return ""


def graph_get(token: str, path: str) -> dict[str, Any]:
    url = path if path.startswith("http") else f"{GRAPH}{path}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Graph HTTP {exc.code}: {err[:400]}") from exc


def graph_count_collection(token: str, path: str) -> int:
    """Page a Graph collection and count items (id-only select preferred)."""
    total = 0
    url = path if path.startswith("http") else f"{GRAPH}{path}"
    while url:
        data = graph_get(token, url)
        items = data.get("value") or []
        total += len(items)
        url = data.get("@odata.nextLink") or ""
        if total > 5000:
            break
    return total


def fetch_outlook_day(token: str, d: date, *, include_unread: bool) -> dict[str, Any]:
    start, end = day_bounds_utc(d)
    start_s, end_s = iso_z(start), iso_z(end)
    recv_filter = (
        f"receivedDateTime ge {start_s} and receivedDateTime lt {end_s}"
    )
    sent_filter = f"sentDateTime ge {start_s} and sentDateTime lt {end_s}"
    recv_path = (
        "/me/mailFolders/inbox/messages?"
        + urllib.parse.urlencode(
            {
                "$filter": recv_filter,
                "$select": "id",
                "$top": "50",
            }
        )
    )
    sent_path = (
        "/me/mailFolders/sentitems/messages?"
        + urllib.parse.urlencode(
            {
                "$filter": sent_filter,
                "$select": "id",
                "$top": "50",
            }
        )
    )
    received = graph_count_collection(token, recv_path)
    sent = graph_count_collection(token, sent_path)
    unread: int | None = None
    if include_unread:
        # Count unread in Inbox (point-in-time)
        unread_path = (
            "/me/mailFolders/inbox/messages?"
            + urllib.parse.urlencode(
                {
                    "$filter": "isRead eq false",
                    "$select": "id",
                    "$top": "50",
                }
            )
        )
        unread = graph_count_collection(token, unread_path)

    return {
        "day": d.isoformat(),
        "captured_at": captured_at(),
        "source": "outlook",
        "received": received,
        "sent": sent,
        "unread": unread,
        "notes": "",
    }


def _msg_day_chicago(iso_ts: str | None) -> date | None:
    if not iso_ts:
        return None
    try:
        # Graph returns Z or offset
        if iso_ts.endswith("Z"):
            dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(iso_ts)
        return dt.astimezone(TZ).date()
    except ValueError:
        return None


def _sender_domain(msg: dict[str, Any]) -> str:
    frm = msg.get("from") or {}
    email_addr = ((frm.get("emailAddress") or {}).get("address") or "").lower()
    if "@" in email_addr:
        return email_addr.split("@", 1)[1]
    user = (frm.get("user") or {}) if isinstance(frm, dict) else {}
    # Some payloads nest differently
    return ""


def _from_user_id(msg: dict[str, Any]) -> str:
    frm = msg.get("from") or {}
    user = frm.get("user") or {}
    if isinstance(user, dict) and user.get("id"):
        return str(user["id"])
    return ""


def fetch_teams_window(token: str, days: list[date]) -> dict[date, dict[str, Any]]:
    """Sample recent chats once; bucket metrics per day in the window."""
    me = graph_get(token, "/me?$select=id,mail,userPrincipalName")
    me_id = str(me.get("id") or "")
    day_set = set(days)
    window_start = day_bounds_utc(days[0])[0]

    acc: dict[date, dict[str, Any]] = {
        d: {
            "day": d.isoformat(),
            "captured_at": captured_at(),
            "source": "teams",
            "messages_from_me": 0,
            "messages_from_others": 0,
            "replies_from_me": 0,
            "chats_active": 0,
            "internal_from_others": 0,
            "external_from_others": 0,
            "chats_sampled": 0,
            "notes": "Proxies from recent chats; not a full tenant export.",
        }
        for d in days
    }

    chats_path = (
        "/me/chats?"
        + urllib.parse.urlencode(
            {
                "$top": "50",
                "$expand": "lastMessagePreview",
            }
        )
    )
    chats: list[dict[str, Any]] = []
    pages = 0
    next_url: str | None = chats_path
    while next_url and pages < 3:
        data = graph_get(token, next_url)
        chats.extend(data.get("value") or [])
        next_url = data.get("@odata.nextLink")
        pages += 1

    chats_examined = 0
    for chat in chats:
        chat_id = chat.get("id")
        if not chat_id:
            continue
        preview = chat.get("lastMessagePreview") or {}
        preview_ts = preview.get("createdDateTime")
        preview_day = _msg_day_chicago(preview_ts)
        # Skip chats with no activity in/near window when we can tell
        if preview_day is not None and preview_day < days[0] - timedelta(days=1):
            continue

        msg_path = (
            f"/me/chats/{urllib.parse.quote(chat_id)}/messages?"
            + urllib.parse.urlencode({"$top": "50"})
        )
        try:
            msg_data = graph_get(token, msg_path)
        except RuntimeError as exc:
            print(f"WARN: teams chat {chat_id[:24]}…: {exc}", file=sys.stderr)
            continue

        messages = msg_data.get("value") or []
        chats_examined += 1

        active_days: set[date] = set()
        for msg in messages:
            # Skip system / empty
            msg_type = (msg.get("messageType") or "message").lower()
            if msg_type not in ("message",):
                continue
            day = _msg_day_chicago(msg.get("createdDateTime") or msg.get("lastModifiedDateTime"))
            if day is None or day not in day_set:
                continue
            # Also skip messages before window start in UTC for safety
            created = msg.get("createdDateTime")
            if created:
                try:
                    cdt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    if cdt < window_start - timedelta(days=1):
                        continue
                except ValueError:
                    pass

            active_days.add(day)
            uid = _from_user_id(msg)
            if me_id and uid == me_id:
                acc[day]["messages_from_me"] = int(acc[day]["messages_from_me"]) + 1
                if msg.get("replyToId"):
                    acc[day]["replies_from_me"] = int(acc[day]["replies_from_me"]) + 1
            else:
                acc[day]["messages_from_others"] = int(acc[day]["messages_from_others"]) + 1
                domain = _sender_domain(msg)
                if domain == VIXXO_DOMAIN:
                    acc[day]["internal_from_others"] = int(acc[day]["internal_from_others"]) + 1
                elif domain:
                    acc[day]["external_from_others"] = int(acc[day]["external_from_others"]) + 1

        for day in active_days:
            acc[day]["chats_active"] = int(acc[day]["chats_active"]) + 1

    for d in days:
        acc[d]["chats_sampled"] = chats_examined

    return acc


# ── Collect / merge ─────────────────────────────────────────────────────────


def write_manifest(d: date, sources: list[str]) -> None:
    write_json(
        snapshot_dir(d) / "manifest.json",
        {
            "day": d.isoformat(),
            "captured_at": captured_at(),
            "sources": sources,
            "owner_email": OWNER_EMAIL,
        },
    )


def collect_day(
    d: date,
    *,
    today: date,
    owner_id: str | None,
    graph_token: str,
    use_sf: bool,
    use_outlook: bool,
    use_teams: bool,
    refresh: bool,
    teams_cache: dict[date, dict[str, Any]] | None,
) -> dict[str, Any]:
    """Return keys: salesforce, outlook, teams (dicts)."""
    out: dict[str, Any] = {}
    sources: list[str] = []
    sdir = snapshot_dir(d)
    is_today = d == today

    if use_sf:
        path = sdir / "salesforce.json"
        existing = None if refresh else load_json(path)
        need_open = is_today and (refresh or not (existing or {}).get("open"))
        if existing and not refresh and (not is_today or existing.get("open")):
            snap = ensure_sf_open(existing, d, persist=True)
            out["salesforce"] = snap
            src = "salesforce(cache)"
            if (snap.get("open") or {}).get("source", "").startswith("good-"):
                src = f"salesforce(cache+{(snap.get('open') or {}).get('source')})"
            sources.append(src)
        else:
            if not owner_id:
                _die("Salesforce owner id missing")
            print(f"SF fetch {d.isoformat()} …")
            snap = fetch_salesforce_day(owner_id, d, include_open=is_today or need_open)
            if not snap.get("open") and existing and existing.get("open"):
                snap["open"] = existing["open"]
            snap = ensure_sf_open(snap, d, persist=False)
            write_json(path, snap)
            out["salesforce"] = snap
            sources.append("salesforce")

    if use_outlook:
        path = sdir / "outlook.json"
        existing = None if refresh else load_json(path)
        if existing and not refresh and (not is_today or existing.get("received") is not None):
            out["outlook"] = existing
            sources.append("outlook(cache)")
        elif graph_token:
            print(f"Outlook fetch {d.isoformat()} …")
            try:
                snap = fetch_outlook_day(graph_token, d, include_unread=is_today)
                write_json(path, snap)
                out["outlook"] = snap
                sources.append("outlook")
            except RuntimeError as exc:
                print(f"WARN: Outlook {d}: {exc}", file=sys.stderr)
                if existing:
                    out["outlook"] = existing
                    sources.append("outlook(cache-fallback)")
                else:
                    out["outlook"] = {
                        "day": d.isoformat(),
                        "captured_at": captured_at(),
                        "source": "outlook",
                        "received": None,
                        "sent": None,
                        "unread": None,
                        "notes": f"fetch failed: {exc}",
                    }
                    write_json(path, out["outlook"])
                    sources.append("outlook(error)")
        else:
            if existing:
                out["outlook"] = existing
                sources.append("outlook(cache)")
            else:
                stub = {
                    "day": d.isoformat(),
                    "captured_at": captured_at(),
                    "source": "outlook",
                    "received": None,
                    "sent": None,
                    "unread": None,
                    "notes": "No Graph token; fill via MS365 MCP (see reference.md).",
                }
                write_json(path, stub)
                out["outlook"] = stub
                sources.append("outlook(stub)")

    if use_teams:
        path = sdir / "teams.json"
        existing = None if refresh else load_json(path)
        if existing and not refresh:
            out["teams"] = existing
            sources.append("teams(cache)")
        elif teams_cache and d in teams_cache:
            snap = teams_cache[d]
            write_json(path, snap)
            out["teams"] = snap
            sources.append("teams")
        elif existing:
            out["teams"] = existing
            sources.append("teams(cache)")
        else:
            stub = {
                "day": d.isoformat(),
                "captured_at": captured_at(),
                "source": "teams",
                "messages_from_me": None,
                "messages_from_others": None,
                "replies_from_me": None,
                "chats_active": None,
                "internal_from_others": None,
                "external_from_others": None,
                "chats_sampled": 0,
                "notes": "No Graph token / Teams fetch; fill via MS365 MCP.",
            }
            write_json(path, stub)
            out["teams"] = stub
            sources.append("teams(stub)")

    write_manifest(d, sources)
    return out


# ── HTML ────────────────────────────────────────────────────────────────────


def _fmt(val: Any) -> str:
    if val is None:
        return "—"
    return str(val)


def _delta_cell(cur: Any, prev: Any) -> tuple[str, str]:
    if cur is None or prev is None:
        return "—", ""
    try:
        d = int(cur) - int(prev)
    except (TypeError, ValueError):
        return "—", ""
    if d > 0:
        return f"+{d}", "pos"
    if d < 0:
        return str(d), "neg"
    return "0", ""


def _metric(day_data: dict[str, Any], path: str) -> Any:
    cur: Any = day_data
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def render_html(
    days: list[date],
    day_data: dict[date, dict[str, Any]],
    out_path: Path,
) -> None:
    labels = [d.isoformat() for d in days]
    sections: list[tuple[str, list[tuple[str, str]]]] = [
        (
            "Salesforce — Open (point-in-time)",
            [("Open cases", "salesforce.open.total")],
        ),
        (
            "Salesforce — Closed that day",
            [("Closed", "salesforce.closed.total")],
        ),
        (
            "Salesforce — New that day",
            [("Created", "salesforce.new.total")],
        ),
        (
            "Outlook",
            [
                ("Received", "outlook.received"),
                ("Sent", "outlook.sent"),
                ("Unread (as-of)", "outlook.unread"),
            ],
        ),
        (
            "Teams chat (proxies)",
            [
                ("From me", "teams.messages_from_me"),
                ("From others", "teams.messages_from_others"),
                ("Replies from me", "teams.replies_from_me"),
                ("Chats active", "teams.chats_active"),
                ("Internal (others)", "teams.internal_from_others"),
                ("External (others)", "teams.external_from_others"),
            ],
        ),
    ]

    parts: list[str] = []
    parts.append("<!DOCTYPE html><html><head><meta charset='utf-8'>")
    parts.append("<title>Daily Ops Report — Crystal</title>")
    parts.append(
        "<style>"
        "body{font-family:Segoe UI,Arial,sans-serif;margin:24px 96px 72px 96px;"
        "color:#1f3d3d;background:#ffffff;}"
        "h1,h2,h3{color:#0f6664;} table{border-collapse:collapse;width:100%;margin:12px 0 28px;}"
        "th,td{border:1px solid #1a3333;padding:6px 8px;text-align:right;"
        "font-variant-numeric:tabular-nums;}"
        "th{font-size:15px;background:#0f6664;color:#f5fffe;font-weight:700;}"
        "td{font-size:15px;background:#ffffff;}"
        "td:first-child,th:first-child{text-align:left;}"
        "td:first-child{font-weight:700;background:#c5e0e0;}"
        ".pos{background:#e57373;color:#ffffff;}"
        ".neg{background:#66bb6a;color:#ffffff;}"
        ".meta{color:#4d7373;font-size:14px;}"
        ".note{color:#4d7373;font-size:13px;margin-top:-12px;}"
        "tr.total td{background:#c5e0e0;font-weight:700;}"
        "</style></head><body>"
    )
    today = days[-1]
    yday = days[-2] if len(days) > 1 else None
    parts.append("<h1>Daily Ops Report — Crystal Gagner</h1>")
    parts.append(
        f"<p class='meta'>Generated {html.escape(now_local().strftime('%Y-%m-%d %H:%M %Z'))}"
        f" · Window {labels[0]} → {labels[-1]} (America/Chicago)"
        f" · Owner {html.escape(OWNER_EMAIL)}</p>"
    )

    # Headline DoD
    parts.append("<h2>Today vs yesterday</h2>")
    parts.append("<table><tr><th>Metric</th><th>Yesterday</th><th>Today</th><th>Δ</th></tr>")
    headline = [
        ("SF open", "salesforce.open.total"),
        ("SF closed", "salesforce.closed.total"),
        ("SF new", "salesforce.new.total"),
        ("Mail received", "outlook.received"),
        ("Mail sent", "outlook.sent"),
        ("Teams from me", "teams.messages_from_me"),
        ("Teams chats active", "teams.chats_active"),
    ]
    for label, path in headline:
        cur = _metric(day_data.get(today, {}), path)
        prev = _metric(day_data.get(yday, {}), path) if yday else None
        dtxt, dcls = _delta_cell(cur, prev)
        parts.append(
            "<tr>"
            f"<td>{html.escape(label)}</td>"
            f"<td>{html.escape(_fmt(prev))}</td>"
            f"<td>{html.escape(_fmt(cur))}</td>"
            f"<td class='{dcls}'>{html.escape(dtxt)}</td>"
            "</tr>"
        )
    parts.append("</table>")

    for title, rows in sections:
        parts.append(f"<h2>{html.escape(title)}</h2>")
        parts.append("<table><tr><th>Metric</th>")
        for lab in labels:
            parts.append(f"<th>{html.escape(lab)}</th><th>Δ</th>")
        parts.append("</tr>")
        for row_label, path in rows:
            parts.append(f"<tr><td>{html.escape(row_label)}</td>")
            prev_val: Any = None
            for i, d in enumerate(days):
                val = _metric(day_data.get(d, {}), path)
                parts.append(f"<td>{html.escape(_fmt(val))}</td>")
                if i == 0:
                    parts.append("<td>—</td>")
                else:
                    dtxt, dcls = _delta_cell(val, prev_val)
                    parts.append(f"<td class='{dcls}'>{html.escape(dtxt)}</td>")
                prev_val = val
            parts.append("</tr>")
        parts.append("</table>")

    # Type breakdown for today SF
    sf_today = (day_data.get(today) or {}).get("salesforce") or {}
    for slice_name, heading in (
        ("open", "Today — open by type"),
        ("closed", "Today — closed by type"),
        ("new", "Today — new by type"),
    ):
        block = sf_today.get(slice_name) or {}
        by_type = block.get("by_type") or {}
        if not by_type:
            continue
        parts.append(f"<h3>{html.escape(heading)}</h3>")
        parts.append("<table><tr><th>Type</th><th>Count</th></tr>")
        for t, n in by_type.items():
            parts.append(
                f"<tr><td>{html.escape(str(t))}</td><td>{html.escape(str(n))}</td></tr>"
            )
        parts.append("</table>")

    parts.append(
        "<p class='note'>Teams figures are activity proxies from recent chats "
        "(not PSTN/Gong). Open SF / unread mail are point-in-time for today; "
        "historical open requires that day’s snapshot.</p>"
    )
    parts.append("</body></html>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(parts), encoding="utf-8")


def load_window_from_snapshots(days: list[date]) -> dict[date, dict[str, Any]]:
    out: dict[date, dict[str, Any]] = {}
    for d in days:
        sdir = snapshot_dir(d)
        out[d] = {}
        for name in ("salesforce", "outlook", "teams"):
            snap = load_json(sdir / f"{name}.json")
            if snap and name == "salesforce":
                snap = ensure_sf_open(snap, d, persist=True)
            if snap:
                out[d][name] = snap
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Crystal daily ops report")
    parser.add_argument("--days", type=int, default=5)
    parser.add_argument("--refresh-all", action="store_true")
    parser.add_argument("--no-salesforce", action="store_true")
    parser.add_argument("--no-outlook", action="store_true")
    parser.add_argument("--no-teams", action="store_true")
    parser.add_argument("--render-only", action="store_true")
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    if args.days < 2:
        _die("--days must be >= 2 for day-over-day")

    today = now_local().date()
    days = rolling_days(today, args.days)
    use_sf = not args.no_salesforce
    use_outlook = not args.no_outlook
    use_teams = not args.no_teams

    if args.render_only:
        day_data = load_window_from_snapshots(days)
    else:
        owner_id = resolve_owner_id() if use_sf else None
        graph_token = get_graph_token() if (use_outlook or use_teams) else ""
        if (use_outlook or use_teams) and not graph_token:
            print(
                "WARN: No Graph token (MS_GRAPH_ACCESS_TOKEN / MS365_MCP_OAUTH_TOKEN). "
                "Outlook/Teams will use cache or stubs — fill via MS365 MCP.",
                file=sys.stderr,
            )

        teams_cache: dict[date, dict[str, Any]] | None = None
        need_teams_live = use_teams and (
            args.refresh_all
            or any(not load_json(snapshot_dir(d) / "teams.json") for d in days)
            or not load_json(snapshot_dir(today) / "teams.json")
        )
        if use_teams and graph_token and (args.refresh_all or need_teams_live):
            print("Teams fetch (window sample) …")
            try:
                teams_cache = fetch_teams_window(graph_token, days)
            except RuntimeError as exc:
                print(f"WARN: Teams window fetch failed: {exc}", file=sys.stderr)
                teams_cache = None

        day_data = {}
        for d in days:
            refresh = args.refresh_all or d == today
            day_data[d] = collect_day(
                d,
                today=today,
                owner_id=owner_id,
                graph_token=graph_token,
                use_sf=use_sf,
                use_outlook=use_outlook,
                use_teams=use_teams,
                refresh=refresh,
                teams_cache=teams_cache,
            )

    out_path = OUTPUT_ROOT / f"daily-ops-{today.isoformat()}.html"
    render_html(days, day_data, out_path)
    print(f"REPORT: {out_path.resolve()}")

    yday = days[-2] if len(days) > 1 else None
    for label, path in (
        ("sf_open", "salesforce.open.total"),
        ("sf_closed", "salesforce.closed.total"),
        ("sf_new", "salesforce.new.total"),
        ("mail_received", "outlook.received"),
        ("mail_sent", "outlook.sent"),
        ("teams_from_me", "teams.messages_from_me"),
        ("teams_chats_active", "teams.chats_active"),
    ):
        cur = _metric(day_data.get(today, {}), path)
        prev = _metric(day_data.get(yday, {}), path) if yday else None
        dtxt, _ = _delta_cell(cur, prev)
        print(f"  {label}: today={_fmt(cur)} yesterday={_fmt(prev)} dod={dtxt}")


if __name__ == "__main__":
    main()
