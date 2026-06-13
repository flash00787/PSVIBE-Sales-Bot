#!/usr/bin/env python3
"""
Voice Message Transcription Tool for Kora
==========================================
Transcribes voice messages from Telegram/other platforms using:
  1. OpenAI Whisper API (primary — best quality, needs OPENAI_API_KEY)
  2. Google Cloud Speech-to-Text (fallback — needs GOOGLE_API_KEY)
  3. Local Whisper (if installed — pip install openai-whisper)

Dependencies:
  - ffmpeg (required for audio extraction/conversion)
  - requests (built-in + pip)
  - google-cloud-speech (optional, for Google STT)

Usage:
  python3 transcribe_voice.py <audio_file> [--provider openai|google|local] [--language en|my|auto]
  python3 transcribe_voice.py voice.ogg --provider openai
  python3 transcribe_voice.py voice.mp3 --language my

Environment:
  OPENAI_API_KEY   - OpenAI API key for Whisper API
  GOOGLE_API_KEY   - Google Cloud API key for Speech-to-Text
"""

import os
import sys
import json
import base64
import subprocess
import tempfile
import urllib.request
import urllib.error
from pathlib import Path

WS = os.environ.get("KORA_WS", "/home/node/.openclaw/workspace")
MEMORY_DIR = os.path.join(WS, "memory", "transcripts")

# ─── Configuration ───────────────────────────────────────────
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
DEFAULT_PROVIDER = "openai" if OPENAI_API_KEY else ("google" if GOOGLE_API_KEY else "none")
SUPPORTED_FORMATS = {".ogg", ".mp3", ".wav", ".m4a", ".flac", ".opus", ".oga", ".aac", ".webm"}

# ─── Audio Preprocessing (ffmpeg) ────────────────────────────

