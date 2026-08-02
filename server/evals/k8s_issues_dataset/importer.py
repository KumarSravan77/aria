from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


DEFAULT_DATASET = Path("datasets/k8s-prod-issues/sample_issues.json")


@dataclass
class K8sIssuesImporter:
    dataset_path: Path = DEFAULT_DATASET

    def load(self) -> list[dict[str, Any]]:
        if not self.dataset_path.exists():
            return []
        return json.loads(self.dataset_path.read_text())
