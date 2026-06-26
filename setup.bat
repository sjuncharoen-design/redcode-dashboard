@echo off
echo ================================================
echo   Setup fb_transcribe
echo ================================================
echo.

echo [1/4] Checking Python...

set PYTHON=

REM Try python in PATH first
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=python
    goto python_ok
)

REM Search Anaconda / Miniconda locations
for %%P in (
    "%USERPROFILE%\anaconda3\python.exe"
    "%USERPROFILE%\Anaconda3\python.exe"
    "%USERPROFILE%\miniconda3\python.exe"
    "%USERPROFILE%\Miniconda3\python.exe"
    "%LOCALAPPDATA%\anaconda3\python.exe"
    "%LOCALAPPDATA%\Anaconda3\python.exe"
    "%LOCALAPPDATA%\miniconda3\python.exe"
    "C:\anaconda3\python.exe"
    "C:\Anaconda3\python.exe"
    "C:\ProgramData\Anaconda3\python.exe"
    "C:\ProgramData\anaconda3\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
) do (
    if exist %%P (
        set PYTHON=%%P
        echo   Found at: %%P
        goto python_ok
    )
)

echo   ERROR: Python not found.
echo   Try running from "Anaconda Prompt" instead of CMD.
pause
exit /b 1

:python_ok
%PYTHON% --version
echo   OK

echo.
echo [2/4] Installing ffmpeg...
winget install --id Gyan.FFmpeg -e --silent 2>nul
echo   Done (ignore warnings above)

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
    echo   Created .env - Opening Notepad to fill in values...
    notepad .env
) else (
    echo   .env already exists - OK
)

echo.
echo ================================================
echo   Setup complete!
echo   Next: fill .env then double-click run.bat
echo ================================================
pause
