"""
JARVIS Computer Control Tools
Phase 3B Component: Controlled, sandboxed Windows system actions with allowlist validation.
"""

import os
import re
import sys
import time
import ctypes
from ctypes import wintypes
import webbrowser
import subprocess
import urllib.parse
import shutil
import json
import psutil
from typing import Dict, Any, Optional, Tuple, List

from backend.security.allowlist import resolve_application, is_path_safe, APPROVED_APPLICATIONS

# Track active local development servers {port: subprocess.Popen}
_ACTIVE_LOCAL_SERVERS: Dict[int, subprocess.Popen] = {}

# Track the last successfully launched application to resolve pronouns ("it", "ise", "use", "app")
_LAST_OPENED_APP: Optional[str] = None


def _is_matching_process(proc_name: str, target: str, alias: Optional[str] = None) -> bool:
    """Robust process name matching with normalized alphanumeric fallback."""
    if not proc_name or not target:
        return False
    pn = proc_name.lower().replace(".exe", "").strip()
    tn = target.lower().replace(".exe", "").strip()
    al = (alias or "").lower().replace(".exe", "").strip()

    if pn in (tn, al):
        return True

    pn_clean = re.sub(r"[^a-z0-9]", "", pn)
    tn_clean = re.sub(r"[^a-z0-9]", "", tn)
    al_clean = re.sub(r"[^a-z0-9]", "", al)

    if pn_clean and tn_clean and pn_clean == tn_clean:
        return True
    if pn_clean and al_clean and pn_clean == al_clean:
        return True

    # Substring matching for multi-word software (e.g., 'github' in 'githubdesktop')
    if len(tn_clean) >= 4 and (tn_clean in pn_clean or pn_clean in tn_clean):
        return True
    if al_clean and len(al_clean) >= 4 and (al_clean in pn_clean or pn_clean in al_clean):
        return True

    return False


def open_application(app_name: str, target_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Open any Windows application installed on the computer.
    Uses native Windows ShellExecute (os.startfile) with subprocess fallback.
    If target_path is specified for IDEs/browsers (e.g. VS Code, Chrome), launches the path inside that app.
    """
    global _LAST_OPENED_APP
    if not app_name or not app_name.strip():
        return {"success": False, "error": "Application name cannot be empty."}

    # If target_path is specified, route directly to specialized opener
    if target_path and target_path.strip():
        low_app = app_name.lower().strip()
        if any(k in low_app for k in ("vscode", "code", "vs code", "visual studio code")):
            return open_in_vscode(target_path)
        if any(k in low_app for k in ("chrome", "browser", "edge", "firefox")):
            return open_file_in_browser(target_path)

    app_info = resolve_application(app_name)
    if not app_info:
        return {
            "success": False,
            "error": f"Application '{app_name}' is not installed or could not be found on this computer.",
            "suggestion": "Please check the application name or ensure it is installed."
        }

    cmd = app_info["command"]
    try:
        # Prefer native os.startfile for Windows shortcuts (.lnk), UWP shell URIs, and full file paths
        if cmd.lower().endswith(".lnk") or cmd.startswith("shell:") or os.path.exists(cmd):
            try:
                os.startfile(cmd)
            except Exception:
                subprocess.Popen(
                    cmd,
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                )
        else:
            subprocess.Popen(
                cmd,
                shell=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            )

        _LAST_OPENED_APP = app_info["name"]
        return {
            "success": True,
            "app_name": app_info["name"],
            "message": f"Successfully launched {app_info['name']}."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to launch {app_info['name']}: {str(e)}"}


def close_folder(folder_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Gracefully close an open File Explorer window (e.g. 'Downloads', 'Documents', 'Projects')
    without killing or restarting the Windows explorer.exe shell process.
    """
    target = (folder_name or "").strip().lower()
    # Normalize generic terms
    if target in ("folder", "file explorer", "explorer", "window", "open folder"):
        target = ""

    ps_code = f"""
    $shell = New-Object -ComObject Shell.Application
    $windows = $shell.Windows()
    $closed = 0
    $target = "{target}".ToLower()
    foreach ($w in $windows) {{
        $name = ("" + $w.LocationName).ToLower()
        $url = ("" + $w.LocationURL).ToLower()
        if (-not $target -or $name -like "*$target*" -or $url -like "*$target*") {{
            $closedName = $w.LocationName
            $w.Quit()
            $closed++
            Write-Output "CLOSED: $closedName"
            break
        }}
    }}
    if ($closed -eq 0) {{
        Write-Output "NO_MATCH"
    }}
    """
    try:
        cmd = ["powershell", "-NoProfile", "-Command", ps_code]
        out = subprocess.check_output(cmd, text=True, encoding="utf-8", timeout=6).strip()
        if "CLOSED:" in out:
            closed_title = out.split("CLOSED:")[-1].strip() or folder_name or "Folder"
            return {"success": True, "message": f"Closed folder window '{closed_title}'."}
        return {"success": False, "error": f"No active folder window found matching '{folder_name or 'Explorer'}'."}
    except Exception as e:
        return {"success": False, "error": f"Failed to close folder: {str(e)}"}


def close_application(app_name: str) -> Dict[str, Any]:
    """
    Gracefully terminate running instances of an application.
    Supports pronoun/context resolution ('it', 'ise', 'use') and fuzzy process matching.
    """
    global _LAST_OPENED_APP
    if not app_name or not app_name.strip():
        if _LAST_OPENED_APP:
            app_name = _LAST_OPENED_APP
        else:
            return {"success": False, "error": "Application name cannot be empty."}

    lowered = app_name.lower().strip()

    # Context / pronoun resolution
    if lowered in ("it", "i", "this", "that", "ise", "use", "app", "application", "window"):
        if _LAST_OPENED_APP:
            app_name = _LAST_OPENED_APP
            lowered = _LAST_OPENED_APP.lower().strip()

    # Special handling: Never terminate explorer.exe (the Windows shell/taskbar)
    # Only redirect to close_folder if explicitly a folder/explorer command (NOT apps like 'GitHub Desktop')
    folder_keywords = ["folder", "file explorer", "explorer window"]
    folder_aliases = ["downloads", "download", "documents", "docs", "desktop folder", "projects folder"]
    if any(k in lowered for k in folder_keywords) or lowered in folder_aliases:
        target = app_name if not any(x in lowered for x in ["file explorer", "explorer"]) else ""
        return close_folder(target)

    app_info = resolve_application(app_name)
    proc_alias = app_info["process_name"] if app_info else None
    name_display = app_info["name"] if app_info else app_name

    closed_count = 0
    try:
        # Pass 1: terminate matching processes via psutil
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                p_name = proc.info['name']
                if p_name and _is_matching_process(p_name, lowered, proc_alias):
                    proc.terminate()
                    closed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Pass 2: Windows taskkill process tree fallback for Electron/multi-process apps
        if proc_alias and proc_alias.lower() != "explorer.exe":
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", proc_alias, "/T"],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
                )
            except Exception:
                pass

        if closed_count > 0:
            return {
                "success": True,
                "app_name": name_display,
                "message": f"Closed {name_display} ({closed_count} process instances terminated)."
            }
        else:
            return {
                "success": True,
                "app_name": name_display,
                "message": f"{name_display} has been closed."
            }
    except Exception as e:
        return {"success": False, "error": f"Error closing {app_name}: {str(e)}"}


def get_open_windows() -> Dict[str, Any]:
    """
    List currently visible application windows on the desktop.
    """
    titles = []
    def enum_proc(hwnd, lParam):
        if ctypes.windll.user32.IsWindowVisible(hwnd):
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.strip()
                excluded = (
                    "Program Manager", "Settings", "Windows Input Experience",
                    "Windows Shell Experience Host", "Task Switching"
                )
                if title and title not in excluded and len(title) > 2:
                    titles.append(title)
        return True

    EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    ctypes.windll.user32.EnumWindows(EnumProc(enum_proc), 0)

    seen = set()
    unique = []
    for t in titles:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return {
        "success": True,
        "windows": unique,
        "count": len(unique),
        "message": f"Active open windows: {', '.join(unique[:8]) if unique else 'None'}"
    }


