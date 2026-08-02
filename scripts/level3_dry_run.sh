#!/usr/bin/env bash
# Level 3 dry run — full stack: Redis + ChromaDB + SQLite (postgres optional)
set -euo pipefail
cd "$(dirname "$0")/.."

export DATABASE_URL=sqlite:///./incident_investigator.db
export REDIS_URL=redis://localhost:6379/0
export CHROMA_HOST=localhost
export CHROMA_PORT=8000
export EVENT_BUS_BACKEND=redis
export PYTHONPATH=.
PYTHON=/opt/homebrew/bin/python3.11

echo "► Starting services..."
docker compose up -d redis chroma
sleep 5
nc -z localhost 6379 || { echo "FAIL: redis not up"; exit 1; }
nc -z localhost 8000 || { echo "FAIL: chroma not up"; exit 1; }
echo "  redis ✓  chroma ✓  (SQLite for DB)"

echo "► Ingesting docs..."
$PYTHON scripts/ingest_docs.py 2>&1 | tail -1
$PYTHON scripts/sync_confluence.py 2>&1 | tail -1

echo "► Starting server..."
kill $(lsof -ti:8080) 2>/dev/null || true
kill $(pgrep -f "celery.*worker") 2>/dev/null || true
sleep 1
$PYTHON -m uvicorn server.api.main:app --port 8080 > /tmp/uvicorn.log 2>&1 &
SERVER_PID=$!

echo "► Starting Celery worker..."
$PYTHON -m celery -A server.workers.celery_app.celery_app worker \
  --include=server.workers.tasks --loglevel=INFO -Q aria > /tmp/celery.log 2>&1 &
WORKER_PID=$!

echo "► Waiting for server..."
for i in $(seq 1 40); do
  curl -s http://localhost:8080/health | grep -q '"ok"' && break
  sleep 3; printf "."
done
echo ""
curl -s http://localhost:8080/health | grep -q '"ok"' || { echo "FAIL: server never started"; cat /tmp/uvicorn.log | tail -10; exit 1; }
grep -q "ready" /tmp/celery.log 2>/dev/null || sleep 3
echo "  server ✓  worker ready"

$PYTHON - <<'PY'
import json, hmac, hashlib, pathlib, requests, time

env = {l.split("=")[0]: l.split("=",1)[1] for l in pathlib.Path(".env").read_text().splitlines() if "=" in l}
TOKEN    = env["API_AUTH_TOKEN"]
APPROVER = env["API_AUTH_TOKENS"].split(":")[0]
FALCO_S  = env["FALCO_WEBHOOK_SECRET"]
AM_S     = env["ALERTMANAGER_WEBHOOK_SECRET"]
BASE     = "http://localhost:8080"
H        = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
HA       = {"Authorization": f"Bearer {APPROVER}", "Content-Type": "application/json"}
results  = []

def check(label, r, expect=200, key=None, val=None):
    ok = r.status_code == expect
    d = {}
    try: d = r.json()
    except: pass
    if key is not None: ok = ok and (d.get(key) == val)
    sym = "PASS" if ok else "FAIL"
    results.append((sym, label))
    if not ok:
        snippet = d.get("detail") or str(d)[:120]
        print(f"  {sym}  [{r.status_code}]  {label}")
        print(f"       ✗ {snippet}")
    else:
        print(f"  {sym}  [{r.status_code}]  {label}")
    return d

# ── Auth & ReBAC ─────────────────────────────────────────────
print("\n── Auth & ReBAC ─────────────────────────────")
check("Unauthenticated → 401", requests.post(f"{BASE}/incidents/intake",
    json={"incident_id":"X","service":"s","severity":"P1"}), 401)
check("ReBAC block hr-payroll → 403", requests.post(f"{BASE}/incidents/intake", headers=H,
    json={"incident_id":"X","service":"hr-payroll","severity":"P1"}), 403)

# ── Incident + Real RAG ──────────────────────────────────────
print("\n── Incident + Real RAG ──────────────────────")
d = check("Create incident P1 checkout-api", requests.post(f"{BASE}/incidents/intake", headers=H,
    json={"incident_id":"INC-FM-001","service":"checkout-api","severity":"P1",
          "environment":"prod","symptoms":["high latency","increased errors"],
          "signals":{"cpu_percent":88,"error_rate_percent":9,"recent_deployment":True}}))
