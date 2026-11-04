"""
Acceptance Tests for Wake Word Engine ("Hey JARVIS", "Suno JARVIS")
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.voice.wake_word import parse_wake_word, get_wake_word_status, set_wake_word_status

def run_wake_word_tests():
    print("=== Testing Wake Word Engine ===")

    # 1. Status & Config
    cfg = get_wake_word_status()
    assert "enabled" in cfg, "Config missing 'enabled'"
    assert "keywords" in cfg, "Config missing 'keywords'"
    print(f" [PASS] Wake Word Config: enabled={cfg['enabled']}, sensitivity={cfg.get('sensitivity')}")

    # 2. Toggle Config
    updated = set_wake_word_status(enabled=True, sensitivity="high", chime=True)
    assert updated["enabled"] is True
    assert updated["sensitivity"] == "high"
    print(" [PASS] Toggle wake word configuration works")

    # 3. Direct wake phrase tests
    test_cases = [
        ("Hey JARVIS", True, "hey jarvis", "", False),
        ("Hey JARVIS open Chrome", True, "hey jarvis", "open Chrome", True),
        ("Suno JARVIS Lahore ka weather batao", True, "hey jarvis", "Lahore ka weather batao", True),
        ("JARVIS suno, git status check karo", True, "jarvis suno", "git status check karo", True),
        ("JARVIS", True, "jarvis", "", False),
        ("Hello JARVIS what is 2 plus 2?", True, "hey jarvis", "what is 2 plus 2?", True),
        ("Tell me what time it is", False, None, "Tell me what time it is", True),
    ]

    for utterance, exp_detected, exp_wake, exp_cmd, exp_has_cmd in test_cases:
        res = parse_wake_word(utterance)
        assert res["detected"] == exp_detected, f"Failed for '{utterance}': expected detected={exp_detected}, got {res['detected']}"
        if exp_detected:
            assert res["command"] == exp_cmd, f"Failed cmd for '{utterance}': expected '{exp_cmd}', got '{res['command']}'"
            assert res["has_command"] == exp_has_cmd
        print(f" [PASS] Parsed: '{utterance}' -> detected={res['detected']}, wake={res['wake_word']}, cmd='{res['command']}'")

    print("=== ALL WAKE WORD TESTS PASSED ===")

if __name__ == "__main__":
    run_wake_word_tests()
