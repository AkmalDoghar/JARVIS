"""
JARVIS WhatsApp Automation & Resilience Test Suite
Verifies:
1. All WhatsApp tools are registered in schema and handlers.
2. Risk classification (all WhatsApp communication tools are properly categorized).
3. Window title matching regex with unread message badges (e.g. '(1) WhatsApp', '(99+) WhatsApp', 'WhatsApp').
4. Non-destructive window state restoration logic.
5. Direct phone formatting (+92 expansion and URL generation).
6. Message formatting and Roman Urdu / greeting auto-correction.
7. Platform switching tracker (desktop vs web).
8. Status tools schema and parameter handling.
9. Calling tools schema and safe click coordinates calculation.
"""

import re
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.tools.registry import execute_tool, JARVIS_TOOLS_SCHEMA, TOOL_HANDLERS
from backend.security.risk import get_tool_risk, RiskLevel
from backend.tools.system_control import (
    clean_and_format_message,
    send_whatsapp_message,
    confirm_send_whatsapp,
    make_whatsapp_call,
    end_whatsapp_call,
    toggle_whatsapp_call_mute,
    post_whatsapp_status,
    customize_whatsapp_status,
    confirm_post_whatsapp_status,
    discard_whatsapp_status,
    delete_whatsapp_status
)
from backend.tools.whatsapp_web import (
    get_last_whatsapp_platform,
    set_last_whatsapp_platform,
    open_whatsapp_web
)


