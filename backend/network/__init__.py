"""
JARVIS Network & Connectivity Package
Phase 11: Real-time network probe, latency monitor, and hybrid mode management.
"""

from backend.network.connectivity import (
    is_internet_available,
    get_network_latency,
    get_network_status,
    set_network_mode,
    NetworkStatus,
    NetworkMode,
)

__all__ = [
    "is_internet_available",
    "get_network_latency",
    "get_network_status",
    "set_network_mode",
    "NetworkStatus",
    "NetworkMode",
]

