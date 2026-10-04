@echo off
setlocal
cd /d "%~dp0"
echo Memulai Prompt Action...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\portable_launch.ps1" -Root "%~dp0"
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" (
  echo.
  echo Prompt Action gagal dimulai dengan normal.
  echo Laporan launcher: runtime\logs\portable-launch-status.txt
  echo Laporan self-check: runtime\logs\portable-self-check.txt
  echo.
  echo Jika perlu dikirim untuk pemeriksaan, jalankan Buat Paket Diagnostik.bat.
  pause
)
exit /b %EXITCODE%
