@echo off
echo ================================================
echo   Setup fb_transcribe
echo ================================================
echo.

echo [1/4] Checking Python...

REM Try python command first
python --version >nul 2>&1
if not errorlevel 1 goto python_ok

REM Try python3
python3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=python3
    goto python_ok
)

REM Try common install locations
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
) do (
    if exist %%P (
        set PYTHON=%%P
        echo   Found Python at: %%P
        goto python_ok
    )
)

echo   ERROR: Python not found in PATH or common locations.
echo   Please open Python installer and check "Add to PATH"
echo   or restart your computer after installing.
pause
exit /b 1

:python_ok
if not defined PYTHON set PYTHON=python
%PYTHON% --version
echo   OK

echo.
echo [2/4] Installing ffmpeg...
winget install --id Gyan.FFmpeg -e --silent 2>nul
if errorlevel 1 (
    winget install ffmpeg --silent 2>nul
)
echo   OK (if ffmpeg was missing, close and reopen CMD after this)

echo.
echo [3/4] Installing Python packages...
%PYTHON% -m pip install yt-dlp faster-whisper google-generativeai -q
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
