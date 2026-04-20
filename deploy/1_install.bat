@echo off
:: ============================================================
:: Jerry - Powertech Tools  |  Service Installer
:: Run once as Administrator to register Jerry as a Windows
:: Service that starts automatically and survives reboots.
::
:: Requires: NSSM  https://nssm.cc/download
::   - Download nssm.exe and place it in C:\tools\ or anywhere on PATH
:: ============================================================
setlocal

set SERVICE=Jerry-Powertech
set APP_DIR=%~dp0..
set UVICORN=%APP_DIR%\.venv\Scripts\uvicorn.exe
set LOG_DIR=%APP_DIR%\logs
set PORT=8000

:: Create logs folder
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo Installing service "%SERVICE%"...
nssm install %SERVICE% "%UVICORN%" "api.main:app --host 0.0.0.0 --port %PORT%"
nssm set %SERVICE% AppDirectory        "%APP_DIR%"
nssm set %SERVICE% AppStdout           "%LOG_DIR%\jerry.log"
nssm set %SERVICE% AppStderr           "%LOG_DIR%\jerry-error.log"
nssm set %SERVICE% AppRotateFiles      1
nssm set %SERVICE% AppRotateOnline     1
nssm set %SERVICE% AppRotateBytes      10485760
nssm set %SERVICE% AppRestartDelay     3000
nssm set %SERVICE% Start               SERVICE_AUTO_START
nssm set %SERVICE% DisplayName         "Jerry - Powertech Analysis Tools"
nssm set %SERVICE% Description         "FastAPI backend serving the Jerry web app on port %PORT%"

nssm start %SERVICE%
echo.
echo Done. Jerry is running at http://localhost:%PORT%
echo Use manage.bat to control the service.
pause
