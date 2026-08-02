from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    failures: list[tuple[str, str, str]] = []
    modules = []
    for path in Path("server").rglob("*.py"):
        if path.name == "__init__.py":
            continue
        module_name = ".".join(path.with_suffix("").parts)
        modules.append(module_name)

    for module_name in modules:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - diagnostic script
            failures.append((module_name, type(exc).__name__, str(exc)))

    print(f"modules_scanned={len(modules)}")
    print(f"import_failures={len(failures)}")
    for module_name, error_type, message in failures:
        print(f"{module_name}: {error_type}: {message}")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
