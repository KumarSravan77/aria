from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from server.platform.terraform_drift.runner import TerraformPlanRunner


class TerraformPlanExecutor(TerraformPlanRunner):
    """Compatibility wrapper for parsing plan JSON and dry-run execution."""

    def parse_plan_json(self, path: str) -> Dict[str, Any]:
        return json.loads(Path(path).read_text())
