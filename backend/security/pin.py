"""
JARVIS Security Framework: PIN & Passphrase Verification
Phase 3A Component: Salted hash verification and lockout protection for HIGH-risk actions.
"""

import hashlib
import os
import time
from typing import Tuple

# Default salt and hash for initial default PIN '1234'
# Generated with pbkdf2_hmac sha256 with 100,000 iterations
_DEFAULT_SALT = b"jarvis_secure_salt_akmal"
_DEFAULT_PIN_HASH = hashlib.pbkdf2_hmac(
    "sha256", "1234".encode("utf-8"), _DEFAULT_SALT, 100_000
).hex()

_failed_attempts = 0
_lockout_until = 0.0
MAX_FAILED_ATTEMPTS = 3
LOCKOUT_DURATION_SECONDS = 300  # 5 minutes


def _get_current_pin_hash_and_salt() -> Tuple[str, bytes]:
    """Retrieve stored PIN hash and salt from environment or defaults."""
    env_hash = os.getenv("JARVIS_SECURITY_PIN_HASH")
    env_salt = os.getenv("JARVIS_SECURITY_PIN_SALT")
    
    if env_hash and env_salt:
        return env_hash, env_salt.encode("utf-8")
    return _DEFAULT_PIN_HASH, _DEFAULT_SALT


def is_locked_out() -> Tuple[bool, int]:
    """Check if PIN verification is temporarily locked out due to excessive failures."""
    global _lockout_until, _failed_attempts
    now = time.time()
    if now < _lockout_until:
        remaining = int(_lockout_until - now)
        return True, remaining
    if _lockout_until > 0 and now >= _lockout_until:
        # Reset lockout when duration has passed
        _lockout_until = 0.0
        _failed_attempts = 0
    return False, 0


def verify_pin(pin: str) -> Tuple[bool, str]:
    """
    Verify the provided PIN against the salted hash.
    Enforces maximum attempt rate-limits.
    """
    global _failed_attempts, _lockout_until

    locked, remaining = is_locked_out()
    if locked:
        return False, f"Security lock active. Too many failed attempts. Try again in {remaining}s."

    if not pin or not str(pin).strip():
        return False, "Security PIN cannot be empty."

    expected_hash, salt = _get_current_pin_hash_and_salt()
    candidate_hash = hashlib.pbkdf2_hmac(
        "sha256", str(pin).strip().encode("utf-8"), salt, 100_000
    ).hex()

    if candidate_hash == expected_hash:
        _failed_attempts = 0
        return True, "PIN verified successfully."
    else:
        _failed_attempts += 1
        if _failed_attempts >= MAX_FAILED_ATTEMPTS:
            _lockout_until = time.time() + LOCKOUT_DURATION_SECONDS
            return False, f"Incorrect PIN. 3 failed attempts reached. Locked for {LOCKOUT_DURATION_SECONDS // 60} minutes."
        
        remaining_tries = MAX_FAILED_ATTEMPTS - _failed_attempts
        return False, f"Incorrect PIN. {remaining_tries} attempts remaining before temporary lockout."
