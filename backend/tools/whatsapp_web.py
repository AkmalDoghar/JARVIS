"""
JARVIS WhatsApp Web Automation Engine (Enhanced & Resilient)
Handles:
1. Browser Window & Tab Detection for WhatsApp Web & WhatsApp Business (Chrome, Edge, Brave, Firefox, Opera)
2. Tab-switching via Chrome/Edge tab search (Ctrl+Shift+A -> 'whatsapp' -> Enter)
3. Installed Chrome Apps & PWAs launch/foreground support (WhatsApp Web.lnk)
4. Non-destructive window foregrounding (preserves maximized state without de-maximizing or minimizing)
5. Direct Chat & Message Drafting via web.whatsapp.com/send URLs or live UI search
6. Two-Step Safe Confirmation & Sending on WhatsApp Web
"""

import os
import re
import time
import ctypes
from ctypes import wintypes
import urllib.parse
import webbrowser
from typing import Dict, Any, Optional, Tuple, List

# Global tracker for last drafted platform
_LAST_WHATSAPP_PLATFORM: str = "desktop"


def set_last_whatsapp_platform(platform: str):
    """Set the platform used for the most recent WhatsApp draft ('web' or 'desktop')."""
    global _LAST_WHATSAPP_PLATFORM
    _LAST_WHATSAPP_PLATFORM = platform.strip().lower()


def get_last_whatsapp_platform() -> str:
    """Get the platform used for the most recent WhatsApp draft."""
    return _LAST_WHATSAPP_PLATFORM


