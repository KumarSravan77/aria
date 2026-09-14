from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation.model_scorecard import evaluate_file, evaluate_records
from models.registry.local_registry import register_model
from models.registry.promotion import compare_for_promotion, evaluate_promotion
from training.common.data_pipeline import (
    DatasetValidationError,
    build_dataset,
    redact_text,
    validate_built_dataset,
)
from training.common.data_quality import audit_dataset, enforce_audit
from training.sft.train import build_plan, load_config


ROOT = Path(__file__).resolve().parents[1]


def test_dataset_build_is_versioned_deduplicated_and_redacted(tmp_path: Path):
    source = tmp_path / "source.jsonl"
    record = {
        "id": "one",
        "task": "rca",
        "messages": [{"role": "user", "content": "token=abc123 investigate"}, {"role": "assistant", "content": "Need evidence"}],
        "provenance": {"source_type": "reviewed_synthetic"},
        "quality": {"reviewed": True},
    }
    duplicate = {**record, "id": "two"}
    third = {**record, "id": "three", "messages": [{"role": "user", "content": "different"}, {"role": "assistant", "content": "Need more evidence"}]}
    source.write_text("\n".join(json.dumps(item) for item in (record, duplicate, third)) + "\n")
    result = build_dataset(source, tmp_path / "processed")
    assert result.duplicate_count == 1
    assert result.redaction_count == 2
    assert result.manifest.record_count == 2
    assert validate_built_dataset(result.manifest_path).source_sha256 == result.manifest.source_sha256


def test_unreviewed_training_data_is_rejected(tmp_path: Path):
    source = tmp_path / "source.jsonl"
    source.write_text(json.dumps({"id": "x", "task": "rca", "messages": [{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}], "provenance": {"source_type": "prod"}, "quality": {"reviewed": False}}) + "\n")
    with pytest.raises(DatasetValidationError):
        build_dataset(source, tmp_path / "output")


def test_secret_redaction():
    output, count = redact_text("password=hunter2 and AKIAABCDEFGHIJKLMNOP")
    assert "hunter2" not in output
    assert "AKIA" not in output
    assert count == 2


def test_scorecard_and_promotion_gate():
    scorecard = evaluate_file(ROOT / "evaluation/fixtures/smoke_predictions.jsonl", "smoke")
    assert scorecard.rca_correctness == 1.0
    assert scorecard.safety == 1.0
    assert evaluate_promotion(scorecard.__dict__).approved is True
    unsafe = evaluate_records([{"response": "kubectl delete namespace prod", "expected_terms": [], "sources": ["x"]}], "unsafe")
    decision = evaluate_promotion(unsafe.__dict__)
    assert decision.approved is False
    assert any("safety" in failure for failure in decision.failures)


def test_registry_entry_is_immutable(tmp_path: Path):
    artifact = tmp_path / "adapter"
    artifact.mkdir()
    (artifact / "adapter.json").write_text("{}")
    dataset = tmp_path / "dataset.json"
    dataset.write_text(json.dumps({"name": "aria", "version": "v1", "source_sha256": "abc"}))
    scorecard = tmp_path / "scorecard.json"
    scorecard.write_text(json.dumps({"model": "base", "benchmark": "v1", "safety": 1.0}))
    entry = register_model(artifact, tmp_path / "registry", name="aria-model", version="1", base_model="Qwen/Qwen2.5-0.5B-Instruct", dataset_manifest=dataset, scorecard=scorecard)
    assert json.loads(entry.read_text())["stage"] == "candidate"
    with pytest.raises(FileExistsError):
        register_model(artifact, tmp_path / "registry", name="aria-model", version="1", base_model="Qwen/Qwen2.5-0.5B-Instruct", dataset_manifest=dataset, scorecard=scorecard)


def test_relative_promotion_gate_requires_quality_gain_and_latency_control():
    baseline = {"rca_correctness": 0.80, "evidence_groundedness": 1.0, "structured_output": 1.0,
                "safety": 1.0, "uncertainty": 1.0, "p95_ms": 1000}
    improved = {**baseline, "rca_correctness": 0.84, "p95_ms": 1050}
    assert compare_for_promotion(baseline, improved).approved is True
    slower_worse = {**baseline, "rca_correctness": 0.79, "p95_ms": 1300}
    decision = compare_for_promotion(baseline, slower_worse)
    assert decision.approved is False
    assert any("rca_delta" in failure for failure in decision.failures)
    assert any("latency_regression" in failure for failure in decision.failures)


def test_training_plan_validates_dataset_manifest(tmp_path: Path):
    processed = tmp_path / "processed"
    build_dataset(ROOT / "datasets/finetuning/raw/aria_sft_seed.jsonl", processed)
    config = load_config(ROOT / "training/configs/lora-local-smoke.yaml")
    config["dataset"] = {
        "train": str(processed / "train.jsonl"),
        "validation": str(processed / "validation.jsonl"),
        "manifest": str(processed / "manifest.json"),
    }
    plan = build_plan(config)
    assert plan["method"] == "lora"
    assert plan["train_records"] == 2


def test_self_hosted_gateway_assets_are_present():
    backend = (ROOT / "k8s/ai-gateway/vllm-backend.yaml").read_text()
    route = (ROOT / "k8s/ai-gateway/route-self-hosted.yaml").read_text()
    compose = (ROOT / "serving/vllm/docker-compose.vllm.yml").read_text()
    assert "aria-vllm" in backend
    assert "aria-private" in route
    assert "vllm/vllm-openai:v0.6.4.post1" in compose


def test_v2_dataset_is_balanced_audited_and_not_benchmark_contaminated(tmp_path: Path):
    source = ROOT / "datasets/finetuning/raw/aria_sft_v2.jsonl"
    benchmark = ROOT / "evaluation/benchmarks/aria_eval_v2.jsonl"
    report = audit_dataset(source, benchmark)
    enforce_audit(report)
    assert report.record_count == 16
    assert report.benchmark_count == 10
    assert report.minimum_quality_score >= 0.9
    assert set(report.task_distribution) >= {"rca", "safety", "monitoring", "tool_selection"}
    assert report.contamination_pairs == []

    result = build_dataset(source, tmp_path / "processed", version="v2")
    assert result.manifest.split_counts == {"train": 12, "validation": 2, "test": 2}


def test_v2_experiment_evidence_is_rejected_and_revision_resolved():
    manifest = json.loads((ROOT / "models/manifests/aria-qwen-lora-v2-experiment.json").read_text())
    assert len(manifest["base_model"]["resolved_revision"]) == 40
    assert manifest["promotion"]["decision"] == "rejected"
    assert manifest["benchmark"]["candidate_rca_correctness"] < manifest["benchmark"]["baseline_rca_correctness"]
