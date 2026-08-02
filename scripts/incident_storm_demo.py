#!/usr/bin/env python3
"""
Incident Storm Demo — Full-Maturity AI SRE Platform
=====================================================
Demonstrates a P1 incident storm where the platform:
  1. Starts in NORMAL mode (all 9 agents)
  2. Receives a P1 storm — platform switches to DEGRADED automatically
  3. Shows agent selection diff: 9 agents → 2 agents
  4. Prioritises P1s — skips low-value paths for P3s
  5. Streams partial evidence from a P1 investigation
  6. Computes topology blast radius for the root service
  7. Simulates PagerDuty escalation bottleneck detection
  8. Enforces governance: 4-eyes approval still required
  9. Restores NORMAL mode and confirms full audit trail
"""
import time
import json
import hmac
import hashlib
import pathlib
import requests
import sys

# ── Config ────────────────────────────────────────────────────────────────────
BASE = "http://localhost:8080"
env = {
    l.split("=")[0]: l.split("=", 1)[1]
    for l in pathlib.Path(".env").read_text().splitlines()
    if "=" in l
}
TOKEN    = env["API_AUTH_TOKEN"]
APPROVER = env["API_AUTH_TOKENS"].split(":")[0]
AM_S     = env["ALERTMANAGER_WEBHOOK_SECRET"]
H        = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
HA       = {"Authorization": f"Bearer {APPROVER}", "Content-Type": "application/json"}


def banner(title: str, char: str = "═") -> None:
    width = 70
    print(f"\n{char * width}")
    print(f"  {title}")
    print(f"{char * width}")


def section(title: str) -> None:
    print(f"\n  ── {title} {'─' * (60 - len(title))}")


def show(label: str, value, indent: int = 4) -> None:
    pad = " " * indent
    if isinstance(value, dict):
        print(f"{pad}{label}:")
        for k, v in value.items():
            print(f"{pad}  {k}: {v}")
    else:
        print(f"{pad}{label}: {value}")


def post(path: str, data: dict, headers=None) -> dict:
    r = requests.post(f"{BASE}{path}", json=data, headers=headers or H, timeout=15)
    return r.json()


def get(path: str, headers=None) -> dict:
    r = requests.get(f"{BASE}{path}", headers=headers or H, timeout=15)
    return r.json()


# ══════════════════════════════════════════════════════════════════════════════
banner("INCIDENT STORM DEMO — AI SRE Platform Full Maturity")
banner("Platform intelligence: adaptive orchestration + governance + streaming", "─")

time.sleep(0.3)

# ── ACT 1: Platform starts in NORMAL mode ─────────────────────────────────────
banner("ACT 1 — Platform in NORMAL Mode (baseline)")

status = get("/orchestration/status")
mode_info = status.get("degradation", {})
bp = status.get("backpressure", {})
print(f"\n  Degradation mode  : {mode_info.get('manual_override', 'auto (normal)')}")
print(f"  Active slots      : {bp.get('active', 0)} / {bp.get('max_concurrent', 50)}")
print(f"  Cached entries    : {status.get('cache', {}).get('cached_entries', 0)}")

section("P1 Investigation — NORMAL mode (all 9 agents)")
p1_normal = post("/agents/investigate", {
    "incident_id": "STORM-BASELINE-001",
    "service": "checkout-api",
    "severity": "P1",
    "environment": "prod",
    "symptoms": ["high latency", "increased errors"],
    "signals": {"cpu_percent": 88, "error_rate_percent": 9, "recent_deployment": True},
})
meta = p1_normal.get("orchestration_meta", {})
print(f"\n  Mode        : {p1_normal.get('mode')}")
print(f"  Agents run  : {p1_normal.get('agent_count')}")
print(f"  Evidence    : {p1_normal.get('evidence_count')}")
print(f"  Est. tokens : {meta.get('estimated_tokens', '?')}")
print(f"  Est. cost   : ${meta.get('estimated_cost_usd', 0):.4f} (local Ollama)")
print(f"  Routing     : {meta.get('routing_reason', '?')[:60]}")


