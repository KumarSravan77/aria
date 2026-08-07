# High availability and automatic recovery

Automatic recovery is a layered control loop, not permission for an AI agent to
run arbitrary infrastructure commands.

1. Kubernetes replaces failed pods and readiness probes remove bad replicas.
2. Disruption budgets and topology spread preserve capacity across zones.
3. EKS managed capacity or Karpenter replaces failed nodes.
4. ARIA calls `/recovery/coordinate` to classify the recovery lane.
5. ARIA publishes an evidence-backed incident signal to On-Call SRE.
6. On-Call owns approval for database, traffic, cluster or regional failover.
7. A deterministic executor performs an approved action exactly once.
8. ARIA validates health, alert clearance, data integrity, RTO and RPO.

Pod replacement is safe to delegate to Kubernetes. Database promotion, regional
traffic shifts and data restore remain approval-gated because a false-positive
failover can cause split brain or data loss.

## Required production topology

- At least three application replicas spread across three availability zones
- Pod disruption budgets, readiness/startup probes and rolling deployments
- Autoscaling with tested minimum capacity and bounded maximums
- PostgreSQL multi-AZ storage for incident state
- Redis or another durable distributed queue for workers
- Idempotency keys and leader election for schedulers
- Warm standby cluster in a second region reconciled by GitOps
- Replicated backups with regularly tested restores
- Independent regional health checks and controlled traffic failover
- OpenTelemetry traces, recovery metrics and Opik AI workflow evaluation
- Chaos tests covering pod, node, zone, database and regional failure

The manifests in `platform/ha-recovery/` are reference controls. They do not make
a service highly available until storage, traffic, secrets, backups and recovery
drills are configured for the target environment.
