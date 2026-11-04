"""
JARVIS Local LLM & Ollama Integration Engine
Phase 11 Component: Discovers, connects, and interfaces with locally-hosted
LLM inference engines (Ollama, LM Studio, llama.cpp, LocalAI).
"""

import json
import os
import threading
import time
import urllib.request
from typing import Any, Dict, List, Optional
from openai import OpenAI


_state_lock = threading.Lock()
_cached_detection: Optional[Dict[str, Any]] = None
_cached_detection_time: float = 0.0
_DETECTION_TTL: float = 10.0


# Standard local inference server endpoints to probe
DEFAULT_CANDIDATE_SERVERS = [
    {
        "type": "ollama",
        "provider": "local_ollama",
        "health_url": "http://127.0.0.1:11434/api/tags",
        "base_url": "http://127.0.0.1:11434/v1",
        "default_models": ["llama3.2", "llama3.1", "qwen2.5", "mistral", "phi3"]
    },
    {
        "type": "lm_studio",
        "provider": "local_lm_studio",
        "health_url": "http://127.0.0.1:1234/v1/models",
        "base_url": "http://127.0.0.1:1234/v1",
        "default_models": ["local-model"]
    },
    {
        "type": "llama_cpp",
        "provider": "local_llama_cpp",
        "health_url": "http://127.0.0.1:8080/v1/models",
        "base_url": "http://127.0.0.1:8080/v1",
        "default_models": ["default"]
    }
]


def _probe_server(health_url: str, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
    """Quick HTTP probe against local server endpoint."""
    try:
        req = urllib.request.Request(
            health_url,
            headers={"User-Agent": "JARVIS-LocalLLM-Probe/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                body = resp.read().decode("utf-8")
                try:
                    return json.loads(body)
                except Exception:
                    return {}
    except Exception:
        return None
    return None


def detect_local_llm(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Detect if Ollama, LM Studio, or a custom local OpenAI-compatible
    inference engine is active on the host machine.
    """
    global _cached_detection, _cached_detection_time

    now = time.time()
    with _state_lock:
        if not force_refresh and _cached_detection is not None and (now - _cached_detection_time) < _DETECTION_TTL:
            return _cached_detection

    custom_url = os.getenv("LOCAL_LLM_URL", "").strip()
    custom_model = os.getenv("LOCAL_LLM_MODEL", "").strip()

    candidate_servers = list(DEFAULT_CANDIDATE_SERVERS)
    if custom_url:
        candidate_servers.insert(0, {
            "type": "custom",
            "provider": "local_custom",
            "health_url": f"{custom_url.rstrip('/')}/models",
            "base_url": custom_url,
            "default_models": [custom_model] if custom_model else ["local-model"]
        })

    detected_info = {
        "available": False,
        "provider": "none",
        "type": None,
        "base_url": None,
        "models": [],
        "active_model": None,
        "message": "No local LLM engine detected on standard ports (11434, 1234, 8080)."
    }

    for s in candidate_servers:
        data = _probe_server(s["health_url"], timeout=0.8)
        if data is not None:
            models_found = []
            # Extract models from Ollama /api/tags
            if s["type"] == "ollama" and "models" in data:
                for m in data["models"]:
                    name = m.get("name") or m.get("model")
                    if name:
                        models_found.append(name)
            # Extract models from OpenAI /v1/models (LM Studio / llama.cpp / custom)
            elif "data" in data and isinstance(data["data"], list):
                for m in data["data"]:
                    mid = m.get("id")
                    if mid:
                        models_found.append(mid)

            if not models_found:
                models_found = s["default_models"]

            active_model = custom_model if (custom_model and custom_model in models_found) else models_found[0]

            detected_info = {
                "available": True,
                "provider": s["provider"],
                "type": s["type"],
                "base_url": s["base_url"],
                "models": models_found,
                "active_model": active_model,
                "message": f"Connected to local {s['type']} server at {s['base_url']} with {len(models_found)} model(s)."
            }
            break

    with _state_lock:
        _cached_detection = detected_info
        _cached_detection_time = now

    return detected_info


def get_local_openai_client(base_url: str, timeout: float = 20.0) -> OpenAI:
    """Create an OpenAI client pointing to the local LLM endpoint."""
    return OpenAI(
        base_url=base_url,
        api_key="ollama-local",
        timeout=timeout,
        max_retries=1
    )
