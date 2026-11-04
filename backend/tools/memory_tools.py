"""
JARVIS Phase 6B: Memory Matrix Tools
Provides functions for LLM tool calling to remember, recall, and manage user preferences and context.
Works 100% offline using local SQLite database.
"""

from typing import Any, Dict, List, Optional
from backend.database import memory as memory_db


def remember_information(
    content: str,
    category: str = "preference",
    key: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Save an explicit user instruction, habit, fact, or preference into JARVIS's persistent memory matrix.
    Refuses passwords, tokens, API keys, and sensitive financial secrets.
    """
    res = memory_db.remember(
        content=content,
        category=category,
        key=key,
        tags=tags
    )
    if not res.get("success"):
        return {
            "success": False,
            "error": res.get("error", "Failed to store memory.")
        }

    action_verb = "updated" if res.get("action") == "updated" else "saved"
    return {
        "success": True,
        "message": f"Successfully {action_verb} in memory: '{res.get('content')}' [Category: {res.get('category')}].",
        "memory_id": res.get("id"),
        "key": res.get("key"),
        "category": res.get("category"),
        "content": res.get("content")
    }


def recall_memories(
    query: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search and retrieve stored memories from JARVIS's persistent long-term memory matrix.
    """
    memories = memory_db.recall(query=query, category=category, limit=limit)
    if not memories:
        return {
            "success": True,
            "message": "No matching memories found.",
            "count": 0,
            "memories": []
        }

    return {
        "success": True,
        "message": f"Found {len(memories)} relevant memories.",
        "count": len(memories),
        "memories": memories
    }


def forget_memory(
    memory_id: Optional[int] = None,
    keyword: Optional[str] = None,
    forget_all: bool = False
) -> Dict[str, Any]:
    """
    Delete a specific memory by ID, memories matching a keyword, or erase all memories.
    """
    if forget_all:
        count = memory_db.forget_all()
        return {
            "success": True,
            "message": f"Erased all {count} long-term memories. Memory Matrix is now fresh.",
            "deleted_count": count
        }

    if memory_id is not None:
        deleted = memory_db.forget(memory_id)
        if deleted:
            return {
                "success": True,
                "message": f"Memory #{memory_id} has been forgotten.",
                "memory_id": memory_id
            }
        return {
            "success": False,
            "error": f"Memory #{memory_id} was not found."
        }

    if keyword and keyword.strip():
        count = memory_db.forget_by_keyword(keyword.strip())
        return {
            "success": True,
            "message": f"Deleted {count} memories matching keyword '{keyword}'.",
            "deleted_count": count
        }

    return {
        "success": False,
        "error": "Specify either memory_id, keyword, or forget_all=True."
    }
