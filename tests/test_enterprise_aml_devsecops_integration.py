from pathlib import Path
import json
import yaml

from server.platform.devsecops import DevSecOpsAgent
from server.platform.enterprise_event_bus import EnterpriseEventBusAgent
from server.platform.transaction_risk_scoring import TransactionRiskScoringAgent, score_transaction
from server.platform.service_review.agent import AIServiceReviewAgent


def test_enterprise_capabilities_registered():
    idx = yaml.safe_load(Path('specs/platform/spec-index.yaml').read_text())['spec_index']
    caps = set(idx['capabilities'])
    assert 'specs/capabilities/enterprise-event-bus-standards.yaml' in caps
    assert 'specs/capabilities/transaction-risk-scoring-standards.yaml' in caps
    assert 'specs/capabilities/devsecops-standards.yaml' in caps


def test_aml_golden_path_requires_eventing_risk_and_devsecops():
    gp = yaml.safe_load(Path('specs/golden-paths/python-aml-mlops.yaml').read_text())
    caps = set(gp['required_capabilities'])
    assert {'enterprise-event-bus-standards', 'transaction-risk-scoring-standards', 'devsecops-standards'} <= caps


def test_transaction_event_schema_exists():
    schema = json.loads(Path('platform/event-bus/transaction-event-v1.schema.json').read_text())
    assert 'transaction_id' in schema['required']
    assert 'idempotency_key' in schema['required']


def test_risk_scorer_scores_high_risk_transaction():
    txn = json.loads(Path('examples/enterprise_transaction_event.json').read_text())
    result = score_transaction(txn)
    assert result['risk_level'] == 'HIGH'
    assert result['recommended_action'] == 'BLOCK_AND_REVIEW'
    assert 'high_risk_country' in result['explanations']


def test_event_bus_agent_flags_missing_controls_for_transaction_producer():
    findings = EnterpriseEventBusAgent().review({'eventing': {'publishes_transaction_events': True}})
    ids = {f.id for f in findings}
    assert 'eventing-missing-topic' in ids
    assert 'eventing-missing-schema' in ids


def test_devsecops_agent_passes_when_all_tools_declared():
    profile = yaml.safe_load(Path('specs/service-profiles/payments-api.yaml').read_text())['service']
    findings = DevSecOpsAgent().review(profile)
    assert findings == []


def test_risk_scoring_agent_passes_for_payments_profile():
    profile = yaml.safe_load(Path('specs/service-profiles/payments-api.yaml').read_text())['service']
    findings = TransactionRiskScoringAgent().review(profile)
    assert findings == []


def test_service_review_runs_enterprise_agents():
    profile = yaml.safe_load(Path('specs/service-profiles/payments-api.yaml').read_text())['service']
    report = AIServiceReviewAgent().review(
        service_id='payments-api',
        environment='prod',
        service_profile=profile,
        slo_config={'availability_target': 99.9},
        telemetry_snapshot={'availability': 99.95, 'error_budget_remaining': 60},
    ).to_dict()
    assert 'enterprise-event-bus-agent' in report['agents_run']
    assert 'transaction-risk-scoring-agent' in report['agents_run']
    assert 'devsecops-agent' in report['agents_run']
    assert 'eventing' in report['scores']
    assert 'risk_scoring' in report['scores']
    assert 'devsecops' in report['scores']
