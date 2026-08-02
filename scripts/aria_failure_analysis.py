#!/usr/bin/env python3
"""Minimal GitHub Actions failure analysis hook for ARIA.

This script is intentionally safe: it summarizes the failure event and produces a
manual review report. Future versions can call the DevOps Agent API after auth,
RAG authorization, and approval policy are configured.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main(path: str) -> None:
    event = json.loads(Path(path).read_text())
    print("# ARIA AI DevOps Failure Analysis")
    print()
    print(f"Workflow: {event.get('workflow')}")
    print(f"Repository: {event.get('repository')}")
    print(f"Branch: {event.get('branch')}")
    print(f"Commit: {event.get('commit')}")
    print(f"Run: {event.get('run_url')}")
    print()
    print("## Initial Classification")
    print("- Type: pipeline_failure")
    print("- Severity: requires_triage")
    print("- Mode: dry_run")
    print()
    print("## Next ARIA Actions")
    print("1. Fetch workflow logs through GitHub API.")
    print("2. Sanitize untrusted log/input content.")
    print("3. Classify build, test, Docker, Terraform, Helm, or deployment failure.")
    print("4. Query ReBAC-aware runbooks through Operational Memory Service.")
    print("5. Generate remediation plan and PR proposal only after approval policy passes.")


if __name__ == "__main__":
    main(sys.argv[1])
