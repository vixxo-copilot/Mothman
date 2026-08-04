#!/usr/bin/env python3
"""Render shell-vetted SF duplicate scan with full vet breakdown."""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

TMP = Path(__file__).resolve().parent
sys.path.insert(0, str(TMP))
from render_sf_duplicate_report_html import (  # noqa: E402
    case_link,
    esc,
    render_table,
    stat_card,
)

RUN_DATE = os.environ.get("RUN_DATE", "20260730")
TMP_ROOT = Path(__file__).resolve().parent


def _path(env_key: str, default: Path) -> Path:
    v = os.environ.get(env_key)
    return Path(v) if v else default


VET_JSON = _path("VET_JSON_PATH", TMP_ROOT / f"shell-account-vet-allorg-{RUN_DATE}.json")
VETTED_JSON = _path("VETTED_JSON_PATH", TMP_ROOT / f"sf-intra-duplicate-scan-allorg-vetted-{RUN_DATE}.json")
COI_PDF_JSON = _path("COI_PDF_JSON_PATH", TMP_ROOT / f"shell-coi-pdf-extraction-allorg-{RUN_DATE}.json")
SENDER_MCP_JSON = _path("SENDER_MCP_JSON_PATH", TMP_ROOT / f"shell-sender-email-enrichment-allorg-{RUN_DATE}.json")
BROKER_VET_JSON = _path("BROKER_VET_JSON_PATH", TMP_ROOT / f"shell-broker-carrier-vet-allorg-{RUN_DATE}.json")
OUT_HTML = _path("VETTED_HTML_PATH", TMP_ROOT / f"sf-intra-duplicate-scan-allorg-vetted-{RUN_DATE}.html")


def manual_reason(entry: dict) -> str:
    if entry.get("vet_status") != "needs_manual":
        return ""
    hints = entry.get("hints") or {}
    company = hints.get("company") or hints.get("provider")
    if company:
        if not entry.get("account_search_candidates"):
            return "Company in subject — SF Account search returned no match"
        return "Company in subject — multiple SF hits, none confident enough"
    if hints.get("email_domain") and not company:
        return f"Broker/carrier sender only ({hints['email_domain']}) — no SP name in subject"
    if hints.get("sr_number"):
        return "SR reference only — needs SR routing review"
    return "No company name, KS#, or usable email domain extracted"


