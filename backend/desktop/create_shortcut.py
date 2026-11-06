"""
JARVIS Desktop Shortcut Creator
Generates a native Windows .lnk shortcut on the Creator's Desktop
with the Arc Reactor icon and silent background launcher.
"""

import os
import sys

def create_desktop_shortcut() -> str:
    """Create JARVIS.lnk on the current user's desktop."""
    import win32com.client

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    ico_path = os.path.join(project_root, "backend", "desktop", "jarvis.ico")
    vbs_path = os.path.join(project_root, "start_jarvis_silent.vbs")

    ws = win32com.client.Dispatch("WScript.Shell")
    desktop_dir = ws.SpecialFolders("Desktop")
    shortcut_path = os.path.join(desktop_dir, "JARVIS.lnk")

    shortcut = ws.CreateShortcut(shortcut_path)
    shortcut.TargetPath = "wscript.exe"
    shortcut.Arguments = f'"{vbs_path}"'
    shortcut.WorkingDirectory = project_root
    shortcut.Description = "JARVIS - Autonomous Personal AI Operating System for Windows"
    if os.path.exists(ico_path):
        shortcut.IconLocation = f"{ico_path},0"
    shortcut.Save()

    print(f"[Shortcut] Successfully created desktop icon: {shortcut_path}")
    return shortcut_path

if __name__ == "__main__":
    create_desktop_shortcut()

