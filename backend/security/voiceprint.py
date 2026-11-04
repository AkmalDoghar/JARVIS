"""
JARVIS Voice Biometrics & Speaker Verification Engine
Phase 3 Security Component: Authenticates Creator Akmal bhai via voiceprint biometrics.
Extracts acoustic voice features (pitch, formant energy, spectral distribution) and
verifies incoming voice commands against enrolled creator voiceprints using cosine similarity.
"""

import os
import json
import math
import struct
from typing import Dict, Any, List, Optional, Tuple

VOICEPRINT_FILE = os.path.join(os.path.dirname(__file__), "creator_voiceprint.json")

# Default verification threshold (0.0 to 1.0)
DEFAULT_SIMILARITY_THRESHOLD = 0.70


def _extract_acoustic_features(pcm_bytes: bytes, sample_rate: int = 16000) -> List[float]:
    """
    Extract a normalized 48-dimensional acoustic speaker feature vector
    from raw 16-bit PCM audio samples.
    Measures pitch, energy bands, spectral centroid, and harmonic distributions.
    """
    if not pcm_bytes or len(pcm_bytes) < 3200: # Need at least 0.1s of audio
        return [0.0] * 48

    # Unpack 16-bit signed PCM samples
    num_samples = len(pcm_bytes) // 2
    try:
        samples = struct.unpack(f"<{num_samples}h", pcm_bytes[:num_samples * 2])
    except Exception:
        return [0.0] * 48

    # Normalize samples to -1.0 .. 1.0
    float_samples = [s / 32768.0 for s in samples]

    # 1. Energy and RMS
    rms = math.sqrt(sum(s * s for s in float_samples) / max(len(float_samples), 1))
    if rms < 0.005: # Silence or background noise
        return [0.0] * 48

    # 2. Zero-crossing rate
    zcr = 0
    for i in range(1, len(float_samples)):
        if (float_samples[i] >= 0 and float_samples[i - 1] < 0) or (float_samples[i] < 0 and float_samples[i - 1] >= 0):
            zcr += 1
    zcr_rate = zcr / max(len(float_samples), 1)

    # 3. Simple FFT / Frequency Band Energy Extraction (Divide into 32 bands from 80Hz to 4000Hz)
    # Using Discrete Fourier Analysis on representative frames
    frame_size = 512
    hop_size = 256
    num_frames = min((len(float_samples) - frame_size) // hop_size, 40)
    
    num_bands = 32
    band_energies = [0.0] * num_bands
    spectral_centroids = []

    for f_idx in range(max(1, num_frames)):
        start = f_idx * hop_size
        frame = float_samples[start:start + frame_size]
        # Apply Hann window
        windowed = [frame[i] * 0.5 * (1 - math.cos(2 * math.pi * i / (frame_size - 1))) for i in range(len(frame))]

        # Quick DFT magnitude approximation across 32 logarithmic frequency bins
        # Focus on vocal frequency range: 80Hz - 3800Hz
        for b in range(num_bands):
            # Center frequency for band b
            freq = 80.0 * math.pow(3800.0 / 80.0, b / (num_bands - 1))
            k = int(freq * frame_size / sample_rate)
            if k < frame_size // 2:
                # Real and Imaginary DFT components at bin k
                angle = 2.0 * math.pi * k / frame_size
                real_part = sum(windowed[n] * math.cos(angle * n) for n in range(0, frame_size, 2))
                imag_part = sum(-windowed[n] * math.sin(angle * n) for n in range(0, frame_size, 2))
                mag = math.sqrt(real_part * real_part + imag_part * imag_part)
                band_energies[b] += mag

    # Normalize band energies
    total_energy = sum(band_energies) + 1e-6
    normalized_bands = [e / total_energy for e in band_energies]

    # 4. Spectral Centroid
    spectral_centroid = sum(i * normalized_bands[i] for i in range(num_bands)) / max(sum(normalized_bands), 1e-6)

    # 5. Rough Pitch Estimation (Autocorrelation on downsampled signal)
    # Pitch range: 70Hz - 280Hz
    min_lag = int(sample_rate / 280.0)
    max_lag = int(sample_rate / 70.0)
    best_lag = min_lag
    best_corr = -1.0

    # Test lags on a 1024 sample window
    sub_window = float_samples[:min(len(float_samples), 2048)]
    for lag in range(min_lag, min(max_lag, len(sub_window) // 2), 2):
        corr = sum(sub_window[i] * sub_window[i + lag] for i in range(len(sub_window) - lag))
        if corr > best_corr:
            best_corr = corr
            best_lag = lag

    pitch_hz = sample_rate / max(best_lag, 1)

    # 6. Formant Ratios (Lower vs Mid vs Upper vocal energy)
    low_vocal = sum(normalized_bands[0:10])   # 80Hz - 400Hz (Chest resonance & F0)
    mid_vocal = sum(normalized_bands[10:22])  # 400Hz - 1600Hz (Vowel formants F1/F2)
    high_vocal = sum(normalized_bands[22:32]) # 1600Hz - 3800Hz (Consonants & clarity)

    # Combine into 48-dim feature vector
    features = (
        normalized_bands + # 32 features
        [
            pitch_hz / 300.0,
            spectral_centroid / 32.0,
            zcr_rate * 10.0,
            low_vocal,
            mid_vocal,
            high_vocal,
            rms * 10.0,
        ] # 7 features
    )

    # Pad or slice to exactly 48 dimensions
    while len(features) < 48:
        features.append(0.0)
    features = features[:48]

    # L2 unit normalization
    norm = math.sqrt(sum(v * v for v in features)) + 1e-6
    return [v / norm for v in features]


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two normalized acoustic vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


def is_voiceprint_enrolled() -> bool:
    """Check if creator's voiceprint is currently enrolled on disk."""
    if not os.path.exists(VOICEPRINT_FILE):
        return False
    try:
        with open(VOICEPRINT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return bool(data.get("enrolled") and data.get("voiceprint_vector"))
    except Exception:
        return False


def get_voiceprint_status() -> Dict[str, Any]:
    """Return enrollment details and biometric security status."""
    enrolled = is_voiceprint_enrolled()
    data = {}
    if enrolled:
        try:
            with open(VOICEPRINT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass

    return {
        "enrolled": enrolled,
        "creator": data.get("creator_name", "Muhammad Akmal"),
        "samples_count": data.get("samples_count", 0),
        "enrolled_at": data.get("enrolled_at", None),
        "similarity_threshold": data.get("threshold", DEFAULT_SIMILARITY_THRESHOLD),
        "biometrics_enabled": data.get("biometrics_enabled", True)
    }


def enroll_creator_voice(pcm_bytes: bytes, sample_rate: int = 16000, creator_name: str = "Muhammad Akmal") -> Dict[str, Any]:
    """
    Enroll or update Akmal bhai's reference voiceprint.
    Averages with existing samples for high stability and accuracy.
    """
    new_vec = _extract_acoustic_features(pcm_bytes, sample_rate)
    if sum(abs(v) for v in new_vec) < 0.1:
        return {
            "success": False,
            "error": "Audio signal too quiet or empty. Please speak clearly into the microphone."
        }

    current_data = {}
    if os.path.exists(VOICEPRINT_FILE):
        try:
            with open(VOICEPRINT_FILE, "r", encoding="utf-8") as f:
                current_data = json.load(f)
        except Exception:
            pass

    existing_vec = current_data.get("voiceprint_vector")
    samples_count = current_data.get("samples_count", 0)

    if existing_vec and len(existing_vec) == len(new_vec):
        # Weighted running average
        updated_vec = [
            (existing_vec[i] * samples_count + new_vec[i]) / (samples_count + 1)
            for i in range(len(new_vec))
        ]
        # Re-normalize
        norm = math.sqrt(sum(v * v for v in updated_vec)) + 1e-6
        updated_vec = [v / norm for v in updated_vec]
        samples_count += 1
    else:
        updated_vec = new_vec
        samples_count = 1

    payload = {
        "enrolled": True,
        "creator_name": creator_name,
        "samples_count": samples_count,
        "voiceprint_vector": updated_vec,
        "threshold": DEFAULT_SIMILARITY_THRESHOLD,
        "biometrics_enabled": True,
        "enrolled_at": json.dumps(str(__import__("datetime").datetime.now()))
    }

    try:
        with open(VOICEPRINT_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return {
            "success": True,
            "message": f"Voiceprint successfully enrolled for {creator_name} (Sample #{samples_count}).",
            "samples_count": samples_count
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to save voiceprint: {str(e)}"}


def verify_voice(pcm_bytes: bytes, sample_rate: int = 16000) -> Tuple[bool, float, str]:
    """
    Verify if incoming audio matches enrolled creator voiceprint.
    Returns:
        (is_authorized, similarity_score, message)
    """
    if not is_voiceprint_enrolled():
        # If no voiceprint is enrolled yet, allow with notice
        return True, 1.0, "Voice biometric security active in learning mode (No voiceprint enrolled yet)."

    try:
        with open(VOICEPRINT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return True, 1.0, "Could not read voiceprint; bypassing check."

    if not data.get("biometrics_enabled", True):
        return True, 1.0, "Biometrics bypassed (disabled in settings)."

    target_vec = data.get("voiceprint_vector", [])
    threshold = data.get("threshold", DEFAULT_SIMILARITY_THRESHOLD)

    incoming_vec = _extract_acoustic_features(pcm_bytes, sample_rate)
    similarity = _cosine_similarity(incoming_vec, target_vec)

    if similarity >= threshold:
        return True, similarity, f"Speaker verified as Creator (Confidence: {similarity:.2f})."
    else:
        return False, similarity, f"Voice signature mismatch (Score: {similarity:.2f} < {threshold:.2f}). Access Denied."


def reset_voiceprint() -> bool:
    """Reset / clear enrolled voiceprints."""
    if os.path.exists(VOICEPRINT_FILE):
        try:
            os.remove(VOICEPRINT_FILE)
            return True
        except Exception:
            return False
    return True
