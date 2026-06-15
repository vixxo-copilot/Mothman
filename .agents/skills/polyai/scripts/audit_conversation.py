#!/usr/bin/env python3
"""Audit PolyAI conversations — integration signals and redacted turns."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import polyai_client  # noqa: E402

VIXXO_METRIC_KEYS = [
    "VALID_SR",
    "API_OK",
    "SR_SUBSTATUS",
    "TRANSACTION_TYPE",
    "TECHNICIAN_STATUS",
    "UPDATE_ETA_START",
    "UPDATE_ETA_SUCCESSFUL",
    "UPDATE_ETA_ETA_COLLECTED",
    "UPDATE_ETA_DETAILS_CONFIRMED",
    "CALLER_PROVIDED_VALID_ETA",
    "USER_CAN_ASSIST_WITH_SR",
    "IVR_ENCOUNTERED",
    "IVR_DURATION_EXCEEDED",
    "HUMAN_ENCOUNTERED",
    "CALL_ANSWERED_BY",
    "OUTBOUND_CALL_STATUS",
    "AGENT_FALLBACK",
]

SR_SPOKEN_RE = re.compile(
    r"SR number is ['\"]([^'\"]+)['\"]|SR[:\s]+([0-9][0-9\-\s]{6,})",
    re.IGNORECASE,
)
WORD_DIGITS = {
    "zero": "0",
    "oh": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
}


def parse_spoken_sr_clause(text: str) -> str | None:
    lower = text.lower()
    anchor = lower.find("sr number is")
    if anchor < 0:
        return None
    clause = lower[anchor : anchor + 220]
    clause = clause.split("and that's for", 1)[0]
    clause = clause.split("',", 1)[0].replace("'", " ")
    parts: list[str] = []
    for token in re.findall(r"[a-z]+|\d+|dash", clause):
        if token == "dash":
            parts.append("-")
        elif token.isdigit():
            parts.extend(list(token))
        elif token in WORD_DIGITS:
            parts.append(WORD_DIGITS[token])
    digits = re.sub(r"\D", "", "".join(parts))
    if len(digits) >= 8:
        if len(digits) == 11 and digits.startswith("1"):
            return f"1-{digits[1:4]}{digits[4:7]}{digits[7:]}"
        return digits
    return None


def extract_sr_from_turns(turns: list[dict]) -> str | None:
    for turn in turns:
        text = turn.get("agent_response") or ""
        spoken = parse_spoken_sr_clause(text)
        if spoken:
            return spoken
        for match in SR_SPOKEN_RE.finditer(text):
            candidate = match.group(1) or match.group(2) or ""
            digits = re.sub(r"\D", "", candidate)
            if len(digits) >= 8:
                return digits
    return None


def redact_turn(turn: dict) -> dict:
    return {
        "user_input": "[redacted]" if turn.get("user_input") else "",
        "agent_response": (turn.get("agent_response") or "")[:500],
        "user_input_datetime": turn.get("user_input_datetime"),
        "agent_response_datetime": turn.get("agent_response_datetime"),
        "is_ood": turn.get("is_ood"),
        "is_silence": turn.get("is_silence"),
    }


def pick_metrics(metrics: dict) -> dict:
    return {key: metrics[key] for key in VIXXO_METRIC_KEYS if key in metrics}


def score_conversation(conv: dict) -> int:
    metrics = conv.get("metrics") or {}
    score = conv.get("num_turns") or 0
    if metrics.get("HUMAN_ENCOUNTERED") or metrics.get("CALL_ANSWERED_BY") == "HUMAN":
        score += 10
    if metrics.get("UPDATE_ETA_SUCCESSFUL"):
        score += 20
    if metrics.get("API_OK"):
        score += 5
    if metrics.get("VALID_SR"):
        score += 5
    if metrics.get("IVR_DURATION_EXCEEDED"):
        score += 3
    return score


def audit_one(conv: dict) -> dict:
    turns = conv.get("turns") or []
    metrics = conv.get("metrics") or {}
    integration = {
        "valid_sr_event": bool(metrics.get("VALID_SR")),
        "api_ok_event": bool(metrics.get("API_OK")),
        "likely_integration": "polyai_custom_api",
        "vixxolink_mcp_tool_events_in_payload": False,
    }
    if metrics.get("UPDATE_ETA_SUCCESSFUL") or metrics.get("UPDATE_ETA_START"):
        integration["inferred_backend_action"] = "update_eta"
    return {
        "id": conv.get("id"),
        "started_at": conv.get("started_at"),
        "duration_sec": conv.get("total_duration"),
        "num_turns": conv.get("num_turns"),
        "variant_name": conv.get("variant_name"),
        "outbound_call_status": metrics.get("OUTBOUND_CALL_STATUS"),
        "transaction_type": metrics.get("TRANSACTION_TYPE"),
        "sr_substatus": metrics.get("SR_SUBSTATUS"),
        "technician_status": metrics.get("TECHNICIAN_STATUS"),
        "extracted_sr_number": extract_sr_from_turns(turns),
        "integration_signals": integration,
        "metrics": pick_metrics(metrics),
        "turns_redacted": [redact_turn(t) for t in turns if (t.get("agent_response") or "").strip()],
    }


def find_conversation(cfg: dict[str, str], conversation_id: str) -> dict | None:
    from polyai_fetch import fetch_all_conversations

    for conv in fetch_all_conversations(cfg, page_size=50, progress=True):
        if conv.get("id") == conversation_id:
            return conv
    return None


def cmd_audit(
    cfg: dict[str, str],
    limit: int,
    conversation_id: str | None,
    pick_best: bool,
    full_scan: bool,
) -> int:
    if conversation_id and full_scan:
        target = find_conversation(cfg, conversation_id)
        if not target:
            raise SystemExit(f"Conversation {conversation_id} not found in full project scan.")
        targets = [target]
    else:
        url = polyai_client.conversations_url(cfg) + f"?limit={limit}"
        data = polyai_client.request_json(url, cfg["POLYAI_API_KEY"])
        conversations = data.get("conversations") or []

        if conversation_id:
            targets = [c for c in conversations if c.get("id") == conversation_id]
            if not targets:
                raise SystemExit(
                    f"Conversation {conversation_id} not found in first {limit} results. "
                    "Increase --limit or pass --full-scan."
                )
        elif pick_best:
            ranked = sorted(conversations, key=score_conversation, reverse=True)
            targets = [c for c in ranked if (c.get("num_turns") or 0) > 0][:1] or conversations[:1]
        else:
            targets = conversations

    print(
        json.dumps(
            {
                "project_id": cfg["POLYAI_PROJECT_ID"],
                "account_id": cfg["POLYAI_ACCOUNT_ID"],
                "audited_count": len(targets),
                "conversations": [audit_one(c) for c in targets],
            },
            indent=2,
        )
    )
    return 0


def main() -> int:
    polyai_client.load_dotenv()
    parser = argparse.ArgumentParser(description="Audit PolyAI conversations")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--conversation-id")
    parser.add_argument("--pick-best", action="store_true")
    parser.add_argument(
        "--project",
        help="PolyAI project_id (default: POLYAI_PROJECT_ID or projects.json default)",
    )
    parser.add_argument(
        "--full-scan",
        action="store_true",
        help="Paginate entire project when looking up --conversation-id",
    )
    args = parser.parse_args()
    cfg = polyai_client.config_from_env(args.project)
    return cmd_audit(
        cfg,
        args.limit,
        args.conversation_id,
        args.pick_best or not args.conversation_id,
        args.full_scan,
    )


if __name__ == "__main__":
    sys.exit(main())
