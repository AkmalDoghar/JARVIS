"""
JARVIS Web Intelligence & Online Research Tools
Phase 5 Component: Real-time web search, weather intelligence, and safe webpage reading.
Fully adheres to Rule 14 (prompt injection defense) and Rule 16 (graceful offline behavior).
"""

import os
import re
import socket
import time
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
import requests
from urllib.parse import urlparse

# Lightweight connectivity check
def is_online(timeout: float = 2.5) -> bool:
    """
    Check if the computer has an active internet connection.
    Attempts a rapid DNS ping to Cloudflare (1.1.1.1) on port 53.
    """
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("1.1.1.1", 53))
        s.close()
        return True
    except Exception:
        # Fallback HTTP check
        try:
            r = requests.get("https://www.google.com/generate_204", timeout=timeout)
            return r.status_code == 204
        except Exception:
            return False


def sanitize_untrusted_content(text: str) -> str:
    """
    Sanitize untrusted external content (Rule 14 Defense).
    Removes common script injection tags, system prompt delimiters, and cleans whitespace.
    """
    if not text:
        return ""
    # Strip script and style blocks
    cleaned = re.sub(r'<script[\s\S]*?</script>', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'<style[\s\S]*?</style>', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<[^>]+>', ' ', cleaned)
    # Neutralize prompt injection attempts (e.g. "Ignore previous instructions", "SYSTEM PROMPT:")
    cleaned = re.sub(r'(?i)\b(ignore previous instructions|disregard all previous instructions|system prompt:)\b', '[REDACTED_INJECTION_ATTEMPT]', cleaned)
    # Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


# ─────────────────────────────────────────────
# 1. Web Search
# ─────────────────────────────────────────────
def search_web(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Search the web in real-time using DuckDuckGo.
    Returns structured results with title, snippet, and source URL.
    """
    clean_query = query.strip()
    if not clean_query:
        return {"success": False, "error": "Search query cannot be empty."}

    if not is_online():
        return {
            "success": False,
            "offline": True,
            "error": "Web search is unavailable in offline mode. Please check your internet connection."
        }

    results: List[Dict[str, str]] = []
    
    # 1. Primary engine: ddgs Python package
    try:
        from ddgs import DDGS
        ddgs_client = DDGS(timeout=8)
        raw_results = list(ddgs_client.text(clean_query, max_results=max_results))
        for item in raw_results:
            title = sanitize_untrusted_content(item.get("title", ""))
            body = sanitize_untrusted_content(item.get("body", ""))
            if len(body) > 220:
                body = body[:220].rsplit(' ', 1)[0] + "..."
            href = item.get("href", "")
            if title and href:
                results.append({
                    "title": title,
                    "snippet": body,
                    "url": href
                })
    except Exception as e:
        # 2. Fallback engine: DuckDuckGo HTML Lite scraping
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = requests.post(
                "https://html.duckduckgo.com/html/",
                data={"q": clean_query},
                headers=headers,
                timeout=6
            )
            if resp.status_code == 200:
                matches = re.findall(
                    r'<a class="result__snippet[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                    resp.text,
                    re.IGNORECASE | re.DOTALL
                )
                for href, snippet in matches[:max_results]:
                    clean_snip = sanitize_untrusted_content(snippet)
                    if clean_snip:
                        results.append({
                            "title": f"Result for {clean_query}",
                            "snippet": clean_snip,
                            "url": href
                        })
        except Exception:
            pass

    if not results:
        return {
            "success": False,
            "query": clean_query,
            "results": [],
            "message": f"No reliable web search results found for '{clean_query}'. Please try rephrasing your search."
        }

    # Format human-readable output with sources
    formatted_entries = []
    for idx, r in enumerate(results, 1):
        formatted_entries.append(
            f"{idx}. **{r['title']}**\n"
            f"   {r['snippet']}\n"
            f"   Source: {r['url']}"
        )
    formatted_summary = "\n\n".join(formatted_entries)

    return {
        "success": True,
        "query": clean_query,
        "total_results": len(results),
        "results": results,
        "formatted": formatted_summary,
        "message": f"Found {len(results)} search results for '{clean_query}':\n\n{formatted_summary}"
    }


# ─────────────────────────────────────────────
# 2. Weather Intelligence
# ─────────────────────────────────────────────
def get_weather(city: str = "Lahore") -> Dict[str, Any]:
    """
    Get current real-time weather and forecast for any city or location.
    Uses wttr.in JSON API (free, zero API key required, reliable).
    """
    clean_city = city.strip() or "Lahore"

    if not is_online():
        return {
            "success": False,
            "offline": True,
            "error": "Weather service is unavailable in offline mode. Please check your internet connection."
        }

    try:
        url = f"https://wttr.in/{requests.utils.quote(clean_city)}?format=j1"
        resp = requests.get(url, timeout=6)
        if resp.status_code != 200:
            return {"success": False, "error": f"Failed to retrieve weather for '{clean_city}' (Status {resp.status_code})."}

        data = resp.json()
        current = data["current_condition"][0]
        nearest = data.get("nearest_area", [{}])[0]
        
        city_name = nearest.get("areaName", [{}])[0].get("value", clean_city)
        country = nearest.get("country", [{}])[0].get("value", "")
        
        temp_c = current.get("temp_C", "N/A")
        feels_like_c = current.get("FeelsLikeC", temp_c)
        desc = current.get("weatherDesc", [{}])[0].get("value", "Clear")
        humidity = current.get("humidity", "N/A")
        wind_kmph = current.get("windspeedKmph", "N/A")
        wind_dir = current.get("winddir16Point", "")

        spoken_summary = f"{city_name} mein mausam {desc.lower()} hai, temperature {temp_c}°C hai aur humidity {humidity}% hai."
        display_summary = (
            f"📍 **Weather for {city_name}, {country}**:\n"
            f"- **Temperature**: {temp_c}°C (Feels like {feels_like_c}°C)\n"
            f"- **Conditions**: {desc}\n"
            f"- **Humidity**: {humidity}%\n"
            f"- **Wind**: {wind_kmph} km/h {wind_dir}\n"
            f"Source: wttr.in"
        )

        return {
            "success": True,
            "city": city_name,
            "country": country,
            "temp_c": temp_c,
            "feels_like_c": feels_like_c,
            "condition": desc,
            "humidity": humidity,
            "wind_kmph": wind_kmph,
            "spoken_summary": spoken_summary,
            "message": display_summary
        }
    except Exception as e:
        return {"success": False, "error": f"Weather lookup failed: {str(e)}"}


# ─────────────────────────────────────────────
# 3. Read Webpage Content (Research / Docs)
# ─────────────────────────────────────────────
def read_webpage(url: str, max_chars: int = 2500) -> Dict[str, Any]:
    """
    Safely fetch and extract clean readable text from a documentation or web page.
    Enforces Rule 14 prompt-injection neutralization and content length limits.
    """
    clean_url = url.strip()
    if not clean_url:
        return {"success": False, "error": "URL cannot be empty."}

    parsed = urlparse(clean_url)
    if not parsed.scheme or not parsed.netloc:
        if not clean_url.startswith(("http://", "https://")):
            clean_url = "https://" + clean_url

    if not is_online():
        return {
            "success": False,
            "offline": True,
            "error": "Webpage reader is unavailable in offline mode. Please check your internet connection."
        }

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JARVIS Research Agent/2.0"
        }
        resp = requests.get(clean_url, headers=headers, timeout=8)
        if resp.status_code != 200:
            return {"success": False, "error": f"Failed to load page '{clean_url}' (HTTP {resp.status_code})."}

        # Extract title
        title_match = re.search(r'<title[^>]*>(.*?)</title>', resp.text, re.IGNORECASE | re.DOTALL)
        page_title = title_match.group(1).strip() if title_match else parsed.netloc

        # Sanitize HTML body
        clean_text = sanitize_untrusted_content(resp.text)
        
        # Enforce character truncation limit
        truncated = clean_text[:max_chars]
        if len(clean_text) > max_chars:
            truncated += "...\n[Content truncated for context window limits]"

        # Wrap in safe untrusted data container (Rule 14)
        safe_wrapped = (
            f"<untrusted_web_content url=\"{clean_url}\" title=\"{page_title}\">\n"
            f"{truncated}\n"
            f"</untrusted_web_content>"
        )

        return {
            "success": True,
            "url": clean_url,
            "title": page_title,
            "length": len(truncated),
            "content": safe_wrapped,
            "message": f"Extracted content from '{page_title}' ({clean_url}):\n\n{truncated}\n\n[Source: {clean_url}]"
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to fetch webpage '{clean_url}': {str(e)}"}


# ─────────────────────────────────────────────
# 4. YouTube Instant Auto-Play Engine
# ─────────────────────────────────────────────
def play_youtube_video(query: str, profile_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Search YouTube and automatically launch & play the top matching video in the browser.
    Resolves the direct video watch URL within ~1.2s via structured ytInitialData parsing
    with yt-dlp fallback and search page fallback.
    Always defaults strictly to creator's Primary Profile ('Default' - Rana Akmal / ranaakmalr703@gmail.com)
    unless explicitly instructed otherwise.
    """
    raw_q = query.strip()
    if not raw_q:
        return {"success": False, "error": "Search query cannot be empty."}

    # Clean query prefixes and intent words
    clean_q = re.sub(
        r'(?i)\b(play|song|gana|geet|chalao|chala do|chala|sunao|suna do|lagao|laga do|listen|search and play|search karke chalao|youtube\s+(?:per|par|pe|pr|mein|main)?)\b',
        '',
        raw_q
    ).strip()
    clean_q = re.sub(r'^[,\s\-:]+|[,\s\-:]+$', '', clean_q).strip()
    if not clean_q:
        clean_q = raw_q

    top_vid_id = None
    video_title = None
    video_url = None
    video_length = ""
    channel_name = ""

    if is_online():
        # Step 1: Rapid HTTP fetch with structured ytInitialData parsing (~1.0s)
        try:
            search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(clean_q)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            }
            req = urllib.request.Request(search_url, headers=headers)
            with urllib.request.urlopen(req, timeout=4.5) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            match = re.search(r'var ytInitialData\s*=\s*({.+?});</script>', html)
            if not match:
                match = re.search(r'ytInitialData\s*=\s*({.+?});', html)

            if match:
                try:
                    data = json.loads(match.group(1))
                    videos = []
                    def walk(node):
                        if isinstance(node, dict):
                            if "videoRenderer" in node:
                                vr = node["videoRenderer"]
                                vid = vr.get("videoId")
                                title_runs = vr.get("title", {}).get("runs", [])
                                title = title_runs[0].get("text") if title_runs else vr.get("title", {}).get("accessibility", {}).get("accessibilityData", {}).get("label")
                                length = vr.get("lengthText", {}).get("simpleText", "")
                                ch_runs = vr.get("ownerText", {}).get("runs", [])
                                ch = ch_runs[0].get("text") if ch_runs else ""
                                if vid and len(vid) == 11 and title:
                                    videos.append({
                                        "id": vid,
                                        "title": title,
                                        "length": length,
                                        "channel": ch
                                    })
                            for val in node.values():
                                walk(val)
                        elif isinstance(node, list):
                            for item in node:
                                walk(item)
                    walk(data)
                    if videos:
                        top_vid_id = videos[0]["id"]
                        video_title = videos[0]["title"]
                        video_length = videos[0]["length"]
                        channel_name = videos[0]["channel"]
                        video_url = f"https://www.youtube.com/watch?v={top_vid_id}"
                except Exception:
                    pass
        except Exception:
            pass

        # Step 2: yt-dlp fallback if structured parsing did not resolve
        if not top_vid_id:
            try:
                import yt_dlp
                ydl_opts = {"quiet": True, "extract_flat": True, "skip_download": True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    res = ydl.extract_info(f"ytsearch1:{clean_q}", download=False)
                    if res and "entries" in res and res["entries"]:
                        entry = res["entries"][0]
                        top_vid_id = entry.get("id")
                        video_url = entry.get("url") or f"https://www.youtube.com/watch?v={top_vid_id}"
                        video_title = entry.get("title") or clean_q
                        video_length = str(entry.get("duration", ""))
                        channel_name = entry.get("uploader", "")
            except Exception:
                pass

    # Step 3: Ultimate fallback if resolution fails or offline
    if not video_url:
        video_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(clean_q)}"
        video_title = clean_q

    # Target Primary Chrome Profile by default (Akmal Sir's primary profile: 'Default' - Rana Akmal / ranaakmalr703@gmail.com)
    target_prof = profile_name if profile_name else "Default"
    opened_profile = None

    try:
        from backend.tools.system_control import _launch_browser, open_chrome_profile
        res_prof = open_chrome_profile(target_prof, video_url)
        if res_prof.get("success"):
            opened_profile = res_prof.get("profile_name") or target_prof
        else:
            _launch_browser(video_url, profile=target_prof)
            opened_profile = target_prof
    except Exception:
        try:
            import webbrowser
            webbrowser.open(video_url)
        except Exception:
            pass

    disp_title = video_title or clean_q
    prof_note = f" in Chrome profile '{opened_profile}'" if opened_profile else ""
    thumbnail_url = f"https://i.ytimg.com/vi/{top_vid_id}/hqdefault.jpg" if top_vid_id else None

    return {
        "success": True,
        "video_id": top_vid_id,
        "video_url": video_url,
        "url": video_url,
        "title": disp_title,
        "duration": video_length,
        "channel": channel_name,
        "thumbnail": thumbnail_url,
        "query": clean_q,
        "profile": opened_profile or target_prof,
        "message": f"Playing '{disp_title}' on YouTube{prof_note}: {video_url}"
    }


# ─────────────────────────────────────────────
# 5. Smart Website Open & Deep Analysis
# ─────────────────────────────────────────────
def analyze_website(
    url: str,
    profile_name: Optional[str] = None,
    open_in_browser: bool = True
) -> Dict[str, Any]:
    """
    Open any website or web application, extract its content, and provide an instant deep analysis.
    If a Chrome profile is specified, opens under that authenticated Google/Chrome profile.
    Performs safe HTML text extraction and structured synthesis (Title, Domain, Summary, Highlights).
    """
    clean_url = url.strip()
    if not clean_url:
        return {"success": False, "error": "URL cannot be empty."}

    # Normalize shortcuts & portals
    lowered = clean_url.lower()
    for prefix in ("open ", "kholo ", "khol ", "mera ", "meri ", "my "):
        if lowered.startswith(prefix):
            lowered = lowered[len(prefix):].strip()

    try:
        from backend.tools.system_control import PORTAL_SHORTCUTS, _launch_browser, open_chrome_profile
    except ImportError:
        PORTAL_SHORTCUTS = {}
        _launch_browser = None
        open_chrome_profile = None

    # Known tech framework to real official documentation website mapping
    TECH_DOMAIN_MAP = {
        "next.js": "https://nextjs.org",
        "nextjs": "https://nextjs.org",
        "next js": "https://nextjs.org",
        "node.js": "https://nodejs.org",
        "nodejs": "https://nodejs.org",
        "vue.js": "https://vuejs.org",
        "vuejs": "https://vuejs.org",
        "react.js": "https://react.dev",
        "reactjs": "https://react.dev",
        "react": "https://react.dev",
        "express.js": "https://expressjs.com",
        "expressjs": "https://expressjs.com",
        "three.js": "https://threejs.org",
        "threejs": "https://threejs.org",
        "tailwind": "https://tailwindcss.com",
        "tailwindcss": "https://tailwindcss.com"
    }

    if lowered in TECH_DOMAIN_MAP:
        clean_url = TECH_DOMAIN_MAP[lowered]
    elif lowered in PORTAL_SHORTCUTS:
        clean_url = PORTAL_SHORTCUTS[lowered]
    elif not clean_url.startswith(("http://", "https://")):
        try:
            from backend.tools.chrome_bookmarks import resolve_smart_url
            res_smart = resolve_smart_url(clean_url)
            if res_smart.get("source") in ("bookmark", "history", "portal"):
                clean_url = res_smart["url"]
            else:
                clean_url = "https://" + clean_url
        except Exception:
            clean_url = "https://" + clean_url

    parsed = urllib.parse.urlparse(clean_url)
    domain = parsed.netloc or parsed.path

    # Step 1: Open in browser if requested
    opened_profile = None
    if open_in_browser:
        try:
            if profile_name and open_chrome_profile:
                prof_res = open_chrome_profile(profile_name, clean_url)
                if prof_res.get("success"):
                    opened_profile = prof_res.get("profile_name")
                elif _launch_browser:
                    _launch_browser(clean_url)
            elif _launch_browser:
                _launch_browser(clean_url)
        except Exception:
            pass

    # Step 2: Read webpage content
    read_res = read_webpage(clean_url, max_chars=4500)
    
    if read_res.get("success"):
        page_title = read_res.get("title") or domain
        raw_text = read_res.get("content", "")
        clean_body = re.sub(r'<[^>]+>', ' ', raw_text)
        clean_body = re.sub(r'\[REDACTED_INJECTION_ATTEMPT\]', '', clean_body)
        clean_body = clean_body.replace("[Content truncated for context window limits]", "").strip()
        
        # Split into sentences for meaningful highlight extraction
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_body) if len(s.strip()) > 35]
        
        seen_s = set()
        highlights = []
        for s in sentences:
            s_clean = re.sub(r'\s+', ' ', s).strip()
            if s_clean.lower() not in seen_s and len(s_clean) < 350:
                seen_s.add(s_clean.lower())
                highlights.append(s_clean)
            if len(highlights) >= 6:
                break

        summary_core = " ".join(highlights[:3]) if highlights else f"Page successfully loaded from {domain}."
        if len(summary_core) > 400:
            summary_core = summary_core[:400] + "..."

        report_lines = [
            f"--- Website Analysis: {page_title} ---",
            f"URL: {clean_url}",
            f"Domain: {domain}",
        ]
        if opened_profile:
            report_lines.append(f"Chrome Profile: {opened_profile}")
        report_lines.append(f"\nSummary:\n{summary_core}")
        if highlights:
            report_lines.append("\nKey Highlights:")
            for h in highlights[:5]:
                report_lines.append(f"- {h}")
        report_text = "\n".join(report_lines)

        return {
            "success": True,
            "url": clean_url,
            "domain": domain,
            "title": page_title,
            "profile": opened_profile,
            "summary": summary_core,
            "highlights": highlights,
            "message": report_text
        }
    else:
        err_msg = read_res.get("error", "Direct content extraction unavailable.")
        prof_info = f" in your Chrome profile '{opened_profile}'" if opened_profile else " in your browser"
        msg = (
            f"Website '{clean_url}' {prof_info} open kar di hai.\n\n"
            f"Note: Yeh page direct text scraper se access nahi hua ({err_msg}), "
            f"kyun ke is par interactive login/JavaScript session security active hai. "
            f"Aap screen par visual analysis ke liye 'inspect screen' keh sakte hain."
        )
        return {
            "success": True,
            "url": clean_url,
            "domain": domain,
            "title": domain,
            "profile": opened_profile,
            "summary": f"Opened {clean_url} in browser session.",
            "message": msg
        }
