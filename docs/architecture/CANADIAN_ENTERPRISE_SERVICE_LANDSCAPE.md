# ARIA — Canadian Enterprise Service Landscape

ARIA now models a realistic multi-domain Canadian enterprise environment.

## Domains

- Capital Markets
- Retail Banking
- Wealth Management
- AML and Fraud
- Insurance
- Retail and E-Commerce

## Why This Matters

ARIA is not tied to a single demo service. It can reason across multiple enterprise business units with different SLOs, risk profiles, and incident patterns.

## Service Registry

```text
config/canadian_enterprise_services.yaml
```

The registry stores:

- domain
- service name
- owner team
- runtime
- language/framework
- SLOs
- risk profile
- common incidents

## API Endpoints

```text
GET /domain/domains
GET /domain/services
GET /domain/services?domain=capital_markets
GET /domain/services/{service_name}
GET /domain/scenarios
```

## Example Services

| Domain | Example Services |
|---|---|
| Capital Markets | trade-execution-api, market-data-service, settlement-engine |
| Retail Banking | payment-processing-api, customer-profile-service, transaction-ledger-service |
| Wealth Management | portfolio-analytics-api, advisor-dashboard-service, investment-recommendation-engine |
| AML/Fraud | fraud-detection-engine, aml-screening-service, transaction-monitoring-service |
| Insurance | claims-processing-api, policy-engine, document-processing-ai |
| Retail/E-Commerce | checkout-api, inventory-service, recommendation-engine |

## Operational Value

Each domain highlights a different ARIA capability:

| Domain | ARIA Capability |
|---|---|
| Capital Markets | low-latency RCA and HA |
| Retail Banking | payment reliability and SLO burn |
| Wealth Management | AI/ML workload observability |
| AML/Fraud | Kafka/event intelligence |
| Insurance | workflow and AI document pipeline resilience |
| Retail/E-Commerce | canary, autoscaling, checkout reliability |
