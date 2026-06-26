"""
fb_transcribe.py
================
Facebook Group (ปิด) → เสียง → Transcript (faster-whisper) → สรุป (Gemini Free)
วิธีใช้: python fb_transcribe.py
"""

import sys
import subprocess
from pathlib import Path

# ============================
# CONFIG — แก้ตรงนี้ 2 บรรทัด
# ============================
FACEBOOK_VIDEO_URL = "https://www.facebook.com/groups/XXXX/posts/XXXX"
GEMINI_API_KEY     = "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
WHISPER_MODEL      = "small"   # small=เร็ว / medium=แม่นยำกว่า
OUTPUT_DIR         = Path("fb_output")
# ============================

def install_deps():
    pkgs = [
        "yt-dlp",
        "faster-whisper",
        "google-generativeai",
    ]
    for pkg in pkgs:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg, "-q"],
            capture_output=True
        )
    print("✅ Dependencies ready")

def download_audio(url: str, out_dir: Path) -> Path:
    out_dir.mkdir(exist_ok=True)
    audio_path = out_dir / "audio.mp3"

    if audio_path.exists():
        audio_path.unlink()

    print("⬇️  กำลังดาวน์โหลดเสียงจาก Facebook...")
    print("   (ต้องเปิด Chrome และ login Facebook ไว้ก่อน)")
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--cookies-from-browser", "chrome",
        "--no-playlist",
        "-o", str(audio_path),
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print("❌ Download failed:")
        print(result.stderr[-800:])
        print("\n💡 วิธีแก้:")
        print("   1. เปิด Chrome → login Facebook")
        print("   2. ปิด Chrome ทุกหน้าต่าง")
        print("   3. รัน script ใหม่")
        sys.exit(1)

    print(f"✅ ดาวน์โหลดสำเร็จ → {audio_path}")
    return audio_path

def transcribe(audio_path: Path, model_size: str, out_dir: Path) -> str:
    print(f"\n🎙️  กำลังถอด transcript (faster-whisper / model={model_size})")
    print("   วีดีโอ 2-3 ชม. ใช้เวลาประมาณ 5-10 นาที...")

    from faster_whisper import WhisperModel

    try:
        model = WhisperModel(model_size, device="cuda", compute_type="float16")
        print("   ⚡ ใช้ GPU (เร็วมาก)")
    except Exception:
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        print("   🖥️  ใช้ CPU")

    segments, info = model.transcribe(
        str(audio_path),
        language="th",
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )

    print("   กำลังประมวลผล", end="", flush=True)
    transcript_parts = []
    for i, seg in enumerate(segments):
        transcript_parts.append(seg.text)
        if i % 50 == 0:
            print(".", end="", flush=True)
    print(" เสร็จ!")

    transcript = " ".join(transcript_parts).strip()

    transcript_path = out_dir / "transcript.txt"
    transcript_path.write_text(transcript, encoding="utf-8")
    print(f"✅ Transcript บันทึกที่: {transcript_path}")
    print(f"   ({len(transcript):,} ตัวอักษร)")
    return transcript

def summarize(transcript: str, api_key: str, out_dir: Path) -> str:
    print("\n🤖 กำลังสรุปด้วย Gemini...")

    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    MAX_CHARS = 800_000
    note = ""
    if len(transcript) > MAX_CHARS:
        transcript = transcript[:MAX_CHARS]
        note = "\n\n⚠️ หมายเหตุ: transcript ถูกตัดบางส่วนเนื่องจากยาวมาก"

    prompt = f"""คุณคือนักวิเคราะห์หุ้นไทย (SET) เชี่ยวชาญด้าน Contrarian Value Investing

จาก transcript ด้านล่าง ให้สรุปเป็นภาษาไทยในหัวข้อต่อไปนี้:

1. **ประเด็นหลัก** — สรุป 3-5 bullet สั้นๆ ว่าพูดเรื่องอะไร
2. **หุ้น/บริษัทที่พูดถึง** — ชื่อ + ประเด็นสำคัญของแต่ละตัว
3. **ตัวเลขสำคัญ** — ราคา, P/E, EPS, revenue growth หรือ metrics ที่กล่าวถึง
4. **มุมมอง/คำแนะนำ** — ผู้พูดมีมุมมองอย่างไร (bullish/bearish/neutral)
5. **Action items** — มีอะไรที่ควรติดตามหรือศึกษาต่อ

---
TRANSCRIPT:
{transcript}
"""

    response = model.generate_content(prompt)
    summary = response.text + note

    summary_path = out_dir / "summary.md"
    summary_path.write_text(summary, encoding="utf-8")
    print(f"✅ สรุปบันทึกที่: {summary_path}")
    return summary

def main():
    print("=" * 55)
    print("  Facebook Video → Transcript + สรุป")
    print("  (faster-whisper + Gemini Free)")
    print("=" * 55)

    if "XXXX" in FACEBOOK_VIDEO_URL:
        print("\n❌ ยังไม่ได้ใส่ URL")
        print("   แก้บรรทัด FACEBOOK_VIDEO_URL ใน script ก่อน")
        sys.exit(1)
    if "AIzaSyXXX" in GEMINI_API_KEY:
        print("\n❌ ยังไม่ได้ใส่ Gemini API Key")
        print("   ขอ key ฟรีที่: https://aistudio.google.com/app/apikey")
        print("   แล้วแก้บรรทัด GEMINI_API_KEY ใน script")
        sys.exit(1)

    print("\n📦 Step 1/3: ติดตั้ง packages...")
    install_deps()

    print("\n📥 Step 2/3: ดาวน์โหลดเสียง...")
    audio_path = download_audio(FACEBOOK_VIDEO_URL, OUTPUT_DIR)

    print("\n📝 Step 3/3: ถอด transcript + สรุป...")
    transcript = transcribe(audio_path, WHISPER_MODEL, OUTPUT_DIR)
    summary    = summarize(transcript, GEMINI_API_KEY, OUTPUT_DIR)

    print("\n" + "=" * 55)
    print("🎉 เสร็จสมบูรณ์!")
    print(f"   📄 Transcript : {OUTPUT_DIR}\\transcript.txt")
    print(f"   📝 Summary    : {OUTPUT_DIR}\\summary.md")
    print("=" * 55)
    print("\n--- สรุป ---\n")
    print(summary)

if __name__ == "__main__":
    main()
