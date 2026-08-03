SHELL := /bin/bash
REPO := aria
CLUSTER := incident-lab
-include .env
export
API_TOKEN ?= $(API_AUTH_TOKEN)
ALERT_SECRET ?= $(ALERTMANAGER_WEBHOOK_SECRET)
APPROVER_TOKEN ?= $(shell echo "$(API_AUTH_TOKENS)" | cut -d: -f1)
AUTH_HEADER := Authorization: Bearer $(API_TOKEN)
APPROVER_AUTH_HEADER := Authorization: Bearer $(APPROVER_TOKEN)
ENVIRONMENT ?= dev

.PHONY: help bootstrap-env
bootstrap-env: ## Generate local .env secrets if missing
	./scripts/bootstrap-env.sh

help:
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "%-28s %s\\n", $$1, $$2}'

telemetry-render: ## Render and validate the local telemetry overlay
	kubectl kustomize telemetry/overlays/local >/dev/null

telemetry-deploy-local: ## Deploy collectors, Redpanda, Vector and MinIO to Kubernetes
	kubectl apply -k telemetry/overlays/local

telemetry-load: ## Send OTLP log traffic; set RATE, DURATION and OTLP_HTTP as needed
	k6 run telemetry/load/k6-otlp.js

telemetry-capacity: ## Calculate the requested capacity; set TB_PER_DAY
	curl -s "http://localhost:8080/telemetry/capacity?tb_per_day=$${TB_PER_DAY:-1}" -H '$(AUTH_HEADER)' | jq

kubeflow-investigate: ## Run the read-only Kubeflow training incident demo
	curl -s -X POST -H '$(AUTH_HEADER)' -H 'Content-Type: application/json' \
	  http://localhost:8080/kubeflow/investigate \
	  -d @examples/kubeflow-trainjob-incident.json | jq

local-up: bootstrap-env ## Start local Docker services
	docker compose up -d --build

local-up-collab: bootstrap-env ## Start local services including Mattermost profile
	docker compose --profile collab up -d --build

local-down: ## Stop local Docker services
	docker compose down -v

install-python: ## Install Python dependencies locally
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -r server/requirements.txt

ingest: ## Ingest repo docs into ChromaDB
	python3 scripts/ingest_docs.py

confluence-sync: ## Sync local/sample Confluence pages into ChromaDB
	python3 scripts/sync_confluence.py

sample-rag-rebac: ## Ask RAG using authenticated user and ReBAC-filtered docs
	curl -s http://localhost:8080/rag/ask -H 'Content-Type: application/json' -H '$(AUTH_HEADER)' -d '{"question":"checkout-api high latency runbook"}' | jq

sample-investigation: ## Call investigation API with sample payload
	curl -s http://localhost:8080/investigate -H 'Content-Type: application/json' -H '$(AUTH_HEADER)' -d @examples/high-latency-incident.json | jq

sample-intake: ## Simulate manual incident intake and AI war-room creation
	curl -s http://localhost:8080/incidents/intake -H 'Content-Type: application/json' -H '$(AUTH_HEADER)' -d @examples/alertmanager-intake.json | jq

sample-alertmanager: ## Simulate real Alertmanager webhook payload
	SIG=$$(python3 -c 'import hmac,hashlib,pathlib,os; body=pathlib.Path("examples/alertmanager-webhook.json").read_bytes(); secret=os.environ["ALERTMANAGER_WEBHOOK_SECRET"].encode(); print("sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest())'); curl -s http://localhost:8080/webhooks/alertmanager -H 'Content-Type: application/json' -H "X-Incident-Signature: $$SIG" -d @examples/alertmanager-webhook.json | jq

sample-timeline: ## Show incident timeline for sample manual intake
	curl -s http://localhost:8080/incidents/INC-2026-002/timeline -H '$(AUTH_HEADER)' | jq

sample-rca: ## Generate RCA draft for sample intake
	curl -s http://localhost:8080/incidents/INC-2026-002/rca-draft -H '$(AUTH_HEADER)' | jq -r .rca_markdown