def open_folder(folder_path: str) -> Dict[str, Any]:
    """
    Open a verified, safe directory in Windows File Explorer.
    """
    # Convenience aliases
    if folder_path.lower() in ("project", "projects", "my project", "jarvis"):
        folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    else:
        from backend.security.path_rules import resolve_path
        folder_path = resolve_path(folder_path)

    is_safe, msg = is_path_safe(folder_path)
    if not is_safe:
        return {"success": False, "error": msg}

    if not os.path.exists(folder_path):
        return {"success": False, "error": f"Folder '{folder_path}' does not exist."}

    try:
        os.startfile(os.path.abspath(folder_path))
        return {
            "success": True,
            "path": os.path.abspath(folder_path),
            "message": f"Opened folder '{os.path.basename(folder_path) or folder_path}' in File Explorer."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to open folder: {str(e)}"}


def get_chrome_executable() -> Optional[str]:
    """Find installed Google Chrome executable on the system."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
    ]
    for exe in candidates:
        if os.path.exists(exe):
            return exe
    return shutil.which("chrome") or shutil.which("google-chrome")


def configure_chrome_as_default_webbrowser() -> None:
    """Register Google Chrome as preferred browser controller in Python's webbrowser module."""
    chrome_exe = get_chrome_executable()
    if chrome_exe:
        try:
            webbrowser.register("chrome", None, webbrowser.BackgroundBrowser(chrome_exe), preferred=True)
        except Exception:
            pass


def get_primary_chrome_profile() -> str:
    """
    Detect the primary Google Chrome profile directory on this system.
    Searches Chrome's Local State to find the default/primary profile (e.g. 'Default').
    Defaults to 'Default' (Rana Akmal / ranaakmalr703@gmail.com).
    """
    try:
        user_data = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data")
        local_state_file = os.path.join(user_data, "Local State")
        if os.path.exists(local_state_file):
            with open(local_state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
                info = state.get("profile", {}).get("info_cache", {})
                if "Default" in info:
                    return "Default"
                for prof_id, prof_data in info.items():
                    if "ranaakmalr703" in prof_data.get("user_name", ""):
                        return prof_id
                if info:
                    return list(info.keys())[0]
    except Exception as e:
        print(f"[Chrome] Primary profile detection fallback: {e}")
    return "Default"


def find_chrome_profile_for_email(email_addr: str) -> Optional[str]:
    """Find which Chrome profile folder corresponds to a given email address."""
    if not email_addr:
        return None
    try:
        user_data = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data")
        local_state_file = os.path.join(user_data, "Local State")
        if os.path.exists(local_state_file):
            with open(local_state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
                info = state.get("profile", {}).get("info_cache", {})
                target_clean = email_addr.lower().strip()
                for prof_id, prof_data in info.items():
                    user_name = prof_data.get("user_name", "").lower().strip()
                    if user_name and user_name == target_clean:
                        return prof_id
    except Exception:
        pass
    return None


def _launch_browser(url: str, inspect: bool = False, profile: Optional[str] = None) -> bool:
    """
    Launch URL directly in Google Chrome within the creator's designated or primary profile ('Default').
    Always forces Google Chrome and the primary profile directory so Edge or other profiles are never used.
    """
    clean_url = (url or "").strip()
    if not clean_url.startswith(("http://", "https://", "file://", "mailto:")):
        clean_url = "https://" + clean_url

    chrome_exe = get_chrome_executable()
    target_profile = (profile or "").strip() or get_primary_chrome_profile()

    if chrome_exe:
        cmd = [chrome_exe]
        if target_profile:
            cmd.append(f"--profile-directory={target_profile}")
        # Force a dedicated window for this profile so Chrome doesn't attach to another profile's window
        cmd.append("--new-window")
        if inspect:
            cmd.append("--auto-open-devtools-for-tabs")
        cmd.append(clean_url)
        try:
            creation_flags = 0
            if os.name == "nt":
                creation_flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            subprocess.Popen(cmd, creationflags=creation_flags)
            return True
        except Exception as e:
            print(f"[Browser] Error launching Chrome directly: {e}")
            try:
                subprocess.Popen(cmd)
                return True
            except Exception:
                pass

    # Fallback to configured webbrowser controller if Chrome not found
    try:
        configure_chrome_as_default_webbrowser()
        return webbrowser.open(clean_url)
    except Exception as e:
        print(f"[Browser] webbrowser.open fallback error: {e}")
        return False


# Register Chrome on module import
configure_chrome_as_default_webbrowser()


PORTAL_SHORTCUTS: Dict[str, str] = {
    # Developer Portals & Dashboards
    "vercel": "https://vercel.com/dashboard",
    "vercel dashboard": "https://vercel.com/dashboard",
    "mera vercel": "https://vercel.com/dashboard",
    "netlify": "https://app.netlify.com/teams/akmaldoghar/projects",
    "netlift": "https://app.netlify.com/teams/akmaldoghar/projects",
    "netlify dashboard": "https://app.netlify.com/teams/akmaldoghar/projects",
    "netlift dashboard": "https://app.netlify.com/teams/akmaldoghar/projects",
    "mera netlify": "https://app.netlify.com/teams/akmaldoghar/projects",
    "mera netlift": "https://app.netlify.com/teams/akmaldoghar/projects",
    "nextjs": "https://nextjs.org",
    "next.js": "https://nextjs.org",
    "next js": "https://nextjs.org",
    "nextjs docs": "https://nextjs.org/docs",
    "react": "https://react.dev",
    "reactjs": "https://react.dev",
    "react.dev": "https://react.dev",
    "vue": "https://vuejs.org",
    "vuejs": "https://vuejs.org",
    "tailwind": "https://tailwindcss.com",
    "tailwindcss": "https://tailwindcss.com",
    "leetcode": "https://leetcode.com",
    "leetcord": "https://leetcode.com",
    "expo": "https://expo.dev/accounts/muhammad_akmal",
    "expo dashboard": "https://expo.dev/accounts/muhammad_akmal",
    "mera expo": "https://expo.dev/accounts/muhammad_akmal",
    "github": "https://github.com",
    "my github": "https://github.com/AkmalDoghar",
    "gitlab": "https://gitlab.com",
    "kaggle": "https://www.kaggle.com",
    "huggingface": "https://huggingface.co",
    "npm": "https://www.npmjs.com",
    "supabase": "https://supabase.com/dashboard",
    "firebase": "https://console.firebase.google.com",
    "openrouter": "https://openrouter.ai",
    "google ai studio": "https://aistudio.google.com/apps",
    "ai studio": "https://aistudio.google.com/apps",
    "infinityfree": "https://www.infinityfree.com",
    "zidio": "https://zidio.in/dashboard/public-profile",
    
    # Google & Productivity
    "map": "https://maps.google.com",
    "maps": "https://maps.google.com",
    "google map": "https://maps.google.com",
    "google maps": "https://maps.google.com",
    "gmail": "https://mail.google.com",
    "email": "https://mail.google.com",
    "google drive": "https://drive.google.com",
    "drive": "https://drive.google.com",
    "calendar": "https://calendar.google.com",
    "google calendar": "https://calendar.google.com",
    "meet": "https://meet.google.com",
    "google meet": "https://meet.google.com",

    # AI Platforms
    "chatgpt": "https://chatgpt.com",
    "claude": "https://claude.ai",
    "gemini": "https://gemini.google.com",
    "v0": "https://v0.dev",
    "bolt": "https://bolt.new",

    # Social & Communications
    "whatsapp": "https://web.whatsapp.com",
    "whatsapp web": "https://web.whatsapp.com",
    "linkedin": "https://www.linkedin.com/feed/",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "youtube": "https://youtube.com",
    "youtube studio": "https://studio.youtube.com",
    "instagram": "https://instagram.com",

    # Creator Portfolio
    "portfolio": "https://akmalcode.vercel.app",
    "mera portfolio": "https://akmalcode.vercel.app",
    "meri website": "https://akmalcode.vercel.app",
}


def open_website(url: str, inspect: bool = False) -> Dict[str, Any]:
    """
    Open an approved website URL, web portal dashboard, or web search in the default browser.
    Automatically normalizes search queries, portal shortcuts (e.g. 'vercel', 'leetcode', 'expo', 'maps'),
    or missing protocols. Supports inspect/developer mode if requested.
    """
    clean_url = url.strip()
    if not clean_url:
        return {"success": False, "error": "URL cannot be empty."}

    # Redirect local files / file:// URIs or local paths to open_file_in_browser
    if clean_url.startswith("file://") or clean_url.lower().endswith((".html", ".htm", ".svg")) or os.path.exists(clean_url):
        return open_file_in_browser(clean_url, inspect=inspect)

    # If input is already an explicit HTTP/HTTPS URL, preserve exact case and do not re-resolve
    resolved_info = None
    if not clean_url.startswith(("http://", "https://")):
        lowered = clean_url.lower().strip()
        # Strip common conversational prefixes
        for prefix in ("open ", "kholo ", "khol ", "mera ", "meri ", "my "):
            if lowered.startswith(prefix):
                clean_url = clean_url[len(prefix):].strip()
                lowered = lowered[len(prefix):].strip()

        # Intelligent URL resolution: Check user's Bookmarks and History first!
        try:
            from backend.tools.chrome_bookmarks import resolve_smart_url
            resolved = resolve_smart_url(clean_url)
            if resolved.get("source") in ("bookmark", "history", "portal"):
                clean_url = resolved["url"]
                resolved_info = resolved
        except Exception:
            pass

        if not resolved_info:
            if lowered in PORTAL_SHORTCUTS:
                clean_url = PORTAL_SHORTCUTS[lowered]
            else:
                # If input is a search command or search query rather than a direct URL
                is_search = False
                search_query = ""
                if lowered.startswith("google search "):
                    search_query = clean_url[14:].strip()
                    is_search = True
                elif lowered.startswith("google "):
                    search_query = clean_url[7:].strip()
                    is_search = True
                elif not clean_url.startswith(("http://", "https://")) and (" " in clean_url or "." not in clean_url):
                    search_query = clean_url
                    is_search = True

                if is_search and search_query:
                    clean_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(search_query)}"

                if not clean_url.startswith(("http://", "https://")):
                    clean_url = "https://" + clean_url

    try:
        _launch_browser(clean_url, inspect=inspect)
        msg = f"Opened {clean_url} in browser"
        if inspect:
            msg += " with Developer Tools (Inspect mode)"
        msg += "."
        return {
            "success": True,
            "url": clean_url,
            "inspect": inspect,
            "message": msg
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to open browser URL: {str(e)}"}


def get_chrome_profiles() -> List[Dict[str, Any]]:
    """Scan and list all Google Chrome profiles from the Windows User Data directory with aliases & account numbering."""
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    local_state_file = os.path.join(local_app_data, 'Google', 'Chrome', 'User Data', 'Local State')
    profiles = []
    if os.path.exists(local_state_file):
        try:
            with open(local_state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            cache = data.get('profile', {}).get('info_cache', {})

            def sort_key(item):
                d = item[0]
                if d == "Default":
                    return 0
                m = re.search(r'\d+', d)
                return int(m.group(0)) if m else 99

            sorted_items = sorted(cache.items(), key=sort_key)
            for idx, (dir_name, pinfo) in enumerate(sorted_items, 1):
                name = pinfo.get('name', dir_name)
                gaia_name = pinfo.get('gaia_name', '')
                email = pinfo.get('user_name', '')

                aliases = [
                    str(idx),
                    f"account {idx}",
                    dir_name.lower()
                ]

                ord_map = {
                    1: ["pehla", "pehle", "first", "one", "default", "personal"],
                    2: ["doosra", "dosra", "second", "two"],
                    3: ["teesra", "tesra", "third", "three"],
                    4: ["chautha", "chotha", "fourth", "four"]
                }
                aliases.extend(ord_map.get(idx, []))

                if "ranaakmal" in email.lower() or "rana akmal" in gaia_name.lower():
                    aliases.extend(["rana akmal", "rana", "ranaakmalr703"])
                if "84pakarmy" in email.lower() or "m. akmal" in gaia_name.lower():
                    aliases.extend(["m akmal", "84pakarmy", "pak army", "pakarmy"])
                if "vu.edu.pk" in email.lower() or "vu" in name.lower():
                    aliases.extend(["vu", "virtual university", "uni", "university", "student", "lms", "bc250211604mak"])
                if "dev42" in email.lower() or "next.js" in name.lower() or "developer" in name.lower():
                    aliases.extend(["developer", "dev", "nextjs", "next.js", "dev42", "m.akmal.dev42"])

                display_title = f"Account {idx}: {gaia_name or name} ({email or dir_name})"
                profiles.append({
                    "account_number": idx,
                    "dir_name": dir_name,
                    "name": name,
                    "gaia_name": gaia_name,
                    "email": email,
                    "display_title": display_title,
                    "aliases": list(set(aliases))
                })
        except Exception:
            pass
    return profiles


def list_google_accounts() -> Dict[str, Any]:
    """
    List all configured Google accounts / Chrome profiles on this PC with numbers, emails, and active aliases.
    Useful when user asks 'which Google accounts are connected?' or 'mere kitne accounts hain?'.
    """
    profiles = get_chrome_profiles()
    if not profiles:
        return {"success": False, "error": "No Google accounts or Chrome profiles found on this PC."}

    lines = ["Google Accounts / Chrome Profiles Configured on this PC:"]
    for p in profiles:
        email_str = f" - {p['email']}" if p.get('email') else ""
        lines.append(f"[{p['account_number']}] {p.get('gaia_name') or p.get('name')}{email_str} (Profile Directory: {p['dir_name']})")

    summary_text = "\n".join(lines)
    return {
        "success": True,
        "count": len(profiles),
        "accounts": profiles,
        "message": summary_text
    }


def open_chrome_profile(profile_name: str, url: Optional[str] = None) -> Dict[str, Any]:
    """
    Open Google Chrome under a specific user profile or Google account (Account 1: Rana Akmal, Account 2: M. Akmal, Account 3: Virtual University, Account 4: Next.js Developer).
    Optionally opens a specific website or portal directly inside that profile.
    """
    profiles = get_chrome_profiles()
    if not profiles:
        return {"success": False, "error": "No Google Chrome profiles found on this computer."}

    def clean_str(s: str) -> str:
        return re.sub(r'[^\w\s]', '', s.lower()).strip()

    q = clean_str(profile_name)
    matched_dir = None
    matched_info = None

    # Step 1: Direct numeric account match (e.g. '1', '2', '3', '4')
    if q in ("1", "2", "3", "4"):
        for p in profiles:
            if str(p.get("account_number")) == q:
                matched_dir = p["dir_name"]
                matched_info = p
                break

    # Step 2: Check rich alias list
    if not matched_dir:
        for p in profiles:
            for alias in p.get("aliases", []):
                clean_alias = clean_str(alias)
                if q == clean_alias or clean_alias in q or (len(q) > 3 and q in clean_alias):
                    matched_dir = p["dir_name"]
                    matched_info = p
                    break
            if matched_dir:
                break

    # Step 3: Normalized substring matching on name, gaia_name, email, or dir_name
    if not matched_dir:
        for p in profiles:
            names = [
                clean_str(p["name"]),
                clean_str(p["gaia_name"]),
                clean_str(p["email"]),
                p["dir_name"].lower()
            ]
            if any(q == n or q in n or n in q for n in names if n):
                matched_dir = p["dir_name"]
                matched_info = p
                break

    # Step 4: Fuzzy token match if not matched
    if not matched_dir:
        for p in profiles:
            combined = f"{p['name']} {p['gaia_name']} {p['email']}".lower()
            if any(token in combined for token in q.split() if len(token) > 2):
                matched_dir = p["dir_name"]
                matched_info = p
                break

    if not matched_dir:
        available = ", ".join([f"[{p['account_number']}] '{p['gaia_name'] or p['name']}' ({p['email'] or p['dir_name']})" for p in profiles])
        return {
            "success": False,
            "error": f"Chrome profile '{profile_name}' not found. Available profiles: {available}"
        }

    target_url = url.strip() if url else ""
    if target_url:
        # If already an explicit HTTP/HTTPS URL, preserve exact case and skip re-resolution
        if not target_url.startswith(("http://", "https://", "file://")):
            raw_target = target_url
            lowered_target = raw_target.lower().strip()
            for prefix in ("open ", "kholo ", "khol ", "mera ", "meri ", "my "):
                if lowered_target.startswith(prefix):
                    raw_target = raw_target[len(prefix):].strip()
                    lowered_target = lowered_target[len(prefix):].strip()

            # Check user's Bookmarks and History for this specific profile!
            try:
                from backend.tools.chrome_bookmarks import resolve_smart_url
                resolved = resolve_smart_url(raw_target, profile_name=matched_dir)
                if resolved.get("source") in ("bookmark", "history", "portal"):
                    target_url = resolved["url"]
            except Exception:
                if lowered_target in PORTAL_SHORTCUTS:
                    target_url = PORTAL_SHORTCUTS[lowered_target]
                elif not target_url.startswith(("http://", "https://")):
                    target_url = "https://" + target_url

    chrome_candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
    ]
    chrome_exe = next((c for c in chrome_candidates if os.path.exists(c)), None)
    if not chrome_exe:
        return {"success": False, "error": "Google Chrome executable not found on PC."}

    cmd = [chrome_exe, f"--profile-directory={matched_dir}", "--new-window"]
    if target_url:
        cmd.append(target_url)

    try:
        creation_flags = 0
        if os.name == "nt":
            creation_flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(cmd, creationflags=creation_flags)
        prof_display = matched_info.get('gaia_name') or matched_info.get('name') or matched_dir
        target_desc = f" and opened {target_url}" if target_url else ""
        return {
            "success": True,
            "profile_name": prof_display,
            "profile_dir": matched_dir,
            "account_number": matched_info.get("account_number"),
            "email": matched_info.get("email", ""),
            "url": target_url,
            "message": f"Opened Google Chrome with profile '{prof_display}' ({matched_info.get('email', '')}){target_desc}."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to launch Chrome with profile: {str(e)}"}



# ─────────────────────────────────────────────
# WhatsApp & Contacts Management
# ─────────────────────────────────────────────
CONTACTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "contacts.json")

def _get_contacts() -> Dict[str, Dict[str, str]]:
    if os.path.exists(CONTACTS_FILE):
        try:
            with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_contacts(contacts: Dict[str, Dict[str, str]]):
    os.makedirs(os.path.dirname(CONTACTS_FILE), exist_ok=True)
    with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
        json.dump(contacts, f, indent=2, ensure_ascii=False)


def _normalize_contact_name(name: str) -> str:
    """Normalize contact name by lowercasing and stripping emojis, symbols, and punctuation."""
    if not name:
        return ""
    norm = re.sub(r"[^\w]", "", name.lower(), flags=re.UNICODE).strip()
    if norm in ("aapi", "aapii", "aapy", "apiy"):
        norm = "api"
    return norm


def _find_contact_entry(target: str) -> Optional[Dict[str, str]]:
    """
    Find a contact in contacts.json using exact, normalized, emoji-stripped,
    substring, and cultural alias matching (e.g. '✨Api✨' <-> 'api' <-> 'aapi').
    """
    if not target:
        return None
    contacts = _get_contacts()
    if not contacts:
        return None

    target_raw = target.strip()
    target_lower = target_raw.lower()
    norm_target = _normalize_contact_name(target_raw)

    # 1. Exact dictionary key match
    if target_lower in contacts:
        return contacts[target_lower]

    # 2. Match against saved entries (by key or name)
    for key, entry in contacts.items():
        entry_name = entry.get("name", "")
        norm_key = _normalize_contact_name(key)
        norm_name = _normalize_contact_name(entry_name)

        # Direct normalized match (e.g. '✨Api✨' -> 'api' matches target 'api')
        if norm_target and (norm_target == norm_key or norm_target == norm_name):
            return entry

    # 3. Substring match (e.g. target 'api' in 'api jaan', or 'wajid' in 'wajid bhai')
    if norm_target and len(norm_target) >= 3:
        for key, entry in contacts.items():
            entry_name = entry.get("name", "")
            norm_key = _normalize_contact_name(key)
            norm_name = _normalize_contact_name(entry_name)
            if (norm_target in norm_key or norm_key in norm_target) or \
               (norm_target in norm_name or norm_name in norm_target):
                return entry

    return None


def save_contact(name: str, phone: str) -> Dict[str, Any]:
    """Save or update a contact's phone number for WhatsApp messaging and calling (e.g. name='✨Api✨' or 'Ali', phone='03001234567')."""
    clean_name = name.strip()
    clean_phone = re.sub(r"[^\d+]", "", phone.strip())
    if not clean_name or not clean_phone:
        return {"success": False, "error": "Both contact name and valid phone number are required."}

    contacts = _get_contacts()
    norm_key = _normalize_contact_name(clean_name)
    entry = {
        "name": clean_name,
        "phone": clean_phone
    }
    contacts[clean_name.lower()] = entry
    if norm_key and norm_key != clean_name.lower():
        contacts[norm_key] = entry
    if norm_key == "api":
        contacts["aapi"] = entry

    _save_contacts(contacts)
    return {
        "success": True,
        "name": clean_name,
        "phone": clean_phone,
        "message": f"Saved contact '{clean_name}' with phone number {clean_phone} into JARVIS address book."
    }


def list_contacts() -> Dict[str, Any]:
    """List all saved contacts in the JARVIS address book."""
    contacts = _get_contacts()
    unique = {}
    for entry in contacts.values():
        clean_p = entry.get("phone", "")
        clean_n = entry.get("name", "")
        ident = clean_p or clean_n
        if ident not in unique:
            unique[ident] = entry
    return {
        "success": True,
        "total": len(unique),
        "contacts": list(unique.values()),
        "message": f"Found {len(unique)} saved contact(s) in address book."
    }


def _bring_whatsapp_window_to_foreground(timeout: float = 5.0):
    """
    Find WhatsApp Desktop windows on the interactive desktop, restore them if minimized,
    and bring the main UI window to foreground with keyboard focus.
    Handles both WinUI 3 Root frame window and Edge WebView2 UI window.
    Supports title matching with unread counts (e.g. '(1) WhatsApp', '(5) WhatsApp', 'WhatsApp').
    Preserves maximized state without de-maximizing.
    """
    import time
    import ctypes
    from ctypes import wintypes
    import subprocess
    import os
    import re
    import psutil

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # Attach thread to interactive desktop station
    input_desk = user32.OpenInputDesktop(0, False, 0x01FF)
    if input_desk:
        user32.SetThreadDesktop(input_desk)

    start_time = time.time()
    matching_hwnds = []

    while time.time() - start_time < timeout:
        matching_hwnds.clear()
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def enum_proc(hwnd, lParam):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.strip()
                title_lower = title.lower()

                cls_buff = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls_buff, 256)
                cls_name = cls_buff.value

                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                try:
                    pname = psutil.Process(pid.value).name().lower()
                except Exception:
                    pname = ""

                # Reject IDEs, editors, code tools, and standard browser tabs
                if any(x in title_lower for x in ("antigravity", "visual studio", "code", ".py", ".ts", "- google chrome", "- microsoft edge", "- brave")):
                    return 1

                is_whatsapp_proc = ("whatsapp" in pname) or (cls_name in ("WinUIDesktopWin32WindowClass", "ApplicationFrameWindow"))
                is_whatsapp_title = (
                    title == "WhatsApp"
                    or title.endswith("WhatsApp")
                    or bool(re.search(r"^\(\d+\+?\)\s*whatsapp", title_lower))
                    or ("whatsapp" in title_lower and is_whatsapp_proc)
                )

                if is_whatsapp_title and (is_whatsapp_proc or "WinUI" in cls_name):
                    matching_hwnds.append((hwnd, cls_name))
                elif is_whatsapp_title and "Chrome" in cls_name and is_whatsapp_proc:
                    matching_hwnds.append((hwnd, cls_name))
            return 1

        cb = WNDENUMPROC(enum_proc)
        if input_desk:
            user32.EnumDesktopWindows(input_desk, cb, 0)
        else:
            user32.EnumWindows(cb, 0)

        if matching_hwnds:
            break
        time.sleep(0.25)

    if not matching_hwnds:
        return False, None

    winui_hwnd = None
    webview_hwnd = None
    for h, cls in matching_hwnds:
        if "WinUI" in cls:
            winui_hwnd = h
        elif "Chrome" in cls:
            webview_hwnd = h

    if not winui_hwnd and matching_hwnds:
        winui_hwnd = matching_hwnds[0][0]

    # Non-destructive restore: only call SW_RESTORE if minimized, otherwise preserve maximized or normal
    def _safe_show(h):
        if not h:
            return
        if user32.IsIconic(h):
            user32.ShowWindow(h, 9)  # SW_RESTORE
        elif user32.IsZoomed(h):
            user32.ShowWindow(h, 3)  # SW_MAXIMIZE
        else:
            user32.ShowWindow(h, 5)  # SW_SHOW

    _safe_show(winui_hwnd)
    if webview_hwnd:
        _safe_show(webview_hwnd)

    fg_hwnd = user32.GetForegroundWindow()
    fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None)
    curr_thread = kernel32.GetCurrentThreadId()

    if fg_thread != curr_thread:
        user32.AttachThreadInput(curr_thread, fg_thread, True)

    # Bypass Windows foreground lock using Alt tap, then dismiss menu highlight with Escape
    VK_MENU = 0x12
    VK_ESCAPE = 0x1B
    KEYUP = 0x0002
    user32.keybd_event(VK_MENU, 0, 0, 0)
    user32.keybd_event(VK_MENU, 0, KEYUP, 0)
    time.sleep(0.04)
    user32.keybd_event(VK_ESCAPE, 0, 0, 0)
    user32.keybd_event(VK_ESCAPE, 0, KEYUP, 0)

    user32.SetForegroundWindow(winui_hwnd)
    user32.BringWindowToTop(winui_hwnd)

    target_hwnd = webview_hwnd if webview_hwnd else winui_hwnd
    user32.SetForegroundWindow(target_hwnd)
    user32.BringWindowToTop(target_hwnd)
    user32.SetFocus(target_hwnd)

    if fg_thread != curr_thread:
        user32.AttachThreadInput(curr_thread, fg_thread, False)

    return True, target_hwnd


def _type_unicode_text(text: str, delay_between: float = 0.03):
    """
    Type Unicode string directly into active control using Windows SendInput.
    Never misses characters and does not interfere with the Windows clipboard.
    """
    import ctypes
    from ctypes import wintypes
    import time

    user32 = ctypes.windll.user32

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_ulonglong)
        ]

    class INPUT(ctypes.Structure):
        class _I(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT)]
        _anonymous_ = ("_i",)
        _fields_ = [("type", wintypes.DWORD), ("_i", _I)]

    KEYEVENTF_UNICODE = 0x0004
    KEYEVENTF_KEYUP = 0x0002
    INPUT_KEYBOARD = 1

    for ch in text:
        inp_down = INPUT()
        inp_down.type = INPUT_KEYBOARD
        inp_down.ki.wVk = 0
        inp_down.ki.wScan = ord(ch)
        inp_down.ki.dwFlags = KEYEVENTF_UNICODE

        inp_up = INPUT()
        inp_up.type = INPUT_KEYBOARD
        inp_up.ki.wVk = 0
        inp_up.ki.wScan = ord(ch)
        inp_up.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP

        user32.SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(INPUT))
        time.sleep(0.012)
        user32.SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(INPUT))
        time.sleep(delay_between)


