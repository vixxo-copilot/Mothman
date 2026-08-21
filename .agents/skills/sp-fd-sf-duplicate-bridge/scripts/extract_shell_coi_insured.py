#!/usr/bin/env python3
"""Extract insured name from COI PDFs on open Shell Account cases (report only).

Batching (recommended — avoids SF CLI / PDF bog-down on large shell sets):

  RUN_DATE=YYYYMMDD python extract_shell_coi_insured.py --batch-size 10
  RUN_DATE=YYYYMMDD python extract_shell_coi_insured.py --batch-size 10 --offset 10
  RUN_DATE=YYYYMMDD python extract_shell_coi_insured.py --resume   # skip case_ids already in OUT_JSON

Env: COI_BATCH_SIZE (default 15), COI_OFFSET, COI_LIMIT, COI_RESUME=1
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPTS.parent
TMP = SKILL_ROOT / ".tmp"
VETTING = SKILL_ROOT.parent / "sp-inbound-vetting" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(VETTING))

import scan_duplicates as sd  # noqa: E402
from shell_sf_intake import company_candidates_from_intake, load_case_intake  # noqa: E402

SF = os.path.expandvars(r"%APPDATA%\npm\sf.cmd")
ORG = "vixxo"
RUN_DATE = os.environ.get("RUN_DATE", "20260730")
TMP_ROOT = TMP


def _path(env_key: str, default: Path) -> Path:
    v = os.environ.get(env_key)
    return Path(v) if v else default


VET_JSON = _path("VET_JSON_PATH", TMP_ROOT / f"shell-account-vet-allorg-{RUN_DATE}.json")
OUT_JSON = _path("COI_PDF_JSON_PATH", TMP_ROOT / f"shell-coi-pdf-extraction-allorg-{RUN_DATE}.json")
OUT_MD = _path("COI_PDF_MD_PATH", TMP_ROOT / f"shell-coi-pdf-extraction-report-allorg-{RUN_DATE}.md")
PDF_DIR = _path("COI_PDF_DIR", TMP_ROOT / f"shell-coi-pdfs-{RUN_DATE}")
COI_SUBJECT = re.compile(
    r"coi|certificate of insurance|proof of insurance|renewal cert|acord|"
    r"additional insured|certificate -",
    re.I,
)
PREFIX_RE = re.compile(r"^(?:ks|cconly|ccpay|stryker)\s*-\s*", re.I)
SUFFIX_RE = re.compile(
    r"\b(LLC|L\.L\.C\.|Inc\.?|Incorporated|Corp\.?|Corporation|Co\.?,?\s*Inc\.?|Company|Ltd\.?|Limited)\b",
    re.I,
)
ACCOUNT_PREFIXES = ("KS - ", "CCONLY - ", "CCPAY - ", "STRYKER - ")
HOLDER_NAMES = {"vixxo corporation", "vixxo corp", "vixxo"}
INSURED_BOILERPLATE = re.compile(
    r"named above|insurer\s+[a-f-z]\s*:|under your|certificate holder|"
    r"^the$|^for the$|policy number|coverages|effective date|legal address|"
    r"endorsement number|first shown in|supplemental|subrogation|provisions or|"
    r"be endorsed|under this|during the|on such other|cancels the|insurer b|"
    r"shown in the declarations|receives notice from us|waived subject",
    re.I,
)
SUBJECT_RENEWAL_COI_RE = re.compile(
    r"^(.+?)\s*-\s*Renewal\s+(?:COI|Certificate)",
    re.I,
)
SUBJECT_CERT_DASH_RE = re.compile(
    r"^(?:Certificate|Renewal Certificate)\s*-\s*(.+?)(?:\s*-\s*Vixxo|\s*$)",
    re.I,
)
SUBJECT_COI_FOR_RE = re.compile(
    r"^(?:COI|Certificate of Insurance|Proof of Insurance)\s+for\s+(.+?)(?:\s*-\s*Vixxo|\s*$)",
    re.I,
)
FILENAME_CSR24_RE = re.compile(r"^(.+?)_(?:Vixxo|VIXXO)", re.I)
FILENAME_SP_RE = re.compile(
    r"_(?:Vixxo[^_]*_)?(.+?)(?:,\s*DBA|_DBA|_Until|\s+Until\s|\.\w+$)",
    re.I,
)
# Broker packets: "Vixxo Corporation_The Pelczar Corporation_'26-27 GL_..."
FILENAME_VIXXO_FIRST_RE = re.compile(
    r"^(?:Vixxo(?:\s+Corporation)?|VIXXO)_(.+?)(?:_['\"`]?\d|_Until|_GL\b|_WC\b|_Auto\b|\.\w+$)",
    re.I,
)
COMPANY_LINE_RE = re.compile(
    r"\b(Corporation|Corp\.?|Incorporated|Inc\.?|LLC|L\.L\.C\.|Ltd\.?|Limited|Company|Co\.?)\s*$",
    re.I,
)
ADDRESS_LINE_RE = re.compile(
    r"^(?:\d+\s+\w|P\.?\s*O\.?\s*Box\b|Suite\b|Ste\.?\b)",
    re.I,
)
JUNK_INSURED_LINE_RE = re.compile(
    r"^(REVISION|CERTIFICATE\s*NUMBER|COVERAGES|IMPORTANT|THIS CERTIFICATE|"
    r"DATE\s*\(|ACORD|CONTACT|PRODUCER|PHONE|FAX|E-MAIL|ADDRESS:|NAME:|"
    r"INSURER|NAIC|POLICY|LIMITS|"
    r"COMMERCIAL\s+(GENERAL|LIABILITY|AUTO|PROPERTY|UMBRELLA)|"
    r"AUTOMOBILE|WORKERS)\b",
    re.I,
)
BROKER_PRODUCER_RE = re.compile(
    r"\b(Insurance\s+Brokers?|Insurance\s+Agency|Insurance\s+Services|"
    r"Insurance\s+Group|Insurance\s+Company|Underwriters?|Brokerage)\b",
    re.I,
)
NOISE = {
    "the", "and", "of", "for", "dba", "llc", "inc", "corp", "co", "ltd", "company",
    "service", "services", "insured", "address", "city", "state", "zip",
    "subsidiary", "subsidiaries", "topco", "holding", "holdings", "lp", "l.p",
}
HOLDING_OPERATING_RE = re.compile(
    r"\band\s+subsidiar(?:y|ies)\s+(.+)$",
    re.I,
)


def sf_json(args: list[str]) -> dict:
    proc = subprocess.run(
        [SF, *args, "--target-org", ORG, "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        raise RuntimeError(proc.stderr or proc.stdout[:500])
    if proc.returncode != 0 or data.get("status", 0) != 0:
        raise RuntimeError(json.dumps(data, indent=2)[:800])
    return data


def sf_query(soql: str) -> list[dict]:
    return sf_json(["data", "query", "--query", soql])["result"]["records"]


def esc(s: str) -> str:
    return (s or "").replace("\\", "\\\\").replace("'", "\\'")


def pdf_text(data: bytes) -> tuple[str, str | None]:
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(BytesIO(data))
        return "\n".join((p.extract_text() or "") for p in reader.pages), None
    except Exception as exc:
        return data.decode("latin-1", errors="ignore"), str(exc)


def clean_line(line: str) -> str:
    line = re.sub(r"\s+", " ", (line or "").strip())
    line = re.sub(r"^(INSURED|NAMED INSURED)\s*:?\s*", "", line, flags=re.I)
    return line.strip(" :;,")


def is_holder_or_noise(name: str) -> bool:
    n = name.lower().strip()
    if not n or len(n) < 3:
        return True
    # Email-thread crumbs / empty shells
    if re.fullmatch(r"(re|fw|fwd|aw|rv)\s*:?", n, re.I):
        return True
    if re.fullmatch(r"(revised|updated|renewal|new|coi|certificate)", n, re.I):
        return True
    if n in HOLDER_NAMES or n.startswith("vixxo "):
        return True
    if INSURED_BOILERPLATE.search(n):
        return True
    if JUNK_INSURED_LINE_RE.search(n):
        return True
    if BROKER_PRODUCER_RE.search(n):
        return True
    if re.match(r"^\d{5}", n):
        return True
    if re.match(r"^(street|po box|suite|scottsdale|address)\b", n, re.I):
        return True
    return False


def extract_company_before_address(lines: list[str]) -> str | None:
    """ACORD text extractors often dump insured near street address, far from INSURED label.

    PDF extract order is frequently scrambled — CERTIFICATE HOLDER may appear
    before the insured block — so scan all company+address pairs and prefer
    non-Vixxo / non-holder names.
    """
    candidates: list[str] = []
    for i, ln in enumerate(lines):
        if is_holder_or_noise(ln) or not COMPANY_LINE_RE.search(ln):
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if nxt and ADDRESS_LINE_RE.search(nxt):
            candidates.append(ln)
    for cand in candidates:
        if not is_holder_or_noise(cand) and "vixxo" not in cand.lower():
            return cand
    return candidates[0] if candidates else None


def extract_insured_fields(text: str) -> dict:
    raw = text or ""
    flat = re.sub(r"[ \t]+", " ", raw)
    lines = [clean_line(ln) for ln in raw.splitlines()]
    lines = [ln for ln in lines if ln]

    legal = None
    dba_names: list[str] = []
    alternate_names: list[str] = []
    method = None

    # Block after INSURED label (line-oriented ACORD layout)
    for i, ln in enumerate(lines):
        if re.fullmatch(r"INSURED", ln, re.I) or ln.upper() == "INSURED":
            block = []
            for nxt in lines[i + 1 : i + 8]:
                if re.match(
                    r"^(POLICY|INSURER|COVERAGES|CERTIFICATE HOLDER|DATE|REVISION|IMPORTANT)\b",
                    nxt,
                    re.I,
                ):
                    break
                if JUNK_INSURED_LINE_RE.search(nxt):
                    break
                if not is_holder_or_noise(nxt):
                    block.append(nxt)
            if block and is_valid_insured(block[0]):
                legal = block[0]
                method = "line_after_insured"
                for extra in block[1:]:
                    m = re.match(r"(?:D/B/A|DBA)\s+(.+)", extra, re.I)
                    if m:
                        dba_names.append(m.group(1).strip())
                    elif not is_holder_or_noise(extra) and not ADDRESS_LINE_RE.search(extra):
                        alternate_names.append(extra)
            break

    # Company name immediately above a street address (jumbled ACORD extract)
    if not legal:
        cand = extract_company_before_address(lines)
        if cand and is_valid_insured(cand):
            legal = cand
            method = "company_before_address"

    # Regex fallback on flattened text
    if not legal:
        for pat in (
            r"INSURED\s+(?:ADDRESS\s*)?(.{3,120}?)\s+(?:POLICY|INSURER|COVERAGES|CERTIFICATE HOLDER)",
            r"Named Insured[:\s]+(.{3,120}?)\s+(?:Policy|Insurer|Certificate Holder)",
        ):
            m = re.search(pat, flat, re.I)
            if m:
                cand = clean_line(m.group(1))
                if is_valid_insured(cand):
                    legal = cand.split(" D/B/A")[0].split(" DBA ")[0].strip()
                    method = "regex_block"
                    break

    if legal:
        dba_inline = re.findall(r"(?:D/B/A|DBA)\s+([^;\n]+)", raw, re.I)
        for d in dba_inline:
            d = clean_line(d)
            if d and d not in dba_names:
                dba_names.append(d)

    return {
        "legal_insured": legal,
        "dba_names": list(dict.fromkeys(dba_names)),
        "alternate_names": list(dict.fromkeys(alternate_names)),
        "extraction_method": method,
        "text_chars": len(raw),
    }


def list_case_pdfs(case_id: str) -> list[dict]:
    rows = sf_query(
        "SELECT ContentDocumentId, ContentDocument.Title, ContentDocument.FileExtension, "
        "ContentDocument.ContentSize, LinkedEntityId "
        f"FROM ContentDocumentLink WHERE LinkedEntityId = '{case_id}' "
        "ORDER BY ContentDocument.CreatedDate DESC"
    )
    pdfs = []
    for row in rows:
        cd = row.get("ContentDocument") or {}
        ext = (cd.get("FileExtension") or "").lower()
        title = (cd.get("Title") or "").lower()
        if ext == "pdf" or title.endswith(".pdf") or "coi" in title or "cert" in title or "acord" in title:
            pdfs.append(
                {
                    "content_document_id": row["ContentDocumentId"],
                    "title": cd.get("Title"),
                    "extension": ext,
                    "size": cd.get("ContentSize"),
                    "source": "case",
                }
            )
    return pdfs


def list_email_pdfs(case_id: str) -> list[dict]:
    emails = sf_query(
        f"SELECT Id, Subject, HasAttachment FROM EmailMessage "
        f"WHERE (ParentId = '{case_id}' OR RelatedToId = '{case_id}') "
        "AND HasAttachment = true ORDER BY CreatedDate DESC LIMIT 10"
    )
    pdfs = []
    for em in emails:
        eid = em["Id"]
        links = sf_query(
            "SELECT ContentDocumentId, ContentDocument.Title, ContentDocument.FileExtension, "
            "ContentDocument.ContentSize "
            f"FROM ContentDocumentLink WHERE LinkedEntityId = '{eid}'"
        )
        for row in links:
            cd = row.get("ContentDocument") or {}
            ext = (cd.get("FileExtension") or "").lower()
            if ext == "pdf":
                pdfs.append(
                    {
                        "content_document_id": row["ContentDocumentId"],
                        "title": cd.get("Title"),
                        "extension": ext,
                        "size": cd.get("ContentSize"),
                        "source": f"email:{eid}",
                    }
                )
    return pdfs


def download_pdf(doc_id: str, dest: Path) -> bool:
    if dest.is_file() and dest.stat().st_size > 0:
        return True
    cv = sf_query(
        "SELECT Id FROM ContentVersion "
        f"WHERE ContentDocumentId = '{doc_id}' AND IsLatest = true LIMIT 1"
    )
    if not cv:
        return False
    cv_id = cv[0]["Id"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [
            SF,
            "api",
            "request",
            "rest",
            f"/services/data/v67.0/sobjects/ContentVersion/{cv_id}/VersionData",
            "-o",
            ORG,
            "-X",
            "GET",
            "-S",
            str(dest),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0 and dest.is_file() and dest.stat().st_size > 0


def norm(name: str) -> str:
    s = name.lower()
    s = PREFIX_RE.sub("", s)
    s = re.sub(r"[^a-z0-9&]+", " ", s)
    s = SUFFIX_RE.sub("", s)
    return re.sub(r"\s+", " ", s).strip()


def tokens(name: str) -> set[str]:
    return {t for t in norm(name).split() if len(t) > 2 and t not in NOISE}


def operating_company_aliases(name: str | None) -> list[str]:
    """Peel holding-company COI strings to the operating SP.

    Example: "Palmetto Topco L.P. and Subsidiaries Commercial Foodservice Repair Inc."
    → "Commercial Foodservice Repair Inc."
    """
    if not name:
        return []
    out: list[str] = []
    m = HOLDING_OPERATING_RE.search(name.strip())
    if m:
        op = m.group(1).strip(" ,.-")
        if op and is_valid_insured(op):
            out.append(op)
    return out


def search_variants(name: str) -> list[str]:
    base = re.sub(r"\s+d/b/a.*", "", name, flags=re.I).strip()
    out = [base, re.sub(r"\s+", " ", re.sub(r"[,.\-/&']", " ", base)).strip()]
    for suffix in (" LLC", " Inc.", " Inc", " LLC.", ", LLC", ", Inc.", " INC", " Company"):
        if base.endswith(suffix):
            out.append(base[: -len(suffix)].strip())
    # Holding + Subsidiaries → also search the operating company
    for op in operating_company_aliases(base):
        out.append(op)
        out.extend(search_variants(op))
    # Distinctive cores: "CECCO, Inc." -> CECCO; "ASAP Sands Outdoor..." -> ASAP Sands
    parts = [t for t in norm(base).split() if t not in NOISE and len(t) >= 3]
    if parts:
        # Single-token cores only when the company itself is short (CECCO).
        # Multi-token names keep 2–3 token cores so "ASAP" alone does not drive LIKE+score.
        if len(parts) == 1:
            out.append(parts[0].upper() if len(parts[0]) <= 6 else parts[0].title())
            out.append(parts[0])
        if len(parts) >= 2:
            out.append(f"{parts[0]} {parts[1]}")
        if len(parts) >= 3:
            out.append(f"{parts[0]} {parts[1]} {parts[2]}")
    return list(dict.fromkeys(v for v in out if v and len(v) >= 3))


def _score_one_account_match(insured: str, account_name: str) -> int:
    ins, acc = norm(insured), norm(account_name)
    it, at = tokens(insured), tokens(account_name)
    if not ins or not acc:
        return 0
    score = 0
    if ins == acc:
        score = 100
    elif ins in acc or acc in ins:
        if len(it) >= 2:
            shared = it & at
            if len(shared) >= max(2, (len(it) + 1) // 2):
                score = 85
        elif len(ins) >= 4:
            # Short legal names like CECCO
            score = 85
    elif it:
        shared = it & at
        score = int((len(shared) / len(it)) * 70)
        if len(it) >= 2 and len(shared) < 2:
            score = 0
    if score >= 55 and any((account_name or "").startswith(p) for p in ACCOUNT_PREFIXES):
        score = min(100, score + 10)
    return score


def score_account_match(insured: str, account_name: str) -> int:
    """Score Account vs insured name (and peeled operating-company aliases)."""
    anchors = [insured, *operating_company_aliases(insured)]
    return max((_score_one_account_match(a, account_name) for a in anchors), default=0)


def names_agree(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return False
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return False
    if na == nb or na in nb or nb in na:
        return True
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return False
    overlap = len(ta & tb) / max(len(ta), len(tb))
    return overlap >= 0.6


def score_identity_consensus(
    subject: str | None,
    legal_insured: str | None,
    hint_sources: dict,
) -> dict:
    """Rank how clearly subject / PDF / filename agree on the SP name."""
    agreeing: list[str] = []
    subj_hits = subject_sp_hints(subject)
    filename = hint_sources.get("pdf_filename")
    pdf_name = (
        legal_insured
        or hint_sources.get("company_before_address")
        or hint_sources.get("line_after_insured")
        or hint_sources.get("pdf_text")
    )
    if pdf_name and any(names_agree(pdf_name, s) for s in subj_hits):
        agreeing.append("subject+pdf")
    if pdf_name and filename and names_agree(pdf_name, filename):
        agreeing.append("pdf+filename")
    if filename and any(names_agree(filename, s) for s in subj_hits):
        agreeing.append("subject+filename")
    if len(agreeing) >= 2 or "subject+pdf" in agreeing:
        confidence = "high"
    elif pdf_name and (subj_hits or filename):
        confidence = "medium"
    elif pdf_name or subj_hits:
        confidence = "low"
    else:
        confidence = "none"
    display = pdf_name or (subj_hits[0] if subj_hits else filename)
    return {
        "confidence": confidence,
        "agreeing_signals": agreeing,
        "sp_name": display,
        "subject_hints": subj_hits,
    }


def gateway_lookup_company(name: str) -> dict | None:
    """Resolve SP # via Gateway invoice/company search (best-effort)."""
    if not name or not is_valid_insured(name):
        return None
    try:
        from gateway_vetting import gateway_find_sp, _enrich_sp_hit  # noqa: WPS433
    except Exception:
        return None
    entities = {
        "company": name,
        "ks_number": None,
        "sr_number": None,
        "requester_email": "Not stated",
        "contact_name": "Not stated",
    }
    try:
        hit = _enrich_sp_hit(gateway_find_sp(entities))
    except Exception:
        return None
    if not hit:
        return None
    return {
        "sp_number": hit.get("sp_number"),
        "name": hit.get("name"),
        "source": hit.get("source"),
    }


