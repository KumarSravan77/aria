from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from training.common.manifests import sha256_tree


def register_model(
    artifact: str | Path,
    registry_dir: str | Path,
    *,
    name: str,
    version: str,
    base_model: str,
    dataset_manifest: str | Path,
    scorecard: str | Path,
) -> Path:
    artifact_path = Path(artifact)
    if not artifact_path.exists():
        raise FileNotFoundError(f"model artifact does not exist: {artifact_path}")
    dataset = json.loads(Path(dataset_manifest).read_text())
    scores = json.loads(Path(scorecard).read_text())
    entry: dict[str, Any] = {
        "name": name,
        "version": version,
        "stage": "candidate",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifact_path": str(artifact_path),
        "artifact_sha256": sha256_tree(artifact_path),
        "base_model": base_model,
        "dataset": {"name": dataset["name"], "version": dataset["version"], "sha256": dataset["source_sha256"]},
        "benchmark": scores.get("benchmark"),
        "scores": scores,
    }
    target = Path(registry_dir) / name / f"{version}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(f"immutable registry entry already exists: {target}")
    target.write_text(json.dumps(entry, indent=2, sort_keys=True) + "\n")
    return target