kind-create: ## Create local Kind cluster
	kind create cluster --name $(CLUSTER) --config k8s/kind/kind-cluster.yaml || true
	kubectl cluster-info --context kind-$(CLUSTER)

kind-delete: ## Delete local Kind cluster
	kind delete cluster --name $(CLUSTER)

k8s-bootstrap: ## Install namespaces, metrics stack, and base config
	kubectl apply -f k8s/namespaces.yaml
	kubectl apply -f k8s/datastores/chroma.yaml
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
	helm repo add grafana https://grafana.github.io/helm-charts
	helm repo update
	helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack -n monitoring -f k8s/monitoring/prometheus-values.yaml --create-namespace

k8s-deploy-app: ## Build and deploy sample app and investigator to Kind
	docker build -t checkout-api:local apps/sample-checkout-api
	kind load docker-image checkout-api:local --name $(CLUSTER)
	docker build -t inventory-api:local apps/inventory-api
	kind load docker-image inventory-api:local --name $(CLUSTER)
	docker build -t banking-api:local apps/banking-api
	kind load docker-image banking-api:local --name $(CLUSTER)
	docker build -t fraud-detection-api:local apps/fraud-detection-api
	kind load docker-image fraud-detection-api:local --name $(CLUSTER)
	docker build -t transaction-ledger-api:local apps/transaction-ledger-api
	kind load docker-image transaction-ledger-api:local --name $(CLUSTER)
	docker build -t aria:local -f server/Dockerfile .
	kind load docker-image aria:local --name $(CLUSTER)
	kubectl apply -f k8s/apps/sample-checkout-api.yaml
	kubectl apply -f k8s/apps/inventory-api.yaml
	kubectl apply -f k8s/apps/banking-demo.yaml
	kubectl apply -f k8s/apps/aria-api.yaml
	kubectl apply -f k8s/monitoring/grafana-application-dashboard.yaml

port-forward: ## Port-forward ARIA, banking API, Grafana, and Prometheus
	@echo "Starting port-forwards. Keep this terminal open."
	kubectl -n sre port-forward svc/aria-api 8080:8080 & 	kubectl -n sre port-forward svc/chroma 8000:8000 & 	kubectl -n demo port-forward svc/banking-api 9200:9200 & 	kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3000:80 & 	kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090 & wait

generate-latency: ## Enable latency in sample app
	kubectl -n demo set env deployment/checkout-api CHAOS_LATENCY_MS=1200 CHAOS_ERROR_RATE=0.1

clear-latency: ## Clear latency in sample app
	kubectl -n demo set env deployment/checkout-api CHAOS_LATENCY_MS=0 CHAOS_ERROR_RATE=0
	kubectl -n demo set env deployment/inventory-api INVENTORY_DELAY_MS=0
	kubectl -n demo set env deployment/fraud-detection-api FRAUD_DELAY_MS=0
	kubectl -n demo set env deployment/transaction-ledger-api LEDGER_FAILURE=false

generate-dependency-latency: ## Slow inventory to demonstrate cross-service trace correlation
	kubectl -n demo set env deployment/fraud-detection-api FRAUD_DELAY_MS=1200

generate-ledger-failure: ## Fail ledger writes to demonstrate banking dependency RCA
	kubectl -n demo set env deployment/transaction-ledger-api LEDGER_FAILURE=true

verify-e2e-observability: ## Prove a request appears in Prometheus, Loki, and Tempo
	python3 scripts/verify_e2e_observability.py

kill-pod: ## Delete one sample app pod to simulate incident
	kubectl -n demo delete pod -l app=checkout-api --wait=false

heal-scale: ## Scale sample app through healing API
	curl -s http://localhost:8080/heal -H 'Content-Type: application/json' -H '$(AUTH_HEADER)' -d '{"action":"scale_deployment","namespace":"demo","target":"checkout-api","replicas":3,"environment":"$(ENVIRONMENT)","dry_run":false,"user":{"role":"sre","team":"payments"}}' | jq

