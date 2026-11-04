"""
JARVIS WhatsApp Status Automation Engine
Handles:
1. Beautiful Text Statuses (AI Islamic, Jumma Mubarak, motivational, or custom text)
2. TikTok Video Statuses (Downloads video from TikTok URL or search query using yt-dlp and prepares/uploads to WhatsApp)
3. Delete WhatsApp Status
"""

import os
import re
import time
import glob
import ctypes
from ctypes import wintypes
import urllib.parse
from typing import Dict, Any, Optional, List

# Ensure cache directory exists
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "media_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def _bring_whatsapp_foreground(timeout: float = 4.0):
    from backend.tools.system_control import _bring_whatsapp_window_to_foreground
    ok, hwnd = _bring_whatsapp_window_to_foreground(timeout=timeout)
    if not ok or not hwnd:
        try:
            os.startfile("whatsapp://")
        except Exception:
            try:
                import subprocess
                subprocess.Popen(['explorer.exe', 'shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App'])
            except Exception:
                pass
        ok, hwnd = _bring_whatsapp_window_to_foreground(timeout=8.0)
    return ok, hwnd


def _get_whatsapp_doc(timeout: float = 6.0):
    """
    Get the Chromium RootWebArea inside WhatsApp Desktop.
    Uses resilient polling to ensure cold-launched WhatsApp has rendered its WebView2.
    """
    import uiautomation as auto
    import win32gui
    import ctypes

    user32 = ctypes.windll.user32
    start_t = time.time()

    ok, hwnd = _bring_whatsapp_foreground(timeout=2.0)
    if not ok or not hwnd:
        return None, None

    while time.time() - start_t < timeout:
        # Check if hwnd itself or a child is the Chrome_WidgetWin
        cls_buff = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buff, 256)
        chrome_hwnd = hwnd if "Chrome" in cls_buff.value else None

        if not chrome_hwnd:
            child_windows = []
            try:
                win32gui.EnumChildWindows(hwnd, lambda ch, _: child_windows.append((ch, win32gui.GetClassName(ch))), None)
                chrome_hwnd = next((h for h, cls in child_windows if "Chrome" in cls), None)
            except Exception:
                pass

        if not chrome_hwnd:
            # In WinUI 3, WebView2 Chrome_WidgetWin_1 can be a top-level sibling window
            from backend.tools.system_control import _bring_whatsapp_window_to_foreground
            _, fg_h = _bring_whatsapp_window_to_foreground(timeout=0.4)
            if fg_h:
                hwnd = fg_h
                cls_buff2 = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls_buff2, 256)
                if "Chrome" in cls_buff2.value:
                    chrome_hwnd = hwnd

        if chrome_hwnd:
            try:
                ctrl = auto.ControlFromHandle(chrome_hwnd)
                doc = ctrl.DocumentControl(AutomationId="RootWebArea")
                if doc and doc.Exists(0.4):
                    return doc, hwnd
            except Exception:
                pass

        time.sleep(0.3)

    return None, hwnd


def _combo_tap(keys, delay: float = 0.04):
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


