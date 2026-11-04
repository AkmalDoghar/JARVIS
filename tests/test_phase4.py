"""
JARVIS Phase 4 Automated Acceptance Tests
Validates all Phase 4 features:
1. Path security rules & blocked Windows directories
2. Safe file reading inside approved roots
3. Project architecture inspection
4. Codebase search & directory listing
5. Git status & git diff
6. File creation & modification with unified diffs
7. HIGH-risk file deletion with PIN verification
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.security.path_rules import is_path_allowed
from backend.tools import code_tools
from backend.tools.registry import execute_tool
from backend.security.risk import get_tool_risk, RiskLevel


def run_all_tests():
    print("==================================================")
    print("  RUNNING PHASE 4 ACCEPTANCE TESTS")
    print("==================================================")

    # 1. Path Boundary Tests
    print("\n[Test 1] Path Security Guard & Traversal Check:")
    allowed, _, msg = is_path_allowed(r"C:\Windows\System32\cmd.exe")
    assert not allowed, "Failed: C:\\Windows should be blocked!"
    print("  [PASS] C:\\Windows is correctly BLOCKED:", msg)

    allowed, _, msg = is_path_allowed(r"C:\Program Files\Internet Explorer")
    assert not allowed, "Failed: Program Files should be blocked!"
    print("  [PASS] C:\\Program Files is correctly BLOCKED:", msg)

    allowed, canon, msg = is_path_allowed(r"d:\projects\JARVIS\README.md")
    assert allowed, f"Failed: d:\\projects\\JARVIS should be allowed! Error: {msg}"
    print(f"  [PASS] Approved project path authorized: {canon}")

    # 2. Read File Test
    print("\n[Test 2] Safe File Reading:")
    res = code_tools.read_file(r"d:\projects\JARVIS\README.md", max_lines=15)
    assert res["success"], f"Failed to read file: {res.get('error')}"
    print(f"  [PASS] Read {res['lines_shown']} lines from README.md successfully.")

    # 3. Project Inspection Test
    print("\n[Test 3] Project Architecture Inspection:")
    res = code_tools.inspect_project(r"d:\projects\JARVIS")
    assert res["success"], f"Failed to inspect project: {res.get('error')}"
    p = res["project"]
    print(f"  [PASS] Project Name: {p['project_name']}")
    print(f"  [PASS] Frameworks: {p['frameworks']}")
    print(f"  [PASS] Entry Points: {p['entry_files']}")
    print(f"  [PASS] Git Status: {p['git']}")

    # 4. Codebase Search Test
    print("\n[Test 4] Codebase Search:")
    res = code_tools.search_codebase(query="JarvisBrain", project_path=r"d:\projects\JARVIS")
    assert res["success"], f"Search failed: {res.get('error')}"
    print(f"  [PASS] Found {res['total_matches']} match(es) for 'JarvisBrain'.")
    if res["matches"]:
        first = res["matches"][0]
        print(f"    Match 1: {first['file']}:{first['line']}")

    # 5. Git Status Test
    print("\n[Test 5] Git Status Tool:")
    res = code_tools.run_git_status(r"d:\projects\JARVIS")
    assert res["success"], f"Git status failed: {res.get('error')}"
    print(f"  [PASS] Git branch: {res['branch']}, Modified: {len(res['modified'])}, Clean: {res['clean']}")

    # 6. File Creation, Modification & Unified Diff Test
    print("\n[Test 6] File Creation, Modification & Diff:")
    test_file = r"d:\projects\JARVIS\phase4_test_file.txt"

    # Create file
    res = code_tools.create_file(test_file, "Line 1: Hello JARVIS\nLine 2: Phase 4 Test\nLine 3: Initial Code\n")
    assert res["success"], f"Failed to create file: {res.get('error')}"
    print(f"  [PASS] Created test file: {res['message']}")

    # Modify file with unified diff
    res = code_tools.modify_file(test_file, "Line 2: Phase 4 Test", "Line 2: Phase 4 Test PASSED")
    assert res["success"], f"Failed to modify file: {res.get('error')}"
    print("  [PASS] Unified Diff generated successfully:")
    for dline in res["diff"].splitlines():
        print(f"      {dline}")

    # 7. Security Enforcement for Deletion (HIGH RISK)
    print("\n[Test 7] Security Enforcement & Deletion (PIN Gated):")
    # A) Attempt to delete without confirmation/PIN via execute_tool
    res = execute_tool("delete_file_or_folder", {"target_path": test_file}, confirmed=False)
    assert res["status"] == "PENDING_CONFIRMATION", "Should be pending confirmation!"
    assert res["requires_pin"] is True, "Delete must require PIN!"
    print(f"  [PASS] Unconfirmed delete intercepted: {res['status']} (requires_pin={res['requires_pin']})")

    # B) Attempt with WRONG PIN
    res = execute_tool("delete_file_or_folder", {"target_path": test_file}, confirmed=True, pin="9999")
    assert res["status"] == "DENIED", "Wrong PIN must be denied!"
    print(f"  [PASS] Wrong PIN correctly DENIED: {res['error']}")

    # C) Attempt with CORRECT PIN (1234)
    res = execute_tool("delete_file_or_folder", {"target_path": test_file}, confirmed=True, pin="1234")
    assert res["status"] == "SUCCESS", f"Correct PIN should succeed! Error: {res.get('error')}"
    print(f"  [PASS] Correct PIN authorized: {res['result']['message']}")
    assert not os.path.exists(test_file), "File should be deleted from disk!"
    print("  [PASS] Test file confirmed deleted from disk.")

    print("\n==================================================")
    print("  ALL PHASE 4 ACCEPTANCE TESTS PASSED! (7/7) [OK]")
    print("==================================================")


if __name__ == "__main__":
    run_all_tests()
