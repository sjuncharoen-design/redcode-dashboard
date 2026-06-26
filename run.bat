@echo off
chcp 65001 >nul
echo ================================================
echo   fb_transcribe — เริ่มทำงาน
echo ================================================
echo.

if not exist ".env" (
    echo ❌ ไม่พบไฟล์ .env
    echo    รัน setup.bat ก่อน หรือสร้างไฟล์ .env เอง
    pause
    exit /b 1
)

python fb_transcribe.py
echo.
pause