def _wait_for_whatsapp_ui_ready(timeout: float = 18.0) -> Tuple[bool, Optional[Any], Optional[int]]:
    """
    Ensure WhatsApp Desktop is running and actively wait until the Chromium Web UI
    has fully rendered its interactive elements (Search edit box or Chats button).
    Solves cold-start delays when WhatsApp was previously closed.
    Returns (is_ready, doc, hwnd).
    """
    import time
    import subprocess
    import os
    import uiautomation as auto
    import win32gui

    # 1. Bring or launch WhatsApp Desktop
    ok, hwnd = _bring_whatsapp_window_to_foreground(timeout=2.0)
    if not ok or not hwnd:
        try:
            os.startfile("whatsapp://")
        except Exception:
            try:
                subprocess.Popen(['explorer.exe', 'shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App'])
            except Exception:
                pass
        time.sleep(1.5)

    start_time = time.time()
    last_bring_time = 0.0

    while time.time() - start_time < timeout:
        if time.time() - last_bring_time > 2.5:
            ok, hwnd = _bring_whatsapp_window_to_foreground(timeout=1.5)
            last_bring_time = time.time()

        if hwnd and win32gui.IsWindow(hwnd):
            child_windows = []
            try:
                win32gui.EnumChildWindows(hwnd, lambda ch, _: child_windows.append((ch, win32gui.GetClassName(ch))), None)
                chrome_hwnd = next((h for h, cls in child_windows if "Chrome" in cls), None)
            except Exception:
                chrome_hwnd = None

            if chrome_hwnd:
                try:
                    ctrl = auto.ControlFromHandle(chrome_hwnd)
                    doc = ctrl.DocumentControl(AutomationId="RootWebArea")
                    if doc and doc.Exists(0.2):
                        found_ready = False
                        def check_ready(c, d=0):
                            nonlocal found_ready
                            if d > 16 or found_ready:
                                return
                            r = c.BoundingRectangle
                            # If Search edit box or Chats button or New chat button is rendered
                            if (c.ControlTypeName == "EditControl" and r.top < 260 and r.left < 550) or (c.ControlTypeName == "ButtonControl" and c.Name in ("Chats", "New chat")):
                                found_ready = True
                                return
                            for ch in c.GetChildren():
                                check_ready(ch, d + 1)

                        check_ready(doc)
                        if found_ready:
                            return True, doc, hwnd
                except Exception:
                    pass

        time.sleep(0.4)

    return False, None, hwnd


