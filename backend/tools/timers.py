"""
JARVIS Timer, Alarm & Reminder Tools
Phase 3C Component: Local countdown timers, alarms (time-of-day), and reminders.
All stored in-memory (survive session, not restart). Fires a desktop toast notification
when a timer/alarm/reminder fires while JARVIS is running.
Works 100% offline.
"""

import re
import time
import threading
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


# ──────────────────────────────────────────────
# Internal state (in-memory for Phase 3)
# Phase 6 will move this to SQLite.
# ──────────────────────────────────────────────
_timers: Dict[str, Dict[str, Any]] = {}      # id → timer dict
_alarms: Dict[str, Dict[str, Any]] = {}      # id → alarm dict
_reminders: Dict[str, Dict[str, Any]] = {}   # id → reminder dict
_lock = threading.Lock()


# ──────────────────────────────────────────────
# Windows Toast Notification helper (offline-safe)
# ──────────────────────────────────────────────
def _toast(title: str, message: str) -> None:
    """Fire a Windows toast notification (non-blocking). Falls back silently."""
    try:
        from plyer import notification  # type: ignore
        notification.notify(
            title=title,
            message=message,
            app_name="JARVIS",
            timeout=10,
        )
    except Exception:
        pass
    # Always print to console as a fallback
    print(f"\n🔔 [JARVIS ALERT] {title}: {message}\n")


# ──────────────────────────────────────────────
# Parse helpers
# ──────────────────────────────────────────────
URDU_NUMBERS: Dict[str, int] = {
    "ek": 1, "aik": 1, "one": 1,
    "do": 2, "two": 2,
    "teen": 3, "three": 3,
    "char": 4, "chaar": 4, "four": 4,
    "paanch": 5, "panch": 5, "five": 5,
    "chhe": 6, "chhey": 6, "che": 6, "six": 6,
    "saat": 7, "seven": 7,
    "aath": 8, "eight": 8,
    "nau": 9, "nine": 9,
    "dus": 10, "das": 10, "ten": 10,
    "gyarah": 11, "barah": 12, "terah": 13, "chaudah": 14,
    "pandrah": 15, "fifteen": 15,
    "solah": 16, "satrah": 17, "atharah": 18, "unnees": 19,
    "bees": 20, "twenty": 20,
    "pachees": 25, "twenty five": 25,
    "tees": 30, "thirty": 30,
    "paintees": 35, "thirty five": 35,
    "chalees": 40, "forty": 40,
    "pentalis": 45, "forty five": 45,
    "pachas": 50, "fifty": 50,
}


def _parse_duration_seconds(text: str) -> Optional[int]:
    """
    Parse natural-language duration strings into total seconds.
    Supports English, Urdu/Roman Urdu, colon notations, and direct numeric strings.
    Examples:
    - '5 minutes', '30 seconds', '2 hours', '1 hour 30 minutes', '90s', '5m', '2h'
    - '10 minute', '2 ghante', 'aadha ghanta', 'dedh ghanta', 'dhai minute'
    - 'paanch minute', 'dus second'
    - '05:00', '01:30:00'
    - Direct integer '60', '120'
    """
    if not text:
        return None
    raw = text.lower().strip()

    # Direct integer
    if raw.isdigit():
        val = int(raw)
        return val if val > 0 else None

    # Colon formats: HH:MM:SS
    m_hms = re.match(r"^(\d{1,2}):(\d{2}):(\d{2})$", raw)
    if m_hms:
        return int(m_hms.group(1)) * 3600 + int(m_hms.group(2)) * 60 + int(m_hms.group(3))

    # Colon formats: MM:SS
    m_ms = re.match(r"^(\d{1,2}):(\d{2})$", raw)
    if m_ms:
        return int(m_ms.group(1)) * 60 + int(m_ms.group(2))

    # Special Urdu phrases
    if any(k in raw for k in ["aadha ghanta", "adhe ghante", "aadhey ghante", "half hour", "half an hour"]):
        return 1800
    if any(k in raw for k in ["dedh ghanta", "dedh ghante"]):
        return 5400
    if any(k in raw for k in ["dhai ghante", "dhai ghanta"]):
        return 9000
    if any(k in raw for k in ["dedh minute", "dedh minat"]):
        return 90
    if any(k in raw for k in ["dhai minute", "dhai minat"]):
        return 150

    # Replace word numbers with digits
    normalized = raw
    for word, num in sorted(URDU_NUMBERS.items(), key=lambda x: -len(x[0])):
        normalized = re.sub(rf"\b{word}\b", str(num), normalized)

    total = 0
    found = False

    patterns = [
        (r"(\d+)\s*(?:hours?|hrs?|ghant[aey]|ghanto|h)\b", 3600),
        (r"(\d+)\s*(?:minutes?|mins?|minat|minto|mintu|m)\b", 60),
        (r"(\d+)\s*(?:seconds?|secs?|sekand|secondo|s)\b", 1),
    ]
    for pattern, multiplier in patterns:
        m = re.search(pattern, normalized)
        if m:
            total += int(m.group(1)) * multiplier
            found = True

    return total if found and total > 0 else None


