# fb_transcribe — Facebook Video → Transcript + สรุปหุ้น

ดาวน์โหลดวีดีโอ Facebook → ถอด transcript → สรุปด้วย Gemini AI

---

## ใช้ครั้งแรก (ทำแค่ครั้งเดียว)

### 1. ติดตั้ง Python
- ดาวน์โหลดที่ https://python.org → กด **Download Python**
- ติดตั้ง → **ติ๊ก "Add to PATH"** ด้วย (สำคัญ)

### 2. ขอ Gemini API Key ฟรี
- ไปที่ https://aistudio.google.com/app/apikey
- กด **"Create API key in new project"**
- คัดลอก key ไว้

### 3. รัน setup.bat
- ดับเบิ้ลคลิกไฟล์ **setup.bat**
- รอจนเสร็จ จะเปิด Notepad ให้ใส่ค่า

### 4. ใส่ค่าใน .env
```
FACEBOOK_VIDEO_URL=https://www.facebook.com/groups/XXXX/posts/XXXX
GEMINI_API_KEY=AIzaSy...ใส่ key ของคุณ
```
บันทึกไฟล์แล้วปิด Notepad

---

## ใช้งานทุกครั้ง

1. เปิด **Chrome** → login Facebook → **ปิด Chrome ทุกหน้าต่าง**
2. แก้ `FACEBOOK_VIDEO_URL` ใน `.env` ให้เป็น URL วีดีโอที่ต้องการ
3. ดับเบิ้ลคลิก **run.bat**
4. รอ 10-15 นาที (วีดีโอ 2-3 ชม.)

---

## ผลลัพธ์

| ไฟล์ | เนื้อหา |
|---|---|
| `fb_output\transcript.txt` | คำพูดทั้งหมด |
| `fb_output\summary.md` | สรุปหุ้น ตัวเลข มุมมอง action items |

---

## ปรับแต่ง

ใน `.env` เพิ่มได้:
```
WHISPER_MODEL=medium   # medium แม่นยำกว่า small แต่ช้ากว่า
OUTPUT_DIR=my_output   # เปลี่ยนโฟลเดอร์ output
```

---

## แก้ปัญหาที่พบบ่อย

**Download failed / ไม่ได้รับอนุญาต**
→ เปิด Chrome → login Facebook → ปิด Chrome ทุกหน้าต่าง → รันใหม่

**ไม่เจอ ffmpeg**
→ เปิด Command Prompt พิมพ์ `winget install ffmpeg` แล้วปิด-เปิด CMD ใหม่

**pip install error**
→ รัน `python -m pip install --upgrade pip` แล้วลองใหม่