def _automate_whatsapp_search_and_paste(contact_name: str, message: str) -> bool:
    """
    Search for a contact name in WhatsApp Desktop, open their conversation,
    and paste the message into the bottom chat input box ready to be sent.
    Guarantees that previous searches/chats are cleared, contact is properly selected,
    and message is NEVER typed into the top-right search box.
    """
    import time
    import ctypes
    import pyperclip
    import win32gui

    # Step 1: Actively wait until WhatsApp window & Chromium UI are fully rendered and interactive
    is_ready, doc, hwnd = _wait_for_whatsapp_ui_ready(timeout=18.0)
    if not is_ready or not hwnd:
        return False

    user32 = ctypes.windll.user32
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.2)

    VK_CONTROL = 0x11
    VK_A = 0x41
    VK_V = 0x56
    VK_BACK = 0x08
    VK_RETURN = 0x0D
    VK_ESCAPE = 0x1B
    KEYUP = 0x0002

    def combo_tap(keys, delay=0.04):
        for k in keys:
            user32.keybd_event(k, 0, 0, 0)
            time.sleep(delay)
        time.sleep(delay)
        for k in reversed(keys):
            user32.keybd_event(k, 0, KEYUP, 0)
            time.sleep(delay)
        time.sleep(delay)

    def key_tap(code, delay=0.04):
        user32.keybd_event(code, 0, 0, 0)
        time.sleep(delay)
        user32.keybd_event(code, 0, KEYUP, 0)
        time.sleep(delay)

    def click_at(x: int, y: int, delay_after: float = 0.2):
        user32.SetCursorPos(int(x), int(y))
        time.sleep(0.04)
        user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.04)
        user32.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(delay_after)

    # Step 1.5: If Status posting view / draft is open, close/discard it first
    from backend.tools.whatsapp_status import _get_whatsapp_doc
    doc, _ = _get_whatsapp_doc()
    if doc:
        close_btn = doc.ButtonControl(searchDepth=15, Name="Close status posting view")
        if close_btn.Exists(0.5):
            try:
                close_btn.GetInvokePattern().Invoke()
            except Exception:
                try:
                    close_btn.Click(simulateMove=False)
                except Exception:
                    pass
            time.sleep(0.35)
            doc, _ = _get_whatsapp_doc()

    # Step 2: Clean slate - Press Escape twice to clear any existing popups or top-right search
    key_tap(VK_ESCAPE, delay=0.06)
    time.sleep(0.1)
    key_tap(VK_ESCAPE, delay=0.06)
    time.sleep(0.2)

    doc, _ = _get_whatsapp_doc()

    # Step 3: Switch to Chats Tab and Find Main Search Box
    search_box = None
    if doc:
        chats_btn = doc.ButtonControl(searchDepth=12, Name="Chats")
        if chats_btn.Exists(0.8):
            try:
                chats_btn.GetTogglePattern().Toggle()
            except Exception:
                try:
                    chats_btn.GetLegacyIAccessiblePattern().DoDefaultAction()
                except Exception:
                    try:
                        chats_btn.Click(simulateMove=False)
                    except Exception:
                        pass
            time.sleep(0.35)
            doc, _ = _get_whatsapp_doc()

        def find_search(c, d=0):
            nonlocal search_box
            if d > 16 or search_box:
                return
            r = c.BoundingRectangle
            if c.ControlTypeName == "EditControl" and r.top < 260 and r.left < 550:
                search_box = c
                return
            for ch in c.GetChildren():
                find_search(ch, d + 1)

        find_search(doc)

    if search_box:
        sr = search_box.BoundingRectangle
        scx = (sr.left + sr.right) // 2
        scy = (sr.top + sr.bottom) // 2
        click_at(scx, scy, delay_after=0.15)
    else:
        rect = win32gui.GetWindowRect(hwnd)
        win_left, win_top = rect[0], rect[1]
        click_at(win_left + 230, win_top + 120, delay_after=0.2)

    # Step 4: Clear any previous search text in the search bar
    combo_tap([VK_CONTROL, VK_A], delay=0.04)
    time.sleep(0.04)
    key_tap(VK_BACK, delay=0.04)
    time.sleep(0.1)

    # Step 5: Type/Paste the contact name into the search box
    try:
        pyperclip.copy(contact_name)
        combo_tap([VK_CONTROL, VK_V], delay=0.05)
    except Exception:
        _type_unicode_text(contact_name, delay_between=0.035)

    # Step 6: Allow WhatsApp search engine sufficient time to filter contacts
    time.sleep(1.0)

    # Step 7: Select and open the contact's chat
    key_tap(VK_RETURN, delay=0.06)
    time.sleep(0.5)

    # Step 8: Active polling for the Bottom Chat Input Box (Message composer at bottom of right pane)
    chat_box = None
    poll_start = time.time()
    while time.time() - poll_start < 4.0:
        doc, _ = _get_whatsapp_doc()
        if doc:
            def find_bottom_chat_box(c, d=0):
                nonlocal chat_box
                if d > 18 or chat_box:
                    return
                r = c.BoundingRectangle
                if c.ControlTypeName == "EditControl" and r.top > 480 and r.left > 550:
                    chat_box = c
                    return
                for ch in c.GetChildren():
                    find_bottom_chat_box(ch, d + 1)

            find_bottom_chat_box(doc)
            if chat_box:
                break
        time.sleep(0.3)

    if chat_box:
        cr = chat_box.BoundingRectangle
        cx = (cr.left + cr.right) // 2
        cy = (cr.top + cr.bottom) // 2
        click_at(cx, cy, delay_after=0.15)
    else:
        rect = win32gui.GetWindowRect(hwnd)
        win_left, win_top, win_right, win_bottom = rect
        cx = win_left + int((win_right - win_left) * 0.72)
        cy = win_bottom - 45
        click_at(cx, cy, delay_after=0.2)

    # Step 9: Clear any previously drafted text in the message box and paste the message
    combo_tap([VK_CONTROL, VK_A], delay=0.04)
    key_tap(VK_BACK, delay=0.04)
    time.sleep(0.08)

    try:
        pyperclip.copy(message)
        combo_tap([VK_CONTROL, VK_V], delay=0.05)
        time.sleep(0.3)
    except Exception:
        _type_unicode_text(message, delay_between=0.02)

    return True


def confirm_send_whatsapp() -> Dict[str, Any]:
    """
    Send the currently drafted message in WhatsApp (Desktop or Web) by focusing the window and pressing Enter.
    Use when the user confirms sending with 'send kr do', 'send it', 'bhejo', 'haan bhej do', etc.
    """
    import time
    import ctypes
    from backend.tools.whatsapp_web import get_last_whatsapp_platform, confirm_send_whatsapp_web, find_whatsapp_web_window

    last_plat = get_last_whatsapp_platform()
    if last_plat == "web":
        return confirm_send_whatsapp_web()

    ok, hwnd = _bring_whatsapp_window_to_foreground(timeout=3.0)
    if not ok or not hwnd:
        # Check if WhatsApp Web is open instead
        web_ok, _, _ = find_whatsapp_web_window(timeout=1.0)
        if web_ok:
            return confirm_send_whatsapp_web()
        return {"success": False, "error": "WhatsApp window could not be found or focused. Please ensure WhatsApp Desktop or WhatsApp Web is open."}

    time.sleep(0.2)
    user32 = ctypes.windll.user32
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.1)

    from backend.tools.whatsapp_status import _get_whatsapp_doc
    doc, _ = _get_whatsapp_doc()
    if doc:
        chat_box = None
        def find_bottom_chat_box(c, d=0):
            nonlocal chat_box
            if d > 18 or chat_box:
                return
            r = c.BoundingRectangle
            if c.ControlTypeName == "EditControl" and r.top > 480 and r.left > 550:
                chat_box = c
                return
            for ch in c.GetChildren():
                find_bottom_chat_box(ch, d + 1)
        find_bottom_chat_box(doc)
        if chat_box:
            cr = chat_box.BoundingRectangle
            cx = (cr.left + cr.right) // 2
            cy = (cr.top + cr.bottom) // 2
            user32.SetCursorPos(int(cx), int(cy))
            time.sleep(0.04)
            user32.mouse_event(0x0002, 0, 0, 0, 0)
            time.sleep(0.04)
            user32.mouse_event(0x0004, 0, 0, 0, 0)
            time.sleep(0.15)

    VK_RETURN = 0x0D
    KEYUP = 0x0002
    user32.keybd_event(VK_RETURN, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_RETURN, 0, KEYUP, 0)

    return {
        "success": True,
        "platform": "desktop",
        "message": "WhatsApp message successfully sent!"
    }


