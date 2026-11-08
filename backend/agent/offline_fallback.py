"""
JARVIS Deterministic Offline Fallback & System Engine
Phase 11: Executes operating system commands, volume, files, git, apps,
and system telemetry 100% offline without requiring internet or cloud LLMs.
"""

import datetime
import os
import re
from typing import Any, Dict, Optional, Tuple
from backend.tools.registry import execute_tool


# Quick Roman Urdu marker detection
ROMAN_URDU_WORDS = {
    "karo", "kardo", "kro", "krdo", "kren", "karein", "kijiye", "khol", "kholo", "jao",
    "per", "par", "ke", "ki", "ka", "ko", "se", "hai", "hain", "main", "mein", "mujhe",
    "mera", "meri", "mere", "batao", "btao", "dekho", "dikhao", "kya", "kyun", "kaise",
    "bhai", "acha", "krna", "krta", "kr", "kar", "chahiye", "aap", "hum", "yeh", "woh",
    "suno", "band", "bolo", "abhi", "do", "lagao", "chalao", "kitni", "kitna", "awaz"
}


def _is_urdu(text: str, response_language: str = "auto") -> bool:
    if response_language in ("ur", "hi"):
        return True
    if not text:
        return False
    words = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))
    return len(words.intersection(ROMAN_URDU_WORDS)) >= 1


def _clean(text: str) -> str:
    return re.sub(r"[?.!,;]+$", "", text.strip()).strip()


# ─── 1. App Open/Close ───
APP_MAP = {
    "notepad": "notepad",
    "calc": "calculator",
    "calculator": "calculator",
    "chrome": "chrome",
    "google chrome": "chrome",
    "vscode": "vscode",
    "vs code": "vscode",
    "code": "vscode",
    "cmd": "cmd",
    "terminal": "cmd",
    "command prompt": "cmd",
    "powershell": "powershell",
    "explorer": "explorer",
    "file explorer": "explorer",
    "files": "explorer",
    "settings": "settings",
    "task manager": "taskmgr",
    "taskmgr": "taskmgr",
    "paint": "mspaint",
    "mspaint": "mspaint",
}


def parse_app_command(text: str) -> Optional[Tuple[str, str]]:
    """Returns ('open'|'close', app_name) or None."""
    t = _clean(text).lower()

    # Open patterns
    m_open = re.search(r"^(?:please\s+)?(?:open|launch|start|kholo|chalao|khol\s+do)\s+([a-zA-Z0-9\s]+)$", t)
    if m_open:
        raw = m_open.group(1).strip()
        app = APP_MAP.get(raw, raw)
        return "open", app

    m_open_ur = re.search(r"^([a-zA-Z0-9\s]+)\s+(?:kholo|khol\s+do|open\s+(?:kro|karo|kardo|karein)|chalao)$", t)
    if m_open_ur:
        raw = m_open_ur.group(1).strip()
        app = APP_MAP.get(raw, raw)
        return "open", app

    # Close patterns
    m_close = re.search(r"^(?:please\s+)?(?:close|stop|terminate|band\s+(?:kro|karo|kardo|karein))\s+([a-zA-Z0-9\s]+)$", t)
    if m_close:
        raw = m_close.group(1).strip()
        app = APP_MAP.get(raw, raw)
        return "close", app

    m_close_ur = re.search(r"^([a-zA-Z0-9\s]+)\s+(?:band\s+(?:kro|karo|kardo|karein)|close\s+(?:kro|karo|kardo|karein))$", t)
    if m_close_ur:
        raw = m_close_ur.group(1).strip()
        app = APP_MAP.get(raw, raw)
        return "close", app

    return None


