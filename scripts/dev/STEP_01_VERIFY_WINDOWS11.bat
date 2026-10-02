@echo off
setlocal
cd /d "%~dp0\..\.."

echo ============================================================
echo Prompt Action - STEP 01 Windows 11 Verification
echo ============================================================
echo.
echo IMPORTANT:
echo - Run this file normally.
echo - DO NOT choose "Run as administrator".
echo - The verifier must run on Windows 11.
echo.

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0verify_step01_windows11.ps1"
set "RC=%ERRORLEVEL%"

if "%RC%"=="0" (
    echo.
    echo STEP 01 verification PASSED.
    echo Evidence folder will open now.
    if exist "%CD%\evidence\step01\STEP01_WINDOWS11_LOCAL_EVIDENCE.zip" (
        start "" "%CD%\evidence\step01"
    )
) else (
    echo.
    echo STEP 01 verification FAILED or is still BLOCKED.
    echo Read the error above, fix it, then run this BAT again normally.
)

echo.
pause
exit /b %RC%
