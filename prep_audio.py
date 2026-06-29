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
ฟังไฟล์เสียงที่แนบมา (ภาษาไทย) แล้วสรุปเป็นภาษาไทย เน้นให้เข้าใจง่ายและนำไปต่อยอดได้:

1. ภาพรวม — คลิปนี้พูดเรื่องอะไร สรุป 3-5 ข้อ
2. หุ้น/บริษัทที่พูดถึง — แต่ละตัวมีประเด็นอะไร (ธุรกิจ จุดเด่น ความเสี่ยง)
3. ตัวเลขสำคัญ — ราคา, P/E, EPS, การเติบโต, ปันผล ฯลฯ ที่กล่าวถึง
4. มุมมองผู้พูด — มองบวก/ลบ/กลางๆ และเพราะอะไร
5. สิ่งที่ควรทำต่อ (Action) — ควรไปศึกษา/ติดตามอะไรเพิ่ม
6. คำพูดเด็ด 3-5 ประโยค ที่น่าจดจำ

ตอบเป็นภาษาไทย กระชับ เข้าใจง่าย ใช้ bullet
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
