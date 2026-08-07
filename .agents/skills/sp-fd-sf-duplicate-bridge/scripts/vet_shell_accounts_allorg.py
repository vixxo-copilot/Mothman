#!/usr/bin/env python3
"""Vet open Shell Account cases — mirrors sp-inbound-vetting COI queue per case."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPTS.parent
TMP = SKILL_ROOT / ".tmp"
VETTING_SCRIPTS = SKILL_ROOT.parent / "sp-inbound-vetting" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(VETTING_SCRIPTS))

import scan_duplicates as sd  # noqa: E402
import scan_sf_duplicates as ssd  # noqa: E402
from entity_extraction import company_search_variants, email_domain_search_tokens  # noqa: E402
from gateway_vetting import gateway_find_sp, _enrich_sp_hit  # noqa: E402
from shell_sf_intake import (  # noqa: E402
    clear_intake_cache,
    load_case_intake,
    norm_email_domain,
    to_sf_case,
)
from sf_vetting import determine_posture, is_autoreply_noise  # noqa: E402

SF = os.path.expandvars(r"%APPDATA%\npm\sf.cmd")
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

def _path(env_key: str, default: Path) -> Path:
    v = os.environ.get(env_key)
    return Path(v) if v else default


SF_CACHE = _path("SF_CACHE_PATH", TMP / "sf-cases-window-allorg-20260730.json")
PRIOR_SCAN = _path("PRIOR_SCAN_PATH", TMP / "sf-intra-duplicate-scan-allorg-20260730.json")
VET_JSON = _path("VET_JSON_PATH", TMP / "shell-account-vet-allorg-20260730.json")
VET_MD = _path("VET_MD_PATH", TMP / "shell-account-vet-report-allorg-20260730.md")
VETTED_JSON = _path("VETTED_JSON_PATH", TMP / "sf-intra-duplicate-scan-allorg-vetted-20260730.json")
VETTED_MD = _path("VETTED_MD_PATH", TMP / "sf-intra-duplicate-report-allorg-vetted-20260730.md")
VETTED_HTML = _path("VETTED_HTML_PATH", TMP / "sf-intra-duplicate-scan-allorg-vetted-20260730.html")

KS_RE = re.compile(r"\b(KS\d+)\b", re.I)
SR_RE = re.compile(r"\b(1-\d{9,10})\b")
ONBOARDING_RE = re.compile(
    r"ksonboarding|onboarding|prosite|coverage application|new provider",
    re.I,
)

AUTO_REPLY_PATTERNS = [
    re.compile(r"auto reply", re.I),
    re.compile(r"your request has been received", re.I),
    re.compile(r"\[request received\]", re.I),
    re.compile(r"federated insurance auto reply", re.I),
    re.compile(r"housecallpro", re.I),
    re.compile(r"notifications@housecallpro", re.I),
    re.compile(r"service desk submitted", re.I),
    re.compile(r"quickbooks.*past due", re.I),
]

# Override with GATEWAY_SLEEP_S / SF_ACCOUNT_SLEEP_S env vars for slower/safer runs
GATEWAY_SLEEP_S = float(os.environ.get("GATEWAY_SLEEP_S", "0.05"))
SF_ACCOUNT_SLEEP_S = float(os.environ.get("SF_ACCOUNT_SLEEP_S", "0.05"))


def load_records(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "records" in data:
        return data["records"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Unexpected cache shape: {path}")


def sf_query(query: str) -> list[dict]:
    timeout_s = float(os.environ.get("SF_QUERY_TIMEOUT_S", "60"))
    try:
        result = subprocess.run(
            [SF, "data", "query", "--query", query, "--target-org", "vixxo", "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"sf query timed out after {timeout_s}s") from exc
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout[:500])
    payload = json.loads(result.stdout)
    return payload.get("result", {}).get("records", [])


def escape_soql(s: str) -> str:
    return (s or "").replace("\\", "\\\\").replace("'", "\\'")


def detect_auto_reply(case: dict, intake_text: str | None = None) -> str | None:
    blob = intake_text or f"{case.get('Subject') or case.get('subject') or ''} {case.get('Description') or case.get('description') or ''}"
    noise = is_autoreply_noise(case if case.get("Subject") is not None else {"Subject": case.get("subject"), "Description": case.get("description")}, blob)
    if noise:
        return noise
    for pat in AUTO_REPLY_PATTERNS:
        if pat.search(blob):
            return pat.pattern
    subj = (case.get("Subject") or case.get("subject") or "").lower()
    if subj.startswith("re:") and "certificate of insurance" in subj:
        if sd.FEDCOI_AUTOREPLY_RE.search(case.get("Subject") or case.get("subject") or ""):
            return "federated_autoreply_suffix"
    return None


def fallback_entities_from_case(case: dict, *, error: str | None = None) -> tuple[dict, str]:
    """Metadata-only entities when full EmailMessage intake is unavailable."""
    sf_case = to_sf_case(case)
    subject = sf_case.get("Subject") or case.get("subject") or ""
    description = sf_case.get("Description") or case.get("description") or ""
    coi_fields = sd.extract_federated_coi_fields(subject)
    email = sd.norm_email(
        sf_case.get("ContactEmail") or sf_case.get("SuppliedEmail") or case.get("contact_email")
    )
    ks_m = KS_RE.search(f"{subject} {description}")
    sr_m = SR_RE.search(f"{subject} {description}")
    company = (coi_fields or {}).get("provider") or "Not stated"
    hint_fn = getattr(sd, "extract_subject_sp_hint", None)
    if hint_fn:
        company = hint_fn(subject) or company
    sources: dict = {"intake_fallback": True}
    if error:
        sources["intake_error"] = error
    entities = {
        "company": company,
        "ks_number": ks_m.group(1).upper() if ks_m else None,
        "sr_number": sr_m.group(0) if sr_m else None,
        "requester_email": email or "Not stated",
        "email_domain_tokens": [],
        "gateway_precheck": None,
        "intake_sources": sources,
    }
    return entities, f"{subject} {description}".strip()


def intake_case(case: dict) -> tuple[dict, str]:
    """Full-thread intake — same path as sp-inbound-vetting COI queue."""
    try:
        entities, intake_text, _, _ = load_case_intake(case, queue="coi")
        return entities, intake_text
    except Exception as exc:
        return fallback_entities_from_case(case, error=str(exc))


def account_search_terms_from_entities(entities: dict, subject: str) -> list[str]:
    """Search terms per sp-inbound-vetting company-vetting order."""
    terms: list[str] = []
    seen: set[str] = set()

    def add(term: str) -> None:
        t = re.sub(r"\s+", " ", (term or "").strip())
        if len(t) < 3:
            return
        key = t.lower()
        if key not in seen and key != "not stated":
            seen.add(key)
            terms.append(t)

    coi_fields = sd.extract_federated_coi_fields(subject)
    provider = coi_fields["provider"] if coi_fields else None
    if provider:
        for v in company_search_variants(provider):
            add(v)
        norm = sd.normalize_coi_provider(provider)
        if norm and len(norm) >= 4:
            add(norm)

    company = entities.get("company")
    if company and company != "Not stated":
        for v in company_search_variants(company):
            add(v)

    gw = entities.get("gateway_precheck") or {}
    if gw.get("name"):
        for v in company_search_variants(gw["name"]):
            add(v)

    vl = entities.get("vl_sr_sp") or {}
    if vl.get("name"):
        for v in company_search_variants(vl["name"]):
            add(v)

    email = entities.get("requester_email")
    if email and email != "Not stated":
        dom = norm_email_domain(email)
        if dom:
            stem = dom.split(".")[0]
            if len(stem) >= 4:
                add(stem)
    for token in entities.get("email_domain_tokens") or []:
        if len(token) >= 4:
            add(token)

    return terms[:8]


def build_cluster_index(scan: dict) -> dict[str, dict]:
    """Map case Id -> cluster metadata."""
    index: dict[str, dict] = {}

    def ingest(groups: list[dict], cluster_type: str) -> None:
        for g in groups:
            primary = g.get("recommended_primary") or {}
            primary_id = primary.get("id")
            cluster_key = (
                g.get("policy_id"),
                g.get("req_id"),
            ) if cluster_type == "federated_coi_req_id" else (
                g.get("fd_ticket_id")
                if cluster_type == "freshdesk_xref"
                else g.get("phone")
            )
            for c in g.get("cases") or []:
                cid = c.get("id")
                if not cid:
                    continue
                index[cid] = {
                    "cluster_type": cluster_type,
                    "cluster_key": cluster_key,
                    "duplicate_of": None
                    if cid == primary_id
                    else {
                        "id": primary_id,
                        "case_number": primary.get("case_number"),
                        "subject": primary.get("subject"),
                    },
                    "is_primary": cid == primary_id,
                    "case_count": g.get("case_count"),
                }

    ingest(scan.get("coi_duplicates") or [], "federated_coi_req_id")
    ingest(scan.get("fd_xref_duplicates") or [], "freshdesk_xref")
    ingest(scan.get("phone_duplicates") or [], "voicemail_phone")
    return index


def account_search_terms(hints: dict) -> list[str]:
    """Backward-compat wrapper."""
    entities = hints.get("entities") or {}
    return account_search_terms_from_entities(entities, hints.get("subject") or "")


def resolve_sf_account(
    entities: dict,
    subject: str,
    account_cache: dict[str, list[dict]],
) -> tuple[dict | None, list[dict]]:
    """Gateway KS # then company/name search — single resolution path."""
    from extract_shell_coi_insured import lookup_account_by_sp_number  # noqa: E402

    account_rows: list[dict] = []
    coi_fields = sd.extract_federated_coi_fields(subject)
    hints = {
        "provider": coi_fields["provider"] if coi_fields else None,
        "company": entities.get("company") if entities.get("company") != "Not stated" else None,
    }

    sp_num = (entities.get("gateway_precheck") or {}).get("sp_number") or entities.get("ks_number")
    if sp_num:
        acct = lookup_account_by_sp_number(str(sp_num), account_cache)
        if acct:
            return {"Id": acct["id"], "Name": acct["name"]}, account_rows

    for term in account_search_terms_from_entities(entities, subject):
        account_rows = lookup_sf_account(term, account_cache)
        account = pick_best_account(account_rows, hints)
        if account:
            return account, account_rows
    return None, account_rows


