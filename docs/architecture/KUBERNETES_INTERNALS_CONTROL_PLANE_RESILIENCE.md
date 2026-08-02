# ARIA — Kubernetes Internals and Control Plane Resilience

ARIA includes a Kubernetes internals layer for platform-level resilience.

## Endpoints

- `GET /kubernetes-internals/control-plane/health`
- `GET /kubernetes-internals/etcd/backups`
- `GET /kubernetes-internals/etcd/recovery-plan`
- `POST /kubernetes-internals/etcd/validate-restore`
- `GET /kubernetes-internals/admission/health`
- `GET /kubernetes-internals/dns/health`
- `GET /kubernetes-internals/cni/health`
- `GET /kubernetes-internals/upgrade/readiness`
- `GET /kubernetes-internals/summary`

## Covers

- etcd backup freshness, size, encryption and restore validation metadata
- etcd recovery plan generation
- API server reachability and latency
- scheduler/controller-manager advisory checks
- admission webhook health
- CoreDNS health
- CNI/node networking health
- upgrade readiness

## Safety Boundary

ARIA must not restore production etcd automatically.

Correct flow:

```text
Detect risk → inspect backup → generate recovery plan → validate restore in sandbox → approval/manual execution → audit
```
