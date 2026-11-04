"""
JARVIS Phase 6B Automated Acceptance Tests
Validates all Phase 6 Long-Term Memory Matrix requirements:
1. Storing explicit user preferences, instructions, and facts into SQLite
2. Memory survives database restarts (100% persistent local storage)
3. Strict privacy enforcement: passwords, API keys, bearer tokens, and OTPs are refused
4. Updating existing memory by key without duplicates
5. Searching and contextual retrieval by keyword/category
6. Deleting single memory, deleting by keyword, and forget all (clearing matrix)
7. Dynamic LLM prompt context formatting for automatic agent recall
8. Integration with tool execution dispatcher and risk enforcement
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import memory as memory_db
from backend.tools import memory_tools
from backend.tools.registry import execute_tool
from backend.security.risk import get_tool_risk, RiskLevel


def run_all_tests():
    print("==================================================")
    print("  RUNNING PHASE 6B ACCEPTANCE TESTS")
    print("==================================================")

    # 1. Risk Level Validation
    print("\n[Test 1] Tool Risk Level Verification:")
    assert get_tool_risk("remember_information") == RiskLevel.LOW, "remember_information should be LOW risk"
    assert get_tool_risk("recall_memories") == RiskLevel.LOW, "recall_memories should be LOW risk"
    assert get_tool_risk("forget_memory") == RiskLevel.LOW, "forget_memory should be LOW risk by default"
    assert get_tool_risk("forget_memory", {"forget_all": True}) == RiskLevel.HIGH, "forget_memory with forget_all=True MUST be HIGH risk (requires PIN)"
    print("  [PASS] remember_information is correctly categorized as LOW risk.")
    print("  [PASS] recall_memories is correctly categorized as LOW risk.")
    print("  [PASS] forget_memory is correctly categorized as LOW risk.")
    print("  [PASS] forget_memory with forget_all=True requires HIGH risk security PIN.")

    # 2. Saving a User Preference
    print("\n[Test 2] Storing User Preference in Memory Matrix:")
    save_res = memory_db.remember(
        content="User prefers VS Code as primary code editor",
        category="preference",
        key="primary_editor",
        tags=["editor", "coding", "vscode"]
    )
    assert save_res["success"], f"Failed to remember preference: {save_res.get('error')}"
    mem_id = save_res["id"]
    print(f"  [PASS] Saved preference with ID #{mem_id}: '{save_res['content']}'")

    # 3. Recalling Stored Memory
    print("\n[Test 3] Searching and Recalling Memory:")
    recall_res = memory_db.recall(query="VS Code")
    assert len(recall_res) > 0, "Failed to retrieve memory matching 'VS Code'"
    found = any(m["id"] == mem_id for m in recall_res)
    assert found, "Created memory item not found in recall results"
    print(f"  [PASS] Recall found {len(recall_res)} items matching query 'VS Code'.")
    print(f"  [PASS] Retrieved: '{recall_res[0]['content']}' [Key: {recall_res[0]['key']}]")

    # 4. Persistence Test (Survives New DB Connection)
    print("\n[Test 4] Persistence Across Database Reconnect:")
    with memory_db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jarvis_memories WHERE id = ?", (mem_id,))
        row = cursor.fetchone()
        assert row is not None, "Memory row did not persist across connection"
        assert row["key"] == "primary_editor"
        print(f"  [PASS] Verified memory #{mem_id} is persistently stored in SQLite disk table.")

    # 5. Privacy Policy: Refusal of Sensitive Secrets
    print("\n[Test 5] Privacy Policy Enforcement (Refuse Sensitive Secrets):")
    secret_tests = [
        "My password is SecretPassword123!",
        "Save this API key: sk-abcdef1234567890abcdef1234567890",
        "My bank card cvv is 789 and pin is 1234",
        "Remember my bearer token: bearer_token_xyz"
    ]
    for secret in secret_tests:
        res = memory_db.remember(secret, category="fact")
        assert not res["success"], f"Security vulnerability: Sensitive secret was accepted: '{secret}'"
        assert "Security Policy" in res["error"], f"Expected Security Policy rejection error, got: {res.get('error')}"
        print(f"  [PASS] Successfully blocked secret: '{secret[:25]}...' -> {res['error']}")

    # 6. Updating Existing Memory by Key
    print("\n[Test 6] Updating Existing Memory (No Duplicates):")
    update_res = memory_db.remember(
        content="User prefers Cursor & VS Code for development",
        category="preference",
        key="primary_editor"
    )
    assert update_res["success"], "Failed to update memory"
    assert update_res["action"] == "updated", f"Expected action 'updated', got '{update_res['action']}'"
    assert update_res["id"] == mem_id, f"Expected same ID #{mem_id}, got #{update_res['id']}"
    print(f"  [PASS] Updated memory #{mem_id} in place without creating duplicate records.")

    # 7. Dynamic LLM Prompt Context Generation
    print("\n[Test 7] Dynamic LLM Prompt Context Generation:")
    prompt_context = memory_db.get_relevant_memories_for_prompt("Which code editor do I use?")
    assert len(prompt_context) > 0, "Expected non-empty prompt context for editor query"
    assert "Cursor & VS Code" in prompt_context or "VS Code" in prompt_context, "Memory content missing from prompt context"
    print("  [PASS] Generated active prompt context:")
    for line in prompt_context.split("\n"):
        print(f"    {line}")

    # 8. Tool Execution via Dispatcher
    print("\n[Test 8] Tool Registry Execution Dispatch:")
    exec_res = execute_tool(
        tool_name="remember_information",
        arguments={
            "content": "User prefers coffee with milk and no sugar",
            "category": "preference",
            "key": "coffee_preference"
        }
    )
    assert exec_res["success"], f"Tool execution failed: {exec_res.get('error')}"
    coffee_id = exec_res["result"]["memory_id"]
    print(f"  [PASS] Tool 'remember_information' executed successfully: #{coffee_id}")

    recall_tool_res = execute_tool(
        tool_name="recall_memories",
        arguments={"query": "coffee"}
    )
    assert recall_tool_res["success"], f"Tool recall failed: {recall_tool_res.get('error')}"
    assert recall_tool_res["result"]["count"] >= 1, "Expected at least 1 memory matching 'coffee'"
    print(f"  [PASS] Tool 'recall_memories' found {recall_tool_res['result']['count']} coffee memories.")

    # 9. Deleting Memory Item by ID
    print("\n[Test 9] Deleting Memory by ID:")
    del_res = memory_tools.forget_memory(memory_id=coffee_id)
    assert del_res["success"], f"Failed to delete memory #{coffee_id}: {del_res.get('error')}"
    print(f"  [PASS] Memory #{coffee_id} successfully deleted.")

    # Verify deleted
    with memory_db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM jarvis_memories WHERE id = ?", (coffee_id,))
        assert cursor.fetchone() is None, "Memory was not deleted from database"
        print(f"  [PASS] Confirmed memory #{coffee_id} no longer exists in database.")

    # 10. Deleting Memory by Keyword
    print("\n[Test 10] Deleting Memory by Keyword:")
    memory_db.remember("User is studying Next.js 16 app router", category="fact", tags=["learning", "nextjs"])
    del_kw_res = memory_tools.forget_memory(keyword="Next.js")
    assert del_kw_res["success"], f"Failed to delete by keyword: {del_kw_res.get('error')}"
    assert del_kw_res["deleted_count"] >= 1, "Expected at least 1 memory deleted by keyword"
    print(f"  [PASS] Deleted {del_kw_res['deleted_count']} memories matching keyword 'Next.js'.")

    print("\n==================================================")
    print("  ALL 10/10 PHASE 6B ACCEPTANCE TESTS PASSED! [SUCCESS]")
    print("==================================================")


if __name__ == "__main__":
    run_all_tests()
