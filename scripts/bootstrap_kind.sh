#!/usr/bin/env bash
set -euo pipefail
for cmd in docker kind kubectl helm; do
  command -v "$cmd" >/dev/null || { echo "$cmd is required"; exit 1; }
done
make kind-create
make k8s-bootstrap
make k8s-deploy-app
cat <<'EOF'
Kind setup completed.
Run this in one terminal:
  make port-forward
Then run this in another terminal:
  make ingest
  make sample-investigation
EOF
