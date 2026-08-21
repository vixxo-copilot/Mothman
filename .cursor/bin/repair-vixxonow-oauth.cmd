@echo off
REM Clear stale mcp-remote OAuth state for vixxonow (auth id bd3af626...).
REM vixxonow now uses the Gateway bearer wrapper — no browser OAuth needed.
powershell -NoProfile -Command ^
  "$authId='bd3af626f5128d032de269bd1f9de2be'; Get-ChildItem -Path (Join-Path $env:USERPROFILE '.mcp-auth') -Recurse -Filter ($authId + '*') -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item $_.FullName -Force; Write-Host ('Removed stale vixxonow OAuth cache ' + $_.Name) }; Get-ChildItem -Path (Join-Path $env:USERPROFILE '.mcp-auth') -Recurse -Filter '*_lock.json' -ErrorAction SilentlyContinue | ForEach-Object { try { $j = Get-Content $_.FullName -Raw | ConvertFrom-Json; if ($j.serverUrl -like '*vixxonow*' -or $j.hash -eq $authId) { Remove-Item $_.FullName -Force; Write-Host ('Removed lock ' + $_.Name) } } catch {} }; Get-CimInstance Win32_Process -Filter \"Name='node.exe'\" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*mcp-remote*' -and $_.CommandLine -like '*mcp/vixxonow*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; Write-Host ('Killed stale mcp-remote PID ' + $_.ProcessId) }"
echo.
echo Stale vixxonow OAuth cache cleared.
echo vixxonow now reuses the Gateway bearer token (no browser OAuth / localhost callback).
echo In Cursor: Settings -^> MCP -^> vixxonow -^> toggle off, then on.
echo Requires a valid Gateway token in ~/.mcp-auth or ~/.vixxo/gateway_api_token.