def clean_and_format_message(text: str) -> Tuple[str, bool]:
    """
    Format and correct a message before drafting or sending:
    - If already clean, grammatically sound, and properly formatted, leaves it as is.
    - If broken, shorthand, informal slang, unpunctuated, or has typos, automatically fixes:
      * Standardizes punctuation spacing (e.g. "hi ,how r u" -> "hi, how r u")
      * Expands greetings (e.g. "aoa", "aslam o alkm" -> "Assalam-o-Alaikum")
      * Expands common Roman Urdu / English shorthand (e.g. "kl" -> "kal", "tm"/"tym" -> "time", "kdr" -> "kidhar", "plz" -> "please", "thx" -> "Thanks")
      * Capitalizes sentences and standalone 'I'
      * Ensures clean spacing without altering the core meaning or language.
    Returns (formatted_text, was_modified).
    """
    if not text or not text.strip():
        return text, False

    original = text.strip()
    msg = original

    # 1. Standardize spacing around punctuation (commas, periods, question marks, exclamation marks)
    msg = re.sub(r'\s+([,.\?!;:])', r'\1', msg)
    msg = re.sub(r'([,.\?!;:])(?=[^\s\d\.,\?!;:])', r'\1 ', msg)

    # 2. Common Roman Urdu & English shorthand and greeting corrections
    word_replacements = [
        (r'\b(aoa|aslam\s*o?\s*alkm|aslam\s*o\s*alaikum|aslaam\s*o\s*alaikum|salam\s*alikum)\b', 'Assalam-o-Alaikum'),
        (r'\b(w\s*salam|wsalam|walikum\s*assalam|walaikum\s*assalam)\b', 'Walaikum Assalam'),
        (r'\b(thnx|thx|thanx)\b', 'Thanks'),
        (r'\b(plz|pls)\b', 'please'),
        (r'\bu\b', 'you'),
        (r'\bur\b', 'your'),
        (r'\br\b', 'are'),
        (r'\bkdr\b', 'kidhar'),
        (r'\bjld\b|\bjldi\b', 'jaldi'),
        (r'\bkl\b', 'kal'),
        (r'\btm\b(?!\w)', 'tum'),
        (r'\btym\b', 'time'),
        (r'\bbcz\b|\bcoz\b|\bcuz\b', 'because'),
        (r'\bmsg\b', 'message'),
        (r'\bpic\b', 'picture'),
        (r'\bvdo\b', 'video'),
        (r'\bap\b', 'aap'),
        (r'\bhn\b', 'hain'),
        (r'\bkya\s*hal\s*h\b', 'kya haal hai'),
        (r'\bkesy\s*ho\b', 'kaise ho'),
        (r'\bkese\s*ho\b', 'kaise ho'),
    ]

    for pattern, repl in word_replacements:
        msg = re.sub(pattern, repl, msg, flags=re.IGNORECASE)

    # 3. Capitalize standalone 'i' to 'I'
    msg = re.sub(r'\bi\b', 'I', msg)

    # 4. Capitalize first letter of each sentence if Latin/Roman script
    sentences = re.split(r'([.?!]\s+)', msg)
    formatted_sentences = []
    for s in sentences:
        if s and s[0].isalpha() and s[0].islower():
            s = s[0].upper() + s[1:]
        formatted_sentences.append(s)
    msg = ''.join(formatted_sentences)

    # Capitalize very first character if lower
    if msg and msg[0].isalpha() and msg[0].islower():
        msg = msg[0].upper() + msg[1:]

    # 5. Clean extra whitespace
    msg = re.sub(r'[ \t]+', ' ', msg).strip()

    was_modified = (msg.strip() != original.strip())
    return msg, was_modified


def send_whatsapp_message(
    contact_name_or_phone: str, 
    message: str,
    platform: str = "auto"
) -> Dict[str, Any]:
    """
    Open WhatsApp chat with a contact or phone number with a pre-filled message ready to send.
    Supports both WhatsApp Desktop and WhatsApp Web (platform='auto', 'web', or 'desktop').
    Supports contact names saved in address book (e.g. 'Ali') or direct phone numbers (e.g. 0300..., +92...).
    If only a contact name is provided, automatically focuses search, types the contact name, and pastes message!
    Automatically ensures message is in proper format: if already proper, keeps it as-is; otherwise corrects and polishes it.
    """
    target = contact_name_or_phone.strip()
    raw_msg = message.strip()
    plat = (platform or "auto").strip().lower()

    if not target:
        return {"success": False, "error": "Contact name or phone number is required."}
    if not raw_msg:
        return {"success": False, "error": "Message content cannot be empty."}

    from backend.tools.whatsapp_web import (
        send_whatsapp_web_message,
        find_whatsapp_web_window,
        set_last_whatsapp_platform
    )

    # Detect if user explicitly requested web mode via argument or keyword
    is_explicit_web = (
        plat in ("web", "whatsapp web", "browser")
        or bool(re.search(r"(?i)\bweb\b", target))
        or "whatsapp web" in raw_msg.lower()
        or bool(re.search(r"(?i)\bwhatsapp\s+web\b", raw_msg))
    )

    # Clean target if it contains "(web)" or "web" tag
    if re.search(r"(?i)\bweb\b", target):
        cleaned_target = re.sub(r"(?i)[\(\[\{]?\s*\bweb\b\s*[\)\]\}]?", "", target).strip()
        if cleaned_target:
            target = cleaned_target

    if is_explicit_web:
        return send_whatsapp_web_message(target, raw_msg)

    # In auto mode: if WhatsApp Desktop is NOT running, but WhatsApp Web is open, use Web!
    if plat == "auto":
        desktop_ok, _ = _bring_whatsapp_window_to_foreground(timeout=0.6)
        if not desktop_ok:
            web_open, _, _ = find_whatsapp_web_window(timeout=0.5)
            if web_open:
                return send_whatsapp_web_message(target, raw_msg)

    set_last_whatsapp_platform("desktop")

    # Format and correct message if rough or shorthand
    clean_msg, was_formatted = clean_and_format_message(raw_msg)

    phone_num = ""
    contact_display = target

    # Copy message to Windows clipboard
    try:
        import pyperclip
        pyperclip.copy(clean_msg)
    except Exception:
        pass

    # Check if target is a phone number
    numeric_target = re.sub(r"[^\d+]", "", target)
    if len(numeric_target) >= 7 and (numeric_target.startswith("+") or numeric_target.startswith("03") or numeric_target.startswith("92")):
        phone_num = numeric_target
        if phone_num.startswith("03"):
            phone_num = "92" + phone_num[1:]
        elif phone_num.startswith("+"):
            phone_num = phone_num[1:]
    else:
        # Search in contacts.json
        entry = _find_contact_entry(target)
        if entry:
            contact_display = entry.get("name", target)
            raw_phone = entry.get("phone", "")
            if raw_phone:
                if raw_phone.startswith("03"):
                    phone_num = "92" + raw_phone[1:]
                elif raw_phone.startswith("+"):
                    phone_num = raw_phone[1:]
                else:
                    phone_num = raw_phone

    encoded_msg = urllib.parse.quote(clean_msg)
    formatted_note = "format aur correct kar ke " if was_formatted else ""

    # If phone number is known, use native direct URI
    if phone_num:
        whatsapp_uri = f"whatsapp://send?phone={phone_num}&text={encoded_msg}"
        try:
            os.startfile(whatsapp_uri)
            return {
                "success": True,
                "contact": contact_display,
                "phone": phone_num,
                "platform": "desktop",
                "message_text": clean_msg,
                "original_message": raw_msg,
                "was_formatted": was_formatted,
                "message": f"WhatsApp direct chat for '{contact_display}' (+{phone_num}) opened with message {formatted_note}drafted: '{clean_msg}'. Kya main ise send kar doon? Aap 'send kar do' bolein to main bhej doonga."
            }
        except Exception:
            set_last_whatsapp_platform("web")
            web_url = f"https://web.whatsapp.com/send?phone={phone_num}&text={encoded_msg}"
            webbrowser.open(web_url)
            return {
                "success": True,
                "contact": contact_display,
                "phone": phone_num,
                "platform": "web",
                "message_text": clean_msg,
                "original_message": raw_msg,
                "was_formatted": was_formatted,
                "message": f"Opened WhatsApp Web for '{contact_display}' with message {formatted_note}drafted: '{clean_msg}'. Kya main ise send kar doon?"
            }
    else:
        # Contact Name only: Launch WhatsApp, wait for UI ready, search contact name + paste message!
        try:
            draft_ok = _automate_whatsapp_search_and_paste(contact_display, clean_msg)
            if not draft_ok:
                # Fallback to WhatsApp Web if Desktop UI was not ready
                web_open, _, _ = find_whatsapp_web_window(timeout=0.5)
                if web_open:
                    return send_whatsapp_web_message(contact_display, clean_msg)
                return {
                    "success": False,
                    "contact": contact_display,
                    "phone": "Auto-searched by name",
                    "error": "WhatsApp open hone mein waqt le raha hai ya responsive nahi hai.",
                    "message": f"WhatsApp abhi fully open nahi ho saka. Aap ka message clipboard par copy kar diya gaya hai. Please WhatsApp ya WhatsApp Web ko screen par open karein aur dobara bolein."
                }
            return {
                "success": True,
                "contact": contact_display,
                "phone": "Auto-searched by name",
                "platform": "desktop",
                "message_text": clean_msg,
                "original_message": raw_msg,
                "was_formatted": was_formatted,
                "message": f"WhatsApp open kar ke '{contact_display}' ki chat mein message {formatted_note}draft kar diya hai: '{clean_msg}'. Kya main ise send kar doon? Aap 'send kar do' bolein to main bhej doonga."
            }
        except Exception as e:
            return {
                "success": False,
                "contact": contact_display,
                "error": f"WhatsApp error: {str(e)}",
                "message": f"WhatsApp message draft karte waqt issue aya: {str(e)}. Message clipboard par copy hai."
            }


# Re-export WhatsApp Web tools
from backend.tools.whatsapp_web import (
    open_whatsapp_web,
    send_whatsapp_web_message,
    confirm_send_whatsapp_web
)


def discard_whatsapp_status() -> Dict[str, Any]:
    """
    Discard any in-progress WhatsApp status draft, close the status posting view,
    and return WhatsApp cleanly to the main Chats screen.
    """
    from backend.tools.whatsapp_status import discard_whatsapp_status as _discard
    return _discard()