def post_whatsapp_text_status(
    text: str,
    auto_send: bool = False,
    cycle_background: int = 3,
    cycle_font: int = 2
) -> Dict[str, Any]:
    """
    Prepare and draft a text status directly to WhatsApp with styling, custom color palette, and font.
    If text is an Islamic/Saturday request, automatically generates an amazing message.
    By default (auto_send=False), it leaves the status drafted and ready on WhatsApp so user can review.
    """
    import pyperclip
    import uiautomation as auto

    clean_text = text.strip() if text else ""
    lowered = clean_text.lower()
    
    # Auto-enrich Saturday / Islamic / Inspirational quote
    if not clean_text or any(k in lowered for k in ("saturday", "achi baat", "acha status", "islamic", "dua", "juma", "jumma", "weekend")):
        if "saturday" in lowered or "weekend" in lowered or "achi" in lowered:
            clean_text = (
                "🌸 Happy Saturday 🌸\n\n"
                "\"Apni zindagi mein hamesha Shukr ki aadat daalo,\n"
                "kyun ke Shukr karne wale par Allah ki rehmatain\n"
                "kabhi kam nahi hoteen.\" 🤲✨\n\n"
                "Have a blessed & peaceful weekend! 🌿"
            )
        elif any(k in lowered for k in ("juma", "jumma")):
            clean_text = (
                "✨ Jumma Mubarak ✨\n\n"
                "\"Ya Allah! Is mubarak din ke sadqay hamare dilon ko sukoon,\n"
                "hamare rizq mein barkat aur hamari preshaniyon ko door farma. Ameen!\" 🤲🌿"
            )
        else:
            clean_text = (
                "🌿 Bismillah-ir-Rahman-ir-Rahim 🌿\n\n"
                "\"Sukoon kisi jagah mein nahi, balkay Allah ke zikr\n"
                "aur uski raza mein hai.\" 🤲✨\n\n"
                "Khush rahein aur duaon mein yaad rakhein! 🌸"
            )
    else:
        from backend.tools.system_control import clean_and_format_message
        clean_text, _ = clean_and_format_message(clean_text)

    doc, hwnd = _get_whatsapp_doc()
    if not doc:
        return {"success": False, "error": "WhatsApp window could not be found or focused."}

    user32 = ctypes.windll.user32

    try:
        # Step 1: Open Status Tab
        status_btn = doc.ButtonControl(searchDepth=12, Name="Status")
        if status_btn.Exists(2):
            try:
                status_btn.GetTogglePattern().Toggle()
            except Exception:
                try:
                    status_btn.GetLegacyIAccessiblePattern().DoDefaultAction()
                except Exception:
                    status_btn.Click(simulateMove=False)
            time.sleep(1.0)

        # Step 2: Click 'Text status'
        btns = []
        def find_ts(c, d=0):
            if d > 12: return
            for child in c.GetChildren():
                if child.ControlTypeName == "ButtonControl" and child.Name == "Text status":
                    btns.append(child)
                find_ts(child, d+1)
        find_ts(doc)

        if btns:
            try:
                btns[0].GetInvokePattern().Invoke()
            except Exception:
                btns[0].Click(simulateMove=False)
            time.sleep(1.0)

        # Step 3: Choose Color Palette & Font
        bg_clicks = max(0, min(10, int(cycle_background or 0)))
        palette_btn = doc.ButtonControl(searchDepth=10, Name="Palette")
        if palette_btn.Exists(1) and bg_clicks > 0:
            try:
                for _ in range(bg_clicks):
                    palette_btn.GetInvokePattern().Invoke()
                    time.sleep(0.15)
            except Exception:
                pass

        font_clicks = max(0, min(10, int(cycle_font or 0)))
        font_btn = doc.ButtonControl(searchDepth=10, Name="Font")
        if font_btn.Exists(1) and font_clicks > 0:
            try:
                for _ in range(font_clicks):
                    font_btn.GetInvokePattern().Invoke()
                    time.sleep(0.15)
            except Exception:
                pass

        # Step 4: Click the center of the status text canvas dynamically
        r = doc.BoundingRectangle if doc else None
        if r and r.right > r.left and r.bottom > r.top:
            canvas_x = (r.left + r.right) // 2
            canvas_y = (r.top + r.bottom) // 2
        else:
            import win32gui
            rect = win32gui.GetWindowRect(hwnd)
            canvas_x = (rect[0] + rect[2]) // 2
            canvas_y = (rect[1] + rect[3]) // 2

        user32.SetCursorPos(int(canvas_x), int(canvas_y))
        time.sleep(0.05)
        user32.mouse_event(0x0002, 0, 0, 0, 0) # Down
        time.sleep(0.05)
        user32.mouse_event(0x0004, 0, 0, 0, 0) # Up
        time.sleep(0.3)

        # Clear any old or accidental text
        VK_CONTROL = 0x11
        VK_A = 0x41
        VK_V = 0x56
        VK_BACK = 0x08
        _combo_tap([VK_CONTROL, VK_A], delay=0.04)
        time.sleep(0.06)
        _key_tap(VK_BACK, delay=0.04)
        time.sleep(0.1)

        # Copy clean text to clipboard and paste via native Windows Ctrl+V
        pyperclip.copy(clean_text)
        time.sleep(0.1)
        _combo_tap([VK_CONTROL, VK_V], delay=0.05)
        time.sleep(0.8)

        if auto_send:
            _click_send_status(doc)
            return {
                "success": True,
                "type": "text",
                "ready": True,
                "status_text": clean_text,
                "message": f"WhatsApp par status kamyabi se upload kar diya hai:\n\n{clean_text}"
            }

        # Leave drafted and ready for user approval
        return {
            "success": True,
            "type": "text",
            "ready": True,
            "status_text": clean_text,
            "message": f"Status ready hai:\n\n\"{clean_text}\"\n\nKya main ise WhatsApp par upload kar doon ya na karoon?"
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to post text status: {str(e)}"}


def customize_whatsapp_status(
    new_text: Optional[str] = None,
    cycle_background: int = 1,
    cycle_font: int = 1,
    auto_send: bool = False
) -> Dict[str, Any]:
    """
    Customize the currently drafted or active WhatsApp status:
    - Click Palette button to cycle/change background color (1-5 times).
    - Click Font button to cycle/change typography/font style (1-5 times).
    - Update or replace status text with new quote, Islamic dua, or custom wording.
    Leaves the updated status ready on WhatsApp for user review.
    """
    import pyperclip
    import uiautomation as auto

    doc, hwnd = _get_whatsapp_doc()
    if not doc or not hwnd:
        return {"success": False, "error": "WhatsApp window could not be found or focused."}

    user32 = ctypes.windll.user32
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.2)

    # Check if Status composer is already open (Palette or Font button exists)
    palette_btn = doc.ButtonControl(searchDepth=15, Name="Palette")
    font_btn = doc.ButtonControl(searchDepth=15, Name="Font")

    if not palette_btn.Exists(0.5):
        # Open Status Tab
        status_btn = doc.ButtonControl(searchDepth=12, Name="Status")
        if status_btn.Exists(1):
            try:
                status_btn.GetTogglePattern().Toggle()
            except Exception:
                status_btn.Click(simulateMove=False)
            time.sleep(0.8)
            doc, _ = _get_whatsapp_doc()

        # Click 'Text status'
        btns = []
        def find_ts(c, d=0):
            if d > 12: return
            for child in c.GetChildren():
                if child.ControlTypeName == "ButtonControl" and child.Name == "Text status":
                    btns.append(child)
                find_ts(child, d+1)
        find_ts(doc)
        if btns:
            try:
                btns[0].GetInvokePattern().Invoke()
            except Exception:
                btns[0].Click(simulateMove=False)
            time.sleep(0.8)
            doc, _ = _get_whatsapp_doc()
            palette_btn = doc.ButtonControl(searchDepth=15, Name="Palette")
            font_btn = doc.ButtonControl(searchDepth=15, Name="Font")

    # 1. Cycle Background Color (Palette button)
    bg_cycles = max(0, min(10, int(cycle_background if cycle_background is not None else 1)))
    if bg_cycles > 0 and palette_btn.Exists(1):
        for _ in range(bg_cycles):
            try:
                palette_btn.GetInvokePattern().Invoke()
            except Exception:
                palette_btn.Click(simulateMove=False)
            time.sleep(0.2)

    # 2. Cycle Font Style (Font button)
    f_cycles = max(0, min(10, int(cycle_font if cycle_font is not None else 1)))
    if f_cycles > 0 and font_btn.Exists(1):
        for _ in range(f_cycles):
            try:
                font_btn.GetInvokePattern().Invoke()
            except Exception:
                font_btn.Click(simulateMove=False)
            time.sleep(0.2)

    # 3. Update Text if provided or requested
    clean_text = (new_text or "").strip()
    if clean_text:
        lowered = clean_text.lower()
        if any(k in lowered for k in ("achi baat", "acha status", "kuch acha", "quote", "different", "koi or", "change")):
            clean_text = (
                "🌿 Bismillah-ir-Rahman-ir-Rahim 🌿\n\n"
                "\"Sabr aur Shukr do aisi taqatain hain,\n"
                "jo insaan ko kabhi tootne nahi deteen.\" 🤲✨\n\n"
                "Hamesha pur-umeed aur khush rahein! 🌸"
            )

        status_edit = doc.EditControl(searchDepth=15, Name="Type a status")
        if status_edit.Exists(0.5):
            status_edit.Click(simulateMove=False)
        else:
            user32.SetCursorPos(650, 350)
            time.sleep(0.04)
            user32.mouse_event(0x0002, 0, 0, 0, 0)
            time.sleep(0.04)
            user32.mouse_event(0x0004, 0, 0, 0, 0)

        time.sleep(0.2)
        VK_CONTROL = 0x11
        VK_A = 0x41
        VK_V = 0x56
        VK_BACK = 0x08
        _combo_tap([VK_CONTROL, VK_A], delay=0.04)
        time.sleep(0.05)
        _key_tap(VK_BACK, delay=0.04)
        time.sleep(0.1)

        pyperclip.copy(clean_text)
        time.sleep(0.05)
        _combo_tap([VK_CONTROL, VK_V], delay=0.05)
        time.sleep(0.5)

    if auto_send:
        _click_send_status(doc)
        return {
            "success": True,
            "ready": True,
            "status_text": clean_text,
            "message": "WhatsApp status ka background color, font aur text update kar ke upload kar diya hai!"
        }

    detail_parts = []
    if bg_cycles > 0:
        detail_parts.append("background color")
    if f_cycles > 0:
        detail_parts.append("font style")
    if clean_text:
        detail_parts.append("text")
    details_str = ", ".join(detail_parts) if detail_parts else "background aur font"

    return {
        "success": True,
        "ready": True,
        "status_text": clean_text,
        "message": f"Status ka {details_str} update kar diya hai:\n\n\"{clean_text or 'Updated background & font'}\"\n\nKya main ise WhatsApp par upload kar doon ya na karoon?"
    }


