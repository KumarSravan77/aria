from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import time, uuid

@dataclass
class InMemoryCheckpointStore:
    checkpoints: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def save(self, investigation_id: str, node: str, state: dict[str, Any]) -> dict[str, Any]:
        checkpoint = {
            "checkpoint_id": str(uuid.uuid4()),
            "investigation_id": investigation_id,
            "node": node,
            "timestamp": time.time(),
            "mode": state.get("mode"),
            "evidence_count": len(state.get("evidence", [])),
            "hypothesis_count": len(state.get("hypotheses", [])),
        }
        self.checkpoints.setdefault(investigation_id, []).append(checkpoint)
        return checkpoint

    def list(self, investigation_id: str) -> list[dict[str, Any]]:
        return self.checkpoints.get(investigation_id, [])
