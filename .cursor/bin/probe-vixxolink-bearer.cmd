@echo off
REM Silent VixxoLink bearer probe (Task Scheduler / pre-login). No browser.
setlocal EnableExtensions
set "PATH=%ProgramFiles%\nodejs;%APPDATA%\npm;%PATH%"
cd /d "%~dp0..\.."
python ".agents\skills\vixxo-mcp-bearer-fix\scripts\probe_vixxolink_bearer.py" --silent-refresh --write-tmp --json
exit /b %ERRORLEVEL%
