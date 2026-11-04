"""
JARVIS WhatsApp Web Test Suite
Verifies:
1. Tool schema registration for send_whatsapp_message (with platform option) and open_whatsapp_web.
2. Tool execution via registry.
3. Proper URL generation and parameter handling for web messaging.
4. Risk classification (RiskLevel.LOW).
5. State tracking between draft and confirm.
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.tools.registry import execute_tool, JARVIS_TOOLS_SCHEMA, TOOL_HANDLERS
from backend.security.risk import get_tool_risk, RiskLevel
from backend.tools.whatsapp_web import (
    get_last_whatsapp_platform,
    set_last_whatsapp_platform,
    find_whatsapp_web_window
)


class TestWhatsAppWebIntegration(unittest.TestCase):

    def test_01_tool_registration_and_schema(self):
        """Verify open_whatsapp_web and send_whatsapp_message are registered in schema and handlers."""
        tool_names = [t["function"]["name"] for t in JARVIS_TOOLS_SCHEMA]
        self.assertIn("open_whatsapp_web", tool_names)
        self.assertIn("send_whatsapp_message", tool_names)
        self.assertIn("confirm_send_whatsapp", tool_names)

        # Verify platform property exists in send_whatsapp_message schema
        schema = next(t["function"] for t in JARVIS_TOOLS_SCHEMA if t["function"]["name"] == "send_whatsapp_message")
        self.assertIn("platform", schema["parameters"]["properties"])
        self.assertIn("web", schema["parameters"]["properties"]["platform"]["enum"])

        # Verify handlers exist
        self.assertIn("open_whatsapp_web", TOOL_HANDLERS)
        self.assertIn("send_whatsapp_message", TOOL_HANDLERS)
        self.assertIn("confirm_send_whatsapp", TOOL_HANDLERS)
        print("[SUCCESS] Test 1: WhatsApp Web tools registered in schema and handlers.")

    def test_02_risk_classification(self):
        """Verify WhatsApp Web tools are marked as LOW risk."""
        self.assertEqual(get_tool_risk("open_whatsapp_web"), RiskLevel.LOW)
        self.assertEqual(get_tool_risk("send_whatsapp_message"), RiskLevel.LOW)
        self.assertEqual(get_tool_risk("confirm_send_whatsapp"), RiskLevel.LOW)
        print("[SUCCESS] Test 2: Risk levels verified as LOW.")

    def test_03_send_whatsapp_web_message_direct_phone(self):
        """Test web messaging with direct phone number creates valid web link and sets platform."""
        res = execute_tool("send_whatsapp_message", {
            "contact_name_or_phone": "03001234567",
            "message": "aslam o alkm kl milte h",
            "platform": "web"
        })
        self.assertTrue(res.get("success"))
        tool_res = res.get("result", {})
        self.assertEqual(tool_res.get("platform"), "web")
        self.assertEqual(tool_res.get("phone"), "923001234567")
        self.assertIn("web.whatsapp.com/send", tool_res.get("web_url", ""))
        self.assertEqual(get_last_whatsapp_platform(), "web")
        # Verify auto-correction
        self.assertTrue(tool_res.get("was_formatted"))
        print("[SUCCESS] Test 3: WhatsApp Web message created with formatted text and web URL.")

    def test_04_explicit_web_keyword_in_target(self):
        """Test that adding '(web)' or 'web' to target name automatically forces web platform."""
        res = execute_tool("send_whatsapp_message", {
            "contact_name_or_phone": "03009876543 (web)",
            "message": "Hello from Jarvis"
        })
        self.assertTrue(res.get("success"))
        tool_res = res.get("result", {})
        self.assertEqual(tool_res.get("platform"), "web")
        self.assertEqual(get_last_whatsapp_platform(), "web")
        print("[SUCCESS] Test 4: Explicit web keyword in target routed directly to web platform.")

    def test_05_platform_state_tracking(self):
        """Test platform state tracker."""
        set_last_whatsapp_platform("web")
        self.assertEqual(get_last_whatsapp_platform(), "web")
        set_last_whatsapp_platform("desktop")
        self.assertEqual(get_last_whatsapp_platform(), "desktop")
        print("[SUCCESS] Test 5: Platform state tracker works as expected.")


if __name__ == "__main__":
    unittest.main()
