"""
JARVIS Voice Input (Speech-to-Text) Module
Phase 2 Component: Handles microphone input listening and transcription.
"""

from importlib.util import find_spec


class UnauthorizedSpeakerError(Exception):
    """Raised when incoming voice fails speaker biometric verification."""
    pass


def is_available() -> bool:
    return find_spec("pyaudio") is not None and find_spec("speech_recognition") is not None


def transcribe_offline(recognizer: "sr.Recognizer", audio: "sr.AudioData", language: str = "en-US") -> str:
    """
    Offline speech-to-text fallback engine.
    Probes locally installed offline speech decoders:
    faster-whisper, whisper, vosk, sphinx.
    """
    # 1. Faster-Whisper (Highest accuracy local engine)
    try:
        if hasattr(recognizer, "recognize_faster_whisper"):
            lang_code = "ur" if ("ur" in language.lower() or "pk" in language.lower()) else "en"
            return recognizer.recognize_faster_whisper(audio, language=lang_code)
    except Exception:
        pass

    # 2. OpenAI Whisper local
    try:
        if hasattr(recognizer, "recognize_whisper"):
            return recognizer.recognize_whisper(audio, model="base")
    except Exception:
        pass

    # 3. Vosk offline
    try:
        if hasattr(recognizer, "recognize_vosk"):
            return recognizer.recognize_vosk(audio)
    except Exception:
        pass

    # 4. CMU Sphinx
    try:
        if hasattr(recognizer, "recognize_sphinx"):
            return recognizer.recognize_sphinx(audio)
    except Exception:
        pass

    raise RuntimeError("Cloud speech recognition unreachable (offline) and no local STT engine (faster-whisper/vosk) is installed.")


def listen(timeout: int = 6, language: str = "en-US", verify_biometrics: bool = False) -> str:
    """
    Listen to user speech from microphone and transcribe to text with fast response.
    Supports automatic offline fallback if cloud recognition is unreachable.
    """
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    recognizer.operation_timeout = 15
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.1)
        audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=10)

    # 1. Voice Biometrics Check (Soft check if requested)
    if verify_biometrics:
        try:
            from backend.security.voiceprint import verify_voice, is_voiceprint_enrolled
            if is_voiceprint_enrolled():
                pcm_bytes = audio.get_raw_data()
                sample_rate = audio.sample_rate
                is_authorized, score, msg = verify_voice(pcm_bytes, sample_rate)
                if not is_authorized:
                    raise UnauthorizedSpeakerError(msg)
        except UnauthorizedSpeakerError:
            raise
        except Exception:
            pass

    # 2. Transcribe speech with automatic offline fallback
    try:
        raw_text = recognizer.recognize_google(audio, language=language)
    except (sr.RequestError, Exception) as cloud_err:
        try:
            raw_text = transcribe_offline(recognizer, audio, language=language)
        except Exception:
            raise cloud_err

    # 3. If Urdu script returned, normalize to Roman Urdu for seamless intent matching
    try:
        from backend.voice.transliterate import normalize_urdu_to_roman
        return normalize_urdu_to_roman(raw_text)
    except Exception:
        return raw_text


def enroll_from_mic(timeout: int = 6) -> dict:
    """
    Listen to creator speaking into microphone and enroll voiceprint.
    """
    import speech_recognition as sr
    from backend.security.voiceprint import enroll_creator_voice

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=timeout)

    pcm_bytes = audio.get_raw_data()
    sample_rate = audio.sample_rate
    return enroll_creator_voice(pcm_bytes, sample_rate)

