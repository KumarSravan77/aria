#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server.platform.spec_engine import SpecDrivenEvaluator, SpecLoader


def main() -> int:
    service_id = sys.argv[1] if len(sys.argv) > 1 else "payments-api"
    result = SpecDrivenEvaluator(SpecLoader(ROOT)).evaluate_service(service_id)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