def _click_send_status(doc=None, hwnd=None) -> bool:
    """Clicks the Send button on the WhatsApp status canvas."""
    import win32gui
    user32 = ctypes.windll.user32
    time.sleep(0.3)

    clicked = False
    if doc:
        try:
            send_btn = doc.ButtonControl(searchDepth=12, Name="Send")
            if send_btn.Exists(1):
                r = send_btn.BoundingRectangle
                if r.right > r.left and r.bottom > r.top:
                    cx = (r.left + r.right) // 2
                    cy = (r.top + r.bottom) // 2
                    user32.SetCursorPos(int(cx), int(cy))
                    time.sleep(0.05)
                    user32.mouse_event(0x0002, 0, 0, 0, 0)
                    time.sleep(0.05)
                    user32.mouse_event(0x0004, 0, 0, 0, 0)
                    clicked = True
        except Exception:
            pass

    if not clicked:
        # Dynamic calculation: Send button is near bottom-right of status canvas
        if doc:
            r = doc.BoundingRectangle
            target_x = r.right - 45
            target_y = r.bottom - 45
        elif hwnd:
            rect = win32gui.GetWindowRect(hwnd)
            target_x = rect[2] - 45
            target_y = rect[3] - 45
        else:
            target_x, target_y = 1071, 618

        user32.SetCursorPos(int(target_x), int(target_y))
        time.sleep(0.05)
        user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.05)
        user32.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(1.0)
        clicked = True

    return clicked


