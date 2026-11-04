"""
JARVIS Text-to-Speech (TTS) Engine
Phase 2 Component: Ultra-Realistic Human Male Voice for Urdu and English.
Integrates ElevenLabs Multilingual v2 (Human Male) with fallback to gTTS (Google Urdu/English)
and pyttsx3 (offline fallback), complete with barge-in/stop support.
"""

import os
import re
import tempfile
import threading
import time
from dotenv import load_dotenv

load_dotenv()

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

# Default ElevenLabs Human Male Voice (Adam - Deep, cinematic, realistic male)
DEFAULT_ELEVENLABS_VOICE = "pNInz6obpgDQGcFmaJgB"
_speech_lock = threading.Lock()
_stop_requested = False


def is_urdu_text(text: str) -> bool:
    """Detect if text contains Urdu script or typical Roman Urdu markers."""
    if not text:
        return False
    # Check for Arabic/Urdu unicode characters
    if re.search(r'[\u0600-\u06FF]', text):
        return True
    # Check common Roman Urdu words
    roman_urdu_words = {
        "kya", "hai", "hain", "hoon", "aap", "tum", "mera", "meri", "kaise", "kaisa",
        "kar", "karo", "sakte", "sakta", "shukriya", "bhai", "main", "yeh",
        "woh", "theek", "acha", "bohot", "mujhe", "batao", "assalam", "alaikum"
    }
    words = set(re.findall(r'\b\w+\b', text.lower()))
    return len(words.intersection(roman_urdu_words)) >= 2


def normalize_urdu_phonetics(text: str) -> str:
    """
    Apply phonetic corrections and vocalic diacritics (Zabar, Zer, Pesh) to Urdu text
    so neural TTS engines (ElevenLabs, gTTS) pronounce names and common words accurately.
    """
    if not text:
        return text

    # Map of words/names to their phonetically disambiguated Urdu equivalents
    # e.g., 'اَکمل' with Zabar (\u064E) forces 'Akmal' instead of 'Ikmal' / 'إكمال'
    phonetic_map = {
        r'\bاکمل\b': 'اَکمل',
        r'\bاحمل\b': 'اَکمل',
        r'\bجاروس\b': 'جاروِس',
        r'\bjarvis\b': 'جاروِس',
        r'\bJarvis\b': 'جاروِس',
        r'\bakmal\b': 'اَکمل',
        r'\bAkmal\b': 'اَکمل',
    }

    normalized = text
    is_urdu = is_urdu_text(text)

    for pattern, replacement in phonetic_map.items():
        # Only replace roman names if the sentence has Urdu context
        if not is_urdu and pattern in (r'\bakmal\b', r'\bAkmal\b', r'\bjarvis\b', r'\bJarvis\b'):
            continue
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

    return normalized


def stop_speech() -> bool:
    """Instantly interrupt and stop any ongoing speech playback (Barge-in)."""
    global _stop_requested
    _stop_requested = True
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            try:
                pygame.mixer.music.unload()
            except AttributeError:
                pass
        return True
    except Exception as e:
        print(f"Error stopping speech: {e}")
        return False


def is_speaking() -> bool:
    """Check if voice is currently playing."""
    try:
        if pygame.mixer.get_init():
            return bool(pygame.mixer.music.get_busy())
    except Exception:
        pass
    return False


def _generate_elevenlabs(text: str, voice_id: str, output_path: str) -> bool:
    """Generate human male speech using ElevenLabs Multilingual v2."""
    api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        return False

    v_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_ELEVENLABS_VOICE)

    try:
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=api_key)
        audio = client.text_to_speech.convert(
            voice_id=v_id,
            text=text,
            model_id="eleven_multilingual_v2"
        )
        audio_bytes = b"".join(list(audio))
        if len(audio_bytes) > 0:
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            return True
    except Exception as e:
        print(f"[TTS] ElevenLabs warning: {e}. Falling back to secondary engine...")
    return False


def _generate_gtts(text: str, output_path: str) -> bool:
    """Generate natural speech using Google TTS (excellent natural Urdu and English)."""
    try:
        import gtts
        lang = "ur" if is_urdu_text(text) else "en"
        tts = gtts.gTTS(text=text, lang=lang, slow=False)
        tts.save(output_path)
        return True
    except Exception as e:
        print(f"[TTS] gTTS warning: {e}")
    return False


def _generate_edge_tts(text: str, output_path: str, voice: str = "") -> bool:
    """
    Generate speech using Microsoft Edge Neural TTS.
    100% Free, unlimited, ultra-natural and lightweight human male voice.
    Automatically transliterates Roman Urdu into Nastaliq script so ur-PK-AsadNeural
    delivers studio-quality Pakistani human male presenter voice without robotic artifacts.
    """
    try:
        import asyncio
        import edge_tts
        from backend.voice.transliterate import prepare_speech_text

        tts_text, recommended_voice = prepare_speech_text(text)
        chosen_voice = voice or recommended_voice

        async def _run():
            communicate = edge_tts.Communicate(tts_text, chosen_voice, rate="+1%")
            await communicate.save(output_path)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    pool.submit(asyncio.run, _run()).result()
            else:
                loop.run_until_complete(_run())
        except RuntimeError:
            asyncio.run(_run())

        return os.path.exists(output_path) and os.path.getsize(output_path) > 0
    except Exception as e:
        print(f"[TTS] edge-tts warning: {e}")
    return False