def resolve_gateway(entities: dict, gateway_cache: dict[str, dict | None]) -> dict | None:
    """Use extract_sf_case_entities gateway_precheck; refresh only if missing."""
    pre = entities.get("gateway_precheck")
    if pre and pre.get("sp_number"):
        return pre

    keys: list[str] = []
    if entities.get("ks_number"):
        keys.append(f"ks:{entities['ks_number']}")
    if entities.get("company") and entities["company"] != "Not stated":
        keys.append(f"co:{entities['company'].lower()[:30]}")
    email = entities.get("requester_email")
    if email and email != "Not stated":
        keys.append(f"em:{email.lower()}")
    cache_key = "|".join(keys) or "empty"
    if cache_key in gateway_cache:
        return gateway_cache[cache_key]

    hit = None
    try:
        hit = _enrich_sp_hit(gateway_find_sp(entities))
    except Exception:
        hit = None
    gateway_cache[cache_key] = hit
    time.sleep(GATEWAY_SLEEP_S)
    return hit


def lookup_sf_account(
    term: str, cache: dict[str, list[dict]]
) -> list[dict]:
    key = term.lower()
    if key in cache:
        return cache[key]

    frag = escape_soql(term[:40])
    query = (
        "SELECT Id, Name FROM Account "
        f"WHERE Name LIKE '%{frag}%' AND Name != '{escape_soql(SHELL)}' "
        "ORDER BY Name LIMIT 8"
    )
    try:
        rows = sf_query(query)
    except RuntimeError:
        rows = []
    cache[key] = rows
    time.sleep(SF_ACCOUNT_SLEEP_S)
    return rows


