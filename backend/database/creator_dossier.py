"""
JARVIS Creator Digital Dossier & Online Presence Engine
Stores and synchronizes complete creator profile, social links, public repositories,
skills, career history, and online footprint in a unified, human-readable format.
"""

import os
import json
import re
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Optional
import requests

DOSSIER_FILE = os.path.join(os.path.dirname(__file__), "creator_dossier.json")

DEFAULT_EMAILS: List[Dict[str, Any]] = [
    {
        "id": "email_1",
        "label": "Personal Gmail",
        "email": "",
        "provider": "gmail",
        "is_primary": True,
        "inbox_url": "",
        "notes": "Main personal Google account"
    },
    {
        "id": "email_2",
        "label": "Work & Business",
        "email": "",
        "provider": "gmail",
        "is_primary": False,
        "inbox_url": "",
        "notes": "Work projects, clients and freelance inquiries"
    },
    {
        "id": "email_3",
        "label": "Developer & GitHub",
        "email": "",
        "provider": "gmail",
        "is_primary": False,
        "inbox_url": "",
        "notes": "VCS, APIs, cloud consoles and developer accounts"
    },
    {
        "id": "email_4",
        "label": "Official / Secondary",
        "email": "",
        "provider": "outlook",
        "is_primary": False,
        "inbox_url": "",
        "notes": "Official communications, banking and documentation"
    }
]

DEFAULT_DOSSIER: Dict[str, Any] = {
    "personal": {
        "name": "Muhammad Akmal",
        "preferred_name": "Akmal Sir",
        "title": "Full Stack Developer & AI Engineer",
        "bio": "Creator and Master Architect of JARVIS AI Assistant System.",
        "location": "Pakistan",
        "email": "",
        "phone": "",
        "avatar_url": ""
    },
    "emails": DEFAULT_EMAILS,
    "social_profiles": {
        "github": "https://github.com/AkmalDoghar",
        "github_username": "",
        "linkedin": "",
        "portfolio": "",
        "twitter": "",
        "youtube": "",
        "instagram": ""
    },
    "tech_stack": [
        "Python", "FastAPI", "Next.js", "React", "TypeScript",
        "Tailwind CSS", "AI/LLMs", "Node.js", "PyTorch", "Git"
    ],
    "coding_preferences": "Clean modular architecture, TypeScript strict, functional components, fast responsive UI, secure code",
    "projects": [
        {
            "name": "JARVIS AI Assistant",
            "role": "Lead Architect & Creator",
            "description": "Next-generation personal AI agent for Windows with voice biometrics, system automation, and web intelligence."
        }
    ],
    "career_summary": "Full Stack Developer & AI Engineer with expertise in building real-time autonomous agent systems, full-stack web applications, and intelligent developer tooling.",
    "online_synced_data": {
        "last_synced": None,
        "github_bio": "",
        "public_repos_count": 0,
        "recent_repos": [],
        "followers": 0,
        "online_summary": "Online profile ready for synchronization."
    },
    "ai_interaction_rules": {
        "honorific": "Akmal Sir",
        "tone": "Respectful, sharp, loyal, concise and proactive Roman Urdu",
        "creator_authority": "Supreme authority - all high-risk actions authenticated exclusively for Akmal Sir."
    }
}


def _ensure_dossier_file() -> None:
    """Create default dossier file if it does not exist."""
    if not os.path.exists(DOSSIER_FILE):
        with open(DOSSIER_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_DOSSIER, f, indent=2, ensure_ascii=False)


