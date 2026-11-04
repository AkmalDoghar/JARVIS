"""
JARVIS Windows System Tray Application (Phase 9 & 10)
Native Windows Taskbar Notification Area (Tray) icon with quick HUD launch,
wake-word toggle, Open Mic control, auto-start toggle, and clean exit.
Uses pywin32 win32gui (100% native, zero heavy dependencies).
"""

import os
import sys
import time
import threading
import webbrowser
from typing import Optional, Dict, Any

import win32api
import win32con
import win32gui

from backend.desktop.icon import get_icon_path
from backend.desktop.autostart import is_autostart_enabled, enable_autostart, disable_autostart
from backend.desktop.hotkey import find_and_focus_jarvis_window

WM_TRAY_MESSAGE = win32con.WM_USER + 20

# Command IDs for Tray Menu
CMD_OPEN_DASHBOARD = 1001
CMD_TOGGLE_WAKE_WORD = 1002
CMD_TOGGLE_OPEN_MIC = 1003
CMD_TOGGLE_AUTOSTART = 1004
CMD_RESTART_BACKEND = 1005
CMD_EXIT = 1006

class JarvisSystemTray:
    def __init__(self):
        self.hwnd = None
        self.nid = None
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self._wake_word_enabled = True
        self._open_mic_enabled = False

    def _create_menu(self):
        menu = win32gui.CreatePopupMenu()
        
        # 1. Open Dashboard
        win32gui.AppendMenu(menu, win32con.MF_STRING, CMD_OPEN_DASHBOARD, "🖥️  Open JARVIS Dashboard")
        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")

        # 2. Wake Word Toggle (with checkmark)
        flags = win32con.MF_STRING | (win32con.MF_CHECKED if self._wake_word_enabled else win32con.MF_UNCHECKED)
        win32gui.AppendMenu(menu, flags, CMD_TOGGLE_WAKE_WORD, "🎙️  Wake Word ('Hey JARVIS')")

        # 3. Open Mic Toggle (with checkmark)
        flags_mic = win32con.MF_STRING | (win32con.MF_CHECKED if self._open_mic_enabled else win32con.MF_UNCHECKED)
        win32gui.AppendMenu(menu, flags_mic, CMD_TOGGLE_OPEN_MIC, "⚡  Open Mic (Continuous)")

        # 4. Start with Windows (with checkmark)
        autostart_on = is_autostart_enabled()
        flags_boot = win32con.MF_STRING | (win32con.MF_CHECKED if autostart_on else win32con.MF_UNCHECKED)
        win32gui.AppendMenu(menu, flags_boot, CMD_TOGGLE_AUTOSTART, "🚀  Start with Windows")

        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
        
        # 5. Restart Backend
        win32gui.AppendMenu(menu, win32con.MF_STRING, CMD_RESTART_BACKEND, "🔄  Restart JARVIS Backend")

        # 6. Exit
        win32gui.AppendMenu(menu, win32con.MF_STRING, CMD_EXIT, "❌  Exit JARVIS Completely")
        return menu

    def _show_context_menu(self):
        menu = self._create_menu()
        pos = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(self.hwnd)
        win32gui.TrackPopupMenu(
            menu,
            win32con.TPM_LEFTALIGN | win32con.TPM_RIGHTBUTTON,
            pos[0],
            pos[1],
            0,
            self.hwnd,
            None
        )
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)

    def _handle_command(self, cmd_id: int):
        if cmd_id == CMD_OPEN_DASHBOARD:
            find_and_focus_jarvis_window()
        elif cmd_id == CMD_TOGGLE_WAKE_WORD:
            self._wake_word_enabled = not self._wake_word_enabled
            try:
                from backend.voice.wake_word import set_wake_word_status
                set_wake_word_status(enabled=self._wake_word_enabled)
            except Exception:
                pass
            print(f"[Tray] Wake word toggled: {self._wake_word_enabled}")
        elif cmd_id == CMD_TOGGLE_OPEN_MIC:
            self._open_mic_enabled = not self._open_mic_enabled
            print(f"[Tray] Open Mic toggled: {self._open_mic_enabled}")
        elif cmd_id == CMD_TOGGLE_AUTOSTART:
            if is_autostart_enabled():
                disable_autostart()
            else:
                enable_autostart()
            print(f"[Tray] Auto-start toggled. Now: {is_autostart_enabled()}")
        elif cmd_id == CMD_RESTART_BACKEND:
            print("[Tray] Restarting JARVIS backend...")
            find_and_focus_jarvis_window()
        elif cmd_id == CMD_EXIT:
            print("[Tray] Exit requested by user. Shutting down JARVIS...")
            self.stop()
            os._exit(0)

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_TRAY_MESSAGE:
            if lparam in (win32con.WM_LBUTTONUP, win32con.WM_LBUTTONDBLCLK):
                find_and_focus_jarvis_window()
            elif lparam == win32con.WM_RBUTTONUP:
                self._show_context_menu()
            return 0
        elif msg == win32con.WM_COMMAND:
            cmd_id = win32api.LOWORD(wparam)
            self._handle_command(cmd_id)
            return 0
        elif msg == win32con.WM_DESTROY:
            if self.nid:
                win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, self.nid)
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _run_tray(self):
        self.is_running = True
        hinst = win32api.GetModuleHandle(None)
        class_name = f"JARVIS_Tray_Window_{time.time()}"

        wc = win32gui.WNDCLASS()
        wc.hInstance = hinst
        wc.lpszClassName = class_name
        wc.lpfnWndProc = self._wnd_proc

        try:
            win32gui.RegisterClass(wc)
        except Exception as e:
            print(f"[Tray] Window class registration warning: {e}")

        self.hwnd = win32gui.CreateWindow(
            class_name,
            "JARVIS_Tray",
            0, 0, 0, 0, 0,
            0, 0, hinst, None
        )

        icon_path = get_icon_path()
        try:
            hicon = win32gui.LoadImage(
                0,
                icon_path,
                win32con.IMAGE_ICON,
                0, 0,
                win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            )
        except Exception as e:
            print(f"[Tray] LoadImage error: {e}. Using standard icon.")
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
        self.nid = (
            self.hwnd,
            0,
            flags,
            WM_TRAY_MESSAGE,
            hicon,
            "⚡ JARVIS AI Assistant (Ready - Ctrl+Space to summon)"
        )

        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, self.nid)
        print(f"[Tray] JARVIS Arc Reactor Tray Icon is live in Windows taskbar!")

        try:
            win32gui.PumpMessages()
        finally:
            self.is_running = False

    def start(self) -> bool:
        """Start the system tray icon in a dedicated daemon thread."""
        if self.is_running:
            return True
        self.thread = threading.Thread(target=self._run_tray, daemon=True, name="JarvisTrayThread")
        self.thread.start()
        return True

    def stop(self) -> bool:
        """Remove tray icon and destroy window."""
        if self.hwnd:
            win32gui.PostMessage(self.hwnd, win32con.WM_DESTROY, 0, 0)
        return True


# Global Tray Singleton
_tray_instance: Optional[JarvisSystemTray] = None

def get_tray_instance() -> JarvisSystemTray:
    global _tray_instance
    if _tray_instance is None:
        _tray_instance = JarvisSystemTray()
    return _tray_instance

def start_tray_app() -> bool:
    tray = get_tray_instance()
    return tray.start()

def stop_tray_app() -> bool:
    tray = get_tray_instance()
    return tray.stop()

if __name__ == "__main__":
    print("Starting JARVIS System Tray standalone test...")
    start_tray_app()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_tray_app()
        print("Tray test stopped.")
