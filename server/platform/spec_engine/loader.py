from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml


class SpecLoader:
    """Loads ARIA YAML specs from the repository.

    The loader is intentionally deterministic and filesystem-backed so the
    harness can validate agent behavior without requiring live platform
    integrations.
    """

    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root or Path.cwd())

    def load_yaml(self, relative_path: str) -> Dict[str, Any]:
        path = self.repo_root / relative_path
        if not path.exists():
            raise FileNotFoundError(f"Spec not found: {relative_path}")
        data = yaml.safe_load(path.read_text()) or {}
        if not isinstance(data, dict):
            raise ValueError(f"Spec must be a YAML object: {relative_path}")
        return data

    def load_index(self) -> Dict[str, Any]:
        return self.load_yaml("specs/platform/spec-index.yaml")

    def load_collection(self, section: str) -> List[Dict[str, Any]]:
        index = self.load_index().get("spec_index", {})
        paths: Iterable[str] = index.get(section, [])
        return [self.load_yaml(path) for path in paths]

    def load_golden_path(self, name: str) -> Dict[str, Any]:
        for spec in self.load_collection("golden_paths"):
            if spec.get("golden_path", {}).get("name") == name:
                return spec
        raise KeyError(f"Golden path not found: {name}")

    def load_service_profile(self, service_id: str) -> Dict[str, Any]:
        return self.load_yaml(f"specs/service-profiles/{service_id}.yaml")
