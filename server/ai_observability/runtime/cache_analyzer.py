from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PromptCacheAnalyzer:
    def prefix_match(self, previous_prompt: str, current_prompt: str) -> dict:
        match = 0
        for a, b in zip(previous_prompt, current_prompt):
            if a != b:
                break
            match += 1
        max_len = max(len(current_prompt), 1)
        return {
            "prefix_match_chars": match,
            "current_chars": len(current_prompt),
            "previous_chars": len(previous_prompt),
            "cache_prefix_ratio": round(match / max_len, 4),
            "break_position": match if match < min(len(previous_prompt), len(current_prompt)) else None,
        }
