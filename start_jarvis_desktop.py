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

    cmd = [python_exe, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"]
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
    print("=" * 65)
    print("  ⚡ JARVIS AI OPERATING SYSTEM - DESKTOP SUITE (PHASE 9 & 10)")
    print("=" * 65)

    # 1. Start Backend & Frontend
    start_backend()
    start_frontend()

    # 2. Wait 2 seconds for services to initialize
    time.sleep(2)

    # 3. Start Global System-Wide Hotkey (Ctrl + Space)
    print("[Launcher] Initializing Global Hotkey (Ctrl + Space)...")
    start_hotkey_listener("ctrl_space")

    # 4. Start Windows System Tray Icon
    print("[Launcher] Mounting Arc Reactor Icon to Windows System Tray...")
    start_tray_app()

    # 5. Open Dashboard in Browser
    time.sleep(1)
    print("[Launcher] Opening JARVIS HUD Dashboard...")
    webbrowser.open("http://localhost:3000")

    print("\n" + "=" * 65)
    print("  JARVIS is running in the background!")
    print("  - Taskbar Tray: Look for the glowing Arc Reactor cyan icon.")
    print("  - Global Hotkey: Press 'Ctrl + Space' from any app to summon HUD.")
    f"  - Auto-start with Windows: {'ENABLED' if is_autostart_enabled() else 'DISABLED'}"
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
