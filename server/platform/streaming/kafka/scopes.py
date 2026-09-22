from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


_DEFAULT_FILE = Path(__file__).resolve().parents[3] / "authz" / "kafka_resources.yaml"


@dataclass
class KafkaResourceScope:
    """Fail-closed service-to-topic/group policy for live diagnostics."""

    path: Path = field(default_factory=lambda: _DEFAULT_FILE)

    def allows(self, service: str, topic: str | None, consumer_group: str | None) -> bool:
        if not service or not topic or not consumer_group or not self.path.is_file():
            return False
        try:
            data = yaml.safe_load(self.path.read_text()) or {}
            entries = data.get("services", {}).get(service, [])
            return any(
                item.get("topic") == topic and item.get("consumer_group") == consumer_group
                for item in entries if isinstance(item, dict)
            )
        except (OSError, yaml.YAMLError, AttributeError, TypeError):
            return False
