@echo off
REM Fix VixxoLink + VixxoNow MCPs: clear stale OAuth, sync Gateway, refresh VixxoLink bearer.
setlocal EnableExtensions
set "PATH=%ProgramFiles%\nodejs;%APPDATA%\npm;%PATH%"
cd /d "%~dp0..\.."

echo === Step 1: Clear stale OAuth ===
call "%~dp0clear-vixxo-stale-mcp-auths.cmd"
if errorlevel 1 exit /b 1

echo.
echo === Step 2: Sync Gateway bearer (vixxonow + gateway family) ===
python "%~dp0sync_gateway_token.py"
if errorlevel 1 (
  echo Gateway sync failed — run: .cursor\bin\refresh-gateway-bearer.cmd
  exit /b 1
)

echo.
echo === Step 3: VixxoLink probe (silent refresh, then Chrome if needed) ===
python ".agents\skills\vixxo-mcp-bearer-fix\scripts\probe_vixxolink_bearer.py" --silent-refresh --prompt-oauth --write-tmp --json
if errorlevel 1 (
  echo VixxoLink probe failed — run: .cursor\bin\refresh-vixxolink-bearer.cmd
  exit /b 1
)

echo.
echo === OK ===
echo Fully quit Cursor, reopen, then toggle vixxolink and vixxonow in Settings -^> MCP.