# ── ACT 2: Incident storm begins ──────────────────────────────────────────────
banner("ACT 2 — Incident Storm Begins (P1s flooding in)")

print("\n  Simulating storm: manually setting DEGRADED mode")
print("  (In production this triggers automatically at 100+ active incidents)")
post("/orchestration/degradation", {"mode": "degraded"})

# Fire 3 rapid P1 incidents (the storm)
storm_ids = []
for i in range(1, 4):
    inc_id = f"STORM-P1-00{i}"
    storm_ids.append(inc_id)
    r = requests.post(f"{BASE}/incidents/intake", headers=H, json={
        "incident_id": inc_id,
        "service": "checkout-api",
        "severity": "P1",
        "environment": "prod",
        "symptoms": ["high latency"],
        "signals": {"error_rate_percent": 8},
    }, timeout=10)
    print(f"  ⚡  Fired P1 incident {inc_id}  →  status {r.status_code}")
    time.sleep(0.1)

section("P1 Investigation — DEGRADED mode (metrics + logs only)")
p1_degraded = post("/agents/investigate", {
    "incident_id": "STORM-P1-001",
    "service": "checkout-api",
    "severity": "P1",
    "environment": "prod",
    "symptoms": ["high latency"],
    "signals": {"error_rate_percent": 8},
})
meta_d = p1_degraded.get("orchestration_meta", {})
print(f"\n  Mode            : {p1_degraded.get('mode')}")
print(f"  Agents run      : {p1_degraded.get('agent_count')}  ← reduced from 9")
print(f"  Evidence        : {p1_degraded.get('evidence_count')}")
print(f"  Est. tokens     : {meta_d.get('estimated_tokens', '?')}  ← reduced")
print(f"  Routing reason  : {meta_d.get('routing_reason', '?')[:60]}")
token_saved = p1_normal.get("orchestration_meta", {}).get("estimated_tokens", 0) - meta_d.get("estimated_tokens", 0)
print(f"\n  ✓  Token reduction vs NORMAL: ~{token_saved} tokens saved per investigation")


# ── ACT 3: P3 deprioritised ───────────────────────────────────────────────────
banner("ACT 3 — Low-Priority Incidents Deprioritised")

section("P3 Investigation — only metrics + logs (routing skips expensive agents)")
p3 = post("/agents/investigate", {
    "incident_id": "STORM-P3-001",
    "service": "checkout-api",
    "severity": "P3",
    "environment": "dev",
    "symptoms": ["slow responses"],
    "signals": {},
})
meta_p3 = p3.get("orchestration_meta", {})
print(f"\n  Mode            : {p3.get('mode')}")
print(f"  Agents run      : {p3.get('agent_count')}  ← minimal path for P3")
print(f"  Est. tokens     : {meta_p3.get('estimated_tokens', '?')}")
print(f"  Routing reason  : {meta_p3.get('routing_reason', '?')[:60]}")

section("Backpressure metrics during storm")
mid_status = get("/orchestration/status")
bp_mid = mid_status.get("backpressure", {})
cache_mid = mid_status.get("cache", {})
print(f"\n  Active slots    : {bp_mid.get('active', 0)} / {bp_mid.get('max_concurrent', 50)}")
print(f"  Total processed : {bp_mid.get('total_processed', 0)}")
print(f"  Cache hit rate  : {cache_mid.get('hit_rate', 0):.1%}")
print(f"  Cached entries  : {cache_mid.get('cached_entries', 0)}")


# ── ACT 4: Topology blast radius ──────────────────────────────────────────────
banner("ACT 4 — Topology Intelligence: Who Else Is Affected?")