paging-install: ## Install local GoAlert demo manifests
	kubectl apply -f k8s/paging/goalert.yaml

paging-forward: ## Port-forward GoAlert
	kubectl -n paging port-forward svc/goalert 8081:8081

chaos-install: ## Install LitmusChaos namespace and Helm chart
	kubectl apply -f k8s/chaos/litmus-install.yaml
	helm repo add litmuschaos https://litmuschaos.github.io/litmus-helm/
	helm repo update
	helm upgrade --install litmus litmuschaos/litmus -n litmus --create-namespace

chaos-pod-delete: ## Run Litmus pod-delete chaos against checkout-api
	kubectl apply -f k8s/chaos/pod-delete-chaosengine.yaml

chaos-cpu-hog: ## Run Litmus CPU hog chaos against checkout-api
	kubectl apply -f k8s/chaos/cpu-hog-chaosengine.yaml

test: ## Run unit tests
	python3 -m pytest tests -q

approve-action: ## Approve and execute pending action; pass APPROVAL_ID=1
	curl -s http://localhost:8080/approvals/$(APPROVAL_ID)/decision -H 'Content-Type: application/json' -H '$(APPROVER_AUTH_HEADER)' -d '{"approved":true,"reason":"approved by incident commander"}' | jq

# ---- AI-native enterprise integrations ----
local-up-ai: bootstrap-env ## Start API dependencies plus Ollama/OpenFGA/Loki/Tempo profiles
	docker compose --profile ai --profile authz --profile observability up -d --build

ollama-pull: ## Pull default local Ollama model
	docker exec -it $$(docker compose ps -q ollama) ollama pull $${OLLAMA_MODEL:-llama3.1:8b}

sample-llm-reason: ## Run Ollama-backed incident reasoning if Ollama is available
	curl -s http://localhost:8080/llm/reason -H 'Content-Type: application/json' -H '$(AUTH_HEADER)' -d @examples/high-latency-incident.json | jq

argocd-install: ## Create Argo CD namespace placeholder and print install notes
	kubectl apply -f k8s/gitops/argocd-install-notes.yaml
	@sed -n '1,8p' k8s/gitops/argocd-install-notes.yaml

argocd-apps: ## Query Argo CD applications through platform adapter
	curl -s http://localhost:8080/gitops/argocd/apps -H '$(AUTH_HEADER)' | jq

rollouts-install: ## Create Argo Rollouts namespace placeholder and print install notes
	kubectl apply -f k8s/rollouts/argo-rollouts-install-notes.yaml
	@sed -n '1,6p' k8s/rollouts/argo-rollouts-install-notes.yaml

observability-query: ## Query Prometheus/Loki/Tempo adapters for checkout-api
	curl -s http://localhost:8080/observability/checkout-api -H '$(AUTH_HEADER)' | jq

keda-install: ## Create KEDA namespace placeholder and print install notes
	kubectl apply -f k8s/scaling/keda-install-notes.yaml
	@sed -n '1,6p' k8s/scaling/keda-install-notes.yaml

keda-recommend: ## Ask platform for KEDA scaling recommendation
	curl -s http://localhost:8080/scaling/keda/demo/checkout-api/recommendation -H '$(AUTH_HEADER)' | jq

opencost-install: ## Create OpenCost namespace placeholder and print install notes
	kubectl apply -f k8s/cost/opencost-install-notes.yaml
	@sed -n '1,6p' k8s/cost/opencost-install-notes.yaml

cost-allocation: ## Query OpenCost adapter
	curl -s 'http://localhost:8080/cost/allocation?namespace=demo' -H '$(AUTH_HEADER)' | jq

falco-install: ## Create Falco namespace placeholder and print install notes
	kubectl apply -f k8s/security/falco-install-notes.yaml
	@sed -n '1,6p' k8s/security/falco-install-notes.yaml

