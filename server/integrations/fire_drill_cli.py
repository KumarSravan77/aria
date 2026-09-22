from __future__ import annotations

import json
import sys

from server.integrations.fire_drill import FireDrillInvestigationRequest, investigate_fire_drill


def main() -> None:
    request = FireDrillInvestigationRequest.model_validate(json.load(sys.stdin))
    print(json.dumps(investigate_fire_drill(request), sort_keys=True))


if __name__ == "__main__":
    main()
