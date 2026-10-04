@echo off
setlocal

set "HERE=%~dp0"
set "CHECK=%HERE%scripts\portable_self_check.ps1"
set "ROOT=%HERE%"

if not exist "%CHECK%" (
  set "CHECK=%HERE%portable_self_check.ps1"
  set "ROOT=%HERE%.."
)

cd /d "%ROOT%"
echo Prompt Action - Pemeriksaan Portable
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%CHECK%" -Root "%ROOT%" -SmokeTest
set "EXITCODE=%ERRORLEVEL%"
echo.
if "%EXITCODE%"=="0" (
  echo HASIL: PASS
) else (
  echo HASIL: FAIL
)
echo Laporan: runtime\logs\portable-self-check.txt
echo.
pause
exit /b %EXITCODE%
