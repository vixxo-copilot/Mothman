@echo off
REM Clear stale mcp-remote OAuth listeners, locks, and node PIDs for Vixxo HTTP MCPs.
setlocal EnableExtensions
set "PATH=%ProgramFiles%\nodejs;%APPDATA%\npm;%PATH%"

echo === Clearing stale Vixxo MCP OAuth state ===
call "%~dp0repair-gateway-oauth.cmd"
call "%~dp0repair-vixxolink-oauth.cmd"
call "%~dp0repair-vixxonow-oauth.cmd"
call "%~dp0repair-business-objects-oauth.cmd"
call "%~dp0repair-powerbi-oauth.cmd"
echo.
echo Done. Stale OAuth cleared for gateway, vixxolink, vixxonow, business-objects, powerbi.
echo Next: .cursor\bin\fix-vixxolink-vixxonow-mcps.cmd  (sync tokens + VixxoLink sign-in if needed)
