from __future__ import annotations

from typing import Any, Dict, List, Optional

from server.platform.connectors.models import NormalizedServiceSnapshot
from server.platform.connectors.repo_connector import RepoConnector
from server.platform.connectors.kubernetes_connector import KubernetesConnector
from server.platform.connectors.cicd_connector import CICDConnector
from server.platform.connectors.telemetry_connector import TelemetryConnector


class ServiceSnapshotBuilder:
    """Builds one canonical service snapshot from self-service inputs/connectors."""

    def __init__(self) -> None:
        self.repo = RepoConnector()
        self.k8s = KubernetesConnector()
        self.cicd = CICDConnector()
        self.telemetry = TelemetryConnector()

    def build(
        self,
        service_id: str,
        environment: str,
        service_profile: Optional[Dict[str, Any]] = None,
        repo_path: Optional[str] = None,
        kubernetes_objects: Optional[List[Dict[str, Any]]] = None,
        slo_config: Optional[Dict[str, Any]] = None,
        telemetry_snapshot: Optional[Dict[str, Any]] = None,
        incident_history: Optional[List[Dict[str, Any]]] = None,
        latest_drift_summary: Optional[Dict[str, Any]] = None,
    ) -> NormalizedServiceSnapshot:
        profile = dict(service_profile or {})
        source_status: Dict[str, str] = {}

        if repo_path:
            repo_data = self.repo.collect(repo_path)
            source_status["repo"] = repo_data.get("status", "unknown")
            if repo_data.get("status") == "ok":
                profile.setdefault("language", repo_data.get("language"))
                profile.setdefault("framework", repo_data.get("framework"))
                profile.setdefault("observability", {}).update(repo_data.get("observability", {}))
                profile.setdefault("iac", repo_data.get("iac", {}))

                cicd_data = self.cicd.collect(repo_path)
                source_status["cicd"] = cicd_data.get("status", "unknown")
                profile.setdefault("cicd", {}).update({k: v for k, v in cicd_data.items() if k != "status"})

        if kubernetes_objects is not None:
            k8s_data = self.k8s.collect_from_objects(kubernetes_objects)
            source_status["kubernetes"] = k8s_data.get("status", "unknown")
            profile.setdefault("kubernetes", {}).update(k8s_data.get("kubernetes", {}))

        telemetry_data = self.telemetry.collect(telemetry_snapshot, slo_config)
        source_status["telemetry"] = telemetry_data.get("status", "unknown")

        return NormalizedServiceSnapshot(
            service_id=service_id,
            environment=environment,
            service_profile=profile,
            slo_config=slo_config,
            telemetry_snapshot=telemetry_data.get("telemetry_snapshot") if telemetry_snapshot else telemetry_snapshot,
            incident_history=incident_history or [],
            latest_drift_summary=latest_drift_summary,
            source_status=source_status,
        )
