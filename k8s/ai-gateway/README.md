# Envoy AI Gateway integration for ARIA

ARIA uses Envoy AI Gateway as the single downstream LLM access point. ARIA sends an OpenAI-compatible request to the gateway; provider credentials, translation, model routing, fallback, rate limits, and provider telemetry stay outside the application.

## Version baseline

The manifests use the stable `aigateway.envoyproxy.io/v1beta1` API introduced before GA. The install target is Envoy AI Gateway `v1.1.0` with Envoy Gateway `v1.8.1`.

## Install control plane

```bash
make ai-gateway-install
```

Then create provider credentials without committing them:

```bash
kubectl -n ai-gateway create secret generic openai-api-key \
  --from-literal=apiKey="$OPENAI_API_KEY"
```

Apply the example gateway resources:

```bash
kubectl apply -f k8s/ai-gateway/gateway.yaml
kubectl apply -f k8s/ai-gateway/openai-backend.yaml
kubectl apply -f k8s/ai-gateway/route.yaml
```

The provider manifest is an example starting point. For Bedrock/Azure/Anthropic, add another `AIServiceBackend` plus its `BackendSecurityPolicy`, then attach it to the `AIGatewayRoute` according to the current Envoy AI Gateway provider documentation.

## ARIA application configuration

```env
LLM_ENABLED=true
LLM_PROVIDER=envoy-ai-gateway
AI_GATEWAY_BASE_URL=http://<gateway-address>
AI_GATEWAY_MODEL=aria-reasoning
AI_GATEWAY_TENANT_ID=aria
```

The application never needs the upstream OpenAI/Bedrock/Azure credential.