def render_shell_vet_section(vet: dict) -> str:
    cases = vet.get("cases") or []
    by_status = Counter(c.get("vet_status") for c in cases)
    manual = [c for c in cases if c.get("vet_status") == "needs_manual"]
    for c in manual:
        c["manual_reason"] = manual_reason(c)
    reason_counts = Counter(c["manual_reason"] for c in manual)

    resolved = [c for c in cases if c.get("vet_status") == "account_resolved"]
    gateway = [c for c in cases if c.get("vet_status") == "gateway_match"]

    needs_manual_count = by_status.get("needs_manual", 0)
    account_resolved_count = by_status.get("account_resolved", 0)
    gateway_match_count = by_status.get("gateway_match", 0)
    enrichment = vet.get("enrichment_summary") or {}

    parts = [
        "<h2>Shell Account vetting</h2>",
        "<div class='card'>",
        f"<p class='warn-box'><strong>needs_manual ({needs_manual_count})</strong> means "
        "<em>no SF Account and no Gateway SP were identified</em> for that Case. "
        f"Account was found for {account_resolved_count} Cases (<code>account_resolved</code>) and "
        f"Gateway KS# for {gateway_match_count} (<code>gateway_match</code>). "
        "Pass 1 used SF Account LIKE search and Gateway on Federated COI + onboarding/KS Cases; "
        "unified enrichment adds COI PDF insured extraction and sender-email MCP lookup.</p>",
        "<div class='stats'>",
        stat_card("Shell open vetted", len(cases)),
        stat_card("Account resolved", account_resolved_count, "ok"),
        stat_card("Gateway match", gateway_match_count, "ok"),
        stat_card("Needs manual", needs_manual_count, "warn"),
        stat_card("SR routing", by_status.get("sr_routing", 0)),
        stat_card("Onboarding", by_status.get("onboarding", 0)),
        stat_card("Auto-reply noise", by_status.get("auto_reply_noise", 0)),
        stat_card("Dup cluster", by_status.get("duplicate_cluster", 0), "ok"),
        "</div></div>",
    ]
    if enrichment:
        parts.extend(
            [
                "<div class='card'><div class='stats'>",
                stat_card("COI PDF scanned", enrichment.get("coi_pdf_cases", 0)),
                stat_card("COI PDF resolved", enrichment.get("coi_pdf_resolved", 0), "ok"),
                stat_card("Sender MCP tried", enrichment.get("sender_mcp_cases", 0)),
                stat_card("Sender MCP resolved", enrichment.get("sender_mcp_resolved", 0), "ok"),
                "</div></div>",
            ]
        )

    if reason_counts:
        rows = [[esc(r), esc(n)] for r, n in reason_counts.most_common()]
        parts.append(f"<h3>Why {needs_manual_count} need manual review</h3><div class='card'>")
        parts.append(render_table(["Reason", "Count"], rows, {1}))
        parts.append("</div>")

    if resolved:
        rows = []
        for c in resolved[:40]:
            acct = (c.get("recommended_account") or {}).get("name") or "—"
            hint = (c.get("hints") or {}).get("company") or (c.get("hints") or {}).get("provider") or "—"
            rows.append(
                [
                    case_link({"case_number": c.get("case_number"), "id": c.get("id")}),
                    esc(acct),
                    esc(str(hint)[:45]),
                    esc((c.get("subject") or "")[:50]),
                ]
            )
        parts.append(
            f"<h3>Account resolved — recommended SF Account ({account_resolved_count})</h3><div class='card'>"
        )
        parts.append(
            "<p class='muted'>These need Account correction on the Case, not duplicate merge.</p>"
        )
        parts.append(render_table(["Case", "Recommended Account", "Hint used", "Subject"], rows))
        if len(resolved) > 40:
            parts.append(f"<p class='muted'>… and {len(resolved) - 40} more in vet JSON.</p>")
        parts.append("</div>")

    if gateway:
        rows = []
        for c in gateway[:20]:
            rows.append(
                [
                    case_link({"case_number": c.get("case_number"), "id": c.get("id")}),
                    esc(c.get("gateway_sp") or "—"),
                    esc(c.get("gateway_name") or "—"),
                    esc((c.get("subject") or "")[:50]),
                ]
            )
        parts.append(f"<h3>Gateway match ({gateway_match_count})</h3><div class='card'>")
        parts.append(render_table(["Case", "KS#", "SP name", "Subject"], rows))
        parts.append("</div>")

    manual_rows = []
    for c in manual[:35]:
        manual_rows.append(
            [
                case_link({"case_number": c.get("case_number"), "id": c.get("id")}),
                esc(c.get("manual_reason", "")[:55]),
                esc((c.get("contact_email") or "—")[:35]),
                esc((c.get("subject") or "")[:45]),
            ]
        )
    if manual_rows:
        parts.append("<h3>Manual review sample (no account identified)</h3><div class='card'>")
        parts.append(render_table(["Case", "Why manual", "Contact email", "Subject"], manual_rows))
        if len(manual) > 35:
            parts.append(f"<p class='muted'>… and {len(manual) - 35} more in shell-account-vet-allorg JSON.</p>")
        parts.append("</div>")

    return "".join(parts)


