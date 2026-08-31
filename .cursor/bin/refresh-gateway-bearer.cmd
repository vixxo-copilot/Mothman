@echo off
REM One-time Gateway browser sign-in when ~/.vixxo/gateway_api_token is missing or expired.
setlocal EnableExtensions
set "PATH=%ProgramFiles%\nodejs;%APPDATA%\npm;%PATH%"

call "%~dp0repair-gateway-oauth.cmd"
echo.
echo Gateway bearer token is missing or expired. Browser sign-in is required ONCE.
echo 1) Complete the Vixxo login in the browser tab that opens.
echo 2) When mcp-remote shows connected, press Ctrl+C in this window.
echo 3) This script will sync the new token and exit.
echo.
npx -y mcp-remote https://vixxonow.com/mcp/gateway
echo.
python "%~dp0sync_gateway_token.py"
if errorlevel 1 (
  echo sync_gateway_token failed — complete sign-in above, then run:
  echo   python .cursor\bin\sync_gateway_token.py
  exit /b 1
)
echo.
echo Gateway token refreshed. Restart gateway, business-objects, powerbi-prod, and vixxonow in Cursor Settings -^> MCP.