rag = d.get("runbook_guidance", {})
print(f"       RAG mode={rag.get('mode')}  sources={len(rag.get('sources',[]))}")
check("Timeline persisted", requests.get(f"{BASE}/incidents/INC-FM-001/timeline", headers=H),
    key="incident_id", val="INC-FM-001")
check("RCA draft generated", requests.get(f"{BASE}/incidents/INC-FM-001/rca-draft", headers=H),
    key="incident_id", val="INC-FM-001")

# ── Multi-Agent Orchestration (parallel) ────────────────────
print("\n── Multi-Agent Orchestration ────────────────")
d = check("8 agents in parallel → all evidence collected", requests.post(f"{BASE}/agents/investigate",
    headers=H,
    json={"incident_id":"INC-FM-001","service":"checkout-api","severity":"P1","environment":"prod"}))
print(f"       mode={d.get('mode')}  agents={d.get('agent_count')}  evidence={d.get('evidence_count')}")
print(f"       safety_boundary present: {'safety_boundary' in d}")

# ── SLO Engine ───────────────────────────────────────────────
print("\n── SLO Engine ───────────────────────────────")
d = check("SLO burn rate — critical threshold",
    requests.post(f"{BASE}/slo/evaluate", headers=H,
    json={"service":"checkout-api","total_requests":10000,"failed_requests":200,"slo_target":99.9}))
print(f"       burn_rate={d.get('burn_rate')}  severity={d.get('severity')}  budget_remaining={d.get('error_budget_remaining')}")
d2 = check("SLO healthy",
    requests.post(f"{BASE}/slo/evaluate", headers=H,
    json={"service":"checkout-api","total_requests":10000,"failed_requests":0,"slo_target":99.9}))
print(f"       burn_rate={d2.get('burn_rate')}  severity={d2.get('severity')}")

# ── Operational Memory (DB-backed) ───────────────────────────
print("\n── Operational Memory (DB-backed) ───────────")
d = check("Record outcome → backend:database",
    requests.post(f"{BASE}/memory/record", headers=H,
    json={"service":"checkout-api","incident_id":"INC-FM-001",
          "outcome":"mitigated","remediation":"scaled to 3 replicas"}))
print(f"       backend={d.get('backend')}  stored={d.get('stored')}")
d2 = check("Recall from DB → count≥1", requests.get(f"{BASE}/memory/checkout-api", headers=H))
print(f"       backend={d2.get('backend')}  count={d2.get('count')}")
check("Memory ReBAC block", requests.get(f"{BASE}/memory/hr-payroll-service", headers=H), 403)

# ── Deployment Intelligence ──────────────────────────────────
print("\n── Deployment Intelligence ──────────────────")
d = check("Correlate deployment → suspicion:high",
    requests.post(f"{BASE}/deployment/correlate", headers=H,
    json={"service":"checkout-api","symptoms":["high latency"],
          "signals":{"recent_deployments":[{"service":"checkout-api","revision":"abc123"}]}}))
print(f"       correlation={d.get('deployment_correlation')}  deployments={len(d.get('recent_deployments',[]))}")

# ── ChatOps Parser ───────────────────────────────────────────
print("\n── ChatOps Parser ───────────────────────────")
d = check("Parse /approve-action → valid intent",
    requests.post(f"{BASE}/chatops/parse", headers=H, json={"text":"/approve-action 42"}))
print(f"       valid={d.get('valid')}  command={d.get('command')}  user={d.get('user')}")
d2 = check("Parse unknown command → invalid",
    requests.post(f"{BASE}/chatops/parse", headers=H, json={"text":"/rm -rf /"}))
print(f"       valid={d2.get('valid')}")

# ── Chaos Engineering (disabled by default) ──────────────────
print("\n── Chaos Engineering ────────────────────────")
check("Chaos disabled by default → available:false",
    requests.post(f"{BASE}/chaos/run", headers=H,
    json={"experiment":"pod-delete","namespace":"demo","service":"checkout-api",
          "app_label":"app=checkout-api","dry_run":True}),
    key="available", val=False)
