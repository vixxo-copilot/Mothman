#!/usr/bin/env python3
"""Fetch Freshdesk tickets assigned to the API key owner."""
from __future__ import annotations

import base64
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


def get_token() -> str | None:
    for src in (os.environ.get("FRESHDESK_API_KEY", ""), os.environ.get("FRESHDESK_TOKEN", "")):
        if src.strip():
            return src.strip()
    token_path = Path.home() / ".vixxo" / "freshdesk_token"
    if token_path.exists():
        return token_path.read_text(encoding="ascii").strip()
    return None


def main() -> int:
    token = get_token()
    domain = os.environ.get("FRESHDESK_DOMAIN", "vixxo-helpdesk.freshdesk.com")
    if not token:
        print(json.dumps({"error": "NO_TOKEN"}))
        return 1

    auth = base64.b64encode(f"{token}:X".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Accept": "application/json"}

    def get(path: str) -> dict | list:
        req = urllib.request.Request(f"https://{domain}{path}", headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())

    me = get("/api/v2/agents/me")
    agent_id = me["id"]
    contact = me.get("contact") or {}

    query = f"agent_id:{agent_id} AND status:2"
    search_path = "/api/v2/search/tickets?query=" + urllib.parse.quote(f'"{query}"')
    page = 1
    all_tickets: list[dict] = []
    while True:
        results = get(f"{search_path}&page={page}")
        batch = results.get("results") or []
        all_tickets.extend(batch)
        if len(batch) < 30:
            break
        page += 1
        if page > 20:
            break

    priority_map = {1: "Low", 2: "Medium", 3: "High", 4: "Urgent"}
    status_map = {2: "Open", 3: "Pending", 4: "Resolved", 5: "Closed"}

    def slim(t: dict) -> dict:
        cf = t.get("custom_fields") or {}
        return {
            "id": t.get("id"),
            "subject": t.get("subject"),
            "status": status_map.get(t.get("status"), t.get("status")),
            "priority": priority_map.get(t.get("priority"), t.get("priority")),
            "type": t.get("type"),
            "tags": t.get("tags") or [],
            "group_id": t.get("group_id"),
            "created_at": t.get("created_at"),
            "updated_at": t.get("updated_at"),
            "due_by": t.get("due_by"),
            "fr_due_by": t.get("fr_due_by"),
            "sp_number": cf.get("cf_sp"),
            "requester_id": t.get("requester_id"),
        }

    payload = {
        "agent": {
            "id": agent_id,
            "name": contact.get("name"),
            "email": contact.get("email"),
        },
        "total_open_assigned": len(all_tickets),
        "tickets": [slim(t) for t in all_tickets],
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
