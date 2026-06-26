# fb_transcribe — Facebook Video → Transcript + สรุปหุ้น

วีดีโอ Facebook → ถอด transcript → สรุปด้วย Gemini AI

> **สำคัญ:** การโหลดวีดีโอจากกลุ่มปิดอัตโนมัติ (yt-dlp) มักไม่สำเร็จ
> วิธีที่ชัวร์ที่สุดคือ **โหลดวีดีโอเองด้วย extension แล้ววางไฟล์ไว้ในโฟลเดอร์**
> จากนั้น script จะถอดเสียง + สรุปให้

---

## ใช้ครั้งแรก (ทำแค่ครั้งเดียว)

### 1. ติดตั้ง Python
- ดาวน์โหลดที่ https://python.org → กด **Download Python**
- ติดตั้ง → **ติ๊ก "Add to PATH"** ด้วย (สำคัญ)

### 2. ขอ Gemini API Key ฟรี
- ไปที่ https://aistudio.google.com/app/apikey
- กด **"Create API key in new project"** → คัดลอก key ไว้

### 3. รัน setup.bat
- ดับเบิ้ลคลิก **setup.bat** → รอจนเสร็จ จะเปิด Notepad
- ใส่ `GEMINI_API_KEY=...` แล้วบันทึก

### 4. ติดตั้ง extension โหลดวีดีโอ (ใน Chrome)
- ติดตั้ง **"Video DownloadHelper"** จาก Chrome Web Store

---

## ใช้งานทุกครั้ง

1. เปิดวีดีโอใน Facebook → กดเล่นสัก 2-3 วินาที
2. กด icon **Video DownloadHelper** → ดาวน์โหลดไฟล์ `.mp4`
3. **ย้ายไฟล์ `.mp4` มาวางในโฟลเดอร์เดียวกับ `run.bat`**
4. ดับเบิ้ลคลิก **run.bat**
5. รอ 10-15 นาที (วีดีโอ 2-3 ชม.)

> script จะหาไฟล์วีดีโอในโฟลเดอร์ให้อัตโนมัติ ไม่ต้องตั้งค่าอะไรเพิ่ม

---

## ผลลัพธ์

| ไฟล์ | เนื้อหา |
|---|---|
| `fb_output\transcript.txt` | คำพูดทั้งหมด |
| `fb_output\summary.md` | สรุปหุ้น ตัวเลข มุมมอง action items |

---

## ปรับแต่ง (ใน .env)

```
LOCAL_FILE=C:\path\to\video.mp4   # ระบุไฟล์ตรงๆ (ถ้าไม่อยากวางในโฟลเดอร์)
WHISPER_MODEL=medium              # แม่นยำกว่า small แต่ช้ากว่า
OUTPUT_DIR=my_output              # เปลี่ยนโฟลเดอร์ output
```

---

## แก้ปัญหาที่พบบ่อย

**script บอกไม่เจอไฟล์**
→ ตรวจว่าไฟล์ `.mp4` อยู่ในโฟลเดอร์เดียวกับ `run.bat` จริงๆ

**ไม่เจอ ffmpeg**
→ เปิด CMD พิมพ์ `winget install ffmpeg` แล้วปิด-เปิด CMD ใหม่

**Video DownloadHelper โหลดไม่ได้**
→ ลอง extension อื่น เช่น "FBDOWN" หรือเล่นวีดีโอจนสุดก่อนกดโหลด
