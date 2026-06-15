# PolyAI Agent Studio — MCP setup for Vixxo

Official docs: https://docs.poly.ai/integrations/mcp

## Steps

1. **Secrets first** — Agent Studio → Configure → Secrets. Add the Vixxo MCP
   token (header value or OAuth client credentials). Grant the secret to your
   project.

2. **Add integration** — Configure → Integrations → **MCP** tab → Add MCP
   integration.

3. **Fields**

   | Field | Value |
   | --- | --- |
   | MCP server URL | `https://vixxonow.com/mcp/vixxolink` |
   | Timeout | Start at 15–20s for SR bundle reads; max 30 |
   | Authentication | Header (typical) or OAuth per Vixxo IT guidance |

4. **Connect** — Studio discovers tools. Expand the panel and toggle tools
   individually. Prefer the voice tool pack in `vixxolink-voice-tool-pack.md`.

5. **Debug chat** — Configure → Test (or debug chat session). Ask: "What is
   the status of service request 12345678?" Confirm tool invocation in
   Conversation Review → Diagnosis.

6. **Optional second server** — Add Gateway only if the voice flow needs
   invoice validation: `https://vixxonow.com/mcp/gateway`.

## Common failures

| Symptom | Likely cause |
| --- | --- |
| Connect fails immediately | Wrong URL, TLS, or token not in Secrets Vault |
| Tools list empty | Server reachable but auth rejected |
| Tool called, timeout | Increase timeout; `resolve_service_request` can be slow |
| Tool succeeds in Cursor, fails in PolyAI | Different token scope or tool toggled off |
| Agent never calls tool | Flow/prompt does not instruct tool use; fix in Studio |

## Auth patterns

- **Header** — `Authorization: Bearer <token>` or custom header per Vixxo
- **OAuth** — Client credentials to Vixxo token endpoint; store client id/secret
  in Secrets Vault

Match whatever works for your Cursor VixxoLink MCP session. Ask Vixxo platform
if unsure which token type applies to Agent Studio integrations.