def prefixed_like(token: str) -> str:
    safe = esc(token)
    parts = [f"Name LIKE '%{safe}%'"]
    for prefix in ACCOUNT_PREFIXES:
        parts.append(f"Name LIKE '{prefix}{safe}%'")
        parts.append(f"Name LIKE '{prefix}%{safe}%'")
    return " OR ".join(parts)


def _region_tiebreak(insured: str, account_name: str) -> int:
    """Small boost when Account region matches clues in the insured string."""
    ins = (insured or "").lower()
    acc = (account_name or "").lower()
    bonus = 0
    # Palmetto Topco / SC holding companies → prefer SC-tagged Accounts
    if "palmetto" in ins and re.search(r"\bsc\b|- sc\b", acc):
        bonus += 5
    for st in ("tx", "sc", "nc", "ga", "fl", "ca", "ny", "oh", "pa"):
        if re.search(rf"\b{st}\b", ins) and re.search(rf"\b{st}\b|- {st}\b", acc):
            bonus += 3
            break
    return bonus


def lookup_account(names: list[str], cache: dict[str, list[dict]]) -> dict | None:
    """LIKE-search with variants; always score against the strongest insured name."""
    anchors = [n for n in names if n and is_valid_insured(n)]
    for name in list(anchors):
        for op in operating_company_aliases(name):
            if op not in anchors:
                anchors.append(op)
    if not anchors:
        return None
    # Prefer multi-token / longer legal names as the scoring anchor
    primary = sorted(anchors, key=lambda n: (len(tokens(n)), len(norm(n))), reverse=True)[0]
    variants: list[str] = []
    for name in anchors:
        variants.extend(search_variants(name))
    variants = list(dict.fromkeys(v for v in variants if v))

    best = None
    best_score = 0
    for variant in variants:
        key = variant.lower()
        if key not in cache:
            rows = sf_query(
                "SELECT Id, Name FROM Account WHERE Type = 'Service Provider' AND "
                f"({prefixed_like(variant)}) LIMIT 15"
            )
            cache[key] = rows
            time.sleep(0.12)
        for row in cache[key]:
            score = score_account_match(primary, row.get("Name") or "")
            score += _region_tiebreak(primary, row.get("Name") or "")
            if score > best_score:
                best_score = score
                best = {
                    "id": row["Id"],
                    "name": row["Name"],
                    "score": score,
                    "matched_on": primary,
                    "search_variant": variant,
                }
    return best if best and best["score"] >= 55 else None


