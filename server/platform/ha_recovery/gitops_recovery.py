from __future__ import annotations
from typing import Any


def cluster_bootstrap_plan(cluster_name: str, git_repo: str = "", argocd_namespace: str = "argocd") -> dict[str, Any]:
    return {
        "strategy": "gitops-app-of-apps-recovery", "cluster": cluster_name,
        "git_repo": git_repo or "<set GITOPS_REPO_URL>",
        "steps": [
            f"Bootstrap new cluster: kind create cluster --name {cluster_name}",
            f"Install Argo CD: kubectl create namespace {argocd_namespace} && helm install argocd ...",
            "Apply root app: kubectl apply -f gitops/root-app.yaml",
            "Argo CD syncs all application manifests from Git — no manual kubectl apply",
            "Validate all apps reach Healthy/Synced status",
            "Run smoke tests and validate RTO target",
        ],
        "safety_boundary": "GitOps recovery requires credentials. Use Sealed Secrets or External Secrets Operator.",
    }


def namespace_restore_plan(namespace: str, backup_name: str = "", git_path: str = "") -> dict[str, Any]:
    return {
        "namespace": namespace,
        "steps": [
            f"velero restore create --from-backup {backup_name or '<backup-name>'} --include-namespaces {namespace}",
            "Wait for Velero restore to complete: velero restore describe",
            f"Force Argo CD re-sync: argocd app sync {namespace}",
            "Validate pod health and SLO burn rate",
        ],
        "git_source": git_path or f"gitops/apps/{namespace}/",
        "safety_boundary": "Namespace restore is destructive. Requires approval before execution.",
    }
