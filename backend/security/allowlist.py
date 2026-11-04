"""
JARVIS Security Framework: Allowlist & Path Safety Rules
Phase 3A Component: Strict validation of applications, folders, and system commands.
"""

import os
import re
import json
import subprocess
from typing import Dict, Optional, List, Tuple


# Allowlist of approved applications with executable mappings and aliases
APPROVED_APPLICATIONS: Dict[str, Dict[str, str]] = {
    "chrome": {
        "name": "Google Chrome",
        "command": "chrome",
        "process_name": "chrome.exe",
    },
    "google chrome": {
        "name": "Google Chrome",
        "command": "chrome",
        "process_name": "chrome.exe",
    },
    "code": {
        "name": "Visual Studio Code",
        "command": "code",
        "process_name": "Code.exe",
    },
    "vscode": {
        "name": "Visual Studio Code",
        "command": "code",
        "process_name": "Code.exe",
    },
    "vs code": {
        "name": "Visual Studio Code",
        "command": "code",
        "process_name": "Code.exe",
    },
    "antigravity": {
        "name": "Antigravity",
        "command": "antigravity",
        "process_name": "antigravity.exe"
    },      
    "notion": {
        "name": "Notion",
        "command": "notion",
        "process_name": "notion.exe"
    },
    "notepad": {
        "name": "Notepad",
        "command": "notepad.exe",
        "process_name": "notepad.exe",
    },
    "calculator": {
        "name": "Windows Calculator",
        "command": "calc.exe",
        "process_name": "CalculatorApp.exe",
    },
    "calc": {
        "name": "Windows Calculator",
        "command": "calc.exe",
        "process_name": "CalculatorApp.exe",
    },
    "explorer": {
        "name": "File Explorer",
        "command": "explorer.exe",
        "process_name": "explorer.exe",
    },
    "file explorer": {
        "name": "File Explorer",
        "command": "explorer.exe",
        "process_name": "explorer.exe",
    },
    "edge": {
        "name": "Microsoft Edge",
        "command": "msedge",
        "process_name": "msedge.exe",
    },
    "terminal": {
        "name": "Windows Terminal",
        "command": "wt.exe",
        "process_name": "WindowsTerminal.exe",
    },
    "cmd": {
        "name": "Command Prompt",
        "command": "cmd.exe",
        "process_name": "cmd.exe",
    },
    "powershell": {
        "name": "PowerShell",
        "command": "powershell.exe",
        "process_name": "powershell.exe",
    },
    "mongodb": {
        "name": "MongoDB Compass",
        "command": os.path.expanduser(r"~\AppData\Local\MongoDBCompass\MongoDBCompass.exe"),
        "process_name": "MongoDBCompass.exe",
    },
    "mongodb compass": {
        "name": "MongoDB Compass",
        "command": os.path.expanduser(r"~\AppData\Local\MongoDBCompass\MongoDBCompass.exe"),
        "process_name": "MongoDBCompass.exe",
    },
    "compass": {
        "name": "MongoDB Compass",
        "command": os.path.expanduser(r"~\AppData\Local\MongoDBCompass\MongoDBCompass.exe"),
        "process_name": "MongoDBCompass.exe",
    },
    "github desktop": {
        "name": "GitHub Desktop",
        "command": 'explorer.exe "shell:AppsFolder\\com.squirrel.GitHubDesktop.GitHubDesktop"',
        "process_name": "GitHubDesktop.exe",
    },
    "github": {
        "name": "GitHub Desktop",
        "command": 'explorer.exe "shell:AppsFolder\\com.squirrel.GitHubDesktop.GitHubDesktop"',
        "process_name": "GitHubDesktop.exe",
    },
    "whatsapp": {
        "name": "WhatsApp",
        "command": 'explorer.exe "shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"',
        "process_name": "WhatsApp.exe",
    },
    "whatsapp desktop": {
        "name": "WhatsApp",
        "command": 'explorer.exe "shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"',
        "process_name": "WhatsApp.exe",
    },
    "whatsapp web": {
        "name": "WhatsApp Web",
        "command": "https://web.whatsapp.com",
        "process_name": "chrome.exe",
    },
    "paint": {
        "name": "Paint",
        "command": "mspaint.exe",
        "process_name": "mspaint.exe",
    },
    "wordpad": {
        "name": "WordPad",
        "command": "wordpad.exe",
        "process_name": "wordpad.exe",
    },
    "camera": {
        "name": "Camera",
        "command": 'explorer.exe "shell:AppsFolder\\Microsoft.WindowsCamera_8wekyb3d8bbwe!App"',
        "process_name": "WindowsCamera.exe",
    },
    "clock": {
        "name": "Clock",
        "command": 'explorer.exe "shell:AppsFolder\\Microsoft.WindowsAlarms_8wekyb3d8bbwe!App"',
        "process_name": "Time.exe",
    },
    "calendar": {
        "name": "Calendar",
        "command": 'explorer.exe "shell:AppsFolder\\microsoft.windowscommunicationsapps_8wekyb3d8bbwe!microsoft.windowslive.calendar"',
        "process_name": "HxCalendarAppImm.exe",
    },
    "android studio": {
        "name": "Android Studio",
        "command": 'explorer.exe "shell:AppsFolder\\{6D809377-6AF0-444B-8957-A3773F02200E}\\Android\\Android Studio\\bin\\studio64.exe"',
        "process_name": "studio64.exe",
    },
}

