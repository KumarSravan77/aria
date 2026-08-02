#!/usr/bin/env python3
"""Verify one checkout request is visible in metrics, logs, and traces."""
import json
import os
import sys
import time
import requests


BANKING = os.getenv("BANKING_URL", "http://localhost:9200")
PROMETHEUS = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
LOKI = os.getenv("LOKI_URL", "http://localhost:3100")
TEMPO = os.getenv("TEMPO_URL", "http://localhost:3200")


def get_json(url, **kwargs):
    response = requests.get(url, timeout=10, **kwargs)
    response.raise_for_status()
    return response.json()


response = requests.post(f"{BANKING}/transactions", params={"amount": 125}, timeout=10)
response.raise_for_status()
transaction = response.json()
trace_id = transaction.get("trace_id")
if not trace_id or len(trace_id) != 32:
    raise SystemExit("banking response did not return a valid trace_id")

time.sleep(int(os.getenv("TELEMETRY_SETTLE_SECONDS", "10")))
metrics = get_json(f"{PROMETHEUS}/api/v1/query", params={"query": "sum(banking_transactions_total)"})
logs = get_json(f"{LOKI}/loki/api/v1/query_range", params={"query": f'{{namespace="demo"}} |= "{trace_id}"', "limit": 20})
trace = get_json(f"{TEMPO}/api/traces/{trace_id}")

result = {
    "trace_id": trace_id,
    "metrics_found": bool(metrics.get("data", {}).get("result")),
    "logs_found": bool(logs.get("data", {}).get("result")),
    "trace_found": bool(trace.get("batches")),
}
print(json.dumps(result, indent=2))
if not all(result[key] for key in ("metrics_found", "logs_found", "trace_found")):
    sys.exit(1)
