from server.agent_runtime.contract import AgentRuntimeContract
from server.agent_runtime.enforcer import AgentRuntimeEnforcer
from server.ai_observability.runtime.cache_analyzer import PromptCacheAnalyzer
from server.ai_observability.runtime.flow_exporter import AgentFlowExporter
from server.ai_observability.runtime.replay_comparator import ReplayComparator


def test_runtime_contract_has_seven_parts():
    c = AgentRuntimeContract().as_dict()
    for key in ["identity", "permissions", "tools", "memory", "observability", "evaluation", "reversibility"]:
        assert key in c


def test_write_action_requires_approval_and_rollback():
    result = AgentRuntimeEnforcer().validate_action(
        "customer_record.change",
        tool="customer_record.change",
        approved=False,
        actor_id="aria-agent",
    )
    assert result["allowed"] is False
    assert "approval_required" in result["violations"]


def test_forbidden_direct_update_blocked():
    result = AgentRuntimeEnforcer().validate_action(
        "direct_customer_record_update",
        tool="direct_customer_record_update",
        approved=True,
        approval_id="APP-1",
        actor_id="aria-agent",
        before_state={},
        rollback_plan={},
    )
    assert result["allowed"] is False
    assert "forbidden_action" in result["violations"]


def test_cache_analyzer_detects_prefix_break():
    result = PromptCacheAnalyzer().prefix_match("abcdef", "abcXYZ")
    assert result["prefix_match_chars"] == 3
    assert result["break_position"] == 3


def test_flow_exporter_builds_nodes_edges():
    events = [{"event_id":"1","event_type":"session_started"},{"event_id":"2","event_type":"node_completed","node":"kafka"}]
    flow = AgentFlowExporter().export(events)
    assert flow["node_count"] == 2
    assert flow["edge_count"] == 1


def test_replay_comparator_detects_route_change():
    result = ReplayComparator().compare({"route":["metrics"]}, {"route":["metrics","kafka"]})
    assert result["route_changed"] is True
    assert "kafka" in result["added_nodes"]
