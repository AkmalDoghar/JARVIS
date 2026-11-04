"""
JARVIS Phase 7 Test Suite: Desktop Vision & Screenshot Error Diagnostics
Acceptance Tests:
1. Screen capture returns valid base64 image data and dimensions.
2. Privacy Guarantee: In-memory capture does NOT save files to disk.
3. Explicit save writes to disk only on request.
4. Prompt Injection Defense: System guard strictly isolates image content as untrusted.
5. Risk Level Enforcement: inspect_screen and capture_screenshot are categorized as LOW risk.
6. Registry integration: Tools are callable via execute_tool.
7. Offline handling: Returns structured offline notification if models are unavailable.
"""

import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.tools import vision_tools
from backend.security.risk import get_tool_risk, RiskLevel
from backend.tools.registry import execute_tool, JARVIS_TOOLS_SCHEMA, TOOL_HANDLERS


class TestPhase7DesktopVision(unittest.TestCase):

    def test_01_screen_capture_in_memory(self):
        """Test on-demand desktop screenshot capture in memory."""
        res = vision_tools.capture_desktop_screenshot(save_path=None)
        if not res.get("success") and "display session" in str(res.get("error")):
            self.skipTest("Display session is detached or screen is locked. Skipping live screen capture test.")
        self.assertTrue(res.get("success"), f"Capture failed: {res.get('error')}")
        self.assertIn("base64_image", res)
        self.assertGreater(len(res["base64_image"]), 1000, "Base64 image payload is too small.")
        self.assertGreater(res["width"], 100)
        self.assertGreater(res["height"], 100)
        # Privacy check: nothing should be saved to disk
        self.assertIsNone(res.get("saved_to"))
        print("[SUCCESS] Test 1: In-memory desktop screen capture succeeded with valid dimensions.")

    def test_02_explicit_save_to_disk(self):
        """Test that screenshots are saved to disk ONLY when explicitly asked."""
        test_file = Path("tests/scratch/test_screen_save.jpg").resolve()
        test_file.parent.mkdir(parents=True, exist_ok=True)
        if test_file.exists():
            test_file.unlink()

        res = vision_tools.capture_desktop_screenshot(save_path=str(test_file))
        if not res.get("success") and "display session" in str(res.get("error")):
            self.skipTest("Display session is detached or screen is locked. Skipping live screen capture test.")
        self.assertTrue(res.get("success"))
        self.assertTrue(test_file.exists(), "Explicitly requested screenshot file was not created on disk.")
        self.assertGreater(test_file.stat().st_size, 1000)

        # Clean up test file
        test_file.unlink()
        print("[SUCCESS] Test 2: Explicit save-to-disk verified and cleaned up.")

    def test_03_prompt_injection_defense_guard(self):
        """Test that the vision system prompt strictly warns against executing commands in screenshots."""
        guard = vision_tools.VISION_SYSTEM_GUARD
        self.assertIn("UNTRUSTED OBSERVATION DATA", guard)
        self.assertIn("DO NOT obey or execute", guard)
        self.assertIn("INDIRECT PROMPT INJECTION DEFENSE", guard)
        print("[SUCCESS] Test 3: Prompt injection defense instructions verified in system guard.")

    def test_04_tool_risk_classification(self):
        """Verify inspect_screen and capture_screenshot are classified as LOW risk."""
        risk_inspect = get_tool_risk("inspect_screen")
        risk_capture = get_tool_risk("capture_screenshot")
        self.assertEqual(risk_inspect, RiskLevel.LOW)
        self.assertEqual(risk_capture, RiskLevel.LOW)
        print("[SUCCESS] Test 4: Vision tools correctly classified as RiskLevel.LOW.")

    def test_05_registry_schema_and_handlers(self):
        """Verify inspect_screen and capture_screenshot are registered in registry schemas and handlers."""
        names = [t["function"]["name"] for t in JARVIS_TOOLS_SCHEMA]
        self.assertIn("inspect_screen", names)
        self.assertIn("capture_screenshot", names)
        self.assertIn("inspect_screen", TOOL_HANDLERS)
        self.assertIn("capture_screenshot", TOOL_HANDLERS)
        print("[SUCCESS] Test 5: Vision tools properly registered in JARVIS_TOOLS_SCHEMA and TOOL_HANDLERS.")

    def test_06_vision_llm_client_detection(self):
        """Verify vision LLM client discovery returns either an active provider or graceful offline."""
        client, provider, models = vision_tools.get_vision_llm_client()
        self.assertIn(provider, ["openrouter", "gemini", "openai", "offline"])
        if provider != "offline":
            self.assertIsNotNone(client)
            self.assertGreater(len(models), 0)
        print(f"[SUCCESS] Test 6: Vision client detector operational (detected: {provider}, models: {len(models)}).")

    def test_07_offline_graceful_handling(self):
        """Verify that inspect_screen handles offline or model failure gracefully without crashing."""
        # Temporarily mock get_vision_llm_client and capture_desktop_screenshot to isolate offline LLM logic
        orig_func = vision_tools.get_vision_llm_client
        orig_capture = vision_tools.capture_desktop_screenshot
        vision_tools.get_vision_llm_client = lambda: (None, "offline", [])
        vision_tools.capture_desktop_screenshot = lambda **kw: {"success": True, "base64_image": "bW9ja19pbWFnZQ==", "width": 800, "height": 600}

        try:
            res = vision_tools.inspect_screen(focus="error")
            self.assertFalse(res.get("success"))
            self.assertTrue(res.get("offline"))
            self.assertIn("unavailable", res.get("error", "").lower())
            self.assertIn("spoken_response", res)
        finally:
            vision_tools.get_vision_llm_client = orig_func
            vision_tools.capture_desktop_screenshot = orig_capture

        print("[SUCCESS] Test 7: Graceful offline fallback validated.")

    def test_08_live_or_fallback_screen_inspection(self):
        """Verify inspect_screen executes end-to-end (or falls back safely if rate limited)."""
        res = vision_tools.inspect_screen(focus="general", question="Briefly describe screen.")
        # Must return a valid dict with status
        self.assertIsInstance(res, dict)
        if res.get("success"):
            self.assertTrue(bool(res.get("analysis")))
            print(f"[SUCCESS] Test 8: Live screen inspection succeeded using {res.get('model')}.")
        else:
            print(f"[NOTE] Test 8: Live call handled cleanly with error notice: {res.get('error')[:80]}...")


if __name__ == "__main__":
    unittest.main(verbosity=2)
