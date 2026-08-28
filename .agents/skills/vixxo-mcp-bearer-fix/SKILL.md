---
name: vixxo-mcp-bearer-fix
description: >-
  Fixes Cursor MCP OAuth loops for Vixxo HTTP servers (Gateway, VixxoLink,
  Business Objects, Power BI) on Windows by wiring bearer-token launchers,
  syncing ~/.vixxo tokens, clearing stale mcp-remote OAuth, and protecting
  mcp-sync-state from skills-mcp revert. Use when MCP shows Bearer token
  required, Chrome login tabs pop up for vixxonow.com/mcp, vixxolink OAuth
  loop on port 37882, gateway port 29069, or helping a teammate mirror the
  Mothman MCP launcher fix.
---

# Vixxo HTTP MCP Bearer Fix (Cursor / Windows)

Work-only skill. Stops browser OAuth pop-ups for Vixxo endpoints by using
**bearer wrappers** in `.cursor/bin/` instead of bare `npx mcp-remote`.

## When to use

- Gateway / VixxoLink / Business Objects / Power BI MCP red or OAuth loop
- `Bearer token required for MCP gateway`
- Multiple Chrome tabs on Cursor restart (`/mcp/gateway`, `/vixxolink`, etc.)
- "Mirror Mothman MCP wiring" for a colleague's assistants-template clone
- After `skills` MCP reverted `mcp.json` to bare `npx`

## Root cause (brief)

Bare `npx mcp-remote https://vixxonow.com/mcp/*` sends **no** auth header →
each endpoint opens its own browser OAuth tab. Bearer wrappers inject
`Authorization: Bearer …` from `~/.vixxo/*.token` files.

| Token file | Servers |
| --- | --- |
| `~/.vixxo/gateway_api_token` | gateway, business-objects, powerbi-prod, vixxonow |
| `~/.vixxo/vixxolink_api_token` | vixxolink only |

Wrappers **fail fast** without tokens (no browser). If Chrome still opens,
Cursor is still on OAuth path or stale `mcp-remote` processes are running.

## Guardrails

- Do **not** commit token files, `.mcp-auth`, or `.tmp/` artifacts
- Do **not** paste bearer token values in chat
- Do **not** send outbound messages
- Commit launcher changes only when {{employee_name}} asks
- Other MCPs (Linear, HubSpot) have their own OAuth — unrelated to this fix

## Quick verify

From repo root:

```bash
python .agents/skills/vixxo-mcp-bearer-fix/scripts/verify_vixxo_mcp_wiring.py
python bin/diagnose-mcp.py
```

## Workflow A — Fix this workspace (agent)

Copy this checklist and track progress:

```
- [ ] 1. Repo root: git rev-parse --show-toplevel
- [ ] 2. Ensure launcher files exist in .cursor/bin/ (see reference.md)
- [ ] 3. Wire .cursor/mcp.json to run-*-mcp.cmd (not npx/url)
- [ ] 4. mcp-sync-state.json: local resolution for all four servers
- [ ] 5. Repair stale OAuth + sync tokens
- [ ] 6. verify_vixxo_mcp_wiring.py + diagnose-mcp.py
- [ ] 7. Tell user: quit Cursor fully, restart four MCPs
```

### Step 1 — Repo root

```bash
git rev-parse --show-toplevel
```

Use that path in `mcp.json` (`cmd.exe` + doubled backslashes on Windows).

### Step 2 — Launcher files

Required under `.cursor/bin/`:

| Server | Files |
| --- | --- |
| gateway | `run-gateway-mcp.py`, `run-gateway-mcp.cmd` |
| vixxolink | `run-vixxolink-mcp.py`, `run-vixxolink-mcp.cmd` (bearer-only, no OAuth fallback) |
| business-objects | `run-business-objects-mcp.py`, `run-business-objects-mcp.cmd` |
| powerbi-prod | `run-powerbi-mcp.py`, `run-powerbi-mcp.cmd` |
| shared | `mcp_env.py`, `sync_gateway_token.py`, `sync_vixxolink_token.py` |
| repair | `repair-gateway-oauth.cmd`, `repair-vixxolink-oauth.cmd`, `repair-business-objects-oauth.cmd`, `repair-powerbi-oauth.cmd` |

If missing, fetch from `vixxo-copilot/Mothman` `main` (368c6c3+ for core fix;
Power BI wrapper on latest `main`):

```bash
git fetch https://github.com/vixxo-copilot/Mothman.git main
git checkout FETCH_HEAD -- .cursor/bin/mcp_env.py .cursor/bin/run-gateway-mcp.*
# ... (see reference.md for full file list)
```

Do **not** replace the whole repo.

### Step 3 — Wire `.cursor/mcp.json`

Each server must use:

```json
"command": "C:\\Windows\\System32\\cmd.exe",
"args": ["/c", "REPO\\.cursor\\bin\\run-<server>-mcp.cmd"]
```

**Bad:** `"command": "npx"` + `mcp-remote`, or `"url": "https://vixxonow.com/mcp/..."`

Do not change unrelated MCP entries.

### Step 4 — Protect from skills-mcp revert

In `.cursor/mcp-sync-state.json`, set `managed_entry_resolution` to `"local"` for:

`gateway`, `vixxolink`, `business-objects`, `powerbi-prod`

Update `managed_entry_fingerprints` to match wired `mcp.json` entries after edits.

Temporarily disable **skills** MCP in Cursor if config keeps reverting after restart.

### Step 5 — Cleanup + tokens

Ask user to disable the four servers (+ skills) in Cursor MCP UI first.

```bash
.cursor/bin/repair-gateway-oauth.cmd
.cursor/bin/repair-vixxolink-oauth.cmd
.cursor/bin/repair-business-objects-oauth.cmd
.cursor/bin/repair-powerbi-oauth.cmd
python .cursor/bin/sync_gateway_token.py
python .cursor/bin/sync_vixxolink_token.py
```

Both sync scripts should report `status=OK`. If FAIL: one Gateway sign-in to
populate `~/.mcp-auth`, then re-run sync (not four separate logins).

Check for duplicate user-level config:

```bash
# Windows
findstr /i "vixxonow.com/mcp" %USERPROFILE%\.cursor\mcp.json
```

Remove duplicate gateway/vixxolink entries from user `mcp.json` if project file has wrappers.

### Step 6 — Verify and hand off

Run verify script and `bin/diagnose-mcp.py`. Report PASS/FAIL per server.

Tell {{employee_name}}:

1. Quit Cursor completely
2. Reopen workspace
3. Enable MCPs one at a time: gateway → vixxolink → business-objects → powerbi-prod
4. Re-enable **skills** last
5. Do not click Connect on vixxolink if wrappers work

## Workflow B — Share fix with a colleague

Produce a copy-paste handoff from [user-handoff.md](user-handoff.md):

- **Part A** — paste into their Cursor Agent (one-time wiring)
- **Part B** — Command Prompt cleanup (repair + sync + restart)

Customize only their repo path (`git rev-parse --show-toplevel`).

## Workflow C — Diagnose only

User reports pop-ups but wiring looks correct:

1. Run `verify_vixxo_mcp_wiring.py`
2. Check browser URL path (`/powerbi` vs `/gateway`)
3. Kill stale `mcp-remote` via repair scripts
4. Confirm `skills` did not revert `mcp.json` (`git diff .cursor/mcp.json`)

## Additional resources

- Root cause and troubleshooting: [reference.md](reference.md)
- Colleague copy-paste pack: [user-handoff.md](user-handoff.md)
- Canonical launcher docs: `.cursor/mcp.README.md` (Vixxo HTTP MCPs section)
