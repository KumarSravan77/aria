from __future__ import annotations

import fcntl
import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GENESIS_HASH = "0" * 64
FORBIDDEN_KEYS = {"prompt", "response", "api_key", "authorization", "secret", "token"}


def _canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _reject_sensitive_keys(value: Any, path: str = "record") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                raise ValueError(f"sensitive field is forbidden in evidence ledger: {path}.{key}")
            _reject_sensitive_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_sensitive_keys(child, f"{path}[{index}]")


@dataclass(frozen=True)
class AITransactionEvidence:
    trace_id: str
    request_id: str
    domain: str
    application: str
    agent_id: str
    workload_identity: str
    model: dict[str, str]
    policy: dict[str, str]
    guardrails: dict[str, str]
    lineage: dict[str, str]
    latency_ms: dict[str, float]
    evaluation: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def validate(self) -> None:
        for name in ("trace_id", "request_id", "domain", "application", "agent_id", "workload_identity"):
            if not getattr(self, name):
                raise ValueError(f"{name} is required")
        for section in ("model", "policy", "guardrails", "lineage"):
            if not getattr(self, section):
                raise ValueError(f"{section} evidence is required")
        _reject_sensitive_keys(asdict(self))


@dataclass(frozen=True)
class LedgerVerification:
    valid: bool
    record_count: int
    error: str | None = None


class EvidenceLedger:
    """Local append-only, hash-chained evidence adapter.

    The chain detects deletion, reordering and modification. Production should
    export records to WORM/object-lock storage or an immutable audit service.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, evidence: AITransactionEvidence) -> dict[str, Any]:
        evidence.validate()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            handle.seek(0)
            lines = [line for line in handle.read().splitlines() if line.strip()]
            previous_hash = json.loads(lines[-1])["record_hash"] if lines else GENESIS_HASH
            record = {**asdict(evidence), "sequence": len(lines) + 1, "previous_hash": previous_hash}
            record["record_hash"] = _hash(record)
            handle.seek(0, 2)
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            handle.flush()
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return record

    def verify(self) -> LedgerVerification:
        if not self.path.exists():
            return LedgerVerification(True, 0)
        previous_hash = GENESIS_HASH
        count = 0
        try:
            for count, line in enumerate(self.path.read_text().splitlines(), 1):
                record = json.loads(line)
                stored_hash = record.pop("record_hash")
                if record.get("sequence") != count:
                    return LedgerVerification(False, count, f"sequence mismatch at record {count}")
                if record.get("previous_hash") != previous_hash:
                    return LedgerVerification(False, count, f"chain mismatch at record {count}")
                if _hash(record) != stored_hash:
                    return LedgerVerification(False, count, f"content hash mismatch at record {count}")
                previous_hash = stored_hash
        except (json.JSONDecodeError, KeyError) as exc:
            return LedgerVerification(False, count, f"invalid record: {exc}")
        return LedgerVerification(True, count)
