# Vixxo MCP bearer fix — reference

## Endpoints and launchers

| MCP key | URL | Launcher | Token source |
| --- | --- | --- | --- |
| gateway | `https://vixxonow.com/mcp/gateway` | `run-gateway-mcp.cmd` | `gateway_api_token` |
| vixxolink | `https://vixxonow.com/mcp/vixxolink` | `run-vixxolink-mcp.cmd` | `vixxolink_api_token` |
| business-objects | `https://vixxonow.com/mcp/bo-universe` | `run-business-objects-mcp.cmd` | `gateway_api_token` |
| powerbi-prod | `https://vixxonow.com/mcp/powerbi` | `run-powerbi-mcp.cmd` | `gateway_api_token` |

Shared helper: `.cursor/bin/mcp_env.py`

## OAuth ports (legacy cleanup)

| Server | Repair script | Port |
| --- | --- | --- |
| Gateway | `repair-gateway-oauth.cmd` | 29069 |
| VixxoLink | `repair-vixxolink-oauth.cmd` | 37882 |
| Business Objects | `repair-business-objects-oauth.cmd` | 43212 |
| Power BI | `repair-powerbi-oauth.cmd` | kills `mcp-remote` for `/mcp/powerbi` |

## skills-mcp revert

Canonical manifest uses bare `npx mcp-remote` for these servers. If
`managed_entry_fingerprints` in `.cursor/mcp-sync-state.json` do not match
local wrapper entries, or `managed_entry_resolution` is not `local`, apply
may revert `mcp.json` on Cursor start.

Run doctor (optional):

```bash
npx -y @vixxo-copilot/skills-mcp doctor
```

Destructive conflicts for gateway/vixxolink/salesforce mean sync-state is stale.

## Duplicate config surfaces

1. Project: `<repo>/.cursor/mcp.json`
2. User: `%USERPROFILE%/.cursor/mcp.json`

Both defining the same URL with `url` or `npx` doubles OAuth flows.

## Mothman file checkout list

```bash
git fetch https://github.com/vixxo-copilot/Mothman.git main
git checkout FETCH_HEAD -- \
  .cursor/bin/mcp_env.py \
  .cursor/bin/run-gateway-mcp.py \
  .cursor/bin/run-gateway-mcp.cmd \
  .cursor/bin/run-vixxolink-mcp.py \
  .cursor/bin/run-vixxolink-mcp.cmd \
  .cursor/bin/run-business-objects-mcp.py \
  .cursor/bin/run-business-objects-mcp.cmd \
  .cursor/bin/run-powerbi-mcp.py \
  .cursor/bin/run-powerbi-mcp.cmd \
  .cursor/bin/sync_gateway_token.py \
  .cursor/bin/sync_vixxolink_token.py \
  .cursor/bin/repair-gateway-oauth.cmd \
  .cursor/bin/repair-vixxolink-oauth.cmd \
  .cursor/bin/repair-business-objects-oauth.cmd \
  .cursor/bin/repair-powerbi-oauth.cmd
```

Merge `.cursor/mcp-sync-state.json` carefully; do not blindly overwrite local overrides.

## Fingerprint helper

After wiring `mcp.json`, update sync-state fingerprints (Node one-liner from repo root):

```bash
node -e "
const fs=require('fs');const c=require('crypto');
function sn(v){if(typeof v==='string')return v.normalize('NFC');if(Array.isArray(v))return v.map(sn);if(v&&typeof v==='object'){const o={};for(const k of Object.keys(v).sort())o[k]=sn(v[k]);return o;}return v;}
function fp(v){return 'sha256:'+c.createHash('sha256').update(JSON.stringify(sn(v))).digest('hex');}
const m=JSON.parse(fs.readFileSync('.cursor/mcp.json','utf8')).mcpServers;
for (const k of ['gateway','vixxolink','business-objects','powerbi-prod']) console.log(k, fp(m[k]));
"
```

## Troubleshooting matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| 4 Chrome tabs on restart | All four still bare `npx` | Part A wiring |
| Chrome for gateway only | Stale listener or missing gateway token | repair-gateway + sync_gateway |
| Chrome for powerbi only | Still bare `npx` | powerbi wrapper |
| Config reverts overnight | skills-mcp sync | local resolution + fingerprints |
| Connect on vixxolink | url/npx config | wrapper in mcp.json |
| Wrapper exists, Chrome opens | Stale mcp-remote PIDs | repair scripts |
| PASS verify, red in Cursor | Did not full quit Cursor | Quit app, reopen |

## Related repo docs

- `.cursor/mcp.README.md` — Vixxo HTTP MCPs section
- `bin/diagnose-mcp.py` — launcher + token checks
