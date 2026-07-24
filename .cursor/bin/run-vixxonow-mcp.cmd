@echo off
setlocal EnableExtensions
set "PATH=%ProgramFiles%\nodejs;%APPDATA%\npm;%PATH%"
python "%~dp0run-vixxonow-mcp.py" %*
