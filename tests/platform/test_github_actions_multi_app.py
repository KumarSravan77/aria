import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_application_catalog_has_multiple_apps():
    catalog = yaml.safe_load((ROOT / "config" / "applications.yaml").read_text())
    assert len(catalog["applications"]) >= 2
    for app in catalog["applications"]:
        assert app["service_id"]
        assert app["app_path"]
        assert app["language"] in {"java", "node", "python", "go", "dotnet", "ruby"}


def test_github_actions_matrix_script_outputs_include_matrix():
    output = subprocess.check_output(
        [sys.executable, "scripts/github_actions_matrix.py", "config/applications.yaml"],
        cwd=ROOT,
        text=True,
    ).strip()
    assert output.startswith("matrix=")
    matrix = json.loads(output.split("=", 1)[1])
    assert "include" in matrix
    assert len(matrix["include"]) >= 2
    assert {"service_id", "app_path", "language", "dockerfile"}.issubset(matrix["include"][0])


def test_required_github_actions_workflows_exist():
    workflows = ROOT / ".github" / "workflows"
    required = [
        "multi-app-platform-ci.yml",
        "reusable-app-ci.yml",
        "reusable-security-scan.yml",
        "reusable-docker-build.yml",
        "reusable-aria-service-review.yml",
        "ai-devops-on-failure.yml",
    ]
    for name in required:
        assert (workflows / name).exists(), name
