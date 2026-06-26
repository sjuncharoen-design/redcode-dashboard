@echo off
chcp 65001 >nul
echo ================================================
echo   ติดตั้ง fb_transcribe — กด Enter เพื่อเริ่ม
echo ================================================
pause

echo.
echo [1/4] ตรวจสอบ Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ไม่พบ Python — กรุณาติดตั้งที่ https://python.org
    echo   อย่าลืมติ๊ก "Add to PATH" ตอนติดตั้ง
    pause
    exit /b 1
)
python --version

echo.
echo [2/4] ติดตั้ง ffmpeg...
winget install --id Gyan.FFmpeg -e --silent
if errorlevel 1 (
    echo   ติดตั้ง ffmpeg ล้มเหลว — ลองรัน: winget install ffmpeg
)

echo.
echo [3/4] ติดตั้ง Python packages...
pip install yt-dlp faster-whisper google-generativeai -q
if errorlevel 1 (
    echo   ติดตั้ง packages ล้มเหลว
    pause
    exit /b 1
)

echo.
echo [4/4] ตรวจสอบไฟล์ .env...
if not exist ".env" (
    echo   ยังไม่มีไฟล์ .env — กำลังสร้างจาก .env.example...
    copy .env.example .env >nul
    echo   สร้างแล้ว! เปิดไฟล์ .env แล้วใส่ URL และ API Key ของคุณ
    notepad .env
) else (
    echo   พบไฟล์ .env แล้ว
)

echo.
echo ================================================
echo   ติดตั้งเสร็จแล้ว!
echo.
echo   ขั้นต่อไป:
echo   1. ใส่ FACEBOOK_VIDEO_URL และ GEMINI_API_KEY ใน .env
echo   2. เปิด Chrome → login Facebook → ปิด Chrome
echo   3. ดับเบิ้ลคลิก run.bat
echo ================================================
pause
