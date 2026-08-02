from __future__ import annotations

from server.platform.connectors.repo_connector import RepoConnector


class GitRepoConnector:
    """Compatibility wrapper for repo scanning tests and callers."""

    def scan(self, repo_path: str) -> dict:
        data = RepoConnector().collect(repo_path)
        iac = data.get("iac", {})
        cicd = data.get("cicd", {})
        return {
            **data,
            "ci_cd": any(bool(v) for v in cicd.values()) if isinstance(cicd, dict) else False,
            "terraform": bool(iac.get("terraform")),
            "kubernetes": bool(iac.get("kubernetes_manifests") or iac.get("helm") or iac.get("kustomize")),
        }
