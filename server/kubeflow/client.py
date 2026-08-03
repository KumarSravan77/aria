from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ResourceDefinition:
    group: str
    version: str
    plural: str
    namespaced: bool = True


class KubeflowEvidenceClient:
    """Least-privilege reader for Kubeflow and Spark custom resources."""

    RESOURCES = {
        "Notebook": ResourceDefinition("kubeflow.org", "v1", "notebooks"),
        "Profile": ResourceDefinition("kubeflow.org", "v1", "profiles", False),
        "PodDefault": ResourceDefinition("kubeflow.org", "v1alpha1", "poddefaults"),
        "Pipeline": ResourceDefinition("pipelines.kubeflow.org", "v2beta1", "pipelines"),
        "PipelineVersion": ResourceDefinition("pipelines.kubeflow.org", "v2beta1", "pipelineversions"),
        "Experiment": ResourceDefinition("kubeflow.org", "v1beta1", "experiments"),
        "Trial": ResourceDefinition("kubeflow.org", "v1beta1", "trials"),
        "Suggestion": ResourceDefinition("kubeflow.org", "v1beta1", "suggestions"),
        "TrainJob": ResourceDefinition("trainer.kubeflow.org", "v1alpha1", "trainjobs"),
        "TrainingRuntime": ResourceDefinition("trainer.kubeflow.org", "v1alpha1", "trainingruntimes"),
        "ClusterTrainingRuntime": ResourceDefinition(
            "trainer.kubeflow.org", "v1alpha1", "clustertrainingruntimes", False
        ),
        "SparkApplication": ResourceDefinition(
            "sparkoperator.k8s.io", "v1beta2", "sparkapplications"
        ),
        "ScheduledSparkApplication": ResourceDefinition(
            "sparkoperator.k8s.io", "v1beta2", "scheduledsparkapplications"
        ),
    }

    def __init__(self, custom_api: Any | None = None):
        self._custom_api = custom_api

    def _load(self) -> tuple[Any | None, str | None]:
        if self._custom_api is not None:
            return self._custom_api, None
        try:
            from kubernetes import client, config

            try:
                config.load_incluster_config()
            except Exception:
                config.load_kube_config()
            return client.CustomObjectsApi(), None
        except Exception as exc:
            return None, str(exc)

    def supported_resources(self) -> list[str]:
        return sorted(self.RESOURCES)

    def get(self, kind: str, name: str, namespace: str = "default") -> dict[str, Any]:
        definition = self.RESOURCES.get(kind)
        if definition is None:
            return {
                "available": False,
                "error": f"unsupported Kubeflow resource kind: {kind}",
                "supported_resources": self.supported_resources(),
            }
        api, error = self._load()
        if api is None:
            return {"available": False, "error": error, "kind": kind, "name": name, "namespace": namespace}
        try:
            if definition.namespaced:
                resource = api.get_namespaced_custom_object(
                    definition.group, definition.version, namespace, definition.plural, name
                )
            else:
                resource = api.get_cluster_custom_object(
                    definition.group, definition.version, definition.plural, name
                )
            return {
                "available": True,
                "api_version": f"{definition.group}/{definition.version}",
                "kind": kind,
                "name": name,
                "namespace": namespace if definition.namespaced else None,
                "resource": self._sanitize(resource),
            }
        except Exception as exc:
            return {
                "available": False,
                "error": str(exc),
                "api_version": f"{definition.group}/{definition.version}",
                "kind": kind,
                "name": name,
                "namespace": namespace if definition.namespaced else None,
            }

    @staticmethod
    def _sanitize(resource: dict[str, Any]) -> dict[str, Any]:
        """Return operational fields only; never return Secret data or environment values."""
        metadata = resource.get("metadata", {}) or {}
        spec = resource.get("spec", {}) or {}
        return {
            "metadata": {
                "name": metadata.get("name"),
                "namespace": metadata.get("namespace"),
                "uid": metadata.get("uid"),
                "generation": metadata.get("generation"),
                "labels": metadata.get("labels", {}),
                "ownerReferences": metadata.get("ownerReferences", []),
            },
            "spec_summary": {
                "runtimeRef": spec.get("runtimeRef"),
                "pipelineRoot": spec.get("pipelineRoot"),
                "suspend": spec.get("suspend"),
            },
            "status": resource.get("status", {}) or {},
        }

