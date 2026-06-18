"""Shared entity name matching for sp-inbound-vetting."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

# Minimum similarity to treat as a fuzzy hit.
FUZZY_THRESHOLD = 0.75

# When scores are within this delta of the best, include as alternates.
CLOSE_SCORE_DELTA = 0.05

_COMMON_SUFFIXES = frozenset(
    {"llc", "inc", "co", "corp", "ltd", "the", "company", "services", "service"}
)


def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalize_company(name: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace, drop common suffixes."""
    text = (name or "").lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = _collapse_ws(text)
    tokens = [t for t in text.split() if t and t not in _COMMON_SUFFIXES]
    return " ".join(tokens)


def normalize_contact_name(name: str) -> str:
    text = (name or "").lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return _collapse_ws(text)


def _tokens(text: str) -> set[str]:
    return {t for t in normalize_company(text).split() if len(t) >= 2}


def token_overlap_ratio(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def sequence_ratio(a: str, b: str) -> float:
    na, nb = normalize_company(a), normalize_company(b)
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def company_similarity(a: str, b: str) -> float:
    """Blend token overlap, substring, and SequenceMatcher scores."""
    na, nb = normalize_company(a), normalize_company(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    if na in nb or nb in na:
        return max(0.85, sequence_ratio(a, b))

    scores = [
        sequence_ratio(a, b),
        token_overlap_ratio(a, b),
    ]
    # Boost when all query tokens appear in candidate (or vice versa).
    ta, tb = set(na.split()), set(nb.split())
    if ta <= tb or tb <= ta:
        scores.append(0.82)
    return max(scores)


def contact_name_similarity(query: str, candidate: str) -> float:
    """Score contact names; last-name + first-initial match scores high."""
    q = normalize_contact_name(query)
    c = normalize_contact_name(candidate)
    if not q or not c:
        return 0.0
    if q == c:
        return 1.0

    q_parts = q.split()
    c_parts = c.split()
    if len(q_parts) >= 2 and len(c_parts) >= 2:
        q_last, c_last = q_parts[-1], c_parts[-1]
        q_first, c_first = q_parts[0], c_parts[0]
        if q_last == c_last and q_first[:1] == c_first[:1]:
            return 0.88

    if q in c or c in q:
        return max(0.80, SequenceMatcher(None, q, c).ratio())

    return SequenceMatcher(None, q, c).ratio()


def is_fuzzy_company_match(a: str, b: str) -> bool:
    return company_similarity(a, b) >= FUZZY_THRESHOLD


def is_fuzzy_contact_match(query: str, candidate: str) -> bool:
    return contact_name_similarity(query, candidate) >= FUZZY_THRESHOLD


def is_exact_company_match(a: str, b: str) -> bool:
    return normalize_company(a) == normalize_company(b)


def rank_candidates(
    query: str,
    candidates: list[dict],
    *,
    field: str,
    kind: str = "company",
) -> list[tuple[dict, float]]:
    """Return (candidate, score) pairs sorted by score descending."""
    scored: list[tuple[dict, float]] = []
    for row in candidates:
        value = str(row.get(field) or "")
        if not value:
            continue
        score = company_similarity(query, value) if kind == "company" else contact_name_similarity(query, value)
        if score > 0:
            scored.append((row, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def best_match_with_alternates(
    query: str,
    candidates: list[dict],
    *,
    field: str,
    kind: str = "company",
    threshold: float = FUZZY_THRESHOLD,
) -> tuple[dict | None, float, list[dict]]:
    """Pick best candidate; return alternates when scores are close."""
    ranked = rank_candidates(query, candidates, field=field, kind=kind)
    if not ranked:
        return None, 0.0, []
    best_row, best_score = ranked[0]
    if best_score < threshold:
        return None, best_score, []
    alternates = [
        row for row, score in ranked[1:]
        if best_score - score <= CLOSE_SCORE_DELTA and score >= threshold
    ]
    return best_row, best_score, alternates


def match_confidence(exact: bool, score: float) -> str:
    if exact:
        return "High"
    if score >= FUZZY_THRESHOLD:
        return "Medium"
    return "Low"


def match_label(exact: bool) -> str:
    return "Yes" if exact else "Possible"
