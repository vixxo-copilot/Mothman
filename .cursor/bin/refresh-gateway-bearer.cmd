@echo off
REM Gateway no longer starts browser OAuth: initialize is unauthenticated.
REM A present ~/.vixxo/gateway_api_token is enough; restart the MCP after sync.
setlocal EnableExtensions
set "PATH=%ProgramFiles%\nodejs;%APPDATA%\npm;%PATH%"

echo Gateway will not open a login tab.
echo mcp-remote connects without auth; the browser flow never starts.
echo Syncing the existing token file, then you can restart the MCPs.
echo.
python "%~dp0sync_gateway_token.py"
if errorlevel 1 (
  echo No Gateway token on disk. Ask platform for a new CGAGNER bearer
  echo and save it to %%USERPROFILE%%\.vixxo\gateway_api_token
  exit /b 1
)
echo.
echo Restart gateway, business-objects, powerbi-prod, and vixxonow in Cursor Settings -^> MCP.