def render_coi_pdf_section(extract: dict) -> str:
    results = extract.get("results") or []
    if not results:
        return ""
    by_status = extract.get("by_post_pdf_status") or {}
    insured = sum(1 for r in results if r.get("legal_insured"))
    resolved = [r for r in results if r.get("recommended_account")]
    insured_no_acct = [r for r in results if r.get("legal_insured") and not r.get("recommended_account")]

    parts = [
        "<h2>COI PDF insured extraction</h2>",
        "<div class='card'>",
        "<p class='muted'>ACORD/cert PDF scan on COI-titled shell Cases — "
        "insured name from certificate, then SF Service Provider Account search.</p>",
        "<div class='stats'>",
        stat_card("Cases scanned", len(results)),
        stat_card("Insured from PDF", insured, "ok"),
        stat_card("Account matched", len(resolved), "ok"),
        stat_card("Insured, no account", len(insured_no_acct), "warn"),
        stat_card(
            "No PDF / parse fail",
            sum(1 for r in results if r.get("extraction_error")),
            "warn",
        ),
        "</div></div>",
    ]

    if resolved:
        rows = []
        for r in resolved[:35]:
            rows.append(
                [
                    case_link({"case_number": r.get("case_number"), "id": r.get("case_id")}),
                    esc((r.get("legal_insured") or "")[:45]),
                    esc((r.get("recommended_account") or {}).get("name", "")[:45]),
                    esc(r.get("account_match_score")),
                ]
            )
        parts.append("<h3>PDF → Account resolved</h3><div class='card'>")
        parts.append(render_table(["Case", "Insured (PDF)", "SF Account", "Score"], rows))
        parts.append("</div>")

    if insured_no_acct:
        rows = []
        for r in insured_no_acct[:25]:
            dba = ", ".join(r.get("dba_names") or []) or "—"
            rows.append(
                [
                    case_link({"case_number": r.get("case_number"), "id": r.get("case_id")}),
                    esc((r.get("legal_insured") or "")[:50]),
                    esc(dba[:35]),
                    esc(r.get("extraction_error") or "no SF match"),
                ]
            )
        parts.append("<h3>Insured from PDF — no SF Account yet</h3><div class='card'>")
        parts.append(render_table(["Case", "Insured (PDF)", "DBA", "Note"], rows))
        parts.append("</div>")

    return "".join(parts)


def render_sender_mcp_section(extract: dict) -> str:
    results = extract.get("results") or []
    if not results:
        return ""
    resolved = [r for r in results if r.get("recommended_account")]
    gw_only = [
        r
        for r in results
        if (r.get("gateway_sp") or r.get("vixxolink_sp")) and not r.get("recommended_account")
    ]
    parts = [
        "<h2>Sender email — Gateway + VixxoLink</h2>",
        "<div class='card'>",
        "<p class='muted'>SP lookup from Case contact email via VixxoNow Gateway invoice search "
        "and VixxoLink user/site-access lookup; then SF Account match when KS/name resolves.</p>",
        "<div class='stats'>",
        stat_card("Cases tried", len(results)),
        stat_card("Account resolved", len(resolved), "ok"),
        stat_card("KS/name only", len(gw_only), "warn"),
        stat_card(
            "Skipped (carrier/system)",
            sum(1 for r in results if r.get("skip_reason")),
        ),
        "</div></div>",
    ]
    if resolved:
        rows = []
        for r in resolved[:30]:
            rows.append(
                [
                    case_link({"case_number": r.get("case_number"), "id": r.get("case_id")}),
                    esc((r.get("contact_email") or "")[:32]),
                    esc(r.get("gateway_sp") or r.get("vixxolink_sp") or "—"),
                    esc((r.get("recommended_account") or {}).get("name", "")[:40]),
                ]
            )
        parts.append("<h3>Sender MCP → Account resolved</h3><div class='card'>")
        parts.append(render_table(["Case", "Email", "KS#", "SF Account"], rows))
        parts.append("</div>")
    if gw_only:
        rows = []
        for r in gw_only[:20]:
            rows.append(
                [
                    case_link({"case_number": r.get("case_number"), "id": r.get("case_id")}),
                    esc((r.get("contact_email") or "")[:30]),
                    esc(r.get("gateway_sp") or r.get("vixxolink_sp") or "—"),
                    esc((r.get("gateway_name") or r.get("vixxolink_name") or "")[:35]),
                ]
            )
        parts.append("<h3>Sender MCP — KS/name, no SF Account</h3><div class='card'>")
        parts.append(render_table(["Case", "Email", "KS#", "SP name"], rows))
        parts.append("</div>")
    return "".join(parts)