def _sp_number_variants(sp_number: str) -> list[str]:
    raw = re.sub(r"[^A-Za-z0-9]", "", (sp_number or "").strip().upper())
    if not raw:
        return []
    variants = [raw]
    if raw.startswith("KS"):
        variants.append(raw[2:])
    else:
        variants.append(f"KS{raw}")
    return list(dict.fromkeys(v for v in variants if v))


def lookup_account_by_sp_number(sp_number: str, cache: dict[str, list[dict]]) -> dict | None:
    """Resolve SF Account from Gateway/VixxoLink KS / SP number."""
    variants = _sp_number_variants(sp_number)
    if not variants:
        return None
    key = f"spnum:{variants[0]}"
    if key not in cache:
        clauses: list[str] = []
        for variant in variants:
            safe = esc(variant)
            clauses.extend(
                [
                    f"Name LIKE '%{safe}%'",
                    f"Name LIKE '%#{safe}%'",
                    f"Name LIKE '% {safe}'",
                ]
            )
        rows = sf_query(
            "SELECT Id, Name FROM Account WHERE Type = 'Service Provider' AND "
            f"({' OR '.join(clauses)}) LIMIT 15"
        )
        cache[key] = rows
        time.sleep(0.12)

    best = None
    best_score = 0
    for variant in variants:
        for row in cache[key]:
            name = row.get("Name") or ""
            upper = name.upper()
            score = 0
            if f"#{variant}" in upper or f" {variant}" in upper or upper.endswith(variant):
                score = 100
            elif variant in upper.replace("-", "").replace(" ", ""):
                score = 90
            elif any(name.startswith(p) for p in ACCOUNT_PREFIXES):
                score = 75
            if score > best_score:
                best_score = score
                best = {"id": row["Id"], "name": name, "score": score, "matched_on": variant}
    return best if best and best_score >= 75 else None


