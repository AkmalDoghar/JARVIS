"""
Acceptance Test for JARVIS TTS Voice Upgrade & Roman Urdu Transliteration Engine
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.voice.transliterate import roman_to_urdu, prepare_speech_text


def run_tts_tests():
    print("==================================================")
    print("  RUNNING TTS & TRANSLITERATION ACCEPTANCE TESTS")
    print("==================================================")

    # 1. Roman Urdu conversion
    print("\n[Test 1] Roman Urdu Transliteration:")
    sample_roman = "Ji Akmal bhai, main sun raha hoon. Aap ka kya hukum hai?"
    urdu_script = roman_to_urdu(sample_roman)
    assert "اَکمل" in urdu_script or "اکمل" in urdu_script, f"Akmal missing in: {urdu_script}"
    assert "بھائی" in urdu_script, f"Bhai missing in: {urdu_script}"
    assert "سن" in urdu_script, f"Sun missing in: {urdu_script}"
    print(f"  [PASS] Input:  '{sample_roman}'")
    print(f"  [PASS] Output: '{urdu_script}'")

    # 2. Tech terms in Roman Urdu
    print("\n[Test 2] Tech Loanwords Transliteration:")
    sample_tech = "Jarvis system online hai aur chrome open kar diya hai."
    tech_urdu = roman_to_urdu(sample_tech)
    assert "جاروِس" in tech_urdu or "سسٹم" in tech_urdu, f"Failed: {tech_urdu}"
    print(f"  [PASS] Tech phrase: '{tech_urdu}'")

    # 3. Voice Router
    print("\n[Test 3] Automatic Voice Routing:")
    # Roman Urdu -> ur-PK-AsadNeural
    txt_ur, voice_ur = prepare_speech_text("Ji sir, kaam ho gaya hai.")
    assert voice_ur == "ur-PK-AsadNeural", f"Expected ur-PK-AsadNeural, got {voice_ur}"
    print(f"  [PASS] Roman Urdu routed to '{voice_ur}'")

    # Pure English -> en-US-ChristopherNeural
    txt_en, voice_en = prepare_speech_text("System memory is running at 45 percent.")
    assert voice_en == "en-US-ChristopherNeural", f"Expected en-US-ChristopherNeural, got {voice_en}"
    print(f"  [PASS] English text routed to '{voice_en}'")

    print("\n==================================================")
    print("  ALL TTS UPGRADE ACCEPTANCE TESTS PASSED!")
    print("==================================================")


if __name__ == "__main__":
    run_tts_tests()
