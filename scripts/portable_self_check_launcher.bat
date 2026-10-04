@echo off
setlocal
cd /d "%~dp0"
echo Prompt Action - Pemeriksaan Portable
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\portable_self_check.ps1" -Root "%~dp0" -SmokeTest
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
