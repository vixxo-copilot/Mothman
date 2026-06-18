@echo off
setlocal EnableExtensions
set "PATH=%APPDATA%\npm;C:\Program Files\nodejs;%PATH%"
npx %*