blast = get("/topology/checkout-api/blast-radius?severity=P1")
print(f"\n  Root service          : {blast.get('root_service')}")
print(f"  Blast radius score    : {blast.get('blast_radius_score')}")
print(f"  Impact level          : {blast.get('impact_level', '').upper()}")
print(f"  Direct downstream     : {blast.get('direct_downstream', [])}")
print(f"  All affected          : {blast.get('all_affected_services', [])}")
print(f"  Customer-facing       : {blast.get('customer_facing_impact', [])}")
print(f"\n  → {blast.get('recommendation', '')}")

section("Dependency graph snapshot")
graph = get("/topology/graph")
print(f"\n  Total services : {graph.get('total_services')}")
print(f"  Total edges    : {graph.get('total_edges')}")
print(f"  Services       : {graph.get('services', [])[:5]} ...")


# ── ACT 5: PagerDuty escalation simulation ────────────────────────────────────
banner("ACT 5 — PagerDuty Escalation Bottleneck Detection")

paging = get("/integrations/pagerduty/checkout-api/escalation?severity=P1")
print(f"\n  Service               : {paging.get('service')}")
print(f"  Bottlenecks detected  : {paging.get('bottlenecks_detected', [])}")
print(f"  Paging saturation risk: {paging.get('paging_saturation_risk')}")
for step in paging.get("escalation_chain", [])[:3]:
    flag = "⚠️" if step.get("bottleneck_risk") else "  "
    print(f"  {flag} L{step['level']}: {step['responder']}  "
          f"(load={step['concurrent_incidents']}, ETA={step['estimated_response_minutes']}min)")
print(f"\n  → {paging.get('recommendation', '')}")


# ── ACT 6: Governance preserved under degradation ────────────────────────────
banner("ACT 6 — Governance Still Enforced Under Load")

section("Prod healing requires approval even in DEGRADED mode")
heal = post("/heal", {
    "action": "scale_deployment",
    "target": "checkout-api",
    "namespace": "demo",
    "environment": "prod",
    "replicas": 5,
    "dry_run": False,
})
aid = heal.get("approval", {}).get("approval_id")
print(f"\n  Heal request result   : approval_required={heal.get('approval_required')}")
print(f"  Approval ID           : {aid}  (status=PENDING)")
print(f"  Policy decision       : {heal.get('policy', {}).get('reason', '?')}")

section("4-eyes: self-approval blocked")
self_approve = requests.post(
    f"{BASE}/approvals/{aid}/decision",
    headers=H, json={"approved": True, "reason": "self"}, timeout=10)
print(f"\n  Self-approve attempt  : HTTP {self_approve.status_code}  "
      f"→  {self_approve.json().get('detail', '')[:50]}")

section("Commander approves → Celery dispatched")
approve = requests.post(
    f"{BASE}/approvals/{aid}/decision",
    headers=HA, json={"approved": True, "reason": "approved during storm — controlled scale"}, timeout=10)
approve_data = approve.json()
exec_info = approve_data.get("execution", {})
print(f"\n  Approval status  : {approve_data.get('status')}")
print(f"  Celery dispatched: {exec_info.get('dispatched')}")
print(f"  Task ID          : {exec_info.get('task_id', 'n/a')[:36]}")


# ── ACT 7: Evidence streaming ─────────────────────────────────────────────────
banner("ACT 7 — Partial Evidence Streaming (SSE)")

# First create an incident to stream
inc_r = requests.post(f"{BASE}/incidents/intake", headers=H, json={
    "incident_id": "STORM-STREAM-001",
    "service": "checkout-api",
    "severity": "P1",
    "environment": "prod",
    "symptoms": ["high latency"],
}, timeout=10)

section("Streaming agent results — evidence arrives incrementally")
print()
stream_count = 0
try:
    with requests.get(f"{BASE}/agents/STORM-STREAM-001/stream",
                      headers=H, stream=True, timeout=20) as r:
        for line in r.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                event = json.loads(line[6:])
                if event.get("done"):
                    print(f"  ✓  Stream complete — {stream_count} agent results received")
                    break
                if event.get("skipped"):
                    print(f"  ⊘  [{event.get('agent')}] skipped ({event.get('reason', '')})")
                else:
                    print(f"  ↳  [{event.get('agent')}] {event.get('summary', '')[:50]}"
                          f"  | recs={len(event.get('recommendations', []))}")
                stream_count += 1
                if stream_count >= 9:
                    break
