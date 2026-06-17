#!/usr/bin/env python3
"""Legacy entry point — use live_run_batch.py --queue ksonboarding."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from live_run_batch import main

if __name__ == "__main__":
    import sys

    if "--queue" not in sys.argv:
        sys.argv[1:1] = ["--queue", "ksonboarding"]
    raise SystemExit(main())
