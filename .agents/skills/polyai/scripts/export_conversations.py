#!/usr/bin/env python3
"""Export all PolyAI conversations to CSV (+ optional JSON)."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import polyai_client  # noqa: E402
from audit_conversation import extract_sr_from_turns  # noqa: E402

EXPORT_METRICS = [
    "VALID_SR",
    "API_OK",
    "TRANSACTION_TYPE",
    "SR_SUBSTATUS",
    "TECHNICIAN_STATUS",
    "UPDATE_ETA_START",
    "UPDATE_ETA_SUCCESSFUL",
    "UPDATE_ETA_ETA_COLLECTED",
    "UPDATE_ETA_DETAILS_CONFIRMED",
    "CALLER_PROVIDED_VALID_ETA",
    "USER_CAN_ASSIST_WITH_SR",
    "USER_CANNOT_ASSIST_WITH_SR",
    "HUMAN_ENCOUNTERED",
    "CALL_ANSWERED_BY",
    "IVR_ENCOUNTERED",
    "IVR_DURATION_EXCEEDED",
    "VOICEMAIL_ENCOUNTERED",
    "OUTBOUND_CALL_STATUS",
    "OUTBOUND_CALL_SIP_CODE",
    "AGENT_FALLBACK",
    "USER_HANGUP",
    "CALL_CONNECTED",
    "OUT_OF_SCOPE_SR",
    "VARIANT_ID",
    "TOTAL_AGENT_TURNS",
    "CALL_COMPLETED",
    "CALL_DURATION",
    "AI_ONLY_CALL_DURATION",
]

BASE_COLUMNS = [
    "project_id",
    "account_id",
    "conversation_id",
    "started_at",
    "started_date",
    "started_hour_utc",
    "duration_sec",
    "num_turns",
    "num_ood",
    "num_silences",
    "variant_name",
    "environment",
    "channel",
    "direction",
    "to_number",
    "handoff",
    "handoff_reason",
    "handoff_destination",
    "in_progress",
    "extracted_sr_number",
    "hangup_category",
    "hangup_reason",
    "last_agent_response",
]


def has_human(metrics: dict) -> bool:
    if metrics.get("HUMAN_ENCOUNTERED"):
        return True
    answered = metrics.get("CALL_ANSWERED_BY")
    if isinstance(answered, list):
        return any(item == "HUMAN" for item in answered)
    return answered == "HUMAN"


def format_metric(metrics: dict, key: str) -> tuple[str, str]:
    value = metrics.get(key)
    if value is None or value == "":
        return "", "N"
    if isinstance(value, list):
        return "; ".join(str(item) for item in value), "Y"
    return str(value), "Y"


def last_agent_response(turns: list[dict]) -> str:
    for turn in reversed(turns or []):
        text = (turn.get("agent_response") or "").strip()
        if text:
            if len(text) > 500:
                return text[:500] + "..."
            return text
    return ""


def hangup_reason_tags(conv: dict, metrics: dict, last_agent: str) -> list[str]:
    tags: list[str] = []
    if (conv.get("num_turns") or 0) == 0:
        tags.append("Zero turns metric")
    if not metrics.get("VALID_SR"):
        tags.append("No VALID_SR")
    if not metrics.get("API_OK"):
        tags.append("No API_OK")
    elif not metrics.get("UPDATE_ETA_SUCCESSFUL") and metrics.get("UPDATE_ETA_START"):
        tags.append("ETA not posted")
    if not has_human(metrics):
        tags.append("No human reached")
    if metrics.get("AGENT_FALLBACK"):
        tags.append("Agent fallback")
    if metrics.get("IVR_DURATION_EXCEEDED"):
        tags.append("IVR timeout")
    sip = str(metrics.get("OUTBOUND_CALL_SIP_CODE") or "")
    status = metrics.get("OUTBOUND_CALL_STATUS") or ""
    if sip == "480":
        tags.append("SIP 480")
    if sip == "486":
        tags.append("SIP 486")
    if status == "Unavailable":
        tags.append("Status=Unavailable")
    if status == "Busy":
        tags.append("Status=Busy")
    lower = last_agent.lower()
    if "wrong number" in lower:
        tags.append("Wrong number apology")
    if "call you back" in lower:
        tags.append("Callback promised")
    if "can't set an eta in the past" in lower or "eta in the past" in lower:
        tags.append("Past ETA rejected")
    if metrics.get("UPDATE_ETA_SUCCESSFUL"):
        tags.append("Normal close with ETA")
    return tags


def voicemail_only(metrics: dict) -> bool:
    answered = metrics.get("CALL_ANSWERED_BY")
    tags = answered if isinstance(answered, list) else ([answered] if answered else [])
    return any(tag == "VOICEMAIL" for tag in tags) and not has_human(metrics)


def hangup_category(conv: dict, metrics: dict, last_agent: str, direction: str) -> str:
    if direction == "inbound" and "wrong number" in last_agent.lower():
        return "Inbound wrong-number test"

    sip = str(metrics.get("OUTBOUND_CALL_SIP_CODE") or "")
    status = metrics.get("OUTBOUND_CALL_STATUS") or ""
    if sip == "480" or status == "Unavailable":
        return "Unreachable (SIP 480)"
    if sip == "486" or status == "Busy":
        return "Other"
    if metrics.get("OUT_OF_SCOPE_SR"):
        return "Out of scope SR"
    if metrics.get("UPDATE_ETA_SUCCESSFUL"):
        return "Success - ETA posted"
    if metrics.get("IVR_DURATION_EXCEEDED"):
        return "IVR timeout"
    if metrics.get("AGENT_FALLBACK") and not (conv.get("total_duration") or 0):
        return "Never connected + fallback"
    if metrics.get("UPDATE_ETA_START") and not metrics.get("UPDATE_ETA_SUCCESSFUL"):
        return "ETA started, not posted"

    duration = conv.get("total_duration") or 0
    if (
        direction == "outbound"
        and duration <= 45
        and not metrics.get("UPDATE_ETA_START")
        and has_human(metrics)
        and not voicemail_only(metrics)
    ):
        return "Hung up early - intro only"
    if metrics.get("API_OK") and not metrics.get("UPDATE_ETA_SUCCESSFUL"):
        return "API_OK but no ETA posted"
    if has_human(metrics) and not metrics.get("API_OK"):
        return "Reached party, no backend write"
    if metrics.get("AGENT_FALLBACK"):
        return "Never connected + fallback"
    return "Other"


def hangup_reason_text(tags: list[str], category: str) -> str:
    if category == "API_OK but no ETA posted" and not tags:
        return "See last_agent_response"
    if category == "API_OK but no ETA posted" and tags == ["Zero turns metric"]:
        return "See last_agent_response"
    if not tags:
        return "See last_agent_response"
    return "; ".join(tags)


def csv_columns() -> list[str]:
    cols = list(BASE_COLUMNS)
    for key in EXPORT_METRICS:
        cols.append(f"metric_{key}")
        cols.append(f"has_{key}")
    return cols


def conversation_row(conv: dict, cfg: dict[str, str]) -> dict:
    metrics = conv.get("metrics") or {}
    turns = conv.get("turns") or []
    started_at = conv.get("started_at") or ""
    started_date = started_at[:10] if len(started_at) >= 10 else ""
    started_hour = started_at[11:13] if len(started_at) >= 13 else ""
    conv_id = conv.get("id") or ""
    direction = "outbound" if conv_id.startswith("OUT-") else "inbound"
    last_agent = last_agent_response(turns)
    tags = hangup_reason_tags(conv, metrics, last_agent)
    category = hangup_category(conv, metrics, last_agent, direction)

    row = {
        "project_id": cfg["POLYAI_PROJECT_ID"],
        "account_id": cfg["POLYAI_ACCOUNT_ID"],
        "conversation_id": conv_id,
        "started_at": started_at,
        "started_date": started_date,
        "started_hour_utc": started_hour,
        "duration_sec": conv.get("total_duration") or 0,
        "num_turns": conv.get("num_turns") or 0,
        "num_ood": conv.get("num_ood") or 0,
        "num_silences": conv.get("num_silences") or 0,
        "variant_name": conv.get("variant_name") or "",
        "environment": conv.get("environment") or "",
        "channel": conv.get("channel") or "",
        "direction": direction,
        "to_number": conv.get("to_number") or "",
        "handoff": conv.get("handoff") or "",
        "handoff_reason": conv.get("handoff_reason") or "",
        "handoff_destination": conv.get("handoff_destination") or "",
        "in_progress": conv.get("in_progress") or False,
        "extracted_sr_number": extract_sr_from_turns(turns) or "",
        "hangup_category": category,
        "hangup_reason": hangup_reason_text(tags, category),
        "last_agent_response": last_agent,
    }

    for key in EXPORT_METRICS:
        value, has_flag = format_metric(metrics, key)
        row[f"metric_{key}"] = value
        row[f"has_{key}"] = has_flag
    return row


def fetch_all(cfg: dict[str, str], page_size: int) -> list[dict]:
    from polyai_fetch import fetch_all_conversations

    return fetch_all_conversations(cfg, page_size=page_size, progress=True)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = csv_columns()
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def export_project(cfg: dict[str, str], output_dir: Path, page_size: int, also_json: bool) -> dict:
    conversations = fetch_all(cfg, page_size)
    rows = [conversation_row(conv, cfg) for conv in conversations]
    rows.sort(key=lambda item: item.get("started_at") or "")

    project_id = cfg["POLYAI_PROJECT_ID"]
    csv_path = output_dir / f"{project_id}-conversations.csv"
    write_csv(csv_path, rows)

    result = {
        "ok": True,
        "project_id": project_id,
        "account_id": cfg["POLYAI_ACCOUNT_ID"],
        "exported_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "row_count": len(rows),
        "csv_path": str(csv_path),
    }

    if also_json:
        json_path = output_dir / f"{project_id}-conversations.json"
        write_json(
            json_path,
            {
                "project_id": project_id,
                "account_id": cfg["POLYAI_ACCOUNT_ID"],
                "exported_at": result["exported_at"],
                "row_count": len(rows),
                "rows": rows,
            },
        )
        result["json_path"] = str(json_path)
    return result


def main() -> int:
    polyai_client.load_dotenv()
    parser = argparse.ArgumentParser(description="Export PolyAI conversations to CSV/JSON")
    parser.add_argument(
        "--output-dir",
        default=str(polyai_client.repo_root() / "exports" / "polyai"),
    )
    parser.add_argument("--page-size", type=int, default=50)
    parser.add_argument("--json", action="store_true", help="Also write JSON export")
    parser.add_argument("--project", help="Single project_id to export")
    parser.add_argument(
        "--all-projects",
        action="store_true",
        help="Export every enabled project in reference/projects.json",
    )
    args = parser.parse_args()

    from polyai_projects import config_for_project, enabled_projects

    output_dir = Path(args.output_dir)
    if args.all_projects:
        project_ids = enabled_projects()
    elif args.project:
        project_ids = [args.project]
    else:
        project_ids = [config_for_project(None)["POLYAI_PROJECT_ID"]]

    results = []
    for project_id in project_ids:
        print(f"Exporting {project_id}...", file=sys.stderr)
        cfg = config_for_project(project_id)
        results.append(export_project(cfg, output_dir, args.page_size, args.json))

    print(json.dumps({"exports": results}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
