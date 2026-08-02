from __future__ import annotations

from typing import Any, Dict, List

from server.platform.cicd_pipeline.models import PipelineStage, PipelineTemplate


class CICDPipelineGenerator:
    """Generates ARIA golden-path CI/CD pipeline plans.

    The generator is intentionally provider-neutral. It returns a normalized
    stage contract plus concrete starter files for GitHub Actions or Jenkins.
    The same contract can later drive Azure DevOps, GitLab, Harness, or
    CloudBees templates.
    """

    name = "cicd-pipeline-generator"

    def generate(self, service_profile: Dict[str, Any]) -> PipelineTemplate:
        service_id = service_profile.get("service_id") or service_profile.get("name") or "unknown-service"
        language = (service_profile.get("language") or "unknown").lower()
        provider = (service_profile.get("cicd", {}) or {}).get("provider", "github-actions")
        deployment_target = (service_profile.get("deployment", {}) or {}).get("target", "kubernetes")
        stages = self._standard_stages(language, deployment_target)
        standards = {
            "required_gates": ["unit_tests", "sast", "sca", "container_scan", "sbom", "policy_as_code", "approval_for_prod"],
            "release_safety": ["dry_run", "canary_or_rolling", "rollback", "post_deploy_slo_check"],
            "observability": ["otel_validation", "dashboard_validation", "alert_validation"],
            "security": ["secret_scan", "image_scan", "artifact_signing", "provenance"],
        }
        generated_files = self._generated_files(provider, language, deployment_target, service_id)
        return PipelineTemplate(service_id, provider, language, deployment_target, stages, generated_files, standards)

    def _standard_stages(self, language: str, deployment_target: str) -> List[PipelineStage]:
        build_tools = {
            "java": ["maven_or_gradle"],
            "python": ["pip", "pytest"],
            "node": ["npm", "jest"],
            "go": ["go test", "go build"],
            ".net": ["dotnet test", "dotnet build"],
        }.get(language, ["language_specific_builder"])
        return [
            PipelineStage("checkout", "Fetch source and metadata", tools=["git"]),
            PipelineStage("detect", "Detect language, framework, IaC, deployment model", tools=["aria-discovery"]),
            PipelineStage("build", "Compile/package service", tools=build_tools),
            PipelineStage("unit_tests", "Run unit tests with coverage gate", gates=["coverage_threshold"]),
            PipelineStage("quality", "Run linting and code quality checks", tools=["sonarqube", "ruff/eslint/checkstyle"]),
            PipelineStage("security", "Run SAST/SCA/secrets/container scanning", gates=["no_critical_vulnerabilities"], tools=["gitleaks", "trivy", "snyk_or_dependency_check"]),
            PipelineStage("sbom", "Generate SBOM and provenance", gates=["sbom_attached"], tools=["syft", "cosign"]),
            PipelineStage("package", "Build immutable artifact/container image", tools=["docker/buildkit"]),
            PipelineStage("policy", "Validate Kubernetes, OTel, and security policies", gates=["opa_or_kyverno_pass"], tools=["conftest", "kubeconform", "aria-standards"]),
            PipelineStage("deploy_dev", "Deploy to development environment", tools=[deployment_target]),
            PipelineStage("smoke_tests", "Run post-deploy smoke tests", gates=["smoke_pass"]),
            PipelineStage("deploy_stage", "Deploy to staging with release safety checks", gates=["approval_if_required"]),
            PipelineStage("slo_check", "Check SLI/SLO and error-budget health after deploy", gates=["no_fast_burn"]),
            PipelineStage("deploy_prod", "Production deploy using canary/rolling strategy", gates=["prod_approval", "rollback_ready"]),
            PipelineStage("post_deploy_ai_review", "Trigger ARIA issue/release review agent", tools=["aria-issue-response-agent"]),
        ]

    def _generated_files(self, provider: str, language: str, deployment_target: str, service_id: str) -> Dict[str, str]:
        if provider in {"jenkins", "cloudbees"}:
            return {"Jenkinsfile": self._jenkinsfile(language, deployment_target, service_id)}
        return {".github/workflows/aria-golden-path.yml": self._github_actions(language, deployment_target, service_id)}

    def _github_actions(self, language: str, deployment_target: str, service_id: str) -> str:
        return f'''name: ARIA Golden Path CI/CD

on:
  pull_request:
  push:
    branches: [ main ]

jobs:
  build-test-secure-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - name: ARIA detect service
        run: python scripts/aria_detect.py --service {service_id} || true
      - name: Build and unit test
        run: echo "Run {language} build and tests here"
      - name: Secrets scan
        run: echo "Run gitleaks here"
      - name: SAST and dependency scan
        run: echo "Run SAST/SCA here"
      - name: Container scan
        run: echo "Run Trivy here"
      - name: Generate SBOM
        run: echo "Run Syft/CycloneDX here"
      - name: Policy validation
        run: echo "Run kubeconform/conftest/Kyverno policy checks here"
      - name: Deploy with rollback guard
        run: echo "Deploy to {deployment_target} using canary/rolling strategy"
      - name: ARIA post-deploy AI review
        run: echo "Call /aria/platform/issues/analyze with deployment event"
'''

    def _jenkinsfile(self, language: str, deployment_target: str, service_id: str) -> str:
        return f'''pipeline {{
  agent any
  options {{ timestamps() }}
  stages {{
    stage('ARIA Detect') {{ steps {{ sh 'python scripts/aria_detect.py --service {service_id} || true' }} }}
    stage('Build') {{ steps {{ sh 'echo Run {language} build here' }} }}
    stage('Unit Tests') {{ steps {{ sh 'echo Run unit tests and coverage gate' }} }}
    stage('Security Gates') {{ steps {{ sh 'echo Run secrets/SAST/SCA/container scans' }} }}
    stage('SBOM + Provenance') {{ steps {{ sh 'echo Generate SBOM and sign artifacts' }} }}
    stage('Policy Validation') {{ steps {{ sh 'echo Validate Kubernetes/OTel/security policies' }} }}
    stage('Deploy') {{ steps {{ sh 'echo Deploy to {deployment_target} with rollback guard' }} }}
    stage('ARIA Post Deploy AI Review') {{ steps {{ sh 'echo Call ARIA issue response agent' }} }}
  }}
}}
'''
