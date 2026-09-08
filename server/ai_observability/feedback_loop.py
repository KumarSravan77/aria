from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any
import hashlib
import json
import time
import uuid

ALLOWED_CATEGORIES = {"correct", "incorrect_answer", "wrong_source", "missing_source", "unsafe", "stale_knowledge", "slow", "other"}
SENSITIVE_KEYS = {"prompt", "document", "context", "token", "password", "secret", "api_key"}

@dataclass(frozen=True)
class FeedbackRecord:
    trace_id: str
    answer_id: str
    rating: int
    category: str
    session_id: str | None = None
    expected_source: str | None = None
    comment: str | None = None
    reviewer_id: str | None = None
    feedback_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    approved_for_evaluation: bool = False
    record_hash: str = ""

    def validate(self) -> None:
        if not self.trace_id or not self.answer_id:
            raise ValueError("trace_id and answer_id are required")
        if self.rating not in {-1, 0, 1}:
            raise ValueError("rating must be -1, 0, or 1")
        if self.category not in ALLOWED_CATEGORIES:
            raise ValueError(f"unsupported feedback category: {self.category}")
        if self.comment and len(self.comment) > 1000:
            raise ValueError("comment exceeds 1000 characters")

class FeedbackStore:
    """Durable, trace-linked feedback with a human-controlled evaluation gate."""

    def __init__(self, path: str | Path = "logs/ai_feedback.jsonl") -> None:
        self.path = Path(path)
        self._lock = Lock()

    @staticmethod
    def _hash(payload: dict[str, Any]) -> str:
        material = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(material.encode()).hexdigest()

    def submit(self, payload: dict[str, Any]) -> dict[str, Any]:
        forbidden = SENSITIVE_KEYS.intersection(payload)
        if forbidden:
            raise ValueError(f"raw sensitive fields are not accepted: {sorted(forbidden)}")
        record = FeedbackRecord(**payload)
        record.validate()
        item = asdict(record)
        item["record_hash"] = self._hash({k: v for k, v in item.items() if k != "record_hash"})
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(item, sort_keys=True) + "\n")
        return item

    def records(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records

    def summary(self) -> dict[str, Any]:
        records = self.records()
        categories: dict[str, int] = {}
        for item in records:
            categories[item["category"]] = categories.get(item["category"], 0) + 1
        negative = sum(1 for item in records if item["rating"] < 0)
        return {"feedback_count": len(records), "negative_count": negative,
                "negative_rate": round(negative / max(len(records), 1), 4),
                "categories": categories,
                "knowledge_gap_count": categories.get("missing_source", 0) + categories.get("stale_knowledge", 0)}

    def approve_for_evaluation(self, feedback_id: str, reviewer_id: str) -> dict[str, Any]:
        if not reviewer_id:
            raise ValueError("reviewer_id is required")
        original = next((item for item in self.records() if item["feedback_id"] == feedback_id), None)
        if not original:
            raise KeyError(feedback_id)
        candidate = {"feedback_id": original["feedback_id"], "trace_id": original["trace_id"],
                     "answer_id": original["answer_id"], "category": original["category"],
                     "expected_source": original.get("expected_source"), "reviewer_id": reviewer_id,
                     "approved_at": time.time()}
        candidate["approval_hash"] = self._hash(candidate)
        return candidate