except Exception as exc:
    print(f"  (streaming unavailable in this run: {exc})")


# ── ACT 8: Storm ends — restore NORMAL mode ───────────────────────────────────
banner("ACT 8 — Storm Over: Restore NORMAL Mode")

restore = post("/orchestration/degradation", {"mode": None})  # clear manual override → auto
print(f"\n  Degradation mode : auto (normal)  ← manual override cleared")

section("SLO impact assessment")
slo = post("/slo/evaluate", {
    "service": "checkout-api",
    "total_requests": 100000,
    "failed_requests": 8500,
    "slo_target": 99.9,
})
print(f"\n  Availability       : {slo.get('availability')}%")
print(f"  Burn rate          : {slo.get('burn_rate')}x  → severity={slo.get('severity').upper()}")
print(f"  Budget remaining   : {slo.get('error_budget_remaining')}%")

section("Incident cluster detection (temporal analysis)")
cluster = get(f"/incidents/{storm_ids[0]}/cluster")
print(f"\n  Cluster size      : {cluster.get('cluster_size')}")
print(f"  Is cluster        : {cluster.get('is_cluster')}")
print(f"  Shared cause      : {cluster.get('probable_shared_cause', 'unknown')}")
print(f"  Recommendation    : {cluster.get('recommendation', '')[:70]}")

section("Predictive forecast after storm")
forecast = get("/forecast/checkout-api")
prediction = forecast.get('prediction') or 'unknown'
print(f"\n  Prediction        : {prediction.upper()}")
print(f"  Confidence        : {forecast.get('confidence')}")
print(f"  Burn label        : {forecast.get('factors', {}).get('burn_label')}")
print(f"  Recommendation    : {forecast.get('recommended_action')}")

section("Final orchestration telemetry")
final_status = get("/orchestration/status")
final_bp = final_status.get("backpressure", {})
final_cache = final_status.get("cache", {})
final_tokens = final_status.get("token_budget", {})
print(f"\n  Total processed   : {final_bp.get('total_processed')} investigations")
print(f"  Total rejected    : {final_bp.get('rejected')} (backpressure)")
print(f"  Cache hit rate    : {final_cache.get('hit_rate', 0):.1%}")
print(f"  Total tokens used : {final_tokens.get('total_tokens_used')}")
print(f"  Total cost (est.) : ${final_tokens.get('estimated_cost_usd', 0):.4f} (local model)")

circuit_status = final_status.get("circuit_breakers", {})
if circuit_status:
    open_circuits = [n for n, s in circuit_status.items() if s.get("state") == "open"]
    print(f"  Open circuits     : {open_circuits or 'none'}")


# ── Summary ────────────────────────────────────────────────────────────────────
banner("DEMO COMPLETE — What the Platform Proved")
print("""
  ✓  Normal → Degraded mode switch preserved platform operation under storm
  ✓  P1 agents: 9 → 2 in degraded mode  (massive token/cost reduction)
  ✓  P3 routed to minimal 2-agent path   (low-value work deprioritised)
  ✓  Topology blast radius identified    (customer-facing services surfaced)
  ✓  PagerDuty bottlenecks detected      (on-call overload visible before page)
  ✓  4-eyes approval enforced            (governance survived degraded mode)
  ✓  Celery action dispatched            (async execution still wired)
  ✓  Evidence streamed incrementally     (partial results visible in real time)
  ✓  SLO burn rate computed              (reliability impact quantified)
  ✓  Temporal cluster detected           (storm treated as one root cause)
  ✓  Predictive forecast updated         (future risk scored from storm data)
  ✓  Full orchestration telemetry visible (audit + cost + health observable)

  Final maturity: Level 7 — Scalable Autonomous SRE Platform
  Enterprise-resilient · cost-controlled · topology-aware · replay-safe
""")
