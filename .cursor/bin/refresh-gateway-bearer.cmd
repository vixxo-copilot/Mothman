@echo off
REM One browser sign-in in this terminal (port 29069), then sync + mirror to VixxoLink.
setlocal EnableExtensions
set "PATH=%ProgramFiles%\nodejs;%APPDATA%\npm;%PATH%"

echo Gateway OAuth refresh (terminal only — not Cursor MCP UI).
echo.
python "%~dp0sync_gateway_token.py"
if not errorlevel 1 goto :done

echo sync_gateway_token failed — opening one-time Gateway sign-in...
python "%~dp0refresh_gateway_oauth.py"
if errorlevel 1 exit /b 1

:done
echo.
echo Restart gateway and vixxolink in Cursor Settings -^> MCP.
