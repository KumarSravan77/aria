# AWS OIDC and FinOps project foundation

ARIA provides a reusable baseline for every portfolio project that uses AWS. It eliminates long-lived AWS access keys from GitHub Actions and makes cost ownership visible before deployment.

## Implemented controls

- Reusable GitHub Actions identity check using OIDC and short-lived AWS STS credentials.
- Exact repository and protected-environment matching in the IAM trust policy.
- Separate deployment roles per project/environment; project-owned permissions remain least privilege.
- Rejection of `AdministratorAccess` and `PowerUserAccess` attachments.
- Expected-account validation before an AWS operation.
- Tag-filtered monthly budgets with forecasted 80% and actual 100% alerts.
- Optional account-level Cost Anomaly Detection with immediate impact alerts.
- Mandatory `Project`, `Environment`, `Owner`, `CostCenter`, and `ManagedBy` tags.

The reusable workflow proves identity. Each project must own deployment steps and a narrow IAM policy. AWS credentials cannot safely be passed from the identity job to a separate deployment job.

## One-time account bootstrap

1. Create GitHub's OIDC provider with URL `https://token.actions.githubusercontent.com` and audience `sts.amazonaws.com` once per AWS account.
2. Apply `platform/aws-foundation/terraform` for every project/environment using an administrator bootstrap session.
3. Set up a protected GitHub Environment with the same name used by Terraform.
4. Store the role output as environment secret `AWS_ROLE_ARN` and expected account as `AWS_ACCOUNT_ID`.
5. Require reviewers for production and restrict its deployment branch to `main`.
6. Activate the `Project` cost-allocation tag in AWS Billing, then allow billing data time to populate.
7. Confirm the alert email subscriptions.

The bootstrap identity is deliberately not stored in GitHub. It creates the initial federated trust.

## Existing and new projects

`platform/aws-foundation/project-standard.yaml` registers ARIA, Canadian Retail MLOps, and Fire Drill Chaos Engineering. To onboard another project, add it to the registry, instantiate the Terraform module with an exact GitHub repository/environment, create a resource-scoped deployment policy, and copy the caller example.

Only one service-based anomaly monitor may exist per account. Set `create_account_anomaly_monitor = true` in exactly one foundation instance. Project-level attribution comes from budgets and cost-allocation tags.

## Operational response

| Signal | Operator response |
|---|---|
| Forecast reaches 80% | Review month-to-date service and project-tag spend; pause optional labs. |
| Actual reaches 100% | Open a cost incident and block non-essential deployments. |
| Cost anomaly | Identify service, account, region, and resource; contain unexpected spend. |
| Missing tags | Fail policy review and assign ownership before deployment. |
| Wrong AWS account | Credential configuration fails through `allowed-account-ids`. |

Budget alerts do not stop resources. Automated shutdown needs a separately approved runbook because it may interrupt production.

## Validation boundary

Repository tests validate the trust scope, credential controls, tags, budget, anomaly resources, and reusable workflow. End-to-end activation still requires an AWS account, confirmed notification address, OIDC provider, protected GitHub Environments, and project-specific IAM policies. No cloud resource is created merely by merging these files.
