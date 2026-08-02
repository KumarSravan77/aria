from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class KubernetesDiagnosticClient:
    """Read-only Kubernetes diagnostic client. Never mutates cluster state."""
    namespace: str = "default"

    def _load(self) -> tuple[Any, Any, str | None]:
        try:
            from kubernetes import client, config
            try:
                config.load_incluster_config()
                mode = "in_cluster"
            except Exception:
                config.load_kube_config()
                mode = "kubeconfig"
            return client, client.CoreV1Api(), mode
        except Exception as exc:
            return None, None, str(exc)

    def describe_pod(self, pod_name: str, namespace: str | None = None) -> dict[str, Any]:
        _, api, mode = self._load()
        ns = namespace or self.namespace
        if api is None:
            return {"available": False, "error": mode, "pod": pod_name, "namespace": ns}
        try:
            pod = api.read_namespaced_pod(pod_name, ns)
            statuses = []
            for s in pod.status.container_statuses or []:
                state = {}
                if s.state and s.state.waiting:
                    state = {"waiting": {"reason": s.state.waiting.reason, "message": s.state.waiting.message}}
                if s.state and s.state.terminated:
                    state = {"terminated": {"reason": s.state.terminated.reason, "exit_code": s.state.terminated.exit_code}}
                statuses.append({"name": s.name, "restart_count": s.restart_count, "ready": s.ready, "state": state})
            return {"available": True, "pod": pod_name, "namespace": ns, "phase": pod.status.phase, "node": pod.spec.node_name, "container_statuses": statuses}
        except Exception as exc:
            return {"available": False, "error": str(exc), "pod": pod_name, "namespace": ns}

    def pod_events(self, pod_name: str, namespace: str | None = None) -> dict[str, Any]:
        _, api, mode = self._load()
        ns = namespace or self.namespace
        if api is None:
            return {"available": False, "error": mode, "events": []}
        try:
            events = api.list_namespaced_event(ns, field_selector=f"involvedObject.name={pod_name}")
            return {"available": True, "events": [{"reason": e.reason, "message": e.message, "type": e.type, "count": e.count} for e in events.items]}
        except Exception as exc:
            return {"available": False, "error": str(exc), "events": []}

    def previous_logs(self, pod_name: str, namespace: str | None = None, container: str | None = None, tail_lines: int = 80) -> dict[str, Any]:
        _, api, mode = self._load()
        ns = namespace or self.namespace
        if api is None:
            return {"available": False, "error": mode, "logs": ""}
        try:
            logs = api.read_namespaced_pod_log(pod_name, ns, container=container, previous=True, tail_lines=tail_lines)
            return {"available": True, "logs": logs}
        except Exception as exc:
            return {"available": False, "error": str(exc), "logs": ""}
