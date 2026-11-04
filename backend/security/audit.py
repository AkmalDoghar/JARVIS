"""
JARVIS Security Framework: Structured Audit Logging
Phase 3A Component: Permanent audit trail for every tool invocation, risk check, and execution result.
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
AUDIT_LOG_FILE = os.path.join(LOGS_DIR, "audit.log")

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)


def log_tool_call(
    tool_name: str,
    arguments: Dict[str, Any],
    risk_level: str,
    confirmed: bool,
    status: str,
    result_summary: str = "",
    error: Optional[str] = None
) -> Dict[str, Any]:
    """Record a tool invocation into the persistent audit trail."""
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "unix_time": time.time(),
        "tool_name": tool_name,
        "arguments": arguments,
        "risk_level": risk_level,
        "confirmed": confirmed,
        "status": status,  # "SUCCESS", "DENIED", "FAILED", "PENDING_CONFIRMATION"
        "result_summary": str(result_summary)[:500],
        "error": error
    }

    try:
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[AUDIT LOG ERROR] Failed to write audit log: {e}")

    return entry


def get_recent_audit_logs(limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieve recent audit log entries for display in dashboard."""
    if not os.path.exists(AUDIT_LOG_FILE):
        return []

    entries = []
    try:
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if line.strip():
                    try:
                        entries.append(json.loads(line))
                        if len(entries) >= limit:
                            break
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"[AUDIT LOG ERROR] Failed to read audit log: {e}")

    return entries
