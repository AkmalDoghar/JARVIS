"""
Tests for Phase 11: Offline & Hybrid Fallback Engine
Verifies network connectivity detector, local LLM probe, deterministic offline
rule engine, offline STT fallback, brain failover, and FastAPI endpoints.
"""

import json
import unittest
import urllib.request
from unittest.mock import MagicMock, patch

from backend.agent.brain import JarvisBrain
from backend.agent.local_llm import detect_local_llm, get_local_openai_client
from backend.agent.offline_fallback import (
    execute_offline_system_command,
    parse_app_command,
    parse_volume_command,
    parse_system_status_command,
    parse_time_command,
    parse_git_command,
    parse_greeting
)
from backend.network.connectivity import (
    NetworkMode,
    get_network_latency,
    get_network_mode,
    get_network_status,
    is_internet_available,
    probe_socket_connectivity,
    set_network_mode
)
from backend.voice.speech_to_text import transcribe_offline


class TestPhase11HybridOfflineEngine(unittest.TestCase):

    def setUp(self):
        # Always ensure network mode is reset to AUTO before each test
        set_network_mode("auto")

    def tearDown(self):
        set_network_mode("auto")

    def test_01_network_probe_and_latency(self):
        """Verify socket connectivity probe and latency calculation."""
        is_conn, latency = probe_socket_connectivity(timeout=1.5)
        self.assertIsInstance(is_conn, bool)
        self.assertIsInstance(latency, float)
        self.assertGreaterEqual(latency, 0.0)

        # Test cached wrapper
        online = is_internet_available(force_refresh=True)
        self.assertIsInstance(online, bool)
        cached_lat = get_network_latency()
        self.assertGreaterEqual(cached_lat, 0.0)
        print("  [PASS] Test 1: Socket connectivity probe and latency verified.")

    def test_02_network_modes_and_lifecycle(self):
        """Verify network mode transitions: auto, offline_only, cloud_only."""
        # 1. Default is AUTO
        self.assertEqual(get_network_mode(), NetworkMode.AUTO)

        # 2. Switch to OFFLINE_ONLY
        res = set_network_mode("offline_only")
        self.assertEqual(res["status"], "success")
        self.assertEqual(get_network_mode(), NetworkMode.OFFLINE_ONLY)

        # 3. Switch to CLOUD_ONLY
        res2 = set_network_mode("cloud_only")
        self.assertEqual(res2["status"], "success")
        self.assertEqual(get_network_mode(), NetworkMode.CLOUD_ONLY)

        # 4. Reject invalid mode
        with self.assertRaises(ValueError):
            set_network_mode("invalid_quantum_mode")

        # 5. Reset to AUTO
        set_network_mode("auto")
        self.assertEqual(get_network_mode(), NetworkMode.AUTO)
        print("  [PASS] Test 2: Network operational mode lifecycle and validation verified.")

    def test_03_local_llm_detection_structure(self):
        """Verify local LLM probe returns structured metadata."""
        info = detect_local_llm(force_refresh=True)
        self.assertIn("available", info)
        self.assertIn("provider", info)
        self.assertIn("models", info)
        self.assertIn("base_url", info)

        # Test OpenAI client builder
        client = get_local_openai_client("http://127.0.0.1:11434/v1")
        self.assertIsNotNone(client)
        self.assertEqual(str(client.base_url).rstrip("/"), "http://127.0.0.1:11434/v1")
        print("  [PASS] Test 3: Local LLM detection structure & client factory verified.")

    def test_04_offline_app_and_volume_parsing(self):
        """Verify parsing of application and volume commands in Roman Urdu & English."""
        # App open
        action, app = parse_app_command("notepad open karo")
        self.assertEqual(action, "open")
        self.assertEqual(app, "notepad")

        action, app = parse_app_command("launch calculator")
        self.assertEqual(action, "open")
        self.assertEqual(app, "calculator")

        # App close
        action, app = parse_app_command("chrome band karo")
        self.assertEqual(action, "close")
        self.assertEqual(app, "chrome")

        # Volume set
        vol_args = parse_volume_command("volume 65 percent karo")
        self.assertIsNotNone(vol_args)
        self.assertEqual(vol_args["action"], "set")
        self.assertEqual(vol_args["level"], 65)

        # Volume mute / unmute
        mute_args = parse_volume_command("awaz band karo")
        self.assertEqual(mute_args["action"], "mute")

        unmute_args = parse_volume_command("unmute karo")
        self.assertEqual(unmute_args["action"], "unmute")
        print("  [PASS] Test 4: App and volume natural language parsing verified.")

    def test_05_offline_system_status_and_time(self):
        """Verify system status, telemetry, time, and git commands parsing."""
        tool = parse_system_status_command("battery kitni hai")
        self.assertEqual(tool, "get_system_status")

        tool = parse_system_status_command("running windows dikhao")
        self.assertEqual(tool, "get_open_windows")

        time_res = parse_time_command("time kya hua hai")
        self.assertIsNotNone(time_res)
        self.assertEqual(time_res["type"], "time")

        git_tool = parse_git_command("git status check karo")
        self.assertEqual(git_tool, "run_git_status")

        greet = parse_greeting("suno jarvis")
        self.assertEqual(greet, "greeting")

        ident = parse_greeting("tum kaun ho")
        self.assertEqual(ident, "identity")
        print("  [PASS] Test 5: System status, time, git, and greeting parsing verified.")

    def test_06_deterministic_offline_execution(self):
        """Verify execution of commands via execute_offline_system_command."""
        # 1. Volume execution
        res_vol = execute_offline_system_command("volume 50 karo")
        self.assertEqual(res_vol["status"], "success")
        self.assertEqual(res_vol["provider"], "offline-deterministic")
        self.assertEqual(res_vol["tool_executed"], "set_system_volume")

        # 2. Time query execution
        res_time = execute_offline_system_command("time kya hua hai")
        self.assertEqual(res_time["status"], "success")
        self.assertIn("time", res_time["response"].lower())

        # 3. Generative query rejection in offline mode
        res_gen = execute_offline_system_command("explain quantum mechanics in detail")
        self.assertEqual(res_gen["status"], "offline_mode_active")
        self.assertIn("offline", res_gen["response"].lower())
        print("  [PASS] Test 6: Deterministic offline execution & generative rejection verified.")

    def test_07_brain_offline_mode_integration(self):
        """Verify JarvisBrain automatically routes to offline engine when in offline_only mode."""
        brain = JarvisBrain()

        # Set to offline mode
        set_network_mode("offline_only")

        # System command should execute offline
        res = brain.process_message("volume 40 karo")
        self.assertEqual(res.get("provider"), "offline-deterministic")
        self.assertEqual(res.get("status"), "success")

        # Generative query should return friendly offline guide
        res_gen = brain.process_message("write a python script for sorting")
        self.assertEqual(res_gen.get("provider"), "offline-deterministic")
        self.assertEqual(res_gen.get("status"), "offline_mode_active")

        # Reset mode
        set_network_mode("auto")
        print("  [PASS] Test 7: JarvisBrain seamless offline routing verified.")

    def test_08_offline_stt_fallback_exception(self):
        """Verify transcribe_offline throws graceful informative exception when no local engine installed."""
        mock_recognizer = MagicMock()
        mock_audio = MagicMock()

        # Mock all local recognizers as missing
        mock_recognizer.recognize_faster_whisper.side_effect = Exception("Not installed")
        mock_recognizer.recognize_whisper.side_effect = Exception("Not installed")
        mock_recognizer.recognize_vosk.side_effect = Exception("Not installed")
        mock_recognizer.recognize_sphinx.side_effect = Exception("Not installed")

        with self.assertRaises(RuntimeError) as ctx:
            transcribe_offline(mock_recognizer, mock_audio)

        self.assertIn("Cloud speech recognition unreachable", str(ctx.exception))
        print("  [PASS] Test 8: Offline STT graceful error handling verified.")

    def test_09_live_network_endpoints(self):
        """Verify FastAPI endpoints /api/network/status, /api/network/mode, and /api/network/local-llm."""
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)

        # 1. GET /api/network/status
        resp = client.get("/api/network/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("is_online", data)
        self.assertIn("mode", data)
        self.assertIn("effective_engine", data)

        # 2. POST /api/network/mode
        resp_post = client.post("/api/network/mode", json={"mode": "offline_only"})
        self.assertEqual(resp_post.status_code, 200)
        data_post = resp_post.json()
        self.assertEqual(data_post["mode"], "offline_only")

        # 3. GET /api/network/local-llm
        resp_local = client.get("/api/network/local-llm")
        self.assertEqual(resp_local.status_code, 200)
        data_local = resp_local.json()
        self.assertIn("available", data_local)

        # Reset mode back to auto
        client.post("/api/network/mode", json={"mode": "auto"})

        # Clean up hotkey background thread started by app startup
        try:
            from backend.desktop.hotkey import stop_hotkey_listener
            stop_hotkey_listener()
        except Exception:
            pass

        print("  [PASS] Test 9: Live FastAPI network endpoints verified.")


if __name__ == "__main__":
    unittest.main()