sample-falco: ## Simulate Falco runtime security alert through webhook
	SIG=$$(python3 -c 'import hmac,hashlib,pathlib,os; body=pathlib.Path("examples/falco-alert.json").read_bytes(); secret=os.environ["FALCO_WEBHOOK_SECRET"].encode(); print("sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest())'); curl -s http://localhost:8080/webhooks/falco -H 'Content-Type: application/json' -H "X-Incident-Signature: $$SIG" -d @examples/falco-alert.json | jq

cilium-notes: ## Print Cilium/Hubble install notes
	@sed -n '1,8p' k8s/networking/cilium-hubble-install-notes.yaml

openfga-notes: ## Print OpenFGA migration notes
	@sed -n '1,8p' k8s/openfga/openfga-install-notes.yaml

# ---- Chaos engineering / resilience validation ----
chaos-list: ## List AI platform chaos experiments
	curl -s http://localhost:8080/chaos/experiments -H '$(AUTH_HEADER)' | jq

chaos-run-dry: ## Dry-run LitmusChaos experiment through platform API; pass EXPERIMENT=pod-delete
	curl -s http://localhost:8080/chaos/run -H 'Content-Type: application/json' -H '$(AUTH_HEADER)' -d '{"experiment":"$${EXPERIMENT:-pod-delete}","namespace":"demo","service":"checkout-api","app_label":"app=checkout-api","dry_run":true}' | jq

chaos-run-live: ## Apply LitmusChaos experiment through platform API; pass EXPERIMENT=pod-delete
	curl -s http://localhost:8080/chaos/run -H 'Content-Type: application/json' -H '$(AUTH_HEADER)' -d '{"experiment":"$${EXPERIMENT:-pod-delete}","namespace":"demo","service":"checkout-api","app_label":"app=checkout-api","dry_run":false}' | jq

chaos-memory-hog: ## Run Litmus memory hog chaos against checkout-api
	kubectl apply -f k8s/chaos/memory-hog-chaosengine.yaml

chaos-network-latency: ## Run Litmus network latency chaos against checkout-api
	kubectl apply -f k8s/chaos/network-latency-chaosengine.yaml

chaos-dns-failure: ## Run Litmus DNS failure chaos against checkout-api
	kubectl apply -f k8s/chaos/dns-failure-chaosengine.yaml

chaos-validate: ## Calculate resilience score from observed chaos signals
	curl -s http://localhost:8080/chaos/validate -H 'Content-Type: application/json' -H '$(AUTH_HEADER)' -d '{"service":"checkout-api","experiment":"$${EXPERIMENT:-pod-delete}","incident_created":true,"alert_fired":true,"healing_succeeded":true,"rag_sources":5,"mttr_seconds":42,"slo_burn_observed":true}' | jq

chaos-report: ## Generate markdown resilience report from observed chaos signals
	curl -s http://localhost:8080/chaos/report -H 'Content-Type: application/json' -H '$(AUTH_HEADER)' -d '{"service":"checkout-api","experiment":"$${EXPERIMENT:-pod-delete}","incident_created":true,"alert_fired":true,"healing_succeeded":true,"rag_sources":5,"mttr_seconds":42,"slo_burn_observed":true}' | jq -r .report_markdown

# ---- Full maturity / agentic operations ----
agent-investigate: ## Run multi-agent deterministic investigation
	curl -s http://localhost:8080/agents/investigate -H 'Content-Type: application/json' -H '$(AUTH_HEADER)' -d @examples/high-latency-incident.json | jq

slo-evaluate: ## Evaluate sample SLO and burn-rate math
	curl -s http://localhost:8080/slo/evaluate -H 'Content-Type: application/json' -H '$(AUTH_HEADER)' -d @examples/slo-evaluation.json | jq

memory-record: ## Record a successful remediation memory
	curl -s http://localhost:8080/memory/record -H 'Content-Type: application/json' -H '$(AUTH_HEADER)' -d @examples/memory-record.json | jq

