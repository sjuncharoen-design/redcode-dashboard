"""
fb_transcribe.py
================
Facebook Group (ปิด) → เสียง → Transcript (faster-whisper) → สรุป (Gemini Free)
วิธีใช้: python fb_transcribe.py
หรือ:   FACEBOOK_VIDEO_URL="https://..." python fb_transcribe.py
"""

import os
import sys
import subprocess
from pathlib import Path

# โหลด .env ถ้ามี (ไม่บังคับ)
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

# ============================
# CONFIG — ใส่ใน .env หรือแก้ตรงนี้
# ============================
FACEBOOK_VIDEO_URL = os.environ.get("FACEBOOK_VIDEO_URL", "")
LOCAL_FILE         = os.environ.get("LOCAL_FILE", "")  # path ไฟล์วีดีโอ/เสียงในเครื่อง (ถ้ามี จะข้ามการดาวน์โหลด)
GEMINI_API_KEY     = os.environ.get("GEMINI_API_KEY", "")
WHISPER_MODEL      = os.environ.get("WHISPER_MODEL", "small")  # small=เร็ว / medium=แม่นยำกว่า
OUTPUT_DIR         = Path(os.environ.get("OUTPUT_DIR", "fb_output"))
# ENGINE: "gemini" = ส่งเสียงให้ Gemini สรุปตรงๆ (เร็วมาก, แนะนำ)
#         "whisper" = ถอดเสียงในเครื่องด้วย faster-whisper (ช้า แต่ได้ transcript เต็ม)
ENGINE             = os.environ.get("ENGINE", "gemini").lower()
GEMINI_MODEL       = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
# ============================

# นามสกุลไฟล์วีดีโอ/เสียงที่รองรับ
MEDIA_EXTS = (".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4a", ".mp3", ".wav", ".aac", ".flac")

def install_deps():
    # yt-dlp ต้อง update บ่อยเพราะ Facebook เปลี่ยน API ตลอด
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-U", "yt-dlp", "-q"],
        capture_output=True
    )
    pkgs = ["google-generativeai", "imageio-ffmpeg"]
    if ENGINE == "whisper":
        pkgs.append("faster-whisper")
    for pkg in pkgs:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg, "-q"],
            capture_output=True
        )
    print("Dependencies ready")

def _find_ytdlp() -> str:
    # yt-dlp อาจอยู่ใน Anaconda Scripts ซึ่งไม่ได้อยู่ใน PATH
    import shutil
    found = shutil.which("yt-dlp")
    if found:
        return found
    # หาจาก Scripts folder ข้างๆ python.exe
    scripts = Path(sys.executable).parent / "Scripts" / "yt-dlp.exe"
    if scripts.exists():
        return str(scripts)
    scripts2 = Path(sys.executable).parent / "yt-dlp.exe"
    if scripts2.exists():
        return str(scripts2)
    # fallback: รันผ่าน python -m yt_dlp
    return None