def is_numeric_sp_label(name: str | None) -> bool:
    return bool(name) and re.fullmatch(r"[A-Za-z]?\d+[A-Za-z]?", (name or "").strip())


def is_valid_insured(name: str | None) -> bool:
    return bool(name) and not is_holder_or_noise(name)


def clean_subject_sp(name: str | None) -> str | None:
    if not name:
        return None
    s = re.sub(r"\s*-\s*Vixxo\b.*$", "", name.strip(), flags=re.I)
    s = re.sub(r"\s*-\s*Renewal(?:\s+COI|\s+Certificate)?\b.*$", "", s, flags=re.I)
    s = s.strip(" -–—,")
    return s if is_valid_insured(s) else None


def extract_subject_fallback(subject: str | None) -> str | None:
    if not subject:
        return None
    subj = subject.strip()
    # Strip leading RE:/FW: chain so "RE: FW: COI - Rhyno's" still yields Rhyno's
    subj_core = re.sub(r"^(?:(?:RE|FW|FWD|AW)\s*:\s*)+", "", subj, flags=re.I).strip()
    for pat in (SUBJECT_RENEWAL_COI_RE, SUBJECT_CERT_DASH_RE, SUBJECT_COI_FOR_RE):
        m = pat.search(subj_core) or pat.search(subj)
        if m:
            cand = clean_subject_sp(m.group(1).strip())
            if cand:
                return cand
    m = re.search(r"(?:^|:\s*)COI\s*[-–]\s*(.+)$", subj_core, re.I)
    if m:
        cand = clean_subject_sp(m.group(1).strip())
        if cand:
            return cand
    m = re.match(r"^(.+?)\s+COI\s+for\s+Vixxo", subj_core, re.I)
    if m:
        return clean_subject_sp(m.group(1).strip())
    return None


