#!/usr/bin/env python3
"""Backfill Case AccountId for Known SP cases vetted 2026-07-22."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from sf_case_account import update_case_account  # noqa: E402

BACKFILL = [
    ("500TS00000pPFUrYAO", "00007122", "001TS00000enGyVYAU", {"Name": "Everywhere Signs LLC", "Service_Provider_Number__c": "F4798551"}),
    ("500TS00000pPgMtYAK", "00007123", "001TS00000enH5MYAU", {"Name": "Meckley Services, Inc.", "Service_Provider_Number__c": "F5013521"}),
    ("500TS00000pPM6UYAW", "00007124", "001TS00000en8UUYAY", {"Name": "KS - Vericlean Services Corporation", "Service_Provider_Number__c": "KS69693"}),
    ("500TS00000pPddYYAS", "00007127", "001TS00000enAq8YAE", {"Name": "Brian's Professional Cleaning & Restoration Co.", "Service_Provider_Number__c": "F4719631"}),
    ("500TS00000pP8TMYA0", "00007128", "001TS00000en9mxYAA", {"Name": "KS - Advanced Equipment Solutions Inc", "Service_Provider_Number__c": "KS68659"}),
    ("500TS00000pQCkvYAG", "00007129", "001TS00000en8srYAA", {"Name": "KS - JH Maintenance Services", "Service_Provider_Number__c": "KS69934"}),
    ("500TS00000pQRonYAG", "00007136", "001TS00000n0UzXYAU", {"Name": "Mechanical Services Inc.", "Service_Provider_Number__c": "4997"}),
    ("500TS00000pQd5BYAS", "00007140", "001TS00000n0KX7YAM", {"Name": "KS - Lee's Locks and Security Services LLC", "Service_Provider_Number__c": "KS102018"}),
    ("500TS00000pQiJNYA0", "00007141", "001TS00000en9CjYAI", {"Name": "Pivotal Doors Inc", "Service_Provider_Number__c": "KS68616"}),
    ("500TS00000pQmYHYA0", "00007142", "001TS00000en8HcYAI", {"Name": "Corpus Christi Safe & Lock Co.", "Service_Provider_Number__c": "12506"}),
    ("500TS00000pQbxtYAC", "00007143", "001TS00000en9OnYAI", {"Name": "Best Beverage Equipment Service", "Service_Provider_Number__c": "68580"}),
    ("500TS00000pQwEHYA0", "00007146", "001TS00000en9CTYAY", {"Name": "KS - Trak Concepts Inc", "Service_Provider_Number__c": "F2798711"}),
    ("500TS00000pQMtyYAG", "00007147", "001TS00000enCehYAE", {"Name": "Spears Services Inc.", "Service_Provider_Number__c": "F4451711"}),
    ("500TS00000pQSzTYAW", "00007149", "001TS00000n0KSJYA2", {"Name": "KS - All Clear Pumping and Sewer", "Service_Provider_Number__c": "KS101687"}),
]


def main() -> int:
    for case_id, case_number, account_id, account in BACKFILL:
        result = update_case_account(
            case_id,
            account_id,
            case_number=case_number,
            posture="Known SP",
            account=account,
        )
        print(f"{case_number}: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
