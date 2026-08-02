from __future__ import annotations

from dataclasses import dataclass
import random
import time


@dataclass
class ReplayContext:
    deterministic: bool = False
    fixed_timestamp: float | None = None
    seed: int = 42

    def now(self) -> float:
        return self.fixed_timestamp if self.fixed_timestamp is not None else time.time()

    def activate(self) -> None:
        if self.deterministic:
            random.seed(self.seed)
