from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TokenTracker:
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0

    def add(self, input_tokens: int = 0, output_tokens: int = 0, cached_tokens: int = 0) -> dict:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.cached_tokens += cached_tokens
        return self.summary()

    def summary(self) -> dict:
        total = self.input_tokens + self.output_tokens
        cache_base = self.input_tokens + self.cached_tokens
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_tokens": self.cached_tokens,
            "total_tokens": total,
            "cache_hit_rate": round(self.cached_tokens / max(cache_base, 1), 4),
        }
