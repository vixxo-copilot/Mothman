@echo off
setlocal EnableExtensions
set "LOCAL=%~dp0ms365-mcp\node_modules\@softeria\ms-365-mcp-server\dist\index.js"
if exist "%LOCAL%" (
  "C:\Program Files\nodejs\node.exe" "%LOCAL%" --org-mode %*
) else (
  npx -y @softeria/ms-365-mcp-server@latest --org-mode %*
)