_BLOCKED_ACCOUNT_NAMES = {
    "vixxo corporation",
    "vixxo corp",
    "service provider support shell account",
    "vixxo facility solutions",
}


def _is_blocked_account(name: str | None) -> bool:
    n = (name or "").strip().lower()
    if not n:
        return True
    if n in _BLOCKED_ACCOUNT_NAMES:
        return True
    if n.startswith("vixxo ") and "ks -" not in n:
        return True
    return False


def pick_best_account(rows: list[dict], hints: dict) -> dict | None:
    if not rows:
        return None
    usable = [r for r in rows if not _is_blocked_account(r.get("Name"))]
    if not usable:
        return None
    target = sd.normalize_coi_provider(hints.get("provider") or hints.get("company") or "")
    if not target or _is_blocked_account(hints.get("company")) or _is_blocked_account(
        hints.get("provider")
    ):
        return usable[0] if len(usable) == 1 else None

    best = usable[0]
    best_score = -1
    for row in usable:
        name = row.get("Name") or ""
        norm = sd.normalize_coi_provider(name)
        score = 0
        if target and (target in norm or norm in target):
            score += 5
        if hints.get("provider") and hints["provider"].lower() in name.lower():
            score += 3
        if score > best_score:
            best_score = score
            best = row
    return best if best_score >= 2 or len(usable) == 1 else None


def assign_vet_status(
    entities: dict,
    subject: str,
    cluster: dict | None,
    auto_pat: str | None,
    account: dict | None,
    gateway: dict | None,
) -> str:
    if auto_pat:
        return "auto_reply_noise"
    if cluster and not cluster.get("is_primary"):
        return "duplicate_cluster"
    if account and account.get("Id"):
        return "account_resolved"
    if gateway and gateway.get("sp_number"):
        return "gateway_match"
    blob = subject or ""
    if ONBOARDING_RE.search(blob) or entities.get("ks_number"):
        return "onboarding"
    if entities.get("sr_number"):
        return "sr_routing"
    return "needs_manual"


