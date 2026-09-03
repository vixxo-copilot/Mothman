@echo off
REM One-time VixxoLink browser sign-in when the cached bearer is rejected.
setlocal EnableExtensions
set "PATH=%ProgramFiles%\nodejs;%APPDATA%\npm;%PATH%"

call "%~dp0repair-vixxolink-oauth.cmd"
echo.
python "%~dp0refresh_vixxolink_oauth.py"
if errorlevel 1 (
  echo refresh_vixxolink_oauth failed — complete Chrome sign-in, then retry.
  exit /b 1
)
echo.
echo VixxoLink token refreshed. Fully quit Cursor, reopen, then restart vixxolink in Settings -^> MCP.
