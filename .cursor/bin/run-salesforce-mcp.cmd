@echo off
setlocal EnableExtensions

set "PATH=%APPDATA%\npm;%PATH%"
set "ROOT=%~dp0salesforce-mcp"
set "ENTRY=%ROOT%\node_modules\@salesforce\mcp\bin\run.js"

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

where sf >nul 2>&1
if errorlevel 1 (
  echo Salesforce MCP: sf CLI not found. Run: npm install -g @salesforce/cli ^&^& sf org login web >&2
  exit /b 1
)

"C:\Program Files\nodejs\node.exe" "%ENTRY%" --orgs DEFAULT_TARGET_ORG --toolsets orgs,metadata,data,users %*
