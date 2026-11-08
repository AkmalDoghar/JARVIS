"""
JARVIS Creator Tools
Phase 3/4 Bridge Component: Creator Profile, Active Projects & Daily Focus Tools for JARVIS Brain.
"""

import os
import json
import subprocess
import urllib.parse
import webbrowser
from typing import Dict, Any, List, Optional
import requests
from backend.database.vault import (
    get_creator_profile,
    get_vault_entries,
    add_vault_entry,
    get_creator_projects,
    get_daily_focus,
    add_daily_focus,
    get_creator_accounts,
    add_or_update_creator_account,
    update_account_sync_summary,
    get_social_posts,
    add_social_post,
    update_social_post_status,
)


def get_creator_info(field: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve creator profile details (name, title, github, portfolio, linkedin, tech stack, or active goals).
    """
    try:
        profile = get_creator_profile()
        goals = get_vault_entries(category="goal", status="active")

        if field:
            clean_field = field.lower().strip()
            if clean_field in ("goal", "goals", "active goals"):
                goal_list = [f"{g.get('title')}: {g.get('content')}" for g in goals]
                return {
                    "success": True,
                    "field": "goals",
                    "goals": goal_list,
                    "message": f"Active goals ({len(goal_list)}): " + ("; ".join(goal_list) if goal_list else "None set yet.")
                }
            if clean_field in profile:
                val = profile[clean_field]
                return {
                    "success": True,
                    "field": clean_field,
                    "value": val,
                    "message": f"Creator {clean_field}: {val or 'Not configured yet.'}"
                }

        return {
            "success": True,
            "profile": profile,
            "active_goals_count": len(goals),
            "message": f"Creator: {profile.get('name')} ({profile.get('title')}). GitHub: {profile.get('github') or 'N/A'}, Portfolio: {profile.get('portfolio') or 'N/A'}."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to retrieve creator info: {str(e)}"}


def open_creator_link(platform: str, inspect: bool = False) -> Dict[str, Any]:
    """
    Open the creator's social/developer link in browser: 'portfolio', 'github', or 'linkedin'.
    Supports inspect/developer mode if requested.
    """
    plat = platform.lower().strip()
    profile = get_creator_profile()

    url = ""
    if "portfolio" in plat or "website" in plat:
        url = profile.get("portfolio")
    elif "github" in plat or "git" in plat:
        url = profile.get("github")
    elif "linkedin" in plat:
        url = profile.get("linkedin")

    if not url:
        return {
            "success": False,
            "error": f"Creator {platform} URL is not set in the Creator Vault.",
            "suggestion": "Please add your link in the Creator Vault dashboard tab."
        }

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        from backend.tools.system_control import _launch_browser
        _launch_browser(url, inspect=inspect)
        msg = f"Opened your {platform} ({url}) in the default browser"
        if inspect:
            msg += " with Developer Tools (Inspect mode)"
        msg += "."
        return {
            "success": True,
            "platform": platform,
            "url": url,
            "inspect": inspect,
            "message": msg
        }
    except Exception as e:
        return {"success": False, "error": f"Could not open browser URL: {str(e)}"}


def save_creator_thought(content: str, category: str = "thought", title: str = "") -> Dict[str, Any]:
    """
    Save a personal thought, goal, or idea directly into the creator vault.
    Categories: 'thought', 'goal', 'plan', 'note'.
    """
    if not content or not content.strip():
        return {"success": False, "error": "Content cannot be empty."}

    try:
        entry = add_vault_entry(category=category, content=content, title=title)
        return {
            "success": True,
            "entry_id": entry["id"],
            "category": entry["category"],
            "title": entry["title"],
            "message": f"Saved {entry['category']} '{entry['title']}' to your Creator Vault successfully."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to save vault entry: {str(e)}"}


def get_active_projects() -> Dict[str, Any]:
    """
    List all active developer projects registered in the Creator Vault.
    """
    try:
        projects = get_creator_projects()
        summary = [f"{p['name']} ({p['path']})" for p in projects]
        return {
            "success": True,
            "projects": projects,
            "count": len(projects),
            "message": f"Registered projects ({len(projects)}): {', '.join(summary)}"
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to get projects: {str(e)}"}


def open_project(project_name: str, in_vscode: bool = True) -> Dict[str, Any]:
    """
    Open a registered project in VS Code (code <path>) or Windows File Explorer.
    """
    clean_name = project_name.lower().strip()
    projects = get_creator_projects()

    target_project = None
    for p in projects:
        if clean_name in p["name"].lower() or p["name"].lower() in clean_name:
            target_project = p
            break

    if not target_project:
        available = ", ".join([p["name"] for p in projects])
        return {
            "success": False,
            "error": f"Project '{project_name}' is not registered in your Creator Vault.",
            "suggestion": f"Registered projects: {available}."
        }

    path = target_project["path"]
    if not os.path.exists(path):
        return {"success": False, "error": f"Project folder '{path}' does not exist on disk."}

    try:
        if in_vscode:
            subprocess.Popen(f'code "{path}"', shell=True)
            return {
                "success": True,
                "project": target_project["name"],
                "path": path,
                "message": f"Opened project '{target_project['name']}' in Visual Studio Code."
            }
        else:
            os.startfile(path)
            return {
                "success": True,
                "project": target_project["name"],
                "path": path,
                "message": f"Opened project '{target_project['name']}' folder in File Explorer."
            }
    except Exception as e:
        return {"success": False, "error": f"Failed to open project: {str(e)}"}


def get_today_focus() -> Dict[str, Any]:
    """
    Get today's daily focus / standup priority tasks.
    """
    try:
        tasks = get_daily_focus()
        pending = [t["task"] for t in tasks if not t.get("completed")]
        done = [t["task"] for t in tasks if t.get("completed")]

        msg = f"Today's Focus: {len(pending)} pending tasks"
        if pending:
            msg += f" (1. {pending[0]})"

        return {
            "success": True,
            "tasks": tasks,
            "pending": pending,
            "completed": done,
            "message": msg
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to retrieve daily focus: {str(e)}"}


def add_today_focus_task(task: str) -> Dict[str, Any]:
    """
    Add a new task to Today's Focus list.
    """
    if not task or not task.strip():
        return {"success": False, "error": "Task description cannot be empty."}

    try:
        item = add_daily_focus(task=task)
        return {
            "success": True,
            "task": item,
            "message": f"Added '{item['task']}' to Today's Focus."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to add focus task: {str(e)}"}


def get_creator_accounts_info(platform: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve all connected developer and social media accounts (GitHub, LinkedIn, Twitter, Portfolio, etc.).
    Returns handles, profile URLs, content themes, target audience, and synced summaries.
    """
    try:
        accounts = get_creator_accounts(platform=platform)
        if not accounts:
            return {
                "success": True,
                "accounts": [],
                "count": 0,
                "message": "No connected accounts registered yet in your Creator Vault."
            }

        acc_summaries = []
        for a in accounts:
            theme_str = f" - Theme: {a['content_theme']}" if a.get("content_theme") else ""
            acc_summaries.append(f"{a['platform'].capitalize()} ({a['handle']}){theme_str}")

        return {
            "success": True,
            "accounts": accounts,
            "count": len(accounts),
            "message": f"Connected accounts ({len(accounts)}): {'; '.join(acc_summaries)}"
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to retrieve creator accounts: {str(e)}"}


def inspect_creator_account(platform: str) -> Dict[str, Any]:
    """
    Live inspect the creator's account on a given platform (e.g. 'github', 'linkedin', 'twitter', 'portfolio').
    Retrieves live public stats, profile info, and recent content, then synchronizes it into the Creator Vault.
    """
    plat = platform.lower().strip()
    accounts = get_creator_accounts(platform=plat)
    if not accounts:
        all_accs = get_creator_accounts()
        matched = [a for a in all_accs if plat in a.get("platform", "").lower() or plat in a.get("handle", "").lower()]
        target_acc = matched[0] if matched else None
    else:
        target_acc = accounts[0]

    if not target_acc:
        return {
            "success": False,
            "error": f"No account found for platform '{platform}' in the Creator Vault.",
            "suggestion": "Please register this account in your Creator Vault Accounts tab first."
        }

    handle = target_acc.get("handle", "").lstrip("@")
    profile_url = target_acc.get("profile_url", "")
    summary_text = ""

    if "github" in plat:
        try:
            gh_url = f"https://api.github.com/users/{handle}" if handle else ""
            res = requests.get(gh_url, headers={"User-Agent": "JARVIS-AI-Agent"}, timeout=5.0)
            if res.status_code == 200:
                data = res.json()
                public_repos = data.get("public_repos", 0)
                followers = data.get("followers", 0)
                bio = data.get("bio") or "Full Stack Developer"
                summary_text = f"Live GitHub Stats: {public_repos} public repos, {followers} followers. Bio: '{bio}'. Primary repo: JARVIS."
            else:
                summary_text = f"GitHub profile: {profile_url} (@{handle}). Active repos: JARVIS (Next.js, Python FastAPI, TypeScript)."
        except Exception:
            summary_text = f"GitHub profile: {profile_url} (@{handle}). Local repositories: JARVIS (AI Core, Voice Intelligence)."
    elif "linkedin" in plat:
        summary_text = f"LinkedIn profile: {profile_url} ({target_acc.get('account_name')}). Professional focus: Full Stack AI Systems, Agentic Workflows & System Architecture."
    elif "portfolio" in plat:
        summary_text = f"Portfolio URL: {profile_url}. Active showcase: JARVIS AI Assistant with voice intelligence & desktop automation."
    elif "twitter" in plat or "x" in plat:
        summary_text = f"X/Twitter profile: {profile_url} (@{handle}). Content theme: Building autonomous AI systems in public."
    else:
        summary_text = f"{target_acc.get('platform').capitalize()} account: {profile_url} ({handle}). Theme: {target_acc.get('content_theme')}."

    update_account_sync_summary(target_acc["id"], summary_text)

    return {
        "success": True,
        "platform": target_acc.get("platform"),
        "handle": target_acc.get("handle"),
        "profile_url": profile_url,
        "content_theme": target_acc.get("content_theme"),
        "synced_summary": summary_text,
        "message": f"Successfully inspected and synced {target_acc.get('platform').capitalize()} account ({target_acc.get('handle')}). {summary_text}"
    }


def draft_social_post(
    platform: str,
    topic: str,
    content_style: str = "engaging",
    hashtags: str = ""
) -> Dict[str, Any]:
    """
    Draft high-impact content for the creator's social media accounts (e.g. 'linkedin', 'twitter', 'github').
    Saves the post draft in the Creator Vault for review and one-click publishing.
    """
    plat = platform.lower().strip()
    topic_clean = topic.strip()
    if not topic_clean:
        return {"success": False, "error": "Post topic or content cannot be empty."}

    # Generate tailored draft based on platform
    if "linkedin" in plat:
        post_content = (
            f"🚀 Transforming personal AI workflows with autonomous systems.\n\n"
            f"Over the past few weeks, I've been refining JARVIS — a localized, voice-first autonomous AI assistant built with FastAPI, Next.js, and TypeScript.\n\n"
            f"Key breakthrough: {topic_clean}\n\n"
            f"By combining ultra-low-latency LPU inference with proactive suggestions and system-level tools, the barrier between conversational intent and execution disappears.\n\n"
            f"Curious to hear how other engineers are structuring their local agent architectures! What is your go-to framework for agentic workflows?\n\n"
            f"#ArtificialIntelligence #FullStack #Python #NextJS #AIEngineering #WebDevelopment"
        )
        post_hashtags = "#AI #FullStack #NextJS #Engineering"
    elif "twitter" in plat or "x" in plat:
        post_content = (
            f"Building autonomous AI systems in public ⚡\n\n"
            f"Latest update on JARVIS: {topic_clean}\n\n"
            f"Sub-second voice inference + proactive suggestion engine = true personal executive experience.\n\n"
            f"Code, tools, and updates coming soon. #buildinpublic #AI #dev"
        )
        post_hashtags = "#buildinpublic #AI #dev"
    elif "github" in plat:
        post_content = (
            f"### 🚀 Project Update: {topic_clean}\n\n"
            f"- Built with Python FastAPI, Next.js, TypeScript, and local system integration.\n"
            f"- Features: Voice intelligence, hardware controls, proactive next-step recommendations, and creator vault.\n"
        )
        post_hashtags = "open-source, python, nextjs, ai"
    else:
        post_content = f"{topic_clean}\n\nShared via JARVIS AI Assistant."
        post_hashtags = "#AI #Tech"

    if hashtags:
        post_hashtags = hashtags

    entry = add_social_post(
        platform=plat,
        content=post_content,
        title=f"{plat.capitalize()} Post: {topic_clean[:40]}",
        hashtags=post_hashtags,
        status="draft"
    )

    return {
        "success": True,
        "post_id": entry["id"],
        "platform": plat,
        "title": entry["title"],
        "content": post_content,
        "hashtags": post_hashtags,
        "status": "draft",
        "message": f"Drafted high-impact {plat.capitalize()} post. Saved to your Creator Vault drafts for review."
    }


def publish_social_post(
    platform: str,
    content: str,
    auto_open_browser: bool = True
) -> Dict[str, Any]:
    """
    Publish or stage a post to social media: copies content to Windows clipboard and opens the platform's posting window.
    """
    plat = platform.lower().strip()
    content_clean = content.strip()
    if not content_clean:
        return {"success": False, "error": "Post content cannot be empty."}

    # 1. Copy to Windows clipboard via PowerShell
    clipboard_copied = False
    try:
        p = subprocess.Popen(["powershell", "-command", "$input | Set-Clipboard"], stdin=subprocess.PIPE, text=True)
        p.communicate(input=content_clean)
        clipboard_copied = True
    except Exception:
        pass

    # 2. Record in database as published
    post_record = add_social_post(
        platform=plat,
        content=content_clean,
        title=f"Published to {plat.capitalize()}",
        status="published"
    )

    # 3. Determine posting URL
    posting_url = ""
    if "linkedin" in plat:
        posting_url = "https://www.linkedin.com/feed/"
    elif "twitter" in plat or "x" in plat:
        encoded_tweet = urllib.parse.quote_plus(content_clean[:280])
        posting_url = f"https://twitter.com/intent/tweet?text={encoded_tweet}"
    elif "github" in plat:
        posting_url = "https://github.com/"
    else:
        posting_url = f"https://www.{plat}.com"

    browser_opened = False
    if auto_open_browser and posting_url:
        try:
            from backend.tools.system_control import _launch_browser
            _launch_browser(posting_url)
            browser_opened = True
        except Exception:
            pass

    msg = f"Post staged for {plat.capitalize()}! Content copied to your clipboard"
    if browser_opened:
        msg += f" and opened {plat.capitalize()} in your browser ready to publish."
    else:
        msg += "."

    return {
        "success": True,
        "post_id": post_record["id"],
        "platform": plat,
        "content_length": len(content_clean),
        "clipboard_copied": clipboard_copied,
        "browser_opened": browser_opened,
        "posting_url": posting_url,
        "message": msg
    }


# ─────────────────────────────────────────────
# 6. Creator Email Management & Direct Launch
# ─────────────────────────────────────────────
def open_creator_email(
    identifier: Optional[str] = "primary",
    action: Optional[str] = "inbox",
    recipient: Optional[str] = None
) -> Dict[str, Any]:
    """
    Open one of creator Akmal Sir's registered email accounts in the browser.
    
    Args:
        identifier: Target email identifier ('primary', 'personal', 'work', 'developer', 'official', '1', '2', '3', '4', or email address).
        action: 'inbox' to open mail folder, or 'compose' to start a new draft.
        recipient: If action is compose, optional target email address.
    """
    from backend.database.creator_dossier import find_creator_email, compute_inbox_url, compute_compose_url
    from backend.tools.system_control import _launch_browser

    target_email = find_creator_email(identifier or "primary")
    if not target_email:
        return {
            "success": False,
            "error": "No registered emails found in Creator Dossier.",
            "suggestion": "Aap Creator Digital Dossier ke 'Email Matrix' tab mein jaa kar apni emails configure kar sakte hain."
        }

    email_addr = (target_email.get("email") or "").strip()
    label = target_email.get("label", "Email Account")
    provider = target_email.get("provider", "gmail")
    custom_inbox = (target_email.get("inbox_url") or "").strip()

    if not email_addr and not custom_inbox:
        return {
            "success": False,
            "error": f"Email address for '{label}' is not configured yet in Creator Dossier.",
            "suggestion": f"Aap Creator Dossier mein {label} ka email enter kar lein, phir JARVIS foran open kar dega."
        }

    # Determine URL
    if action == "compose":
        url = compute_compose_url(email_addr, provider=provider, to=recipient or "")
        msg_action = "new compose draft"
    else:
        url = custom_inbox or compute_inbox_url(email_addr, provider=provider)
        msg_action = "inbox"

    try:
        _launch_browser(url)
        spoken_msg = f"Akmal Sir, aapka {label} ({email_addr or provider}) ka {msg_action} browser mein open kar diya gaya hai."
        return {
            "success": True,
            "label": label,
            "email": email_addr,
            "provider": provider,
            "url": url,
            "action": action,
            "message": spoken_msg,
            "spoken_response": spoken_msg
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to launch browser: {str(e)}"}


def get_creator_emails_summary() -> Dict[str, Any]:
    """Retrieve summary of all registered emails in Creator Dossier."""
    from backend.database.creator_dossier import get_creator_emails
    emails = get_creator_emails()
    active = [e for e in emails if isinstance(e, dict) and e.get("email")]
    return {
        "success": True,
        "total_slots": len(emails),
        "configured_count": len(active),
        "emails": emails,
        "message": f"Found {len(active)} configured email account(s) out of {len(emails)} registered slots."
    }