def vet_shell_cases(
    records: list[dict],
    duplicate_scan: dict,
    intake_packs: dict[str, dict] | None = None,
    *,
    checkpoint_path: Path | None = None,
) -> dict:
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed

    shell_cases = [
        c
        for c in records
        if (c.get("Account") or {}).get("Name") == SHELL
        and (c.get("Status") or "").lower() in OPEN
        and (c.get("Id") or c.get("id"))
    ]
    cluster_index = build_cluster_index(duplicate_scan)
    account_cache: dict[str, list[dict]] = {}
    gateway_cache: dict[str, dict | None] = {}
    cache_lock = threading.Lock()
    vetted: list[dict] = []
    done_ids: set[str] = set()
    packs = intake_packs or {}

    if checkpoint_path and checkpoint_path.exists():
        try:
            ck = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            vetted = ck.get("cases") or []
            done_ids = {v["id"] for v in vetted if v.get("id")}
            if done_ids:
                print(f"Resuming vetting from checkpoint ({len(done_ids)} cases)...", flush=True)
        except (json.JSONDecodeError, OSError):
            pass

    pending = [
        c
        for c in sorted(shell_cases, key=lambda x: x.get("CreatedDate") or "")
        if (c.get("Id") or c.get("id")) not in done_ids
    ]
    workers = max(1, int(os.environ.get("VET_WORKERS", "6")))
    print(f"Vetting {len(pending)} cases with {workers} workers...", flush=True)

    def _vet_one_parallel(case: dict) -> dict:
        cid = case.get("Id") or case.get("id")
        subject = case.get("Subject") or ""
        pack = packs.get(cid) or {}
        if pack.get("entities"):
            entities = pack["entities"]
            intake_text = pack.get("intake_text") or ""
        elif pack.get("intake_error"):
            entities, intake_text = fallback_entities_from_case(case, error=pack["intake_error"])
        else:
            entities, intake_text = intake_case(case)
        auto_pat = detect_auto_reply(case, intake_text)
        cluster = cluster_index.get(cid)

        account = None
        account_rows: list[dict] = []
        gateway = None
        if not auto_pat:
            # Cache-aware resolve without holding lock across sleeps
            pre = entities.get("gateway_precheck")
            if pre and pre.get("sp_number"):
                gateway = pre
            else:
                keys: list[str] = []
                if entities.get("ks_number"):
                    keys.append(f"ks:{entities['ks_number']}")
                if entities.get("company") and entities["company"] != "Not stated":
                    keys.append(f"co:{entities['company'].lower()[:30]}")
                email_key = entities.get("requester_email")
                if email_key and email_key != "Not stated":
                    keys.append(f"em:{email_key.lower()}")
                cache_key = "|".join(keys) or "empty"
                with cache_lock:
                    hit = gateway_cache.get(cache_key, "__miss__")
                if hit == "__miss__":
                    try:
                        hit = _enrich_sp_hit(gateway_find_sp(entities))
                    except Exception:
                        hit = None
                    with cache_lock:
                        gateway_cache[cache_key] = hit
                    time.sleep(GATEWAY_SLEEP_S)
                else:
                    hit = hit  # cached
                gateway = hit
            with cache_lock:
                account, account_rows = resolve_sf_account(entities, subject, account_cache)

        coi_fields = sd.extract_federated_coi_fields(subject)
        email = entities.get("requester_email")
        if email == "Not stated":
            email = None
        vet_status = assign_vet_status(entities, subject, cluster, auto_pat, account, gateway)
        posture = determine_posture(entities, gateway)
        return {
            "id": case.get("Id"),
            "case_number": case.get("CaseNumber"),
            "subject": subject,
            "status": case.get("Status"),
            "created_date": case.get("CreatedDate"),
            "contact_email": email,
            "vetting": {
                "queue": "coi",
                "posture": posture,
                "company": entities.get("company"),
                "ks_number": entities.get("ks_number"),
                "sr_number": entities.get("sr_number"),
                "requester_email": email,
                "gateway_sp": gateway.get("sp_number") if gateway else None,
                "gateway_name": gateway.get("name") if gateway else None,
                "gateway_source": gateway.get("source") if gateway else None,
                "intake_sources": entities.get("intake_sources"),
            },
            "hints": {
                "provider": coi_fields["provider"] if coi_fields else None,
                "company": entities.get("company") if entities.get("company") != "Not stated" else None,
                "ks_number": entities.get("ks_number"),
                "sr_number": entities.get("sr_number"),
                "email_domain": norm_email_domain(email),
                "coi_policy_id": (coi_fields or {}).get("policy_id"),
                "coi_req_id": (coi_fields or {}).get("req_id"),
                "intake_sources": entities.get("intake_sources"),
            },
            "vet_status": vet_status,
            "auto_reply_pattern": auto_pat,
            "duplicate_cluster": cluster,
            "duplicate_of": (cluster or {}).get("duplicate_of"),
            "recommended_account": (
                {"id": account["Id"], "name": account["Name"]} if account else None
            ),
            "account_search_candidates": [
                {"id": r["Id"], "name": r["Name"]} for r in (account_rows or [])[:5]
            ],
            "gateway_sp": gateway.get("sp_number") if gateway else None,
            "gateway_name": gateway.get("name") if gateway else None,
            "gateway_source": gateway.get("source") if gateway else None,
            "context_clues": pack.get("context_clues"),
            "attachment_names": pack.get("attachment_names") or [],
        }

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_vet_one_parallel, case) for case in pending]
        for fut in as_completed(futures):
            try:
                entry = fut.result()
            except Exception as exc:
                print(f"  Vet worker error (continuing): {exc}", flush=True)
                continue
            vetted.append(entry)
            done_count = len(vetted)
            if done_count % 5 == 0 or done_count == len(shell_cases):
                print(f"Vetted {done_count}/{len(shell_cases)}...", flush=True)
            if checkpoint_path and (done_count % 10 == 0 or done_count == len(shell_cases)):
                ordered = sorted(vetted, key=lambda x: x.get("created_date") or "")
                checkpoint_path.write_text(
                    json.dumps({"cases": ordered}, indent=2),
                    encoding="utf-8",
                )

    vetted = sorted(vetted, key=lambda x: x.get("created_date") or "")
    if checkpoint_path and checkpoint_path.exists():
        checkpoint_path.unlink(missing_ok=True)

    by_status = Counter(v["vet_status"] for v in vetted)
    return {
        "generated": datetime.now(timezone.utc).isoformat(),
        "sf_cache": str(SF_CACHE),
        "duplicate_scan": duplicate_scan.get("scan"),
        "shell_open_count": len(vetted),
        "by_vet_status": dict(by_status.most_common()),
        "cases": vetted,
    }