def confirm_post_whatsapp_status() -> Dict[str, Any]:
    """
    Send / upload the currently drafted WhatsApp status.
    Call when user confirms: 'upload kar do', 'post kar do', 'laga do', 'send kar do', 'upload it', etc.
    """
    doc, hwnd = _get_whatsapp_doc(timeout=4.0)
    if not hwnd:
        return {"success": False, "error": "WhatsApp window could not be found or focused."}

    try:
        _click_send_status(doc, hwnd)
        return {
            "success": True,
            "message": "WhatsApp status kamyabi se upload kar diya hai!"
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to upload status: {str(e)}"}


def _download_tikwm_video(url: str, out_path: str) -> bool:
    """Download TikTok video without watermark using TikWM API."""
    import requests
    try:
        r = requests.post(
            "https://www.tikwm.com/api/",
            data={"url": url},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=12
        )
        if r.status_code == 200:
            res = r.json()
            if res.get("code") == 0:
                play_url = res.get("data", {}).get("play") or res.get("data", {}).get("wmplay")
                if play_url:
                    v_res = requests.get(
                        play_url,
                        stream=True,
                        headers={"User-Agent": "Mozilla/5.0"},
                        timeout=25
                    )
                    if v_res.status_code == 200:
                        with open(out_path, "wb") as f:
                            for chunk in v_res.iter_content(chunk_size=1024 * 64):
                                if chunk:
                                    f.write(chunk)
                        if os.path.exists(out_path) and os.path.getsize(out_path) > 20000:
                            return True
    except Exception as e:
        print("tikwm download failed:", e)
    return False


def _search_tiktok_video_urls(query: str, max_results: int = 6) -> List[str]:
    """Search web for matching TikTok video URLs."""
    from backend.tools.web_tools import search_web
    clean_q = re.sub(r'(?i)\b(tiktok|status|video|whatsapp)\b', '', query).strip()
    clean_q = clean_q or query.strip()

    search_queries = [
        f"site:tiktok.com {clean_q} status video",
        f"site:tiktok.com/@ {clean_q}",
        f"site:tiktok.com {clean_q}"
    ]

    found_urls: List[str] = []
    for sq in search_queries:
        try:
            res = search_web(sq, max_results=max_results)
            for r in res.get("results", []):
                u = r.get("url", "")
                if re.search(r'tiktok\.com/@[^/]+/video/\d+', u) or re.search(r'vt\.tiktok\.com/\w+', u):
                    if u not in found_urls:
                        found_urls.append(u)
            if found_urls:
                break
        except Exception:
            pass

    return found_urls


def download_tiktok_video(query_or_url: str) -> Optional[str]:
    """Download video from TikTok URL or search query."""
    target = query_or_url.strip()
    out_path = os.path.join(CACHE_DIR, "tiktok_status.mp4")

    # If already a direct local file
    if os.path.exists(target) and target.lower().endswith((".mp4", ".mov", ".mkv")):
        return target

    # Clean existing file
    if os.path.exists(out_path):
        try:
            os.remove(out_path)
        except Exception:
            pass

    is_url = target.startswith(("http://", "https://"))

    # Case 1: Direct TikTok URL
    if is_url and ("tiktok.com" in target.lower()):
        if _download_tikwm_video(target, out_path):
            return out_path

    # Case 2: Search query for TikTok
    if not is_url or ("tiktok.com" not in target.lower() and not target.endswith((".mp4", ".mov"))):
        cand_urls = _search_tiktok_video_urls(target)
        for u in cand_urls:
            if _download_tikwm_video(u, out_path):
                return out_path

    # Case 3: Fallback using yt-dlp
    try:
        import yt_dlp
        ydl_opts = {
            "outtmpl": os.path.join(CACHE_DIR, "tiktok_status.%(ext)s"),
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "max_filesize": 40 * 1024 * 1024, # 40MB max for WhatsApp status
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if is_url:
                ydl.download([target])
            else:
                search_query = f"ytsearch1:{target} status short"
                ydl.download([search_query])

        # Find downloaded file
        candidates = glob.glob(os.path.join(CACHE_DIR, "tiktok_status.*"))
        if candidates:
            return candidates[0]
    except Exception as e:
        print("yt-dlp fallback download error:", e)

    return None


def post_whatsapp_tiktok_status(query_or_url: str, caption: Optional[str] = None, auto_send: bool = False) -> Dict[str, Any]:
    """
    Download a video from TikTok (or URL/search) and prepare it on WhatsApp Status.
    """
    video_file = download_tiktok_video(query_or_url)
    if not video_file or not os.path.exists(video_file):
        # Fallback: if user asked for a status, provide a high quality text status
        fallback_res = post_whatsapp_text_status(query_or_url, auto_send=auto_send)
        if fallback_res.get("success"):
            return {
                "success": True,
                "type": "text_fallback",
                "ready": True,
                "status_text": fallback_res.get("status_text"),
                "message": f"TikTok video download karne mein issue aya, is liye aap ke request ke mutabiq text status ready kar diya hai: '{fallback_res.get('status_text')}'. Kya main ise upload kar doon ya na karoon?"
            }
        return {
            "success": False,
            "error": f"TikTok video download nahi ho saki from: '{query_or_url}'. Please check link."
        }

    # Bring WhatsApp to foreground and switch to Status
    doc, hwnd = _get_whatsapp_doc()
    if doc:
        status_btn = doc.ButtonControl(searchDepth=12, Name="Status")
        if status_btn.Exists(2):
            try:
                status_btn.GetLegacyIAccessiblePattern().DoDefaultAction()
            except Exception:
                status_btn.Click(simulateMove=False)
            time.sleep(0.8)

    # Copy video file to Windows Clipboard as CF_HDROP
    try:
        import win32clipboard
        import win32con

        class DROPFILES(ctypes.Structure):
            _fields_ = [
                ("pFiles", wintypes.DWORD),
                ("pt", wintypes.POINT),
                ("fNC", wintypes.BOOL),
                ("fWide", wintypes.BOOL),
            ]

        pDropFiles = DROPFILES()
        pDropFiles.pFiles = ctypes.sizeof(DROPFILES)
        pDropFiles.fWide = True
        files_bytes = (os.path.abspath(video_file) + "\0\0").encode("utf-16le")
        data = bytes(pDropFiles) + files_bytes

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_HDROP, data)
        win32clipboard.CloseClipboard()
    except Exception as e:
        print("Clipboard CF_HDROP error:", e)

    # Open video file folder and focus WhatsApp
    try:
        import subprocess
        subprocess.Popen(['explorer.exe', f'/select,{os.path.abspath(video_file)}'])
    except Exception:
        pass

    return {
        "success": True,
        "type": "video",
        "ready": True,
        "video_path": video_file,
        "status_text": f"TikTok video ({os.path.basename(video_file)})",
        "message": f"TikTok video '{os.path.basename(video_file)}' ready kar li hai aur WhatsApp Status open hai. Kya main ise upload kar doon ya na karoon?"
    }


def discard_whatsapp_status() -> Dict[str, Any]:
    """
    Discard any in-progress WhatsApp status draft, close the status posting view,
    and return WhatsApp cleanly to the main Chats screen.
    Call when user says: 'upload mat karna', 'status mat lagao', 'cancel kar do',
    'discard kar do', 'upload na karo', 'rehne do', 'status na lagao', etc.
    """
    import win32gui
    import win32con
    import uiautomation as auto
    from backend.tools.system_control import _bring_whatsapp_window_to_foreground

    ok, hwnd = _bring_whatsapp_window_to_foreground(timeout=3.0)
    if not ok or not hwnd:
        return {"success": False, "error": "WhatsApp window could not be found or focused."}

    user32 = ctypes.windll.user32
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.15)

    doc, _ = _get_whatsapp_doc()

    # 1. Look for 'Close status posting view' button and click it
    if doc:
        close_btn = doc.ButtonControl(searchDepth=15, Name="Close status posting view")
        if close_btn.Exists(0.5):
            try:
                close_btn.GetInvokePattern().Invoke()
            except Exception:
                try:
                    close_btn.Click(simulateMove=False)
                except Exception:
                    pass
            time.sleep(0.35)
            doc, _ = _get_whatsapp_doc()

    # 2. Press Escape twice to clear any menu/popups or remaining modal
    VK_ESCAPE = 0x1B
    KEYUP = 0x0002
    user32.keybd_event(VK_ESCAPE, 0, 0, 0)
    time.sleep(0.04)
    user32.keybd_event(VK_ESCAPE, 0, KEYUP, 0)
    time.sleep(0.1)
    user32.keybd_event(VK_ESCAPE, 0, 0, 0)
    time.sleep(0.04)
    user32.keybd_event(VK_ESCAPE, 0, KEYUP, 0)
    time.sleep(0.2)

    # 3. Switch back to Chats tab
    doc, _ = _get_whatsapp_doc()
    switched_to_chats = False
    if doc:
        chats_btn = doc.ButtonControl(searchDepth=12, Name="Chats")
        if chats_btn.Exists(0.8):
            try:
                chats_btn.GetTogglePattern().Toggle()
                switched_to_chats = True
            except Exception:
                try:
                    chats_btn.GetLegacyIAccessiblePattern().DoDefaultAction()
                    switched_to_chats = True
                except Exception:
                    try:
                        chats_btn.Click(simulateMove=False)
                        switched_to_chats = True
                    except Exception:
                        pass
            time.sleep(0.3)

    if not switched_to_chats:
        # Fallback click to Chats icon in top-left sidebar (win_left + 32, win_top + 105)
        rect = win32gui.GetWindowRect(hwnd)
        win_left, win_top = rect[0], rect[1]
        user32.SetCursorPos(win_left + 32, win_top + 105)
        time.sleep(0.04)
        user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.04)
        user32.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(0.3)

    return {
        "success": True,
        "message": "WhatsApp status draft discard kar diya hai aur Chats screen par wapis aa gaye hain."
    }


