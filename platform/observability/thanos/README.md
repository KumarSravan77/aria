# Thanos

Thanos extends Prometheus with long-term storage, global query, and multi-cluster visibility.

Use Thanos when ARIA moves beyond a single local Kind cluster and needs:

- multi-cluster metrics
- durable historical metrics
- cross-cluster SLO/burn-rate queries
- object storage backed retention

Prometheus remains the local metrics source. Thanos is the enterprise/global metrics layer.
