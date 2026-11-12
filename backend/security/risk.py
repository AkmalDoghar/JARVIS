"""
JARVIS Security Framework: Risk Classification
Phase 3A Component: Strict categorization of actions into LOW, MEDIUM, and HIGH risk levels.
"""

from enum import Enum
from typing import Dict, Any


class RiskLevel(str, Enum):
    LOW = "LOW"          # Safe actions: can execute automatically
    MEDIUM = "MEDIUM"    # Actions modifying non-critical state: requires user confirmation
    HIGH = "HIGH"        # Sensitive/destructive actions: requires explicit confirmation + PIN


# Mapping of registered tool names to their default risk classification
TOOL_RISK_MAP: Dict[str, RiskLevel] = {
    # System monitoring, safe inspection & routine app/folder control (LOW - Auto Run)
    "get_system_status": RiskLevel.LOW,
    "get_open_windows": RiskLevel.LOW,
    "open_application": RiskLevel.LOW,
    "close_application": RiskLevel.LOW,
    "open_website": RiskLevel.LOW,
    "open_folder": RiskLevel.LOW,
    "close_folder": RiskLevel.LOW,
    "open_file": RiskLevel.LOW,
    "set_system_volume": RiskLevel.LOW,
    "set_system_brightness": RiskLevel.LOW,
    "control_quick_setting": RiskLevel.LOW,
    "open_chrome_profile": RiskLevel.LOW,
    "send_whatsapp_message": RiskLevel.LOW,
    "confirm_send_whatsapp": RiskLevel.LOW,
    "open_whatsapp_web": RiskLevel.LOW,
    "send_whatsapp_web_message": RiskLevel.LOW,
    "confirm_send_whatsapp_web": RiskLevel.LOW,
    "save_contact": RiskLevel.LOW,
    "list_contacts": RiskLevel.LOW,
    "post_whatsapp_status": RiskLevel.LOW,
    "customize_whatsapp_status": RiskLevel.LOW,
    "confirm_post_whatsapp_status": RiskLevel.LOW,
    "delete_whatsapp_status": RiskLevel.LOW,
    "discard_whatsapp_status": RiskLevel.LOW,
    "make_whatsapp_call": RiskLevel.LOW,
    "end_whatsapp_call": RiskLevel.LOW,
    "toggle_whatsapp_call_mute": RiskLevel.LOW,
    # Phase 3C: Timer, Alarm & Reminder tools (all LOW - no side effects)
    "set_timer": RiskLevel.LOW,
    "set_alarm": RiskLevel.LOW,
    "set_reminder": RiskLevel.LOW,
    "list_timers": RiskLevel.LOW,
    "cancel_timer": RiskLevel.LOW,
    # Creator Vault & Identity tools (all LOW)
    "get_creator_info": RiskLevel.LOW,
    "open_creator_link": RiskLevel.LOW,
    "save_creator_thought": RiskLevel.LOW,
    "get_active_projects": RiskLevel.LOW,
    "open_project": RiskLevel.LOW,
    "get_today_focus": RiskLevel.LOW,
    "add_today_focus_task": RiskLevel.LOW,
    "get_creator_accounts_info": RiskLevel.LOW,
    "inspect_creator_account": RiskLevel.LOW,
    "draft_social_post": RiskLevel.LOW,
    "publish_social_post": RiskLevel.LOW,
    "get_creator_dossier": RiskLevel.LOW,
    "sync_creator_online_presence": RiskLevel.LOW,
    
    # Phase 4: Coding & File Tools
    # Read-only / Inspection (LOW - Auto Run)
    "read_file": RiskLevel.LOW,
    "inspect_project": RiskLevel.LOW,
    "list_directory_files": RiskLevel.LOW,
    "search_codebase": RiskLevel.LOW,
    "run_git_status": RiskLevel.LOW,
    "run_git_diff": RiskLevel.LOW,
    "explain_code_error": RiskLevel.LOW,
    "create_file": RiskLevel.LOW,
    "create_folder": RiskLevel.LOW,
    "modify_file": RiskLevel.LOW,
    "run_dev_tests": RiskLevel.LOW,
    "open_in_vscode": RiskLevel.LOW,
    "open_file_in_browser": RiskLevel.LOW,
    "start_local_server": RiskLevel.LOW,
    "open_in_terminal": RiskLevel.LOW,

    
    # Phase 5: Web Intelligence Tools (LOW - Read-only Internet Information)
    "search_web": RiskLevel.LOW,
    "get_weather": RiskLevel.LOW,
    "read_webpage": RiskLevel.LOW,
    "play_youtube_video": RiskLevel.LOW,
    "analyze_website": RiskLevel.LOW,
    "list_google_accounts": RiskLevel.LOW,
    "open_chrome_profile": RiskLevel.LOW,
    "list_chrome_bookmarks": RiskLevel.LOW,
    "search_chrome_history": RiskLevel.LOW,
    "open_smart_website": RiskLevel.LOW,

    # Phase 6B: Long-Term Memory Matrix Tools
    "remember_information": RiskLevel.LOW,
    "recall_memories": RiskLevel.LOW,
    "forget_memory": RiskLevel.LOW,

    # Phase 7: Desktop Vision & Screenshot Diagnostics Tools (LOW - Safe on-demand observation)
    "inspect_screen": RiskLevel.LOW,
    "capture_screenshot": RiskLevel.LOW,

    # Phase 8: Autonomous Multi-Step Agent Tools (LOW - Steps gated individually)
    "create_agent_plan": RiskLevel.LOW,
    "execute_agent_mission": RiskLevel.LOW,
    "stop_agent_mission": RiskLevel.LOW,
    "autonomous_browser_agent": RiskLevel.LOW,
    
    # State modification & desktop locking (MEDIUM - Confirmation)
    "lock_computer": RiskLevel.MEDIUM,
    "sleep_computer": RiskLevel.MEDIUM,
    
    # Critical power & destructive actions (HIGH - Requires PIN)
    "shutdown_computer": RiskLevel.HIGH,
    "restart_computer": RiskLevel.HIGH,
    "delete_file_or_folder": RiskLevel.HIGH,
}


def get_tool_risk(tool_name: str, args: Dict[str, Any] = None) -> RiskLevel:
    """Return the risk level for a tool execution."""
    if tool_name == "forget_memory" and args and args.get("forget_all"):
        return RiskLevel.HIGH
    return TOOL_RISK_MAP.get(tool_name, RiskLevel.HIGH)
