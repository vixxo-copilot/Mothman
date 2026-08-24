@echo off
setlocal EnableExtensions

set "PATH=%ProgramFiles%\nodejs;%APPDATA%\npm;%PATH%"
set "ROOT=%~dp0salesforce-mcp"
set "ENTRY=%ROOT%\node_modules\@salesforce\mcp\bin\run.js"
set "SF=%APPDATA%\npm\sf.cmd"

if not exist "%ENTRY%" (
  echo Salesforce MCP: installing vendored @salesforce/mcp... >&2
  pushd "%ROOT%"
  call npm install --no-fund --no-audit
  if errorlevel 1 (
    echo Salesforce MCP: npm install failed in %ROOT% >&2
    popd
    exit /b 1
  )
  popd
)

if not exist "%SF%" (
  echo Salesforce MCP: sf CLI not found at %SF% >&2
  echo Run: npm install -g @salesforce/cli ^&^& sf org login web >&2
  exit /b 1
)

set "NODE=%ProgramFiles%\nodejs\node.exe"
if not exist "%NODE%" (
  for /f "delims=" %%N in ('where node 2^>nul') do set "NODE=%%N" & goto :have_node
  echo Salesforce MCP: node.exe not found. Install Node.js from https://nodejs.org/ >&2
  exit /b 1
)
:have_node

"%NODE%" "%ENTRY%" --orgs DEFAULT_TARGET_ORG --toolsets orgs,metadata,data,users %*
