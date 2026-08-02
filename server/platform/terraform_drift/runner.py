from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional


class TerraformPlanRunner:
    """Runs Terraform plan in read-only JSON mode for drift analysis.

    Safety defaults:
    - no apply
    - no auto-approve
    - plan output only
    - command execution must be explicitly allowed by caller
    """

    def build_commands(self, working_dir: str, plan_file: str = "tfplan") -> Dict[str, Any]:
        return {
            "working_dir": working_dir,
            "commands": [
                ["terraform", "init", "-input=false"],
                ["terraform", "plan", "-refresh=true", "-out", plan_file, "-input=false"],
                ["terraform", "show", "-json", plan_file],
            ],
            "safety": {"apply_allowed": False, "approval_required": True, "dry_run": True},
        }

    def run_plan_json(self, working_dir: str, allow_execute: bool = False, timeout_seconds: int = 180) -> Dict[str, Any]:
        if not allow_execute:
            return {
                "status": "dry_run_only",
                "message": "Terraform command execution disabled. Set allow_execute=True in a controlled environment.",
                **self.build_commands(working_dir),
            }
        root = Path(working_dir)
        if not root.exists():
            return {"status": "error", "message": f"working_dir does not exist: {working_dir}"}
        init = subprocess.run(["terraform", "init", "-input=false"], cwd=root, text=True, capture_output=True, timeout=timeout_seconds)
        if init.returncode != 0:
            return {"status": "error", "stage": "init", "stdout": init.stdout, "stderr": init.stderr}
        plan = subprocess.run(["terraform", "plan", "-refresh=true", "-out", "tfplan", "-input=false"], cwd=root, text=True, capture_output=True, timeout=timeout_seconds)
        if plan.returncode not in (0, 2):
            return {"status": "error", "stage": "plan", "stdout": plan.stdout, "stderr": plan.stderr}
        show = subprocess.run(["terraform", "show", "-json", "tfplan"], cwd=root, text=True, capture_output=True, timeout=timeout_seconds)
        if show.returncode != 0:
            return {"status": "error", "stage": "show", "stdout": show.stdout, "stderr": show.stderr}
        try:
            return {"status": "ok", "terraform_plan": json.loads(show.stdout)}
        except json.JSONDecodeError as exc:
            return {"status": "error", "stage": "parse", "message": str(exc), "stdout": show.stdout[:2000]}