def extract_filename_sp(title: str | None) -> str | None:
    if not title:
        return None
    base = re.sub(r"\.pdf$", "", title.strip(), flags=re.I)
    for pat in (FILENAME_VIXXO_FIRST_RE, FILENAME_CSR24_RE, FILENAME_SP_RE):
        m = pat.search(base)
        if m:
            name = m.group(1).replace("_", " ").strip(" '\"`")
            # Drop trailing policy/date crumbs: "'26-27 GL" already cut by regex
            name = re.sub(r"\s+'?\d{2}-\d{2}.*$", "", name).strip()
            if is_valid_insured(name):
                return name
    return None


def subject_sp_hints(subject: str | None) -> list[str]:
    out: list[str] = []
    for raw in (
        sd.extract_subject_sp_hint(subject),
        extract_subject_fallback(subject),
    ):
        cleaned = clean_subject_sp(raw)
        if cleaned and cleaned not in out:
            out.append(cleaned)
    return out


def collect_search_names(
    subject: str | None,
    pdf_title: str | None,
    fields: dict,
) -> tuple[list[str], dict]:
    """Build SP name candidates: filename (Vixxo_* packets), PDF insured, subject."""
    sources: dict = {}
    names: list[str] = []

    def add(name: str | None, source: str) -> None:
        if not name or not is_valid_insured(name):
            return
        if name not in names:
            names.append(name)
        sources.setdefault(source, name)

    # Filename first for broker packets named Vixxo*_SP_*
    add(extract_filename_sp(pdf_title), "pdf_filename")

    legal = fields.get("legal_insured")
    if is_valid_insured(legal):
        add(legal, fields.get("extraction_method") or "pdf_text")
    elif legal:
        fields["legal_insured"] = None
        fields["extraction_error"] = "insured_boilerplate_rejected"

    for hint in subject_sp_hints(subject):
        add(hint, "subject")
    for dba in fields.get("dba_names") or []:
        add(dba, "pdf_dba")
    for alt in fields.get("alternate_names") or []:
        add(alt, "pdf_alt")

    return names, sources


def resolve_insured_display(fields: dict, sources: dict) -> str | None:
    for key in (
        "pdf_filename",
        "line_after_insured",
        "company_before_address",
        "regex_block",
        "pdf_text",
        "subject",
        "pdf_dba",
    ):
        if key in sources:
            return sources[key]
    return fields.get("legal_insured")


def _company_is_emailish(value: str | None) -> bool:
    s = (value or "").strip()
    return bool(s) and ("@" in s or s.lower().startswith("mail-server"))


def coi_cases(vet: dict) -> list[dict]:
    """COI-like shell Cases that still need PDF insured extraction.

    Always include certificate subjects. Also re-process weak
    ``account_resolved`` hits where company was an email/mail-server
    (recurring false match — e.g. Pelczar PDF on broker-forwarded COI).
    """
    out: list[dict] = []
    for c in vet.get("cases") or []:
        subject = c.get("subject") or ""
        if not COI_SUBJECT.search(subject):
            continue
        vs = c.get("vet_status") or ""
        hints = c.get("hints") or {}
        company = hints.get("company") or (c.get("vetting") or {}).get("company")
        already_pdf = (c.get("vet_source") == "coi_pdf_extraction") or bool(
            (c.get("coi_pdf") or {}).get("legal_insured")
        )
        if already_pdf and vs == "account_resolved":
            continue
        if vs in ("needs_manual", "needs_manual_pdf_insured", "onboarding"):
            out.append(c)
            continue
        if vs == "account_resolved" and _company_is_emailish(company):
            out.append(c)
            continue
        if vs in ("auto_reply_noise", "duplicate_cluster", "sr_routing"):
            continue
        # Default: still scan COI subjects so PDF insured is never skipped
        out.append(c)
    return out


