"""
JARVIS Chrome Bookmarks & Browsing History Intelligence Engine
Phase 5 Component: Deep browser intelligence that connects directly to the user's
Chrome Bookmarks (AccountBookmarks/Bookmarks) and SQLite Browsing History across all
authenticated Google/Chrome profiles.

Enables JARVIS to automatically resolve user requests like "open Vercel", "open LMS",
"open my Gmail" to their exact personalized, bookmarked, and logged-in account URLs
instead of generic homepages.
"""

import os
import json
import sqlite3
import shutil
import tempfile
import re
import urllib.parse
from typing import Dict, Any, List, Optional


def _get_user_data_dir() -> str:
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    return os.path.join(local_app_data, "Google", "Chrome", "User Data")


def get_chrome_bookmarks(
    query: Optional[str] = None,
    profile_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extract saved bookmarks from Chrome profiles. Supports both cloud-synced
    'AccountBookmarks' and local 'Bookmarks' JSON files.
    Optionally filters by keyword query or specific profile/account.
    """
    from backend.tools.system_control import get_chrome_profiles

    profiles = get_chrome_profiles()
    user_data = _get_user_data_dir()

    target_dirs = []
    if profile_name:
        p_clean = profile_name.lower().strip()
        matched = None
        for p in profiles:
            if str(p.get("account_number")) == p_clean or any(a in p_clean or p_clean in a for a in p.get("aliases", [])):
                matched = p
                break
        if matched:
            target_dirs = [(matched["dir_name"], matched.get("gaia_name") or matched.get("name"), matched.get("account_number"))]

    if not target_dirs:
        target_dirs = [(p["dir_name"], p.get("gaia_name") or p.get("name"), p.get("account_number")) for p in profiles]

    results: List[Dict[str, Any]] = []
    for dir_name, prof_label, acc_num in target_dirs:
        p_dir = os.path.join(user_data, dir_name)
        for fname in ("AccountBookmarks", "Bookmarks"):
            bm_file = os.path.join(p_dir, fname)
            if not os.path.exists(bm_file):
                continue
            try:
                with open(bm_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                def extract_nodes(node: dict, folder: str = ""):
                    if node.get("type") == "url":
                        t = node.get("name", "")
                        u = node.get("url", "")
                        if u.startswith(("http://", "https://")):
                            if query:
                                q_l = query.lower().strip()
                                if q_l in t.lower() or q_l in u.lower() or q_l in folder.lower():
                                    results.append({
                                        "profile_name": prof_label,
                                        "profile_dir": dir_name,
                                        "account_number": acc_num,
                                        "title": t,
                                        "url": u,
                                        "folder": folder,
                                        "source": "bookmark"
                                    })
                            else:
                                results.append({
                                    "profile_name": prof_label,
                                    "profile_dir": dir_name,
                                    "account_number": acc_num,
                                    "title": t,
                                    "url": u,
                                    "folder": folder,
                                    "source": "bookmark"
                                })
                    for ch in node.get("children", []):
                        f_name = node.get("name", "") if node.get("type") == "folder" else folder
                        extract_nodes(ch, folder=f_name)

                for r in data.get("roots", {}).values():
                    extract_nodes(r)
            except Exception:
                pass

    return results


def search_chrome_history(
    query: Optional[str] = None,
    profile_name: Optional[str] = None,
    limit: int = 40
) -> List[Dict[str, Any]]:
    """
    Safely query Chrome's SQLite History database without locking issues by copying
    to a temporary file. Returns visited web pages ordered by visit_count DESC.
    """
    from backend.tools.system_control import get_chrome_profiles

    profiles = get_chrome_profiles()
    user_data = _get_user_data_dir()

    target_dirs = []
    if profile_name:
        p_clean = profile_name.lower().strip()
        matched = None
        for p in profiles:
            if str(p.get("account_number")) == p_clean or any(a in p_clean or p_clean in a for a in p.get("aliases", [])):
                matched = p
                break
        if matched:
            target_dirs = [(matched["dir_name"], matched.get("gaia_name") or matched.get("name"), matched.get("account_number"))]

    if not target_dirs:
        target_dirs = [(p["dir_name"], p.get("gaia_name") or p.get("name"), p.get("account_number")) for p in profiles]

    results: List[Dict[str, Any]] = []
    for dir_name, prof_label, acc_num in target_dirs:
        h_file = os.path.join(user_data, dir_name, "History")
        if not os.path.exists(h_file):
            continue
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tf:
                tmp_path = tf.name
            shutil.copy2(h_file, tmp_path)
            conn = sqlite3.connect(tmp_path)
            cur = conn.cursor()
            if query:
                sql = "SELECT title, url, visit_count FROM urls WHERE (title LIKE ? OR url LIKE ?) AND visit_count > 0 ORDER BY visit_count DESC LIMIT ?"
                cur.execute(sql, (f"%{query}%", f"%{query}%", limit))
            else:
                sql = "SELECT title, url, visit_count FROM urls WHERE visit_count > 1 ORDER BY visit_count DESC LIMIT ?"
                cur.execute(sql, (limit,))

            for title, url, vc in cur.fetchall():
                if url.startswith(("http://", "https://")):
                    results.append({
                        "profile_name": prof_label,
                        "profile_dir": dir_name,
                        "account_number": acc_num,
                        "title": title or url,
                        "url": url,
                        "visit_count": vc,
                        "source": "history"
                    })
            conn.close()
        except Exception:
            pass
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    results.sort(key=lambda x: x.get("visit_count", 0), reverse=True)
    return results[:limit]


def score_item(item: Dict[str, Any], query: str) -> float:
    """Calculate matching score between user query and a bookmark/history candidate."""
    title = (item.get("title") or "").lower()
    url = (item.get("url") or "").lower()
    q = query.lower().strip()
    all_tokens = [t for t in q.split() if len(t) > 1]

    # Filter out generic qualifier stop words if brand tokens exist
    stop_words = {"dashboard", "portal", "website", "account", "site", "page", "open", "kro", "karo", "chalao", "mera", "meri", "khol"}
    meaningful = [t for t in all_tokens if t not in stop_words]
    tokens = meaningful if meaningful else all_tokens

    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.lower()

    score = 0.0

    # 1. Exact match on title or domain
    if q == title:
        score += 150
    elif q == domain or f"www.{q}" == domain:
        score += 130
    elif q in title:
        score += 65
    elif q in domain:
        score += 55
    elif q in path:
        score += 45

    # 2. Token coverage
    if tokens:
        tokens_in_title = sum(1 for t in tokens if t in title)
        tokens_in_url = sum(1 for t in tokens if t in url)
        score += (tokens_in_title * 35) + (tokens_in_url * 20)
        if tokens_in_title == len(tokens):
            score += 45

    # 3. Source weight: Bookmarks have intentional user affinity
    if item.get("source") == "bookmark":
        score += 35

    # 4. Visit count boost (up to 30 points)
    vc = item.get("visit_count", 0)
    score += min(vc * 0.8, 30)

    # 5. Fuzzy matching for typos (e.g. "netlift" -> "netlify", "leetcord" -> "leetcode")
    import difflib
    title_words = re.findall(r'[a-zA-Z0-9]+', title)
    domain_words = re.findall(r'[a-zA-Z0-9]+', domain)
    all_words = title_words + domain_words
    if tokens:
        for t in tokens:
            best_r = 0.0
            for w in all_words:
                r = difflib.SequenceMatcher(None, t, w).ratio()
                if r > best_r:
                    best_r = r
            if best_r >= 0.75:
                score += best_r * 80

    return score


def resolve_smart_url(query_or_url: str, profile_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Intelligently resolve a requested website or portal name against the user's
    Chrome Bookmarks, Browsing History, and Portal shortcuts.
    Returns the exact authenticated account URL and designated Chrome profile.
    """
    raw = query_or_url.strip()
    lowered = raw.lower()

    # 1. Explicit Direct URL (http:// or https://)
    if raw.startswith(("http://", "https://")) and not any(k in lowered for k in ("google.com/search", "youtube.com/results")):
        return {
            "url": raw,
            "title": raw,
            "source": "direct",
            "profile_name": profile_name
        }

    # Clean leading verbs, fillers, and possessives
    cleaned = lowered
    for _ in range(3):
        cleaned = re.sub(r'^(?:yar\s+|bhai\s+|please\s+|sir\s+)', '', cleaned).strip()
        cleaned = re.sub(r'^(?:mera\s+|meri\s+|my\s+|apna\s+|apni\s+)', '', cleaned).strip()
        cleaned = re.sub(r'^(?:open\s+|kholo\s+|khol\s+|launch\s+|start\s+|chalao\s+|go\s+to\s+|browse\s+|visit\s+)', '', cleaned).strip()

    # Clean trailing action verbs
    cleaned = re.sub(r'\s+(?:open\s+(?:kro|karo|kardo|karein)|kholo|khol\s+do|chalao|chala\s+do|launch\s+karo|open|kholo|chalao)$', '', cleaned).strip()

    # Core key without generic qualifiers (dashboard, portal, website, account, site, page)
    core_key = re.sub(r'\s+(?:dashboard|portal|website|account|site|page|link|app)$', '', cleaned).strip()
    core_key = re.sub(r'^(?:dashboard|portal|website|account|site|page|link|app)\s+', '', core_key).strip()

    # 2. Check direct portal & technology shortcuts
    try:
        from backend.tools.system_control import PORTAL_SHORTCUTS
        for candidate_key in (core_key, cleaned, lowered):
            if candidate_key and candidate_key in PORTAL_SHORTCUTS:
                return {
                    "url": PORTAL_SHORTCUTS[candidate_key],
                    "title": candidate_key.title(),
                    "source": "portal",
                    "profile_name": profile_name
                }
    except Exception:
        pass

    # 3. Gather candidates from Bookmarks and History
    bookmarks = get_chrome_bookmarks(profile_name=profile_name)
    search_q = core_key if core_key else cleaned
    history = search_chrome_history(query=search_q, profile_name=profile_name, limit=30)

    candidates = bookmarks + history
    scored_candidates = []
    for c in candidates:
        s = score_item(c, search_q)
        if s > 30:  # Minimum relevance threshold
            scored_candidates.append((s, c))

    scored_candidates.sort(key=lambda x: x[0], reverse=True)

    if scored_candidates:
        best_score, best = scored_candidates[0]
        return {
            "url": best["url"],
            "title": best["title"],
            "source": best["source"],
            "found": True,
            "score": best_score,
            "profile_name": best["profile_name"],
            "profile_dir": best["profile_dir"],
            "account_number": best["account_number"],
            "visit_count": best.get("visit_count")
        }

    # 4. Portal Shortcuts fallback
    from backend.tools.system_control import PORTAL_SHORTCUTS
    for candidate_key in (core_key, cleaned, lowered):
        if candidate_key and candidate_key in PORTAL_SHORTCUTS:
            return {
                "url": PORTAL_SHORTCUTS[candidate_key],
                "title": candidate_key.capitalize(),
                "source": "portal",
                "found": True,
                "profile_name": profile_name
            }

    # 5. Domain fallback (e.g. 'github.com', 'python.org')
    fallback_target = core_key if core_key else cleaned
    if "." in fallback_target and " " not in fallback_target:
        return {
            "url": f"https://{fallback_target}",
            "title": fallback_target,
            "source": "direct",
            "found": False,
            "profile_name": profile_name
        }

    # 6. Google Search fallback
    return {
        "url": f"https://www.google.com/search?q={urllib.parse.quote_plus(fallback_target)}",
        "title": f"Google Search: {fallback_target}",
        "source": "search",
        "found": False,
        "profile_name": profile_name
    }


def open_smart_website(
    query_or_url: str,
    profile_name: Optional[str] = None,
    inspect: bool = False
) -> Dict[str, Any]:
    """
    Open any website, bookmark, portal, or history item directly in Google Chrome.
    Automatically resolves to the user's specific authenticated account/dashboard link
    and opens in the designated Chrome profile.
    """
    from backend.tools.system_control import open_chrome_profile, _launch_browser

    resolved = resolve_smart_url(query_or_url, profile_name=profile_name)
    target_url = resolved["url"]
    target_title = resolved.get("title") or target_url
    source = resolved.get("source", "web")
    matched_dir = resolved.get("profile_dir")
    matched_prof = resolved.get("profile_name")
    acc_num = resolved.get("account_number")

    # If a specific profile was requested, prefer it; otherwise strictly default to Primary Profile ('Default')
    prof_to_use = profile_name or "Default"

    opened = False
    disp_profile = matched_prof
    if prof_to_use:
        res = open_chrome_profile(prof_to_use, target_url)
        if res.get("success"):
            opened = True
            disp_profile = res.get("profile_name", disp_profile)

    if not opened:
        try:
            _launch_browser(target_url, inspect=inspect)
            opened = True
        except Exception:
            import webbrowser
            webbrowser.open(target_url)
            opened = True

    source_desc = {
        "bookmark": "bookmarked account page",
        "history": "frequently visited page",
        "portal": "direct portal dashboard",
        "direct": "website",
        "search": "search query"
    }.get(source, "page")

    prof_desc = f" under '{disp_profile}'" if disp_profile else ""
    msg = f"Opened your {source_desc} '{target_title}'{prof_desc}: {target_url}"

    return {
        "success": True,
        "url": target_url,
        "title": target_title,
        "source": source,
        "profile": disp_profile,
        "account_number": acc_num,
        "message": msg
    }


def list_chrome_bookmarks(
    query: Optional[str] = None,
    profile_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    List user's saved Chrome Bookmarks with URLs, folders, and profile names.
    Useful when user asks "mere bookmarks dikhao" or "bookmarks mein se X dhoondo".
    """
    bms = get_chrome_bookmarks(query=query, profile_name=profile_name)
    if not bms:
        q_msg = f" matching '{query}'" if query else ""
        return {"success": True, "count": 0, "bookmarks": [], "message": f"No bookmarks found{q_msg}."}

    lines = [f"Found {len(bms)} Chrome Bookmark(s):"]
    for idx, b in enumerate(bms[:25], 1):
        folder_str = f" [{b['folder']}]" if b.get('folder') else ""
        lines.append(f"{idx}. [{b['profile_name']}] {b['title']}{folder_str} -> {b['url']}")

    if len(bms) > 25:
        lines.append(f"... and {len(bms) - 25} more bookmarks.")

    return {
        "success": True,
        "count": len(bms),
        "bookmarks": bms[:25],
        "message": "\n".join(lines)
    }


def search_chrome_history_tool(
    query: str,
    profile_name: Optional[str] = None,
    limit: int = 15
) -> Dict[str, Any]:
    """
    Search user's Chrome browsing history for specific websites, visited topics, or portals.
    Useful when user asks "meri history mein se X check karo" or "history search karo".
    """
    hist = search_chrome_history(query=query, profile_name=profile_name, limit=limit)
    if not hist:
        return {"success": True, "count": 0, "history": [], "message": f"No history found matching '{query}'."}

    lines = [f"Found {len(hist)} History Entry(ies) for '{query}':"]
    for idx, h in enumerate(hist, 1):
        lines.append(f"{idx}. [{h['profile_name']}] ({h['visit_count']} visits) {h['title'][:45]} -> {h['url']}")

    return {
        "success": True,
        "count": len(hist),
        "history": hist,
        "message": "\n".join(lines)
    }
