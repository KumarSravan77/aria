from __future__ import annotations

from typing import Any, Protocol


class LLMClient(Protocol):
    """Minimal interface used by ARIA reasoning components."""

    model: str

    def generate(self, prompt: str, *, system: str | None = None) -> dict[str, Any]:
        ...
