from __future__ import annotations

import json
from pathlib import Path

import pytest

from server.governance.evidence_ledger import AITransactionEvidence, EvidenceLedger, GENESIS_HASH


def sample_evidence(**changes):
    values = {
        "trace_id": "trace-1",
        "request_id": "request-1",
        "domain": "capital-markets",
        "application": "risk-assistant",
        "agent_id": "risk-agent",
        "workload_identity": "spiffe://example.ca/ai/risk-agent",
        "model": {"provider": "self-hosted", "deployment": "aria-private", "region": "ca-central"},
        "policy": {"bundle_version": "policy-1", "decision": "ALLOW", "risk_tier": "HIGH"},
        "guardrails": {"prompt_injection": "PASS", "pii": "PASS", "groundedness": "PASS"},
        "lineage": {"dataset": "aria-sft-v1", "model": "aria-qwen-lora-0.1.0"},
        "latency_ms": {"gateway": 17.0, "policy": 3.0, "model": 200.0},
        "evaluation": {"safety": 1.0},
    }
    values.update(changes)
    return AITransactionEvidence(**values)


def test_ledger_builds_and_verifies_hash_chain(tmp_path: Path):
    ledger = EvidenceLedger(tmp_path / "evidence.jsonl")
    first = ledger.append(sample_evidence())
    second = ledger.append(sample_evidence(trace_id="trace-2", request_id="request-2"))
    assert first["previous_hash"] == GENESIS_HASH
    assert second["previous_hash"] == first["record_hash"]
    assert ledger.verify().valid is True
    assert ledger.verify().record_count == 2


def test_ledger_detects_tampering(tmp_path: Path):
    ledger = EvidenceLedger(tmp_path / "evidence.jsonl")
    ledger.append(sample_evidence())
    record = json.loads(ledger.path.read_text())
    record["policy"]["decision"] = "DENY"
    ledger.path.write_text(json.dumps(record) + "\n")
    verification = ledger.verify()
    assert verification.valid is False
    assert "hash mismatch" in verification.error


def test_ledger_rejects_prompt_or_credentials(tmp_path: Path):
    ledger = EvidenceLedger(tmp_path / "evidence.jsonl")
    with pytest.raises(ValueError, match="sensitive field"):
        ledger.append(sample_evidence(evaluation={"prompt": "private text"}))
