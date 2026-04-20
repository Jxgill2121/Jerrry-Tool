@echo off
:: ============================================================
:: Jerry - Powertech Tools  |  Service Manager
::
:: Usage:
::   manage.bat status    - Is Jerry running?
::   manage.bat start     - Start Jerry
::   manage.bat stop      - Stop Jerry
::   manage.bat restart   - Restart Jerry (after a code update)
::   manage.bat logs      - Live tail of application logs
::   manage.bat errors    - Live tail of error log
::   manage.bat update    - git pull + rebuild frontend + restart
:: ============================================================
setlocal
set SERVICE=Jerry-Powertech
set APP_DIR=%~dp0..
set LOG_DIR=%APP_DIR%\logs

if "%1"==""        goto :usage
if "%1"=="status"  goto :status
if "%1"=="start"   goto :start
if "%1"=="stop"    goto :stop
if "%1"=="restart" goto :restart
if "%1"=="logs"    goto :logs
if "%1"=="errors"  goto :errors
if "%1"=="update"  goto :update
goto :usage

:status
  echo.
  nssm status %SERVICE%
  echo.
  echo --- Last 20 log lines ---
  powershell -Command "if (Test-Path '%LOG_DIR%\jerry.log') { Get-Content '%LOG_DIR%\jerry.log' -Tail 20 } else { Write-Host 'No log file yet.' }"
  goto :done

:start
  nssm start %SERVICE%
  echo Jerry started.
  goto :done

:stop
  nssm stop %SERVICE%
  echo Jerry stopped.
  goto :done

:restart
  nssm restart %SERVICE%
  echo Jerry restarted.
  goto :done

:logs
  echo Tailing logs (Ctrl+C to stop)...
  powershell -Command "Get-Content '%LOG_DIR%\jerry.log' -Wait -Tail 40"
  goto :done

:errors
  echo Tailing error log (Ctrl+C to stop)...
  powershell -Command "Get-Content '%LOG_DIR%\jerry-error.log' -Wait -Tail 40"
  goto :done

:update
  echo Pulling latest code...
  cd /d "%APP_DIR%"
  git pull origin claude/convert-to-webapp-BR383
  echo.
  echo Rebuilding frontend...
  cd /d "%APP_DIR%\frontend"
  call npm install
  call npm run build
  echo.
  echo Restarting service...
  nssm restart %SERVICE%
  echo.
  echo Update complete. Jerry is running the latest version.
  goto :done

:usage
  echo.
  echo  Usage: manage.bat [status^|start^|stop^|restart^|logs^|errors^|update]
  echo.
  echo    status   - Show if Jerry is running + recent log lines
  echo    start    - Start the service
  echo    stop     - Stop the service
  echo    restart  - Restart (use after code changes)
  echo    logs     - Live tail of the main log
  echo    errors   - Live tail of the error log
  echo    update   - Pull latest code, rebuild UI, restart
  echo.

:done
