@echo off
setlocal
cd /d "%~dp0"

set "SCRIPT=%~dp0portable_collect_diagnostics.ps1"
if not exist "%SCRIPT%" set "SCRIPT=%~dp0scripts\portable_collect_diagnostics.ps1"

echo Prompt Action - Buat Paket Diagnostik
echo.
if not exist "%SCRIPT%" (
  echo GAGAL: portable_collect_diagnostics.ps1 tidak ditemukan.
  echo.
  pause
  exit /b 2
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" -Root "%~dp0"
set "EXITCODE=%ERRORLEVEL%"
echo.
if "%EXITCODE%"=="0" (
  echo HASIL: SELESAI
  echo Paket ada di folder runtime\diagnostics
  echo Kirim ZIP diagnostik jika perlu pemeriksaan bug.
) else (
  echo HASIL: GAGAL ^(kode %EXITCODE%^\)
)
echo.
pause
exit /b %EXITCODE%
