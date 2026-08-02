from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import subprocess


@dataclass
class KopsClient:
    """kOps AWS Kubernetes cluster management.

    Runs kops CLI commands. kops binary must be on PATH and KOPS_STATE_STORE set.
    Returns available:False gracefully when kops is not installed.
    """

    def list_clusters(self) -> dict[str, Any]:
        try:
            result = subprocess.run(
                ["kops", "get", "clusters", "--output", "json"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode != 0:
                return {"available": False, "error": result.stderr.strip()}
            import json
            return {"available": True, "clusters": json.loads(result.stdout or "[]")}
        except FileNotFoundError:
            return {
                "available": False,
                "message": "kops binary not found. Install kops and set KOPS_STATE_STORE.",
            }
        except Exception as exc:
            return {"available": False, "error": str(exc)}
