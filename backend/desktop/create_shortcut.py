"""
JARVIS Desktop & Taskbar Shortcut Creator
Generates native Windows .lnk shortcuts on Desktop, Start Menu, and Taskbar
with the Arc Reactor icon, dedicated AppUserModelID, and native JARVIS.exe target.
"""

import os
import sys

def create_desktop_shortcut() -> str:
    """Create JARVIS.lnk on current user's desktop, start menu, and taskbar."""
    import win32com.client

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    ico_path = os.path.join(project_root, "backend", "desktop", "jarvis.ico")
    jarvis_exe = os.path.join(project_root, "JARVIS.exe")

    ws = win32com.client.Dispatch("WScript.Shell")

    target_path = jarvis_exe if os.path.exists(jarvis_exe) else os.path.join(project_root, ".venv", "Scripts", "pythonw.exe")
    arguments = "" if os.path.exists(jarvis_exe) else f'"{os.path.join(project_root, "start_jarvis_desktop.py")}"'

    target_folders = []
    try:
        desktop_dir = ws.SpecialFolders("Desktop")
        if desktop_dir and os.path.exists(desktop_dir):
            target_folders.append(desktop_dir)
    except Exception:
        pass

    user_home = os.path.expanduser("~")
    local_desktop = os.path.join(user_home, "Desktop")
    onedrive_desktop = os.path.join(user_home, "OneDrive", "Desktop")
    for d in (local_desktop, onedrive_desktop):
        if os.path.exists(d) and d not in target_folders:
            target_folders.append(d)

    # Start Menu Programs
    try:
        programs_dir = ws.SpecialFolders("Programs")
        if programs_dir and os.path.exists(programs_dir) and programs_dir not in target_folders:
            target_folders.append(programs_dir)
    except Exception:
        pass

    # User Pinned Taskbar
    appdata = os.environ.get("APPDATA", "")
    taskbar_dir = os.path.join(appdata, r"Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar")
    if os.path.exists(taskbar_dir) and taskbar_dir not in target_folders:
        target_folders.append(taskbar_dir)

    primary_shortcut = ""
    for folder in target_folders:
        try:
            shortcut_path = os.path.join(folder, "JARVIS.lnk")
            shortcut = ws.CreateShortcut(shortcut_path)
            shortcut.TargetPath = target_path
            shortcut.Arguments = arguments
            shortcut.WorkingDirectory = project_root
            shortcut.Description = "JARVIS - Autonomous Personal AI Operating System for Windows"
            if os.path.exists(ico_path):
                shortcut.IconLocation = f"{ico_path},0"
            shortcut.Save()

            # Set AppUserModelID on shortcut
            try:
                from win32com.propsys import propsys, pscon
                store = propsys.SHGetPropertyStoreFromParsingName(shortcut_path)
                store.SetValue(pscon.PKEY_AppUserModel_ID, propsys.PROPVARIANTType("JARVIS.Personal.AI.Assistant"))
                store.Commit()
            except Exception:
                pass

            if not primary_shortcut:
                primary_shortcut = shortcut_path
            print(f"[Shortcut] Created: {shortcut_path}")
        except Exception as e:
            print(f"[Shortcut] Notice for {folder}: {e}")

    return primary_shortcut or "JARVIS.lnk"

if __name__ == "__main__":
    create_desktop_shortcut()

