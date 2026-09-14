from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from training.common.manifests import DatasetManifest, canonical_hash, sha256_file, write_jsonl


SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


class DatasetValidationError(ValueError):
    pass


def redact_text(text: str) -> tuple[str, int]:
    redactions = 0
    output = text
    for pattern in SECRET_PATTERNS:
        output, count = pattern.subn("[REDACTED]", output)
        redactions += count
    return output, redactions


def _validate_messages(messages: Any) -> None:
    if not isinstance(messages, list) or not messages:
        raise DatasetValidationError("messages must be a non-empty list")
    roles = [item.get("role") for item in messages if isinstance(item, dict)]
    if "user" not in roles or "assistant" not in roles:
        raise DatasetValidationError("messages require user and assistant roles")
    for item in messages:
        if not isinstance(item, dict) or item.get("role") not in {"system", "user", "assistant", "tool"}:
            raise DatasetValidationError("invalid message role")
        if not isinstance(item.get("content"), str) or not item["content"].strip():
            raise DatasetValidationError("message content must be non-empty text")


def validate_record(record: dict[str, Any]) -> None:
    for field in ("id", "task", "messages", "provenance", "quality"):
        if field not in record:
            raise DatasetValidationError(f"missing required field: {field}")
    if not record["quality"].get("reviewed", False):
        raise DatasetValidationError("training records must be explicitly reviewed")
    if not record["provenance"].get("source_type"):
        raise DatasetValidationError("provenance.source_type is required")
    _validate_messages(record["messages"])


def sanitize_record(record: dict[str, Any]) -> tuple[dict[str, Any], int]:
    sanitized = json.loads(json.dumps(record))
    count = 0
    for message in sanitized["messages"]:
        message["content"], found = redact_text(message["content"])
        count += found
    sanitized["content_sha256"] = canonical_hash(sanitized["messages"])
    return sanitized, count


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                validate_record(record)
            except (json.JSONDecodeError, DatasetValidationError) as exc:
                raise DatasetValidationError(f"{path}:{line_number}: {exc}") from exc
            records.append(record)
    if not records:
        raise DatasetValidationError("dataset contains no records")
    return records


def deterministic_splits(records: list[dict[str, Any]], seed: int = 42) -> dict[str, list[dict[str, Any]]]:
    ordered = sorted(records, key=lambda item: item["id"])
    random.Random(seed).shuffle(ordered)
    total = len(ordered)
    test_count = max(1, round(total * 0.1)) if total >= 3 else 0
    validation_count = max(1, round(total * 0.1)) if total >= 2 else 0
    train_count = total - validation_count - test_count
    return {
        "train": ordered[:train_count],
        "validation": ordered[train_count : train_count + validation_count],
        "test": ordered[train_count + validation_count :],
    }


@dataclass(frozen=True)
class BuildResult:
    manifest_path: Path
    manifest: DatasetManifest
    duplicate_count: int
    redaction_count: int


def build_dataset(
    source: str | Path,
    output_dir: str | Path,
    *,
    name: str = "aria-sft",
    version: str = "v1",
    seed: int = 42,
) -> BuildResult:
    source_path = Path(source)
    output = Path(output_dir)
    seen: set[str] = set()
    sanitized_records: list[dict[str, Any]] = []
    duplicates = 0
    redactions = 0
    for record in read_jsonl(source_path):
        sanitized, count = sanitize_record(record)
        redactions += count
        fingerprint = sanitized["content_sha256"]
        if fingerprint in seen:
            duplicates += 1
            continue
        seen.add(fingerprint)
        sanitized_records.append(sanitized)

    splits = deterministic_splits(sanitized_records, seed)
    split_hashes: dict[str, str] = {}
    for split, records in splits.items():
        split_path = output / f"{split}.jsonl"
        write_jsonl(split_path, records)
        split_hashes[split] = sha256_file(split_path)

    manifest = DatasetManifest(
        name=name,
        version=version,
        source_path=str(source_path),
        source_sha256=sha256_file(source_path),
        record_count=len(sanitized_records),
        split_counts={key: len(value) for key, value in splits.items()},
        split_sha256=split_hashes,
        seed=seed,
    )
    manifest_path = output / "manifest.json"
    manifest.write(manifest_path)
    return BuildResult(manifest_path, manifest, duplicates, redactions)


def validate_built_dataset(manifest_path: str | Path) -> DatasetManifest:
    path = Path(manifest_path)
    payload = json.loads(path.read_text())
    manifest = DatasetManifest(**payload)
    for split, expected_hash in manifest.split_sha256.items():
        split_path = path.parent / f"{split}.jsonl"
        if not split_path.exists() or sha256_file(split_path) != expected_hash:
            raise DatasetValidationError(f"split hash mismatch: {split}")
        for record in read_jsonl(split_path) if split_path.stat().st_size else []:
            if any(pattern.search(message["content"]) for pattern in SECRET_PATTERNS for message in record["messages"]):
                raise DatasetValidationError(f"secret-like content remains in split: {split}")
    return manifest
