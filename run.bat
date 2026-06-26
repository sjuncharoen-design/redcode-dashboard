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

REM Find Python
set PYTHON=

python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=python
    goto run
)

for %%P in (
    "%USERPROFILE%\anaconda3\python.exe"
    "%USERPROFILE%\Anaconda3\python.exe"
    "%USERPROFILE%\miniconda3\python.exe"
    "%USERPROFILE%\Miniconda3\python.exe"
    "%LOCALAPPDATA%\anaconda3\python.exe"
    "%LOCALAPPDATA%\Anaconda3\python.exe"
    "C:\ProgramData\Anaconda3\python.exe"
    "C:\anaconda3\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
) do (
    if exist %%P (
        set PYTHON=%%P
        goto run
    )
)

echo ERROR: Python not found.
echo Use Anaconda Prompt instead: run "python fb_transcribe.py"
pause
exit /b 1

:run
echo Using: %PYTHON%
%PYTHON% fb_transcribe.py
echo.
pause
