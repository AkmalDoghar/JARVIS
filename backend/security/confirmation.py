"""
JARVIS Security Framework: Single-Use Confirmation Management
Phase 3A Component: Ephemeral confirmation requests with TTL expiration and PIN enforcement.
"""

import time
import uuid
from typing import Dict, Any, Optional, Tuple
from backend.security.risk import RiskLevel
from backend.security.pin import verify_pin


# In-memory store of pending confirmation requests
# Maps confirmation_id -> request dict
_pending_confirmations: Dict[str, Dict[str, Any]] = {}
CONFIRMATION_TTL_SECONDS = 60  # Confirmations expire after 60 seconds


def create_confirmation_request(
    tool_name: str,
    arguments: Dict[str, Any],
    risk_level: RiskLevel,
    description: str
) -> Dict[str, Any]:
    """Create a pending confirmation request that expires after TTL."""
    # Prune expired requests
    cleanup_expired_confirmations()

    confirmation_id = str(uuid.uuid4())
    now = time.time()
    
    req = {
        "confirmation_id": confirmation_id,
        "tool_name": tool_name,
        "arguments": arguments,
        "risk_level": risk_level.value,
        "description": description,
        "created_at": now,
        "expires_at": now + CONFIRMATION_TTL_SECONDS,
        "requires_pin": (risk_level == RiskLevel.HIGH)
    }
    
    _pending_confirmations[confirmation_id] = req
    return req


def validate_and_consume_confirmation(
    confirmation_id: str,
    pin: Optional[str] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Validate and consume a single-use confirmation token.
    Enforces expiration and PIN check if required.
    """
    cleanup_expired_confirmations()

    if not confirmation_id or confirmation_id not in _pending_confirmations:
        return False, "Invalid or expired confirmation request.", None

    req = _pending_confirmations[confirmation_id]
    
    # Check expiration
    if time.time() > req["expires_at"]:
        del _pending_confirmations[confirmation_id]
        return False, "Confirmation request has expired. Please try the action again.", None

    # Check PIN for HIGH-risk actions
    if req.get("requires_pin"):
        if not pin:
            return False, "This HIGH risk action requires a security PIN.", None
        valid_pin, pin_msg = verify_pin(pin)
        if not valid_pin:
            return False, pin_msg, None

    # Single-use consumption
    del _pending_confirmations[confirmation_id]
    return True, "Confirmation accepted.", req


def cancel_confirmation(confirmation_id: str) -> bool:
    """Cancel and delete a pending confirmation request."""
    if confirmation_id in _pending_confirmations:
        del _pending_confirmations[confirmation_id]
        return True
    return False


def cleanup_expired_confirmations() -> None:
    """Remove expired confirmation requests from memory."""
    now = time.time()
    expired = [cid for cid, req in _pending_confirmations.items() if req["expires_at"] < now]
    for cid in expired:
        del _pending_confirmations[cid]
