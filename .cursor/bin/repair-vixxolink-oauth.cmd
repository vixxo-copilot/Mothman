@echo off
REM Clear stale mcp-remote OAuth callback on port 37882 (Cursor vixxolink MCP).
powershell -NoProfile -Command ^
  "$port=37882; Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host ('Killed stale OAuth listener PID ' + $_.OwningProcess) }; Get-ChildItem -Path (Join-Path $env:USERPROFILE '.mcp-auth') -Recurse -Filter '*_lock.json' -ErrorAction SilentlyContinue | ForEach-Object { try { $j = Get-Content $_.FullName -Raw | ConvertFrom-Json; if ($j.port -eq $port) { Remove-Item $_.FullName -Force; Write-Host ('Removed lock ' + $_.Name) } } catch {} }"
echo.
echo Port 37882 should be free. In Cursor: Settings -^> MCP -^> vixxolink -^> Reconnect.
echo Complete the browser OAuth sign-in when prompted.
