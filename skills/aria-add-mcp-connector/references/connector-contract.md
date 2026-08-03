# Connector contract

Return `available`, `source`, `operation`, `resource_id`, `observed_at`, `retrieved_at`, `authorization_scope`, `redacted`, `evidence`, `link`, and `error`.

Require bounded timeout/response, pagination, safe-read retries, circuit breaker, schema validation, structured errors, correlation ID, audit event, metric and trace. Expose explicit operations such as `search_issues` or `get_build`, never generic LLM command execution.
