#!/usr/bin/env python3
"""Load Crystal's Outlook email signatures for Graph send/reply.

Default for all Graph sends: compact Reply signature
(`assets/email-signature/reply.compact.html`) — same colors/content as
Outlook Reply, with tightened spacing. Optional `--raw` loads the full
Word HTML from %%APPDATA%%\\Microsoft\\Signatures.

Usage:
  python .cursor/bin/outlook_signature.py --mode reply
  python .cursor/bin/outlook_signature.py --mode new
  python .cursor/bin/outlook_signature.py --mode reply --json
  python .cursor/bin/outlook_signature.py --sync   # refresh assets/email-signature/
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import pathlib
import re
import shutil
import sys
import winreg

SIG_ROOT = pathlib.Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Signatures"
ASSETS = pathlib.Path(__file__).resolve().parents[2] / "assets" / "email-signature"
COMPACT_REPLY = ASSETS / "reply.compact.html"
# Graph sends always use Reply (not the Connex new-message signature).
FORCE_REPLY_FOR_ALL = True

# Outlook profile registry path for signature defaults (Office 16 / Outlook)
PROFILE_ROOT = r"Software\Microsoft\Office\16.0\Outlook\Profiles"


def _reg_str(value) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-16-le", errors="ignore").rstrip("\x00")
    return str(value)


def read_outlook_defaults() -> dict[str, str]:
    """Return {new, reply} signature display names from the Outlook profile."""
    defaults = {"new": "", "reply": ""}
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, PROFILE_ROOT) as profiles:
            # Walk profile subkeys looking for New Signature / Reply-Forward Signature
            def walk(key, path: str = "") -> None:
                try:
                    i = 0
                    while True:
                        name = winreg.EnumValue(key, i)[0]
                        if name in ("New Signature", "Reply-Forward Signature"):
                            _, val, _ = winreg.EnumValue(key, i)
                            text = _reg_str(val).strip()
                            if name == "New Signature" and text:
                                defaults["new"] = text
                            if name == "Reply-Forward Signature" and text:
                                defaults["reply"] = text
                        i += 1
                except OSError:
                    pass
                try:
                    j = 0
                    while True:
                        sub = winreg.EnumKey(key, j)
                        with winreg.OpenKey(key, sub) as child:
                            walk(child, f"{path}\\{sub}" if path else sub)
                        j += 1
                except OSError:
                    pass

            walk(profiles)
    except OSError:
        pass

    # Fallbacks matching Crystal's current Outlook defaults (2026-07-31)
    if not defaults["new"]:
        defaults["new"] = "Connex 2026 New Message (Crystal.Gagner@vixxo.com)"
    if not defaults["reply"]:
        defaults["reply"] = "Reply (Crystal.Gagner@vixxo.com)"
    return defaults


def _resolve_htm(signature_name: str) -> pathlib.Path:
    live = SIG_ROOT / f"{signature_name}.htm"
    if live.exists():
        return live
    # Fallback to synced assets
    mode = "reply" if signature_name.lower().startswith("reply") else "new-message"
    asset = ASSETS / f"{mode}.htm"
    if asset.exists():
        return asset
    raise FileNotFoundError(
        f"Signature HTML not found for {signature_name!r} "
        f"(looked in {live} and {asset})"
    )


def _files_dir_for(htm_path: pathlib.Path, signature_name: str) -> pathlib.Path | None:
    live = SIG_ROOT / f"{signature_name}_files"
    if live.is_dir():
        return live
    # Asset fallback: reply-files / new-message-files
    mode = "reply" if signature_name.lower().startswith("reply") else "new-message"
    asset = ASSETS / f"{mode}-files"
    return asset if asset.is_dir() else None


def load_compact_reply(mode: str) -> dict:
    """Compact Reply signature used for all Graph sends by default."""
    defaults = read_outlook_defaults()
    if not COMPACT_REPLY.exists():
        raise FileNotFoundError(f"Missing compact signature: {COMPACT_REPLY}")
    html = COMPACT_REPLY.read_text(encoding="utf-8")
    # Strip HTML comments
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S).strip()
    return {
        "mode": mode,
        "signatureName": defaults["reply"],
        "sourcePath": str(COMPACT_REPLY),
        "html": html,
        "attachments": [],
        "defaults": defaults,
        "compact": True,
    }


def load_signature(mode: str, *, raw: bool = False) -> dict:
    """Return Graph-ready signature payload.

    Keys: mode, signatureName, html, attachments (list of Graph fileAttachment dicts)

    By default returns the compact Reply signature for both `reply` and `new`.
    Pass raw=True to load full Outlook Word HTML (and Connex for new).
    """
    if mode not in ("reply", "new"):
        raise ValueError("mode must be 'reply' or 'new'")

    if not raw and (FORCE_REPLY_FOR_ALL or mode == "reply"):
        if COMPACT_REPLY.exists():
            return load_compact_reply(mode)

    defaults = read_outlook_defaults()
    # Prefer Reply even for "new" unless raw explicitly wants Outlook new default
    use_reply = FORCE_REPLY_FOR_ALL or mode == "reply"
    signature_name = defaults["reply" if use_reply else "new"]
    htm_path = _resolve_htm(signature_name)
    files_dir = _files_dir_for(htm_path, signature_name)

    html = htm_path.read_text(encoding="utf-8", errors="replace")
    body_m = re.search(r"(?is)<body[^>]*>(.*)</body>", html)
    body = body_m.group(1).strip() if body_m else html

    attachments: list[dict] = []
    used_cids: set[str] = set()

    def img_repl(match: re.Match[str]) -> str:
        src = match.group(1)
        filename = pathlib.Path(src.replace("\\", "/").split("?")[0]).name
        if not filename or files_dir is None:
            return match.group(0)
        candidate = files_dir / filename
        if not candidate.exists():
            # URL-decoded name may differ; try unquoted
            from urllib.parse import unquote

            candidate = files_dir / unquote(filename)
        if not candidate.exists():
            return match.group(0)

        cid = re.sub(r"[^A-Za-z0-9_.-]", "_", filename)
        if cid not in used_cids:
            used_cids.add(cid)
            ext = candidate.suffix.lower().lstrip(".")
            content_type = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "gif": "image/gif",
            }.get(ext, "application/octet-stream")
            attachments.append(
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": filename,
                    "contentType": content_type,
                    "contentId": cid,
                    "isInline": True,
                    "contentBytes": base64.b64encode(candidate.read_bytes()).decode(
                        "ascii"
                    ),
                }
            )
        return f'src="cid:{cid}"'

    body = re.sub(r'src=["\']([^"\']+)["\']', img_repl, body, flags=re.I)

    # Minimal spacer before signature
    wrapped = (
        f'<div id="mothman-outlook-signature" style="margin-top:8px">{body}</div>'
    )

    return {
        "mode": mode,
        "signatureName": signature_name,
        "sourcePath": str(htm_path),
        "html": wrapped,
        "attachments": attachments,
        "defaults": defaults,
        "compact": False,
    }


def append_signature(
    body_html: str, mode: str = "reply", *, raw: bool = False
) -> tuple[str, list[dict]]:
    """Append Outlook signature HTML to an existing HTML body."""
    sig = load_signature(mode, raw=raw)
    # Avoid double-append
    if 'id="mothman-outlook-signature"' in body_html:
        return body_html, []
    return body_html.rstrip() + sig["html"], sig["attachments"]


def sync_assets() -> None:
    """Copy live Outlook signatures into assets/email-signature/."""
    defaults = read_outlook_defaults()
    ASSETS.mkdir(parents=True, exist_ok=True)
    mapping = {
        "reply": defaults["reply"],
        "new-message": defaults["new"],
    }
    manifest = {"syncedFrom": str(SIG_ROOT), "defaults": defaults, "files": {}}
    for label, name in mapping.items():
        # Keep HTML + plain text only (skip bulky .rtf — not used for Graph sends)
        for ext in (".htm", ".txt"):
            src = SIG_ROOT / f"{name}{ext}"
            if src.exists():
                dst = ASSETS / f"{label}{ext}"
                shutil.copy2(src, dst)
                manifest["files"][f"{label}{ext}"] = name
        stale_rtf = ASSETS / f"{label}.rtf"
        if stale_rtf.exists():
            stale_rtf.unlink()
        files_src = SIG_ROOT / f"{name}_files"
        if files_src.is_dir():
            files_dst = ASSETS / f"{label}-files"
            if files_dst.exists():
                shutil.rmtree(files_dst)
            # Copy image/binary assets; skip Office theme metadata noise if huge
            files_dst.mkdir(parents=True, exist_ok=True)
            for f in files_src.iterdir():
                if f.is_file() and f.suffix.lower() in {
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".gif",
                    ".xml",
                    ".thmx",
                }:
                    shutil.copy2(f, files_dst / f.name)
            manifest["files"][f"{label}-files"] = name
    (ASSETS / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    # Compact Reply is the Graph-send preview (always)
    payload = load_signature("reply")
    preview = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>Signature preview — compact Reply</title></head>"
        "<body style='background:#fff;padding:24px;font-family:Calibri,Arial,sans-serif;font-size:11pt'>"
        "<p style='margin:0 0 12px 0;color:#666'>Sample message body.</p>"
        f"{payload['html']}</body></html>"
    )
    (ASSETS / "reply.preview.html").write_text(preview, encoding="utf-8")
    print(f"Synced signatures to {ASSETS}")
    print(json.dumps(manifest, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("reply", "new"),
        default="reply",
        help="Signature mode (both resolve to compact Reply unless --raw)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit full JSON (html + Graph attachments)",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Use full Outlook Word HTML instead of compact Reply",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Copy live Outlook signatures into assets/email-signature/",
    )
    parser.add_argument(
        "--defaults",
        action="store_true",
        help="Print Outlook New/Reply signature defaults",
    )
    args = parser.parse_args()

    if args.sync:
        sync_assets()
        return 0
    if args.defaults:
        print(json.dumps(read_outlook_defaults(), indent=2))
        return 0

    payload = load_signature(args.mode, raw=args.raw)
    if args.json:
        print(json.dumps(payload))
    else:
        # HTML only (attachments summary on stderr)
        if payload["attachments"]:
            print(
                f"# {len(payload['attachments'])} inline attachment(s) — "
                f"use --json for Graph payload",
                file=sys.stderr,
            )
        print(payload["html"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
