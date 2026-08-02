from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


class CICDConnector:
    """Extracts CI/CD governance signals from local pipeline files."""

    def collect(self, repo_path: str) -> Dict[str, Any]:
        root = Path(repo_path)
        if not root.exists():
            return {"status": "unavailable", "reason": f"repo_path does not exist: {repo_path}"}
        candidates = list(root.glob("Jenkinsfile")) + list(root.glob(".github/workflows/*.yml")) + list(root.glob(".github/workflows/*.yaml")) + list(root.glob("azure-pipelines*.yml")) + list(root.glob(".gitlab-ci.yml"))
        content = "\n".join(p.read_text(errors="ignore").lower() for p in candidates if p.is_file())
        return {
            "status": "ok",
            "pipeline_files": [str(p.relative_to(root)) for p in candidates],
            "sast": any(token in content for token in ["sonarqube", "sonar", "semgrep", "codeql"]),
            "sca": any(token in content for token in ["snyk", "dependency-check", "trivy fs", "maven dependency"]),
            "container_scan": any(token in content for token in ["trivy image", "grype", "twistlock", "prisma"]),
            "secret_scan": any(token in content for token in ["gitleaks", "trufflehog", "detect-secrets"]),
            "rollback": any(token in content for token in ["rollback", "argo rollback", "helm rollback"]),
            "canary": any(token in content for token in ["canary", "rollouts", "traffic-split"]),
            "approval_gate": any(token in content for token in ["input", "approval", "environment:", "manualvalidation"]),
        }
