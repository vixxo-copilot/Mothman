@echo off
REM Clear stale mcp-remote processes for Power BI (Gateway bearer wrapper; no browser OAuth).
powershell -NoProfile -Command ^
  "Get-CimInstance Win32_Process -Filter \"Name='node.exe'\" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*mcp-remote*' -and $_.CommandLine -like '*mcp/powerbi*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; Write-Host ('Killed stale mcp-remote PID ' + $_.ProcessId) }"
echo.
echo Stale Power BI mcp-remote processes cleared.
echo powerbi-prod uses Gateway bearer via run-powerbi-mcp.cmd (no browser OAuth).
echo If MCP still fails: python .cursor\bin\sync_gateway_token.py
echo Then restart powerbi-prod in Cursor Settings -^> MCP.