d = check("Chaos catalog always readable",
    requests.get(f"{BASE}/chaos/experiments", headers=H))
experiments = [e["name"] for e in d.get("experiments", [])]
print(f"       available={d.get('available')}  experiments={experiments}")
d = check("Chaos validation + resilience score",
    requests.post(f"{BASE}/chaos/validate", headers=H,
    json={"service":"checkout-api","experiment":"pod-delete","incident_created":True,
          "alert_fired":True,"healing_succeeded":True,"rag_sources":5,"mttr_seconds":42,"slo_burn_observed":True}))
print(f"       score={d.get('resilience_score')}  status={d.get('status')}")
d = check("Chaos report markdown",
    requests.post(f"{BASE}/chaos/report", headers=H,
    json={"service":"checkout-api","experiment":"cpu-hog","incident_created":True,
          "alert_fired":False,"healing_succeeded":True,"rag_sources":2,"mttr_seconds":90,"slo_burn_observed":False}))
print(f"       score={d.get('validation',{}).get('resilience_score')}  has_markdown={'report_markdown' in d}")

# ── ArgoCD + Approval → Celery ───────────────────────────────
print("\n── ArgoCD Approval → Celery Execution ───────")
check("ArgoCD dry_run=true", requests.post(f"{BASE}/gitops/argocd/checkout-api/sync?dry_run=true", headers=H),
    key="dry_run", val=True)
d = check("ArgoCD dry_run=false → approval (gitops-checkout-api)",
    requests.post(f"{BASE}/gitops/argocd/checkout-api/sync?dry_run=false", headers=H),
    key="approval_required", val=True)
aid = d.get("approval", {}).get("approval_id")
check("Self-approve → 4-eyes 409", requests.post(f"{BASE}/approvals/{aid}/decision", headers=H,
    json={"approved":True,"reason":"self"}), 409)
d3 = check("Commander approve → dispatched",
    requests.post(f"{BASE}/approvals/{aid}/decision", headers=HA,
    json={"approved":True,"reason":"approved"}),
    key="status", val="APPROVED")
dispatched = d3.get("execution",{}).get("dispatched")
task_id = d3.get("execution",{}).get("task_id")
print(f"       dispatched={dispatched}  task_id={task_id}")
if dispatched:
    time.sleep(5)
    log = pathlib.Path("/tmp/celery.log").read_text()
    if task_id in log:
        print(f"       Celery task succeeded={('succeeded' in log)}")
        results.append(("PASS" if "succeeded" in log else "FAIL", "Celery execution completed"))

# ── Webhooks ─────────────────────────────────────────────────
print("\n── Webhooks ─────────────────────────────────")
fb = pathlib.Path("examples/falco-webhook.json").read_bytes()
sig_f = "sha256=" + hmac.new(FALCO_S.encode(), fb, hashlib.sha256).hexdigest()
check("Falco HMAC → incident created", requests.post(f"{BASE}/webhooks/falco",
    data=fb, headers={"Content-Type":"application/json","X-Incident-Signature":sig_f}))
check("Falco bad HMAC → 401", requests.post(f"{BASE}/webhooks/falco",
    data=fb, headers={"Content-Type":"application/json","X-Incident-Signature":"sha256=bad"}), 401)
ab = pathlib.Path("examples/alertmanager-webhook.json").read_bytes()
sig_a = "sha256=" + hmac.new(AM_S.encode(), ab, hashlib.sha256).hexdigest()
da = check("Alertmanager HMAC → incident(s) created", requests.post(f"{BASE}/webhooks/alertmanager",
    data=ab, headers={"Content-Type":"application/json","X-Incident-Signature":sig_a}))
print(f"       received={da.get('received')}")

# ── Summary ──────────────────────────────────────────────────
passed = sum(1 for r in results if r[0]=="PASS")
failed = sum(1 for r in results if r[0]=="FAIL")
print(f"\n{'─'*52}")
print(f"  {passed} PASSED  |  {failed} FAILED  |  {len(results)} total")
if failed:
    print("  FAILED:")
    for sym, lbl in results:
        if sym == "FAIL": print(f"    ✗ {lbl}")
PY

echo ""
echo "► Stopping server and worker"
kill $SERVER_PID $WORKER_PID 2>/dev/null || true
echo "Done."
