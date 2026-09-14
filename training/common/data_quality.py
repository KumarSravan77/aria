from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from training.common.data_pipeline import DatasetValidationError, read_jsonl


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_-]+", text.lower()))


def _user_text(record: dict[str, Any]) -> str:
    return " ".join(item["content"] for item in record["messages"] if item["role"] == "user")


def _jaccard(left: str, right: str) -> float:
    a, b = _tokens(left), _tokens(right)
    return len(a & b) / len(a | b) if a or b else 1.0


@dataclass(frozen=True)
class DatasetAudit:
    record_count: int
    task_distribution: dict[str, int]
    service_distribution: dict[str, int]
    difficulty_distribution: dict[str, int]
    minimum_quality_score: float
    benchmark_count: int
    contamination_pairs: list[dict[str, Any]]

    def write(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(asdict(self), indent=2, sort_keys=True) + "\n")


def audit_dataset(source: str | Path, benchmark: str | Path, *, threshold: float = 0.8) -> DatasetAudit:
    records = read_jsonl(source)
    benchmark_items = [json.loads(line) for line in Path(benchmark).read_text().splitlines() if line.strip()]
    contamination: list[dict[str, Any]] = []
    for record in records:
        training_prompt = _user_text(record)
        for item in benchmark_items:
            similarity = _jaccard(training_prompt, item["prompt"])
            if similarity >= threshold:
                contamination.append({
                    "training_id": record["id"],
                    "benchmark_id": item["id"],
                    "jaccard": round(similarity, 4),
                })
    quality_scores = [float(item.get("quality", {}).get("score", 0.0)) for item in records]
    return DatasetAudit(
        record_count=len(records),
        task_distribution=dict(sorted(Counter(item["task"] for item in records).items())),
        service_distribution=dict(sorted(Counter(item.get("service", "unknown") for item in records).items())),
        difficulty_distribution=dict(sorted(Counter(item.get("difficulty", "unknown") for item in records).items())),
        minimum_quality_score=min(quality_scores),
        benchmark_count=len(benchmark_items),
        contamination_pairs=contamination,
    )


def enforce_audit(audit: DatasetAudit, *, minimum_quality: float = 0.9) -> None:
    if audit.minimum_quality_score < minimum_quality:
        raise DatasetValidationError(
            f"minimum quality {audit.minimum_quality_score:.2f} is below {minimum_quality:.2f}"
        )
    if audit.contamination_pairs:
        raise DatasetValidationError("training/evaluation prompt contamination detected")
