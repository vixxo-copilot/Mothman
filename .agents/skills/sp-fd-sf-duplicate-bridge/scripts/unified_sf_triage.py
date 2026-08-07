#!/usr/bin/env python3
"""Unified SF triage: one intake pass for context clues + duplicate clustering + shell vet."""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any

import scan_duplicates as sd

SHELL = "Service Provider Support Shell Account"
OPEN = {
    "new",
    "working",
    "open",
    "pending",
    "escalated",
    "on hold",
    "compliance in progress",
}


def extract_context_clues(
    *,
    subject: str,
    intake_text: str,
    attachment_names: list[str],
    entities: dict,
) -> dict:
    """Context clues from email body + attachments (sp-inbound-vetting intake)."""
    blob = f"{subject}\n{intake_text}\n{' '.join(attachment_names)}"
    clues: dict[str, Any] = {
        "fd_ticket_ids": sorted({m.group(1) for m in sd.FD_TICKET_RE.finditer(blob)}),
        "sp_numbers": [],
        "attachment_hints": [],
    }
    try:
        from entity_extraction import extract_sp_numbers  # noqa: WPS433

        clues["sp_numbers"] = extract_sp_numbers(intake_text, attachment_names=attachment_names)
    except Exception:
        pass

    for name in attachment_names:
        low = (name or "").lower()
        if any(k in low for k in ("coi", "cert", "acord", "insurance", "liability")):
            clues["attachment_hints"].append(name)

    coi_subject = sd.extract_federated_coi_fields(subject)
    coi_body = sd.extract_federated_coi_fields(intake_text[:2000] if intake_text else "")
    clues["coi_subject"] = coi_subject
    clues["coi_body"] = coi_body

    email = entities.get("requester_email")
    if email and email != "Not stated":
        clues["requester_email"] = email
    if entities.get("company") and entities["company"] != "Not stated":
        clues["company"] = entities["company"]
    if entities.get("ks_number"):
        clues["ks_number"] = entities["ks_number"]
    if entities.get("sr_number"):
        clues["sr_number"] = entities["sr_number"]

    return clues


def enrich_record_with_intake(record: dict, intake_pack: dict) -> dict:
    """Merge full-thread text into scan blob so duplicate logic sees body + attachments."""
    r = dict(record)
    intake_text = intake_pack.get("intake_text") or ""
    attachments = " ".join(intake_pack.get("attachment_names") or [])
    clues = intake_pack.get("context_clues") or {}
    fd_refs = " ".join(f"Freshdesk #{x}" for x in clues.get("fd_ticket_ids") or [])
    r["Description"] = (
        (r.get("Description") or "")
        + "\n--- intake ---\n"
        + intake_text
        + "\n"
        + attachments
        + "\n"
        + fd_refs
    )
    email = clues.get("requester_email") or intake_pack.get("requester_email")
    if email:
        r["ContactEmail"] = email
    return r


def shell_open_ids(records: list[dict]) -> set[str]:
    out: set[str] = set()
    for c in records:
        if (
            (c.get("Account") or {}).get("Name") == SHELL
            and (c.get("Status") or "").lower() in OPEN
            and c.get("Id")
        ):
            out.add(c["Id"])
    return out


def intake_target_ids(records: list[dict], seed_scan: dict) -> set[str]:
    """Cases needing full EmailMessage + attachment pull (shell + duplicate members)."""
    from scan_sf_duplicates import duplicate_member_ids  # noqa: WPS433

    return shell_open_ids(records) | duplicate_member_ids(seed_scan)


def _fallback_pack(case: dict, exc: Exception) -> dict:
    subject = case.get("Subject") or ""
    coi_fields = sd.extract_federated_coi_fields(subject)
    email = sd.norm_email(case.get("ContactEmail") or case.get("SuppliedEmail"))
    company = (coi_fields or {}).get("provider") or "Not stated"
    hint_fn = getattr(sd, "extract_subject_sp_hint", None)
    if hint_fn:
        company = hint_fn(subject) or company
    return {
        "intake_error": str(exc),
        "entities": {
            "company": company,
            "ks_number": None,
            "sr_number": None,
            "requester_email": email or "Not stated",
            "email_domain_tokens": [],
            "gateway_precheck": None,
            "intake_sources": {"intake_error": str(exc)},
        },
        "intake_text": subject,
        "attachment_names": [],
    }


def pull_intake_batch(
    records: list[dict],
    target_ids: set[str],
    load_case_intake,
) -> dict[str, dict]:
    """Batched SF prefetch + parallel entity extraction (much faster than per-case CLI)."""
    import os
    from concurrent.futures import ThreadPoolExecutor, as_completed

    by_id = {c["Id"]: c for c in records if c.get("Id")}
    ids = [cid for cid in sorted(target_ids) if cid in by_id]
    packs: dict[str, dict] = {}
    if not ids:
        return packs

    # Warm caches with batched SOQL (orders of magnitude fewer SF CLI calls)
    try:
        from shell_sf_intake import prefetch_intake_for_ids  # noqa: WPS433

        prefetch_intake_for_ids(
            ids,
            email_batch_size=int(os.environ.get("INTAKE_EMAIL_BATCH", "12")),
            attach_batch_size=int(os.environ.get("INTAKE_ATTACH_BATCH", "40")),
        )
    except Exception as exc:
        print(f"  Prefetch warning (falling back to per-case): {exc}", flush=True)

    workers = max(1, int(os.environ.get("INTAKE_WORKERS", "8")))

    def _one(cid: str) -> tuple[str, dict]:
        case = by_id[cid]
        try:
            entities, intake_text, _, attachments = load_case_intake(case, queue="coi")
            clues = extract_context_clues(
                subject=case.get("Subject") or "",
                intake_text=intake_text,
                attachment_names=attachments,
                entities=entities,
            )
            return cid, {
                "entities": entities,
                "intake_text": intake_text,
                "attachment_names": attachments,
                "context_clues": clues,
                "requester_email": clues.get("requester_email"),
            }
        except Exception as exc:
            return cid, _fallback_pack(case, exc)

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_one, cid) for cid in ids]
        for fut in as_completed(futures):
            cid, pack = fut.result()
            packs[cid] = pack
            done += 1
            if done % 25 == 0 or done == len(ids):
                print(f"  Intake extract {done}/{len(ids)}...", flush=True)
    return packs


def build_enriched_records(records: list[dict], intake_packs: dict[str, dict]) -> list[dict]:
    out: list[dict] = []
    for r in records:
        cid = r.get("Id")
        if cid and cid in intake_packs and intake_packs[cid].get("intake_text"):
            out.append(enrich_record_with_intake(r, intake_packs[cid]))
        else:
            out.append(r)
    return out


def run_duplicate_scan(records: list[dict], *, sf_cache: str, scope: str) -> dict:
    import os

    from scan_sf_duplicates import build_scan_result  # noqa: WPS433

    # Default open/new-only — shrinks duplicate-member intake targets
    open_only = os.environ.get("SCAN_INCLUDE_CLOSED", "0") != "1"
    return build_scan_result(
        records,
        sf_cache=sf_cache,
        scope=scope,
        open_only=open_only,
    )
