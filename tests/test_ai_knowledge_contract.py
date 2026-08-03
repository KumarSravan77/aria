from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_runbook_and_portable_skill_contracts():
    runbook = (ROOT / "docs/runbooks/payments-cicd-deployment-failure.md").read_text()
    for field in ["service:", "team:", "doc_type: runbook", "version:", "required_permissions:"]:
        assert field in runbook
    for section in ["## Evidence collection", "## Decision tree", "## Recovery validation", "## Evidence and audit record"]:
        assert section in runbook
    for name in ["aria-investigate-incident", "aria-author-runbook", "aria-add-mcp-connector"]:
        skill = ROOT / "skills" / name / "SKILL.md"
        assert skill.is_file()
        assert f"name: {name}" in skill.read_text()
        assert (ROOT / "skills" / name / "agents/openai.yaml").is_file()


def test_readme_exposes_ai_architecture():
    readme = (ROOT / "README.md").read_text()
    assert "## AI architecture and operating model" in readme
    assert "verified memory" in readme
    assert "docs/runbooks/" in readme
