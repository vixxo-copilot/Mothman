# Vixxo MCP bearer fix — colleague handoff (copy/paste)

Two parts: **Part A** = one-time setup (paste into Cursor Agent). **Part B** = cleanup when Chrome login tabs already happened. Use both; Part B alone does not fix bad wiring.

---

## WHY TWO PARTS?

**Part A** fixes the root cause: `mcp.json` used bare `npx mcp-remote` or `url`, so each Vixxo endpoint opened its own browser OAuth tab.

| MCP | URL |
| --- | --- |
| Gateway | …/mcp/gateway |
| VixxoLink | …/mcp/vixxolink |
| Business Objects | …/mcp/bo-universe |
| Power BI | …/mcp/powerbi |

Bearer wrappers (`run-*-mcp.cmd`) send a token header and should not open Chrome when wired correctly.

**Part B** is still needed because old `mcp-remote` OAuth processes may still run, token files may be stale, **skills** MCP may have reverted `mcp.json`, or project + user `mcp.json` may duplicate entries.

You do **not** need to remove Linear, GitHub, or other MCPs.

---

## PART A — PASTE INTO CURSOR AGENT

```
Mirror Vixxo HTTP MCP wiring from vixxo-copilot/Mothman (main, commit 368c6c3 or later).

Goal: Fix Gateway, VixxoLink, Business Objects, and Power BI in Cursor on Windows using bearer-token wrappers (no bare npx mcp-remote, no vixxolink OAuth loop).

1) REPO ROOT
   Run git rev-parse --show-toplevel and use that absolute path in mcp.json (double backslashes in JSON).

2) PULL FILES FROM MOTHMAN (do not replace whole repo)
   git fetch https://github.com/vixxo-copilot/Mothman.git main
   Checkout into my workspace:
   .cursor/bin/mcp_env.py
   .cursor/bin/run-gateway-mcp.py + run-gateway-mcp.cmd
   .cursor/bin/run-vixxolink-mcp.py + run-vixxolink-mcp.cmd (bearer-only, no OAuth fallback)
   .cursor/bin/run-business-objects-mcp.py + run-business-objects-mcp.cmd
   .cursor/bin/run-powerbi-mcp.py + run-powerbi-mcp.cmd
   .cursor/bin/sync_gateway_token.py + sync_vixxolink_token.py
   .cursor/bin/repair-*-oauth.cmd (gateway, vixxolink, business-objects, powerbi)
   .cursor/mcp-sync-state.json (merge carefully if I have local overrides)

3) WIRE .cursor/mcp.json — cmd wrappers, NOT npx/url:
   gateway, vixxolink, business-objects, powerbi-prod → cmd.exe /c REPO\.cursor\bin\run-*-mcp.cmd

4) SKILLS-MCP SYNC STATE
   managed_entry_resolution "local" for gateway, vixxolink, business-objects, powerbi-prod
   Update managed_entry_fingerprints to match mcp.json.

5) TOKENS (report output, do not paste token values)
   python .cursor/bin/sync_gateway_token.py
   python .cursor/bin/sync_vixxolink_token.py

6) VERIFY
   python .agents/skills/vixxo-mcp-bearer-fix/scripts/verify_vixxo_mcp_wiring.py
   python bin/diagnose-mcp.py if present
   Tell me to quit Cursor fully, reopen, restart those four MCPs.

Do not commit unless I ask. Do not add .tmp/ or secrets to git.
```

---

## PART B — MANUAL CLEANUP (Command Prompt)

### B1. Go to your repo

```text
cd C:\Users\YourName\path\to\your-repo
```

Or: `git rev-parse --show-toplevel` → `cd` to that path.

### B2. Turn OFF in Cursor

Disable gateway, vixxolink, business-objects, powerbi-prod, and temporarily skills.

### B3. Check config

```text
findstr /i "vixxonow.com/mcp" .cursor\mcp.json
findstr /i "vixxonow.com/mcp" %USERPROFILE%\.cursor\mcp.json
```

Good: `run-gateway-mcp.cmd`, `run-vixxolink-mcp.cmd`, etc.  
Bad: `npx` + `mcp-remote`, or `"url": "https://vixxonow.com/mcp/..."`

### B4. Clear stale OAuth

```text
.cursor\bin\repair-gateway-oauth.cmd
.cursor\bin\repair-vixxolink-oauth.cmd
.cursor\bin\repair-business-objects-oauth.cmd
.cursor\bin\repair-vixxonow-oauth.cmd
.cursor\bin\repair-powerbi-oauth.cmd
```

### B5. Sync tokens

```text
python .cursor\bin\sync_gateway_token.py
python .cursor\bin\sync_vixxolink_token.py
```

Both should show **status=OK**. If VixxoLink prints
`vixxolink_rejected_gateway_bearer`, run one terminal sign-in (not Cursor
Connect):

```text
python .cursor\bin\refresh_vixxolink_oauth.py
python .cursor\bin\sync_vixxolink_token.py
```

```text
dir %USERPROFILE%\.vixxo\gateway_api_token
dir %USERPROFILE%\.vixxo\vixxolink_api_token
```

### B6. Restart Cursor

Quit fully → reopen → enable MCPs one at a time → skills last.

### B7. Verify

```text
python .agents\skills\vixxo-mcp-bearer-fix\scripts\verify_vixxo_mcp_wiring.py
```

---

## QUICK REFERENCE

| Situation | Action |
| --- | --- |
| First-time fix | Part A then Part B |
| Chrome after fix | Part B only |
| Config reverts on restart | sync-state `local` + disable skills briefly |
| One MCP still OAuth | Check browser URL path |

**Source:** github.com/vixxo-copilot/Mothman — main (368c6c3+)
