#!/usr/bin/env python3
"""Compatibility wrapper — use list_owner_vm_cases.py.

Defaults to the signed-in Salesforce user. Crystal's Good Morning can still
call this path; pass --owner-email only to force a mailbox.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from list_owner_vm_cases import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
