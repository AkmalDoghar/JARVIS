"""
JARVIS Network Connectivity & Status Supervisor
Phase 11: Real-time network probe, latency monitor, operational mode manager,
and local LLM availability checker.
"""

import enum
import os
import socket
import threading
import time
import urllib.request
from typing import Any, Dict, Optional, Tuple


class NetworkMode(str, enum.Enum):
    AUTO = "auto"              # Cloud primary -> Local LLM -> Offline rules
    CLOUD_ONLY = "cloud_only"  # Strict cloud APIs (error if disconnected)
    OFFLINE_ONLY = "offline_only"  # Force local/offline even if internet is available


class NetworkStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


# State variables
_state_lock = threading.Lock()
_current_mode: NetworkMode = NetworkMode.AUTO
_cached_online: Optional[bool] = None
_cached_latency_ms: float = 0.0
_cached_timestamp: float = 0.0
_CACHE_TTL_SECONDS: float = 5.0

# Reliable DNS and HTTP endpoints for fast network probing
DNS_PROBE_TARGETS = [
    ("1.1.1.1", 53),   # Cloudflare Primary DNS
    ("8.8.8.8", 53),   # Google Primary DNS
    ("9.9.9.9", 53),   # Quad9 Primary DNS
]
HTTP_PROBE_URLS = [
    "http://1.1.1.1",
    "http://www.google.com",
    "http://www.cloudflare.com",
]


def probe_socket_connectivity(timeout: float = 1.2) -> Tuple[bool, float]:
    """
    Ultra-fast socket connection probe against global DNS servers.
    Returns (is_connected, latency_ms).
    """
    for host, port in DNS_PROBE_TARGETS:
        t0 = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
            sock.close()
            latency = (time.time() - t0) * 1000.0
            return True, round(latency, 2)
        except (socket.timeout, OSError):
            continue

    # Fallback to HTTP probe if DNS ports (53) are firewalled
    for url in HTTP_PROBE_URLS:
        t0 = time.time()
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "JARVIS-Network-Probe/1.0"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status in (200, 204, 301, 302):
                    latency = (time.time() - t0) * 1000.0
                    return True, round(latency, 2)
        except Exception:
            continue

    return False, 0.0


def is_internet_available(force_refresh: bool = False, timeout: float = 1.2) -> bool:
    """
    Check if the host machine has an active Internet connection.
    Uses in-memory caching with TTL to keep performance instantaneous.
    """
    global _cached_online, _cached_latency_ms, _cached_timestamp

    now = time.time()
    with _state_lock:
        if not force_refresh and _cached_online is not None and (now - _cached_timestamp) < _CACHE_TTL_SECONDS:
            return _cached_online

    is_online, latency = probe_socket_connectivity(timeout=timeout)

    with _state_lock:
        _cached_online = is_online
        _cached_latency_ms = latency
        _cached_timestamp = now

    return is_online


def get_network_latency(force_refresh: bool = False, timeout: float = 1.2) -> float:
    """Return latency in milliseconds to primary network probe."""
    global _cached_latency_ms
    is_internet_available(force_refresh=force_refresh, timeout=timeout)
    return _cached_latency_ms


def get_network_mode() -> NetworkMode:
    """Get current configured network mode."""
    with _state_lock:
        return _current_mode


def set_network_mode(mode: str) -> Dict[str, Any]:
    """
    Update configured network mode.
    Accepted: 'auto', 'cloud_only', 'offline_only'.
    """
    global _current_mode
    mode_str = mode.strip().lower()
    try:
        new_mode = NetworkMode(mode_str)
    except ValueError:
        raise ValueError(f"Invalid mode '{mode}'. Choose from: 'auto', 'cloud_only', 'offline_only'.")

    with _state_lock:
        _current_mode = new_mode

    return {
        "status": "success",
        "mode": _current_mode.value,
        "message": f"Network mode switched to '{_current_mode.value}'"
    }


def get_network_status(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Retrieve comprehensive network telemetry, operational mode, and local LLM presence.
    """
    online = is_internet_available(force_refresh=force_refresh)
    latency = _cached_latency_ms
    mode = get_network_mode()

    # Query local LLM presence
    from backend.agent.local_llm import detect_local_llm
    local_info = detect_local_llm()

    # Determine effective runtime mode
    if mode == NetworkMode.OFFLINE_ONLY:
        status_label = "offline_forced"
        if local_info and local_info.get("available"):
            effective_engine = "local_llm"
        else:
            effective_engine = "offline_deterministic"
    elif not online:
        status_label = "offline_disconnected"
        if local_info and local_info.get("available"):
            effective_engine = "local_llm"
        else:
            effective_engine = "offline_deterministic"
    else:
        status_label = "online"
        effective_engine = "cloud_primary"

    return {
        "is_online": online,
        "latency_ms": latency,
        "status": status_label,
        "mode": mode.value,
        "effective_engine": effective_engine,
        "local_llm": local_info,
        "timestamp": time.time(),
        "probe_targets": [t[0] for t in DNS_PROBE_TARGETS]
    }

