from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RedactionResult:
    text: str
    redactions: list[dict[str, str]]


class SecretRedactor:
    """Redacts common secret patterns before logs/docs enter prompts, RAG, or reports."""

    PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
        ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
        ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
        ("generic_api_key", re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[^'\"\s]{8,}")),
        ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----")),
        ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
        ("connection_string_password", re.compile(r"(?i)(password=)[^;\s]+")),
    )

    def redact_text(self, text: str | None) -> RedactionResult:
        safe = text or ""
        redactions: list[dict[str, str]] = []
        for kind, pattern in self.PATTERNS:
            matches = list(pattern.finditer(safe))
            if matches:
                redactions.append({"type": kind, "count": str(len(matches))})
                safe = pattern.sub(f"[REDACTED:{kind}]", safe)
        return RedactionResult(text=safe, redactions=redactions)

    def redact_payload(self, payload: Any) -> Any:
        if isinstance(payload, str):
            return self.redact_text(payload).text
        if isinstance(payload, list):
            return [self.redact_payload(item) for item in payload]
        if isinstance(payload, dict):
            sanitized = {}
            for key, value in payload.items():
                if re.search(r"(?i)(password|secret|token|api_key|apikey|private_key)", str(key)):
                    sanitized[key] = "[REDACTED:key-name]"
                else:
                    sanitized[key] = self.redact_payload(value)
            return sanitized
        return payload
