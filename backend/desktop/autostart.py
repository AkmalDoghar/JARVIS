"""
JARVIS Desktop Auto-Start Manager (Phase 10)
Manages 'Start with Windows' functionality using Windows Current User Registry.
Requires no administrator privileges (operates strictly within HKCU).
"""

import os
import sys
import winreg
from typing import Dict, Any, Optional

REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_VAL_NAME = "JARVIS_Assistant"

def _get_default_launch_command() -> str:
    """Return the absolute command to launch JARVIS silently on Windows startup."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    vbs_path = os.path.join(project_root, "start_jarvis_silent.vbs")
    bat_path = os.path.join(project_root, "start_jarvis_all.bat")
    
    # If silent VBS exists, prefer it to prevent console flash on boot
    if os.path.exists(vbs_path):
        return f'wscript.exe "{vbs_path}"'
    return f'cmd.exe /c "{bat_path}"'

def is_autostart_enabled() -> bool:
    """Check if JARVIS is currently registered to start with Windows."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, REG_VAL_NAME)
            return bool(val)
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"[AutoStart] Query warning: {e}")
        return False

def enable_autostart(custom_command: Optional[str] = None) -> bool:
    """
    Register JARVIS in Windows HKCU Run key so it boots automatically.
    """
    cmd = custom_command or _get_default_launch_command()
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, REG_VAL_NAME, 0, winreg.REG_SZ, cmd)
        print(f"[AutoStart] Successfully enabled. Launch command: {cmd}")
        return True
    except Exception as e:
        print(f"[AutoStart] Failed to enable: {e}")
        return False

def disable_autostart() -> bool:
    """
    Remove JARVIS from Windows HKCU Run key.
    """
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, REG_VAL_NAME)
        print("[AutoStart] Successfully disabled.")
        return True
    except FileNotFoundError:
        return True  # Already not present
    except Exception as e:
        print(f"[AutoStart] Failed to disable: {e}")
        return False

def get_autostart_status() -> Dict[str, Any]:
    """Return structured status of the Windows auto-start configuration."""
    enabled = is_autostart_enabled()
    cmd = None
    if enabled:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_READ) as key:
                cmd, _ = winreg.QueryValueEx(key, REG_VAL_NAME)
        except Exception:
            pass
            
    return {
        "enabled": enabled,
        "registry_key": f"HKCU\\{REG_KEY_PATH}\\{REG_VAL_NAME}",
        "command": cmd,
        "default_command": _get_default_launch_command()
    }
