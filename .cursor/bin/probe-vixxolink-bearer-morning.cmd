@echo off
REM Morning / interactive: silent refresh, then Chrome sign-in if still invalid.
setlocal EnableExtensions
set "PATH=%ProgramFiles%\nodejs;%APPDATA%\npm;%PATH%"
cd /d "%~dp0..\.."
python ".agents\skills\vixxo-mcp-bearer-fix\scripts\probe_vixxolink_bearer.py" --silent-refresh --prompt-oauth --write-tmp --json
exit /b %ERRORLEVEL%
