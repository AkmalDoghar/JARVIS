"""
JARVIS Phase 6B: Persistent Long-Term Memory Matrix
Stores user preferences, project context, instructions, facts, and conversation insights.
Uses local SQLite (works 100% offline, zero cloud reliance).
Strictly enforces privacy: refuses passwords, tokens, API keys, and financial credentials.
"""

import os
import re
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "jarvis_vault.db")

# Strict blacklist patterns for sensitive credentials & secrets (Rule 7 & Section 6.6)
SENSITIVE_SECRET_PATTERNS = [
    r"\b(?:password|passwd|pwd|passcode|passphrase)\b",
    r"\b(?:api[\s_-]?key|secret[\s_-]?key|access[\s_-]?token|bearer[\s_-]?token|auth[\s_-]?token|jwt)\b",
    r"\b(?:credit[\s_-]?card|debit[\s_-]?card|cvv|cvc|card[\s_-]?number)\b",
    r"\b(?:otp|one[\s_-]?time[\s_-]?password|pin[\s_-]?code|2fa|mfa)\b",
    r"\b(?:private[\s_-]?key|rsa[\s_-]?private|ssh[\s_-]?key|id_rsa)\b",
    r"\b(?:sk-[a-zA-Z0-9_-]{20,})\b",  # OpenAI / API key patterns
    r"\b(?:ghp_[a-zA-Z0-9]{36})\b",     # GitHub Personal Access Token
]

SENSITIVE_REGEX = re.compile("|".join(SENSITIVE_SECRET_PATTERNS), re.IGNORECASE)


def is_sensitive_secret(text: str) -> bool:
    """Return True if text contains passwords, API keys, OTPs, or financial secrets."""
    if not text:
        return False
    return bool(SENSITIVE_REGEX.search(text))


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_memory_db() -> None:
    """Initialize the Long-term Memory Matrix SQLite table."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL CHECK (category IN ('preference', 'project', 'instruction', 'fact', 'context')),
                key TEXT,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '',
                importance INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Index for fast lookup by category and key
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_category ON jarvis_memories(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_key ON jarvis_memories(key)")
        conn.commit()


# Initialize table on import
init_memory_db()


def remember(
    content: str,
    category: str = "preference",
    key: Optional[str] = None,
    tags: Optional[List[str]] = None,
    importance: int = 1
) -> Dict[str, Any]:
    """
    Save an explicit user preference, fact, project context, or instruction into long-term memory.
    Refuses passwords, tokens, API keys, or financial secrets.
    """
    if not content or not content.strip():
        return {
            "success": False,
            "error": "Memory content cannot be empty."
        }

    # Security check: Never store sensitive secrets (Rule 7)
    combined_check = f"{content} {key or ''} {' '.join(tags or [])}"
    if is_sensitive_secret(combined_check):
        return {
            "success": False,
            "error": "Security Policy: JARVIS refuses to store passwords, API keys, PINs, or financial secrets in memory."
        }

    valid_categories = {"preference", "project", "instruction", "fact", "context"}
    cat = category.lower().strip() if category else "preference"
    if cat not in valid_categories:
        cat = "preference"

    clean_content = content.strip()
    clean_key = (key.strip().lower() if key else None)
    clean_tags = ",".join([t.strip().lower() for t in tags if t.strip()]) if tags else ""

    with _get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if identical key and category already exist -> update it
        if clean_key:
            cursor.execute("""
                SELECT id FROM jarvis_memories 
                WHERE category = ? AND LOWER(key) = ?
            """, (cat, clean_key))
            existing = cursor.fetchone()
            if existing:
                mem_id = existing["id"]
                cursor.execute("""
                    UPDATE jarvis_memories
                    SET content = ?, tags = ?, importance = ?, updated_at = CURRENT_TIMESTAMP, last_accessed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (clean_content, clean_tags, importance, mem_id))
                conn.commit()
                return {
                    "success": True,
                    "id": mem_id,
                    "action": "updated",
                    "category": cat,
                    "key": clean_key,
                    "content": clean_content
                }

        # Otherwise insert new memory entry
        cursor.execute("""
            INSERT INTO jarvis_memories (category, key, content, tags, importance)
            VALUES (?, ?, ?, ?, ?)
        """, (cat, clean_key, clean_content, clean_tags, importance))
        conn.commit()
        mem_id = cursor.lastrowid

        return {
            "success": True,
            "id": mem_id,
            "action": "saved",
            "category": cat,
            "key": clean_key,
            "content": clean_content
        }


def recall(
    query: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 15
) -> List[Dict[str, Any]]:
    """
    Search and retrieve long-term memories matching a query keyword or category.
    Updates last_accessed_at for retrieved items.
    """
    with _get_connection() as conn:
        cursor = conn.cursor()
        sql = "SELECT * FROM jarvis_memories WHERE 1=1"
        params: List[Any] = []

        if category and category.strip():
            sql += " AND category = ?"
            params.append(category.strip().lower())

        if query and query.strip():
            keywords = [k.strip() for k in re.findall(r"\w+", query) if len(k.strip()) >= 2]
            if keywords:
                like_clauses = []
                for kw in keywords:
                    like_clauses.append("(content LIKE ? OR key LIKE ? OR tags LIKE ?)")
                    params.extend([f"%{kw}%", f"%{kw}%", f"%{kw}%"])
                sql += " AND (" + " OR ".join(like_clauses) + ")"

        sql += " ORDER BY importance DESC, updated_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        results = [dict(r) for r in rows]

        # Update last_accessed_at
        if results:
            ids = [r["id"] for r in results]
            placeholders = ",".join("?" for _ in ids)
            cursor.execute(f"UPDATE jarvis_memories SET last_accessed_at = CURRENT_TIMESTAMP WHERE id IN ({placeholders})", ids)
            conn.commit()

        return results


def get_all_memories() -> List[Dict[str, Any]]:
    """Return all stored memories ordered by newest first."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jarvis_memories ORDER BY id DESC")
        return [dict(r) for r in cursor.fetchall()]


def forget(memory_id: int) -> bool:
    """Delete a single memory by ID."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jarvis_memories WHERE id = ?", (memory_id,))
        conn.commit()
        return cursor.rowcount > 0


def forget_by_keyword(keyword: str) -> int:
    """Delete all memories matching a keyword in content, key, or tags."""
    if not keyword or not keyword.strip():
        return 0
    kw = f"%{keyword.strip()}%"
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jarvis_memories WHERE content LIKE ? OR key LIKE ? OR tags LIKE ?", (kw, kw, kw))
        conn.commit()
        return cursor.rowcount


def forget_all() -> int:
    """Erase all memories from the long-term matrix ('Forget Everything')."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jarvis_memories")
        conn.commit()
        return cursor.rowcount


def get_relevant_memories_for_prompt(user_query: str, limit: int = 6) -> str:
    """
    Search for memories relevant to the user query and format as clean context for LLM prompt.
    If query is general, includes top important preferences.
    """
    memories = recall(query=user_query, limit=limit)
    if not memories:
        # Fallback to top preferences
        memories = recall(category="preference", limit=4)
        if not memories:
            return ""

    lines = []
    for m in memories:
        cat = m.get("category", "preference").capitalize()
        key = m.get("key")
        content = m.get("content", "")
        if key:
            lines.append(f"- [{cat}: {key}] {content}")
        else:
            lines.append(f"- [{cat}] {content}")

    return "\n".join(lines)
