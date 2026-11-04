"""
JARVIS Wake Word Detection & Hands-Free Activation Module
Phase 10A Component: Allows continuous background listener to wake JARVIS
upon hearing triggers like "Hey JARVIS", "Suno JARVIS", or "JARVIS".
"""

import os
import re
import json
from typing import Dict, Any, Tuple, Optional

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "wake_word_config.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "enabled": True,
    "keywords": [
        "hey jarvis",
        "jarvis",
        "suno jarvis",
        "hello jarvis",
        "jarvis suno",
        "oye jarvis",
        "ok jarvis"
    ],
    "chime": True,
    "sensitivity": "medium",  # "low", "medium", "high"
    "auto_execute": True      # If command follows wake word in same utterance, execute directly
}

def load_wake_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULT_CONFIG, **data}
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_wake_config(config: Dict[str, Any]) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass

def get_wake_word_status() -> Dict[str, Any]:
    """Retrieve the current wake word configuration and status."""
    return load_wake_config()

def set_wake_word_status(enabled: bool, chime: Optional[bool] = None, sensitivity: Optional[str] = None) -> Dict[str, Any]:
    """Enable or disable hands-free wake word listening."""
    cfg = load_wake_config()
    cfg["enabled"] = bool(enabled)
    if chime is not None:
        cfg["chime"] = bool(chime)
    if sensitivity in ["low", "medium", "high"]:
        cfg["sensitivity"] = sensitivity
    save_wake_config(cfg)
    return cfg

def parse_wake_word(text: str) -> Dict[str, Any]:
    """
    Examine incoming transcript for wake words.
    Returns:
        {
            "detected": bool,
            "wake_word": str or None,
            "command": str,
            "has_command": bool
        }
    """
    if not text:
        return {"detected": False, "wake_word": None, "command": "", "has_command": False}

    cleaned = text.strip()
    lower = cleaned.lower()

    # Regex patterns prioritizing multi-word triggers first
    patterns = [
        (r"^(?:hey|hay|aye|oi|oye|ok|okay|suno|hello|hi|سنو|اوئے|اوے|ہیلو)\s*(?:jarvis|jarvice|jervis|جاروس|جارویس)\b[\s,.:!?-]*", "hey jarvis"),
        (r"^(?:jarvis|jarvice|jervis|جاروس|جارویس)\s*(?:suno|سنو)\b[\s,.:!?-]*", "jarvis suno"),
        (r"^(?:jarvis|jarvice|jervis|جاروس|جارویس)\b[\s,.:!?-]*", "jarvis"),
        (r"\b(?:hey|suno|oye|سنو|اوئے)\s*(?:jarvis|jarvice|jervis|جاروس|جارویس)\b[\s,.:!?-]*", "hey jarvis"),
        (r"\b(?:jarvis|jarvice|jervis|جاروس|جارویس)\b", "jarvis"),
    ]

    for pat, canonical in patterns:
        m = re.search(pat, lower)
        if m:
            start, end = m.span()
            # If wake word is at start, the rest is the command
            if start == 0:
                command = cleaned[end:].strip()
            else:
                # If inside text, take text after the wake word
                command = cleaned[end:].strip()
            
            # Clean leading punctuation from command
            command = re.sub(r"^[\s,.:!?-]+", "", command).strip()

            return {
                "detected": True,
                "wake_word": canonical,
                "command": command,
                "has_command": len(command) > 0
            }

    return {"detected": False, "wake_word": None, "command": cleaned, "has_command": len(cleaned) > 0}
