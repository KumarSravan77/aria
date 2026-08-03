# Production telemetry storage

This Terraform root provisions the encrypted, private AWS archive bucket used by the production telemetry profiles. It deliberately does not create a Kubernetes cluster or long-lived access keys. Bind the Vector service account to a least-privilege cloud role and inject the bucket name through the deployment system.

Run `terraform init`, review `terraform plan`, and apply only through the organization's approved infrastructure workflow. The local profile continues to use MinIO and needs no cloud account.

