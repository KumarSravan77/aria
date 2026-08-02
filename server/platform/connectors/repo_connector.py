from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable


class RepoConnector:
    """Read-only repository connector for local service repositories.

    This intentionally avoids network calls. It inspects local files and produces
    a service profile that can later be replaced by GitHub/GitLab/Bitbucket APIs.
    """

    def collect(self, repo_path: str) -> Dict[str, Any]:
        root = Path(repo_path)
        if not root.exists():
            return {"status": "unavailable", "reason": f"repo_path does not exist: {repo_path}"}

        files = {p.name.lower(): p for p in self._iter_files(root, depth=3)}
        language = self._detect_language(files)
        framework = self._detect_framework(root, files)
        cicd = self._detect_cicd(root)
        iac = self._detect_iac(root)
        observability = self._detect_observability(root, files)

        return {
            "status": "ok",
            "repo_path": str(root),
            "language": language,
            "framework": framework,
            "cicd": cicd,
            "iac": iac,
            "observability": observability,
            "repo_files_detected": sorted(list(files.keys()))[:40],
        }

    def _iter_files(self, root: Path, depth: int) -> Iterable[Path]:
        for path in root.rglob("*"):
            if path.is_file() and len(path.relative_to(root).parts) <= depth:
                yield path

    def _detect_language(self, files: Dict[str, Path]) -> str:
        if "pom.xml" in files or "build.gradle" in files or "build.gradle.kts" in files:
            return "java"
        if "package.json" in files:
            return "nodejs"
        if "requirements.txt" in files or "pyproject.toml" in files:
            return "python"
        if "go.mod" in files:
            return "go"
        if any(name.endswith(".csproj") for name in files):
            return "dotnet"
        if "gemfile" in files:
            return "ruby"
        return "unknown"

    def _detect_framework(self, root: Path, files: Dict[str, Path]) -> str:
        package_json = files.get("package.json")
        if package_json:
            try:
                data = json.loads(package_json.read_text())
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                if "next" in deps:
                    return "nextjs"
                if "express" in deps:
                    return "express"
                if "react" in deps:
                    return "react"
            except Exception:
                pass
        pom = files.get("pom.xml")
        gradle = files.get("build.gradle") or files.get("build.gradle.kts")
        content = ""
        for candidate in (pom, gradle):
            if candidate:
                try:
                    content += candidate.read_text(errors="ignore").lower()
                except Exception:
                    pass
        if "spring-boot" in content:
            return "spring-boot"
        if "fastapi" in " ".join(files.keys()) or (files.get("requirements.txt") and "fastapi" in files["requirements.txt"].read_text(errors="ignore").lower()):
            return "fastapi"
        return "unknown"

    def _detect_cicd(self, root: Path) -> Dict[str, Any]:
        return {
            "jenkins": (root / "Jenkinsfile").exists(),
            "github_actions": (root / ".github" / "workflows").exists(),
            "gitlab_ci": (root / ".gitlab-ci.yml").exists(),
            "azure_devops": any(root.glob("azure-pipelines*.yml")),
        }

    def _detect_iac(self, root: Path) -> Dict[str, Any]:
        return {
            "terraform": any(root.rglob("*.tf")),
            "helm": (root / "Chart.yaml").exists() or any(root.rglob("Chart.yaml")),
            "kustomize": (root / "kustomization.yaml").exists() or any(root.rglob("kustomization.yaml")),
            "kubernetes_manifests": any(root.rglob("*.yaml")) or any(root.rglob("*.yml")),
        }

    def _detect_observability(self, root: Path, files: Dict[str, Path]) -> Dict[str, Any]:
        text_sample = ""
        for name in ["pom.xml", "build.gradle", "requirements.txt", "package.json", "go.mod"]:
            p = files.get(name)
            if p:
                try:
                    text_sample += p.read_text(errors="ignore").lower()
                except Exception:
                    pass
        return {
            "otel_enabled": "opentelemetry" in text_sample or "otel" in text_sample,
            "prometheus_client": "prometheus" in text_sample,
            "dynatrace_hint": "dynatrace" in text_sample or "oneagent" in text_sample,
        }