# Blocked system directories that JARVIS must never alter or open destructively
BLOCKED_SYSTEM_PATHS: List[str] = [
    r"c:\windows",
    r"c:\windows\system32",
    r"c:\windows\syswow64",
    r"c:\program files\windowsapps",
    r"c:\$recycle.bin",
    r"c:\recovery",
]

# Destructive shell command patterns that are blocked outright
DESTRUCTIVE_PATTERNS: List[str] = [
    r"\bformat\b",
    r"\bdel\s+/[sS]\b",
    r"\brmdir\s+/[sS]\b",
    r"\brd\s+/[sS]\b",
    r"\bdiskpart\b",
    r"\breg\s+delete\b",
    r":\(\)\s*\{",  # Fork bomb
]

import winreg
import shutil
import difflib
import time

# Unified in-memory cache of all installed Windows applications
_INSTALLED_APPS_CACHE: Optional[Dict[str, Dict[str, str]]] = None
_LAST_SCAN_TIME: float = 0.0


def scan_all_installed_apps(force_refresh: bool = False) -> Dict[str, Dict[str, str]]:
    """
    Dynamically scan all installed applications across the entire Windows system:
    1. Start Menu shortcuts (.lnk in ProgramData and AppData)
    2. Desktop shortcuts (.lnk in Public and User Desktop)
    3. Windows Registry App Paths (HKLM and HKCU)
    4. Modern Windows Store / UWP apps (Get-StartApps)
    5. Curated approved application shortcuts
    """
    global _INSTALLED_APPS_CACHE, _LAST_SCAN_TIME

    # Return cached index if valid and fresh (< 5 minutes old) unless force_refresh is requested
    if not force_refresh and _INSTALLED_APPS_CACHE is not None and (time.time() - _LAST_SCAN_TIME < 300):
        return _INSTALLED_APPS_CACHE

    apps: Dict[str, Dict[str, str]] = {}

    # 1. Start Menu & Desktop Shortcuts (.lnk) - fast pure Python
    shortcut_dirs = [
        os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%PUBLIC%\Desktop"),
        os.path.expandvars(r"%USERPROFILE%\Desktop"),
        os.path.expandvars(r"%USERPROFILE%\OneDrive\Desktop"),
    ]
    for sdir in shortcut_dirs:
        if os.path.exists(sdir):
            for root, _, files in os.walk(sdir):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        name = os.path.splitext(f)[0].strip()
                        full_path = os.path.join(root, f)
                        key = name.lower()
                        if key not in apps:
                            apps[key] = {
                                "name": name,
                                "command": full_path,
                                "process_name": f"{name}.exe",
                                "type": "shortcut",
                            }

    # 2. Windows Registry App Paths (covers Win32 installed software)
    for root_key in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(root_key, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths") as key:
                num_subkeys = winreg.QueryInfoKey(key)[0]
                for i in range(num_subkeys):
                    try:
                        kname = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, kname) as app_key:
                            val, _ = winreg.QueryValueEx(app_key, "")
                            if val and os.path.exists(val):
                                clean_name = kname.replace(".exe", "").strip()
                                key_str = clean_name.lower()
                                if key_str not in apps:
                                    apps[key_str] = {
                                        "name": clean_name,
                                        "command": val,
                                        "process_name": kname if kname.endswith(".exe") else f"{kname}.exe",
                                        "type": "registry",
                                    }
                    except Exception:
                        pass
        except Exception:
            pass

    # 3. Modern UWP Store Apps & System apps via PowerShell Get-StartApps
    try:
        cmd = ["powershell", "-NoProfile", "-Command", "Get-StartApps | ConvertTo-Json -Compress"]
        out = subprocess.check_output(cmd, text=True, encoding="utf-8", timeout=5)
        raw = json.loads(out)
        if isinstance(raw, dict):
            raw = [raw]
        for item in raw:
            name = item.get("Name", "").strip()
            appid = item.get("AppID", "").strip()
            if name and appid:
                key_str = name.lower()
                if key_str not in apps:
                    apps[key_str] = {
                        "name": name,
                        "command": f"shell:AppsFolder\\{appid}",
                        "process_name": f"{name}.exe",
                        "app_id": appid,
                        "type": "uwp",
                    }
    except Exception:
        pass

    _INSTALLED_APPS_CACHE = apps
    _LAST_SCAN_TIME = time.time()
    return apps


