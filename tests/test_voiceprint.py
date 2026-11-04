"""
Unit & Acceptance Tests for JARVIS Voice Biometrics (Speaker Verification)
"""
import os
import sys
import struct
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.security.voiceprint import (
    _extract_acoustic_features,
    _cosine_similarity,
    enroll_creator_voice,
    verify_voice,
    get_voiceprint_status,
    reset_voiceprint,
    VOICEPRINT_FILE
)


def generate_synthetic_pcm(frequency: float, duration_sec: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Generate synthetic 16-bit PCM wave with specific fundamental and harmonics."""
    num_samples = int(sample_rate * duration_sec)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        # Fundamental pitch + 2 harmonics to simulate vocal cords & formant
        val = 0.6 * math.sin(2 * math.pi * frequency * t) + \
              0.3 * math.sin(2 * math.pi * frequency * 2 * t) + \
              0.1 * math.sin(2 * math.pi * frequency * 3 * t)
        samples.append(int(val * 32000))
    return struct.pack(f"<{num_samples}h", *samples)


def run_biometrics_tests():
    print("==================================================")
    print("  RUNNING VOICE BIOMETRICS ACCEPTANCE TESTS")
    print("==================================================")

    # Clean state
    reset_voiceprint()

    # 1. Feature Extraction
    print("\n[Test 1] Acoustic Feature Extraction:")
    pcm_akmal = generate_synthetic_pcm(frequency=125.0) # Typical adult male pitch (Akmal bhai)
    vec1 = _extract_acoustic_features(pcm_akmal)
    assert len(vec1) == 48, f"Feature vector length must be 48, got {len(vec1)}"
    assert any(v > 0 for v in vec1), "Features should not be all zero"
    print("  [PASS] 48-dimensional normalized vocal vector extracted.")

    # 2. Self Similarity
    print("\n[Test 2] Same Speaker Acoustic Self-Similarity:")
    pcm_akmal_sample2 = generate_synthetic_pcm(frequency=127.0) # Akmal speaking slightly higher pitch
    vec2 = _extract_acoustic_features(pcm_akmal_sample2)
    self_sim = _cosine_similarity(vec1, vec2)
    assert self_sim > 0.85, f"Self-similarity should be > 0.85, got {self_sim:.3f}"
    print(f"  [PASS] Same speaker similarity: {self_sim:.3f} (> 0.85)")

    # 3. Imposter / Cross-Speaker Discrimination
    print("\n[Test 3] Unauthorized Speaker Discrimination (Imposter Test):")
    pcm_imposter = generate_synthetic_pcm(frequency=240.0) # Much higher pitch voice (e.g. child or female or high pitch stranger)
    vec_imposter = _extract_acoustic_features(pcm_imposter)
    cross_sim = _cosine_similarity(vec1, vec_imposter)
    assert cross_sim < 0.60, f"Imposter similarity should be < 0.60, got {cross_sim:.3f}"
    print(f"  [PASS] Imposter similarity: {cross_sim:.3f} (< 0.60) -> Strong Separation!")

    # 4. Enrollment & Verification Cycle
    print("\n[Test 4] Voiceprint Enrollment Cycle:")
    res = enroll_creator_voice(pcm_akmal, creator_name="Muhammad Akmal")
    assert res["success"], "Enrollment failed"
    status = get_voiceprint_status()
    assert status["enrolled"] is True, "Status does not reflect enrolled"
    print(f"  [PASS] Enrolled voiceprint: {status['creator']} (Sample count: {status['samples_count']})")

    # 5. Verify Creator Access
    print("\n[Test 5] Access Control: Creator Allowed:")
    auth, score, msg = verify_voice(pcm_akmal_sample2)
    assert auth is True, f"Creator should be authorized! Msg: {msg}"
    print(f"  [PASS] Creator verified: score={score:.2f} -> {msg}")

    # 6. Verify Imposter Rejected
    print("\n[Test 6] Access Control: Imposter Blocked:")
    auth_imp, score_imp, msg_imp = verify_voice(pcm_imposter)
    assert auth_imp is False, f"Imposter should be rejected! Msg: {msg_imp}"
    print(f"  [PASS] Imposter correctly blocked: score={score_imp:.2f} -> {msg_imp}")

    # Cleanup test voiceprint
    reset_voiceprint()
    print("\n==================================================")
    print("  ALL VOICE BIOMETRICS ACCEPTANCE TESTS PASSED!")
    print("==================================================")


if __name__ == "__main__":
    run_biometrics_tests()