def make_whatsapp_call(contact_name_or_phone: str, call_type: str = "voice") -> Dict[str, Any]:
    """
    Start a WhatsApp Voice or Video call with a contact or phone number.
    call_type: 'voice' (default) or 'video'.
    Automatically focuses WhatsApp, opens contact conversation, and clicks Call button.
    """
    import win32gui
    import win32con
    import uiautomation as auto
    import time
    import ctypes

    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception:
        pass

    try:
        target = (contact_name_or_phone or "").strip()
        if not target:
            return {"success": False, "error": "Contact name or phone number is required."}

        c_type = (call_type or "voice").lower().strip()
        is_video = "video" in c_type
        button_name = "Video call" if is_video else "Voice call"
        display_type = "video call" if is_video else "voice call"

        phone_num = ""
        contact_display = target

        # Check if target is a phone number
        numeric_target = re.sub(r"[^\d+]", "", target)
        if len(numeric_target) >= 7 and (numeric_target.startswith("+") or numeric_target.startswith("03") or numeric_target.startswith("92")):
            phone_num = numeric_target
            if phone_num.startswith("03"):
                phone_num = "92" + phone_num[1:]
            elif phone_num.startswith("+"):
                phone_num = phone_num[1:]
        else:
            # Check saved contacts
            entry = _find_contact_entry(target)
            if entry:
                contact_display = entry.get("name", target)
                raw_phone = entry.get("phone", "")
                if raw_phone:
                    if raw_phone.startswith("03"):
                        phone_num = "92" + raw_phone[1:]
                    elif raw_phone.startswith("+"):
                        phone_num = raw_phone[1:]
                    else:
                        phone_num = raw_phone

        # Step 1: Ensure WhatsApp is in foreground and clean of drafts
        ok, hwnd = _bring_whatsapp_window_to_foreground(timeout=3.0)
        if not ok or not hwnd:
            return {"success": False, "error": "WhatsApp window could not be found or focused."}

        user32 = ctypes.windll.user32
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.15)

        from backend.tools.whatsapp_status import _get_whatsapp_doc
        doc, _ = _get_whatsapp_doc()
        if doc:
            try:
                close_btn = doc.ButtonControl(searchDepth=15, Name="Close status posting view")
                if close_btn.Exists(0.3):
                    try:
                        close_btn.Click(simulateMove=False)
                    except Exception:
                        pass
                    time.sleep(0.2)
            except Exception:
                pass

        # Step 2: Check if Call button is ALREADY visible in the active chat
        already_open = False
        if doc:
            try:
                check_btn = doc.ButtonControl(searchDepth=15, Name=button_name)
                if check_btn.Exists(0.4):
                    already_open = True
            except Exception:
                pass

        if not already_open:
            if phone_num:
                whatsapp_uri = f"whatsapp://send?phone={phone_num}"
                try:
                    os.startfile(whatsapp_uri)
                    time.sleep(1.2)
                except Exception:
                    pass
            else:
                # Search contact name using safe UI steps
                VK_ESCAPE = 0x1B
                VK_CONTROL = 0x11
                VK_RETURN = 0x0D
                VK_A = 0x41
                VK_V = 0x56
                VK_BACK = 0x08
                KEYUP = 0x0002

                def key_tap(code, delay=0.04):
                    user32.keybd_event(code, 0, 0, 0)
                    time.sleep(delay)
                    user32.keybd_event(code, 0, KEYUP, 0)
                    time.sleep(delay)

                def combo_tap(keys, delay=0.04):
                    for k in keys:
                        user32.keybd_event(k, 0, 0, 0)
                        time.sleep(delay)
                    for k in reversed(keys):
                        user32.keybd_event(k, 0, KEYUP, 0)
                        time.sleep(delay)

                # Escape any modal / top search
                key_tap(VK_ESCAPE)
                time.sleep(0.06)
                key_tap(VK_ESCAPE)
                time.sleep(0.15)

                doc, _ = _get_whatsapp_doc()
                if doc:
                    try:
                        chats_btn = doc.ButtonControl(searchDepth=12, Name="Chats")
                        if chats_btn.Exists(0.6):
                            try:
                                chats_btn.Click(simulateMove=False)
                            except Exception:
                                pass
                            time.sleep(0.25)
                    except Exception:
                        pass

                    search_box = None
                    def find_search(c, d=0):
                        nonlocal search_box
                        if d > 16 or search_box: return
                        try:
                            r = c.BoundingRectangle
                            if c.ControlTypeName == "EditControl" and r.top < 260 and r.left < 550:
                                search_box = c
                                return
                            for ch in c.GetChildren():
                                find_search(ch, d + 1)
                        except Exception:
                            pass
                    find_search(doc)

                    if search_box:
                        try:
                            sr = search_box.BoundingRectangle
                            user32.SetCursorPos((sr.left + sr.right) // 2, (sr.top + sr.bottom) // 2)
                            user32.mouse_event(0x0002, 0, 0, 0, 0)
                            user32.mouse_event(0x0004, 0, 0, 0, 0)
                            time.sleep(0.12)
                        except Exception:
                            pass
                    else:
                        rect = win32gui.GetWindowRect(hwnd)
                        user32.SetCursorPos(rect[0] + 230, rect[1] + 120)
                        user32.mouse_event(0x0002, 0, 0, 0, 0)
                        user32.mouse_event(0x0004, 0, 0, 0, 0)
                        time.sleep(0.15)

                    # Clear search
                    combo_tap([VK_CONTROL, VK_A])
                    key_tap(VK_BACK)
                    time.sleep(0.08)

                    # Type contact name
                    import pyperclip
                    pyperclip.copy(contact_display)
                    combo_tap([VK_CONTROL, VK_V])
                    time.sleep(0.8)

                    # Open chat
                    key_tap(VK_RETURN)
                    time.sleep(0.6)

        # Step 3: Find and Click Call Button (Voice call or Video call)
        clicked = False
        poll_start = time.time()
        while time.time() - poll_start < 3.5:
            doc, _ = _get_whatsapp_doc()
            if doc:
                try:
                    btn = doc.ButtonControl(searchDepth=15, Name=button_name)
                    if btn.Exists(0.3):
                        # Use direct mouse event to avoid Chromium WebView2 COM subscriber errors
                        try:
                            r = btn.BoundingRectangle
                            if r.right > r.left and r.bottom > r.top:
                                cx = (r.left + r.right) // 2
                                cy = (r.top + r.bottom) // 2
                                user32.SetCursorPos(int(cx), int(cy))
                                time.sleep(0.05)
                                user32.mouse_event(0x0002, 0, 0, 0, 0)
                                time.sleep(0.05)
                                user32.mouse_event(0x0004, 0, 0, 0, 0)
                                clicked = True
                                break
                        except Exception:
                            pass
                except Exception:
                    pass
            time.sleep(0.25)

        # Step 4: Fallback to exact WhatsApp header coordinates if UIA didn't click
        if not clicked:
            try:
                rect = win32gui.GetWindowRect(hwnd)
                win_left, win_top, win_right, win_bottom = rect
                # In WhatsApp Desktop header: Voice call is right-148, top+69; Video call is right-204, top+69
                target_x = win_right - 204 if is_video else win_right - 148
                target_y = win_top + 69
                user32.SetCursorPos(int(target_x), int(target_y))
                time.sleep(0.05)
                user32.mouse_event(0x0002, 0, 0, 0, 0)
                time.sleep(0.05)
                user32.mouse_event(0x0004, 0, 0, 0, 0)
                clicked = True
            except Exception:
                pass

        if not clicked:
            return {
                "success": False,
                "contact": contact_display,
                "error": f"WhatsApp header mein '{button_name}' button nahi mil saka.",
                "message": f"'{contact_display}' ki chat open karne ke baad call button locate nahi ho saka."
            }

        return {
            "success": True,
            "contact": contact_display,
            "call_type": "video" if is_video else "voice",
            "message": f"Ji Akmal Sir, '{contact_display}' ko WhatsApp {display_type} mila di hai!"
        }

    except Exception as e:
        return {
            "success": False,
            "contact": contact_name_or_phone,
            "error": f"WhatsApp call error: {str(e)}",
            "message": f"WhatsApp call lagate waqt technical issue aya: {str(e)}"
        }


def end_whatsapp_call() -> Dict[str, Any]:
    """
    Disconnect or end an active, outgoing, or incoming WhatsApp voice or video call.
    Locates the End Call / Leave Call button across WhatsApp windows and clicks it.
    """
    import win32gui
    import win32con
    import uiautomation as auto
    import time
    import ctypes
    from ctypes import wintypes

    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception:
        pass

    user32 = ctypes.windll.user32
    end_names = (
        "end call", "leave call", "disconnect", "hang up", "decline", 
        "cancel call", "end voice call", "end video call"
    )

    clicked = False

    # 1. Search inside WhatsApp root document
    try:
        from backend.tools.whatsapp_status import _get_whatsapp_doc
        doc, _ = _get_whatsapp_doc()
        if doc:
            def find_end_btn(c, d=0):
                nonlocal clicked
                if d > 16 or clicked: return
                try:
                    if c.ControlTypeName == "ButtonControl":
                        cname = (c.Name or "").strip().lower()
                        if any(k in cname for k in end_names):
                            r = c.BoundingRectangle
                            if r.right > r.left and r.bottom > r.top:
                                cx = (r.left + r.right) // 2
                                cy = (r.top + r.bottom) // 2
                                user32.SetCursorPos(int(cx), int(cy))
                                time.sleep(0.04)
                                user32.mouse_event(0x0002, 0, 0, 0, 0)
                                time.sleep(0.04)
                                user32.mouse_event(0x0004, 0, 0, 0, 0)
                                clicked = True
                                return
                    for ch in c.GetChildren():
                        find_end_btn(ch, d + 1)
                except Exception:
                    pass
            find_end_btn(doc)
    except Exception:
        pass

    # 2. Check top-level windows for WhatsApp Call floating window (using safe ctypes enumeration)
    call_hwnds = []
    def enum_call_wins(h, _):
        if user32.IsWindowVisible(h):
            length = user32.GetWindowTextLengthW(h)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(h, buff, length + 1)
                title = buff.value.lower()
                cls_buff = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(h, cls_buff, 256)
                cls = cls_buff.value.lower()
                if ("whatsapp" in title and "call" in title) or ("call" in title and "winui" in cls) or ("chrome" in cls and "whatsapp" in title):
                    call_hwnds.append(h)
        return 1

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(enum_call_wins), 0)

    if not clicked:
        for chwnd in call_hwnds:
            try:
                user32.SetForegroundWindow(chwnd)
                time.sleep(0.1)
                ctrl = auto.ControlFromHandle(chwnd)
                if ctrl:
                    def find_in_win(c, d=0):
                        nonlocal clicked
                        if d > 12 or clicked: return
                        if c.ControlTypeName == "ButtonControl":
                            cname = (c.Name or "").strip().lower()
                            if any(k in cname for k in end_names):
                                r = c.BoundingRectangle
                                if r.right > r.left and r.bottom > r.top:
                                    cx = (r.left + r.right) // 2
                                    cy = (r.top + r.bottom) // 2
                                    user32.SetCursorPos(int(cx), int(cy))
                                    time.sleep(0.04)
                                    user32.mouse_event(0x0002, 0, 0, 0, 0)
                                    time.sleep(0.04)
                                    user32.mouse_event(0x0004, 0, 0, 0, 0)
                                    clicked = True
                                    return
                        try:
                            for ch in c.GetChildren():
                                find_in_win(ch, d + 1)
                        except Exception:
                            pass
                    find_in_win(ctrl)
                if clicked:
                    break
            except Exception:
                pass

    # 3. Fallback: Send Alt+F4 to call window if identified
    if not clicked and call_hwnds:
        for chwnd in call_hwnds:
            user32.SetForegroundWindow(chwnd)
            time.sleep(0.05)
            user32.keybd_event(0x12, 0, 0, 0) # VK_MENU
            user32.keybd_event(0x73, 0, 0, 0) # VK_F4
            time.sleep(0.05)
            user32.keybd_event(0x73, 0, 0x0002, 0)
            user32.keybd_event(0x12, 0, 0x0002, 0)
            clicked = True
            break

    # If call was ended via in-app Escape
    if not clicked:
        VK_ESCAPE = 0x1B
        KEYUP = 0x0002
        user32.keybd_event(VK_ESCAPE, 0, 0, 0)
        time.sleep(0.04)
        user32.keybd_event(VK_ESCAPE, 0, KEYUP, 0)

    return {
        "success": True,
        "message": "WhatsApp call disconnect / end kar di hai."
    }


def toggle_whatsapp_call_mute(action: str = "toggle") -> Dict[str, Any]:
    """
    Mute or unmute the microphone during a WhatsApp voice/video call.
    action: 'mute', 'unmute', or 'toggle'.
    """
    import win32gui
    import uiautomation as auto
    import time
    import ctypes

    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception:
        pass

    user32 = ctypes.windll.user32
    mute_names = ("mute", "unmute", "turn off microphone", "turn on microphone", "mic")
    clicked = False

    try:
        from backend.tools.whatsapp_status import _get_whatsapp_doc
        doc, hwnd = _get_whatsapp_doc()
        if doc:
            def find_mute(c, d=0):
                nonlocal clicked
                if d > 16 or clicked: return
                try:
                    if c.ControlTypeName == "ButtonControl":
                        cname = (c.Name or "").strip().lower()
                        if any(k in cname for k in mute_names):
                            r = c.BoundingRectangle
                            if r.right > r.left and r.bottom > r.top:
                                cx = (r.left + r.right) // 2
                                cy = (r.top + r.bottom) // 2
                                user32.SetCursorPos(int(cx), int(cy))
                                time.sleep(0.04)
                                user32.mouse_event(0x0002, 0, 0, 0, 0)
                                time.sleep(0.04)
                                user32.mouse_event(0x0004, 0, 0, 0, 0)
                                clicked = True
                                return
                    for ch in c.GetChildren():
                        find_mute(ch, d + 1)
                except Exception:
                    pass
            find_mute(doc)
    except Exception:
        pass

    act_text = "mute" if "mute" in action.lower() else "unmute" if "unmute" in action.lower() else "toggle"
    return {
        "success": True,
        "message": f"WhatsApp call par microphone {act_text} kar diya hai."
    }


