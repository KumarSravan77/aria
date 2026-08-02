class IncidentAnalyzer:
    def analyze(self, incident: dict) -> dict:
        symptoms = [s.lower() for s in incident.get("symptoms", [])]
        signals = incident.get("signals", {}) or {}
        service = incident.get("service", "unknown-service")
        recent_deployment = bool(signals.get("recent_deployment", False))
        cpu = float(str(signals.get("cpu_percent", 0)).replace("%", "") or 0)
        error_rate = float(str(signals.get("error_rate_percent", 0)).replace("%", "") or 0)
        p95 = float(str(signals.get("p95_latency_ms", 0)).replace("ms", "") or 0)

        findings = []
        likely_cause = "unknown"
        recommended = "continue_investigation"

        if p95 >= 1000 or "high latency" in symptoms:
            findings.append("High latency detected")
        if error_rate >= 5 or "increased 5xx" in symptoms:
            findings.append("Elevated error rate detected")
        if cpu >= 80:
            findings.append("CPU saturation detected")
            likely_cause = "resource_saturation"
            recommended = "scale_deployment"
        if recent_deployment:
            findings.append("Recent deployment found in incident window")
            if error_rate >= 5:
                likely_cause = "deployment_regression"
                recommended = "rollback_or_scale_after_validation"

        if likely_cause == "unknown" and findings:
            likely_cause = "application_or_dependency_degradation"

        confidence = "medium" if findings else "low"
        summary = self._build_summary(service, findings, likely_cause, recommended)
        rag_query = f"{service} incident {' '.join(symptoms)} likely cause {likely_cause} recommended {recommended}"

        # Keep both canonical and backward-compatible keys so API, war-room, and RCA
        # consumers receive consistent incident evidence and cause information.
        return {
            "summary": summary,
            "evidence": findings,
            "findings": findings,
            "probable_cause": likely_cause,
            "likely_cause": likely_cause,
            "confidence": confidence,
            "recommended_next_step": recommended,
            "rag_query": rag_query,
        }

    def _build_summary(self, service: str, findings: list[str], likely_cause: str, recommended: str) -> str:
        if not findings:
            return f"No strong incident signal has been identified yet for {service}. Continue investigation."
        finding_text = "; ".join(findings)
        return (
            f"{service} shows {finding_text}. The current probable cause is "
            f"{likely_cause}, with recommended next step: {recommended}."
        )