def write_vet_report(vet: dict, path: Path) -> None:
    lines = [
        "# Shell Account Vetting — All Org",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Source:** `{vet['sf_cache']}`",
        f"**Shell open cases vetted:** {vet['shell_open_count']}",
        "",
        "## Summary by vet_status",
        "",
        "| vet_status | Count |",
        "|------------|------:|",
    ]
    for status, count in sorted(
        (vet.get("by_vet_status") or {}).items(), key=lambda x: -x[1]
    ):
        lines.append(f"| `{status}` | {count} |")
    lines.append("")

    actionable = [
        c
        for c in vet["cases"]
        if c["vet_status"]
        in ("duplicate_cluster", "account_resolved", "gateway_match", "onboarding")
    ]
    lines.extend(
        [
            "## Top actionable rows",
            "",
            "| Case | vet_status | Provider/Company | Account / KS | Duplicate of | Subject |",
            "|------|------------|------------------|--------------|--------------|---------|",
        ]
    )
    for c in actionable[:40]:
        h = c.get("hints") or {}
        sp = h.get("provider") or h.get("company") or "—"
        acct = ""
        if c.get("recommended_account"):
            acct = c["recommended_account"]["name"]
        elif c.get("gateway_sp"):
            acct = c["gateway_sp"]
        dup = (c.get("duplicate_of") or {}).get("case_number") or "—"
        subj = (c.get("subject") or "")[:50]
        lines.append(
            f"| {c['case_number']} | `{c['vet_status']}` | {sp} | {acct or '—'} | {dup} | {subj} |"
        )
    if len(actionable) > 40:
        lines.append("")
        lines.append(f"_… and {len(actionable) - 40} more actionable rows in JSON._")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def annotate_case_summary(case: dict, vet_map: dict[str, dict]) -> dict:
    out = dict(case)
    vid = case.get("id")
    if vid and vid in vet_map:
        v = vet_map[vid]
        out["shell_vet_status"] = v.get("vet_status")
        out["shell_recommended_account"] = v.get("recommended_account")
        out["shell_gateway_sp"] = v.get("gateway_sp")
    return out


def is_actionable_vet(status: str | None) -> bool:
    return status not in (None, "auto_reply_noise")


