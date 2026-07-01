#!/usr/bin/env python3
import subprocess
from pathlib import Path

SF = str(Path.home() / "AppData/Roaming/npm/sf.cmd")
PRIMARY = "500TS00000nmtkLYAQ"
emails = [
    ("00005886", "Req 19", "02sTS00000lFFLVYA4", "Req 19 auto-reply"),
    ("00005831", "Req 22", "02sTS00000lCFg9YAG", "Req 22 cert EP15270"),
    ("00006016", "Req 23", "02sTS00000lSDnJYAW", "Req 23 cert ET19680"),
]
for case_num, req, em_id, note in emails:
    subject = f"SF email archive — {req} from Case #{case_num}"
    desc = (
        f"Email thread archived from merged SF Case #{case_num} ({req}). "
        f"EmailMessage Id: {em_id}. {note}. "
        f"Certs linked on primary #00005985 Files tab. "
        f"EmailMessage.ParentId reparent blocked by org FLS; thread preserved on closed Case."
    )
    proc = subprocess.run(
        [
            SF,
            "data",
            "create",
            "record",
            "--sobject",
            "Task",
            "--target-org",
            "vixxo",
            "--json",
            "--values",
            f"Subject='{subject}' Description='{desc}' WhatId={PRIMARY} Status=Completed Priority=Normal",
        ],
        capture_output=True,
        text=True,
    )
    print(subject, "OK" if proc.returncode == 0 else proc.stderr[:150])
