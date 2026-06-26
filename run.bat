@echo off
echo ================================================
echo   fb_transcribe - Starting...
echo ================================================
echo.

if not exist ".env" (
    echo ERROR: .env file not found.
    echo Please run setup.bat first.
    pause
    exit /b 1
)

python fb_transcribe.py
echo.
pause
