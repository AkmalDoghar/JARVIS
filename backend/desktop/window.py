"""
JARVIS Dedicated Desktop App Window Manager (Phase 9 & 10)
Transforms the Next.js HUD interface into a dedicated, standalone Windows desktop
application window (Frameless/Clean App Mode) using native Chromium engine.
Removes address bars, tabs, bookmark bars, and navigation buttons for a true
native software experience.
"""

import os
import sys
import time
import subprocess
import webbrowser
from typing import Optional, List

import win32con
import win32gui


# Candidate Chromium executables supporting native --app mode
CANDIDATE_EXECUTABLES = [
    os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
]


def get_browser_app_executable() -> Optional[str]:
    """Find the first available Chromium executable that supports --app mode."""
    for exe in CANDIDATE_EXECUTABLES:
        if os.path.exists(exe):
            return exe
    return None


def is_app_mode_supported() -> bool:
    """Return True if a supported Chromium app runner is installed."""
    return get_browser_app_executable() is not None


def find_and_focus_jarvis_window() -> bool:
    """
    Search running top-level windows for JARVIS Dashboard and bring it to foreground.
    Matches window titles containing 'JARVIS', 'J.A.R.V.I.S', or 'localhost:3000'.
    """
    found_hwnd = None

    def enum_windows_callback(hwnd, _):
        nonlocal found_hwnd
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd).strip()
            # Match common dashboard window titles
            title_low = title.lower()
            if any(k in title_low for k in ("j.a.r.v.i.s", "jarvis", "localhost:3000", "3000")):
                # Avoid matching code editors, terminals, or folders containing the word 'jarvis'
                if not any(k in title_low for k in ("visual studio code", "powershell", "cmd.exe", "github desktop")):
                    found_hwnd = hwnd
                    return False
        return True

    try:
        win32gui.EnumWindows(enum_windows_callback, None)
    except Exception:
        pass

    if found_hwnd:
        try:
            # Restore if minimized
            if win32gui.IsIconic(found_hwnd):
                win32gui.ShowWindow(found_hwnd, win32con.SW_RESTORE)
            else:
                win32gui.ShowWindow(found_hwnd, win32con.SW_SHOW)

            # Bring to front & set foreground
            win32gui.BringWindowToTop(found_hwnd)
            win32gui.SetForegroundWindow(found_hwnd)
            return True
        except Exception as e:
            print(f"[Window] Focus notice: {e}")

    return False


def launch_jarvis_app_window(
    url: str = "http://localhost:3000",
    width: int = 1366,
    height: int = 820,
    force_new: bool = False
) -> bool:
    """
    Launch or focus the dedicated JARVIS Desktop Application window.
    Runs in standalone Chromium App Mode (--app=) without address bar or tabs.
    """
    if not force_new and find_and_focus_jarvis_window():
        print("[Window] Existing JARVIS Desktop window brought to foreground.")
        return True

    exe = get_browser_app_executable()
    if not exe:
        print("[Window] Native Chromium app runner not found. Falling back to default browser.")
        return webbrowser.open(url)

    # Isolated user profile for JARVIS so it never interferes with user's daily browsing
    user_home = os.path.expanduser("~")
    profile_dir = os.path.join(user_home, ".jarvis_desktop_profile")
    os.makedirs(profile_dir, exist_ok=True)

    cmd = [
        exe,
        f"--app={url}",
        f"--window-size={width},{height}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--disable-features=Translate",
        "--disable-background-mode",
        "--app-id=JARVIS_Personal_AI_Assistant"
    ]

    try:
        creation_flags = 0
        if os.name == "nt":
            creation_flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

        print(f"[Window] Launching standalone JARVIS Desktop Window via {os.path.basename(exe)}...")
        subprocess.Popen(cmd, creationflags=creation_flags)
        return True
    except Exception as e:
        print(f"[Window] Error launching native app window: {e}. Falling back to default browser.")
        return webbrowser.open(url)