def get_installed_windows_apps() -> List[Dict[str, str]]:
    """Return a flat list of all indexed applications for backwards compatibility."""
    apps_dict = scan_all_installed_apps()
    return list(apps_dict.values())


def resolve_application(app_query: str) -> Optional[Dict[str, str]]:
    """
    Resolve ANY application installed on the user's computer.
    Includes smart alias mappings, dynamic scanning, fuzzy matching, and automatic on-demand rescan
    if a newly installed app is requested.
    """
    query = app_query.strip().lower()
    if not query:
        return None

    # Common colloquial tech aliases
    TECH_ALIASES = {
        "vscode": "code",
        "vs code": "code",
        "visual studio code": "code",
        "calc": "calculator",
        "compass": "mongodb compass",
        "mongo": "mongodb compass",
        "cmd": "cmd",
        "command prompt": "cmd",
        "terminal": "terminal",
        "powershell": "powershell",
        "rar": "winrar",
        "edge": "edge",
        "studio": "android studio",
        "word": "wordpad",
    }

    # Normalize query if alias exists
    normalized_query = TECH_ALIASES.get(query, query)

    # 1. Curated quick aliases (chrome, code, notepad, calc, mongodb, etc.)
    if normalized_query in APPROVED_APPLICATIONS:
        return APPROVED_APPLICATIONS[normalized_query]
    if query in APPROVED_APPLICATIONS:
        return APPROVED_APPLICATIONS[query]

    # Helper function to match against scanned catalog
    def _find_in_catalog(catalog: Dict[str, Dict[str, str]], target: str) -> Optional[Dict[str, str]]:
        # Exact match
        if target in catalog:
            return catalog[target]

        # Word boundary match (e.g. 'chrome' in 'google chrome')
        for k, info in catalog.items():
            if target in k.split():
                return info

        # Substring match (e.g. 'github' in 'github desktop')
        for k, info in catalog.items():
            if len(target) >= 3 and (target in k or k in target):
                return info

        # Fuzzy match with high similarity
        matches = difflib.get_close_matches(target, list(catalog.keys()), n=1, cutoff=0.7)
        if matches:
            return catalog[matches[0]]

        return None

    # 2. Check current in-memory catalog
    catalog = scan_all_installed_apps(force_refresh=False)
    matched = _find_in_catalog(catalog, normalized_query)
    if not matched and query != normalized_query:
        matched = _find_in_catalog(catalog, query)

    if matched:
        return matched

    # 3. Not found in current cache: trigger automatic on-demand refresh!
    # (Catches newly installed apps without requiring restart)
    refreshed_catalog = scan_all_installed_apps(force_refresh=True)
    matched = _find_in_catalog(refreshed_catalog, normalized_query)
    if not matched and query != normalized_query:
        matched = _find_in_catalog(refreshed_catalog, query)

    if matched:
        return matched

    # 4. Check system PATH via shutil.which (e.g. cli utilities or binaries in PATH)
    path_exe = shutil.which(query) or shutil.which(f"{query}.exe")
    if path_exe:
        clean_name = os.path.splitext(os.path.basename(path_exe))[0].capitalize()
        return {
            "name": clean_name,
            "command": path_exe,
            "process_name": os.path.basename(path_exe),
            "type": "path",
        }

    return None


def is_path_safe(path: str) -> Tuple[bool, str]:
    """Check if a path is safe and outside blocked system locations."""
    if not path or not path.strip():
        return False, "Path cannot be empty."

    norm_path = os.path.abspath(path).lower()

    for blocked in BLOCKED_SYSTEM_PATHS:
        if norm_path == blocked or norm_path.startswith(blocked + os.sep):
            return False, f"Access to sensitive Windows system directory '{path}' is blocked."

    return True, "Path is allowed."


def is_command_safe(command: str) -> Tuple[bool, str]:
    """Validate that a terminal command does not match blocked destructive patterns."""
    if not command:
        return False, "Command cannot be empty."

    for pattern in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Command contains prohibited destructive pattern matching '{pattern}'."

    return True, "Command is allowed."
