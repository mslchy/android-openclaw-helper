@echo off
chcp 65001 >nul
echo ========================================
echo   SSH Tunnel Cleanup Tool
echo ========================================
echo.

echo Checking for SSH tunnel processes...
echo.

REM Find SSH processes listening on our ports
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "18789 18791 18792 8080" ^| findstr "LISTENING"') do (
    echo Killing process: %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo [DONE] Tunnel cleanup completed
echo.
pause
