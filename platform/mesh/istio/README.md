# Istio Service Mesh

Istio is the primary service mesh for this repo because it supports:

- canary traffic splitting with Argo Rollouts
- retries and timeouts
- mTLS
- telemetry
- fault injection for resilience testing

Cilium/Hubble remains useful for eBPF networking and visibility, but Istio is the default mesh for canary rollout control.
