#!/usr/bin/env python3
"""Backward-compat wrapper — delegates to polyai skill."""
from __future__ import annotations

import runpy
from pathlib import Path

TARGET = Path(__file__).resolve().parents[2] / "polyai" / "scripts" / "audit_conversation.py"
runpy.run_path(str(TARGET), run_name="__main__")
