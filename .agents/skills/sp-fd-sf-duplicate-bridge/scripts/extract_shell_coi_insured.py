#!/usr/bin/env python3
"""Extract insured name from COI PDFs on open Shell Account cases (report only)."""

from __future__ import annotations

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
NOISE = {
    "the", "and", "of", "for", "dba", "llc", "inc", "corp", "co", "ltd", "company",
    "service", "services", "insured", "address", "city", "state", "zip",
}


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
    if n in HOLDER_NAMES or n.startswith("vixxo "):
        return True
    if INSURED_BOILERPLATE.search(n):
        return True
    if re.match(r"^\d{5}", n):
        return True
    if re.match(r"^(street|po box|suite|scottsdale|address)\b", n, re.I):
        return True
    return False


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
            for nxt in lines[i + 1 : i + 6]:
                if re.match(r"^(POLICY|INSURER|COVERAGES|CERTIFICATE HOLDER|DATE)\b", nxt, re.I):
                    break
                if not is_holder_or_noise(nxt):
                    block.append(nxt)
            if block:
                legal = block[0]
                method = "line_after_insured"
                for extra in block[1:]:
                    m = re.match(r"(?:D/B/A|DBA)\s+(.+)", extra, re.I)
                    if m:
                        dba_names.append(m.group(1).strip())
                    elif not is_holder_or_noise(extra):
                        alternate_names.append(extra)
            break

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
        f"SELECT Id, Subject, HasAttachment FROM EmailMessage WHERE ParentId = '{case_id}' "
        "AND HasAttachment = true ORDER BY CreatedDate DESC LIMIT 5"
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


def search_variants(name: str) -> list[str]:
    base = re.sub(r"\s+d/b/a.*", "", name, flags=re.I).strip()
    out = [base, re.sub(r"\s+", " ", re.sub(r"[,.\-/&']", " ", base)).strip()]
    for suffix in (" LLC", " Inc.", " Inc", " LLC.", ", LLC", ", Inc.", " INC", " Company"):
        if base.endswith(suffix):
            out.append(base[: -len(suffix)].strip())
    return list(dict.fromkeys(v for v in out if v))


def prefixed_like(token: str) -> str:
    safe = esc(token)
    parts = [f"Name LIKE '%{safe}%'"]
    for prefix in ACCOUNT_PREFIXES:
        parts.append(f"Name LIKE '{prefix}{safe}%'")
        parts.append(f"Name LIKE '{prefix}%{safe}%'")
    return " OR ".join(parts)


def lookup_account(names: list[str], cache: dict[str, list[dict]]) -> dict | None:
    best = None
    best_score = 0
    for name in names:
        for variant in search_variants(name):
            key = variant.lower()
            if key not in cache:
                rows = sf_query(
                    "SELECT Id, Name FROM Account WHERE Type = 'Service Provider' AND "
                    f"({prefixed_like(variant)}) LIMIT 15"
                )
                cache[key] = rows
                time.sleep(0.12)
            for row in cache[key]:
                ins, acc = norm(name), norm(row.get("Name") or "")
                score = 0
                if ins == acc:
                    score = 100
                elif ins in acc or acc in ins:
                    score = 85
                else:
                    it, at = tokens(name), tokens(row.get("Name") or "")
                    if it:
                        score = int((len(it & at) / len(it)) * 60)
                if any((row.get("Name") or "").startswith(p) for p in ACCOUNT_PREFIXES):
                    score += 10
                if score > best_score:
                    best_score = score
                    best = {"id": row["Id"], "name": row["Name"], "score": score, "matched_on": name}
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
    s = re.sub(r"\s*-\s*Vixxo\b.*$", "", name.strip(), flags=re.I).strip(" -–—,")
    return s if is_valid_insured(s) else None


def extract_subject_fallback(subject: str | None) -> str | None:
    if not subject:
        return None
    subj = subject.strip()
    for pat in (SUBJECT_RENEWAL_COI_RE, SUBJECT_CERT_DASH_RE, SUBJECT_COI_FOR_RE):
        m = pat.search(subj)
        if m:
            cand = clean_subject_sp(m.group(1).strip())
            if cand:
                return cand
    m = re.match(r"^(.+?)\s+COI\s+for\s+Vixxo", subj, re.I)
    if m:
        return clean_subject_sp(m.group(1).strip())
    return None


def extract_filename_sp(title: str | None) -> str | None:
    if not title:
        return None
    base = re.sub(r"\.pdf$", "", title.strip(), flags=re.I)
    for pat in (FILENAME_CSR24_RE, FILENAME_SP_RE):
        m = pat.search(base)
        if m:
            name = m.group(1).replace("_", " ").strip()
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
    """Build SP name candidates: valid PDF insured, filename, subject (priority order)."""
    sources: dict = {}
    names: list[str] = []

    def add(name: str | None, source: str) -> None:
        if not name or not is_valid_insured(name):
            return
        if name not in names:
            names.append(name)
        sources.setdefault(source, name)

    legal = fields.get("legal_insured")
    if is_valid_insured(legal):
        add(legal, fields.get("extraction_method") or "pdf_text")
    elif legal:
        fields["legal_insured"] = None
        fields["extraction_error"] = "insured_boilerplate_rejected"

    add(extract_filename_sp(pdf_title), "pdf_filename")
    for hint in subject_sp_hints(subject):
        add(hint, "subject")
    for dba in fields.get("dba_names") or []:
        add(dba, "pdf_dba")
    for alt in fields.get("alternate_names") or []:
        add(alt, "pdf_alt")

    return names, sources


