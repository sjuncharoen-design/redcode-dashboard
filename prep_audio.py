"""
prep_audio.py
=============
เตรียมเสียงจากวีดีโอ เพื่อเอาไปสรุปด้วย AI ฟรี (Google AI Studio)

วิธีนี้ไม่ต้องใช้ API key, ไม่มี quota, ไม่ต้องถอดเสียงในเครื่อง
- หาไฟล์วีดีโอในโฟลเดอร์นี้
- ดึงเฉพาะเสียงออกมาเป็น mp3 ขนาดเล็ก
- เขียนคำสั่ง (prompt) สำหรับ AI ให้พร้อมก็อป
จากนั้นเอา audio.mp3 ไปอัปโหลดที่ https://aistudio.google.com แล้ววาง prompt
"""

import os
import sys
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "audio_for_ai"
MEDIA_EXTS = (".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4a", ".wav", ".aac", ".flac")

PROMPT = """คุณคือนักวิเคราะห์หุ้นไทย (SET) เชี่ยวชาญ Contrarian Value Investing
ฟังไฟล์เสียงที่แนบมา (ภาษาไทย) แล้วเขียนสรุปเชิงลึกเป็นภาษาไทย ความยาวประมาณ 1 หน้า A4
เน้นให้เข้าใจแก่น เห็นเหตุผลเบื้องหลัง และนำไปต่อยอด/ตัดสินใจลงทุนได้จริง
อย่าสรุปสั้นเกินไป ให้ลงรายละเอียดในจุดสำคัญ พร้อมอธิบายว่า "ทำไม" ไม่ใช่แค่ "อะไร"

โครงสร้างที่ต้องการ:

1. ภาพรวมเนื้อหา (Executive Summary)
   - คลิปนี้พูดเรื่องอะไร ธีมหลักคืออะไร สรุป 4-6 ข้อ
   - บริบท/สถานการณ์ตลาดที่ผู้พูดอ้างถึง

2. หุ้น/บริษัทที่พูดถึง (วิเคราะห์ทีละตัว)
   สำหรับแต่ละตัว ให้ลงรายละเอียด:
   - ทำธุรกิจอะไร โมเดลรายได้
   - จุดเด่น/ความได้เปรียบในการแข่งขัน (moat)
   - ความเสี่ยง/จุดอ่อน/สิ่งที่ต้องระวัง
   - เหตุผลที่ผู้พูดสนใจหรือไม่สนใจ (thesis)

3. ตัวเลข/ข้อมูลเชิงปริมาณ
   - ราคา, P/E, P/BV, EPS, ROE, อัตราการเติบโต, ปันผล, มาร์จิ้น ฯลฯ ที่กล่าวถึง
   - มูลค่าเหมาะสม/เป้าหมายราคา ถ้ามี และที่มาของการประเมิน

4. มุมมอง/กลยุทธ์ของผู้พูด
   - มองบวก/ลบ/กลาง ต่อแต่ละตัวและต่อตลาดโดยรวม พร้อมเหตุผล
   - หลักคิด/กรอบการวิเคราะห์ที่ใช้ (เช่น มอง valuation, วัฏจักร, catalyst)

5. ประเด็นน่าสนใจ/ข้อคิดเชิงลึก
   - แนวคิดหรือมุมมองที่แตกต่าง น่านำไปคิดต่อ

6. Action items — สิ่งที่ควรไปศึกษา ติดตาม หรือตรวจสอบเพิ่ม (เป็นข้อๆ ทำได้จริง)

7. คำพูดเด็ด 3-5 ประโยค ที่สะท้อนแนวคิดสำคัญ (ยกมาตามที่พูด)

จัดรูปแบบด้วยหัวข้อและ bullet ให้อ่านง่าย ใช้ภาษากระชับแต่ได้สาระครบ
"""


def find_video():
    cands = [f for f in HERE.iterdir() if f.is_file() and f.suffix.lower() in MEDIA_EXTS]
    if not cands:
        return None
    return max(cands, key=lambda f: f.stat().st_size)


def main():
    print("=" * 55)
    print("  เตรียมเสียงสำหรับสรุปด้วย AI (ฟรี ไม่ต้องใช้ API key)")
    print("=" * 55)

    print("\n[1/3] ติดตั้งเครื่องมือ (ครั้งแรกครั้งเดียว)...")
    subprocess.run([sys.executable, "-m", "pip", "install", "imageio-ffmpeg", "-q"], capture_output=True)
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()

    print("\n[2/3] หาวีดีโอ + ดึงเสียง...")
    video = find_video()
    if not video:
        print("  ❌ ไม่พบไฟล์วีดีโอในโฟลเดอร์นี้")
        print("     เอาไฟล์วีดีโอ (.mp4) มาวางในโฟลเดอร์เดียวกับไฟล์นี้ก่อน")
        input("\nกด Enter เพื่อปิด...")
        sys.exit(1)
    print(f"  พบวีดีโอ: {video.name}")

    OUT.mkdir(exist_ok=True)
    audio = OUT / "audio.mp3"
    if audio.exists():
        audio.unlink()
    print("  กำลังดึงเสียง (อาจใช้เวลา 1-2 นาทีสำหรับคลิปยาว)...")
    subprocess.run(
        [ff, "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-b:a", "32k", str(audio)],
        capture_output=True,
    )
    if not audio.exists():
        print("  ❌ ดึงเสียงไม่สำเร็จ")
        input("\nกด Enter เพื่อปิด...")
        sys.exit(1)
    mb = audio.stat().st_size / 1_000_000
    print(f"  ✅ ได้ไฟล์เสียง: {audio}  ({mb:.1f} MB)")

    # เขียน prompt ไว้ให้ก็อปง่ายๆ
    prompt_file = OUT / "prompt.txt"
    prompt_file.write_text(PROMPT, encoding="utf-8")

    print("\n[3/3] เอาไปสรุปด้วย AI ฟรี — ทำตามนี้:")
    print("  1. เปิดเว็บ  https://aistudio.google.com  (login Google ธรรมดา ไม่ต้องใช้ key)")
    print("  2. กดปุ่ม + (แนบไฟล์) → เลือกไฟล์:")
    print(f"       {audio}")
    print(f"  3. เปิดไฟล์ prompt.txt → ก็อปข้อความทั้งหมด → วางในช่องแชต")
    print(f"       (prompt อยู่ที่: {prompt_file})")
    print("  4. กด Run / ส่ง → ได้สรุปทันที (ราว 1-2 นาที)")

    # เปิดโฟลเดอร์ผลลัพธ์ให้อัตโนมัติ (Windows)
    try:
        os.startfile(str(OUT))  # type: ignore[attr-defined]
    except Exception:
        pass

    print("\n" + "=" * 55)
    print("  เสร็จขั้นเตรียม! ทำตามข้อ 1-4 ด้านบนต่อได้เลย")
    print("=" * 55)
    input("\nกด Enter เพื่อปิด...")


if __name__ == "__main__":
    main()