def build_vetted_scan(duplicate_scan: dict, vet: dict) -> dict:
    vet_map = {c["id"]: c for c in vet["cases"]}

    def annotate_groups(groups: list[dict]) -> list[dict]:
        out = []
        for g in groups:
            ng = dict(g)
            ng["cases"] = [annotate_case_summary(c, vet_map) for c in g.get("cases") or []]
            ng["recommended_primary"] = annotate_case_summary(
                g.get("recommended_primary") or {}, vet_map
            )
            ng["merge_candidates"] = [
                annotate_case_summary(c, vet_map) for c in g.get("merge_candidates") or []
            ]
            shell_involved = [
                c for c in ng["cases"] if (c.get("account") == SHELL or c.get("shell_vet_status"))
            ]
            ng["shell_involved_count"] = len(shell_involved)
            ng["shell_vet_statuses"] = Counter(
                c.get("shell_vet_status") for c in shell_involved if c.get("shell_vet_status")
            ).most_common()
            noise_only = shell_involved and all(
                c.get("shell_vet_status") == "auto_reply_noise" for c in shell_involved
            )
            ng["actionable_after_vet"] = not noise_only
            out.append(ng)
        return out

    coi = annotate_groups(duplicate_scan.get("coi_duplicates") or [])
    fd = annotate_groups(duplicate_scan.get("fd_xref_duplicates") or [])
    phone = annotate_groups(duplicate_scan.get("phone_duplicates") or [])

    def count_actionable(groups: list[dict]) -> int:
        return sum(1 for g in groups if g.get("actionable_after_vet", True))

    before_actionable = (
        len(duplicate_scan.get("coi_duplicates") or [])
        + len(duplicate_scan.get("fd_xref_duplicates") or [])
        + len(duplicate_scan.get("phone_duplicates") or [])
    )
    after_actionable = count_actionable(coi) + count_actionable(fd) + count_actionable(phone)

    shell_candidates = []
    for c in vet["cases"]:
        if c["vet_status"] == "auto_reply_noise":
            continue
        if c["vet_status"] in ("duplicate_cluster", "account_resolved", "gateway_match"):
            shell_candidates.append(
                {
                    "case_number": c["case_number"],
                    "id": c["id"],
                    "vet_status": c["vet_status"],
                    "provider": (c.get("hints") or {}).get("provider")
                    or (c.get("hints") or {}).get("company"),
                    "recommended_account": c.get("recommended_account"),
                    "gateway_sp": c.get("gateway_sp"),
                    "duplicate_of": c.get("duplicate_of"),
                    "cluster_type": (c.get("duplicate_cluster") or {}).get("cluster_type"),
                    "subject": c.get("subject"),
                    "merge_recommended": c["vet_status"] == "duplicate_cluster"
                    or (
                        c["vet_status"] in ("account_resolved", "gateway_match")
                        and c.get("duplicate_of")
                    ),
                }
            )

    shell_open = [
        annotate_case_summary(c, vet_map) for c in duplicate_scan.get("shell_open") or []
    ]

    result = dict(duplicate_scan)
    result.update(
        {
            "generated": datetime.now(timezone.utc).isoformat(),
            "triage_mode": "unified_intake",
            "shell_vet_source": str(VET_JSON),
            "coi_duplicates": coi,
            "fd_xref_duplicates": fd,
            "phone_duplicates": phone,
            "shell_open": shell_open,
            "shell_vetted_duplicate_candidates": shell_candidates,
            "vetting_summary": {
                "shell_open_vetted": vet["shell_open_count"],
                "by_vet_status": vet.get("by_vet_status"),
                "actionable_duplicate_groups_before": before_actionable,
                "actionable_duplicate_groups_after": after_actionable,
                "auto_reply_noise_shell_count": vet.get("by_vet_status", {}).get(
                    "auto_reply_noise", 0
                ),
                "shell_merge_recommended_count": sum(
                    1 for c in shell_candidates if c.get("merge_recommended")
                ),
            },
        }
    )
    return result


