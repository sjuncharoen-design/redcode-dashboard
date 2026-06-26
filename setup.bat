@echo off
echo ================================================
echo   Setup fb_transcribe
echo ================================================
echo.

echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python not found.
    echo   Please install from https://python.org
    echo   Make sure to check "Add to PATH" during install.
    pause
    exit /b 1
)
python --version
echo   OK

echo.
echo [2/4] Installing ffmpeg...
winget install --id Gyan.FFmpeg -e --silent
if errorlevel 1 (
    echo   WARNING: ffmpeg install may have failed.
    echo   Try manually: winget install ffmpeg
)
echo   OK

echo.
echo [3/4] Installing Python packages...
pip install yt-dlp faster-whisper google-generativeai -q
if errorlevel 1 (
    echo   ERROR: pip install failed.
    pause
    exit /b 1
)
echo   OK

echo.
echo [4/4] Setting up .env file...
if not exist ".env" (
    copy .env.example .env >nul
    echo   Created .env - Opening for you to fill in...
    echo   Please set FACEBOOK_VIDEO_URL and GEMINI_API_KEY
    notepad .env
) else (
    echo   .env already exists - OK
)

echo.
echo ================================================
echo   Setup complete!
echo.
echo   Next steps:
echo   1. Fill in FACEBOOK_VIDEO_URL and GEMINI_API_KEY in .env
echo   2. Open Chrome, login to Facebook, then CLOSE Chrome
echo   3. Double-click run.bat
echo ================================================
pause
