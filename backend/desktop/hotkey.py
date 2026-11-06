"""
JARVIS Global System-Wide Hotkey Engine (Phase 9 & 10)
Enables system-wide summoning of JARVIS from any application, game, or desktop state
using native Windows Win32 API RegisterHotKey.
"""

import os
import sys
import time
import ctypes
import ctypes.wintypes
import threading
import webbrowser
from typing import Callable, Optional, Dict, Any

import win32api
import win32con
import win32gui

HOTKEY_ID = 4242
_listener_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()
_is_running = False
_current_hotkey_name = "Ctrl + Space"

# Window search and summon helper for JARVIS Dashboard
def find_and_focus_jarvis_window() -> bool:
    """Delegate to dedicated window manager."""
    from backend.desktop.window import find_and_focus_jarvis_window as _focus
    return _focus()


def default_hotkey_action():
    """Default action executed when global hotkey is pressed."""
    print("[Hotkey] Global Hotkey triggered! Summoning JARVIS HUD...")
    from backend.desktop.window import find_and_focus_jarvis_window as _focus, launch_jarvis_app_window
    if not _focus():
        launch_jarvis_app_window()

    # Play subtle sci-fi activation chime in a quick thread
    def _play():
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception:
            pass
    threading.Thread(target=_play, daemon=True).start()
    threading.Thread(target=_play, daemon=True).start()


def _hotkey_worker(modifier: int, vk: int, callback: Callable):
    global _is_running
    _is_running = True

    # Register message-only window
    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = win32gui.DefWindowProc
    wc.lpszClassName = f"JARVIS_Hotkey_Class_{time.time()}"
    hinst = win32api.GetModuleHandle(None)

    try:
        class_atom = win32gui.RegisterClass(wc)
    except Exception as e:
        print(f"[Hotkey] Window class registration warning: {e}")
        class_atom = None

    hwnd = win32gui.CreateWindow(
        wc.lpszClassName,
        "JARVIS_Hotkey_Window",
        0, 0, 0, 0, 0,
        0, 0, hinst, None
    )

    # Register the hotkey using Win32 user32.dll
    user32 = ctypes.windll.user32
    fs_mod = modifier | win32con.MOD_NOREPEAT
    reg_ok = user32.RegisterHotKey(hwnd, HOTKEY_ID, fs_mod, vk)
    if not reg_ok:
        print(f"[Hotkey] Could not register {_current_hotkey_name}. Trying Alt + J fallback...")
        reg_ok = user32.RegisterHotKey(hwnd, HOTKEY_ID, win32con.MOD_ALT | win32con.MOD_NOREPEAT, ord('J'))
        if reg_ok:
            print("[Hotkey] Alt + J registered successfully.")

    if not reg_ok:
        print("[Hotkey] Failed to register any global hotkey.")
        _is_running = False
        return

    print(f"[Hotkey] Listening for global summon shortcut ({_current_hotkey_name})...")

    try:
        msg = ctypes.wintypes.MSG()
        while not _stop_event.is_set():
            # Non-blocking peek message with small sleep to allow clean thread shutdown
            has_msg = user32.PeekMessageW(ctypes.byref(msg), hwnd, 0, 0, win32con.PM_REMOVE)
            if has_msg:
                if msg.message == win32con.WM_HOTKEY and msg.wParam == HOTKEY_ID:
                    try:
                        callback()
                    except Exception as err:
                        print(f"[Hotkey] Callback error: {err}")
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            else:
                time.sleep(0.04)
    finally:
        try:
            user32.UnregisterHotKey(hwnd, HOTKEY_ID)
            win32gui.DestroyWindow(hwnd)
        except Exception:
            pass
        _is_running = False
        print("[Hotkey] Listener stopped.")


def start_hotkey_listener(
    hotkey_type: str = "ctrl_space",
    callback: Optional[Callable] = None
) -> bool:
    """
    Start the background Global Hotkey thread.
    hotkey_type options: 'ctrl_space' (Ctrl+Space), 'alt_j' (Alt+J), 'ctrl_alt_j'
    """
    global _listener_thread, _stop_event, _current_hotkey_name

    if _is_running:
        print("[Hotkey] Hotkey listener is already active.")
        return True

    _stop_event.clear()
    cb = callback or default_hotkey_action

    if hotkey_type == "alt_j":
        mod = win32con.MOD_ALT
        vk = ord('J')
        _current_hotkey_name = "Alt + J"
    elif hotkey_type == "ctrl_alt_j":
        mod = win32con.MOD_CONTROL | win32con.MOD_ALT
        vk = ord('J')
        _current_hotkey_name = "Ctrl + Alt + J"
    else:
        mod = win32con.MOD_CONTROL
        vk = win32con.VK_SPACE
        _current_hotkey_name = "Ctrl + Space"

    _listener_thread = threading.Thread(
        target=_hotkey_worker,
        args=(mod, vk, cb),
        daemon=True,
        name="JarvisHotkeyThread"
    )
    _listener_thread.start()
    return True


def stop_hotkey_listener() -> bool:
    """Stop the background hotkey thread."""
    global _stop_event
    _stop_event.set()
    return True


def get_hotkey_status() -> Dict[str, Any]:
    """Retrieve the current hotkey listener state."""
    return {
        "running": _is_running,
        "current_hotkey": _current_hotkey_name,
        "shortcut_description": f"Press {_current_hotkey_name} from anywhere in Windows to summon JARVIS HUD"
    }
