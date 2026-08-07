# ARIA and On-Call SRE integration

ARIA is the AIOps intelligence plane. On-Call SRE is the incident authority and
response plane. ARIA never receives paging credentials and On-Call never needs
direct access to telemetry backends.

```text
telemetry -> ARIA correlation/RCA -> signed intelligence signal -> On-Call SRE
                                                              -> page/approve/execute
recovery evidence <- ARIA validation <- execution result <----+
```

ARIA sends `schema_version: 1.0` JSON to
`POST /api/v1/intelligence/aria`. The request includes timestamp, unique nonce
and HMAC-SHA256 signature headers. On-Call rejects expired requests, invalid
signatures and replayed nonces. The signal carries a W3C `traceparent` so ARIA,
On-Call and Opik can display the same end-to-end workflow.

Configure both services with the same randomly generated integration secret,
injected from a secret manager. Do not reuse the admin token or route token.
ARIA degrades gracefully when On-Call is unavailable; a failed delivery never
causes ARIA to execute remediation itself.

On ARIA:

```text
ON_CALL_SRE_URL=http://on-call-sre
ON_CALL_SRE_INTEGRATION_SECRET=<secret-manager-reference>
```

On On-Call SRE:

```text
ARIA_INTEGRATION_SECRET=<same-secret-manager-reference>
ARIA_ROUTE_TOKEN=<dedicated-route-token>
```

Create a normal On-Call route whose source is `aria`, then publish using
`POST /integrations/on-call/publish`. Evidence URIs and recommendations are
stored in the incident audit history; recommended actions are not executed.

Both services emit OpenTelemetry spans. Configure OTLP over HTTP to point at a
self-hosted Opik deployment. Opik observes agent steps and evaluations without
becoming an authorization dependency. Never export secrets or unredacted
customer data as span attributes.