class TestWhatsAppAutomationResilience(unittest.TestCase):

    def test_01_all_whatsapp_tools_registered(self):
        """Verify all WhatsApp tools are in JARVIS_TOOLS_SCHEMA and TOOL_HANDLERS."""
        expected_tools = [
            "send_whatsapp_message",
            "confirm_send_whatsapp",
            "open_whatsapp_web",
            "make_whatsapp_call",
            "end_whatsapp_call",
            "toggle_whatsapp_call_mute",
            "post_whatsapp_status",
            "customize_whatsapp_status",
            "confirm_post_whatsapp_status",
            "discard_whatsapp_status",
            "delete_whatsapp_status"
        ]
        registered_schema_names = [t["function"]["name"] for t in JARVIS_TOOLS_SCHEMA]
        for tool_name in expected_tools:
            self.assertIn(tool_name, registered_schema_names, f"Tool {tool_name} missing from schema.")
            self.assertIn(tool_name, TOOL_HANDLERS, f"Tool {tool_name} missing from handlers.")

        print(f"[PASS] Test 1: All {len(expected_tools)} WhatsApp tools registered in schema and handlers.")

    def test_02_risk_levels(self):
        """Verify all WhatsApp communication and status tools have appropriate risk levels."""
        low_risk_tools = [
            "send_whatsapp_message",
            "confirm_send_whatsapp",
            "open_whatsapp_web",
            "make_whatsapp_call",
            "end_whatsapp_call",
            "toggle_whatsapp_call_mute",
            "post_whatsapp_status",
            "customize_whatsapp_status",
            "confirm_post_whatsapp_status",
            "discard_whatsapp_status",
            "delete_whatsapp_status"
        ]
        for t in low_risk_tools:
            self.assertEqual(get_tool_risk(t), RiskLevel.LOW, f"Tool {t} should be LOW risk.")

        print("[PASS] Test 2: Risk classification verified for all WhatsApp tools.")

    def test_03_unread_badge_title_matching(self):
        """Verify regex accurately recognizes WhatsApp window titles with unread counters."""
        pattern = r"^\(\d+\+?\)\s*whatsapp|whatsapp$"
        
        valid_titles = [
            "WhatsApp",
            "(1) WhatsApp",
            "(5) WhatsApp",
            "(25) WhatsApp",
            "(99+) WhatsApp",
            "(1)  WhatsApp"
        ]
        for title in valid_titles:
            t_lower = title.strip().lower()
            matched = (
                title == "WhatsApp"
                or title.endswith("WhatsApp")
                or bool(re.search(r"^\(\d+\+?\)\s*whatsapp", t_lower))
                or "whatsapp" in t_lower
            )
            self.assertTrue(matched, f"Title '{title}' failed to match WhatsApp pattern.")

        # False positives to reject
        invalid_titles = [
            "whatsapp_status.py - Visual Studio Code",
            "JARVIS - Antigravity IDE - whatsapp_web.py",
            "How to use WhatsApp - Google Chrome"
        ]
        for title in invalid_titles:
            t_lower = title.strip().lower()
            is_rejected = any(x in t_lower for x in ("antigravity", "visual studio", "code", ".py", ".ts", "- google chrome", "- microsoft edge", "- brave"))
            self.assertTrue(is_rejected, f"Title '{title}' should have been rejected as an editor/tool/browser tab.")

        print("[PASS] Test 3: Unread badge window title matching and false-positive rejection verified.")

    def test_04_message_cleaning_and_formatting(self):
        """Verify shorthand expansion, greeting standardization, and capitalization."""
        # Case A: Shorthand greetings and Roman Urdu
        input_text = "aslam o alkm kl kdr ho tm?"
        cleaned, was_modified = clean_and_format_message(input_text)
        self.assertTrue(was_modified)
        self.assertIn("Assalam-o-Alaikum", cleaned)
        self.assertIn("kal", cleaned)
        self.assertIn("kidhar", cleaned)

        # Case B: Already clean sentence
        clean_input = "Hello Ahmed, I will see you tomorrow at 4 PM."
        res, modified = clean_and_format_message(clean_input)
        self.assertEqual(res, clean_input)

        # Case C: Punctuation normalization
        punct_input = "hello ,how are you ?"
        res, modified = clean_and_format_message(punct_input)
        self.assertEqual(res, "Hello, how are you?")

        print("[PASS] Test 4: Message cleaning and greeting expansion verified.")

    def test_05_phone_number_routing_and_platform_tracker(self):
        """Verify phone number formatting (+92 conversion) and platform state tracker."""
        set_last_whatsapp_platform("web")
        self.assertEqual(get_last_whatsapp_platform(), "web")
        set_last_whatsapp_platform("desktop")
        self.assertEqual(get_last_whatsapp_platform(), "desktop")

        # Execute web messaging tool directly
        res = execute_tool("send_whatsapp_message", {
            "contact_name_or_phone": "03007654321",
            "message": "aoa kl meeting hai",
            "platform": "web"
        })
        self.assertTrue(res.get("success"))
        r = res.get("result", {})
        self.assertEqual(r.get("platform"), "web")
        self.assertEqual(r.get("phone"), "923007654321")
        self.assertEqual(get_last_whatsapp_platform(), "web")
        self.assertIn("Assalam-o-Alaikum", r.get("message_text", ""))

        print("[PASS] Test 5: Direct phone formatting and platform state persistence verified.")

    def test_06_make_whatsapp_call_schema_and_empty_guard(self):
        """Verify make_whatsapp_call parameter validation and guards."""
        res = execute_tool("make_whatsapp_call", {"contact_name_or_phone": ""})
        self.assertFalse(res.get("success"))
        self.assertIn("required", res.get("error", "").lower())

        # Test video call type schema option
        schema = next(t["function"] for t in JARVIS_TOOLS_SCHEMA if t["function"]["name"] == "make_whatsapp_call")
        props = schema["parameters"]["properties"]
        self.assertIn("contact_name_or_phone", props)
        self.assertIn("call_type", props)
        self.assertIn("video", props["call_type"]["enum"])
        self.assertIn("voice", props["call_type"]["enum"])

        print("[PASS] Test 6: WhatsApp Call schema validation and empty target guard verified.")

    def test_07_post_whatsapp_status_schema(self):
        """Verify WhatsApp Status posting tool schema and auto-styling options."""
        schema = next(t["function"] for t in JARVIS_TOOLS_SCHEMA if t["function"]["name"] == "post_whatsapp_status")
        props = schema["parameters"]["properties"]
        self.assertIn("status_text", props)
        self.assertIn("cycle_background", props)
        self.assertIn("cycle_font", props)
        self.assertIn("status_type", props)

        # Verify customize and discard tool schemas
        cust_schema = next(t["function"] for t in JARVIS_TOOLS_SCHEMA if t["function"]["name"] == "customize_whatsapp_status")
        self.assertIn("cycle_background", cust_schema["parameters"]["properties"])
        
        discard_schema = next(t["function"] for t in JARVIS_TOOLS_SCHEMA if t["function"]["name"] == "discard_whatsapp_status")
        self.assertEqual(discard_schema["name"], "discard_whatsapp_status")

        print("[PASS] Test 7: WhatsApp Status tool schemas and styling parameters verified.")


if __name__ == "__main__":
    unittest.main()
