@echo off
setlocal EnableExtensions
set "PATH=%APPDATA%\npm;%PATH%"
npx -y @salesforce/mcp@latest --orgs DEFAULT_TARGET_ORG --toolsets orgs,metadata,data,users %*
