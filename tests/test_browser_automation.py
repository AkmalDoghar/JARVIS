"""
Unit test suite for JARVIS Browser Automation, YouTube Auto-Play, Website Analysis,
and Google Multi-Account / Chrome Profile Switcher.
"""

import unittest
from unittest import mock
import sys
import os

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.tools.web_tools import play_youtube_video, analyze_website
from backend.tools.system_control import get_chrome_profiles, list_google_accounts, open_chrome_profile
from backend.tools.chrome_bookmarks import (
    get_chrome_bookmarks,
    list_chrome_bookmarks,
    search_chrome_history,
    search_chrome_history_tool,
    resolve_smart_url,
    open_smart_website
)
from backend.tools.registry import JARVIS_TOOLS_SCHEMA, TOOL_HANDLERS
from backend.security.risk import TOOL_RISK_MAP, RiskLevel
from backend.agent.brain import (
    parse_browser_search,
    get_spoken_acknowledgment,
    parse_bookmarks_query,
    parse_history_query,
    parse_smart_portal_open
)


class TestBrowserAutomation(unittest.TestCase):

    def test_01_tool_registration_and_risk(self):
        """Verify all new browser tools are properly registered with RiskLevel.LOW."""
        expected_tools = ["play_youtube_video", "analyze_website", "list_google_accounts"]
        
        tool_names = [t["function"]["name"] for t in JARVIS_TOOLS_SCHEMA if "function" in t]
        for name in expected_tools:
            self.assertIn(name, tool_names, f"Tool '{name}' not found in JARVIS_TOOLS_SCHEMA registry schema.")
            self.assertIn(name, TOOL_HANDLERS, f"Tool '{name}' not found in TOOL_HANDLERS mapping.")
            self.assertEqual(TOOL_RISK_MAP.get(name), RiskLevel.LOW, f"Tool '{name}' must have RiskLevel.LOW.")

    def test_02_google_accounts_listing(self):
        """Verify get_chrome_profiles and list_google_accounts detect the 4 user accounts."""
        profs = get_chrome_profiles()
        self.assertGreaterEqual(len(profs), 4, f"Expected at least 4 profiles, found {len(profs)}.")
        
        # Verify account numbering 1 through 4
        acc_nums = [p.get("account_number") for p in profs]
        self.assertIn(1, acc_nums)
        self.assertIn(2, acc_nums)
        self.assertIn(3, acc_nums)
        self.assertIn(4, acc_nums)
        
        # Verify specific emails present
        emails = [p.get("email", "").lower() for p in profs]
        self.assertTrue(any("ranaakmal" in e for e in emails), "ranaakmalr703 email not found in profiles.")
        self.assertTrue(any("84pakarmy" in e for e in emails), "84pakarmy email not found in profiles.")
        self.assertTrue(any("vu.edu.pk" in e for e in emails), "vu.edu.pk email not found in profiles.")
        self.assertTrue(any("dev42" in e for e in emails), "m.akmal.dev42 email not found in profiles.")
        
        # Verify list_google_accounts returns formatted message
        res = list_google_accounts()
        self.assertTrue(res.get("success"))
        self.assertIn("Google Accounts", res.get("message", ""))
        self.assertEqual(res.get("count"), len(profs))

    @mock.patch("subprocess.Popen")
    def test_03_chrome_profile_matching(self, mock_popen):
        """Verify rich profile matching by number, ordinal, and keywords."""
        mock_popen.return_value = mock.MagicMock()
        profs = get_chrome_profiles()
        
        # Test Account 1
        for q in ["1", "pehla", "rana akmal", "default"]:
            m = open_chrome_profile(q)
            # Executable check or match check
            if not m.get("success") and "executable not found" in m.get("error", "").lower():
                pass
            else:
                self.assertEqual(m.get("account_number"), 1, f"Query '{q}' failed to match Account 1.")

        # Test Account 2
        for q in ["2", "dosra", "84pakarmy", "m akmal"]:
            m = open_chrome_profile(q)
            if not m.get("success") and "executable not found" in m.get("error", "").lower():
                pass
            else:
                self.assertEqual(m.get("account_number"), 2, f"Query '{q}' failed to match Account 2.")

        # Test Account 3
        for q in ["3", "teesra", "vu", "lms", "virtual university"]:
            m = open_chrome_profile(q)
            if not m.get("success") and "executable not found" in m.get("error", "").lower():
                pass
            else:
                self.assertEqual(m.get("account_number"), 3, f"Query '{q}' failed to match Account 3.")

        # Test Account 4
        for q in ["4", "chautha", "developer", "nextjs"]:
            m = open_chrome_profile(q)
            if not m.get("success") and "executable not found" in m.get("error", "").lower():
                pass
            else:
                self.assertEqual(m.get("account_number"), 4, f"Query '{q}' failed to match Account 4.")

    def test_04_youtube_auto_play_resolution(self):
        """Verify play_youtube_video resolves direct watch?v= URL with correct video title."""
        res = play_youtube_video("atif aslam tajdar e haram")
        self.assertTrue(res.get("success"))
        self.assertTrue(res.get("video_url", "").startswith("https://www.youtube.com/watch?v="))
        self.assertIsNotNone(res.get("video_id"))
        self.assertEqual(len(res.get("video_id", "")), 11)
        self.assertTrue(len(res.get("title", "")) > 0)

    def test_05_website_deep_analysis(self):
        """Verify analyze_website extracts structured analysis from public URL."""
        res = analyze_website("https://python.org", open_in_browser=False)
        self.assertTrue(res.get("success"))
        self.assertIn("Python", res.get("title", ""))
        self.assertTrue(len(res.get("summary", "")) > 10)
        self.assertTrue(len(res.get("highlights", [])) > 0)
        self.assertIn("--- Website Analysis:", res.get("message", ""))

    def test_06_search_and_play_fast_path_parsing(self):
        """Verify parse_browser_search correctly distinguishes between search and auto-play."""
        # Auto-play queries
        play_queries = [
            ("youtube per ye song search kro or play kro", "ye song"),
            ("youtube per atif aslam tajdar e haram play kro", "atif aslam tajdar e haram"),
            ("youtube par satinder sartaaj chalao", "satinder sartaaj"),
            ("play softly on youtube", "softly"),
        ]
        for q, exp_query in play_queries:
            parsed = parse_browser_search(q)
            self.assertIsNotNone(parsed, f"Failed to parse '{q}'")
            self.assertEqual(parsed.get("platform"), "youtube")
            self.assertTrue(parsed.get("play"), f"Expected play=True for '{q}'")

        # Pure search queries
        search_queries = [
            ("google per search kro jarvis ai", "google"),
            ("youtube per search kro machine learning", "youtube"),
            ("search python docs on google", "google"),
        ]
        for q, exp_plat in search_queries:
            parsed = parse_browser_search(q)
            self.assertIsNotNone(parsed, f"Failed to parse '{q}'")
            self.assertEqual(parsed.get("platform"), exp_plat)
            self.assertFalse(parsed.get("play", False), f"Expected play=False for '{q}'")

    def test_07_spoken_acknowledgments(self):
        """Verify spoken responses for play_youtube_video, analyze_website, list_google_accounts."""
        # YouTube play
        ack_yt = get_spoken_acknowledgment("play_youtube_video", {
            "success": True,
            "title": "Tajdar-e-Haram",
            "video_url": "https://www.youtube.com/watch?v=a18py61_F_w"
        }, is_urdu=True)
        self.assertIn("Tajdar-e-Haram", ack_yt)
        self.assertIn("play", ack_yt)

        # Website analysis
        ack_site = get_spoken_acknowledgment("analyze_website", {
            "success": True,
            "title": "Python.org",
            "summary": "Official Python programming language website."
        }, is_urdu=True)
        self.assertIn("Python.org", ack_site)
        self.assertIn("analyze", ack_site)

        # List accounts
        ack_accs = get_spoken_acknowledgment("list_google_accounts", {
            "success": True,
            "count": 4
        }, is_urdu=True)
        self.assertIn("4", ack_accs)
        self.assertIn("Google accounts", ack_accs)

        # Bookmarks & History acknowledgments
        ack_bm = get_spoken_acknowledgment("list_chrome_bookmarks", {
            "success": True,
            "count": 83
        }, is_urdu=True)
        self.assertIn("83", ack_bm)
        self.assertIn("bookmarks", ack_bm)

        ack_smart = get_spoken_acknowledgment("open_smart_website", {
            "success": True,
            "title": "Vercel Dashboard",
            "source": "bookmark",
            "profile": "Account 4"
        }, is_urdu=True)
        self.assertIn("Vercel Dashboard", ack_smart)
        self.assertIn("bookmark", ack_smart)

    def test_08_bookmarks_and_history_tool_registration(self):
        """Verify bookmark and history tools are registered in schema and handlers."""
        new_tools = ["list_chrome_bookmarks", "search_chrome_history", "open_smart_website"]
        tool_names = [t["function"]["name"] for t in JARVIS_TOOLS_SCHEMA if "function" in t]
        for name in new_tools:
            self.assertIn(name, tool_names, f"Tool '{name}' not found in JARVIS_TOOLS_SCHEMA.")
            self.assertIn(name, TOOL_HANDLERS, f"Tool '{name}' not found in TOOL_HANDLERS mapping.")
            self.assertEqual(TOOL_RISK_MAP.get(name), RiskLevel.LOW, f"Tool '{name}' must have RiskLevel.LOW.")

    def test_09_extract_chrome_bookmarks(self):
        """Verify get_chrome_bookmarks and list_chrome_bookmarks extract bookmarks from Chrome profiles."""
        bms = get_chrome_bookmarks()
        self.assertIsInstance(bms, list)
        self.assertGreater(len(bms), 0, "Expected to find saved bookmarks in user's Chrome data.")
        
        # Verify bookmark structure
        first = bms[0]
        self.assertIn("title", first)
        self.assertIn("url", first)
        self.assertIn("profile_name", first)
        self.assertTrue(first["url"].startswith(("http://", "https://")))

        # Test list_chrome_bookmarks formatting
        res = list_chrome_bookmarks()
        self.assertTrue(res.get("success"))
        self.assertGreater(res.get("count", 0), 0)
        self.assertIn("Chrome Bookmark", res.get("message", ""))

    def test_10_chrome_history_search(self):
        """Verify search_chrome_history can read history SQLite without lock issues."""
        res = search_chrome_history_tool(query="google", limit=5)
        self.assertTrue(res.get("success"))
        self.assertIsInstance(res.get("history"), list)

    def test_11_smart_url_resolver(self):
        """Verify resolve_smart_url accurately matches queries to bookmarks/history."""
        # Vercel should resolve to user's personal project dashboard URL
        res_vercel = resolve_smart_url("vercel")
        self.assertTrue(res_vercel.get("found"))
        self.assertIn("vercel.com", res_vercel.get("url"))
        self.assertIn("akmaldoghars-projects", res_vercel.get("url"))

        # LMS should resolve to VU LMS login/portal or student service
        res_lms = resolve_smart_url("lms")
        self.assertTrue(res_lms.get("found"))
        self.assertTrue(any(domain in res_lms.get("url") for domain in ("vu.edu.pk", "vulms.vu.edu.pk")))

    @mock.patch("subprocess.Popen")
    def test_12_open_smart_website_mocked(self, mock_popen):
        """Verify open_smart_website executes and returns descriptive confirmation."""
        mock_popen.return_value = mock.MagicMock()
        res = open_smart_website("vercel")
        self.assertTrue(res.get("success"))
        self.assertIn("vercel.com", res.get("url"))
        self.assertIn("akmaldoghars-projects", res.get("url"))
        self.assertIn("Opened your", res.get("message"))

    def test_13_bookmarks_history_fast_path_parsing(self):
        """Verify brain parsers for bookmarks, history, and smart portal opening."""
        # Bookmarks queries
        bm_list = parse_bookmarks_query("mere bookmarks dikhao")
        self.assertIsNotNone(bm_list)
        self.assertEqual(bm_list.get("action"), "list")

        bm_open = parse_bookmarks_query("bookmarks mein se vercel open karo")
        self.assertIsNotNone(bm_open)
        self.assertEqual(bm_open.get("action"), "open")
        self.assertEqual(bm_open.get("query"), "vercel")

        # History queries
        hist_search = parse_history_query("chrome history search karo python")
        self.assertIsNotNone(hist_search)
        self.assertEqual(hist_search.get("action"), "search")
        self.assertEqual(hist_search.get("query"), "python")

        hist_open = parse_history_query("history se lms kholo")
        self.assertIsNotNone(hist_open)
        self.assertEqual(hist_open.get("action"), "open")
        self.assertEqual(hist_open.get("query"), "lms")

        # Portal queries
        portal = parse_smart_portal_open("mera vercel open karo")
        self.assertIsNotNone(portal)
        self.assertEqual(portal.get("query"), "vercel")


if __name__ == "__main__":
    unittest.main()