def post_whatsapp_status(
    status_text: Optional[str] = None,
    media_url: Optional[str] = None,
    status_type: str = "text",
    auto_send: bool = False,
    cycle_background: int = 3,
    cycle_font: int = 2
) -> Dict[str, Any]:
    """
    Prepare and draft a WhatsApp status.
    Supports:
    - Text status (Islamic, Jumma Mubarak, motivational, custom text) with background color and font styling.
    - TikTok / Web video status (downloads from TikTok URL or search query using yt-dlp).
    By default (auto_send=False), drafts the status on WhatsApp so user can review and approve.
    """
    from backend.tools.whatsapp_status import post_whatsapp_text_status, post_whatsapp_tiktok_status

    stype = (status_type or "text").lower().strip()
    target_media = media_url or ""

    if stype in ("tiktok", "video", "media") or (target_media and ("tiktok" in target_media.lower() or "http" in target_media.lower())):
        query = target_media or status_text or "islamic status"
        return post_whatsapp_tiktok_status(query, caption=status_text, auto_send=auto_send)

    # Text status
    content = status_text or target_media or ""
    return post_whatsapp_text_status(
        content,
        auto_send=auto_send,
        cycle_background=cycle_background,
        cycle_font=cycle_font
    )


def customize_whatsapp_status(
    new_text: Optional[str] = None,
    cycle_background: int = 1,
    cycle_font: int = 1,
    auto_send: bool = False
) -> Dict[str, Any]:
    """
    Change or customize the WhatsApp status draft:
    - Cycle / change background color (via WhatsApp Palette button).
    - Cycle / change typography / font style (via WhatsApp Font button).
    - Update or replace status text with a new quote or custom wording.
    Leaves the updated status ready on WhatsApp for user review.
    """
    from backend.tools.whatsapp_status import customize_whatsapp_status as _cust_status
    return _cust_status(
        new_text=new_text,
        cycle_background=cycle_background,
        cycle_font=cycle_font,
        auto_send=auto_send
    )


def confirm_post_whatsapp_status() -> Dict[str, Any]:
    """
    Send / upload the currently drafted WhatsApp status.
    Call when user confirms: 'upload kar do', 'post kar do', 'laga do', 'send kar do', 'upload it', etc.
    """
    from backend.tools.whatsapp_status import confirm_post_whatsapp_status as _confirm_status
    return _confirm_status()


def delete_whatsapp_status() -> Dict[str, Any]:
    """
    Delete the currently active WhatsApp status update or discard an in-progress status draft.
    """
    from backend.tools.whatsapp_status import delete_whatsapp_status as _del_status
    return _del_status()


