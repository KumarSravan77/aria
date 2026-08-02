# Platform Self-Service Gap Fixes

This update hardens and completes the spec-driven self-service platform API.

## Fixed

1. **Authentication on platform routes**
   All `/platform/self-service/*` routes now require bearer authentication via `require_auth`.

2. **Service ReBAC on service-specific operations**
   Snapshot, service review, report generation, remediation PR planning, spec evaluation, Terraform drift analysis, CI/CD generation, issue events, and secrets governance now check service access when a `service_id` is present.

3. **Missing endpoints wired**
   Added:
   - `POST /platform/self-service/cicd/generate`
   - `POST /platform/self-service/issue-event`

4. **Spec evaluation uses request body**
   `/platform/self-service/specs/evaluate` now requires and evaluates the requested `service_id` instead of silently defaulting to `payments-api`.

5. **Self-service service profile creation**
   Onboarding now creates `specs/service-profiles/<service_id>.yaml` when missing, using the requested service profile and inferred golden path.

6. **Real GitHub Actions workflow output**
   CI/CD generation now returns concrete workflow file content and can optionally write files to disk with `write_files=true` and `output_dir`.

## Safety behavior

- Existing service operations enforce ReBAC.
- New service onboarding is limited to platform operators: `admin`, `sre`, or `incident-commander`.
- Terraform command generation is treated as platform-operator only.
- Generated CI/CD files are deterministic starter artifacts, not executed automatically.

## Regression coverage

Added `tests/test_platform_gap_fixes.py` covering:

- unauthenticated platform requests are rejected
- `/specs/evaluate` evaluates the requested service
- CI/CD and issue-event endpoints are reachable
- onboarding creates service profiles
- CI/CD generator writes a real GitHub Actions workflow file
