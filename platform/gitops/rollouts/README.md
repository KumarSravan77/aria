# Argo Rollouts Canary Strategy

ARIA uses Argo Rollouts as the preferred progressive delivery controller.

Recommended canary flow:

```text
Argo CD syncs desired rollout
→ Argo Rollouts shifts traffic 10/25/50/75/100
→ Prometheus AnalysisTemplate checks latency/error rate
→ AI reviews evidence
→ Rollout promotes or aborts through approval workflow
```

Use Istio for traffic splitting and Prometheus for analysis.