def vet_source_label(case: dict) -> str:
    vs = case.get("vet_source")
    if vs == "coi_pdf_extraction":
        return "coi_pdf_extraction"
    if vs == "sender_email_mcp":
        return "sender_email_mcp"
    if case.get("vet_status") == "gateway_match":
        return "gateway_match (pass1)"
    if case.get("vet_status") == "account_resolved":
        return "pass1"
    return vs or "pass1"


def resolution_chain(case: dict) -> str:
    """Build hint chain: subject | PDF insured | sender domain → Account/KS."""
    hints = case.get("hints") or {}
    chain: list[str] = []
    subj = hints.get("company") or hints.get("provider")
    if subj:
        chain.append(f"subject: {subj}")
    coi = case.get("coi_pdf") or {}
    if coi.get("legal_insured"):
        chain.append(f"PDF: {coi['legal_insured']}")
    sender = case.get("sender_mcp") or {}
    email = sender.get("contact_email") or case.get("contact_email")
    if email:
        domain = email.split("@", 1)[-1] if "@" in email else email
        chain.append(f"sender: {domain}")
    if case.get("recommended_account"):
        dest = (case["recommended_account"] or {}).get("name") or "Account"
    elif case.get("gateway_sp"):
        dest = case.get("gateway_sp")
        if case.get("gateway_name"):
            dest = f"{dest} ({case['gateway_name']})"
    else:
        dest = "—"
    return " → ".join([(" | ".join(chain) if chain else "no hints"), dest])


def coi_sidecar_or_vet(vet: dict) -> dict:
    """Prefer sidecar JSON; fall back to coi_pdf fields embedded in vet cases."""
    if COI_PDF_JSON.is_file():
        return json.loads(COI_PDF_JSON.read_text(encoding="utf-8"))
    results = []
    for c in vet.get("cases") or []:
        coi = c.get("coi_pdf")
        if not coi:
            continue
        results.append(
            {
                "case_id": c.get("id"),
                "case_number": c.get("case_number"),
                "subject": c.get("subject"),
                "legal_insured": coi.get("legal_insured"),
                "dba_names": coi.get("dba_names"),
                "extraction_error": coi.get("extraction_error"),
                "recommended_account": c.get("recommended_account")
                if c.get("vet_source") == "coi_pdf_extraction"
                else None,
                "account_match_score": None,
                "post_pdf_vet_status": coi.get("post_pdf_vet_status"),
            }
        )
    if not results:
        return {}
    return {
        "results": results,
        "by_post_pdf_status": dict(
            Counter(r.get("post_pdf_vet_status") for r in results).most_common()
        ),
    }


def sender_sidecar_or_vet(vet: dict) -> dict:
    """Prefer sidecar JSON; fall back to sender_mcp fields embedded in vet cases."""
    if SENDER_MCP_JSON.is_file():
        return json.loads(SENDER_MCP_JSON.read_text(encoding="utf-8"))
    results = []
    for c in vet.get("cases") or []:
        sender = c.get("sender_mcp")
        if not sender:
            continue
        results.append(
            {
                "case_id": c.get("id"),
                "case_number": c.get("case_number"),
                "contact_email": sender.get("contact_email"),
                "gateway_sp": sender.get("gateway_sp"),
                "gateway_name": sender.get("gateway_name"),
                "vixxolink_sp": sender.get("vixxolink_sp"),
                "vixxolink_name": sender.get("vixxolink_name"),
                "recommended_account": c.get("recommended_account")
                if c.get("vet_source") == "sender_email_mcp"
                else None,
                "skip_reason": None,
                "post_email_vet_status": sender.get("post_email_vet_status"),
            }
        )
    if not results:
        return {}
    return {"results": results}


