from pathlib import Path
import pytest
from server.ai_observability.feedback_loop import FeedbackStore
from server.ai_observability.runtime.session_recorder import AiRuntimeSessionRecorder

def test_feedback_is_trace_linked_and_summarized(tmp_path: Path):
    store = FeedbackStore(tmp_path / "feedback.jsonl")
    item = store.submit({"trace_id": "a" * 32, "session_id": "session-1", "answer_id": "answer-1",
                         "rating": -1, "category": "missing_source", "expected_source": "bank-risk-runbook"})
    assert item["record_hash"]
    assert store.summary()["knowledge_gap_count"] == 1
    approved = store.approve_for_evaluation(item["feedback_id"], "reviewer-1")
    assert approved["trace_id"] == item["trace_id"]
    assert approved["approval_hash"]

def test_feedback_rejects_raw_sensitive_payloads(tmp_path: Path):
    with pytest.raises(ValueError, match="sensitive"):
        FeedbackStore(tmp_path / "feedback.jsonl").submit({"trace_id": "trace-1", "answer_id": "answer-1",
            "rating": -1, "category": "other", "prompt": "private customer data"})

def test_runtime_session_propagates_trace_identity(tmp_path: Path):
    recorder = AiRuntimeSessionRecorder(tmp_path / "events.jsonl")
    session = recorder.start_session("incident-1")
    event = recorder.record(session["session_id"], "agent_completed", agent_id="retrieval-agent")
    assert event["trace_id"] == session["trace_id"]
    assert event["span_id"]
    assert recorder.summary(session["session_id"])["trace_id"] == session["trace_id"]
