"""
JARVIS Creator Vault & Identity System
Persistent SQLite storage for creator profile, social/dev links, active projects,
today's daily focus standup, coding preferences, private thoughts, and vision goals.
Protected by JARVIS Security PIN.
"""

import os
import json
import sqlite3
from datetime import datetime, date
from typing import Dict, Any, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "jarvis_vault.db")


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_vault_db() -> None:
    """Initialize SQLite tables for Creator Profile, Projects, Daily Focus, and Vault Entries."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Creator Profile table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS creator_profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT NOT NULL DEFAULT 'M. Akmal',
                title TEXT DEFAULT 'Full Stack Developer & AI Engineer',
                bio TEXT DEFAULT 'Creator and Master Architect of JARVIS AI System.',
                linkedin TEXT DEFAULT '',
                github TEXT DEFAULT '',
                portfolio TEXT DEFAULT '',
                email TEXT DEFAULT '',
                tech_stack TEXT DEFAULT 'Python, Next.js, React, TypeScript, FastAPI, AI/LLMs',
                coding_preferences TEXT DEFAULT 'TypeScript strict, Tailwind CSS, Clean Modular Architecture, Functional components',
                ai_tone TEXT DEFAULT 'Sharp, respectful, friendly Roman Urdu (Akmal Sir), concise and direct',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migration: ensure coding_preferences and ai_tone columns exist if created previously
        cursor.execute("PRAGMA table_info(creator_profile)")
        columns = [col["name"] for col in cursor.fetchall()]
        if "coding_preferences" not in columns:
            cursor.execute("ALTER TABLE creator_profile ADD COLUMN coding_preferences TEXT DEFAULT 'TypeScript strict, Tailwind CSS, Clean Modular Architecture'")
        if "ai_tone" not in columns:
            cursor.execute("ALTER TABLE creator_profile ADD COLUMN ai_tone TEXT DEFAULT 'Sharp, respectful, friendly Roman Urdu (Akmal Sir), concise'")

        # Ensure default profile row exists
        cursor.execute("SELECT id FROM creator_profile WHERE id = 1")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO creator_profile (id, name, title, bio, tech_stack, coding_preferences, ai_tone)
                VALUES (1, 'M. Akmal', 'Full Stack Developer & AI Engineer', 
                        'Creator and Lead Developer of JARVIS AI System.', 
                        'Python, Next.js, React, TypeScript, FastAPI, AI/LLMs',
                        'TypeScript strict, Tailwind CSS, Clean Modular Architecture',
                        'Sharp, respectful, friendly Roman Urdu (Akmal Sir), concise')
            """)

        # 2. Creator Active Projects Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS creator_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT NOT NULL,
                repo_url TEXT DEFAULT '',
                tech_stack TEXT DEFAULT '',
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'paused')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Seed JARVIS project if empty
        cursor.execute("SELECT id FROM creator_projects WHERE name = 'JARVIS'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO creator_projects (name, path, repo_url, tech_stack, status)
                VALUES ('JARVIS', 'd:/projects/JARVIS', 'https://github.com/akmal/JARVIS', 'Next.js, Python, FastAPI, TypeScript', 'active')
            """)

        # 3. Daily Focus / Standup Tasks Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS creator_daily_focus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 4. Vault Entries Table (Goals, Thoughts, Plans, Notes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vault_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL CHECK (category IN ('goal', 'thought', 'plan', 'note')),
                title TEXT DEFAULT '',
                content TEXT NOT NULL,
                priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'archived')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 5. Connected Accounts & Social Media Presence Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS creator_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                account_name TEXT NOT NULL,
                handle TEXT NOT NULL,
                profile_url TEXT NOT NULL,
                content_theme TEXT DEFAULT '',
                audience TEXT DEFAULT '',
                api_key_or_token TEXT DEFAULT '',
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused')),
                last_synced_summary TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 6. Social Media & Developer Posts Queue Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS creator_social_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                title TEXT DEFAULT '',
                content TEXT NOT NULL,
                hashtags TEXT DEFAULT '',
                media_urls TEXT DEFAULT '',
                status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'published', 'archived')),
                published_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Seed default accounts if table is empty
        cursor.execute("SELECT COUNT(*) as count FROM creator_accounts")
        row = cursor.fetchone()
        if not row or row["count"] == 0:
            cursor.execute("""
                INSERT INTO creator_accounts (platform, account_name, handle, profile_url, content_theme, audience, last_synced_summary)
                VALUES 
                ('github', 'M. Akmal', '@akmaldev', 'https://github.com/akmal', 'Full Stack & AI Development, JARVIS AI Assistant', 'Global Developers & AI Engineers', 'Main codebase: JARVIS. Core technologies: Python, FastAPI, Next.js, TypeScript.'),
                ('linkedin', 'M. Akmal', 'M. Akmal', 'https://linkedin.com/in/akmal', 'AI Engineering, Full Stack Systems, Tech Innovations', 'Founders, Tech Recruiters & Software Engineers', 'Profile: Full Stack Developer & AI Engineer. Creator of JARVIS.'),
                ('portfolio', 'Personal Portfolio', 'Akmal Portfolio', 'https://akmalportfolio.vercel.app', 'Live Demonstration of Production Apps & AI Agents', 'Tech Clients & Collaborators', 'Portfolio showcases AI Assistant, responsive dashboards, and backend services.'),
                ('twitter', 'M. Akmal', '@akmal_dev', 'https://x.com/akmal_dev', 'AI agent updates, building in public, modern tech trends', 'Indie Hackers & Tech Enthusiasts', 'Building autonomous AI tools and sharing daily progress.')
            """)

        conn.commit()


# Initialize on import
init_vault_db()


# ─────────────────────────────────────────────
# Profile Operations
# ─────────────────────────────────────────────
def get_creator_profile() -> Dict[str, Any]:
    """Retrieve creator profile information."""
    init_vault_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM creator_profile WHERE id = 1")
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {
            "name": "M. Akmal",
            "title": "Full Stack Developer & AI Engineer",
            "bio": "Creator of JARVIS",
            "linkedin": "",
            "github": "",
            "portfolio": "",
            "email": "",
            "tech_stack": "Python, Next.js, React, TypeScript, FastAPI",
            "coding_preferences": "TypeScript, Tailwind CSS, Clean Architecture",
            "ai_tone": "Sharp, friendly Roman Urdu",
        }


def update_creator_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Update creator profile details."""
    init_vault_db()
    fields = [
        "name", "title", "bio", "linkedin", "github", "portfolio", 
        "email", "tech_stack", "coding_preferences", "ai_tone"
    ]
    updates = []
    params = []

    for f in fields:
        if f in data:
            updates.append(f"{f} = ?")
            params.append(str(data[f]).strip())

    if not updates:
        return get_creator_profile()

    updates.append("updated_at = CURRENT_TIMESTAMP")
    sql = f"UPDATE creator_profile SET {', '.join(updates)} WHERE id = 1"

    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()

    return get_creator_profile()


# ─────────────────────────────────────────────
# Projects Directory Operations
# ─────────────────────────────────────────────
def get_creator_projects() -> List[Dict[str, Any]]:
    """Retrieve all registered developer projects."""
    init_vault_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM creator_projects ORDER BY created_at ASC")
        return [dict(r) for r in cursor.fetchall()]


def add_creator_project(
    name: str,
    path: str,
    repo_url: str = "",
    tech_stack: str = "",
    status: str = "active"
) -> Dict[str, Any]:
    """Register a new project in the Creator Vault."""
    init_vault_db()
    norm_path = os.path.abspath(path.strip()) if os.path.isabs(path.strip()) else path.strip()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO creator_projects (name, path, repo_url, tech_stack, status)
            VALUES (?, ?, ?, ?, ?)
        """, (name.strip(), norm_path, repo_url.strip(), tech_stack.strip(), status.strip()))
        project_id = cursor.lastrowid
        conn.commit()

        cursor.execute("SELECT * FROM creator_projects WHERE id = ?", (project_id,))
        return dict(cursor.fetchone())


def delete_creator_project(project_id: int) -> bool:
    """Delete a project from the Creator Vault."""
    init_vault_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM creator_projects WHERE id = ?", (project_id,))
        conn.commit()
        return cursor.rowcount > 0


# ─────────────────────────────────────────────
# Daily Focus / Standup Operations
# ─────────────────────────────────────────────
def get_daily_focus(date_str: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve daily focus tasks for a specific date (defaults to today)."""
    init_vault_db()
    target_date = date_str or str(date.today())
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM creator_daily_focus WHERE date = ? ORDER BY id ASC", (target_date,))
        rows = cursor.fetchall()
        # If no tasks for today, also return pending uncompleted tasks from recent days
        if not rows and not date_str:
            cursor.execute("SELECT * FROM creator_daily_focus WHERE completed = 0 ORDER BY id DESC LIMIT 5")
            rows = cursor.fetchall()
        return [dict(r) for r in rows]


def add_daily_focus(task: str, date_str: Optional[str] = None) -> Dict[str, Any]:
    """Add a new task to Today's Focus."""
    init_vault_db()
    target_date = date_str or str(date.today())
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO creator_daily_focus (task, completed, date)
            VALUES (?, 0, ?)
        """, (task.strip(), target_date))
        task_id = cursor.lastrowid
        conn.commit()

        cursor.execute("SELECT * FROM creator_daily_focus WHERE id = ?", (task_id,))
        return dict(cursor.fetchone())


def toggle_daily_focus(task_id: int) -> Optional[Dict[str, Any]]:
    """Toggle completed status of a daily focus task."""
    init_vault_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT completed FROM creator_daily_focus WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if not row:
            return None
        new_val = 0 if row["completed"] else 1
        cursor.execute("UPDATE creator_daily_focus SET completed = ? WHERE id = ?", (new_val, task_id))
        conn.commit()

        cursor.execute("SELECT * FROM creator_daily_focus WHERE id = ?", (task_id,))
        return dict(cursor.fetchone())


def delete_daily_focus(task_id: int) -> bool:
    """Delete a task from Daily Focus."""
    init_vault_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM creator_daily_focus WHERE id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0


# ─────────────────────────────────────────────
# Vault Entries Operations (Goals, Thoughts)
# ─────────────────────────────────────────────
def get_vault_entries(category: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve vault entries filtered by category or status."""
    init_vault_db()
    sql = "SELECT * FROM vault_entries WHERE 1=1"
    params = []

    if category:
        sql += " AND category = ?"
        params.append(category.lower().strip())
    if status:
        sql += " AND status = ?"
        params.append(status.lower().strip())

    sql += " ORDER BY created_at DESC"

    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def add_vault_entry(
    category: str,
    content: str,
    title: str = "",
    priority: str = "medium"
) -> Dict[str, Any]:
    """Create a new vault entry (thought, goal, plan, note)."""
    init_vault_db()
    cat = category.lower().strip()
    if cat not in ("goal", "thought", "plan", "note"):
        cat = "thought"

    prio = priority.lower().strip()
    if prio not in ("low", "medium", "high"):
        prio = "medium"

    clean_content = content.strip()
    clean_title = title.strip() or (clean_content[:35] + "..." if len(clean_content) > 35 else clean_content)

    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO vault_entries (category, title, content, priority, status)
            VALUES (?, ?, ?, ?, 'active')
        """, (cat, clean_title, clean_content, prio))
        entry_id = cursor.lastrowid
        conn.commit()

        cursor.execute("SELECT * FROM vault_entries WHERE id = ?", (entry_id,))
        return dict(cursor.fetchone())


def update_vault_entry(entry_id: int, status: Optional[str] = None, content: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Update status or content of an existing entry."""
    init_vault_db()
    updates = []
    params = []

    if status:
        updates.append("status = ?")
        params.append(status.lower().strip())
    if content:
        updates.append("content = ?")
        params.append(content.strip())

    if not updates:
        return None

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(entry_id)
    sql = f"UPDATE vault_entries SET {', '.join(updates)} WHERE id = ?"

    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()

        cursor.execute("SELECT * FROM vault_entries WHERE id = ?", (entry_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def delete_vault_entry(entry_id: int) -> bool:
    """Delete a vault entry by its ID."""
    init_vault_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vault_entries WHERE id = ?", (entry_id,))
        conn.commit()
        return cursor.rowcount > 0


# ─────────────────────────────────────────────
# Connected Accounts Operations
# ─────────────────────────────────────────────
def get_creator_accounts(platform: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all registered creator accounts or filter by platform."""
    init_vault_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        if platform:
            cursor.execute(
                "SELECT * FROM creator_accounts WHERE LOWER(platform) = LOWER(?) ORDER BY created_at ASC",
                (platform.strip(),)
            )
        else:
            cursor.execute("SELECT * FROM creator_accounts ORDER BY id ASC")
        return [dict(r) for r in cursor.fetchall()]


def add_or_update_creator_account(
    platform: str,
    account_name: str,
    handle: str,
    profile_url: str,
    content_theme: str = "",
    audience: str = "",
    api_key_or_token: str = "",
    status: str = "active",
    last_synced_summary: str = ""
) -> Dict[str, Any]:
    """Add a new account or update existing if platform & handle match."""
    init_vault_db()
    plat = platform.strip().lower()
    h = handle.strip()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM creator_accounts WHERE LOWER(platform) = ? AND (LOWER(handle) = ? OR profile_url = ?)",
            (plat, h.lower(), profile_url.strip())
        )
        existing = cursor.fetchone()
        if existing:
            cursor.execute("""
                UPDATE creator_accounts
                SET account_name = ?, handle = ?, profile_url = ?, content_theme = ?, audience = ?,
                    api_key_or_token = CASE WHEN ? != '' THEN ? ELSE api_key_or_token END,
                    status = ?, last_synced_summary = CASE WHEN ? != '' THEN ? ELSE last_synced_summary END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (account_name.strip(), h, profile_url.strip(), content_theme.strip(), audience.strip(),
                  api_key_or_token, api_key_or_token, status, last_synced_summary, last_synced_summary, existing["id"]))
            conn.commit()
            acc_id = existing["id"]
        else:
            cursor.execute("""
                INSERT INTO creator_accounts (platform, account_name, handle, profile_url, content_theme, audience, api_key_or_token, status, last_synced_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (plat, account_name.strip(), h, profile_url.strip(), content_theme.strip(), audience.strip(),
                  api_key_or_token, status, last_synced_summary))
            conn.commit()
            acc_id = cursor.lastrowid

        cursor.execute("SELECT * FROM creator_accounts WHERE id = ?", (acc_id,))
        return dict(cursor.fetchone())


def delete_creator_account(account_id: int) -> bool:
    """Delete a connected account."""
    init_vault_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM creator_accounts WHERE id = ?", (account_id,))
        conn.commit()
        return cursor.rowcount > 0


def update_account_sync_summary(account_id: int, summary: str) -> bool:
    """Update live synced stats / summary for an account."""
    init_vault_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE creator_accounts SET last_synced_summary = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (summary.strip(), account_id)
        )
        conn.commit()
        return cursor.rowcount > 0


# ─────────────────────────────────────────────
# Social Media Posts Operations
# ─────────────────────────────────────────────
def get_social_posts(platform: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve creator social media posts, drafts, or published history."""
    init_vault_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM creator_social_posts WHERE 1=1"
        params = []
        if platform:
            query += " AND LOWER(platform) = LOWER(?)"
            params.append(platform.strip())
        if status:
            query += " AND LOWER(status) = LOWER(?)"
            params.append(status.strip())
        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]


def add_social_post(
    platform: str,
    content: str,
    title: str = "",
    hashtags: str = "",
    media_urls: str = "",
    status: str = "draft"
) -> Dict[str, Any]:
    """Add a new drafted or published social post."""
    init_vault_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO creator_social_posts (platform, title, content, hashtags, media_urls, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (platform.strip().lower(), title.strip(), content.strip(), hashtags.strip(), media_urls.strip(), status.strip()))
        conn.commit()
        post_id = cursor.lastrowid
        cursor.execute("SELECT * FROM creator_social_posts WHERE id = ?", (post_id,))
        return dict(cursor.fetchone())


def update_social_post_status(post_id: int, status: str) -> bool:
    """Update status of a social post (draft, approved, published, archived)."""
    init_vault_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        pub_at = datetime.now().isoformat() if status == "published" else None
        if pub_at:
            cursor.execute(
                "UPDATE creator_social_posts SET status = ?, published_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status.strip(), pub_at, post_id)
            )
        else:
            cursor.execute(
                "UPDATE creator_social_posts SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status.strip(), post_id)
            )
        conn.commit()
        return cursor.rowcount > 0


def delete_social_post(post_id: int) -> bool:
    """Delete a social post draft or record."""
    init_vault_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM creator_social_posts WHERE id = ?", (post_id,))
        conn.commit()
        return cursor.rowcount > 0


# ─────────────────────────────────────────────
# Backup Export
# ─────────────────────────────────────────────
def export_vault_data() -> Dict[str, Any]:
    """Export complete Creator Vault data for backup."""
    init_vault_db()
    return {
        "version": "3.0",
        "exported_at": datetime.now().isoformat(),
        "profile": get_creator_profile(),
        "accounts": get_creator_accounts(),
        "social_posts": get_social_posts(),
        "projects": get_creator_projects(),
        "daily_focus": get_daily_focus(),
        "vault_entries": get_vault_entries(),
    }


# ─────────────────────────────────────────────
# Prompt Summary for AI Brain
# ─────────────────────────────────────────────
def get_creator_prompt_summary() -> str:
    """Generate comprehensive creator identity, digital dossier, online accounts, and projects for the LLM."""
    try:
        from backend.database.creator_dossier import get_dossier_prompt_context
        dossier_context = get_dossier_prompt_context()
        if dossier_context:
            return dossier_context

        profile = get_creator_profile()
        goals = get_vault_entries(category="goal", status="active")
        projects = get_creator_projects()
        focus_tasks = [t for t in get_daily_focus() if not t.get("completed")]
        accounts = get_creator_accounts()
        
        name = profile.get("name", "M. Akmal")
        title = profile.get("title", "Full Stack Developer & AI Engineer")
        github = profile.get("github", "")
        portfolio = profile.get("portfolio", "")
        linkedin = profile.get("linkedin", "")
        tech = profile.get("tech_stack", "")
        coding_pref = profile.get("coding_preferences", "")
        ai_tone = profile.get("ai_tone", "")

        summary_parts = [
            f"CREATOR IDENTITY & VAULT: You are the personal assistant of {name} ({title}).",
            f"Tone Preference: {ai_tone}." if ai_tone else "",
            f"Coding Preferences: {coding_pref}." if coding_pref else "",
            f"Tech Stack: {tech}." if tech else "",
            f"GitHub: {github}." if github else "",
            f"Portfolio: {portfolio}." if portfolio else "",
            f"LinkedIn: {linkedin}." if linkedin else "",
        ]

        if accounts:
            acc_list = [f"{a.get('platform').capitalize()} ({a.get('handle')}: {a.get('content_theme') or 'general'})" for a in accounts[:6]]
            summary_parts.append(f"Connected Creator Accounts: {', '.join(acc_list)}.")

        if projects:
            proj_list = [f"{p.get('name')} (Path: {p.get('path')})" for p in projects[:4]]
            summary_parts.append(f"Registered Projects: {', '.join(proj_list)}.")

        if focus_tasks:
            tasks_str = "; ".join([t.get("task", "") for t in focus_tasks[:3]])
            summary_parts.append(f"Today's Priority Focus Tasks: {tasks_str}.")

        if goals:
            active_goals = [f"{g.get('title')}: {g.get('content')}" for g in goals[:3]]
            summary_parts.append("Key Goals: " + " | ".join(active_goals))

        return " ".join([p for p in summary_parts if p])
    except Exception:
        return "CREATOR IDENTITY: You are JARVIS, built exclusively for your creator M. Akmal (Akmal Sir)."