memory-recall: ## Recall operational memory for checkout-api
	curl -s http://localhost:8080/memory/checkout-api -H '$(AUTH_HEADER)' | jq

deployment-correlate: ## Correlate recent deployments with incident symptoms
	curl -s http://localhost:8080/deployment/correlate -H 'Content-Type: application/json' -H '$(AUTH_HEADER)' -d @examples/deployment-correlation.json | jq

chatops-parse: ## Parse a ChatOps slash command safely
	curl -s http://localhost:8080/chatops/parse -H 'Content-Type: application/json' -H '$(AUTH_HEADER)' -d @examples/chatops-command.json | jq

# ---- Kubernetes-native platform tooling ----
platform-tools: ## List Kubernetes-native platform tools exposed by API
	curl -s http://localhost:8080/platform/tools -H '$(AUTH_HEADER)' | jq

canary-plan: ## Generate canary rollout plan for checkout-api
	curl -s http://localhost:8080/platform/canary/plan -H 'Content-Type: application/json' -H '$(AUTH_HEADER)' -d '{"service":"checkout-api","namespace":"demo","strategy":"canary","traffic_steps":[10,25,50,75,100]}' | jq

kyverno-install: ## Install Kyverno namespace/notes; then install Helm chart manually if needed
	kubectl apply -f platform/security/kyverno/install-notes.yaml
	@echo "Install Kyverno with: helm upgrade --install kyverno kyverno/kyverno -n kyverno --create-namespace"

kyverno-policies-apply: ## Apply ARIA Kyverno policy pack
	kubectl apply -f platform/security/kyverno/policies/

gatekeeper-policies-apply: ## Apply sample Gatekeeper required-labels policy
	kubectl apply -f platform/security/gatekeeper/required-labels-template.yaml
	kubectl apply -f platform/security/gatekeeper/required-labels-constraint.yaml

rollouts-canary-apply: ## Apply sample Argo Rollouts canary assets
	kubectl apply -f platform/gitops/rollouts/analysis-template.yaml
	kubectl apply -f platform/mesh/istio/checkout-api-traffic.yaml
	kubectl apply -f platform/gitops/rollouts/checkout-api-rollout.yaml

istio-notes: ## Print Istio integration notes
	@sed -n '1,80p' platform/mesh/istio/README.md

thanos-notes: ## Print Thanos integration notes
	@sed -n '1,80p' platform/observability/thanos/README.md

vpa-apply: ## Apply VPA recommendation-only example for checkout-api
	kubectl apply -f platform/autoscaling/vpa/vpa-checkout-api.yaml

karpenter-notes: ## Print Karpenter integration notes
	@sed -n '1,120p' platform/autoscaling/karpenter/README.md

cluster-autoscaler-notes: ## Print Cluster Autoscaler notes
	@sed -n '1,80p' platform/autoscaling/cluster-autoscaler/README.md

trivy-scan: ## Run Trivy filesystem scan if Trivy is installed
	./platform/security/trivy/trivy-scan.sh

kubescape-notes: ## Print Kubescape posture scan notes
	@sed -n '1,80p' platform/security/kubescape/README.md

cert-manager-notes: ## Print cert-manager notes
	@sed -n '1,80p' platform/security/cert-manager/README.md


# HA/DR recovery
recovery-plan:
	curl -s -X POST http://localhost:8080/recovery/plan \
	  -H "Authorization: Bearer $$API_TOKEN" \
	  -H "Content-Type: application/json" \
	  -d '{"service":"checkout-api","failure_type":"node_failure","environment":"prod"}' | jq .

recovery-validate:
	curl -s -X POST http://localhost:8080/recovery/validate \
	  -H "Authorization: Bearer $$API_TOKEN" \
	  -H "Content-Type: application/json" \
	  -d '{"service":"checkout-api","replicas_ready":true,"traffic_restored":true,"data_restored":true,"alerts_resolved":true,"rto_met":true,"rpo_met":true}' | jq .