def open_in_vscode(path: str) -> Dict[str, Any]:
    """
    Open any project folder, directory, or code file in Visual Studio Code.
    Supports Windows shorthand paths (Desktop/CounterPage, Projects/...), tilde (~),
    and absolute paths across all drives.
    """
    global _LAST_OPENED_APP
    from backend.security.path_rules import resolve_path

    clean = path.strip().strip("'\"")
    if clean.lower() in ("project", "projects", "my project", "jarvis"):
        target_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    else:
        target_path = resolve_path(clean)

    if not os.path.exists(target_path):
        return {
            "success": False,
            "error": f"Path '{path}' (resolved: '{target_path}') does not exist on this computer."
        }

    is_safe, msg = is_path_safe(target_path)
    if not is_safe:
        return {"success": False, "error": msg}

    # Locate VS Code executable or CLI
    code_bin = shutil.which("code")
    if not code_bin:
        candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
            r"C:\Program Files\Microsoft VS Code\bin\code.cmd",
            r"C:\Program Files\Microsoft VS Code\Code.exe",
        ]
        for c in candidates:
            if os.path.exists(c):
                code_bin = c
                break

    abs_target = os.path.abspath(target_path)
    try:
        if code_bin:
            subprocess.Popen(f'"{code_bin}" "{abs_target}"', shell=True)
        else:
            subprocess.Popen(f'code "{abs_target}"', shell=True)

        _LAST_OPENED_APP = "Visual Studio Code"
        name = os.path.basename(abs_target) or abs_target
        item_type = "folder" if os.path.isdir(abs_target) else "file"
        return {
            "success": True,
            "path": abs_target,
            "name": name,
            "type": item_type,
            "message": f"Opened {item_type} '{name}' in Visual Studio Code."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to open '{abs_target}' in VS Code: {str(e)}"}


def open_file_in_browser(file_path: str, inspect: bool = False) -> Dict[str, Any]:
    """
    Open and run any local HTML file, web page, or web project in the default web browser (Chrome/Edge).
    If a folder path is provided, automatically locates index.html or index.htm.
    Supports file:// URIs, Windows shorthand (Desktop/...), and absolute paths.
    """
    from backend.security.path_rules import resolve_path

    clean = file_path.strip().strip("'\"")
    if clean.startswith("file:///"):
        raw_path = clean[8:] if os.name == "nt" and clean[9:11] == ":/" else clean[7:]
        clean = urllib.parse.unquote(raw_path)

    canonical = resolve_path(clean)

    # If target is a directory, search for an HTML entrypoint
    if os.path.isdir(canonical):
        for candidate_name in ("index.html", "index.htm", "main.html", "home.html", "default.html"):
            cand = os.path.join(canonical, candidate_name)
            if os.path.exists(cand):
                canonical = cand
                break
        else:
            try:
                for f in os.listdir(canonical):
                    if f.lower().endswith((".html", ".htm")):
                        canonical = os.path.join(canonical, f)
                        break
            except Exception:
                pass

    if not os.path.exists(canonical):
        return {
            "success": False,
            "error": f"File or folder '{file_path}' does not exist on disk."
        }

    is_safe, msg = is_path_safe(canonical)
    if not is_safe:
        return {"success": False, "error": msg}

    try:
        abs_path = os.path.abspath(canonical)
        file_uri = Path(abs_path).as_uri()
        _launch_browser(file_uri, inspect=inspect)
        fname = os.path.basename(abs_path)
        msg = f"Opened '{fname}' in default browser"
        if inspect:
            msg += " with Developer Tools (Inspect mode)"
        msg += "."
        return {
            "success": True,
            "path": abs_path,
            "url": file_uri,
            "filename": fname,
            "inspect": inspect,
            "message": msg
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to open '{canonical}' in browser: {str(e)}"}


def start_local_server(project_path: str, port: int = 5500, auto_open: bool = True) -> Dict[str, Any]:
    """
    Start a lightweight local HTTP web server (e.g. for testing web apps, HTML/JS/CSS projects).
    Runs in background and optionally opens http://localhost:<port> in the default browser.
    """
    from backend.security.path_rules import resolve_path

    clean = project_path.strip().strip("'\"")
    target_path = resolve_path(clean)

    if not os.path.exists(target_path):
        return {"success": False, "error": f"Folder '{project_path}' does not exist."}

    folder = target_path if os.path.isdir(target_path) else os.path.dirname(target_path)
    abs_folder = os.path.abspath(folder)

    # Check if a server is already running on this port
    if port in _ACTIVE_LOCAL_SERVERS:
        proc = _ACTIVE_LOCAL_SERVERS[port]
        if proc.poll() is None:
            server_url = f"http://localhost:{port}"
            if auto_open:
                _launch_browser(server_url)
            return {
                "success": True,
                "port": port,
                "url": server_url,
                "already_running": True,
                "message": f"Local HTTP server is already running on {server_url}."
            }

    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(port)],
            cwd=abs_folder,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS if os.name == "nt" else 0
        )
        _ACTIVE_LOCAL_SERVERS[port] = proc
        server_url = f"http://localhost:{port}"
        if auto_open:
            import time
            time.sleep(0.4)
            _launch_browser(server_url)

        return {
            "success": True,
            "port": port,
            "url": server_url,
            "directory": abs_folder,
            "message": f"Started local HTTP server on {server_url} serving '{os.path.basename(abs_folder)}'."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to start local server on port {port}: {str(e)}"}


def open_in_terminal(path: str) -> Dict[str, Any]:
    """
    Open Windows Terminal or PowerShell in the specified directory or project folder.
    """
    from backend.security.path_rules import resolve_path

    clean = path.strip().strip("'\"")
    if clean.lower() in ("project", "projects", "my project", "jarvis"):
        target_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    else:
        target_path = resolve_path(clean)

    if not os.path.exists(target_path):
        return {"success": False, "error": f"Path '{path}' does not exist."}

    folder = target_path if os.path.isdir(target_path) else os.path.dirname(target_path)
    abs_folder = os.path.abspath(folder)

    try:
        if shutil.which("wt"):
            subprocess.Popen(["wt", "-d", abs_folder], shell=True)
        else:
            subprocess.Popen(f'start powershell -NoExit -Command "Set-Location \'{abs_folder}\'"', shell=True)

        return {
            "success": True,
            "path": abs_folder,
            "message": f"Opened terminal in '{os.path.basename(abs_folder) or abs_folder}'."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to open terminal: {str(e)}"}


def get_system_status() -> Dict[str, Any]:
    """
    Retrieve real-time hardware status metrics (CPU, RAM, Battery, Disk).
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.2)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('C:')
        
        battery = psutil.sensors_battery()
        battery_data = None
        if battery:
            battery_data = {
                "percent": int(battery.percent),
                "power_plugged": bool(battery.power_plugged),
                "time_remaining_sec": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
            }

        return {
            "success": True,
            "cpu_percent": round(cpu_percent, 1),
            "ram_percent": round(ram.percent, 1),
            "ram_used_gb": round((ram.total - ram.available) / (1024**3), 2),
            "ram_total_gb": round(ram.total / (1024**3), 2),
            "disk_free_gb": round(disk.free / (1024**3), 1),
            "battery": battery_data,
            "message": f"CPU: {cpu_percent}%, RAM: {ram.percent}% ({round(ram.used / (1024**3), 1)}GB / {round(ram.total / (1024**3), 1)}GB)"
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to retrieve system status: {str(e)}"}


def set_system_volume(action: str, level: Optional[int] = None) -> Dict[str, Any]:
    """
    Control Windows master volume: 'mute', 'unmute', 'up', 'down', 'set', 'get'.
    Supports precise levels (0-100) via Core Audio API (pycaw) with keybd_event fallback.
    """
    action = action.lower().strip()

    # Try pycaw first for accurate volume control
    try:
        from pycaw.pycaw import AudioUtilities
        device = AudioUtilities.GetSpeakers()
        vol = device.EndpointVolume
        current_scalar = vol.GetMasterVolumeLevelScalar()
        current_pct = round(current_scalar * 100)

        if action in ("mute", "unmute", "toggle_mute"):
            new_mute = not vol.GetMute() if action == "toggle_mute" else (True if action == "mute" else False)
            vol.SetMute(new_mute, None)
            state_str = "Muted" if new_mute else "Unmuted"
            return {"success": True, "action": action, "message": f"Volume {state_str} (currently at {current_pct}%)."}

        elif action in ("up", "increase", "volume_up"):
            step = (level or 15) / 100.0
            new_scalar = min(1.0, current_scalar + step)
            vol.SetMasterVolumeLevelScalar(new_scalar, None)
            vol.SetMute(0, None)
            new_pct = round(new_scalar * 100)
            return {"success": True, "action": "up", "level": new_pct, "message": f"Volume increased to {new_pct}%."}

        elif action in ("down", "decrease", "volume_down"):
            step = (level or 15) / 100.0
            new_scalar = max(0.0, current_scalar - step)
            vol.SetMasterVolumeLevelScalar(new_scalar, None)
            new_pct = round(new_scalar * 100)
            return {"success": True, "action": "down", "level": new_pct, "message": f"Volume decreased to {new_pct}%."}

        elif action == "set":
            target = max(0, min(100, (level if level is not None else 50)))
            new_scalar = target / 100.0
            vol.SetMasterVolumeLevelScalar(new_scalar, None)
            vol.SetMute(0, None)
            return {"success": True, "action": "set", "level": target, "message": f"Volume set to {target}%."}

        elif action == "get":
            is_muted = bool(vol.GetMute())
            return {"success": True, "action": "get", "level": current_pct, "muted": is_muted, "message": f"Current volume is {current_pct}% ({'Muted' if is_muted else 'Active'})."}

    except Exception as e:
        print(f"[Volume] pycaw warning: {e}, falling back to keybd_event...")

    # Fallback to keybd_event
    VK_VOLUME_MUTE = 0xAD
    VK_VOLUME_DOWN = 0xAE
    VK_VOLUME_UP = 0xAF
    try:
        if action in ("mute", "unmute", "toggle_mute"):
            ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
            return {"success": True, "message": "Volume mute toggled."}
        elif action in ("up", "increase", "volume_up"):
            for _ in range(8):
                ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
            return {"success": True, "message": "Increased volume."}
        elif action in ("down", "decrease", "volume_down"):
            for _ in range(8):
                ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
            return {"success": True, "message": "Decreased volume."}
        else:
            return {"success": False, "error": f"Unknown volume action '{action}'."}
    except Exception as e:
        return {"success": False, "error": f"Volume control failed: {str(e)}"}


def set_system_brightness(action: str, level: Optional[int] = None) -> Dict[str, Any]:
    """
    Control screen brightness: 'up', 'down', 'set', 'get'.
    Supports precise percentages (0-100) via native Windows CIM/WMI with sbc fallback.
    """
    action = action.lower().strip()

    def _get_brightness_val() -> Optional[int]:
        # Method 1: Native Windows PowerShell CIM
        try:
            ps_cmd = ["powershell", "-NoProfile", "-Command", "(Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBrightness).CurrentBrightness"]
            out = subprocess.check_output(ps_cmd, text=True, encoding="utf-8", timeout=3).strip()
            if out.isdigit():
                return int(out)
        except Exception:
            pass

        # Method 2: screen_brightness_control
        try:
            import screen_brightness_control as sbc
            val = sbc.get_brightness()
            if isinstance(val, list) and val:
                return int(val[0])
            elif isinstance(val, (int, float)):
                return int(val)
        except Exception:
            pass
        return None

    def _set_brightness_val(target: int) -> bool:
        target = max(5, min(100, target))
        # Method 1: Native Windows PowerShell WMI
        try:
            ps_cmd = [
                "powershell", "-NoProfile", "-Command",
                f"(Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {target})"
            ]
            res = subprocess.run(ps_cmd, timeout=3, capture_output=True)
            if res.returncode == 0:
                return True
        except Exception:
            pass

        # Method 2: screen_brightness_control
        try:
            import screen_brightness_control as sbc
            sbc.set_brightness(target)
            return True
        except Exception:
            pass
        return False

    current_pct = _get_brightness_val() or 50

    if action in ("get", "status"):
        return {"success": True, "brightness": current_pct, "message": f"Current screen brightness is {current_pct}%."}

    elif action in ("up", "increase"):
        step = level or 15
        new_val = min(100, current_pct + step)
        if _set_brightness_val(new_val):
            return {"success": True, "brightness": new_val, "message": f"Brightness increased to {new_val}%."}
        else:
            os.system("start ms-settings:display")
            return {"success": True, "message": "Opened display settings to adjust brightness."}

    elif action in ("down", "decrease"):
        step = level or 15
        new_val = max(5, current_pct - step)
        if _set_brightness_val(new_val):
            return {"success": True, "brightness": new_val, "message": f"Brightness decreased to {new_val}%."}
        else:
            os.system("start ms-settings:display")
            return {"success": True, "message": "Opened display settings to adjust brightness."}

    elif action == "set":
        target = max(5, min(100, (level if level is not None else 50)))
        if _set_brightness_val(target):
            return {"success": True, "brightness": target, "message": f"Brightness set to {target}%."}
        else:
            os.system("start ms-settings:display")
            return {"success": True, "message": "Opened display settings to adjust brightness."}

    else:
        return {"success": False, "error": f"Unknown brightness action '{action}'."}


def control_quick_setting(setting_name: str, action: Optional[str] = "open") -> Dict[str, Any]:
    """
    Manage Windows quick settings: 'wifi', 'bluetooth', 'airplane', 'nightlight', 'display', 'sound'.
    Actions: 'open', 'status', 'on', 'off'.
    """
    name = (setting_name or "").lower().strip()
    act = (action or "open").lower().strip()

    if name in ("wifi", "wi-fi", "wireless", "internet"):
        if act == "status":
            try:
                res = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], text=True, encoding="utf-8", timeout=4)
                ssid_match = re.search(r"SSID\s*:\s*(.+)", res)
                state_match = re.search(r"State\s*:\s*(.+)", res)
                signal_match = re.search(r"Signal\s*:\s*(.+)", res)
                ssid = ssid_match.group(1).strip() if ssid_match else "Unknown"
                state = state_match.group(1).strip() if state_match else "disconnected"
                signal = signal_match.group(1).strip() if signal_match else "0%"
                return {"success": True, "connected": state == "connected", "ssid": ssid, "signal": signal, "message": f"Wi-Fi is {state} to '{ssid}' (Signal: {signal})."}
            except Exception as e:
                return {"success": False, "error": f"Failed to get Wi-Fi status: {str(e)}"}
        elif act in ("on", "enable"):
            try:
                subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "admin=ENABLED"], timeout=4, check=False)
                return {"success": True, "message": "Wi-Fi enabled."}
            except Exception as e:
                return {"success": False, "error": f"Could not enable Wi-Fi: {str(e)}"}
        elif act in ("off", "disable"):
            try:
                subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "admin=DISABLED"], timeout=4, check=False)
                return {"success": True, "message": "Wi-Fi disabled."}
            except Exception as e:
                return {"success": False, "error": f"Could not disable Wi-Fi: {str(e)}"}
        else:
            os.system("start ms-settings:network-wifi")
            return {"success": True, "message": "Opened Wi-Fi settings."}

    elif name in ("bluetooth", "bt"):
        if act == "status":
            try:
                res = subprocess.check_output(
                    ["powershell", "-NoProfile", "-Command", "Get-PnpDevice -Class 'Bluetooth' -ErrorAction SilentlyContinue | Where-Object { $_.FriendlyName -like '*Intel*' -or $_.FriendlyName -like '*Wireless*' -or $_.FriendlyName -like '*Adapter*' } | Select-Object -ExpandProperty Status"],
                    text=True, encoding="utf-8", timeout=5
                ).strip()
                status = "Active" if "OK" in res else "Off / Unknown"
                return {"success": True, "status": status, "message": f"Bluetooth status: {status}."}
            except Exception:
                pass
        os.system("start ms-settings:bluetooth")
        return {"success": True, "message": "Opened Bluetooth settings."}

    elif name in ("airplane", "airplanemode", "flightmode"):
        os.system("start ms-settings:network-airplanemode")
        return {"success": True, "message": "Opened Airplane mode settings."}

    elif name in ("nightlight", "night_light", "readingmode"):
        os.system("start ms-settings:nightlight")
        return {"success": True, "message": "Opened Night light settings."}

    elif name in ("display", "screen"):
        os.system("start ms-settings:display")
        return {"success": True, "message": "Opened Display settings."}

    elif name in ("sound", "audio"):
        os.system("start ms-settings:sound")
        return {"success": True, "message": "Opened Sound settings."}

    else:
        os.system("start ms-settings:")
        return {"success": True, "message": f"Opened Windows settings for '{setting_name}'."}


def lock_computer() -> Dict[str, Any]:
    """
    Lock the Windows workstation immediately.
    """
    try:
        ctypes.windll.user32.LockWorkStation()
        return {"success": True, "message": "Workstation locked successfully."}
    except Exception as e:
        return {"success": False, "error": f"Failed to lock workstation: {str(e)}"}


def sleep_computer() -> Dict[str, Any]:
    """
    Put the Windows computer to sleep mode.
    """
    try:
        subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=False)
        return {"success": True, "message": "Computer placed in sleep mode."}
    except Exception as e:
        return {"success": False, "error": f"Failed to initiate sleep mode: {str(e)}"}


def shutdown_computer(delay_seconds: int = 30) -> Dict[str, Any]:
    """
    Shutdown the Windows computer with a configurable delay. (HIGH Risk - PIN Required).
    """
    try:
        subprocess.run(["shutdown", "/s", "/t", str(delay_seconds), "/c", "JARVIS initiating shutdown."], check=True)
        return {
            "success": True,
            "message": f"Computer will shut down in {delay_seconds} seconds. Run 'shutdown /a' to cancel."
        }
    except Exception as e:
        return {"success": False, "error": f"Shutdown command failed: {str(e)}"}


def restart_computer(delay_seconds: int = 30) -> Dict[str, Any]:
    """
    Restart the Windows computer with a configurable delay. (HIGH Risk - PIN Required).
    """
    try:
        subprocess.run(["shutdown", "/r", "/t", str(delay_seconds), "/c", "JARVIS initiating restart."], check=True)
        return {
            "success": True,
            "message": f"Computer will restart in {delay_seconds} seconds."
        }
    except Exception as e:
        return {"success": False, "error": f"Restart command failed: {str(e)}"}


def open_file(file_name_or_path: str, location_hint: Optional[str] = None, app_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Open any document, media file, code, or PDF using default Windows application or specific app (e.g. Notepad, VS Code).
    Supports exact paths or searches Desktop, Downloads, Documents, Projects.
    """
    if not file_name_or_path or not file_name_or_path.strip():
        return {"success": False, "error": "File name or path cannot be empty."}

    query = file_name_or_path.strip().strip('"').strip("'")

    def _launch(target_path: str) -> Tuple[bool, str]:
        abs_p = os.path.abspath(target_path)
        if app_name and app_name.strip():
            app_info = resolve_application(app_name.strip())
            if app_info:
                cmd = app_info["command"]
                subprocess.Popen(
                    f'"{cmd}" "{abs_p}"',
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                )
                return True, f"Opened '{os.path.basename(abs_p)}' with {app_info['name']}."
        os.startfile(abs_p)
        return True, f"Opened '{os.path.basename(abs_p)}' successfully."

    # 1. Direct path check
    if os.path.exists(query) and os.path.isfile(query):
        is_safe, msg = is_path_safe(query)
        if not is_safe:
            return {"success": False, "error": msg}
        try:
            ok, launch_msg = _launch(query)
            return {
                "success": True,
                "file_name": os.path.basename(query),
                "path": os.path.abspath(query),
                "message": launch_msg
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to open file: {str(e)}"}

    # 2. Smart search across common user directories
    user_home = os.path.expanduser("~")
    search_dirs = [
        os.path.join(user_home, "Desktop"),
        os.path.join(user_home, "Downloads"),
        os.path.join(user_home, "Documents"),
        os.path.join(user_home, "Pictures"),
        os.path.join(user_home, "Videos"),
        r"d:\projects",
    ]

    clean_target = os.path.basename(query).lower()
    matched_file: Optional[str] = None

    # Fast scan with depth limit to prevent hanging
    for base_dir in search_dirs:
        if not os.path.exists(base_dir):
            continue
        try:
            for root, dirs, files in os.walk(base_dir):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() not in ("node_modules", ".venv", "appdata", "$recycle.bin", "__pycache__")]
                rel_depth = len(os.path.relpath(root, base_dir).split(os.sep))
                if rel_depth > 3:
                    dirs.clear()
                    continue

                for f in files:
                    f_lower = f.lower()
                    if clean_target == f_lower or clean_target in f_lower:
                        matched_file = os.path.join(root, f)
                        break
                if matched_file:
                    break
        except Exception:
            continue
        if matched_file:
            break

    if matched_file and os.path.exists(matched_file):
        is_safe, msg = is_path_safe(matched_file)
        if not is_safe:
            return {"success": False, "error": msg}
        try:
            ok, launch_msg = _launch(matched_file)
            return {
                "success": True,
                "file_name": os.path.basename(matched_file),
                "path": os.path.abspath(matched_file),
                "message": launch_msg
            }
        except Exception as e:
            return {"success": False, "error": f"Found file but failed to open: {str(e)}"}

    return {
        "success": False,
        "error": f"Could not find any file matching '{query}' in Desktop, Downloads, Documents, or Projects folders."
    }
