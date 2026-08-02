#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then
  echo ".env already exists; not overwriting."
  exit 0
fi
gen() { python - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
}
api_token="$(gen)"
approver_token="$(gen)"
webhook_secret="$(python - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
)"
cat > .env <<EOF
APP_ENV=local
DATABASE_URL=sqlite:///./incident_investigator.db
REDIS_URL=redis://localhost:6379/0
EVENT_BUS_BACKEND=inmemory
API_AUTH_TOKEN=$api_token
ALERTMANAGER_WEBHOOK_SECRET=$webhook_secret
FALCO_WEBHOOK_SECRET=$falco_secret
API_USER_ID=local-sre
API_USER_ROLE=sre
API_USER_TEAM=platform
API_AUTH_TOKENS=$approver_token:incident-commander:incident-commander:platform
COLLABORATION_PROVIDER=stdout
OTEL_ENABLED=false
EOF
echo "Generated .env with unique local secrets."
echo "Requester bearer token: $api_token"
echo "Approver bearer token:  $approver_token"
echo "Alertmanager secret:   $webhook_secret"
