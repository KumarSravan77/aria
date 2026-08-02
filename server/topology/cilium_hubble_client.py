from __future__ import annotations

from typing import Any


class CiliumHubbleClient:
    """Boundary for service topology and network flow evidence.

    Local implementation returns a placeholder so the rest of the platform can be wired before Hubble Relay is available.
    """

    def service_topology(self, service: str) -> dict[str, Any]:
        return {
            "available": False,
            "service": service,
            "message": "Hubble Relay not configured. Install Cilium/Hubble and wire this adapter to hubble observe/export APIs.",
            "upstream": [],
            "downstream": [],
        }