def render_provider_resolution_section(vet: dict) -> str:
    """Unified provider resolution grouped by vet_source with resolution chains."""
    resolved_statuses = {"account_resolved", "gateway_match"}
    cases = [
        c
        for c in vet.get("cases") or []
        if c.get("vet_status") in resolved_statuses
        or c.get("vet_source") in ("coi_pdf_extraction", "sender_email_mcp")
    ]
    if not cases:
        return ""

    by_source: dict[str, list[dict]] = {}
    for c in cases:
        label = vet_source_label(c)
        by_source.setdefault(label, []).append(c)

    parts = [
        "<h2>Provider resolution</h2>",
        "<div class='card'>",
        "<p class='muted'>Cases where a Service Provider was identified, grouped by resolution "
        "source. Chain shows subject hint → PDF insured → sender domain → SF Account or KS#.</p>",
        "<div class='stats'>",
    ]
    source_order = [
        "pass1",
        "gateway_match (pass1)",
        "coi_pdf_extraction",
        "sender_email_mcp",
    ]
    for src in source_order:
        group = by_source.get(src, [])
        if group:
            parts.append(stat_card(src.replace("_", " "), len(group), "ok"))
    for src, group in sorted(by_source.items()):
        if src not in source_order:
            parts.append(stat_card(src.replace("_", " "), len(group), "ok"))
    parts.append("</div></div>")

    for src in source_order + [s for s in by_source if s not in source_order]:
        group = by_source.get(src)
        if not group:
            continue
        rows = []
        for c in group[:35]:
            acct = (c.get("recommended_account") or {}).get("name") or c.get("gateway_sp") or "—"
            rows.append(
                [
                    case_link({"case_number": c.get("case_number"), "id": c.get("id")}),
                    esc(c.get("vet_status") or "—"),
                    esc(resolution_chain(c)[:90]),
                    esc(str(acct)[:45]),
                ]
            )
        parts.append(f"<h3>{esc(src)} ({len(group)})</h3><div class='card'>")
        parts.append(render_table(["Case", "Status", "Resolution chain", "Account / KS"], rows))
        if len(group) > 35:
            parts.append(f"<p class='muted'>… and {len(group) - 35} more in vet JSON.</p>")
        parts.append("</div>")

    return "".join(parts)


def render_broker_vet_section(data: dict) -> str:
    results = data.get("results") or []
    if not results:
        return ""
    resolved = [r for r in results if r.get("recommended_account")]
    gw = [r for r in results if r.get("gateway_sp") and not r.get("recommended_account")]
    no_hint = [r for r in results if r.get("vet_status") == "needs_manual_broker_no_hint"]
    parts = [
        "<h2>Broker / carrier COI vet</h2>",
        "<div class='card'>",
        "<p class='muted'>Carrier/broker senders (csr24, fedcerts, agents) — SP resolved from "
        "subject, email body (<code>our client</code>), and COI PDF / attachment filename — "
        "not from sender email alone.</p>",
        "<div class='stats'>",
        stat_card("Cases reviewed", len(results)),
        stat_card("Account resolved", len(resolved), "ok"),
        stat_card("Gateway KS only", len(gw), "warn"),
        stat_card("No SP hint", len(no_hint), "warn"),
        "</div></div>",
    ]
    if resolved:
        rows = []
        for r in resolved[:35]:
            hint = (r.get("sp_hints") or ["—"])[0]
            rows.append(
                [
                    case_link({"case_number": r.get("case_number"), "id": r.get("case_id")}),
                    esc((r.get("contact_email") or "")[:28]),
                    esc(hint[:40]),
                    esc((r.get("recommended_account") or {}).get("name", "")[:40]),
                ]
            )
        parts.append("<h3>Broker/carrier → Account resolved</h3><div class='card'>")
        parts.append(render_table(["Case", "Sender", "SP hint", "SF Account"], rows))
        parts.append("</div>")
    if no_hint:
        rows = []
        for r in no_hint[:15]:
            rows.append(
                [
                    case_link({"case_number": r.get("case_number"), "id": r.get("case_id")}),
                    esc((r.get("subject") or "")[:50]),
                    esc((r.get("contact_email") or "")[:28]),
                ]
            )
        parts.append("<h3>Still needs manual COI PDF review</h3><div class='card'>")
        parts.append(render_table(["Case", "Subject", "Sender"], rows))
        parts.append("</div>")
    return "".join(parts)