def write_vetted_markdown(data: dict, path: Path) -> None:
    vs = data.get("vetting_summary") or {}
    lines = [
        "# Salesforce Intra-SF Duplicate Scan (Shell-Vetted)",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Source:** `{data.get('sf_cache')}` + unified triage `{data.get('triage_mode')}`",
        f"**Scope:** {data.get('scope', '')}",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|------:|",
        f"| Total Cases in export | {data.get('total_cases', 0)} |",
        f"| Open (actionable) | {data.get('open_total', 0)} |",
        f"| COI duplicate Req groups | {data.get('coi_dupe_groups', 0)} |",
        f"| FD cross-ref duplicate groups | {data.get('fd_xref_groups', 0)} |",
        f"| Voicemail phone duplicate groups | {data.get('phone_groups', 0)} |",
        f"| Open on Shell Account | {data.get('shell_open_count', 0)} |",
        f"| **Actionable dup groups (before vet)** | {vs.get('actionable_duplicate_groups_before', 0)} |",
        f"| **Actionable dup groups (after vet)** | {vs.get('actionable_duplicate_groups_after', 0)} |",
        f"| Shell auto-reply noise | {vs.get('auto_reply_noise_shell_count', 0)} |",
        f"| Shell merge recommended | {vs.get('shell_merge_recommended_count', 0)} |",
        "",
    ]

    if data.get("shell_vetted_duplicate_candidates"):
        lines.extend(
            [
                "## Shell-vetted duplicate candidates",
                "",
                "Cases where vet confirms SP identity and merge is recommended (report only).",
                "",
                "| Case | vet_status | Provider | Account / KS | Duplicate of | Cluster |",
                "|------|------------|----------|--------------|--------------|---------|",
            ]
        )
        for c in data["shell_vetted_duplicate_candidates"]:
            if not c.get("merge_recommended") and c.get("vet_status") != "duplicate_cluster":
                continue
            acct = ""
            if c.get("recommended_account"):
                acct = c["recommended_account"].get("name", "")
            elif c.get("gateway_sp"):
                acct = c["gateway_sp"]
            dup = (c.get("duplicate_of") or {}).get("case_number") or "—"
            lines.append(
                f"| {c['case_number']} | `{c['vet_status']}` | {c.get('provider') or '—'} | "
                f"{acct or '—'} | {dup} | {c.get('cluster_type') or '—'} |"
            )
        lines.append("")

    for section, key, title in (
        ("coi", "coi_duplicates", "Federated COI — same `(policy_id, Req id)`"),
        ("fd", "fd_xref_duplicates", "Freshdesk cross-ref duplicates"),
        ("phone", "phone_duplicates", "Voicemail phone duplicates"),
    ):
        groups = [g for g in (data.get(key) or []) if g.get("shell_involved_count")]
        if not groups:
            continue
        lines.extend([f"## {title} (shell involvement)", ""])
        if section == "coi":
            lines.append(
                "| Provider | Req key | Cases | Shell | Primary | Shell vet on merge candidates |"
            )
            lines.append("|----------|---------|------:|------:|---------|------------------------------|")
            for g in groups:
                primary = g["recommended_primary"]["case_number"]
                merge_vet = ", ".join(
                    f"{c['case_number']}:{c.get('shell_vet_status', '?')}"
                    for c in g.get("merge_candidates") or []
                    if c.get("account") == SHELL or c.get("shell_vet_status")
                )
                lines.append(
                    f"| {g.get('provider') or '—'} | `{g.get('policy_id')} Req {g.get('req_id')}` | "
                    f"{g['case_count']} | {g.get('shell_involved_count', 0)} | **{primary}** | {merge_vet or '—'} |"
                )
        elif section == "fd":
            lines.append("| FD ticket | Cases | Shell | Primary | Shell vet |")
            lines.append("|-----------|------:|------:|---------|-----------|")
            for g in groups:
                primary = g["recommended_primary"]["case_number"]
                merge_vet = ", ".join(
                    f"{c['case_number']}:{c.get('shell_vet_status', '?')}"
                    for c in g.get("merge_candidates") or []
                    if c.get("account") == SHELL
                )
                lines.append(
                    f"| #{g['fd_ticket_id']} | {g['case_count']} | {g.get('shell_involved_count', 0)} | "
                    f"**{primary}** | {merge_vet or '—'} |"
                )
        else:
            lines.append("| Phone | Cases | Shell | Primary | Shell vet |")
            lines.append("|-------|------:|------:|---------|-----------|")
            for g in groups:
                primary = g["recommended_primary"]["case_number"]
                merge_vet = ", ".join(
                    f"{c['case_number']}:{c.get('shell_vet_status', '?')}"
                    for c in g.get("merge_candidates") or []
                    if c.get("account") == SHELL
                )
                lines.append(
                    f"| {g.get('phone')} | {g['case_count']} | {g.get('shell_involved_count', 0)} | "
                    f"**{primary}** | {merge_vet or '—'} |"
                )
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def render_vetted_html(data: dict, path: Path) -> None:
    sys.path.insert(0, str(SCRIPTS))
    from render_sf_duplicate_report_html import render_html  # noqa: E402

    html = render_html(data)
    extra = [
        "<h2>Shell vetting summary</h2><div class='card'><div class='stats'>",
    ]
    vs = data.get("vetting_summary") or {}
    for label, key in (
        ("Dup groups before", "actionable_duplicate_groups_before"),
        ("Dup groups after", "actionable_duplicate_groups_after"),
        ("Shell noise", "auto_reply_noise_shell_count"),
        ("Merge recommended", "shell_merge_recommended_count"),
    ):
        extra.append(
            f"<div class='stat warn'><div class='n'>{vs.get(key, 0)}</div>"
            f"<div class='l'>{label}</div></div>"
        )
    extra.append("</div></div>")

    candidates = data.get("shell_vetted_duplicate_candidates") or []
    if candidates:
        extra.append("<h2>Shell-vetted duplicate candidates</h2><div class='card'><table><thead><tr>")
        for h in ("Case", "Status", "Provider", "Account/KS", "Duplicate of"):
            extra.append(f"<th>{h}</th>")
        extra.append("</tr></thead><tbody>")
        for c in candidates[:30]:
            if not c.get("merge_recommended"):
                continue
            acct = (c.get("recommended_account") or {}).get("name") or c.get("gateway_sp") or "—"
            dup = (c.get("duplicate_of") or {}).get("case_number") or "—"
            extra.append(
                f"<tr><td>{c.get('case_number')}</td><td>{c.get('vet_status')}</td>"
                f"<td>{(c.get('provider') or '')[:40]}</td><td>{acct}</td><td>{dup}</td></tr>"
            )
        extra.append("</tbody></table></div>")

    block = "".join(extra)
    html = html.replace("<h2>Shell Account blockers</h2>", block + "<h2>Shell Account blockers</h2>")
    path.write_text(html, encoding="utf-8")