def check_ffmpeg():
    """Verify ffmpeg is available."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def extract_audio(input_path, output_format="wav", sample_rate=16000, channels=1):
    """
    Use ffmpeg to extract/convert audio to transcription-ready format.
    Returns path to converted file.
    """
    ext = Path(input_path).suffix.lower()
    if ext not in SUPPORTED_FORMATS:
        print(f"⚠️  Unsupported format: {ext}. Attempting conversion anyway...")

    output_path = input_path + f"_converted.{output_format}"

    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-ar", str(sample_rate),
        "-ac", str(channels),
        "-acodec", "pcm_s16le" if output_format == "wav" else "libmp3lame",
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"❌ ffmpeg conversion failed:\n{result.stderr[:500]}")
            return None
        print(f"   🎵 Audio converted: {os.path.getsize(output_path)} bytes")
        return output_path
    except subprocess.TimeoutExpired:
        print("❌ ffmpeg conversion timed out (>60s)")
        return None
    except Exception as e:
        print(f"❌ ffmpeg error: {e}")
        return None


# ─── Provider: OpenAI Whisper API ────────────────────────────

def transcribe_openai(audio_path, language="auto"):
    """
    Transcribe using OpenAI Whisper API.
    Supports: flac, m4a, mp3, mp4, mpeg, mpga, oga, ogg, wav, webm
    Max file size: 25MB
    """
    if not OPENAI_API_KEY:
        return None, "❌ OPENAI_API_KEY not set in environment"

    # Ensure format is supported by OpenAI
    ext = Path(audio_path).suffix.lower()
    openai_formats = {".flac", ".m4a", ".mp3", ".mp4", ".mpeg", ".mpga", ".oga", ".ogg", ".wav", ".webm"}

    file_to_send = audio_path
    if ext not in openai_formats:
        print(f"   🔄 Converting {ext} to mp3 for OpenAI...")
        converted = extract_audio(audio_path, "mp3")
        if not converted:
            return None, "❌ Could not convert audio for OpenAI"
        file_to_send = converted

    file_size = os.path.getsize(file_to_send)
    if file_size > 25 * 1024 * 1024:
        return None, f"❌ File too large for OpenAI Whisper API: {file_size / 1024 / 1024:.1f}MB (max 25MB)"

    try:
        import requests

        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

        data = {"model": "whisper-1"}
        if language and language != "auto":
            data["language"] = language
        data["response_format"] = "verbose_json"

        with open(file_to_send, "rb") as f:
            files = {"file": (os.path.basename(file_to_send), f)}
            resp = requests.post(url, headers=headers, data=data, files=files, timeout=120)

        if resp.status_code != 200:
            return None, f"❌ OpenAI API error ({resp.status_code}): {resp.text[:300]}"

        result = resp.json()
        text = result.get("text", "")
        segments = result.get("segments", [])

        return {
            "text": text.strip(),
            "segments": segments,
            "language": result.get("language", "unknown"),
            "duration": result.get("duration", 0),
            "provider": "openai-whisper-1"
        }, None

    except ImportError:
        return None, "❌ 'requests' package not available"
    except Exception as e:
        return None, f"❌ OpenAI Whisper API error: {e}"


# ─── Provider: Google Cloud Speech-to-Text ───────────────────

def transcribe_google(audio_path, language="en-US"):
    """
    Transcribe using Google Cloud Speech-to-Text API (v1, API key auth).
    Supports: WAV, FLAC, OGG, WEBM (mono, specific encodings)
    """
    if not GOOGLE_API_KEY:
        return None, "❌ GOOGLE_API_KEY not set in environment"

    # Google STT expects LINEAR16 or FLAC in most cases
    ext = Path(audio_path).suffix.lower()
    google_formats = {".wav", ".flac", ".ogg", ".opus", ".webm"}

    file_to_send = audio_path
    if ext not in google_formats:
        print(f"   🔄 Converting {ext} to FLAC for Google STT...")
        converted = extract_audio(audio_path, "flac", sample_rate=16000, channels=1)
        if not converted:
            converted = extract_audio(audio_path, "wav", sample_rate=16000, channels=1)
        if not converted:
            return None, "❌ Could not convert audio for Google STT"
        file_to_send = converted

    try:
        with open(file_to_send, "rb") as f:
            audio_content = base64.b64encode(f.read()).decode("utf-8")

        lang_map = {"auto": "en-US", "my": "my-MM", "en": "en-US", "th": "th-TH"}
        lang_code = lang_map.get(language, language)

        body = {
            "config": {
                "encoding": "FLAC" if file_to_send.endswith(".flac") else "LINEAR16",
                "sampleRateHertz": 16000,
                "languageCode": lang_code,
                "enableAutomaticPunctuation": True,
                "model": "default",
            },
            "audio": {"content": audio_content},
        }

        url = f"https://speech.googleapis.com/v1/speech:recognize?key={GOOGLE_API_KEY}"
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())

        if not result.get("results"):
            return None, "❌ No speech detected in audio"

        transcript = ""
        confidence_total = 0
        count = 0
        for r in result["results"]:
            alt = r.get("alternatives", [{}])[0]
            transcript += alt.get("transcript", "") + " "
            if "confidence" in alt:
                confidence_total += alt["confidence"]
                count += 1

        confidence = confidence_total / count if count > 0 else 0

        return {
            "text": transcript.strip(),
            "language": lang_code,
            "confidence": round(confidence, 3),
            "provider": "google-cloud-stt"
        }, None

    except urllib.error.HTTPError as e:
        err_body = e.read().decode()[:300]
        return None, f"❌ Google STT API error ({e.code}): {err_body}"
    except Exception as e:
        return None, f"❌ Google STT error: {e}"


# ─── Provider: Local Whisper (if installed) ──────────────────

def transcribe_local(audio_path, language="auto"):
    """Transcribe using locally installed openai-whisper."""
    try:
        import whisper
    except ImportError:
        return None, "❌ openai-whisper not installed. Run: pip install openai-whisper"

    try:
        model_size = os.environ.get("WHISPER_MODEL", "base")
        print(f"   🔄 Loading local whisper model '{model_size}'...")
        model = whisper.load_model(model_size)

        lang = None if language == "auto" else language
        result = model.transcribe(audio_path, language=lang, verbose=False)

        return {
            "text": result["text"].strip(),
            "segments": result.get("segments", []),
            "language": result.get("language", "unknown"),
            "provider": f"local-whisper-{model_size}"
        }, None

    except Exception as e:
        return None, f"❌ Local whisper error: {e}"


# ─── Main Transcription Pipeline ─────────────────────────────

def transcribe(audio_path, provider="auto", language="auto"):
    """
    Main entry point: transcribe voice message to text.
    
    Args:
        audio_path: Path to voice message file (ogg, mp3, wav, etc.)
        provider: "openai", "google", "local", or "auto" (tries best available)
        language: Language code ("en", "my", "th", "auto") or BCP-47 tag
    
    Returns:
        tuple: (result_dict, error_string)
    """
    # Validate input
    if not os.path.exists(audio_path):
        return None, f"❌ File not found: {audio_path}"

    if not check_ffmpeg():
        return None, "❌ ffmpeg is required for audio processing. Install: apt install ffmpeg"

    file_size = os.path.getsize(audio_path)
    print(f"\n🎤 Voice Transcription")
    print(f"   File: {os.path.basename(audio_path)} ({file_size / 1024:.1f} KB)")
    print(f"   Provider: {provider} | Language: {language}")

    # Auto-select provider
    if provider == "auto":
        if OPENAI_API_KEY:
            provider = "openai"
        elif GOOGLE_API_KEY:
            provider = "google"
        else:
            # Try local whisper
            try:
                import whisper
                provider = "local"
            except ImportError:
                return None, (
                    "❌ No transcription provider available.\n"
                    "   Set OPENAI_API_KEY for OpenAI Whisper API (recommended)\n"
                    "   or GOOGLE_API_KEY for Google Cloud Speech-to-Text\n"
                    "   or install: pip install openai-whisper"
                )

    # Transcribe
    result = None
    error = None

    if provider == "openai":
        result, error = transcribe_openai(audio_path, language)
    elif provider == "google":
        result, error = transcribe_google(audio_path, language)
    elif provider == "local":
        result, error = transcribe_local(audio_path, language)
    else:
        error = f"❌ Unknown provider: {provider}. Use: openai, google, or local"

    if error:
        return None, error

    # Save transcript
    os.makedirs(MEMORY_DIR, exist_ok=True)
    base_name = Path(audio_path).stem
    timestamp = __import__('time').strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(MEMORY_DIR, f"{base_name}_{timestamp}.md")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Voice Transcript\n\n")
        f.write(f"- **File:** {os.path.basename(audio_path)}\n")
        f.write(f"- **Provider:** {result['provider']}\n")
        f.write(f"- **Language:** {result.get('language', 'unknown')}\n")
        if "duration" in result:
            f.write(f"- **Duration:** {result['duration']:.1f}s\n")
        if "confidence" in result:
            f.write(f"- **Confidence:** {result['confidence']:.2%}\n")
        f.write(f"- **Date:** {__import__('datetime').datetime.now().isoformat()}\n\n")
        f.write(f"---\n\n{result['text']}\n")

    print(f"\n📝 Transcript saved to: {out_path}")
    print(f"\n{'─' * 60}")
    print(result["text"][:500])
    if len(result["text"]) > 500:
        print(f"... (truncated, full in {out_path})")
    print(f"{'─' * 60}")

    return result, None


# ─── CLI ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import time
    import datetime

    parser = argparse.ArgumentParser(
        description="Kora Voice Message Transcription Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 transcribe_voice.py voice.ogg
  python3 transcribe_voice.py voice.mp3 --provider openai --language my
  python3 transcribe_voice.py audio.wav --provider google

Supported providers:
  openai  - OpenAI Whisper API (best quality, needs OPENAI_API_KEY)
  google  - Google Cloud Speech-to-Text (needs GOOGLE_API_KEY)
  local   - Local openai-whisper (needs pip install openai-whisper)
  auto    - Auto-select best available (default)
        """
    )
    parser.add_argument("audio_file", help="Path to voice message file")
    parser.add_argument("--provider", choices=["openai", "google", "local", "auto"],
                        default="auto", help="Transcription provider (default: auto)")
    parser.add_argument("--language", default="auto",
                        help="Language code: en, my, th, auto (default: auto)")
    args = parser.parse_args()

    result, error = transcribe(args.audio_file, args.provider, args.language)

    if error:
        print(f"\n{error}")
        sys.exit(1)

    print(f"\n✅ Transcription complete ({result['provider']})")
