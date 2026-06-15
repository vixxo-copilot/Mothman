# PolyAI Studio — MCP integrations

Docs: https://docs.poly.ai/integrations/mcp

PolyAI is an **MCP client**. Add external servers under Configure → Integrations → MCP.

For VixxoLink specifically (tool pack, guardrails), use skill `polyai-vixxo-bridge`.

## Generic setup

1. Secrets Vault — store server token
2. Configure → Integrations → MCP → Add
3. HTTPS URL + auth (Header / OAuth)
4. Connect → toggle tools individually
5. Test in debug chat; verify in Conversation Review → Diagnosis