rto-rpo:
	curl -s -X POST http://localhost:8080/recovery/rto-rpo \
	  -H "Authorization: Bearer $$API_TOKEN" \
	  -H "Content-Type: application/json" \
	  -d '{"service":"checkout-api","rto_target_minutes":30,"rpo_target_minutes":15,"actual_recovery_minutes":12,"actual_data_loss_minutes":3}' | jq .

ha-pdb-apply:
	kubectl apply -f platform/ha-recovery/pdb/pdb-checkout-api.yaml

ha-topology-apply:
	kubectl apply -f platform/ha-recovery/topology-spread/deployment-topology-spread.yaml

velero-schedule-example:
	kubectl apply -f platform/ha-recovery/velero/backup-schedule.yaml

# ---- Operational intelligence last-mile integrations ----
observability-correlate: ## Correlate Prometheus/Loki/Tempo/Hubble evidence for checkout-api
	curl -s -X POST http://localhost:8080/observability/correlate \
	  -H "Authorization: Bearer $$API_TOKEN" \
	  -H "Content-Type: application/json" \
	  -d '{"service":"checkout-api","window_minutes":30,"deployment":{"recent_deployment":true,"revision":"abc123"}}' | jq .

slo-burn-alert: ## Evaluate SLO burn-rate and build Alertmanager payload
	curl -s -X POST http://localhost:8080/slo/burn-alert \
	  -H "Authorization: Bearer $$API_TOKEN" \
	  -H "Content-Type: application/json" \
	  -d '{"service":"checkout-api","total_requests":1000,"failed_requests":100,"slo_target":99.9,"window_minutes":30}' | jq .

chaos-schedule-plan: ## Build weekly chaos schedule plan without enabling execution
	curl -s -X POST http://localhost:8080/chaos/schedule \
	  -H "Authorization: Bearer $$API_TOKEN" \
	  -H "Content-Type: application/json" \
	  -d '{"service":"checkout-api","namespace":"demo","experiments":["pod-delete","cpu-hog"]}' | jq .

chaos-trends: ## Show resilience trends from operational memory
	curl -s http://localhost:8080/chaos/trends/checkout-api -H "Authorization: Bearer $$API_TOKEN" | jq .

kyverno-incident-sample: ## Ingest a sample Kyverno violation as an incident
	curl -s -X POST http://localhost:8080/webhooks/kyverno \
	  -H "Authorization: Bearer $$API_TOKEN" \
	  -H "Content-Type: application/json" \
	  -d '{"service":"checkout-api","namespace":"demo","policy":"require-probes","message":"readinessProbe is required","severity":"P2"}' | jq .

gatekeeper-incident-sample: ## Ingest a sample Gatekeeper violation as an incident
	curl -s -X POST http://localhost:8080/webhooks/gatekeeper \
	  -H "Authorization: Bearer $$API_TOKEN" \
	  -H "Content-Type: application/json" \
	  -d '{"service":"checkout-api","namespace":"demo","constraint":"required-labels","message":"owner label is required","severity":"P2"}' | jq .

chatops-approval-card: ## Render Slack/Mattermost-style approval card payload
	curl -s -X POST http://localhost:8080/chatops/approval-card \
	  -H "Authorization: Bearer $$API_TOKEN" \
	  -H "Content-Type: application/json" \
	  -d '{"approval_id":1,"incident_id":"INC-1","action":{"action":"argocd_sync","target":"checkout-api"}}' | jq .

chatops-thread-update: ## Render threaded evidence update payload
	curl -s -X POST http://localhost:8080/chatops/thread-update \
	  -H "Authorization: Bearer $$API_TOKEN" \
	  -H "Content-Type: application/json" \
	  -d '{"incident_id":"INC-1","evidence":[{"source":"metrics","summary":"p95 latency increased"}],"recommendation":"continue investigation"}' | jq .

