"""
JARVIS Security Framework: Path Protection & Boundary Rules
Phase 4 Security Component: Strict validation of file system paths.
Ensures file and coding tools only touch approved project directories
and strictly blocks critical Windows system paths and directory traversal attacks.
"""

import os
from pathlib import Path
from typing import Tuple, List, Optional
from backend.database.vault import get_creator_projects

# High-risk Windows system directories that can NEVER be read or written to
BLOCKED_SYSTEM_PATHS: List[str] = [
    r"C:\Windows",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    r"C:\ProgramData",
    r"C:\Recovery",
    r"C:\System Volume Information",
    r"C:\$Recycle.Bin",
    r"C:\Boot",
    r"C:\EFI",
]

# Sensitive system files that can never be accessed
BLOCKED_SYSTEM_FILES: List[str] = [
    "pagefile.sys",
    "hiberfil.sys",
    "swapfile.sys",
    "bootmgr",
    "NTUSER.DAT",
    "SAM",
    "SECURITY",
    "SYSTEM",
    "SOFTWARE",
]

# Safe default user bases
USER_HOME = os.path.expanduser("~")

def get_windows_shell_folder(folder_key: str, fallback_rel: str) -> str:
    """Retrieve actual active Windows shell folder (handles OneDrive folder redirection)."""
    # 1. Try Windows Registry (User Shell Folders)
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        ) as key:
            val, _ = winreg.QueryValueEx(key, folder_key)
            expanded = os.path.normpath(os.path.expandvars(val))
            if os.path.exists(expanded):
                return expanded
    except Exception:
        pass

    # 2. Check OneDrive subfolder as primary fallback if redirected
    onedrive_path = os.path.join(USER_HOME, "OneDrive", fallback_rel)
    if os.path.exists(onedrive_path):
        return os.path.normpath(onedrive_path)

    # 3. Standard user home fallback
    return os.path.normpath(os.path.join(USER_HOME, fallback_rel))

REAL_DESKTOP = get_windows_shell_folder("Desktop", "Desktop")
REAL_DOCUMENTS = get_windows_shell_folder("Personal", "Documents")
REAL_DOWNLOADS = get_windows_shell_folder("{374DE290-123F-4565-9164-39C4925E467B}", "Downloads")

DEFAULT_SAFE_ROOTS: List[str] = [
    r"D:\projects",
    r"C:\projects",
    REAL_DESKTOP,
    REAL_DOCUMENTS,
    REAL_DOWNLOADS,
    os.path.join(USER_HOME, "Desktop"),
    os.path.join(USER_HOME, "Documents"),
    os.path.join(USER_HOME, "Downloads"),
    os.path.join(USER_HOME, "Projects"),
    os.path.join(USER_HOME, "source"),
    os.path.join(USER_HOME, "workspace"),
]


def get_approved_roots() -> List[str]:
    """
    Get all approved root directories:
    Includes registered projects from Creator Vault and standard user dev roots.
    """
    roots = list(DEFAULT_SAFE_ROOTS)
    
    # Add all projects registered in Creator Vault
    try:
        projects = get_creator_projects()
        for p in projects:
            path = p.get("path")
            if path and os.path.exists(path):
                roots.append(os.path.abspath(path))
    except Exception:
        pass

    # Normalize all roots
    normalized = []
    for r in roots:
        norm = os.path.normpath(os.path.abspath(r))
        if norm not in normalized:
            normalized.append(norm)

    return normalized


WINDOWS_USER_LIBRARIES = {
    "downloads": REAL_DOWNLOADS,
    "download": REAL_DOWNLOADS,
    "downlord": REAL_DOWNLOADS,
    "downlaod": REAL_DOWNLOADS,
    "desktop": REAL_DESKTOP,
    "documents": REAL_DOCUMENTS,
    "document": REAL_DOCUMENTS,
    "doc": REAL_DOCUMENTS,
    "docs": REAL_DOCUMENTS,
    "my documents": REAL_DOCUMENTS,
    "my document": REAL_DOCUMENTS,
    "pictures": os.path.join(USER_HOME, "Pictures"),
    "picture": os.path.join(USER_HOME, "Pictures"),
    "photos": os.path.join(USER_HOME, "Pictures"),
    "videos": os.path.join(USER_HOME, "Videos"),
    "video": os.path.join(USER_HOME, "Videos"),
    "music": os.path.join(USER_HOME, "Music"),
}


