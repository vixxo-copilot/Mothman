@echo off
REM Clear stale mcp-remote listeners for business-objects (port 43212) and orphaned bo-universe proxies.
powershell -NoProfile -Command ^
  "$port=43212; $authId='9bc54f26569ad2e61b53aab68c19e22f'; Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host ('Killed stale OAuth listener PID ' + $_.OwningProcess) }; Get-CimInstance Win32_Process -Filter \"Name='node.exe'\" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*bo-universe*' -or ($_.CommandLine -like '*mcp-remote*' -and $_.CommandLine -like '*43212*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; Write-Host ('Killed stale mcp-remote PID ' + $_.ProcessId) }; Get-ChildItem -Path (Join-Path $env:USERPROFILE '.mcp-auth') -Recurse -Filter '*_lock.json' -ErrorAction SilentlyContinue | ForEach-Object { try { $j = Get-Content $_.FullName -Raw | ConvertFrom-Json; if ($j.port -eq $port) { Remove-Item $_.FullName -Force; Write-Host ('Removed lock ' + $_.Name) } } catch {} }; Get-ChildItem -Path (Join-Path $env:USERPROFILE '.mcp-auth') -Recurse -Filter ($authId + '*') -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item $_.FullName -Force; Write-Host ('Removed stale business-objects OAuth cache ' + $_.Name) }"
echo.
echo Port 43212 should be free.
echo business-objects now reuses the Gateway bearer token (no browser OAuth / userID prompt).
echo In Cursor: Settings -^> MCP -^> business-objects -^> toggle off, then on.
echo Requires a valid Gateway token in ~/.mcp-auth or ~/.vixxo/gateway_api_token.