def _run_date() -> str:
    if os.environ.get("RUN_DATE"):
        return os.environ["RUN_DATE"]
    m = re.search(r"(\d{8})", VET_JSON.name)
    return m.group(1) if m else "20260730"


def render_vetted_html_shell(vetted: dict, path: Path) -> None:
    """Render shell-vetted HTML via render_shell_vetted_report_html (uses RUN_DATE paths)."""
    os.environ.setdefault("RUN_DATE", _run_date())
    if "VET_JSON_PATH" not in os.environ:
        os.environ["VET_JSON_PATH"] = str(VET_JSON)
    if "VETTED_JSON_PATH" not in os.environ:
        os.environ["VETTED_JSON_PATH"] = str(VETTED_JSON)
    if "VETTED_HTML_PATH" not in os.environ:
        os.environ["VETTED_HTML_PATH"] = str(path)
    sys.path.insert(0, str(SCRIPTS))
    from render_shell_vetted_report_html import main as render_shell_html  # noqa: E402

    render_shell_html()


def main() -> int:
    records = load_records(SF_CACHE)
    scope = os.environ.get(
        "SCAN_SCOPE",
        "CreatedDate >= 2026-06-26 (all org)",
    )

    from unified_sf_triage import (  # noqa: E402
        build_enriched_records,
        intake_target_ids,
        pull_intake_batch,
        run_duplicate_scan,
    )

    print("Phase 1: Seed duplicate clusters (subject/metadata)...", flush=True)
    seed_scan = run_duplicate_scan(records, sf_cache=str(SF_CACHE), scope=scope)

    run_date = os.environ.get("RUN_DATE", datetime.now(timezone.utc).strftime("%Y%m%d"))
    intake_packs_path = _path(
        "INTAKE_PACKS_PATH",
        TMP / f"intake-packs-allorg-{run_date}.json",
    )
    vet_checkpoint_path = _path(
        "VET_CHECKPOINT_PATH",
        TMP / f"shell-vet-checkpoint-allorg-{run_date}.json",
    )

    targets = intake_target_ids(records, seed_scan)
    if intake_packs_path.exists() and os.environ.get("FORCE_INTAKE") != "1":
        intake_packs = json.loads(intake_packs_path.read_text(encoding="utf-8"))
        print(
            f"Phase 2: Loaded {len(intake_packs)} cached intake packs "
            f"({intake_packs_path.name})",
            flush=True,
        )
    else:
        print(
            f"Phase 2: Full intake (email body + attachments) for {len(targets)} cases "
            f"(shell open + duplicate members)...",
            flush=True,
        )
        clear_intake_cache()
        intake_packs = pull_intake_batch(records, targets, load_case_intake)
        intake_packs_path.write_text(json.dumps(intake_packs, indent=2), encoding="utf-8")
        print(f"Saved intake packs -> {intake_packs_path}", flush=True)

    print("Phase 3: Duplicate clusters from intake-enriched context...", flush=True)
    enriched = build_enriched_records(records, intake_packs)
    dup_scan = run_duplicate_scan(
        enriched,
        sf_cache=str(SF_CACHE),
        scope=f"{scope} + email/attachment intake",
    )
    SCAN_OUT = _path("SCAN_JSON_PATH", PRIOR_SCAN)
    SCAN_OUT.write_text(json.dumps(dup_scan, indent=2), encoding="utf-8")

    print("Phase 4: Shell vetting (sp-inbound-vetting path)...", flush=True)
    vet = vet_shell_cases(
        records,
        dup_scan,
        intake_packs,
        checkpoint_path=vet_checkpoint_path,
    )

    vet["by_vet_status"] = dict(Counter(c.get("vet_status") for c in vet["cases"]).most_common())
    VET_JSON.write_text(json.dumps(vet, indent=2), encoding="utf-8")
    write_vet_report(vet, VET_MD)
    print(json.dumps(vet["by_vet_status"], indent=2))

    print("Phase 5: Building vetted duplicate report...", flush=True)
    vetted = build_vetted_scan(dup_scan, vet)
    VETTED_JSON.write_text(json.dumps(vetted, indent=2), encoding="utf-8")
    write_vetted_markdown(vetted, VETTED_MD)

    print("Phase 6: Rendering HTML...", flush=True)
    render_vetted_html_shell(vetted, VETTED_HTML)

    print(f"VET_JSON: {VET_JSON.resolve()}")
    print(f"VET_MD: {VET_MD.resolve()}")
    print(f"VETTED_JSON: {VETTED_JSON.resolve()}")
    print(f"VETTED_MD: {VETTED_MD.resolve()}")
    print(f"VETTED_HTML: {VETTED_HTML.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