def process_case(case: dict, account_cache: dict[str, list[dict]]) -> dict:
    case_id = case["id"]
    case_number = case.get("case_number")
    pdfs = list_case_pdfs(case_id) + list_email_pdfs(case_id)
    result = {
        "case_id": case_id,
        "case_number": case_number,
        "subject": case.get("subject"),
        "prior_vet_status": case.get("vet_status"),
        "pdf_count": len(pdfs),
        "pdfs": pdfs,
        "legal_insured": None,
        "dba_names": [],
        "alternate_names": [],
        "extraction_method": None,
        "extraction_error": None,
        "recommended_account": None,
        "account_match_score": None,
        "post_pdf_vet_status": case.get("vet_status"),
    }

    if not pdfs:
        result["extraction_error"] = "no_pdf_attachment"
        return result

    chosen = pdfs[0]
    for p in pdfs:
        title = (p.get("title") or "").lower()
        if any(k in title for k in ("coi", "cert", "acord", "insurance", "liability")):
            chosen = p
            break

    safe_num = re.sub(r"[^\w]", "_", case_number or case_id)
    dest = PDF_DIR / f"{safe_num}_{chosen['content_document_id']}.pdf"
    if not download_pdf(chosen["content_document_id"], dest):
        result["extraction_error"] = "download_failed"
        return result

    text, err = pdf_text(dest.read_bytes())
    if err and len(text.strip()) < 40:
        result["extraction_error"] = f"pdf_parse:{err}"
        return result

    fields = extract_insured_fields(text)
    result.update(fields)
    result["pdf_path"] = str(dest.relative_to(TMP.parent.parent.parent.parent).as_posix())

    search_names, hint_sources = collect_search_names(
        case.get("subject"), chosen.get("title"), fields
    )
    try:
        entities, intake_text, _, _ = load_case_intake(case, queue="coi")
        for name in company_candidates_from_intake(entities, intake_text):
            if name and name not in search_names:
                search_names.insert(0, name)
                hint_sources.setdefault("intake", name)
    except Exception as exc:
        hint_sources["intake_error"] = str(exc)
    result["hint_sources"] = hint_sources
    result["legal_insured"] = resolve_insured_display(fields, hint_sources)

    if not search_names:
        if not result.get("extraction_error"):
            result["extraction_error"] = "insured_not_found_in_pdf"
        return result

    consensus = score_identity_consensus(
        case.get("subject"), result.get("legal_insured"), hint_sources
    )
    result["identity_confidence"] = consensus["confidence"]
    result["identity_signals"] = consensus["agreeing_signals"]
    if consensus.get("sp_name") and is_valid_insured(consensus["sp_name"]):
        result["legal_insured"] = consensus["sp_name"]
        if consensus["sp_name"] not in search_names:
            search_names.insert(0, consensus["sp_name"])

    acct = lookup_account(search_names, account_cache)
    gateway = None
    if not acct:
        # Prefer consensus SP name for Gateway; fall back through search list
        for candidate in [consensus.get("sp_name"), *search_names]:
            if not candidate:
                continue
            gateway = gateway_lookup_company(candidate)
            if gateway and gateway.get("sp_number"):
                break
            gateway = None
        if gateway and gateway.get("sp_number"):
            by_sp = lookup_account_by_sp_number(str(gateway["sp_number"]), account_cache)
            if by_sp:
                acct = {
                    "id": by_sp["id"],
                    "name": by_sp["name"],
                    "score": by_sp.get("score") or 90,
                    "matched_on": gateway.get("name") or gateway.get("sp_number"),
                }
            result["gateway_sp"] = gateway.get("sp_number")
            result["gateway_name"] = gateway.get("name")
            result["gateway_source"] = gateway.get("source")

    if acct:
        result["recommended_account"] = {"id": acct["id"], "name": acct["name"]}
        result["account_match_score"] = acct["score"]
        result["matched_on"] = acct.get("matched_on")
        result["post_pdf_vet_status"] = "account_resolved_pdf"
    elif gateway and gateway.get("sp_number"):
        result["post_pdf_vet_status"] = "gateway_match_pdf"
    elif consensus["confidence"] == "high":
        # Subject + PDF (etc.) agree — SP is clear even without SF Account
        result["post_pdf_vet_status"] = "sp_identified"
    else:
        result["post_pdf_vet_status"] = "needs_manual_pdf_insured_only"

    return result


def write_report(results: list[dict], path: Path) -> None:
    by_status = Counter(r.get("post_pdf_vet_status") for r in results)
    by_err = Counter(r.get("extraction_error") for r in results if r.get("extraction_error"))
    resolved = [r for r in results if r.get("recommended_account")]
    identified = [
        r
        for r in results
        if r.get("post_pdf_vet_status") in ("sp_identified", "gateway_match_pdf")
        and not r.get("recommended_account")
    ]
    insured_only = [
        r
        for r in results
        if r.get("legal_insured")
        and not r.get("recommended_account")
        and r.get("post_pdf_vet_status") == "needs_manual_pdf_insured_only"
    ]

    lines = [
        "# Shell COI PDF Insured Extraction",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Cases processed:** {len(results)}",
        "",
        "## Outcomes",
        "",
        "| post_pdf_vet_status | Count |",
        "|---------------------|------:|",
    ]
    for k, v in by_status.most_common():
        lines.append(f"| `{k}` | {v} |")
    if by_err:
        lines.extend(["", "## Extraction errors", "", "| error | count |", "|-------|------:|"])
        for k, v in by_err.most_common():
            lines.append(f"| `{k}` | {v} |")

    lines.extend(["", "## Account resolved from PDF insured (sample)", ""])
    lines.append("| Case | Insured (PDF) | SF Account | Score |")
    lines.append("|------|---------------|------------|------:|")
    for r in resolved[:40]:
        acct = r["recommended_account"]["name"]
        lines.append(
            f"| {r['case_number']} | {(r.get('legal_insured') or '')[:45]} | {acct[:45]} | {r.get('account_match_score')} |"
        )

    lines.extend(
        [
            "",
            "## SP identified (subject+PDF agree) — no SF Account yet",
            "",
            "These are **not** identity mysteries. Apply/create Account using the SP name.",
            "",
            "| Case | SP name | Confidence | Signals | Gateway SP |",
            "|------|---------|------------|---------|------------|",
        ]
    )
    for r in identified[:50]:
        signals = ", ".join(r.get("identity_signals") or []) or "—"
        lines.append(
            f"| {r.get('case_number')} | {(r.get('legal_insured') or '')[:45]} | "
            f"{r.get('identity_confidence') or '—'} | {signals} | "
            f"{r.get('gateway_sp') or '—'} |"
        )

    lines.extend(["", "## Weak / unclear insured (still manual)", ""])
    lines.append("| Case | Insured (PDF) | DBA |")
    lines.append("|------|---------------|-----|")
    for r in insured_only[:30]:
        dba = ", ".join(r.get("dba_names") or []) or "—"
        lines.append(
            f"| {r['case_number']} | {(r.get('legal_insured') or '')[:50]} | {dba[:40]} |"
        )

    path.write_text("\n".join(lines), encoding="utf-8")