def _parse_alarm_time(text: str) -> Optional[datetime]:
    """
    Parse a time-of-day string into a today/tomorrow datetime.
    Supports: '7:30 am', '15:00', '9 pm', 'noon', 'midnight'.
    """
    text = text.lower().strip()

    special = {"noon": (12, 0), "midnight": (0, 0)}
    if text in special:
        h, m = special[text]
        target = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)
        if target <= datetime.now():
            target += timedelta(days=1)
        return target

    # Patterns: "7:30 am", "07:30", "9 pm"
    patterns = [
        r"(\d{1,2}):(\d{2})\s*(am|pm)?",
        r"(\d{1,2})\s*(am|pm)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            groups = m.groups()
            if len(groups) == 3:          # HH:MM [am/pm]
                hour, minute, meridiem = int(groups[0]), int(groups[1]), groups[2]
            else:                          # H am/pm
                hour, minute, meridiem = int(groups[0]), 0, groups[1]

            if meridiem == "pm" and hour != 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0

            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                continue

            target = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= datetime.now():
                target += timedelta(days=1)
            return target

    return None


# ──────────────────────────────────────────────
# Timer (countdown)
# ──────────────────────────────────────────────
def set_timer(duration: str = "", label: str = "", seconds: Optional[int] = None) -> Dict[str, Any]:
    """
    Start a countdown timer.
    duration: e.g. '5 minutes', '30 seconds', '1 hour', '10 minute', 'aadha ghanta'
    label: optional custom label for this timer (e.g. 'Chai', 'Pomodoro', 'Meeting')
    seconds: direct integer seconds from UI (e.g. 300)
    """
    sec = None
    if seconds is not None and isinstance(seconds, (int, float)) and seconds > 0:
        sec = int(seconds)
    elif duration:
        sec = _parse_duration_seconds(duration)

    if sec is None or sec <= 0:
        return {
            "success": False,
            "error": f"Could not understand duration '{duration}'. Try '5 minutes', '30 seconds', '10 minute', or direct seconds."
        }

    timer_id = str(uuid.uuid4())[:8]
    label = label.strip() or f"Timer {timer_id}"
    fire_at = time.time() + sec
    human_time = _seconds_to_human(sec)

    with _lock:
        _timers[timer_id] = {
            "id": timer_id,
            "label": label,
            "duration_seconds": sec,
            "fire_at": fire_at,
            "fired": False,
            "cancelled": False,
        }

    # Background thread to fire notification + voice alert
    def _run():
        remaining = fire_at - time.time()
        if remaining > 0:
            time.sleep(remaining)
        with _lock:
            entry = _timers.get(timer_id)
            if not entry or entry["cancelled"]:
                return
            entry["fired"] = True

        _toast("⏰ Timer Done!", f"'{label}' — {human_time} is up!")
        try:
            from backend.voice.text_to_speech import speak
            threading.Thread(
                target=speak,
                args=(f"Sir, aap ka timer '{label}' pura ho gaya hai.",),
                daemon=True
            ).start()
        except Exception:
            pass

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    return {
        "success": True,
        "timer_id": timer_id,
        "label": label,
        "duration_seconds": sec,
        "fire_at": fire_at,
        "message": f"Timer '{label}' set for {human_time}. I will notify you when it's done."
    }


def cancel_any(item_id: str) -> Dict[str, Any]:
    """Cancel any timer, alarm, or reminder by ID."""
    with _lock:
        if item_id in _timers:
            _timers[item_id]["cancelled"] = True
            return {"success": True, "message": f"Timer '{_timers[item_id]['label']}' has been cancelled."}
        if item_id in _alarms:
            _alarms[item_id]["cancelled"] = True
            return {"success": True, "message": f"Alarm '{_alarms[item_id]['label']}' has been cancelled."}
        if item_id in _reminders:
            _reminders[item_id]["cancelled"] = True
            return {"success": True, "message": f"Reminder '{_reminders[item_id]['message']}' has been cancelled."}
    return {"success": False, "error": f"Item '{item_id}' not found."}


def cancel_timer(timer_id: str) -> Dict[str, Any]:
    """Cancel a running timer by ID."""
    return cancel_any(timer_id)


def list_timers() -> Dict[str, Any]:
    """List all active (not-fired, not-cancelled) timers with exact timing metadata."""
    now = time.time()
    with _lock:
        active = [
            {
                "id": t["id"],
                "label": t["label"],
                "duration_seconds": t["duration_seconds"],
                "fire_at": t["fire_at"],
                "remaining_seconds": max(0, int(t["fire_at"] - now)),
                "remaining": _seconds_to_human(max(0, int(t["fire_at"] - now))),
            }
            for t in _timers.values()
            if not t["fired"] and not t["cancelled"]
        ]
    return {
        "success": True,
        "timers": active,
        "count": len(active),
        "message": f"{len(active)} active timer(s)." if active else "No active timers."
    }


# ──────────────────────────────────────────────
# Alarm (time-of-day)
# ──────────────────────────────────────────────
def set_alarm(alarm_time: str, label: str = "") -> Dict[str, Any]:
    """
    Set an alarm for a specific time of day.
    alarm_time: e.g. '7:30 am', '15:00', '9 pm', 'noon'
    """
    target = _parse_alarm_time(alarm_time)
    if target is None:
        return {
            "success": False,
            "error": f"Could not parse alarm time '{alarm_time}'. Try '7:30 am', '15:00', or '9 pm'."
        }

    alarm_id = str(uuid.uuid4())[:8]
    label = label.strip() or f"Alarm at {target.strftime('%I:%M %p')}"
    fire_at = target.timestamp()

    with _lock:
        _alarms[alarm_id] = {
            "id": alarm_id,
            "label": label,
            "fire_at": fire_at,
            "fire_at_str": target.strftime("%I:%M %p"),
            "fired": False,
            "cancelled": False,
        }

    def _run():
        remaining = fire_at - time.time()
        if remaining > 0:
            time.sleep(remaining)
        with _lock:
            entry = _alarms.get(alarm_id)
            if entry and not entry["cancelled"]:
                entry["fired"] = True
        _toast("🔔 JARVIS Alarm!", f"'{label}' — It's {target.strftime('%I:%M %p')}!")

    threading.Thread(target=_run, daemon=True).start()

    return {
        "success": True,
        "alarm_id": alarm_id,
        "label": label,
        "fires_at": target.strftime("%I:%M %p"),
        "message": f"Alarm '{label}' set for {target.strftime('%I:%M %p')}."
    }


def cancel_alarm(alarm_id: str) -> Dict[str, Any]:
    """Cancel an alarm by ID."""
    with _lock:
        entry = _alarms.get(alarm_id)
        if not entry:
            return {"success": False, "error": f"Alarm '{alarm_id}' not found."}
        entry["cancelled"] = True
    return {"success": True, "message": f"Alarm '{entry['label']}' has been cancelled."}


def list_alarms() -> Dict[str, Any]:
    """List all upcoming (not-fired, not-cancelled) alarms."""
    with _lock:
        upcoming = [
            {
                "id": a["id"],
                "label": a["label"],
                "fires_at": a["fire_at_str"],
            }
            for a in _alarms.values()
            if not a["fired"] and not a["cancelled"]
        ]
    return {
        "success": True,
        "alarms": upcoming,
        "count": len(upcoming),
        "message": f"{len(upcoming)} alarm(s) scheduled." if upcoming else "No active alarms."
    }


# ──────────────────────────────────────────────
# Reminder (text message at a time/after delay)
# ──────────────────────────────────────────────
def set_reminder(message: str, when: str) -> Dict[str, Any]:
    """
    Set a reminder for a specific message.
    when: time-of-day ('5 pm', '14:30') OR duration ('in 30 minutes', '2 hours')
    """
    # Try duration first
    seconds = _parse_duration_seconds(when)
    if seconds:
        fire_at = time.time() + seconds
        fire_at_str = datetime.fromtimestamp(fire_at).strftime("%I:%M %p")
    else:
        target = _parse_alarm_time(when)
        if target is None:
            return {
                "success": False,
                "error": f"Could not parse when='{when}'. Try '5 pm', '14:30', or '30 minutes'."
            }
        fire_at = target.timestamp()
        fire_at_str = target.strftime("%I:%M %p")

    rem_id = str(uuid.uuid4())[:8]
    with _lock:
        _reminders[rem_id] = {
            "id": rem_id,
            "message": message,
            "fire_at": fire_at,
            "fire_at_str": fire_at_str,
            "fired": False,
            "cancelled": False,
        }

    def _run():
        remaining = fire_at - time.time()
        if remaining > 0:
            time.sleep(remaining)
        with _lock:
            entry = _reminders.get(rem_id)
            if entry and not entry["cancelled"]:
                entry["fired"] = True
        _toast("📌 JARVIS Reminder", message)

    threading.Thread(target=_run, daemon=True).start()

    return {
        "success": True,
        "reminder_id": rem_id,
        "message_text": message,
        "fires_at": fire_at_str,
        "message": f"Reminder set: '{message}' at {fire_at_str}."
    }


def cancel_reminder(reminder_id: str) -> Dict[str, Any]:
    """Cancel a reminder by ID."""
    with _lock:
        entry = _reminders.get(reminder_id)
        if not entry:
            return {"success": False, "error": f"Reminder '{reminder_id}' not found."}
        entry["cancelled"] = True
    return {"success": True, "message": f"Reminder cancelled: '{entry['message']}'."}


def list_reminders() -> Dict[str, Any]:
    """List all pending (not-fired, not-cancelled) reminders."""
    with _lock:
        pending = [
            {
                "id": r["id"],
                "message": r["message"],
                "fires_at": r["fire_at_str"],
            }
            for r in _reminders.values()
            if not r["fired"] and not r["cancelled"]
        ]
    return {
        "success": True,
        "reminders": pending,
        "count": len(pending),
        "message": f"{len(pending)} reminder(s) pending." if pending else "No pending reminders."
    }


def get_all_active() -> Dict[str, Any]:
    """Return a combined summary of all active timers, alarms, and reminders."""
    t = list_timers()
    a = list_alarms()
    r = list_reminders()
    total = t["count"] + a["count"] + r["count"]
    return {
        "success": True,
        "timers": t["timers"],
        "alarms": a["alarms"],
        "reminders": r["reminders"],
        "total": total,
        "message": f"{total} item(s) scheduled." if total else "No timers, alarms or reminders active."
    }


# ──────────────────────────────────────────────
# Utility
# ──────────────────────────────────────────────
def _seconds_to_human(sec: int) -> str:
    if sec <= 0:
        return "0 seconds"
    parts = []
    if sec >= 3600:
        h = sec // 3600
        parts.append(f"{h} hour{'s' if h != 1 else ''}")
        sec %= 3600
    if sec >= 60:
        m = sec // 60
        parts.append(f"{m} minute{'s' if m != 1 else ''}")
        sec %= 60
    if sec > 0:
        parts.append(f"{sec} second{'s' if sec != 1 else ''}")
    return ", ".join(parts)