def get_dossier() -> Dict[str, Any]:
    """Retrieve full creator dossier."""
    _ensure_dossier_file()
    try:
        with open(DOSSIER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all default keys exist
            for key, val in DEFAULT_DOSSIER.items():
                if key not in data:
                    data[key] = val
            # Ensure emails list exists and is initialized
            if "emails" not in data or not isinstance(data.get("emails"), list) or len(data["emails"]) == 0:
                data["emails"] = [dict(e) for e in DEFAULT_EMAILS]
            else:
                # Fill any missing default slots up to 4 accounts
                existing_ids = {e.get("id") for e in data["emails"] if isinstance(e, dict)}
                for default_em in DEFAULT_EMAILS:
                    if default_em["id"] not in existing_ids and len(data["emails"]) < 4:
                        data["emails"].append(dict(default_em))

            for em in data.get("emails", []):
                if isinstance(em, dict) and not em.get("inbox_url") and em.get("email"):
                    em["inbox_url"] = compute_inbox_url(em.get("email", ""), em.get("provider", "gmail"))

            return data
    except Exception as e:
        print(f"[Dossier] Read error: {e}")
        return DEFAULT_DOSSIER.copy()


def compute_inbox_url(email_address: str, provider: str = "gmail", custom_url: Optional[str] = None) -> str:
    """Compute direct web inbox URL for instant launch in browser."""
    if custom_url and custom_url.strip():
        u = custom_url.strip()
        return u if u.startswith(("http://", "https://")) else f"https://{u}"

    clean_email = (email_address or "").strip()
    prov = (provider or "").lower().strip()

    if "gmail" in prov or clean_email.endswith("@gmail.com"):
        if clean_email:
            return f"https://mail.google.com/mail/u/?authuser={urllib.parse.quote(clean_email)}"
        return "https://mail.google.com"
    elif "outlook" in prov or "hotmail" in prov or clean_email.endswith(("@outlook.com", "@hotmail.com", "@live.com")):
        return "https://outlook.live.com/mail/0/inbox"
    elif "yahoo" in prov or clean_email.endswith("@yahoo.com"):
        return "https://mail.yahoo.com"
    elif "proton" in prov or clean_email.endswith("@proton.me"):
        return "https://mail.proton.me"

    return f"https://mail.google.com/mail/u/?authuser={urllib.parse.quote(clean_email)}" if clean_email else "https://mail.google.com"


def compute_compose_url(email_address: str, provider: str = "gmail", to: str = "") -> str:
    """Compute direct webmail compose URL to start a new email draft."""
    clean_email = (email_address or "").strip()
    prov = (provider or "").lower().strip()
    to_param = f"&to={urllib.parse.quote(to)}" if to else ""

    if "gmail" in prov or clean_email.endswith("@gmail.com"):
        if clean_email:
            return f"https://mail.google.com/mail/u/?authuser={urllib.parse.quote(clean_email)}#inbox?compose=new{to_param}"
        return f"https://mail.google.com/mail/#inbox?compose=new{to_param}"
    elif "outlook" in prov or "hotmail" in prov or clean_email.endswith(("@outlook.com", "@hotmail.com")):
        return f"https://outlook.live.com/mail/0/deeplink/compose?to={urllib.parse.quote(to)}" if to else "https://outlook.live.com/mail/0/deeplink/compose"

    return f"mailto:{to}" if to else "https://mail.google.com"


def get_creator_emails() -> List[Dict[str, Any]]:
    """Retrieve all configured creator email accounts."""
    dossier = get_dossier()
    return dossier.get("emails", [])


def save_creator_email(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add or update an email account entry in the Creator Dossier."""
    dossier = get_dossier()
    emails: List[Dict[str, Any]] = dossier.get("emails", [])

    email_id = email_data.get("id") or f"email_{len(emails) + 1}"
    addr = email_data.get("email", "").strip()
    prov = email_data.get("provider", "gmail")
    is_primary = bool(email_data.get("is_primary", False))
    custom_inbox = email_data.get("inbox_url", "").strip()
    inbox_url = custom_inbox or compute_inbox_url(addr, provider=prov)

    # If this is marked primary, unset other primaries
    if is_primary:
        for em in emails:
            em["is_primary"] = False

    entry: Dict[str, Any] = {
        "id": email_id,
        "label": email_data.get("label", "Email Account").strip(),
        "email": addr,
        "provider": prov,
        "is_primary": is_primary,
        "inbox_url": inbox_url,
        "notes": email_data.get("notes", "").strip()
    }

    found = False
    for i, em in enumerate(emails):
        if em.get("id") == email_id:
            emails[i] = entry
            found = True
            break

    if not found:
        emails.append(entry)

    dossier["emails"] = emails
    save_dossier(dossier)
    return entry


def delete_creator_email(email_id: str) -> bool:
    """Delete or detach an email entry from Creator Dossier."""
    dossier = get_dossier()
    emails = dossier.get("emails", [])
    changed = False

    # For standard slots (email_1 to email_4), reset email address to allow fresh attachment
    standard_ids = {"email_1", "email_2", "email_3", "email_4"}
    if email_id in standard_ids:
        for em in emails:
            if em.get("id") == email_id:
                em["email"] = ""
                em["inbox_url"] = ""
                changed = True
                break
    else:
        initial_len = len(emails)
        emails = [em for em in emails if em.get("id") != email_id]
        if len(emails) != initial_len:
            dossier["emails"] = emails
            changed = True

    if changed:
        save_dossier(dossier)
        return True
    return False


def save_creator_repo(repo_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add or update a repository in creator dossier."""
    dossier = get_dossier()
    synced = dossier.get("online_synced_data", {})
    repos: List[Dict[str, Any]] = synced.get("recent_repos", [])

    repo_name = (repo_data.get("name") or "").strip()
    if not repo_name:
        raise ValueError("Repository name cannot be empty.")

    entry = {
        "name": repo_name,
        "description": repo_data.get("description", "Project repository").strip(),
        "language": repo_data.get("language", "Code").strip(),
        "stars": int(repo_data.get("stars", 0)),
        "html_url": repo_data.get("html_url", f"https://github.com/AkmalDoghar/{repo_name}").strip()
    }

    found = False
    for i, r in enumerate(repos):
        if r.get("name", "").lower() == repo_name.lower():
            repos[i] = entry
            found = True
            break

    if not found:
        repos.append(entry)

    synced["recent_repos"] = repos
    synced["public_repos_count"] = len(repos)
    dossier["online_synced_data"] = synced
    save_dossier(dossier)
    return entry


def delete_creator_repo(repo_name: str) -> bool:
    """Delete a repository from creator dossier."""
    dossier = get_dossier()
    synced = dossier.get("online_synced_data", {})
    repos = synced.get("recent_repos", [])
    initial_len = len(repos)
    repos = [r for r in repos if r.get("name", "").lower() != repo_name.lower()]
    if len(repos) != initial_len:
        synced["recent_repos"] = repos
        synced["public_repos_count"] = len(repos)
        dossier["online_synced_data"] = synced
        save_dossier(dossier)
        return True
    return False


def find_creator_email(query: str = "primary") -> Optional[Dict[str, Any]]:
    """
    Find matching email account from creator dossier.
    Matches by:
    - ID: "email_1", "email_2", etc.
    - Number word: "first", "pehle", "second", "doosri", "third", "teesri", "fourth", "chauthi", "1", "2", "3", "4"
    - Label/purpose: "personal", "work", "business", "developer", "github", "official", "secondary"
    - Provider: "gmail", "outlook", "hotmail", "yahoo"
    - Partial email address match: "akmal", "@gmail.com", etc.
    - Fallback: Primary email account
    """
    dossier = get_dossier()
    emails = dossier.get("emails", [])
    if not emails:
        return None

    clean_q = query.lower().strip()

    # Empty or generic inquiry -> primary email
    if not clean_q or clean_q in ("primary", "main", "default", "email", "mail", "meri email", "inbox", "dak"):
        for em in emails:
            if em.get("is_primary") and em.get("email"):
                return em
        for em in emails:
            if em.get("email"):
                return em
        return emails[0] if emails else None

    # Number index matching (1, 2, 3, 4, first, second, etc.)
    index_map = {
        "1": 0, "first": 0, "pehli": 0, "pehle": 0, "one": 0, "pehl": 0,
        "2": 1, "second": 1, "doosri": 1, "dusri": 1, "two": 1, "doosr": 1,
        "3": 2, "third": 2, "teesri": 2, "tisri": 2, "three": 2, "teesr": 2,
        "4": 3, "fourth": 3, "chauthi": 3, "chothi": 3, "four": 3, "chauth": 3,
    }
    for word, idx in index_map.items():
        if word in clean_q and idx < len(emails):
            return emails[idx]

    # Exact ID match
    for em in emails:
        if em.get("id", "").lower() == clean_q:
            return em

    # Label or notes match
    for em in emails:
        lbl = (em.get("label") or "").lower()
        notes = (em.get("notes") or "").lower()
        if clean_q in lbl or any(k in lbl for k in clean_q.split() if len(k) > 2):
            return em
        if clean_q in notes:
            return em

    # Email address match
    for em in emails:
        addr = (em.get("email") or "").lower()
        if clean_q in addr or addr.startswith(clean_q):
            return em

    # Provider match
    for em in emails:
        prov = (em.get("provider") or "").lower()
        if prov in clean_q:
            return em

    # Fallback to primary
    for em in emails:
        if em.get("is_primary") and em.get("email"):
            return em
    for em in emails:
        if em.get("email"):
            return em
    return emails[0] if emails else None


def save_dossier(data: Dict[str, Any]) -> bool:
    """Save updated dossier to disk."""
    try:
        with open(DOSSIER_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[Dossier] Save error: {e}")
        return False


def update_dossier(updates: Dict[str, Any]) -> Dict[str, Any]:
    """Merge updates into dossier."""
    current = get_dossier()
    for key, val in updates.items():
        if isinstance(val, dict) and isinstance(current.get(key), dict):
            current[key].update(val)
        else:
            current[key] = val
    save_dossier(current)
    return current


def sync_creator_online(github_username: Optional[str] = None) -> Dict[str, Any]:
    """
    Automatically scrape and sync public details from GitHub and online footprint.
    Fetches public repositories, bio, follower count, and recent updates.
    """
    dossier = get_dossier()
    user_handle = github_username or dossier.get("social_profiles", {}).get("github_username")

    # If handle not in github_username, extract from github url if available
    if not user_handle:
        gh_url = dossier.get("social_profiles", {}).get("github", "")
        if "github.com/" in gh_url:
            parts = gh_url.rstrip("/").split("github.com/")
            if len(parts) > 1 and parts[1].strip():
                user_handle = parts[1].strip().split("/")[0]

    synced_info: Dict[str, Any] = {
        "success": False,
        "message": "No GitHub handle provided for online sync.",
        "last_synced": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    if user_handle:
        try:
            headers = {"User-Agent": "JARVIS-AI-Agent"}
            user_res = requests.get(f"https://api.github.com/users/{user_handle}", headers=headers, timeout=8)
            if user_res.status_code == 200:
                user_data = user_res.json()
                bio = user_data.get("bio") or ""
                public_repos = user_data.get("public_repos", 0)
                followers = user_data.get("followers", 0)
                blog = user_data.get("blog") or ""
                company = user_data.get("company") or ""

                # Fetch top recent public repos
                recent_repos_list = []
                repos_res = requests.get(
                    f"https://api.github.com/users/{user_handle}/repos?sort=updated&per_page=6",
                    headers=headers,
                    timeout=8
                )
                if repos_res.status_code == 200:
                    for repo in repos_res.json():
                        recent_repos_list.append({
                            "name": repo.get("name"),
                            "description": repo.get("description") or "No description",
                            "language": repo.get("language") or "Code",
                            "stars": repo.get("stargazers_count", 0),
                            "html_url": repo.get("html_url")
                        })

                # Update dossier with live findings
                dossier["social_profiles"]["github_username"] = user_handle
                if not dossier["social_profiles"].get("github") or dossier["social_profiles"].get("github") == "https://github.com":
                    dossier["social_profiles"]["github"] = f"https://github.com/{user_handle}"

                if blog and not dossier["social_profiles"].get("portfolio"):
                    dossier["social_profiles"]["portfolio"] = blog if blog.startswith("http") else f"https://{blog}"

                avatar_url = user_data.get("avatar_url") or f"https://github.com/{user_handle}.png"
                if avatar_url:
                    dossier["personal"]["avatar_url"] = avatar_url

                if bio and not dossier["personal"].get("bio"):
                    dossier["personal"]["bio"] = bio

                dossier["online_synced_data"] = {
                    "last_synced": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "github_handle": user_handle,
                    "github_bio": bio,
                    "public_repos_count": public_repos,
                    "followers": followers,
                    "recent_repos": recent_repos_list,
                    "online_summary": f"GitHub @{user_handle} synced: {public_repos} public repos, {followers} followers."
                }
                save_dossier(dossier)

                synced_info = {
                    "success": True,
                    "handle": user_handle,
                    "public_repos": public_repos,
                    "followers": followers,
                    "recent_repos": recent_repos_list,
                    "message": f"Successfully synced online footprint for @{user_handle}. {public_repos} repositories retrieved."
                }
            elif user_res.status_code == 404:
                synced_info = {"success": False, "message": f"GitHub user '{user_handle}' not found."}
            else:
                synced_info = {"success": False, "message": f"GitHub API status code: {user_res.status_code}"}
        except Exception as e:
            synced_info = {"success": False, "message": f"Online sync error: {str(e)}"}

    return synced_info


def get_dossier_prompt_context() -> str:
    """
    Generate deep, rich context about Akmal Sir to inject directly into JARVIS AI Brain.
    Ensures JARVIS immediately knows his full identity, social media, projects, and tech stack.
    """
    try:
        d = get_dossier()
        p = d.get("personal", {})
        soc = d.get("social_profiles", {})
        tech = d.get("tech_stack", [])
        synced = d.get("online_synced_data", {})
        projects = d.get("projects", [])
        rules = d.get("ai_interaction_rules", {})

        name = p.get("name", "Muhammad Akmal")
        title = p.get("title", "Full Stack Developer & AI Engineer")
        preferred = p.get("preferred_name", "Akmal Sir")
        bio = p.get("bio", "")

        context_lines = [
            f"CREATOR DOSSIER: You are the dedicated personal AI assistant of {name} ({preferred}), who is a {title}.",
            f"Creator Bio: {bio}" if bio else "",
            f"Social Media & Links: GitHub: {soc.get('github') or 'Not set'}, LinkedIn: {soc.get('linkedin') or 'Not set'}, Portfolio: {soc.get('portfolio') or 'Not set'}, Instagram: {soc.get('instagram') or 'Not set'}.",
            f"Tech Stack: {', '.join(tech) if isinstance(tech, list) else tech}.",
            f"Coding Preferences: {d.get('coding_preferences', '')}.",
        ]

        if synced.get("recent_repos"):
            repo_names = [f"{r.get('name')} ({r.get('language')})" for r in synced.get("recent_repos")[:4]]
            context_lines.append(f"Public Repositories ({synced.get('public_repos_count', 0)} total): {', '.join(repo_names)}.")

        if projects:
            proj_str = "; ".join([f"{prj.get('name')} ({prj.get('role')})" for prj in projects[:3]])
            context_lines.append(f"Current Projects: {proj_str}.")

        # Add registered email accounts context
        emails = d.get("emails", [])
        active_emails = [e for e in emails if isinstance(e, dict) and e.get("email")]
        if active_emails:
            em_descriptions = []
            for em in active_emails:
                primary_tag = " [PRIMARY]" if em.get("is_primary") else ""
                em_descriptions.append(f"{em.get('label')}{primary_tag}: {em.get('email')} ({em.get('provider', 'gmail')})")
            context_lines.append(f"Creator Registered Emails ({len(active_emails)} total): " + "; ".join(em_descriptions) + ".")
            context_lines.append(
                "EMAIL COMMAND PROTOCOL: When creator asks to open, check, view, or compose an email "
                "(e.g., 'email open karo', 'open my work email', 'check my second email', 'open developer email', 'email check karo'), "
                "ALWAYS invoke the tool 'open_creator_email' with the appropriate identifier ('primary', 'work', 'developer', 'official', or account number/email)."
            )

        context_lines.append(f"Creator Protocol: Address creator as '{preferred}'. {rules.get('tone', 'Respectful, sharp Roman Urdu')}.")

        return " ".join([line for line in context_lines if line])
    except Exception as e:
        print(f"[Dossier] Prompt context error: {e}")
        return "CREATOR DOSSIER: You are the dedicated AI assistant of your creator Akmal Sir."