def refine_existing_results(vet: dict) -> tuple[dict, list]:
    """Re-score sidecar rows without re-downloading PDFs (consensus + Gateway + Account)."""
    prior = _load_prior_results()
    if not prior:
        print("No prior COI PDF results to refine.", flush=True)
        return vet, []
    account_cache: dict[str, list[dict]] = {}
    out: list[dict] = []
    for i, r in enumerate(prior, 1):
        legal = r.get("legal_insured")
        hint_sources = dict(r.get("hint_sources") or {})
        # Recover SP from subject when prior legal was junk (e.g. "FW:")
        if not legal or not is_valid_insured(legal):
            subj_hits = subject_sp_hints(r.get("subject"))
            if subj_hits:
                legal = subj_hits[0]
                r["legal_insured"] = legal
                hint_sources["subject"] = legal
            else:
                r["post_pdf_vet_status"] = r.get("post_pdf_vet_status") or "needs_manual"
                r.pop("recommended_account", None)
                out.append(r)
                continue
        print(f"[refine {i}/{len(prior)}] {r.get('case_number')} {legal[:40]}...", flush=True)
        consensus = score_identity_consensus(r.get("subject"), legal, hint_sources)
        r["identity_confidence"] = consensus["confidence"]
        r["identity_signals"] = consensus["agreeing_signals"]
        r["hint_sources"] = hint_sources
        if consensus.get("sp_name") and is_valid_insured(consensus["sp_name"]):
            r["legal_insured"] = consensus["sp_name"]
            legal = consensus["sp_name"]
        names = list(
            dict.fromkeys(
                [
                    legal,
                    *(consensus.get("subject_hints") or []),
                ]
            )
        )
        # Clear prior false Account hits before re-score
        r.pop("recommended_account", None)
        r.pop("account_match_score", None)
        r.pop("matched_on", None)
        acct = lookup_account(names, account_cache)
        gateway = gateway_lookup_company(legal) if not acct else None
        if gateway and gateway.get("sp_number") and not acct:
            by_sp = lookup_account_by_sp_number(str(gateway["sp_number"]), account_cache)
            if by_sp:
                acct = {
                    "id": by_sp["id"],
                    "name": by_sp["name"],
                    "score": by_sp.get("score") or 90,
                    "matched_on": gateway.get("name") or gateway.get("sp_number"),
                }
            r["gateway_sp"] = gateway.get("sp_number")
            r["gateway_name"] = gateway.get("name")
            r["gateway_source"] = gateway.get("source")
        if acct:
            r["recommended_account"] = {"id": acct["id"], "name": acct["name"]}
            r["account_match_score"] = acct["score"]
            r["matched_on"] = acct.get("matched_on")
            r["post_pdf_vet_status"] = "account_resolved_pdf"
        elif gateway and gateway.get("sp_number"):
            r["post_pdf_vet_status"] = "gateway_match_pdf"
        elif consensus["confidence"] == "high":
            r["post_pdf_vet_status"] = "sp_identified"
        else:
            r["post_pdf_vet_status"] = "needs_manual_pdf_insured_only"
        out.append(r)
        time.sleep(0.05)

    merge_vet(vet, out)
    vet["coi_pdf_extraction"] = str(OUT_JSON)
    vet["by_vet_status"] = dict(
        Counter(c.get("vet_status") for c in vet.get("cases") or []).most_common()
    )
    VET_JSON.write_text(json.dumps(vet, indent=2), encoding="utf-8")
    _write_sidecar(out, batch_meta={"refine": True, "done": True, "remaining": 0})
    return vet, out


def merge_vet(vet: dict, results: list[dict]) -> None:
    by_id = {r["case_id"]: r for r in results}
    for c in vet.get("cases") or []:
        r = by_id.get(c.get("id"))
        if not r:
            continue
        c["coi_pdf"] = {
            "legal_insured": r.get("legal_insured"),
            "dba_names": r.get("dba_names"),
            "alternate_names": r.get("alternate_names"),
            "extraction_method": r.get("extraction_method"),
            "extraction_error": r.get("extraction_error"),
            "pdf_count": r.get("pdf_count"),
            "post_pdf_vet_status": r.get("post_pdf_vet_status"),
            "hint_sources": r.get("hint_sources"),
            "match_source": r.get("match_source"),
            "identity_confidence": r.get("identity_confidence"),
            "identity_signals": r.get("identity_signals"),
            "gateway_sp": r.get("gateway_sp"),
            "gateway_name": r.get("gateway_name"),
        }
        hints = c.get("hints") or {}
        prior_company = hints.get("company") or (c.get("vetting") or {}).get("company")
        legal = r.get("legal_insured")
        if legal and is_valid_insured(legal):
            hints["company"] = legal
            hints["provider"] = hints.get("provider") or legal
            c["hints"] = hints
            vetting = c.get("vetting") or {}
            vetting["company"] = legal
            c["vetting"] = vetting
        elif is_holder_or_noise(hints.get("company") or "") or _company_is_emailish(prior_company):
            subj_hints = subject_sp_hints(c.get("subject"))
            if subj_hints:
                hints["company"] = subj_hints[0]
                c["hints"] = hints
        weak_prior = _company_is_emailish(prior_company) or c.get("vet_source") != "coi_pdf_extraction"
        if r.get("gateway_sp"):
            c["gateway_sp"] = r.get("gateway_sp")
            c["gateway_name"] = r.get("gateway_name")
            c["gateway_source"] = r.get("gateway_source")
        if r.get("identity_confidence"):
            c["identity_confidence"] = r.get("identity_confidence")
            c["identity_signals"] = r.get("identity_signals")
        post = r.get("post_pdf_vet_status")
        if r.get("recommended_account"):
            c["recommended_account"] = r["recommended_account"]
            c["vet_status"] = "account_resolved"
            c["vet_source"] = "coi_pdf_extraction"
        elif post == "gateway_match_pdf":
            c["vet_status"] = "gateway_match"
            c["vet_source"] = "coi_pdf_extraction"
        elif post == "sp_identified" or (
            legal
            and is_valid_insured(legal)
            and (r.get("identity_confidence") == "high")
        ):
            # Clear SP from subject+PDF — not "manual mystery"
            if weak_prior and c.get("vet_status") == "account_resolved":
                c["recommended_account"] = None
                c["account_search_candidates"] = []
            c["vet_status"] = "sp_identified"
            c["vet_source"] = "coi_pdf_extraction"
        elif legal and is_valid_insured(legal):
            # Prefer PDF insured over email-as-company false Account hits
            if weak_prior or c.get("vet_status") in (
                "needs_manual",
                "account_resolved",
                "onboarding",
            ):
                if weak_prior and c.get("vet_status") == "account_resolved":
                    c["recommended_account"] = None
                    c["account_search_candidates"] = []
                c["vet_status"] = "needs_manual_pdf_insured"
                c["vet_source"] = "coi_pdf_extraction"


