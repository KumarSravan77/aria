# ARIA On-Call SRE Copilot

ARIA now follows the engineer across development and incident response without granting the model direct production authority.

## Surfaces

- **Alertmanager and PagerDuty** create or update durable incidents.
- **Slack, Teams, and Mattermost** receive incident briefs, threaded evidence, and approval requests.
- **Codex, Cursor, and other MCP clients** can read incident timelines, service telemetry, SDLC context, and start evidence-only investigations.
- **GitHub/CI/CD** can post code-change, deployment, alert-change, runbook, decision, and incident-outcome events.
- **ARIA API and database** maintain identity links, audit trails, bounded investigation checkpoints, verified memory, and incident timelines.

## On-call sequence

```text
alert → signed intake → deduplicated incident → telemetry investigation
      → SDLC/deployment correlation → incident room update
      → recommendation → ReBAC/policy/4-eyes approval
      → deterministic Celery/GitOps execution → recovery validation
      → RCA draft → candidate memory → commander verification
```

Temporal links are explicitly labelled as correlations, not causes. Only verified operational-memory entries may influence future remediation ranking.

## Configuration

Set secrets through a secret manager or local `.env`; never commit them:

```text
PAGERDUTY_WEBHOOK_SECRET
SLACK_SIGNING_SECRET
SLACK_BOT_TOKEN
SLACK_DEFAULT_CHANNEL
TEAMS_WEBHOOK_URL
ARIA_API_TOKEN (MCP client only)
ARIA_API_URL (MCP client only)
```

Use `integrations/slack/manifest.yaml` as the Slack app manifest after replacing the public host. Use `integrations/mcp/codex.example.json` as an MCP client template.

## SDLC event contract

`POST /oncall/sdlc/events` requires ARIA authentication and ReBAC access:

```json
{
  "event_id": "github:deployment:1234",
  "event_type": "deployment",
  "service": "banking-api",
  "environment": "prod",
  "revision": "abc123",
  "occurred_at": "2026-08-03T14:00:00Z",
  "metadata": {"workflow": "deploy", "url": "https://example.invalid/run/1234"}
}
```

Allowed types are `code_change`, `pull_request`, `deployment`, `alert_change`, `runbook_change`, `engineer_decision`, and `incident_outcome`.

## Safety boundary

The MCP server exposes no approve or execute tools. Slack interactions verify Slack signatures but return approval context only; the user must still authenticate to ARIA, pass identity mapping, ReBAC, policy, separation-of-duties, and the existing approval service before execution is queued.
