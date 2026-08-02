from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class KubernetesTroubleshootingRules:
    def classify(self, incident: dict[str, Any]) -> str:
        text = " ".join(str(v).lower() for v in incident.values())
        signals = " ".join(str(x).lower() for x in incident.get("signals", []))
        combined = f"{text} {signals}"
        if "crashloop" in combined:
            return "CrashLoopBackOff"
        if "oom" in combined:
            return "OOMKilled"
        if "pending" in combined or "unschedulable" in combined:
            return "Pending"
        if "evicted" in combined:
            return "Evicted"
        if "nodenotready" in combined or "node not ready" in combined:
            return "NodeNotReady"
        if "imagepull" in combined or "errimagepull" in combined:
            return "ImagePullBackOff"
        if "probe" in combined or "readiness" in combined or "liveness" in combined:
            return "ProbeFailure"
        return "GeneralKubernetes"

    def checklist(self, failure_mode: str) -> list[str]:
        checks = {
            "CrashLoopBackOff": ["check previous logs", "check restart count", "check exit code", "check OOMKilled flag", "check probes"],
            "OOMKilled": ["compare memory request/limit", "check node pressure", "review VPA recommendations", "inspect previous logs"],
            "Pending": ["check node selector", "check taints/tolerations", "check resource availability", "check PVC binding"],
            "Evicted": ["check node memory/disk/PID pressure", "review eviction events", "check QoS/resource requests"],
            "NodeNotReady": ["check node conditions", "check kubelet", "check disk/memory/PID pressure", "review node events"],
            "ImagePullBackOff": ["check image tag", "check registry credentials", "check imagePullSecrets", "check network"],
            "ProbeFailure": ["check probe path", "check timeout/failureThreshold", "compare startup time with probe config"],
        }
        return checks.get(failure_mode, ["collect pod description", "collect events", "collect logs", "check recent deployment"])
