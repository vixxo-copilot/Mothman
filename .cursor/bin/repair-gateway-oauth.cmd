@echo off
REM Clear stale mcp-remote OAuth callback on port 29069 (Gateway bearer wrapper).
powershell -NoProfile -Command ^
  "$port=29069; Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host ('Killed stale OAuth listener PID ' + $_.OwningProcess) }; Get-ChildItem -Path (Join-Path $env:USERPROFILE '.mcp-auth') -Recurse -Filter '*_lock.json' -ErrorAction SilentlyContinue | ForEach-Object { try { $j = Get-Content $_.FullName -Raw | ConvertFrom-Json; if ($j.port -eq $port) { Remove-Item $_.FullName -Force; Write-Host ('Removed lock ' + $_.Name) } } catch {} }"
echo.
python "%~dp0sync_gateway_token.py"
echo.
echo Port 29069 should be free.
echo Gateway uses bearer auth via run-gateway-mcp.cmd (no browser OAuth in Cursor).
echo Do not click Connect on gateway. Restart the gateway MCP after this repair.