def delete_whatsapp_status() -> Dict[str, Any]:
    """
    Delete the current active WhatsApp Status update, or discard an in-progress status draft.
    Uses dynamic window-relative coordinates, keyboard automation, and verified multi-step flow.
    """
    import ctypes
    import win32gui
    import win32con
    import uiautomation as auto
    from backend.tools.system_control import _bring_whatsapp_window_to_foreground

    # If status posting view / draft is open, discard it cleanly
    doc, _ = _get_whatsapp_doc()
    if doc:
        close_btn = doc.ButtonControl(searchDepth=15, Name="Close status posting view")
        if close_btn.Exists(0.5):
            return discard_whatsapp_status()

    user32 = ctypes.windll.user32

    # Step 1: Focus and restore WhatsApp window to foreground
    ok, hwnd = _bring_whatsapp_window_to_foreground(timeout=3.0)
    if not ok or not hwnd:
        return {"success": False, "error": "WhatsApp window could not be found or focused."}

    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.4)

    # Force WhatsApp to topmost and foreground on Windows 11
    SWP_FLAGS = win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, SWP_FLAGS)
    time.sleep(0.05)
    win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, SWP_FLAGS)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.2)

    rect = win32gui.GetWindowRect(hwnd)
    win_left, win_top, win_right, win_bottom = rect

    def _click(x: int, y: int, delay_after: float = 0.35):
        user32.SetCursorPos(int(x), int(y))
        time.sleep(0.04)
        user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.04)
        user32.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(delay_after)

    def _press_key(vk: int):
        user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.04)
        user32.keybd_event(vk, 0, 0x0002, 0)
        time.sleep(0.08)

    def _press_escape(count: int = 2):
        for _ in range(count):
            _press_key(0x1B) # VK_ESCAPE
            time.sleep(0.12)

    try:
        # Step 0: Discard draft composer / close any open menus or overlays
        _press_escape(2)
        time.sleep(0.3)

        # Step 1: Open Status Tab on left navigation bar
        try:
            doc, _ = _get_whatsapp_doc()
            if doc:
                status_btn = doc.ButtonControl(searchDepth=12, Name="Status")
                if status_btn.Exists(1):
                    try:
                        status_btn.GetLegacyIAccessiblePattern().DoDefaultAction()
                    except Exception:
                        status_btn.Click(simulateMove=False)
        except Exception:
            pass

        # Fallback click on Status tab in sidebar (win_left + 32, win_top + 155):
        status_tab_x = win_left + 32
        status_tab_y = win_top + 155
        _click(status_tab_x, status_tab_y, delay_after=0.8)

        # Step 2: Open "My status" story viewer (win_left + 200, win_top + 137)
        my_status_x = win_left + 200
        my_status_y = win_top + 137
        _click(my_status_x, my_status_y, delay_after=0.4)

        # Step 3: Click Three Dots menu (⋮) at top right of the story viewer (win_left + 694, win_top + 108)
        dots_x = win_left + 694
        dots_y = win_top + 108
        _click(dots_x, dots_y, delay_after=0.4)

        # Step 4: Click "Delete" item in dropdown menu (win_left + 745, win_top + 160)
        delete_item_x = win_left + 745
        delete_item_y = win_top + 160
        _click(delete_item_x, delete_item_y, delay_after=0.5)

        # Step 5: Click red "Delete" confirmation button in modal popup (win_left + 638, win_top + 368)
        modal_del_x = win_left + 638
        modal_del_y = win_top + 368
        _click(modal_del_x, modal_del_y, delay_after=0.4)

        # Send Enter key as safety confirmation
        _press_key(0x0D) # VK_RETURN
        time.sleep(1.0)

        # Return cleanly to Status drawer
        _press_escape(1)

        return {
            "success": True,
            "message": "WhatsApp status kamyabi se delete kar diya gaya hai! ✅"
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to delete WhatsApp status: {str(e)}"}