def _generate_pyttsx3(text: str, output_path: str) -> bool:
    """Offline system voice fallback."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        # Set male voice if available
        voices = engine.getProperty('voices')
        for v in voices:
            if "david" in v.name.lower() or "male" in v.name.lower():
                engine.setProperty('voice', v.id)
                break
        engine.setProperty('rate', 165)
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        return True
    except Exception as e:
        print(f"[TTS] pyttsx3 warning: {e}")
    return False


def clean_text_for_speech(text: str) -> str:
    """
    Clean text for spoken audio: strip markdown code blocks, inline code,
    urls, headers, tables and excessive text so voice output is crisp and natural.
    """
    if not text:
        return ""
    # Strip markdown code blocks ```...```
    cleaned = re.sub(r'```[\s\S]*?```', '', text)
    # Strip inline backticks `foo`
    cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)
    # Strip URLs
    cleaned = re.sub(r'https?://\S+', '', cleaned)
    # Strip markdown headers, table separators, bullets
    cleaned = re.sub(r'^#+\s+', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'[*_~#|]', '', cleaned)
    cleaned = re.sub(r'^[-*+]\s+', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # If the text was entirely code/markdown and nothing is left
    if not cleaned:
        if is_urdu_text(text):
            return "Ji Akmal bhai, code aur details screen par display kar di hain."
        return "Yes sir, the details are displayed on your screen."

    # If text is very long, limit to first 1-2 sentences for natural speech
    if len(cleaned) > 220:
        sentences = re.split(r'(?<=[.!?])\s+', cleaned)
        if sentences:
            spoken = " ".join(sentences[:2]).strip()
            if len(spoken) <= 220:
                return spoken
            return spoken[:200].rstrip() + "."
        return cleaned[:200].rstrip() + "..."
    return cleaned


def speak(text: str, voice_id: str = "") -> bool:
    """
    Synthesize and play speech with real human male voice.
    Automatically prioritizes Edge-TTS (Free Light Male Voice), ElevenLabs, pyttsx3, then gTTS.
    """
    global _stop_requested
    if not text or not text.strip():
        return False

    # Clean text to strip code blocks, raw diffs, and long markdown before speech synthesis
    text = clean_text_for_speech(text)

    # Apply phonetic diacritics for accurate Urdu pronunciation (e.g., Akmal)
    text = normalize_urdu_phonetics(text)

    # Reset stop flag for this playback
    _stop_requested = False

    temp_mp3 = None
    temp_wav = None
    played_file = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_mp3 = f.name
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_wav = f.name

        # Tier 1: Microsoft Edge Neural TTS (Free, Studio-Grade Human Male Voice)
        if _generate_edge_tts(text, temp_mp3, voice=voice_id) and os.path.exists(temp_mp3) and os.path.getsize(temp_mp3) > 0:
            played_file = temp_mp3

        # Tier 2: ElevenLabs (Realistic Human Male Voice - Adam)
        if not played_file and os.getenv("ELEVENLABS_API_KEY"):
            if _generate_elevenlabs(text, voice_id, temp_mp3) and os.path.exists(temp_mp3) and os.path.getsize(temp_mp3) > 0:
                played_file = temp_mp3

        # Tier 3: pyttsx3 (Microsoft David - Offline System Fallback)
        if not played_file:
            if _generate_pyttsx3(text, temp_wav) and os.path.exists(temp_wav) and os.path.getsize(temp_wav) > 0:
                played_file = temp_wav

        # Tier 4: gTTS (Emergency fallback)
        if not played_file:
            if _generate_gtts(text, temp_mp3) and os.path.exists(temp_mp3) and os.path.getsize(temp_mp3) > 0:
                played_file = temp_mp3

        if not played_file:
            print("[TTS] All speech generation providers failed.")
            return False

        if _stop_requested:
            return False

        # Play audio using pygame.mixer
        with _speech_lock:
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            pygame.mixer.music.load(played_file)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                if _stop_requested:
                    pygame.mixer.music.stop()
                    break
                pygame.time.wait(100)

        return True

    except Exception as error:
        print(f"[TTS] Playback error: {error}")
        return False
    finally:
        try:
            if pygame.mixer.get_init() and not pygame.mixer.music.get_busy():
                try:
                    pygame.mixer.music.unload()
                except AttributeError:
                    pass
        except Exception:
            pass

        for p in (temp_mp3, temp_wav):
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass


if __name__ == "__main__":
    print("Testing JARVIS Real Human Male Voice (Urdu)...")
    speak("السلام علیکم، میں جاروس ہوں۔ میں آپ کی کیا مدد کر سکتا ہوں؟")
    print("Testing JARVIS Real Human Male Voice (Roman Urdu)...")
    speak("Assalam o Alaikum! Main JARVIS hoon. Aap kaise hain?")
    print("Testing JARVIS Real Human Male Voice (English)...")
    speak("Hello Akmal, JARVIS is fully online and ready.")
