"""
JARVIS Desktop & System Integration Package (Phase 9 & 10)
"""

from backend.desktop.icon import get_icon_path, generate_arc_reactor_icon
from backend.desktop.autostart import (
    is_autostart_enabled,
    enable_autostart,
    disable_autostart,
    get_autostart_status
)
from backend.desktop.hotkey import (
    start_hotkey_listener,
    stop_hotkey_listener,
    get_hotkey_status,
    find_and_focus_jarvis_window
)
from backend.desktop.tray import (
    JarvisSystemTray,
    get_tray_instance,
    start_tray_app,
    stop_tray_app
)

from backend.desktop.window import (
    launch_jarvis_app_window,
    is_app_mode_supported,
    get_browser_app_executable,
    find_and_focus_jarvis_window
)

__all__ = [
    "get_icon_path",
    "generate_arc_reactor_icon",
    "is_autostart_enabled",
    "enable_autostart",
    "disable_autostart",
    "get_autostart_status",
    "start_hotkey_listener",
    "stop_hotkey_listener",
    "get_hotkey_status",
    "find_and_focus_jarvis_window",
    "launch_jarvis_app_window",
    "is_app_mode_supported",
    "get_browser_app_executable",
    "JarvisSystemTray",
    "get_tray_instance",
    "start_tray_app",
    "stop_tray_app"
]

