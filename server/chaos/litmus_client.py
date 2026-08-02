from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
except Exception:  # pragma: no cover - optional dependency for slim/local test installs
    client = None
    config = None
    class ApiException(Exception):
        status = None
        reason = "kubernetes package unavailable"
        body = None

from server.chaos.experiment_catalog import get_experiment
from server.utils_time import utc_now


@dataclass
class LitmusChaosClient:
    """Small LitmusChaos ChaosEngine client with graceful degradation.

    It never throws when Kubernetes or Litmus is unavailable. Instead it returns
    structured `available: False` responses so dry-runs and local demos keep working.
    """

    def __post_init__(self):
        self.mode = "unconfigured"
        self.custom_api = None
        if client is None or config is None:
            return
        try:
            config.load_incluster_config()
            self.mode = "in_cluster"
        except Exception:
            try:
                config.load_kube_config()
                self.mode = "kubeconfig"
            except Exception:
                self.mode = "unconfigured"
        if self.mode != "unconfigured":
            self.custom_api = client.CustomObjectsApi()

    def build_engine(self, experiment: str, namespace: str, service: str, app_label: str, duration_seconds: int | None = None) -> dict[str, Any]:
        definition = get_experiment(experiment)
        duration = str(duration_seconds or definition.default_duration_seconds)
        env = [{"name": "TOTAL_CHAOS_DURATION", "value": duration}]
        if experiment == "pod-delete":
            env.extend([{"name": "CHAOS_INTERVAL", "value": "10"}, {"name": "FORCE", "value": "false"}])
        elif experiment == "cpu-hog":
            env.append({"name": "CPU_CORES", "value": "1"})
        elif experiment == "memory-hog":
            env.append({"name": "MEMORY_CONSUMPTION", "value": "256"})
        elif experiment == "network-latency":
            env.extend([{"name": "NETWORK_LATENCY", "value": "1200"}, {"name": "DESTINATION_HOSTS", "value": ""}])
        elif experiment == "dns-failure":
            env.append({"name": "TARGET_HOSTNAMES", "value": "kubernetes.default.svc.cluster.local"})

        safe_name = f"{service}-{experiment}".replace("_", "-").replace(".", "-")[:60]
        return {
            "apiVersion": "litmuschaos.io/v1alpha1",
            "kind": "ChaosEngine",
            "metadata": {
                "name": safe_name,
                "namespace": namespace,
                "labels": {
                    "app.kubernetes.io/managed-by": "aria",
                    "aria/chaos-experiment": experiment,
                },
            },
            "spec": {
                "appinfo": {"appns": namespace, "applabel": app_label, "appkind": "deployment"},
                "chaosServiceAccount": "litmus-admin",
                "engineState": "active",
                "experiments": [
                    {"name": definition.litmus_experiment, "spec": {"components": {"env": env}}}
                ],
            },
        }

    def run_experiment(self, experiment: str, namespace: str, service: str, app_label: str, duration_seconds: int | None = None, dry_run: bool = True) -> dict[str, Any]:
        definition = get_experiment(experiment)
        manifest = self.build_engine(experiment, namespace, service, app_label, duration_seconds)
        base = {
            "available": self.mode != "unconfigured",
            "mode": self.mode,
            "experiment": definition.to_dict(),
            "namespace": namespace,
            "service": service,
            "dry_run": dry_run,
            "manifest": manifest,
            "started_at": utc_now().isoformat(),
        }
        if dry_run:
            return {**base, "executed": False, "message": "Dry run only. Litmus ChaosEngine manifest was generated but not applied."}
        if self.custom_api is None:
            return {**base, "executed": False, "available": False, "reason": "Kubernetes client is not configured. Install/configure kubectl or run inside the cluster."}
        try:
            result = self.custom_api.create_namespaced_custom_object(
                group="litmuschaos.io",
                version="v1alpha1",
                namespace=namespace,
                plural="chaosengines",
                body=manifest,
            )
            return {**base, "executed": True, "result_name": result.get("metadata", {}).get("name")}
        except ApiException as exc:
            if exc.status == 409:
                try:
                    result = self.custom_api.patch_namespaced_custom_object(
                        group="litmuschaos.io",
                        version="v1alpha1",
                        namespace=namespace,
                        plural="chaosengines",
                        name=manifest["metadata"]["name"],
                        body=manifest,
                    )
                    return {**base, "executed": True, "updated": True, "result_name": result.get("metadata", {}).get("name")}
                except ApiException as patch_exc:
                    return {**base, "executed": False, "status": patch_exc.status, "reason": patch_exc.reason, "body": patch_exc.body}
            return {**base, "executed": False, "status": exc.status, "reason": exc.reason, "body": exc.body}
