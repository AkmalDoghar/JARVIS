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

DEFAULT_DOSSIER: Dict[str, Any] = {
    "personal": {
        "name": "Muhammad Akmal",
        "preferred_name": "Akmal bhai",
        "title": "Full Stack Developer & AI Engineer",
        "bio": "Creator and Master Architect of JARVIS AI Assistant System.",
        "location": "Pakistan",
        "email": "",
        "phone": "",
        "avatar_url": ""
    },
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
        "honorific": "Akmal bhai",
        "tone": "Respectful, sharp, loyal, concise and proactive Roman Urdu",
        "creator_authority": "Supreme authority - all high-risk actions authenticated exclusively for Akmal bhai."
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
            return data
    except Exception as e:
        print(f"[Dossier] Read error: {e}")
        return DEFAULT_DOSSIER.copy()


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
    Generate deep, rich context about Akmal bhai to inject directly into JARVIS AI Brain.
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
        preferred = p.get("preferred_name", "Akmal bhai")
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

        context_lines.append(f"Creator Protocol: Address creator as '{preferred}'. {rules.get('tone', 'Respectful, sharp Roman Urdu')}.")

        return " ".join([line for line in context_lines if line])
    except Exception as e:
        print(f"[Dossier] Prompt context error: {e}")
        return "CREATOR DOSSIER: You are the dedicated AI assistant of your creator Akmal bhai."