# ─── 2. Volume & Audio ───
def parse_volume_command(text: str) -> Optional[Dict[str, Any]]:
    """Returns args for 'set_system_volume' or None."""
    t = _clean(text).lower()

    # Unmute (Check before mute to avoid substring collision)
    if any(k in t for k in ("unmute karo", "volume unmute", "sound unmute", "unmute audio", "awaz kholo")):
        return {"action": "unmute"}
    if t == "unmute":
        return {"action": "unmute"}

    # Mute
    if any(k in t for k in ("mute karo", "volume mute", "sound mute", "mute audio", "awaz band karo")):
        return {"action": "mute"}
    if t in ("mute", "shant ho jao"):
        return {"action": "mute"}

    # Set specific volume level (0-100)
    m_num = re.search(r"(?:volume|awaz)\s*(?:ko\s*)?(?:set\s+karo\s+|set\s+to\s+|to\s+)?(\d{1,3})(?:\s*%|\s*percent)?", t)
    if not m_num:
        m_num = re.search(r"(\d{1,3})(?:\s*%|\s*percent)?\s*(?:volume|awaz)", t)

    if m_num:
        try:
            level = int(m_num.group(1))
            if 0 <= level <= 100:
                return {"action": "set", "level": level}
        except ValueError:
            pass

    # Volume up / down
    if any(k in t for k in ("volume up", "volume badhao", "awaz badhao", "increase volume")):
        return {"action": "up"}
    if any(k in t for k in ("volume down", "volume kam karo", "awaz kam karo", "decrease volume")):
        return {"action": "down"}

    return None


# ─── 3. System Telemetry & Specs ───
def parse_system_status_command(text: str) -> Optional[str]:
    """Returns tool name ('get_system_status', 'get_open_windows')."""
    t = _clean(text).lower()

    # Open windows
    if any(k in t for k in ("open windows", "khuli hui windows", "running apps", "active windows", "windows dikhao")):
        return "get_open_windows"

    # General system status / battery / hardware / specs
    if any(k in t for k in (
        "battery", "battery kitni hai", "battery status", "charging",
        "specs", "hardware", "ram kitni hai", "cpu kitna hai", "hardware specs",
        "system status", "system check", "pc ka hal", "system kaisa chal raha", "telemetry"
    )):
        return "get_system_status"

    return None


# ─── 4. Power Options ───
def parse_power_command(text: str) -> Optional[str]:
    """Returns 'lock_computer'|'sleep_computer'|'restart_computer'|'shutdown_computer' or None."""
    t = _clean(text).lower()

    if any(k in t for k in ("lock laptop", "lock screen", "laptop lock karo", "screen lock karo", "pc lock karo", "lock computer")):
        return "lock_computer"
    if any(k in t for k in ("sleep laptop", "laptop sleep karo", "pc sleep karo", "laptop sula do", "sleep computer")):
        return "sleep_computer"
    if any(k in t for k in ("restart laptop", "restart pc", "pc restart karo", "laptop restart karo", "restart computer")):
        return "restart_computer"
    if any(k in t for k in ("shutdown laptop", "shutdown pc", "pc band karo", "laptop band karo", "shutdown computer")):
        return "shutdown_computer"

    return None


# ─── 5. Time & Date ───
def parse_time_command(text: str) -> Optional[Dict[str, Any]]:
    """Detect current time or date queries."""
    t = _clean(text).lower()

    # Time queries
    time_triggers = (
        "time kya hua hai", "time kya hai", "kya time hai", "time batao",
        "what time is it", "current time", "what is the time"
    )
    if any(k in t for k in time_triggers):
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p")
        return {"type": "time", "value": time_str}

    # Date queries
    date_triggers = (
        "date kya hai", "aaj kya date hai", "aaj konsi tarikh hai", "tarikh batao",
        "what is the date", "today's date", "current date"
    )
    if any(k in t for k in date_triggers):
        now = datetime.datetime.now()
        date_str = now.strftime("%A, %d %B %Y")
        return {"type": "date", "value": date_str}

    return None


# ─── 6. Developer & Git ───
def parse_git_command(text: str) -> Optional[str]:
    """Returns 'run_git_status' or 'run_git_diff'."""
    t = _clean(text).lower()
    if any(k in t for k in ("git status", "git check", "repo status", "status check karo")):
        return "run_git_status"
    if any(k in t for k in ("git diff", "changes dikhao", "code diff")):
        return "run_git_diff"
    return None


# ─── 7. Screenshot ───
def parse_screenshot_command(text: str) -> bool:
    t = _clean(text).lower()
    return any(k in t for k in ("screenshot", "screen capture", "screen snapshot", "screen lo", "screenshot lo"))


