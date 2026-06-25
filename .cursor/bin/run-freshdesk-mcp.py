#!/usr/bin/env python3
"""Windows launcher for freshdesk-mcp — loads credentials then starts stdio server."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

PATCH_ID = "1.1.1-search-query-quotes"
PACKAGE_VERSION = "1.1.1"


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and val and not os.environ.get(key):
            os.environ[key] = val


def load_secret_file(path: Path, target: str) -> None:
    if os.environ.get(target) or not path.is_file():
        return
    secret = path.read_text(encoding="utf-8").strip()
    if secret:
        os.environ[target] = secret


def apply_search_query_patch(vendor_root: Path) -> None:
    freshdesk_js = vendor_root / "dist" / "freshdesk.js"
    tickets_js = vendor_root / "dist" / "tools" / "tickets.js"

    freshdesk_src = freshdesk_js.read_text(encoding="utf-8")
    if "formatFreshdeskSearchQuery" not in freshdesk_src:
        freshdesk_js.write_text(
            freshdesk_src.replace(
                "export function parseLinkHeader(link) {",
                """/** Wrap Freshdesk ticket search filter in required double quotes. */
export function formatFreshdeskSearchQuery(query) {
    const trimmed = query.trim();
    if (trimmed.startsWith('"') && trimmed.endsWith('"')) {
        return trimmed;
    }
    return `"${trimmed}"`;
}
export function parseLinkHeader(link) {""",
            ),
            encoding="utf-8",
        )

    tickets_src = tickets_js.read_text(encoding="utf-8")
    if "formatFreshdeskSearchQuery" not in tickets_src:
        tickets_src = tickets_src.replace(
            'import { errorPayload, fd, parseLinkHeader } from "../freshdesk.js";',
            'import { errorPayload, fd, formatFreshdeskSearchQuery, parseLinkHeader } from "../freshdesk.js";',
        )
        tickets_src = tickets_src.replace(
            """    tool(server, "search_tickets", "Search tickets using Freshdesk filter syntax.", { query: z.string() }, async ({ query }) => {
        const res = await fd.get("/search/tickets", { query });
        return text(res.ok ? res.data : errorPayload("Failed to search tickets", res));
    });""",
            """    tool(server, "search_tickets", "Search tickets using Freshdesk filter syntax. Pass the filter expression only (e.g. status:2, created_at:>'2026-06-24', group_id:159000485013 AND status:2). Double quotes around the expression are added automatically if omitted.", {
        query: z.string(),
        page: z.number().int().min(1).optional().default(1),
    }, async ({ query, page }) => {
        const res = await fd.get("/search/tickets", {
            query: formatFreshdeskSearchQuery(query),
            page,
        });
        return text(res.ok ? res.data : errorPayload("Failed to search tickets", res));
    });""",
        )
        tickets_js.write_text(tickets_src, encoding="utf-8")


def extract_package(tar_path: Path, vendor_root: Path) -> None:
    vendor_root.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, "r:gz") as archive:
        members = [m for m in archive.getmembers() if m.name.startswith("package/")]
        for member in members:
            member.name = member.name.removeprefix("package/")
            if not member.name:
                continue
            archive.extract(member, vendor_root)


def ensure_vendor(root: Path) -> Path:
    vendor_root = root / ".cursor" / "vendor" / "freshdesk-mcp"
    marker = vendor_root / ".vixxo-patch"
    entry = vendor_root / "dist" / "index.js"
    node_modules = vendor_root / "node_modules"

    if marker.read_text(encoding="utf-8").strip() == PATCH_ID if marker.is_file() else False:
        if entry.is_file() and node_modules.is_dir():
            return vendor_root

    if vendor_root.exists():
        shutil.rmtree(vendor_root)
    vendor_root.mkdir(parents=True, exist_ok=True)

    npm = os.environ.get("NPM", "").strip() or shutil.which("npm") or "npm"
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        subprocess.run(
            [npm, "pack", f"freshdesk-mcp@{PACKAGE_VERSION}"],
            cwd=tmp_dir,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        tgz = next(tmp_dir.glob("freshdesk-mcp-*.tgz"))
        extract_package(tgz, vendor_root)

    subprocess.run(
        [npm, "install", "--omit=dev"],
        cwd=vendor_root,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    apply_search_query_patch(vendor_root)
    marker.write_text(PATCH_ID + "\n", encoding="utf-8")
    return vendor_root


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    load_env_file(root / ".env")

    home_vixxo = Path.home() / ".vixxo"
    load_secret_file(home_vixxo / "freshdesk_token", "FRESHDESK_API_KEY")
    load_secret_file(home_vixxo / "freshdesk_api_key", "FRESHDESK_API_KEY")

    if not os.environ.get("FRESHDESK_API_KEY") and os.environ.get("FRESHDESK_TOKEN"):
        os.environ["FRESHDESK_API_KEY"] = os.environ["FRESHDESK_TOKEN"]

    os.environ.setdefault("FRESHDESK_DOMAIN", "vixxo-helpdesk.freshdesk.com")
    os.environ.setdefault("NODE_ENV", "production")

    if not os.environ.get("FRESHDESK_API_KEY"):
        print(
            "Freshdesk MCP: FRESHDESK_API_KEY not set — server will start but API tools will fail until configured.",
            file=sys.stderr,
        )
        print(
            "Fix: set FRESHDESK_API_KEY in .env or save key to ~/.vixxo/freshdesk_token, then restart MCP.",
            file=sys.stderr,
        )

    try:
        vendor_root = ensure_vendor(root)
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"Freshdesk MCP: failed to prepare patched vendor package: {exc}", file=sys.stderr)
        return 1

    node = os.environ.get("NODE", "").strip() or shutil.which("node") or "node"
    entry = vendor_root / "dist" / "index.js"
    if not entry.is_file():
        print(f"Freshdesk MCP: patched vendor entry missing at {entry}", file=sys.stderr)
        return 1
    return subprocess.call([node, str(entry), *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