def _find_installed_whatsapp_web_shortcut() -> Optional[str]:
    """Find installed Chrome / Edge PWA shortcut for WhatsApp Web."""
    candidate_paths = [
        os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Chrome Apps\WhatsApp Web.lnk"),
        os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Chrome Apps\WhatsApp.lnk"),
        os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Edge Apps\WhatsApp Web.lnk"),
        os.path.expanduser(r"~\Desktop\WhatsApp Web.lnk"),
        os.path.expanduser(r"~\Desktop\WhatsApp.lnk"),
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            return p
    return None


def _combo_tap(keys: List[int], delay: float = 0.04):
    user32 = ctypes.windll.user32
    KEYUP = 0x0002
    for k in keys:
        user32.keybd_event(k, 0, 0, 0)
        time.sleep(delay)
    for k in reversed(keys):
        user32.keybd_event(k, 0, KEYUP, 0)
        time.sleep(delay)


def _key_tap(code: int, delay: float = 0.04):
    user32 = ctypes.windll.user32
    KEYUP = 0x0002
    user32.keybd_event(code, 0, 0, 0)
    time.sleep(delay)
    user32.keybd_event(code, 0, KEYUP, 0)
    time.sleep(delay)


def find_whatsapp_web_window(timeout: float = 2.0) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Search interactive desktop for active browser windows containing WhatsApp Web.
    If Chrome/Edge is open on another tab (e.g. YouTube), attempts an intelligent
    tab switch (Ctrl+Shift+A -> 'whatsapp' -> Enter) to bring WhatsApp Web to the active tab.
    Returns (found, hwnd, browser_process_name).
    """
    import win32gui
    import win32process
    import psutil
    import pyperclip

    user32 = ctypes.windll.user32

    input_desk = user32.OpenInputDesktop(0, False, 0x01FF)
    if input_desk:
        user32.SetThreadDesktop(input_desk)

    browser_processes = {
        "chrome.exe", "msedge.exe", "brave.exe", "firefox.exe",
        "opera.exe", "opera_gx.exe", "vivaldi.exe"
    }

    start_time = time.time()
    while time.time() - start_time < timeout:
        browser_hwnds = []

        def enum_proc(hwnd, lParam):
            if user32.IsWindowVisible(hwnd) and user32.GetWindowTextLengthW(hwnd) > 0:
                length = user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    proc_name = psutil.Process(pid).name().lower()
                except Exception:
                    proc_name = ""

                # Direct match: Browser window with WhatsApp in title
                if proc_name in browser_processes:
                    browser_hwnds.append((hwnd, proc_name, title))
            return True

        EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        if input_desk:
            user32.EnumDesktopWindows(input_desk, EnumProc(enum_proc), 0)
        else:
            user32.EnumWindows(EnumProc(enum_proc), 0)

        # 1. First priority: Window whose active tab ALREADY says WhatsApp
        for hwnd, proc_name, title in browser_hwnds:
            if "whatsapp" in title.lower():
                return True, hwnd, proc_name

        # 2. Second priority: If Chrome/Edge is open on another tab, switch to WhatsApp tab!
        for hwnd, proc_name, title in browser_hwnds:
            if proc_name in ("chrome.exe", "msedge.exe", "brave.exe"):
                # Bring browser to front safely without de-maximizing
                if user32.IsIconic(hwnd):
                    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                else:
                    user32.ShowWindow(hwnd, 5)  # SW_SHOW

                user32.SetForegroundWindow(hwnd)
                user32.BringWindowToTop(hwnd)
                time.sleep(0.15)

                VK_CONTROL = 0x11
                VK_SHIFT = 0x10
                VK_A = 0x41
                VK_RETURN = 0x0D
                VK_ESCAPE = 0x1B

                # Send Ctrl+Shift+A (Search open tabs in Chrome/Edge)
                _combo_tap([VK_CONTROL, VK_SHIFT, VK_A], delay=0.04)
                time.sleep(0.25)

                # Type 'whatsapp' into tab search
                try:
                    pyperclip.copy("whatsapp")
                    _combo_tap([VK_CONTROL, 0x56], delay=0.04)  # Ctrl + V
                except Exception:
                    pass
                time.sleep(0.3)

                # Press Enter to select the matched tab
                _key_tap(VK_RETURN, delay=0.04)
                time.sleep(0.4)

                # Verify if title switched to WhatsApp
                cur_len = user32.GetWindowTextLengthW(hwnd)
                cur_buf = ctypes.create_unicode_buffer(cur_len + 1)
                user32.GetWindowTextW(hwnd, cur_buf, cur_len + 1)
                if "whatsapp" in cur_buf.value.lower():
                    return True, hwnd, proc_name

                # Dismiss tab search popup if not matched
                _key_tap(VK_ESCAPE, delay=0.04)

        time.sleep(0.2)

    return False, None, None


def _bring_whatsapp_web_window_to_foreground(timeout: float = 4.0) -> Tuple[bool, Optional[int]]:
    """
    Bring the active WhatsApp Web browser window to the foreground with keyboard focus.
    Critically preserves maximized window state (NEVER calls SW_RESTORE on an already maximized window).
    """
    import win32gui

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    ok, hwnd, _ = find_whatsapp_web_window(timeout=timeout)
    if not ok or not hwnd:
        # Check if installed shortcut exists and launch it
        shortcut = _find_installed_whatsapp_web_shortcut()
        if shortcut:
            try:
                os.startfile(shortcut)
                time.sleep(2.0)
                ok, hwnd, _ = find_whatsapp_web_window(timeout=6.0)
            except Exception:
                pass

    if not ok or not hwnd:
        return False, None

    # SAFELY RESTORE WITHOUT UN-MAXIMIZING:
    # Only call SW_RESTORE if window is currently minimized (IsIconic).
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    elif user32.IsZoomed(hwnd):
        user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
    else:
        user32.ShowWindow(hwnd, 5)  # SW_SHOW

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

    user32.SetForegroundWindow(hwnd)
    user32.BringWindowToTop(hwnd)
    user32.SetFocus(hwnd)

    if fg_thread != curr_thread:
        user32.AttachThreadInput(curr_thread, fg_thread, False)

    time.sleep(0.15)
    return True, hwnd


def open_whatsapp_web(section: str = "chats") -> Dict[str, Any]:
    """
    Open WhatsApp Web in default browser or bring it to foreground if already open.
    Section options: 'chats' (default), 'status', or 'channels'.
    """
    sec = section.strip().lower() if section else "chats"
    
    # Check if already open
    ok, hwnd, proc = find_whatsapp_web_window(timeout=1.5)
    if ok and hwnd:
        _bring_whatsapp_web_window_to_foreground(timeout=2.0)
        return {
            "success": True,
            "already_open": True,
            "browser": proc,
            "section": sec,
            "message": f"WhatsApp Web ({proc}) already open tha, use screen par active kar diya hai."
        }

    # If installed shortcut exists, use it
    shortcut = _find_installed_whatsapp_web_shortcut()
    if shortcut:
        try:
            os.startfile(shortcut)
            time.sleep(2.0)
            return {
                "success": True,
                "already_open": False,
                "shortcut": shortcut,
                "section": sec,
                "message": "Installed WhatsApp Web application launch kar di hai."
            }
        except Exception:
            pass

    # Fallback to browser
    url = "https://web.whatsapp.com"
    webbrowser.open(url)
    time.sleep(1.0)

    return {
        "success": True,
        "already_open": False,
        "url": url,
        "section": sec,
        "message": f"WhatsApp Web ({url}) default browser mein open kar diya hai."
    }


def _automate_whatsapp_web_search_and_paste(contact_name: str, message: str) -> bool:
    """
    Search for a contact name inside WhatsApp Web, select them, and paste the drafted message.
    Uses official WhatsApp Web keyboard shortcuts:
    - Ctrl + Alt + / (Focus Search box)
    - Type contact name
    - Enter (Select first match and open chat)
    - Ctrl + V (Paste message into chat input box)
    """
    import pyperclip

    # Ensure message is copied to clipboard
    try:
        pyperclip.copy(message)
    except Exception:
        pass

    # Step 1: Ensure WhatsApp Web window is open and brought to foreground
    ok, hwnd = _bring_whatsapp_web_window_to_foreground(timeout=3.0)
    if not ok or not hwnd:
        # Check installed shortcut
        shortcut = _find_installed_whatsapp_web_shortcut()
        if shortcut:
            try:
                os.startfile(shortcut)
            except Exception:
                webbrowser.open("https://web.whatsapp.com")
        else:
            webbrowser.open("https://web.whatsapp.com")

        # Give WhatsApp Web sufficient time to connect and render
        time.sleep(6.0)
        ok, hwnd = _bring_whatsapp_web_window_to_foreground(timeout=8.0)
        if not ok or not hwnd:
            return False

    time.sleep(0.35)

    VK_CONTROL = 0x11
    VK_MENU = 0x12  # Alt
    VK_OEM_2 = 0xBF  # '/' (slash)
    VK_RETURN = 0x0D
    VK_V = 0x56
    VK_ESCAPE = 0x1B

    # Step 2: Clear any active search, modal, or input with Escape
    _key_tap(VK_ESCAPE, delay=0.05)
    time.sleep(0.15)

    # Step 3: Focus WhatsApp Web search box (Ctrl + Alt + /)
    _combo_tap([VK_CONTROL, VK_MENU, VK_OEM_2], delay=0.06)
    time.sleep(0.3)

    # Step 4: Type contact name via clipboard paste
    try:
        pyperclip.copy(contact_name)
        _combo_tap([VK_CONTROL, VK_V], delay=0.05)
    except Exception:
        for ch in contact_name:
            code = ord(ch.upper())
            _key_tap(code, delay=0.03)

    # Step 5: Allow WhatsApp Web filter engine time to filter contact list
    time.sleep(1.2)

    # Step 6: Press Enter to open the top matching contact's chat
    _key_tap(VK_RETURN, delay=0.06)
    time.sleep(0.6)

    # Step 7: Paste formatted message into chat input
    try:
        pyperclip.copy(message)
    except Exception:
        pass

    _combo_tap([VK_CONTROL, VK_V], delay=0.06)
    time.sleep(0.2)

    return True


def send_whatsapp_web_message(contact_name_or_phone: str, message: str) -> Dict[str, Any]:
    """
    Open WhatsApp Web, draft the message for a contact or phone number, and prepare for sending.
    Supports:
    1. Phone numbers (e.g. '03001234567', '+92...'): Uses direct web URL:
       https://web.whatsapp.com/send?phone=...&text=...
    2. Contact names (e.g. 'Mubeen', 'Ali', 'Wajid'): Resolves from contacts book or auto-searches in WhatsApp Web UI.
    """
    import pyperclip
    from backend.tools.system_control import clean_and_format_message, _find_contact_entry

    target = contact_name_or_phone.strip()
    raw_msg = message.strip()
    if not target:
        return {"success": False, "error": "Contact name or phone number is required."}
    if not raw_msg:
        return {"success": False, "error": "Message content cannot be empty."}

    # Format and correct message
    clean_msg, was_formatted = clean_and_format_message(raw_msg)
    formatted_note = "format aur correct kar ke " if was_formatted else ""

    # Always copy message to clipboard as safe backup
    try:
        pyperclip.copy(clean_msg)
    except Exception:
        pass

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

    encoded_msg = urllib.parse.quote(clean_msg)
    set_last_whatsapp_platform("web")

    # If phone number is available, open direct send URL in browser
    if phone_num:
        web_url = f"https://web.whatsapp.com/send?phone={phone_num}&text={encoded_msg}"
        webbrowser.open(web_url)

        return {
            "success": True,
            "platform": "web",
            "contact": contact_display,
            "phone": phone_num,
            "web_url": web_url,
            "message_text": clean_msg,
            "original_message": raw_msg,
            "was_formatted": was_formatted,
            "message": (
                f"WhatsApp Web par '{contact_display}' (+{phone_num}) ki chat open kar ke message "
                f"{formatted_note}draft kar diya hai: '{clean_msg}'. Kya main ise send kar doon? "
                "Aap 'send kar do' bolein to main bhej doonga."
            )
        }
    else:
        # Contact Name only: automate search and paste on WhatsApp Web
        try:
            draft_ok = _automate_whatsapp_web_search_and_paste(contact_display, clean_msg)
            if not draft_ok:
                return {
                    "success": False,
                    "platform": "web",
                    "contact": contact_display,
                    "phone": "Searched on WhatsApp Web",
                    "error": "WhatsApp Web browser window could not be focused in time.",
                    "message": (
                        f"WhatsApp Web load hone mein waqt le raha hai. Aap ka message clipboard par copy kar diya gaya hai: "
                        f"'{clean_msg}'. Please WhatsApp Web screen par open karein aur dobara bolein."
                    )
                }

            return {
                "success": True,
                "platform": "web",
                "contact": contact_display,
                "phone": "Searched on WhatsApp Web",
                "message_text": clean_msg,
                "original_message": raw_msg,
                "was_formatted": was_formatted,
                "message": (
                    f"WhatsApp Web par '{contact_display}' ki chat mein message "
                    f"{formatted_note}draft kar diya hai: '{clean_msg}'. Kya main ise send kar doon? "
                    "Aap 'send kar do' bolein to main bhej doonga."
                )
            }
        except Exception as e:
            return {
                "success": False,
                "platform": "web",
                "contact": contact_display,
                "error": f"WhatsApp Web error: {str(e)}",
                "message": f"WhatsApp Web par message draft karte waqt issue aya: {str(e)}. Message clipboard par copy hai."
            }


def confirm_send_whatsapp_web() -> Dict[str, Any]:
    """
    Send the currently drafted message on WhatsApp Web by focusing the browser window and pressing Enter.
    """
    ok, hwnd = _bring_whatsapp_web_window_to_foreground(timeout=4.0)
    if not ok or not hwnd:
        return {
            "success": False,
            "platform": "web",
            "error": "WhatsApp Web browser window could not be found or focused. Please ensure WhatsApp Web is open in Chrome or Edge."
        }

    time.sleep(0.3)
    user32 = ctypes.windll.user32
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.15)

    VK_RETURN = 0x0D
    KEYUP = 0x0002
    user32.keybd_event(VK_RETURN, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_RETURN, 0, KEYUP, 0)

    return {
        "success": True,
        "platform": "web",
        "message": "WhatsApp Web par message successfully send kar diya gaya!"
    }