# ─── 8. Creator Dossier & Memories ───
def parse_dossier_query(text: str) -> Optional[str]:
    t = _clean(text).lower()
    if any(k in t for k in ("creator details", "Akmal Sir ki profile", "who created you", "tumhe kisne banaya", "dossier")):
        return "dossier"
    if any(k in t for k in ("memories dikhao", "show memories", "active memories", "yaad kya hai")):
        return "memories"
    return None


# ─── 9. Greetings & Polite Status ───
def parse_greeting(text: str) -> Optional[str]:
    t = _clean(text).lower()
    greetings = ("hello", "hi", "hey jarvis", "suno jarvis", "assalam o alaikum", "slam", "kaise ho", "kya haal hai")
    if any(t == g or t.startswith(g + " ") for g in greetings):
        return "greeting"
    if any(k in t for k in ("tum kaun ho", "who are you", "what are you")):
        return "identity"
    return None


# ======================================================================
# MASTER OFFLINE EXECUTOR
# ======================================================================

def execute_offline_system_command(message: str, response_language: str = "auto") -> Dict[str, Any]:
    """
    Execute natural user commands 100% offline without any external AI model.
    Dispatches directly to native JARVIS tools and returns structured responses.
    """
    is_ur = _is_urdu(message, response_language)

    # 1. App Control
    app_cmd = parse_app_command(message)
    if app_cmd:
        action, app_name = app_cmd
        tool_name = "open_application" if action == "open" else "close_application"
        tool_res = execute_tool(tool_name, {"app_name": app_name})
        spoken = (
            f"Ji Akmal Sir, {app_name} {'open' if action == 'open' else 'close'} kar di hai."
            if is_ur else
            f"Yes sir, {app_name} has been {'opened' if action == 'open' else 'closed'}."
        )
        return {
            "response": tool_res.get("result", {}).get("message") or spoken,
            "spoken_response": spoken,
            "status": "success" if tool_res.get("success") else "error",
            "tool_executed": tool_name,
            "tool_result": tool_res,
            "model": "offline-rule-engine",
            "provider": "offline-deterministic",
            "offline_mode": True,
            "suggestions": ["Calculator kholo", "Volume 50 karo", "Battery status check karo"]
        }

    # 2. Volume Control
    vol_args = parse_volume_command(message)
    if vol_args:
        tool_name = "set_system_volume"
        tool_res = execute_tool(tool_name, vol_args)
        act = vol_args.get("action")
        if act == "set":
            lvl = vol_args.get("level", 50)
            spoken = f"Ji sir, volume {lvl} percent par set kar diya hai." if is_ur else f"Volume set to {lvl} percent."
        elif act == "mute":
            spoken = "Ji sir, audio mute kar di hai." if is_ur else "Audio has been muted."
        elif act == "unmute":
            spoken = "Ji sir, audio unmute kar di hai." if is_ur else "Audio has been unmuted."
        elif act == "up":
            spoken = "Ji sir, volume increase kar diya hai." if is_ur else "Volume increased."
        else:
            spoken = "Ji sir, volume decrease kar diya hai." if is_ur else "Volume decreased."

        return {
            "response": spoken,
            "spoken_response": spoken,
            "status": "success" if tool_res.get("success") else "error",
            "tool_executed": tool_name,
            "tool_result": tool_res,
            "model": "offline-rule-engine",
            "provider": "offline-deterministic",
            "offline_mode": True,
            "suggestions": ["Volume unmute karo", "Notepad open karo", "System status"]
        }

    # 3. System Telemetry / Battery / Specs
    sys_tool = parse_system_status_command(message)
    if sys_tool:
        tool_res = execute_tool(sys_tool, {})
        res_data = tool_res.get("result", {})
        msg_text = res_data.get("message") or tool_res.get("message") or "System status retrieved."
        spoken = (
            "Ji Akmal Sir, system telemetry screen par display kar di hai."
            if is_ur else
            "System telemetry has been retrieved and displayed on your screen."
        )
        return {
            "response": msg_text,
            "spoken_response": spoken,
            "status": "success" if tool_res.get("success") else "error",
            "tool_executed": sys_tool,
            "tool_result": tool_res,
            "model": "offline-rule-engine",
            "provider": "offline-deterministic",
            "offline_mode": True,
            "suggestions": ["Battery status", "Specs dikhao", "Git status check karo"]
        }

    # 4. Power Controls
    pwr_tool = parse_power_command(message)
    if pwr_tool:
        tool_res = execute_tool(pwr_tool, {})
        if tool_res.get("status") == "PENDING_CONFIRMATION":
            spoken = "Ji Akmal Sir, is action ke liye PIN aur confirmation required hai." if is_ur else "Security confirmation required."
            return {
                "response": tool_res.get("message", f"Action '{pwr_tool}' requires confirmation."),
                "spoken_response": spoken,
                "status": "pending_confirmation",
                "requires_pin": tool_res.get("requires_pin", False),
                "confirmation_id": tool_res.get("confirmation_id"),
                "tool_name": pwr_tool,
                "model": "offline-rule-engine",
                "provider": "offline-deterministic",
                "offline_mode": True,
                "suggestions": ["Confirm action", "Cancel action"]
            }

        spoken = (
            f"Ji sir, {pwr_tool.replace('_', ' ')} execute kar diya hai."
            if is_ur else
            f"Executed {pwr_tool.replace('_', ' ')} successfully."
        )
        return {
            "response": spoken,
            "spoken_response": spoken,
            "status": "success" if tool_res.get("success") else "error",
            "tool_executed": pwr_tool,
            "tool_result": tool_res,
            "model": "offline-rule-engine",
            "provider": "offline-deterministic",
            "offline_mode": True,
            "suggestions": ["Lock screen", "Battery status", "Notepad kholo"]
        }

    # 5. Time & Date Queries
    time_info = parse_time_command(message)
    if time_info:
        if time_info["type"] == "time":
            val = time_info["value"]
            reply = f"Is waqt time {val} hai." if is_ur else f"The current time is {val}."
        else:
            val = time_info["value"]
            reply = f"Aaj ki date {val} hai." if is_ur else f"Today's date is {val}."

        return {
            "response": reply,
            "spoken_response": reply,
            "status": "success",
            "tool_executed": "get_current_time",
            "model": "offline-rule-engine",
            "provider": "offline-deterministic",
            "offline_mode": True,
            "suggestions": ["System status", "Battery check karo", "Notepad open karo"]
        }

    # 6. Git Status / Diff
    git_tool = parse_git_command(message)
    if git_tool:
        tool_res = execute_tool(git_tool, {})
        res_data = tool_res.get("result", {})
        diff_str = res_data.get("diff", "")
        status_msg = res_data.get("message", "")
        reply = status_msg
        if git_tool == "run_git_diff" and diff_str:
            reply = f"{status_msg}\n\n```diff\n{diff_str}\n```"

        spoken = (
            "Ji Akmal Sir, git status check kar liya hai."
            if is_ur else
            "Git status verified."
        )
        return {
            "response": reply,
            "spoken_response": spoken,
            "status": "success" if tool_res.get("success") else "error",
            "tool_executed": git_tool,
            "tool_result": tool_res,
            "model": "offline-rule-engine",
            "provider": "offline-deterministic",
            "offline_mode": True,
            "suggestions": ["Git status check karo", "Git diff dikhao", "Notepad kholo"]
        }

    # 7. Screenshot
    if parse_screenshot_command(message):
        tool_res = execute_tool("take_screenshot", {})
        spoken = "Ji Akmal Sir, screenshot capture kar liya hai." if is_ur else "Screenshot captured successfully."
        return {
            "response": tool_res.get("result", {}).get("message") or spoken,
            "spoken_response": spoken,
            "status": "success" if tool_res.get("success") else "error",
            "tool_executed": "take_screenshot",
            "tool_result": tool_res,
            "model": "offline-rule-engine",
            "provider": "offline-deterministic",
            "offline_mode": True,
            "suggestions": ["Open folder", "System status", "Notepad open karo"]
        }

    # 8. Dossier & Memories
    dossier_kind = parse_dossier_query(message)
    if dossier_kind == "dossier":
        from backend.database.vault import get_creator_prompt_summary
        summary = get_creator_prompt_summary()
        reply = (
            f"**Master Creator Digital Dossier**:\n{summary}\n\n"
            "Official Portfolio: https://akmalcode.vercel.app\n"
            "GitHub: https://github.com/AkmalDoghar"
        )
        spoken = "Ji Akmal Sir, aap ka Digital Dossier screen par display kar diya hai." if is_ur else "Master Creator profile displayed."
        return {
            "response": reply,
            "spoken_response": spoken,
            "status": "success",
            "tool_executed": "get_creator_dossier",
            "model": "offline-rule-engine",
            "provider": "offline-deterministic",
            "offline_mode": True,
            "suggestions": ["Portfolio open karo", "GitHub open karo", "Memories dikhao"]
        }
    elif dossier_kind == "memories":
        from backend.database.memory import recall_memories
        mems = recall_memories("", limit=5)
        if mems:
            mem_lines = [f"- **{m.get('title', 'Memory')}**: {m.get('content', '')}" for m in mems]
            reply = "### Active Long-Term Memories:\n" + "\n".join(mem_lines)
        else:
            reply = "Filhal koi long-term memory store nahi hai." if is_ur else "No long-term memories currently stored."

        spoken = "Ji Akmal Sir, long term memories screen par display kar di hain." if is_ur else "Long term memories displayed."
        return {
            "response": reply,
            "spoken_response": spoken,
            "status": "success",
            "tool_executed": "recall_memories",
            "model": "offline-rule-engine",
            "provider": "offline-deterministic",
            "offline_mode": True,
            "suggestions": ["Creator details", "System status", "Notepad kholo"]
        }

    # 9. Greeting / Identity
    greet = parse_greeting(message)
    if greet:
        if greet == "identity":
            reply = (
                "Main JARVIS hoon—Muhammad Akmal (Akmal Sir) ka Autonomous Personal AI Operating System. "
                "Main aap ke Windows system controls, developer workflows aur automation ko handle karta hoon."
                if is_ur else
                "I am JARVIS—an Autonomous Personal AI Operating System architected for Muhammad Akmal. "
                "I control system tasks, dev workflows, and Windows automation."
            )
        else:
            reply = (
                "Ji Akmal Sir! Main hazir hoon. Filhal Offline Mode mein hoon, tamam system controls (apps, volume, files, git, specs) operational hain. Farmayiye kya hukum hai?"
                if is_ur else
                "Hello sir! JARVIS is online in Offline System Mode. All computer controls (apps, volume, hardware specs, files, git) are fully active. How may I assist you?"
            )
        return {
            "response": reply,
            "spoken_response": reply,
            "status": "success",
            "tool_executed": "greeting",
            "model": "offline-rule-engine",
            "provider": "offline-deterministic",
            "offline_mode": True,
            "suggestions": ["Notepad kholo", "Volume 50 karo", "Battery status", "Git status check karo"]
        }

    # 10. Fallback for Complex / Generative Queries when Offline with No Local LLM
    offline_msg = (
        "Akmal Sir, internet connection filhal offline hai aur local Ollama model active nahi mila. "
        "Tamam system commands (apps open/close, volume, files, git status, hardware specs, screenshot) offline bilkul active hain. "
        "Generative sawalat ya complex coding ke liye internet connect karein ya `ollama run llama3.2` start karein."
        if is_ur else
        "Sir, internet connection is currently offline and no local Ollama instance was detected. "
        "All system commands (applications, volume, hardware specs, git, screenshots) remain 100% operational offline. "
        "For complex generative tasks, please connect to the internet or start a local Ollama model."
    )
    spoken_offline = (
        "Ji Akmal Sir, system offline mode mein hai. System commands active hain, lekin generative sawalat ke liye internet ya Ollama darkar hai."
        if is_ur else
        "System is in offline mode. Local system commands are ready."
    )
    return {
        "response": offline_msg,
        "spoken_response": spoken_offline,
        "status": "offline_mode_active",
        "model": "offline-rule-engine",
        "provider": "offline-deterministic",
        "offline_mode": True,
        "suggestions": ["Notepad kholo", "Volume 50 karo", "Battery status check karo", "Git status check karo"]
    }