llm-guardrails-validate: ## Validate LLM output grounding before using it operationally
	curl -s -X POST http://localhost:8080/llm/guardrails/validate \
	  -H "Authorization: Bearer $$API_TOKEN" \
	  -H "Content-Type: application/json" \
	  -d '{"answer":"Rollback checkout-api","sources":[],"evidence":[]}' | jq .


# --- Fixed signed webhook samples ---
# These use the current server-side signature contract:
# X-Timestamp + X-Nonce + X-Incident-Signature.
sample-alertmanager-signed:
	@tmp=$$(mktemp); \
	cp samples/alertmanager/high-latency.json $$tmp 2>/dev/null || cp samples/alertmanager_payload.json $$tmp; \
	headers=$$(ALERTMANAGER_WEBHOOK_SECRET=$${ALERTMANAGER_WEBHOOK_SECRET:-replace-with-long-random-alertmanager-secret} python3 scripts/hmac_sign.py ALERTMANAGER_WEBHOOK_SECRET $$tmp); \
	curl -s -X POST http://localhost:8080/webhooks/alertmanager \
	  -H "Content-Type: application/json" \
	  -H "$$(echo "$$headers" | sed -n '1p')" \
	  -H "$$(echo "$$headers" | sed -n '2p')" \
	  -H "$$(echo "$$headers" | sed -n '3p')" \
	  --data-binary @$$tmp; \
	rm -f $$tmp

sample-falco-signed:
	@tmp=$$(mktemp); \
	cp samples/falco/runtime-alert.json $$tmp 2>/dev/null || cp samples/falco_payload.json $$tmp; \
	headers=$$(FALCO_WEBHOOK_SECRET=$${FALCO_WEBHOOK_SECRET:-replace-with-long-random-falco-secret} python3 scripts/hmac_sign.py FALCO_WEBHOOK_SECRET $$tmp); \
	curl -s -X POST http://localhost:8080/webhooks/falco \
	  -H "Content-Type: application/json" \
	  -H "$$(echo "$$headers" | sed -n '1p')" \
	  -H "$$(echo "$$headers" | sed -n '2p')" \
	  -H "$$(echo "$$headers" | sed -n '3p')" \
	  --data-binary @$$tmp; \
	rm -f $$tmp

evals-benchmark:
	curl -s -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" http://localhost:8080/evals/benchmark | jq .

gitops-ai-propose:
	curl -s -X POST -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" \
	  "http://localhost:8080/gitops-ai/propose?service=checkout-api&issue=latency-regression&dry_run=true" | jq .


# --- AI-SRE maturity endpoints ---
evals-benchmark:
	curl -s -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" http://localhost:8080/evals/benchmark | jq .

evals-synthetic:
	curl -s -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" http://localhost:8080/evals/synthetic-incidents | jq .

gitops-ai-propose:
	curl -s -X POST -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" \
	  "http://localhost:8080/gitops-ai/propose?service=checkout-api&issue=latency-regression&dry_run=true" | jq .

ai-observability-evaluate:
	curl -s -X POST -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" \
	  -H "Content-Type: application/json" \
	  http://localhost:8080/ai-observability/evaluate \
	  -d '{"incident_id":"demo","service":"checkout-api","answer":"Rollback deployment after latency regression","sources":[{"title":"checkout-api deployment regression runbook"}]}' | jq .

investigation-graph-demo:
	curl -s -X POST -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" \
	  -H "Content-Type: application/json" \
	  http://localhost:8080/investigation-graph/invoke \
	  -d '{"incident":{"incident_id":"demo-graph","service":"checkout-api","severity":"P1","signals":["deployment","latency"]},"active_incidents":0}' | jq .

k8s-troubleshooter-demo:
	curl -s -X POST -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" \
	  -H "Content-Type: application/json" \
	  http://localhost:8080/kubernetes-troubleshooter/analyze \
	  -d '{"incident":{"service":"checkout-api","namespace":"default","pod":"checkout-api-abc","signals":["CrashLoopBackOff"]}}' | jq .