def resolve_insured_display(fields: dict, sources: dict) -> str | None:
    for key in ("pdf_text", "line_after_insured", "regex_block", "pdf_filename", "subject", "pdf_dba"):
        if key in sources:
            return sources[key]
    return fields.get("legal_insured")


def coi_cases(vet: dict) -> list[dict]:
    return [
        c
        for c in vet.get("cases") or []
        if COI_SUBJECT.search(c.get("subject") or "")
    ]


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

    acct = lookup_account(search_names, account_cache)
    if acct:
        result["recommended_account"] = {"id": acct["id"], "name": acct["name"]}
        result["account_match_score"] = acct["score"]
        result["matched_on"] = acct.get("matched_on")
        result["post_pdf_vet_status"] = "account_resolved_pdf"
    else:
        result["post_pdf_vet_status"] = "needs_manual_pdf_insured_only"

    return result


def write_report(results: list[dict], path: Path) -> None:
    by_status = Counter(r.get("post_pdf_vet_status") for r in results)
    by_err = Counter(r.get("extraction_error") for r in results if r.get("extraction_error"))
    resolved = [r for r in results if r.get("recommended_account")]
    insured_only = [r for r in results if r.get("legal_insured") and not r.get("recommended_account")]

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
            f"| {r['case_number']} | {r['legal_insured'][:45]} | {acct[:45]} | {r.get('account_match_score')} |"
        )

    lines.extend(["", "## Insured found, no SF Account match (sample)", ""])
    lines.append("| Case | Insured (PDF) | DBA |")
    lines.append("|------|---------------|-----|")
    for r in insured_only[:30]:
        dba = ", ".join(r.get("dba_names") or []) or "—"
        lines.append(f"| {r['case_number']} | {r['legal_insured'][:50]} | {dba[:40]} |")

    path.write_text("\n".join(lines), encoding="utf-8")


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
        }
        hints = c.get("hints") or {}
        if is_holder_or_noise(hints.get("company") or ""):
            subj_hints = subject_sp_hints(c.get("subject"))
            if subj_hints:
                hints["company"] = subj_hints[0]
                c["hints"] = hints
        if r.get("recommended_account"):
            c["recommended_account"] = r["recommended_account"]
            c["vet_status"] = "account_resolved"
            c["vet_source"] = "coi_pdf_extraction"
        elif r.get("legal_insured") and is_valid_insured(r.get("legal_insured")):
            if c.get("vet_status") == "needs_manual":
                c["vet_status"] = "needs_manual_pdf_insured"


def run_coi_enrichment(vet: dict) -> tuple[dict, list]:
    """Extract COI PDF insured names and merge into vet; return (vet, sidecar results)."""
    targets = coi_cases(vet)
    print(f"COI shell cases to process: {len(targets)}", flush=True)

    account_cache: dict[str, list[dict]] = {}
    results = []
    for i, case in enumerate(targets, 1):
        print(f"[{i}/{len(targets)}] {case.get('case_number')} ...", flush=True)
        try:
            results.append(process_case(case, account_cache))
        except Exception as exc:
            results.append(
                {
                    "case_id": case.get("id"),
                    "case_number": case.get("case_number"),
                    "subject": case.get("subject"),
                    "extraction_error": f"exception:{exc}",
                    "post_pdf_vet_status": case.get("vet_status"),
                }
            )
        time.sleep(0.08)

    merge_vet(vet, results)
    vet["coi_pdf_extraction"] = str(OUT_JSON)

    payload = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "case_count": len(results),
        "by_post_pdf_status": dict(
            Counter(r.get("post_pdf_vet_status") for r in results).most_common()
        ),
        "by_extraction_error": dict(
            Counter(r.get("extraction_error") for r in results if r.get("extraction_error")).most_common()
        ),
        "results": results,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_report(results, OUT_MD)
    return vet, results


def main() -> int:
    vet = json.loads(VET_JSON.read_text(encoding="utf-8"))
    vet, results = run_coi_enrichment(vet)
    vet["by_vet_status"] = dict(Counter(c.get("vet_status") for c in vet["cases"]).most_common())
    VET_JSON.write_text(json.dumps(vet, indent=2), encoding="utf-8")

    print(json.dumps(dict(Counter(r.get("post_pdf_vet_status") for r in results).most_common()), indent=2))
    print(f"OUT_JSON: {OUT_JSON.resolve()}")
    print(f"OUT_MD: {OUT_MD.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
