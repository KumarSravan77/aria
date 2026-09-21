#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then
  if ! grep -q '^ARIA_INTEGRATION_SECRET=' .env; then
    PYTHON_BIN=${PYTHON_BIN:-$(command -v python3 || command -v python)}
    integration_secret=$("$PYTHON_BIN" -c 'import secrets; print(secrets.token_urlsafe(32))')
    printf '\nARIA_INTEGRATION_SECRET=%s\n' "$integration_secret" >> .env
    echo "Added missing ARIA integration secret to .env."
  fi
  echo ".env already exists; not overwriting."
  exit 0
fi
PYTHON_BIN=${PYTHON_BIN:-$(command -v python3 || command -v python)}
gen() { "$PYTHON_BIN" - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
}
api_token="$(gen)"
approver_token="$(gen)"
webhook_secret="$("$PYTHON_BIN" - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
)"
falco_secret="$(gen)"
integration_secret="$(gen)"
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
ARIA_INTEGRATION_SECRET=$integration_secret
EOF
echo "Generated .env with unique local secrets."
echo "Secrets were written to .env and were not printed."
