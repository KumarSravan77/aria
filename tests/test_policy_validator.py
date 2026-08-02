from pathlib import Path
from server.healing.policy_validator import PolicyValidator

POLICY = Path(__file__).resolve().parents[1] / 'server' / 'healing' / 'policies' / 'self_healing_policy.yaml'


def test_policy_allows_dev_scale():
    p = PolicyValidator(POLICY)
    result = p.validate({'action':'scale_deployment','environment':'dev','replicas':3,'user':{'role':'sre'}})
    assert result['allowed'] is True


def test_policy_blocks_delete_namespace():
    p = PolicyValidator(POLICY)
    result = p.validate({'action':'delete_namespace','environment':'dev','user':{'role':'sre'}})
    assert result['allowed'] is False


def test_policy_requires_prod_scale_approval():
    p = PolicyValidator(POLICY)
    result = p.validate({'action':'scale_deployment','environment':'prod','replicas':3,'user':{'role':'sre'}})
    assert result['allowed'] is True
    assert result['requires_approval'] is True


def test_policy_blocks_non_privileged_role():
    p = PolicyValidator(POLICY)
    result = p.validate({'action':'scale_deployment','environment':'dev','user':{'role':'developer'}})
    assert result['allowed'] is False
