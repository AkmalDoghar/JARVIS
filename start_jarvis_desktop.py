"""
======================================================================
  JARVIS MASTER DESKTOP LAUNCHER & SUPERVISOR (Phase 9 & 10)
  Launches Backend, Frontend, System Tray, and Global Hotkey Engine
  with single-click ease and graceful shutdown management.
======================================================================
"""

import os
import sys
import time
import signal
import subprocess
import threading
import webbrowser

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.desktop.tray import get_tray_instance, start_tray_app, stop_tray_app
from backend.desktop.hotkey import start_hotkey_listener, stop_hotkey_listener
from backend.desktop.autostart import is_autostart_enabled

BACKEND_PROCESS = None
FRONTEND_PROCESS = None

def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def start_backend():
    global BACKEND_PROCESS
    if is_port_in_use(8000):
        print("[Launcher] Port 8000 already active. Using existing backend.")
        return

    python_exe = os.path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe")
    if not os.path.exists(python_exe):
        python_exe = sys.executable

    cmd = [python_exe, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
    print("[Launcher] Starting FastAPI backend on http://127.0.0.1:8000 ...")
    BACKEND_PROCESS = subprocess.Popen(
        cmd,
        cwd=PROJECT_ROOT,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    )

def start_frontend():
    global FRONTEND_PROCESS
    if is_port_in_use(3000):
        print("[Launcher] Port 3000 already active. Using existing frontend.")
        return

    frontend_dir = os.path.join(PROJECT_ROOT, "frontend")
    print("[Launcher] Starting Next.js frontend on http://localhost:3000 ...")
    cmd = "npm run dev"
    FRONTEND_PROCESS = subprocess.Popen(
        cmd,
        cwd=frontend_dir,
        shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    )

def wait_for_port(port: int, max_wait: float = 25.0) -> bool:
    import socket
    start_t = time.time()
    while time.time() - start_t < max_wait:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex(('127.0.0.1', port)) == 0:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

SUPERVISOR_MUTEX = None

def acquire_single_instance_mutex():
    """
    Ensure only one instance of the JARVIS Desktop Supervisor runs at a time.
    If already running, brings the existing window to the foreground and exits.
    """
    global SUPERVISOR_MUTEX
    if os.name != "nt":
        return True
    try:
        import win32event
        import win32api
        import winerror

        SUPERVISOR_MUTEX = win32event.CreateMutex(None, False, "Global\\JARVIS_Desktop_Supervisor_Mutex")
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            print("[Supervisor] JARVIS Desktop Suite is already active in the background.")
            print("[Supervisor] Bringing existing JARVIS Desktop window to foreground...")
            from backend.desktop.window import find_and_focus_jarvis_window, launch_jarvis_app_window
            if not find_and_focus_jarvis_window():
                launch_jarvis_app_window("http://localhost:3000")
            sys.exit(0)
        return True
    except Exception as e:
        print(f"[Supervisor] Mutex notice: {e}")
        return True

def shutdown():
    print("\n[Launcher] Shutting down JARVIS Desktop System...")
    stop_hotkey_listener()
    stop_tray_app()

    global BACKEND_PROCESS, FRONTEND_PROCESS
    if BACKEND_PROCESS:
        try:
            BACKEND_PROCESS.terminate()
        except Exception:
            pass
    if FRONTEND_PROCESS:
        try:
            FRONTEND_PROCESS.terminate()
        except Exception:
            pass
    print("[Launcher] All JARVIS services terminated cleanly. Goodbye!")
    sys.exit(0)

def main():
    # 0. Single-instance protection
    acquire_single_instance_mutex()

    print("=" * 65)
    print("  ⚡ JARVIS AI OPERATING SYSTEM - DESKTOP SUITE (PHASE 9 & 10)")
    print("=" * 65)

    # 1. Start Backend & Frontend
    start_backend()
    start_frontend()

    # 2. Start Global System-Wide Hotkey (Ctrl + Space)
    print("[Launcher] Initializing Global Hotkey (Ctrl + Space)...")
    start_hotkey_listener("ctrl_space")

    # 3. Start Windows System Tray Icon
    print("[Launcher] Mounting Arc Reactor Icon to Windows System Tray...")
    start_tray_app()

    # 4. Wait for Next.js Frontend service to be ready before popping window
    print("[Launcher] Waiting for JARVIS Desktop UI on http://localhost:3000 ...")
    wait_for_port(3000, max_wait=25.0)

    # 5. Open Dedicated Native Desktop App Window (No browser tabs or address bar)
    print("[Launcher] Launching dedicated standalone JARVIS Desktop Window...")
    from backend.desktop.window import launch_jarvis_app_window
    launch_jarvis_app_window("http://localhost:3000")

    print("\n" + "=" * 65)
    print("  JARVIS is running in the background!")
    print("  - Taskbar Tray: Look for the glowing Arc Reactor cyan icon.")
    print("  - Global Hotkey: Press 'Ctrl + Space' from any app to summon HUD.")
    print(f"  - Auto-start with Windows: {'ENABLED' if is_autostart_enabled() else 'DISABLED'}")
    print("  Press Ctrl+C in this terminal or right-click Tray icon to Exit.")
    print("=" * 65 + "\n")

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()

if __name__ == "__main__":
    main()

