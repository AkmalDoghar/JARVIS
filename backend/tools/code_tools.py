"""
JARVIS Coding & Files Tools
Phase 4 Component: High-precision file reading, project inspection, codebase search,
code editing with unified diffs, Git operations, test execution, and error diagnostics.
Protected by Path Security Guard and JARVIS Risk Evaluation Framework.
"""

import os
import re
import difflib
import shutil
import subprocess
from typing import Dict, Any, List, Optional
from backend.security.path_rules import is_path_allowed, resolve_path

# Standard directories and patterns to skip during directory walks and searches
IGNORED_DIRS = {
    "node_modules", ".venv", "venv", ".git", ".next", "__pycache__", 
    "dist", "build", "coverage", ".idea", ".vscode", "target", ".turbo"
}

IGNORED_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".dll", ".exe", ".so", ".dylib", ".bin", 
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".mp3", ".wav", 
    ".mp4", ".zip", ".tar", ".gz", ".7z", ".pdf", ".lock"
}


# ─────────────────────────────────────────────
# 1. Read File
# ─────────────────────────────────────────────
def read_file(file_path: str, max_lines: int = 250, offset: int = 1) -> Dict[str, Any]:
    """
    Read the contents of a file inside an approved project directory.
    Supports line slicing (offset and max_lines).
    """
    allowed, canonical, msg = is_path_allowed(file_path, for_write=False)
    if not allowed:
        return {"success": False, "error": msg}

    if not os.path.exists(canonical):
        return {"success": False, "error": f"File '{canonical}' does not exist."}

    if os.path.isdir(canonical):
        return {"success": False, "error": f"'{canonical}' is a directory, not a file. Use list_directory_files instead."}

    try:
        # Detect encoding
        encoding = "utf-8"
        try:
            with open(canonical, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            encoding = "latin-1"
            with open(canonical, "r", encoding="latin-1") as f:
                lines = f.readlines()

        total_lines = len(lines)
        start_idx = max(0, offset - 1)
        end_idx = min(total_lines, start_idx + max_lines)
        sliced_lines = lines[start_idx:end_idx]

        content = "".join(sliced_lines)
        is_truncated = end_idx < total_lines

        return {
            "success": True,
            "path": canonical,
            "filename": os.path.basename(canonical),
            "encoding": encoding,
            "total_lines": total_lines,
            "lines_shown": len(sliced_lines),
            "offset": offset,
            "is_truncated": is_truncated,
            "content": content,
            "message": f"Read {len(sliced_lines)} of {total_lines} lines from '{os.path.basename(canonical)}'."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to read file: {str(e)}"}


# ─────────────────────────────────────────────
# 2. Inspect Project
# ─────────────────────────────────────────────
def inspect_project(project_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze a project's architecture, dependencies, git status, and key entry points.
    """
    target = project_path or os.getcwd()
    allowed, canonical, msg = is_path_allowed(target, for_write=False)
    if not allowed:
        return {"success": False, "error": msg}

    if not os.path.isdir(canonical):
        return {"success": False, "error": f"Project folder '{canonical}' is not a directory."}

    try:
        project_name = os.path.basename(canonical) or "Project"
        findings: Dict[str, Any] = {
            "project_name": project_name,
            "path": canonical,
            "frameworks": [],
            "dependencies": [],
            "scripts": {},
            "entry_files": [],
            "git": {}
        }

        # Check for Node.js / Next.js
        pkg_json_path = os.path.join(canonical, "package.json")
        if os.path.exists(pkg_json_path):
            import json
            try:
                with open(pkg_json_path, "r", encoding="utf-8") as f:
                    pkg_data = json.load(f)
                    findings["frameworks"].append("Node.js")
                    deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
                    if "next" in deps:
                        findings["frameworks"].append(f"Next.js ({deps.get('next')})")
                    if "react" in deps:
                        findings["frameworks"].append(f"React ({deps.get('react')})")
                    if "tailwindcss" in deps:
                        findings["frameworks"].append("Tailwind CSS")
                    if "typescript" in deps:
                        findings["frameworks"].append("TypeScript")
                    if "fastapi" in deps:
                        findings["frameworks"].append("FastAPI")

                    findings["dependencies"] = list(deps.keys())[:25]
                    findings["scripts"] = pkg_data.get("scripts", {})
            except Exception:
                pass

        # Check for Python
        req_path = os.path.join(canonical, "requirements.txt")
        if os.path.exists(req_path):
            findings["frameworks"].append("Python")
            try:
                with open(req_path, "r", encoding="utf-8") as f:
                    req_lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                    findings["dependencies"].extend(req_lines[:25])
                    for r in req_lines:
                        r_lower = r.lower()
                        if "fastapi" in r_lower:
                            findings["frameworks"].append("FastAPI")
                        elif "flask" in r_lower:
                            findings["frameworks"].append("Flask")
                        elif "django" in r_lower:
                            findings["frameworks"].append("Django")
            except Exception:
                pass

        pyproject_path = os.path.join(canonical, "pyproject.toml")
        if os.path.exists(pyproject_path) and "Python" not in findings["frameworks"]:
            findings["frameworks"].append("Python (pyproject.toml)")

        # Identify key entry files
        common_entries = [
            "main.py", "app.py", "index.ts", "index.js", "src/app/page.tsx", 
            "src/main.ts", "server.js", "App.tsx", "README.md"
        ]
        for entry in common_entries:
            ep = os.path.join(canonical, entry)
            if os.path.exists(ep):
                findings["entry_files"].append(entry)

        # Check Git status
        git_dir = os.path.join(canonical, ".git")
        if os.path.exists(git_dir):
            try:
                branch = subprocess.check_output(
                    ["git", "branch", "--show-current"], 
                    cwd=canonical, text=True, timeout=5, stderr=subprocess.DEVNULL
                ).strip()
                status = subprocess.check_output(
                    ["git", "status", "--short"], 
                    cwd=canonical, text=True, timeout=5, stderr=subprocess.DEVNULL
                ).strip()
                findings["git"] = {
                    "is_git_repo": True,
                    "branch": branch or "main",
                    "modified_count": len(status.splitlines()) if status else 0,
                    "status_summary": status[:500] if status else "Clean working tree"
                }
            except Exception:
                findings["git"] = {"is_git_repo": True, "error": "Could not query git"}
        else:
            findings["git"] = {"is_git_repo": False}

        # Summary text
        fm_str = ", ".join(set(findings["frameworks"])) or "General Project"
        entries_str = ", ".join(findings["entry_files"]) or "None identified"
        git_str = f"Branch: {findings['git'].get('branch', 'N/A')}, Modified: {findings['git'].get('modified_count', 0)}" if findings['git'].get('is_git_repo') else "Not a Git repo"

        message = (
            f"Project '{project_name}' ({canonical})\n"
            f"Stack: {fm_str}\n"
            f"Entry Points: {entries_str}\n"
            f"Git: {git_str}"
        )

        return {
            "success": True,
            "project": findings,
            "message": message
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to inspect project: {str(e)}"}


# ─────────────────────────────────────────────
# 3. List Directory Files
# ─────────────────────────────────────────────
def list_directory_files(directory_path: str, recursive: bool = False, max_depth: int = 2) -> Dict[str, Any]:
    """
    List files and folders in an approved directory, ignoring bulky vendor/cache directories.
    """
    allowed, canonical, msg = is_path_allowed(directory_path, for_write=False)
    if not allowed:
        return {"success": False, "error": msg}

    if not os.path.isdir(canonical):
        return {"success": False, "error": f"'{canonical}' is not a directory."}

    items = []
    base_depth = canonical.rstrip(os.sep).count(os.sep)

    try:
        if not recursive:
            with os.scandir(canonical) as scanner:
                for entry in scanner:
                    if entry.name in IGNORED_DIRS or entry.name.startswith("."):
                        continue
                    items.append({
                        "name": entry.name,
                        "type": "directory" if entry.is_dir() else "file",
                        "size": entry.stat().st_size if entry.is_file() else None,
                        "path": os.path.relpath(entry.path, canonical)
                    })
        else:
            for root, dirs, files in os.walk(canonical):
                # Filter out ignored dirs in-place
                dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
                cur_depth = root.count(os.sep) - base_depth
                if cur_depth >= max_depth:
                    continue

                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in IGNORED_EXTENSIONS or f.startswith("."):
                        continue
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, canonical)
                    items.append({
                        "name": f,
                        "type": "file",
                        "path": rel_p,
                        "size": os.path.getsize(full_p)
                    })

                for d in dirs:
                    full_d = os.path.join(root, d)
                    rel_d = os.path.relpath(full_d, canonical)
                    items.append({
                        "name": d,
                        "type": "directory",
                        "path": rel_d,
                    })

                if len(items) >= 200:
                    break

        return {
            "success": True,
            "directory": canonical,
            "total_items": len(items),
            "items": items[:150],
            "message": f"Found {len(items)} items in '{os.path.basename(canonical)}'."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to list directory: {str(e)}"}


# ─────────────────────────────────────────────
# 4. Search Codebase
# ─────────────────────────────────────────────
def search_codebase(query: str, project_path: Optional[str] = None, file_pattern: str = "") -> Dict[str, Any]:
    """
    Search for a text string, function name, class, or pattern across project files.
    """
    if not query or not query.strip():
        return {"success": False, "error": "Search query cannot be empty."}

    target = project_path or os.getcwd()
    allowed, canonical, msg = is_path_allowed(target, for_write=False)
    if not allowed:
        return {"success": False, "error": msg}

    clean_query = query.strip("? '\".,:;!").strip()
    if not clean_query:
        return {"success": False, "error": "Search query cannot be empty."}

    regex = re.compile(re.escape(clean_query), re.IGNORECASE)
    pattern_re = re.compile(file_pattern, re.IGNORECASE) if file_pattern else None

    matches = []
    max_matches = 35

    def scan_dir(target_regex):
        found = []
        for root, dirs, files in os.walk(canonical):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in IGNORED_EXTENSIONS or f.startswith("."):
                    continue

                if pattern_re and not pattern_re.search(f):
                    continue

                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, canonical)

                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as file_obj:
                        for line_num, line in enumerate(file_obj, 1):
                            if target_regex.search(line):
                                found.append({
                                    "file": rel_path,
                                    "line": line_num,
                                    "snippet": line.strip()[:180]
                                })
                                if len(found) >= max_matches:
                                    return found
                except Exception:
                    continue
        return found

    try:
        matches = scan_dir(regex)

        # Smart Fallback: if 0 matches and query contains common STT mishearings (e.g. jarver -> jarvis)
        if not matches and "jarver" in clean_query.lower():
            alt_query = re.sub(r"jarver", "jarvis", clean_query, flags=re.IGNORECASE)
            matches = scan_dir(re.compile(re.escape(alt_query), re.IGNORECASE))
            if matches:
                clean_query = alt_query

        summary = "\n".join([f"{m['file']}:{m['line']}: {m['snippet']}" for m in matches[:10]])
        if not matches:
            msg = f"Found 0 matches for '{clean_query}' in '{os.path.basename(canonical)}'."
        else:
            msg = f"Found {len(matches)} match(es) for '{clean_query}':\n{summary}"

        return {
            "success": True,
            "query": clean_query,
            "total_matches": len(matches),
            "matches": matches,
            "message": msg
        }
    except Exception as e:
        return {"success": False, "error": f"Codebase search failed: {str(e)}"}


# ─────────────────────────────────────────────
# 5. Create File
# ─────────────────────────────────────────────
def create_file(file_path: Optional[str] = None, content: Optional[str] = None, overwrite: bool = True, path: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new file with specified content anywhere on PC.
    Overwrites if file already exists when overwrite=True.
    """
    target_path = file_path or path
    if not target_path or not str(target_path).strip():
        return {
            "success": False, 
            "error": "Missing required argument 'file_path'. Please provide the destination path for the file."
        }
    
    if content is None:
        content = ""

    allowed, canonical, msg = is_path_allowed(target_path, for_write=True)
    if not allowed:
        return {"success": False, "error": msg}

    is_existing = os.path.exists(canonical)
    if is_existing and not overwrite:
        return {
            "success": False, 
            "error": f"File '{canonical}' already exists. Use modify_file to edit existing files safely."
        }

    try:
        os.makedirs(os.path.dirname(canonical), exist_ok=True)
        with open(canonical, "w", encoding="utf-8") as f:
            f.write(content)

        line_count = len(content.splitlines())
        byte_size = os.path.getsize(canonical)

        action_word = "Updated" if is_existing else "Created"
        return {
            "success": True,
            "path": canonical,
            "filename": os.path.basename(canonical),
            "lines": line_count,
            "bytes": byte_size,
            "message": f"{action_word} file '{os.path.basename(canonical)}' ({line_count} lines, {byte_size} bytes)."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to write file: {str(e)}"}


# ─────────────────────────────────────────────
# 6. Create Folder
# ─────────────────────────────────────────────
def create_folder(folder_path: Optional[str] = None, path: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a directory in an approved project workspace.
    Medium risk action.
    """
    target_folder = folder_path or path
    if not target_folder or not str(target_folder).strip():
        return {
            "success": False,
            "error": "Missing required argument 'folder_path'. Please provide the directory path to create."
        }

    allowed, canonical, msg = is_path_allowed(target_folder, for_write=True)
    if not allowed:
        return {"success": False, "error": msg}

    if os.path.exists(canonical):
        return {"success": True, "path": canonical, "message": f"Folder '{canonical}' already exists."}

    try:
        os.makedirs(canonical, exist_ok=True)
        return {
            "success": True,
            "path": canonical,
            "message": f"Created folder '{canonical}' successfully."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to create folder: {str(e)}"}


# ─────────────────────────────────────────────
# 7. Modify File with Diff Generation
# ─────────────────────────────────────────────
def modify_file(file_path: str, target_content: str, replacement_content: str) -> Dict[str, Any]:
    """
    Modify an existing file by replacing target_content with replacement_content.
    Generates a unified git-style diff. Medium risk action.
    """
    allowed, canonical, msg = is_path_allowed(file_path, for_write=True)
    if not allowed:
        return {"success": False, "error": msg}

    if not os.path.exists(canonical):
        return {"success": False, "error": f"File '{canonical}' does not exist to modify."}

    try:
        with open(canonical, "r", encoding="utf-8") as f:
            original = f.read()

        if target_content not in original:
            return {
                "success": False,
                "error": f"Target content was not found in '{os.path.basename(canonical)}'. Please read the file first to verify exact contents."
            }

        new_content = original.replace(target_content, replacement_content, 1)

        # Generate Unified Diff
        orig_lines = original.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        diff_lines = list(difflib.unified_diff(
            orig_lines, new_lines,
            fromfile=f"a/{os.path.basename(canonical)}",
            tofile=f"b/{os.path.basename(canonical)}",
            lineterm=""
        ))
        diff_str = "\n".join(diff_lines)

        # Write modified content
        with open(canonical, "w", encoding="utf-8") as f:
            f.write(new_content)

        return {
            "success": True,
            "path": canonical,
            "diff": diff_str,
            "message": f"Successfully updated '{os.path.basename(canonical)}'.\n\n```diff\n{diff_str}\n```"
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to modify file: {str(e)}"}


# ─────────────────────────────────────────────
# 8. Delete File or Folder (HIGH RISK - PIN Protected)
# ─────────────────────────────────────────────
def delete_file_or_folder(target_path: str) -> Dict[str, Any]:
    """
    Delete a specific file or folder.
    HIGH RISK: Requires explicit confirmation and Security PIN.
    """
    allowed, canonical, msg = is_path_allowed(target_path, for_write=True)
    if not allowed:
        return {"success": False, "error": msg}

    if not os.path.exists(canonical):
        return {"success": False, "error": f"Target '{canonical}' does not exist."}

    # Protection: Never allow deleting an approved root itself!
    from backend.security.path_rules import get_approved_roots
    for root in get_approved_roots():
        if os.path.normpath(canonical).lower() == os.path.normpath(root).lower():
            return {
                "success": False, 
                "error": f"Security Violation: Cannot delete an entire approved project/workspace root '{canonical}'."
            }

    try:
        if os.path.isdir(canonical):
            shutil.rmtree(canonical)
            return {
                "success": True,
                "deleted": canonical,
                "type": "directory",
                "message": f"Permanently deleted directory '{canonical}'."
            }
        else:
            os.remove(canonical)
            return {
                "success": True,
                "deleted": canonical,
                "type": "file",
                "message": f"Permanently deleted file '{canonical}'."
            }
    except Exception as e:
        return {"success": False, "error": f"Failed to delete '{canonical}': {str(e)}"}


# ─────────────────────────────────────────────
# 9. Run Git Status
# ─────────────────────────────────────────────
def run_git_status(project_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve Git working tree status and active branch.
    """
    target = project_path or os.getcwd()
    allowed, canonical, msg = is_path_allowed(target, for_write=False)
    if not allowed:
        return {"success": False, "error": msg}

    git_dir = os.path.join(canonical, ".git")
    if not os.path.exists(git_dir):
        return {"success": False, "error": f"'{canonical}' is not a Git repository."}

    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], 
            cwd=canonical, text=True, timeout=6, stderr=subprocess.DEVNULL
        ).strip()
        status_out = subprocess.check_output(
            ["git", "status", "--short"], 
            cwd=canonical, text=True, timeout=6, stderr=subprocess.DEVNULL
        ).strip()

        lines = status_out.splitlines() if status_out else []
        modified = [l[3:] for l in lines if l.startswith((" M", "M "))]
        untracked = [l[3:] for l in lines if l.startswith("??")]
        staged = [l[3:] for l in lines if l[0] in ("A", "M", "D") and l[1] == " "]

        summary = f"Branch: {branch or 'main'}\n"
        if not lines:
            summary += "Working tree clean. No uncommitted changes."
        else:
            summary += f"Changes: {len(modified)} modified, {len(untracked)} untracked, {len(staged)} staged."

        return {
            "success": True,
            "branch": branch or "main",
            "clean": len(lines) == 0,
            "modified": modified,
            "untracked": untracked,
            "staged": staged,
            "raw_status": status_out[:1000],
            "message": summary
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to check git status: {str(e)}"}


# ─────────────────────────────────────────────
# 10. Run Git Diff
# ─────────────────────────────────────────────
def run_git_diff(project_path: Optional[str] = None, file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    View uncommitted git diffs for a project or specific file.
    """
    target = project_path or os.getcwd()
    allowed, canonical, msg = is_path_allowed(target, for_write=False)
    if not allowed:
        return {"success": False, "error": msg}

    try:
        cmd = ["git", "diff"]
        if file_path:
            cmd.append(file_path.strip())

        diff_out = subprocess.check_output(
            cmd, cwd=canonical, text=True, timeout=8, stderr=subprocess.DEVNULL
        )

        lines = diff_out.splitlines()
        capped = "\n".join(lines[:200])
        is_capped = len(lines) > 200

        if not diff_out.strip():
            return {
                "success": True,
                "diff": "",
                "message": "No uncommitted git diff changes found."
            }

        return {
            "success": True,
            "lines_count": len(lines),
            "is_truncated": is_capped,
            "diff": capped,
            "message": f"Git Diff ({len(lines)} lines):\n\n```diff\n{capped}\n```"
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to run git diff: {str(e)}"}


# ─────────────────────────────────────────────
# 11. Run Development Tests
# ─────────────────────────────────────────────
def run_dev_tests(project_path: Optional[str] = None, test_command: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute unit tests in the project (e.g. pytest, npm test, python -m unittest).
    Medium risk action.
    """
    target = project_path or os.getcwd()
    allowed, canonical, msg = is_path_allowed(target, for_write=False)
    if not allowed:
        return {"success": False, "error": msg}

    cmd = test_command

    # Auto-detect if not provided
    if not cmd:
        if os.path.exists(os.path.join(canonical, "package.json")):
            cmd = "npm test"
        elif os.path.exists(os.path.join(canonical, "pytest.ini")) or os.path.exists(os.path.join(canonical, "tests")):
            cmd = "pytest"
        else:
            cmd = "python -m unittest"

    try:
        proc = subprocess.run(
            cmd,
            cwd=canonical,
            shell=True,
            capture_output=True,
            text=True,
            timeout=45
        )

        stdout_lines = proc.stdout.splitlines()
        stderr_lines = proc.stderr.splitlines()

        combined = "\n".join((stdout_lines + stderr_lines)[:150])
        is_passed = proc.returncode == 0

        status_str = "PASSED" if is_passed else "FAILED"
        message = f"Tests {status_str} (Exit Code: {proc.returncode})\nCommand: {cmd}\n\n{combined[:1500]}"

        return {
            "success": is_passed,
            "command": cmd,
            "exit_code": proc.returncode,
            "passed": is_passed,
            "output": combined,
            "message": message
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Test command '{cmd}' timed out after 45 seconds."}
    except Exception as e:
        return {"success": False, "error": f"Failed to run tests: {str(e)}"}


# ─────────────────────────────────────────────
# 12. Explain Code Error
# ─────────────────────────────────────────────
def explain_code_error(error_log: str, project_context: Optional[str] = None) -> Dict[str, Any]:
    """
    Diagnose a runtime traceback, compiler error, or syntax exception and explain the fix.
    """
    if not error_log or not error_log.strip():
        return {"success": False, "error": "Error log cannot be empty."}

    clean_err = error_log.strip()

    # Pattern recognition for common errors
    analysis = []
    
    # Python traceback detection
    py_match = re.search(r'File "([^"]+)", line (\d+), in (.*)', clean_err)
    if py_match:
        analysis.append(f"Failing File: {py_match.group(1)} (Line {py_match.group(2)}) in {py_match.group(3)}")

    # Python exception name
    py_exc = re.search(r'([A-Za-z]+Error|Exception): (.*)', clean_err)
    if py_exc:
        analysis.append(f"Exception: {py_exc.group(1)} - {py_exc.group(2)}")

    # Node.js / TypeScript error detection
    ts_match = re.search(r'([A-Za-z0-9_\-\./\\]+\.(?:ts|tsx|js|jsx)):(\d+):(\d+)', clean_err)
    if ts_match:
        analysis.append(f"Source Location: {ts_match.group(1)} (Line {ts_match.group(2)}, Col {ts_match.group(3)})")

    # Module not found
    if "ModuleNotFoundError" in clean_err or "Cannot find module" in clean_err:
        mod = re.search(r"(?:No module named|Cannot find module) ['\"]([^'\"]+)['\"]", clean_err)
        if mod:
            analysis.append(f"Diagnosis: Missing dependency '{mod.group(1)}'. Solution: Install with pip/npm.")

    summary = "\n".join(analysis) if analysis else "Traceback extracted for analysis."

    return {
        "success": True,
        "raw_error": clean_err[:1200],
        "analysis": analysis,
        "project_context": project_context,
        "message": f"Error Diagnostic:\n{summary}\n\nFull Log Captured."
    }
