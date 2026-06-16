# Flight Search — Setup (fli MCP)

This skill requires the `fli` MCP (Google Flights). It hits Google Flights'
unofficial API directly — treat it as a personal-use tool, not a production
dependency.

## 1. Install the package

`fli` ships the MCP server, a CLI, and a Python library. Install with the `mcp`
extra so the server has its dependencies:

```bash
# Recommended: isolated install via pipx
pipx install "flights[mcp]"

# If you don't have pipx:
brew install pipx && pipx ensurepath
```

This installs three commands: `fli` (CLI), `fli-mcp` (stdio server),
`fli-mcp-http` (HTTP server). Find the server path with:

```bash
which fli-mcp     # e.g. /Users/<you>/.local/bin/fli-mcp
```

## 2. Register the MCP in Cursor

Add an entry to your user-level config at `~/.cursor/mcp.json` (or a project's
`.cursor/mcp.json`). Use the absolute path from `which fli-mcp`:

```json
{
  "mcpServers": {
    "fli": {
      "command": "/Users/<you>/.local/bin/fli-mcp"
    }
  }
}
```

## 3. Activate

Open Cursor Settings → MCP (or reload the window) and confirm `fli` shows up and
is enabled. MCP servers load per session, so the tools appear in your next chat.

## 4. Verify

Quick CLI smoke test (proves the data layer works):

```bash
fli flights JFK LAX 2026-07-15 --stops NON_STOP
```

You should see a list of flight options. In chat, you can then ask the agent to
find flights and it will use the `fli` MCP tools (`find_airports`,
`search_flights`, `search_dates`).

## Troubleshooting

- **"MCP dependencies are not installed"** when running `fli-mcp`: you installed
  `flights` without the `mcp` extra. Reinstall: `pipx install --force "flights[mcp]"`
  (or `pipx uninstall flights && pipx install "flights[mcp]"`).
- **Tools don't appear in chat**: reload the Cursor window; MCP config is read at
  session start.
- **`--format json` schema looks different**: it's marked experimental upstream
  and may change.
