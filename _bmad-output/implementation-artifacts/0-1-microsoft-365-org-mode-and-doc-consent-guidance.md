# Story 0.1: Enable Microsoft 365 org mode and document consent flow

Status: ready-for-dev

## Story

As a Vixxo employee using the assistants template,
I want the Microsoft 365 MCP server to run with org mode enabled and clearly documented onboarding steps,
so that Teams, SharePoint, and shared-mailbox capabilities are available after a predictable restart and re-auth flow.

## Acceptance Criteria

1. `.cursor/mcp.json` keeps the existing `microsoft-365` server key and package, and adds `"--org-mode"` to the args list after `@softeria/ms-365-mcp-server@latest`.
2. `.cursor/mcp.README.md`, `docs/setup.md`, and `docs/mcps.md` explicitly document the org-mode enablement impact and the required restart + re-login flow.
3. Documentation calls out likely consent prompts for `Chat.ReadWrite`, `ChannelMessage.*`, `Sites.Read.All`, and `User.Read.All`, with language that some scopes may require tenant admin approval.
4. Story tasks include a validation checklist confirming config shape, updated documentation consistency, and a clear next-step path when consent is blocked by tenant policy.

## Tasks / Subtasks

- [ ] Update Microsoft 365 MCP config requirements in `.cursor/mcp.json` (AC: 1)
  - [ ] Ensure key remains `microsoft-365`, command remains `npx`, and existing package reference is preserved.
  - [ ] Add `"--org-mode"` to the args array without changing unrelated MCP entries.
- [ ] Update M365 operational guidance in `.cursor/mcp.README.md` (AC: 2, 3)
  - [ ] Document why org mode is enabled and what new tool surface it unlocks.
  - [ ] Document restart/re-login and Graph scope consent expectations.
- [ ] Update onboarding docs in `docs/setup.md` and `docs/mcps.md` (AC: 2, 3)
  - [ ] Add restart/re-login steps after config change.
  - [ ] Add admin-approval caveat and escalation guidance when consent is denied.
- [ ] Validate consistency and scope boundaries (AC: 4)
  - [ ] Confirm all three docs use aligned wording for scopes and approval caveats.
  - [ ] Confirm change remains config+docs only (no unrelated MCP or wizard behavior edits).

## Dev Notes

- Current baseline: `.cursor/mcp.json` has the `microsoft-365` server without `--org-mode`.
- Existing docs describe device-code auth but do not fully spell out org-mode scope consent and admin-approval implications.
- This story is intentionally scoped to config + documentation updates only; no new MCP servers or credential variable expansions are part of this work.

### Project Structure Notes

- Config change location: `.cursor/mcp.json`.
- Documentation updates: `.cursor/mcp.README.md`, `docs/setup.md`, `docs/mcps.md`.
- Tracking keys must stay aligned with sprint status key `0-1-microsoft-365-org-mode-and-doc-consent-guidance`.

### References

- `_bmad-output/planning-artifacts/epics.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `.cursor/mcp.json`
- `.cursor/mcp.README.md`
- `docs/setup.md`
- `docs/mcps.md`

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