def download_audio(url: str, out_dir: Path) -> Path:
    out_dir.mkdir(exist_ok=True)
    audio_path = out_dir / "audio.mp3"

    if audio_path.exists():
        audio_path.unlink()

    print("Downloading audio from Facebook...")
    print("   (Chrome must be closed after login)")

    ytdlp = _find_ytdlp()
    if ytdlp:
        cmd = [ytdlp]
    else:
        cmd = [sys.executable, "-m", "yt_dlp"]

    # ใช้ cookies.txt ถ้ามี (แก้ปัญหา Chrome 127+ DPAPI encryption)
    cookies_file = Path(__file__).parent / "cookies.txt"
    if cookies_file.exists():
        print("   Using cookies.txt file")
        cookie_args = ["--cookies", str(cookies_file)]
    else:
        print("   Using Chrome browser cookies (close Chrome first!)")
        cookie_args = ["--cookies-from-browser", "chrome"]

    cmd += [
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        *cookie_args,
        "--no-playlist",
        "-o", str(audio_path),
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print("Download failed:")
        print(result.stderr[-1200:])
        print("\nFix: Export cookies from Chrome using 'Get cookies.txt LOCALLY' extension")
        print("     Save as 'cookies.txt' in the same folder as this script, then run again.")
        sys.exit(1)

    print(f"✅ ดาวน์โหลดสำเร็จ → {audio_path}")
    return audio_path

def find_local_media() -> Path:
    """หาไฟล์วีดีโอ/เสียงในเครื่อง: จาก LOCAL_FILE ก่อน, ไม่งั้นสแกนในโฟลเดอร์ script"""
    if LOCAL_FILE:
        p = Path(LOCAL_FILE)
        if p.exists():
            return p
        print(f"Warning: LOCAL_FILE ไม่พบไฟล์: {LOCAL_FILE}")

    # สแกนหาไฟล์ media ในโฟลเดอร์เดียวกับ script (ยกเว้นไฟล์ output ของเราเอง)
    here = Path(__file__).parent
    candidates = [
        f for f in here.iterdir()
        if f.is_file() and f.suffix.lower() in MEDIA_EXTS
    ]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        # เลือกไฟล์ที่ใหญ่ที่สุด (น่าจะเป็นวีดีโอที่โหลดมา)
        return max(candidates, key=lambda f: f.stat().st_size)
    return None


def extract_audio_small(media_path: Path, out_dir: Path) -> Path:
    """ดึงเฉพาะเสียงออกมาเป็น mp3 ขนาดเล็ก (mono 16kHz) เพื่ออัปโหลดให้ Gemini เร็วๆ"""
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    audio = out_dir / "audio.mp3"
    if audio.exists():
        audio.unlink()

    print("   กำลังดึงเสียงออกจากวีดีโอ...")
    cmd = [
        ffmpeg, "-y", "-i", str(media_path),
        "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k",
        str(audio),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if not audio.exists():
        print("❌ ดึงเสียงไม่สำเร็จ:")
        print(result.stderr[-800:])
        sys.exit(1)
    mb = audio.stat().st_size / 1_000_000
    print(f"   ได้ไฟล์เสียง {mb:.1f} MB")
    return audio


def summarize_from_audio(audio_path: Path, api_key: str, out_dir: Path) -> str:
    """อัปโหลดเสียงให้ Gemini แล้วสรุปโดยตรง (ไม่ต้องถอด transcript ในเครื่อง)"""
    import time
    import google.generativeai as genai

    genai.configure(api_key=api_key)

    print("   กำลังอัปโหลดเสียงไป Gemini...")
    f = genai.upload_file(str(audio_path))
    # รอจน Gemini ประมวลผลไฟล์เสร็จ
    while getattr(f.state, "name", str(f.state)) == "PROCESSING":
        time.sleep(2)
        f = genai.get_file(f.name)
    if getattr(f.state, "name", str(f.state)) == "FAILED":
        print("❌ Gemini ประมวลผลไฟล์เสียงไม่สำเร็จ")
        sys.exit(1)

    print("   กำลังให้ Gemini ฟังและสรุป...")
    model = genai.GenerativeModel(GEMINI_MODEL)

    prompt = """คุณคือนักวิเคราะห์หุ้นไทย (SET) เชี่ยวชาญด้าน Contrarian Value Investing

ฟังเสียงคลิปนี้ (เป็นภาษาไทย) แล้วสรุปเป็นภาษาไทยในหัวข้อต่อไปนี้:

1. **ประเด็นหลัก** — สรุป 3-5 bullet สั้นๆ ว่าพูดเรื่องอะไร
2. **หุ้น/บริษัทที่พูดถึง** — ชื่อ + ประเด็นสำคัญของแต่ละตัว
3. **ตัวเลขสำคัญ** — ราคา, P/E, EPS, revenue growth หรือ metrics ที่กล่าวถึง
4. **มุมมอง/คำแนะนำ** — ผู้พูดมีมุมมองอย่างไร (bullish/bearish/neutral)
5. **Action items** — มีอะไรที่ควรติดตามหรือศึกษาต่อ
6. **คำพูดสำคัญ (quotes)** — ยกประโยคเด็ดๆ 3-5 ประโยคที่น่าสนใจ
"""

    response = model.generate_content([prompt, f])
    summary = response.text

    summary_path = out_dir / "summary.md"
    summary_path.write_text(summary, encoding="utf-8")
    print(f"✅ สรุปบันทึกที่: {summary_path}")

    # ลบไฟล์ที่อัปโหลดทิ้ง (ไม่บังคับ)
    try:
        genai.delete_file(f.name)
    except Exception:
        pass

    return summary


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

    if not GEMINI_API_KEY:
        print("\n❌ ยังไม่ได้ใส่ Gemini API Key")
        print("   ขอ key ฟรีที่: https://aistudio.google.com/app/apikey")
        print("   ใส่ใน .env:  GEMINI_API_KEY=AIzaSy...")
        sys.exit(1)

    print("\n📦 Step 1/3: ติดตั้ง packages...")
    install_deps()

    print("\n📥 Step 2/3: หาไฟล์เสียง/วีดีโอ...")
    OUTPUT_DIR.mkdir(exist_ok=True)
    media = find_local_media()
    if media:
        # มีไฟล์ในเครื่อง → ข้ามการดาวน์โหลด
        print(f"✅ ใช้ไฟล์ในเครื่อง: {media.name}")
        audio_path = media
    elif FACEBOOK_VIDEO_URL:
        # ไม่มีไฟล์ → ลองดาวน์โหลดด้วย yt-dlp
        audio_path = download_audio(FACEBOOK_VIDEO_URL, OUTPUT_DIR)
    else:
        print("\n❌ ไม่พบไฟล์วีดีโอ/เสียง และไม่ได้ใส่ URL")
        print("\n   วิธีที่ง่ายที่สุด (แนะนำ):")
        print("   1. โหลดวีดีโอจาก Facebook ด้วย extension 'Video DownloadHelper'")
        print("   2. เอาไฟล์ที่ได้ (.mp4) มาวางในโฟลเดอร์เดียวกับ run.bat")
        print("   3. รัน run.bat อีกครั้ง")
        sys.exit(1)

    if ENGINE == "whisper":
        # โหมดช้า: ถอด transcript เต็มในเครื่องด้วย faster-whisper
        print("\n📝 Step 3/3: ถอด transcript + สรุป (โหมด whisper)...")
        transcript = transcribe(audio_path, WHISPER_MODEL, OUTPUT_DIR)
        summary    = summarize(transcript, GEMINI_API_KEY, OUTPUT_DIR)
        print("\n" + "=" * 55)
        print("🎉 เสร็จสมบูรณ์!")
        print(f"   📄 Transcript : {OUTPUT_DIR}\\transcript.txt")
        print(f"   📝 Summary    : {OUTPUT_DIR}\\summary.md")
    else:
        # โหมดเร็ว (แนะนำ): ส่งเสียงให้ Gemini สรุปตรงๆ
        print("\n📝 Step 3/3: สรุปด้วย Gemini (โหมดเร็ว)...")
        audio = extract_audio_small(audio_path, OUTPUT_DIR)
        summary = summarize_from_audio(audio, GEMINI_API_KEY, OUTPUT_DIR)
        print("\n" + "=" * 55)
        print("🎉 เสร็จสมบูรณ์!")
        print(f"   📝 Summary : {OUTPUT_DIR}\\summary.md")

    print("=" * 55)
    print("\n--- สรุป ---\n")
    print(summary)

if __name__ == "__main__":
    main()
