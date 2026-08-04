#!/usr/bin/env python3
"""Deprecated — shell vetting now runs sp-inbound-vetting inline in vet_shell_accounts_allorg."""

from __future__ import annotations

import os
import warnings


def run_unified_enrichment(vet: dict) -> dict:
    if os.environ.get("LEGACY_SHELL_ENRICHMENT") == "1":
        from extract_shell_coi_insured import run_coi_enrichment
        from enrich_shell_vet_sender_mcp import run_sender_enrichment

        warnings.warn(
            "LEGACY_SHELL_ENRICHMENT=1 runs separate COI/sender passes; "
            "prefer single-path vet_shell_accounts_allorg",
            stacklevel=2,
        )
        vet, _ = run_coi_enrichment(vet)
        vet, _ = run_sender_enrichment(vet)
        return vet
    return vet