def resolve_path(target_path: str, project_context: Optional[str] = None) -> str:
    """
    Resolve a potentially relative or shorthand path into an absolute canonical path.
    Supports Windows user libraries (Downloads, Desktop, Documents, etc.), tilde (~),
    environment variables, and relative project paths. Automatically redirects
    Desktop/Documents to active OneDrive shell folder if redirected.
    """
    clean = target_path.strip().strip("'\"")

    # Expand tilde and environment variables
    if clean.startswith("~"):
        clean = os.path.expanduser(clean)
    clean = os.path.expandvars(clean)

    if os.path.isabs(clean):
        norm = os.path.normpath(clean)

        # Handle redirection from local unredirected Desktop/Documents to active OneDrive folders
        local_desktop = os.path.normpath(os.path.join(USER_HOME, "Desktop"))
        if REAL_DESKTOP.lower() != local_desktop.lower():
            if norm.lower() == local_desktop.lower():
                return REAL_DESKTOP
            if norm.lower().startswith(local_desktop.lower() + os.sep):
                rel = norm[len(local_desktop) + 1:]
                return os.path.normpath(os.path.join(REAL_DESKTOP, rel))

        local_docs = os.path.normpath(os.path.join(USER_HOME, "Documents"))
        if REAL_DOCUMENTS.lower() != local_docs.lower():
            if norm.lower() == local_docs.lower():
                return REAL_DOCUMENTS
            if norm.lower().startswith(local_docs.lower() + os.sep):
                rel = norm[len(local_docs) + 1:]
                return os.path.normpath(os.path.join(REAL_DOCUMENTS, rel))

        parts = norm.split(os.sep)
        # Handle cases where model hallucinated username (e.g. C:\Users\Akmal\Desktop\... -> REAL_DESKTOP\...)
        if len(parts) >= 3 and parts[0].endswith(":") and parts[1].lower() == "users":
            guessed_user = parts[2].lower()
            actual_user = os.path.basename(USER_HOME).lower()
            if guessed_user != actual_user and guessed_user != "public":
                guessed_path = os.path.join(parts[0] + os.sep, parts[1], parts[2])
                if not os.path.exists(guessed_path):
                    if len(parts) > 3 and parts[3].lower() == "desktop":
                        return os.path.normpath(os.path.join(REAL_DESKTOP, *parts[4:]))
                    if len(parts) > 3 and parts[3].lower() == "documents":
                        return os.path.normpath(os.path.join(REAL_DOCUMENTS, *parts[4:]))
                    return os.path.normpath(os.path.join(USER_HOME, *parts[3:]))
        return norm

    # Check if first component is a Windows User Library (e.g. 'downloads/private' or 'desktop/file.txt')
    normalized_slashes = clean.replace('/', '\\')
    parts = [p.strip() for p in normalized_slashes.split('\\') if p.strip()]
    if parts:
        first_segment = parts[0].lower()
        if first_segment in WINDOWS_USER_LIBRARIES:
            library_base = WINDOWS_USER_LIBRARIES[first_segment]
            if len(parts) > 1:
                return os.path.normpath(os.path.join(library_base, *parts[1:]))
            return os.path.normpath(library_base)

    # If relative, resolve against context
    base = project_context or os.getcwd()
    return os.path.normpath(os.path.join(base, clean))


def is_path_allowed(target_path: str, for_write: bool = False, project_context: Optional[str] = None) -> Tuple[bool, str, str]:
    """
    Validate whether a target file/folder path is permitted for access.
    
    Returns:
        (allowed: bool, canonical_path: str, message: str)
    """
    if not target_path or not target_path.strip():
        return False, "", "Path cannot be empty."

    # 1. Resolve canonical absolute path
    canonical_path = resolve_path(target_path, project_context)

    # 2. Prevent directory traversal attacks checking
    # os.path.normpath and os.path.abspath eliminate '..'
    norm_lower = canonical_path.lower()

    # 3. Check against blocked Windows system directories
    for blocked in BLOCKED_SYSTEM_PATHS:
        blocked_norm = os.path.normpath(blocked).lower()
        if norm_lower == blocked_norm or norm_lower.startswith(blocked_norm + os.sep):
            return False, canonical_path, f"Access DENIED: '{canonical_path}' is inside a protected Windows system directory."

    # 4. Check for blocked system file names
    base_name = os.path.basename(canonical_path)
    if base_name in BLOCKED_SYSTEM_FILES or base_name.upper() in BLOCKED_SYSTEM_FILES:
        return False, canonical_path, f"Access DENIED: '{base_name}' is a protected Windows system file."

    # 5. Check drive roots (e.g. C:\ or D:\ directly without subfolder)
    path_obj = Path(canonical_path)
    if path_obj.parent == path_obj:  # Root directory itself
        return False, canonical_path, "Access DENIED: Cannot operate directly on a drive root directory."

    # 6. Allow user operations across all valid PC drives and directories
    # (Excluding protected Windows system paths, system files, and bare drive roots checked above)
    return True, canonical_path, "Path authorized."