istio-agent-demo:
	curl -s -X POST -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" \
	  -H "Content-Type: application/json" \
	  http://localhost:8080/platform-agents/istio \
	  -d '{"incident":{"service":"checkout-api","namespace":"default","pod":"checkout-api-abc","signals":["istio","mtls","canary"]}}' | jq .

thanos-agent-demo:
	curl -s -X POST -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" \
	  -H "Content-Type: application/json" \
	  http://localhost:8080/platform-agents/thanos \
	  -d '{"incident":{"service":"checkout-api","signals":["historical","slo trend"],"window":"30d"}}' | jq .

domain-demo:
	curl -s -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" http://localhost:8080/domain/domains | jq .
	curl -s -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" http://localhost:8080/domain/services | jq .
	curl -s -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" http://localhost:8080/domain/scenarios | jq .

k8s-issues-normalized:
	curl -s -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" \
	  http://localhost:8080/evals/k8s-issues/normalized | jq .

k8s-issues-replay:
	curl -s -X POST -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" \
	  "http://localhost:8080/evals/k8s-issues/replay?limit=5" | jq .

kafka-agent-demo:
	curl -s -X POST -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" \
	  -H "Content-Type: application/json" \
	  http://localhost:8080/platform-agents/kafka \
	  -d '{"incident":{"service":"fraud-detection-engine","severity":"P1","signals":["kafka","consumer lag","streaming"],"topic":"transactions.stream","consumer_group":"fraud-detection-engine"}}' | jq .

eval-scorecard-demo:
	curl -s -X POST -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" \
	  -H "Content-Type: application/json" \
	  http://localhost:8080/evals/scorecard \
	  -d '{"route":["metrics","logs","kafka","rca"],"expected_nodes":["metrics","logs","kafka","rca"],"predicted_rca":"consumer_lag_growth","expected_rca":"consumer_lag_growth","recommendation":"rollback consumer deployment after approval"}' | jq .

## Security
install-pre-commit: ## Install pre-commit hooks (run once after clone)
	pip install pre-commit
	pre-commit install
	pre-commit install --hook-type commit-msg

scan-secrets: ## Run gitleaks and trufflehog against full repo
	pre-commit run gitleaks --all-files
	pre-commit run trufflehog --all-files

rag-simple-demo:
	curl -s -X POST -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" -H "Content-Type: application/json" http://localhost:8080/rag/simple -d '{"query":"kafka consumer lag fraud","service":"fraud-detection-engine"}' | jq .

rag-agentic-demo:
	curl -s -X POST -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" -H "Content-Type: application/json" http://localhost:8080/rag/agentic -d '{"incident":{"service":"fraud-detection-engine","domain":"aml_fraud","severity":"P1","signals":["kafka","consumer lag","rebalance"]}}' | jq .

rag-graph-demo:
	curl -s -X POST -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" -H "Content-Type: application/json" http://localhost:8080/rag/graph -d '{"query":"kafka lag rebalance fraud","service":"fraud-detection-engine","depth":1}' | jq .

ai-runtime-contract:
	curl -s -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" \
	  http://localhost:8080/ai-runtime/contract | jq .

ai-runtime-validate:
	curl -s -X POST -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" \
	  -H "Content-Type: application/json" \
	  http://localhost:8080/ai-runtime/validate-action \
	  -d '{"action":"customer_record.change","tool":"customer_record.change","approved":false,"actor_id":"aria-agent"}' | jq .

ai-runtime-cache:
	curl -s -X POST -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" \
	  -H "Content-Type: application/json" \
	  http://localhost:8080/ai-runtime/cache/analyze \
	  -d '{"previous_prompt":"system instructions + incident context","current_prompt":"system instructions + inserted text + incident context"}' | jq .

k8s-internals-summary:
	curl -s -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" http://localhost:8080/kubernetes-internals/summary | jq .

k8s-etcd-backups:
	curl -s -H "Authorization: Bearer $${API_TOKEN:-dev-user-token}" http://localhost:8080/kubernetes-internals/etcd/backups | jq .
