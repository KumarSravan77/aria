from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = ROOT / "platform" / "aws-foundation"


def test_standard_forbids_static_credentials_and_admin_policies():
    standard = yaml.safe_load((FOUNDATION / "project-standard.yaml").read_text())
    defaults = standard["defaults"]
    assert defaults["authentication"] == "github-oidc"
    assert defaults["static_aws_keys_allowed"] is False
    assert defaults["exact_repository_subject_required"] is True
    assert set(defaults["forbidden_managed_policies"]) == {
        "AdministratorAccess", "PowerUserAccess"
    }


def test_every_registered_project_has_cost_ownership():
    projects = yaml.safe_load((FOUNDATION / "project-standard.yaml").read_text())["projects"]
    assert projects
    for project in projects:
        assert project["repository"].startswith("KumarSravan77/")
        assert project["environment"] and project["owner"] and project["cost_center"]
        assert project["monthly_budget_usd"] > 0


def test_terraform_scopes_oidc_and_provisions_cost_controls():
    terraform = (FOUNDATION / "terraform" / "main.tf").read_text()
    assert "sts:AssumeRoleWithWebIdentity" in terraform
    assert 'variable = "token.actions.githubusercontent.com:aud"' in terraform
    assert 'variable = "token.actions.githubusercontent.com:sub"' in terraform
    assert "environment:${var.environment}" in terraform
    assert 'resource "aws_budgets_budget" "project"' in terraform
    assert 'resource "aws_ce_anomaly_monitor" "account_services"' in terraform
    assert 'resource "aws_ce_anomaly_subscription" "account_services"' in terraform


def test_reusable_workflow_uses_oidc_and_wrong_account_guard():
    workflow = yaml.safe_load((ROOT / ".github/workflows/reusable-aws-oidc.yml").read_text())
    trigger = workflow.get("on", workflow.get(True))  # PyYAML 1.1 treats `on` as boolean.
    assert "workflow_call" in trigger
    assert workflow["permissions"] == {"contents": "read", "id-token": "write"}
    action = next(step for step in workflow["jobs"]["identity"]["steps"] if "uses" in step)
    assert action["uses"].startswith("aws-actions/configure-aws-credentials@")
    assert action["with"]["allowed-account-ids"]
    assert "aws-access-key-id" not in action["with"]
    assert "aws-secret-access-key" not in action["with"]
