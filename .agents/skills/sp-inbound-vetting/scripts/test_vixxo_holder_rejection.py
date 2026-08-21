#!/usr/bin/env python3
"""Regression: never treat Vixxo certificate-holder / signature as the SP company."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from entity_extraction import (  # noqa: E402
    extract_subject_company,
    sanitize_company,
)
from sf_vetting import extract_sf_case_entities  # noqa: E402


def test_reject_vixxo_corporation() -> None:
    assert sanitize_company("Vixxo Corporation") is None
    assert sanitize_company("Risk Management Department Vixxo Corporation") is None


def test_designteam_subject() -> None:
    subj = "Re: DesignTeam Inc - Service Provider number KS102207 - Your account Vixxo"
    assert extract_subject_company(subj) == "DesignTeam Inc"
    ents = extract_sf_case_entities(
        {
            "Id": "x",
            "CaseNumber": "00005928",
            "Subject": subj,
            "Description": "John Grant\nDesignTeam\n801.483.9000\n\nVixxo Corporation\n",
            "ContactEmail": "john@designteamslc.com",
            "SuppliedEmail": "john@designteamslc.com",
        },
        "coi",
    )
    assert ents["company"] == "DesignTeam Inc"
    assert ents["ks_number"] == "KS102207"


def test_next_insurance_insured_business() -> None:
    ents = extract_sf_case_entities(
        {
            "Id": "y",
            "CaseNumber": "00006117",
            "Subject": "New 30 days notice of cancellation approved for Brian Turner Commercial Services",
            "Description": (
                "Insured business:\nBrian Turner Commercial Services\n"
                "Entity:\nVixxo Corporation\n"
            ),
            "ContactEmail": "hello@nextinsurance.com",
            "SuppliedEmail": "hello@nextinsurance.com",
        },
        "coi",
    )
    assert ents["company"] == "Brian Turner Commercial Services"


def test_cooks_locksmith_signature() -> None:
    ents = extract_sf_case_entities(
        {
            "Id": "w",
            "CaseNumber": "00006134",
            "Subject": "Fwd: Rate Changes",
            "Description": (
                "Teresa Clark\nCook's Locksmith Services\n502-964-8238\n\n"
                "Vixxo Corporation\n128 N. First St.\n"
            ),
            "ContactEmail": "accountsreceivable@cookslocksmith.com",
            "SuppliedEmail": "accountsreceivable@cookslocksmith.com",
        },
        "coi",
    )
    assert ents["company"] == "Cook's Locksmith Services"


if __name__ == "__main__":
    test_reject_vixxo_corporation()
    test_designteam_subject()
    test_next_insurance_insured_business()
    test_cooks_locksmith_signature()
    print("OK")
