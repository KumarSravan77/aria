from datetime import datetime, timezone
from typing import Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException

class KubernetesActions:
    def __init__(self):
        try:
            config.load_incluster_config()
            self.mode = "in_cluster"
        except Exception:
            try:
                config.load_kube_config()
                self.mode = "kubeconfig"
            except Exception:
                self.mode = "unconfigured"
        self.apps = client.AppsV1Api() if self.mode != "unconfigured" else None

    def execute(self, action: str, namespace: str, target: str, replicas: Optional[int] = None):
        if self.mode == "unconfigured":
            return {"status": "failed", "reason": "Kubernetes client is not configured"}
        if action == "scale_deployment":
            return self.scale_deployment(namespace, target, replicas or 2)
        if action == "restart_deployment":
            return self.restart_deployment(namespace, target)
        return {"status": "unsupported", "action": action}

    def scale_deployment(self, namespace: str, deployment: str, replicas: int):
        body = {"spec": {"replicas": replicas}}
        try:
            result = self.apps.patch_namespaced_deployment_scale(deployment, namespace, body)
            return {"status": "ok", "action": "scale_deployment", "namespace": namespace, "deployment": deployment, "replicas": result.spec.replicas, "mode": self.mode}
        except ApiException as e:
            return {"status": "failed", "reason": e.reason, "body": e.body}

    def restart_deployment(self, namespace: str, deployment: str):
        now = datetime.now(timezone.utc).isoformat()
        body = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "aria/restarted-at": now
                        }
                    }
                }
            }
        }
        try:
            self.apps.patch_namespaced_deployment(deployment, namespace, body)
            return {"status": "ok", "action": "restart_deployment", "namespace": namespace, "deployment": deployment, "restarted_at": now, "mode": self.mode}
        except ApiException as e:
            return {"status": "failed", "reason": e.reason, "body": e.body}
