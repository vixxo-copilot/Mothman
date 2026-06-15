---
name: polyai-vixxo-bridge
description: >-
  Wires VixxoLink and Gateway MCP into PolyAI Agent Studio for voice agents.
  Documents which VixxoLink tools to enable, read-only voice guardrails, and
  Cursor-side SR validation. For general PolyAI API and conversation audit
  work, use the polyai skill instead. Use when wiring VixxoLink into PolyAI,
  voice agent MCP tool packs, or Vixxo outbound integration design.
---

# PolyAI ↔ Vixxo Bridge

## Scope

This skill is **Vixxo MCP wiring only**. PolyAI API, conversation audit, and
Jupiter config live in the **`polyai`** skill.

| Task | Skill |
| --- | --- |
| Pull/audit PolyAI conversations | `polyai` |
| Wire VixxoLink MCP in Agent Studio | **this skill** |
| Validate SR lookups from Cursor | **this skill** + VixxoLink MCP |

## When to use

Trigger phrases:

- "wire VixxoLink into PolyAI"
- "which MCP tools should the voice agent have?"
- "review PolyAI conversations where SR lookup failed"
- "test-resolve SR the way the phone agent would"
- "PolyAI Agent Studio MCP setup"

## Output format

Return results with these sections:

1. **Mode** (`A`, `B`, or `A+B`)
2. **Goal** (one sentence)
3. **Configuration or findings** (steps, tool list, or API results)
4. **Guardrails** (read vs write, PII, approval gates)
5. **Next actions** (numbered, owner-assigned where possible)

---

## Mode A — PolyAI voice agent uses Vixxo data

PolyAI is an **MCP client**. Point Agent Studio at Vixxo MCP URLs; PolyAI
discovers tools automatically. PolyAI does **not** expose an MCP server for
Cursor to call your voice agents.

### Studio setup checklist

Copy this checklist and track progress:

```
PolyAI MCP setup:
- [ ] Open Agent Studio → Configure → Integrations → MCP
- [ ] Add MCP server URL (see table below)
- [ ] Set auth (Header / OAuth) using Secrets Vault credentials
- [ ] Click Connect — verify tools discovered
- [ ] Enable only the voice-safe tool pack (see reference)
- [ ] Test in debug chat with a known SR number
- [ ] Promote to sandbox, then live
```

### Vixxo MCP endpoints (match `.cursor/mcp.json`)

| Server | URL | Typical voice use |
| --- | --- | --- |
| VixxoLink | `https://vixxonow.com/mcp/vixxolink` | SR lookup, site, SP, notes (read-first) |
| Gateway | `https://vixxonow.com/mcp/gateway` | Invoice/payment validation (rare on voice) |
| Gong | `https://transact.vixxo.com/mcp/gong` | Call context (ops review, not live voice) |

Auth: use the same token type Vixxo IT provisions for MCP. Store in PolyAI
**Secrets Vault**; grant access to the project. Never embed tokens in flows.

Full Studio steps: [reference/polyai-studio-mcp-setup.md](reference/polyai-studio-mcp-setup.md)

### Recommended voice tool pack

Start **read-only**. Enable writes only after explicit product approval.

| Priority | VixxoLink tool | Voice scenario |
| --- | --- | --- |
| P0 | `vixxolink_resolve_service_request` | Caller gives SR number — status, site, SP, notes |
| P0 | `vixxolink_search_service_requests` | Caller gives site/store, not SR number |
| P1 | `vixxolink_find_site` | Site address / contact lookup |
| P1 | `vixxolink_get_customer` | Confirm customer context |
| P2 | `vixxolink_post_service_request_note` | **Write** — log call outcome on SR |
| Block | `vixxolink_patch_service_request` | Status changes — human approval only |
| Block | `vixxolink_release_service_request` | Dispatch actions — not for voice |

Full pack with guardrails: [reference/vixxolink-voice-tool-pack.md](reference/vixxolink-voice-tool-pack.md)

### Cursor-side validation (before/after Studio wiring)

Rehearse the same call path Cursor uses:

1. `vixxolink_get_customer_service_health` — confirm MCP reachable
2. `vixxolink_resolve_service_request` with `include: ["notes", "time_events"]`
3. Compare output to what PolyAI debug chat returns

If Cursor succeeds but PolyAI fails, suspect auth, timeout (default 10s), or
tool toggles off in Studio.

---

## With `polyai` skill — end-to-end ship checklist

```
Task progress:
- [ ] polyai: audit 3 recent outbound conversations (VALID_SR, API_OK)
- [ ] polyai-vixxo-bridge: confirm VixxoLink MCP in Studio + P0 tools
- [ ] Cursor: vixxolink_resolve_service_request for extracted SR numbers
- [ ] Document gaps (custom API vs MCP; tool not called vs timeout)
```

---

## Guardrails

- **Outbound messaging** — draft-only; never send customer-facing comms without
  explicit user approval (`.cursor/rules/outbound-messaging-guardrail.mdc`).
- **Writes on SRs** — `post_service_request_note` only with user approval; block
  patch/release/dispatch tools on voice by default.
- **PII** — summarize transcripts; do not paste full caller phone numbers or
  names into Linear/memory unless asked.
- **Credentials** — never commit API keys; use `.env` and PolyAI Secrets Vault.
- **Linear routing** — PolyAI platform work routes to team **PolyAI**
  (`b9f464ef-b5c8-4f8c-9d19-de9cd6165af8`) when filing issues via
  `linear-issue-creator`.

## Reference files

| File | When to read |
| --- | --- |
| [reference/polyai-studio-mcp-setup.md](reference/polyai-studio-mcp-setup.md) | Mode A — Studio MCP wiring |
| [reference/vixxolink-voice-tool-pack.md](reference/vixxolink-voice-tool-pack.md) | Mode A — tool toggles and guardrails |
| [reference/polyai-api-cursor.md](reference/polyai-api-cursor.md) | Mode B — API families, URLs, auth |

## Related skills

- **`polyai`** — standalone PolyAI API, audit, Jupiter config (use this first)
- `polyai-conversation-audit` — alias for `polyai` audit mode

## Test phrases (new chat)

- "Use polyai-vixxo-bridge — P0 VixxoLink tools for outbound USP voice"
- "Use polyai-vixxo-bridge — Studio MCP setup for VixxoLink"
- "Use polyai — audit the best recent outbound call" (not this skill)
