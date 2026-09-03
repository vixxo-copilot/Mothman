@echo off
REM Clear stale mcp-remote OAuth callback on port 37882 (legacy OAuth path).
powershell -NoProfile -Command ^
  "$port=37882; Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host ('Killed stale OAuth listener PID ' + $_.OwningProcess) }; Get-ChildItem -Path (Join-Path $env:USERPROFILE '.mcp-auth') -Recurse -Filter '*_lock.json' -ErrorAction SilentlyContinue | ForEach-Object { try { $j = Get-Content $_.FullName -Raw | ConvertFrom-Json; if ($j.port -eq $port) { Remove-Item $_.FullName -Force; Write-Host ('Removed lock ' + $_.Name) } } catch {} }"
echo.
echo Port 37882 should be free.
echo vixxolink reuses the Gateway bearer (gateway_api_token).
echo Run: python .cursor\bin\sync_gateway_token.py
echo Then restart vixxolink in Cursor Settings -^> MCP.
