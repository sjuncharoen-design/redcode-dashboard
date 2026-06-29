@echo off
echo ================================================
echo   Prepare audio for free AI summary
echo ================================================
echo.

REM Find Python
set PYTHON=
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=python
    goto run
)
for %%P in (
    "%USERPROFILE%\anaconda3\python.exe"
    "%LOCALAPPDATA%\anaconda3\python.exe"
    "C:\ProgramData\Anaconda3\python.exe"
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
echo ERROR: Python not found
pause
exit /b 1

:run
%PYTHON% prep_audio.py