def _load_prior_results() -> list[dict]:
    if not OUT_JSON.is_file():
        return []
    try:
        prior = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return list(prior.get("results") or [])


def _write_sidecar(results: list[dict], *, batch_meta: dict | None = None) -> None:
    payload = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "case_count": len(results),
        "by_post_pdf_status": dict(
            Counter(r.get("post_pdf_vet_status") for r in results).most_common()
        ),
        "by_extraction_error": dict(
            Counter(
                r.get("extraction_error") for r in results if r.get("extraction_error")
            ).most_common()
        ),
        "results": results,
    }
    if batch_meta:
        payload["batch"] = batch_meta
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_report(results, OUT_MD)


def run_coi_enrichment(
    vet: dict,
    *,
    batch_size: int = 15,
    offset: int = 0,
    limit: int | None = None,
    resume: bool = True,
) -> tuple[dict, list]:
    """Extract COI PDF insured names and merge into vet; return (vet, sidecar results).

    Processes in batches and checkpoints OUT_JSON + VET_JSON after each batch so a
    bogged SF CLI run can resume without redoing completed Cases.
    """
    targets = coi_cases(vet)
    prior = _load_prior_results() if resume else []
    by_id = {r.get("case_id"): r for r in prior if r.get("case_id")}
    if resume and by_id:
        before = len(targets)
        targets = [c for c in targets if c.get("id") not in by_id]
        print(
            f"Resume: {len(by_id)} already in {OUT_JSON.name}; "
            f"{before - len(targets)} skipped, {len(targets)} remaining",
            flush=True,
        )

    if offset:
        targets = targets[offset:]
    if limit is not None:
        targets = targets[:limit]

    print(
        f"COI shell cases to process: {len(targets)} "
        f"(batch_size={batch_size}, offset={offset}, limit={limit})",
        flush=True,
    )
    if not targets:
        results = list(by_id.values())
        merge_vet(vet, results)
        vet["coi_pdf_extraction"] = str(OUT_JSON)
        _write_sidecar(results, batch_meta={"done": True, "remaining": 0})
        return vet, results

    account_cache: dict[str, list[dict]] = {}
    results = list(by_id.values())
    total = len(targets)
    batch_size = max(1, batch_size)

    for batch_start in range(0, total, batch_size):
        batch = targets[batch_start : batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        batch_total = (total + batch_size - 1) // batch_size
        print(
            f"--- COI batch {batch_num}/{batch_total} "
            f"({len(batch)} cases) ---",
            flush=True,
        )
        for j, case in enumerate(batch, 1):
            idx = batch_start + j
            print(f"[{idx}/{total}] {case.get('case_number')} ...", flush=True)
            try:
                row = process_case(case, account_cache)
            except Exception as exc:
                row = {
                    "case_id": case.get("id"),
                    "case_number": case.get("case_number"),
                    "subject": case.get("subject"),
                    "extraction_error": f"exception:{exc}",
                    "post_pdf_vet_status": case.get("vet_status"),
                }
            results.append(row)
            by_id[row.get("case_id")] = row
            time.sleep(0.08)

        # Checkpoint after every batch
        merge_vet(vet, results)
        vet["coi_pdf_extraction"] = str(OUT_JSON)
        vet["by_vet_status"] = dict(
            Counter(c.get("vet_status") for c in vet.get("cases") or []).most_common()
        )
        VET_JSON.write_text(json.dumps(vet, indent=2), encoding="utf-8")
        remaining = total - (batch_start + len(batch))
        _write_sidecar(
            results,
            batch_meta={
                "batch_num": batch_num,
                "batch_total": batch_total,
                "batch_size": batch_size,
                "remaining": remaining,
                "done": remaining == 0,
            },
        )
        print(
            f"Checkpoint: {len(results)} results -> {OUT_JSON.name} "
            f"(remaining this run: {remaining})",
            flush=True,
        )

    return vet, results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--batch-size",
        type=int,
        default=int(os.environ.get("COI_BATCH_SIZE", "15")),
        help="Cases per checkpoint batch (default 15; env COI_BATCH_SIZE)",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=int(os.environ.get("COI_OFFSET", "0")),
        help="Skip first N pending targets (after resume filter)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=int(os.environ["COI_LIMIT"]) if os.environ.get("COI_LIMIT") else None,
        help="Max cases this run (env COI_LIMIT)",
    )
    parser.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        default=os.environ.get("COI_RESUME", "1") != "0",
        help="Skip case_ids already present in OUT_JSON (default on)",
    )
    parser.add_argument(
        "--no-write-vet",
        action="store_true",
        help="Do not rewrite VET_JSON (sidecar only) — unused; batches always checkpoint vet",
    )
    parser.add_argument(
        "--refine-only",
        action="store_true",
        help="Re-score existing OUT_JSON (consensus + Gateway + Account) without re-downloading PDFs",
    )
    args = parser.parse_args(argv)

    vet = json.loads(VET_JSON.read_text(encoding="utf-8"))
    if args.refine_only:
        vet, results = refine_existing_results(vet)
    else:
        vet, results = run_coi_enrichment(
            vet,
            batch_size=args.batch_size,
            offset=args.offset,
            limit=args.limit,
            resume=args.resume,
        )
    vet["by_vet_status"] = dict(
        Counter(c.get("vet_status") for c in vet["cases"]).most_common()
    )
    VET_JSON.write_text(json.dumps(vet, indent=2), encoding="utf-8")

    print(
        json.dumps(
            dict(Counter(r.get("post_pdf_vet_status") for r in results).most_common()),
            indent=2,
        )
    )
    print(f"OUT_JSON: {OUT_JSON.resolve()}")
    print(f"OUT_MD: {OUT_MD.resolve()}")
    remaining = (json.loads(OUT_JSON.read_text(encoding="utf-8")).get("batch") or {}).get(
        "remaining"
    )
    if remaining:
        print(
            f"NEXT: RUN_DATE={RUN_DATE} python extract_shell_coi_insured.py "
            f"--batch-size {args.batch_size} --resume",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
