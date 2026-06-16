@echo off
setlocal EnableExtensions

set "ROOT=%~dp0..\.."
set "BIN=%~dp0github-mcp-server.exe"

if not exist "%BIN%" (
  echo github-mcp-server binary missing at %BIN% >&2
  echo Download: https://github.com/github/github-mcp-server/releases/latest >&2
  exit /b 1
)

if "%GITHUB_PERSONAL_ACCESS_TOKEN%"=="" (
  for /f "usebackq delims=" %%T in (`gh auth token 2^>nul`) do set "GITHUB_PERSONAL_ACCESS_TOKEN=%%T"
)

if "%GITHUB_PERSONAL_ACCESS_TOKEN%"=="" (
  echo GitHub MCP: set GITHUB_PERSONAL_ACCESS_TOKEN or run 'gh auth login' >&2
  exit /b 1
)

"%BIN%" stdio %*
