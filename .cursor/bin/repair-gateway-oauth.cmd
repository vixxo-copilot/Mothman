@echo off
REM Clear stale mcp-remote OAuth callback on port 29069 (Cursor gateway MCP).
powershell -NoProfile -Command ^
  "$port=29069; $authId='6486a04241e2b8e809e7c6f312812185'; Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host ('Killed stale OAuth listener PID ' + $_.OwningProcess) }; Get-ChildItem -Path (Join-Path $env:USERPROFILE '.mcp-auth') -Recurse -Filter '*_lock.json' -ErrorAction SilentlyContinue | ForEach-Object { try { $j = Get-Content $_.FullName -Raw | ConvertFrom-Json; if ($j.port -eq $port) { Remove-Item $_.FullName -Force; Write-Host ('Removed lock ' + $_.Name) } } catch {} }; Get-ChildItem -Path (Join-Path $env:USERPROFILE '.mcp-auth') -Recurse -Filter ($authId + '*') -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item $_.FullName -Force; Write-Host ('Removed stale gateway OAuth cache ' + $_.Name) }"
echo.
echo Port 29069 should be free. In Cursor: Settings -^> MCP -^> gateway -^> Reconnect.
echo Complete the browser OAuth sign-in when prompted.
echo.
echo Prefer bearer auth (no localhost callback): add an Authorization Bearer header to gateway mcp-remote args in .cursor/mcp.json.
echo Token: ~/.vixxo/gateway_api_token or cached ~/.mcp-auth token.