def main() -> int:
    vetted = json.loads(VETTED_JSON.read_text(encoding="utf-8"))
    vet = json.loads(VET_JSON.read_text(encoding="utf-8"))

    from render_sf_duplicate_report_html import render_html  # noqa: E402

    html = render_html(vetted)
    vs = vetted.get("vetting_summary") or {}
    dup_extra = [
        "<h2>Duplicate groups after shell vet</h2><div class='card'><div class='stats'>",
        stat_card("Before vet", vs.get("actionable_duplicate_groups_before", 0)),
        stat_card("After vet", vs.get("actionable_duplicate_groups_after", 0), "ok"),
        stat_card("Merge recommended", vs.get("shell_merge_recommended_count", 0), "ok"),
        "</div></div>",
    ]
    candidates = vetted.get("shell_vetted_duplicate_candidates") or []
    merge_rows = []
    for c in candidates:
        if not c.get("merge_recommended"):
            continue
        acct = (c.get("recommended_account") or {}).get("name") or c.get("gateway_sp") or "—"
        dup = (c.get("duplicate_of") or {}).get("case_number") or "—"
        merge_rows.append(
            [
                case_link({"case_number": c.get("case_number"), "id": c.get("id")}),
                esc(c.get("vet_status")),
                esc(acct),
                esc(dup),
            ]
        )
    if merge_rows:
        dup_extra.append("<h3>Shell-vetted merge recommended</h3><div class='card'>")
        dup_extra.append(render_table(["Case", "Vet status", "Account/KS", "Duplicate of"], merge_rows))
        dup_extra.append("</div>")

    shell_section = render_shell_vet_section(vet)
    provider_section = render_provider_resolution_section(vet)
    coi_data = coi_sidecar_or_vet(vet)
    coi_pdf_section = render_coi_pdf_section(coi_data) if coi_data else ""
    sender_data = sender_sidecar_or_vet(vet)
    sender_section = render_sender_mcp_section(sender_data) if sender_data else ""
    broker_section = ""
    if BROKER_VET_JSON.is_file():
        broker_section = render_broker_vet_section(json.loads(BROKER_VET_JSON.read_text(encoding="utf-8")))
    insert = (
        shell_section
        + provider_section
        + coi_pdf_section
        + sender_section
        + broker_section
        + "".join(dup_extra)
    )
    html = html.replace("<h2>Summary</h2>", insert + "<h2>Summary</h2>")
    html = html.replace(
        "<title>SF Duplicate Scan — Mothman</title>",
        "<title>SF Duplicate Scan (Shell-Vetted) — Mothman</title>",
    )
    html = html.replace(
        "SF <span class='ember-text'>Duplicate</span> Scan</h1>",
        "SF <span class='ember-text'>Duplicate</span> Scan <span class='tag ok'>Shell-Vetted</span></h1>",
    )

    OUT_HTML.write_text(html, encoding="utf-8")
    print(OUT_HTML.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
