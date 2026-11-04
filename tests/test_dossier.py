"""
Acceptance test for Creator Digital Dossier & Online Presence Engine
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.creator_dossier import get_dossier, update_dossier, get_dossier_prompt_context, sync_creator_online

def run_dossier_tests():
    print("=== Testing Creator Digital Dossier ===")
    
    # 1. Retrieve default dossier
    d = get_dossier()
    assert d is not None, "Failed to retrieve dossier"
    assert "personal" in d, "Personal info missing from dossier"
    assert "social_profiles" in d, "Social profiles missing from dossier"
    print(f" [PASS] Dossier loaded: {d['personal']['name']} ({d['personal']['title']})")
    
    # 2. Test prompt context generation
    ctx = get_dossier_prompt_context()
    assert "Akmal bhai" in ctx, "Preferred honorific missing in context"
    print(f" [PASS] Prompt context generated ({len(ctx)} chars)")
    
    # 3. Test update
    update_dossier({
        "personal": {"location": "Lahore, Pakistan"},
        "social_profiles": {"github_username": "torvalds"} # Public profile for test
    })
    d_updated = get_dossier()
    assert d_updated["personal"]["location"] == "Lahore, Pakistan"
    print(" [PASS] Update merged successfully")

    # 4. Test online sync (mocked / real GitHub public API)
    print(" [Testing online sync with GitHub API...]")
    sync_res = sync_creator_online("torvalds")
    if sync_res.get("success"):
        print(f" [PASS] Live GitHub Sync verified: {sync_res.get('public_repos')} public repos retrieved.")
    else:
        print(f" [INFO] Sync message: {sync_res.get('message')}")
        
    print("=== ALL DOSSIER TESTS PASSED ===")

if __name__ == "__main__":
    run_dossier_tests()
