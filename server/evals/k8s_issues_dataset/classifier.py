from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class K8sIssueClassifier:
    def classify(self, issue: dict[str, Any]) -> str:
        text = " ".join(str(v).lower() for v in issue.values())
        symptoms = " ".join(str(x).lower() for x in issue.get("symptoms", []))
        combined = f"{text} {symptoms}"

        if "crashloop" in combined:
            return "CrashLoopBackOff"
        if "oom" in combined:
            return "OOMKilled"
        if "pending" in combined or "unschedulable" in combined:
            return "Pending"
        if "imagepull" in combined or "errimagepull" in combined:
            return "ImagePullBackOff"
        if "nodenotready" in combined or "node not ready" in combined:
            return "NodeNotReady"
        if "evicted" in combined:
            return "Evicted"
        if "mtls" in combined or "istio" in combined or "destinationrule" in combined:
            return "ServiceMesh"
        if "dns" in combined:
            return "DNSFailure"
        return "GeneralKubernetes"
