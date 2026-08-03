from __future__ import annotations

import hashlib, hmac, time


def verify_hmac(body: bytes, supplied: str | None, secret: str | None, *, prefix: str = "") -> bool:
    if not secret or not supplied: return False
    expected = prefix + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, supplied)


def verify_slack_signature(body: bytes, timestamp: str | None, signature: str | None, secret: str | None, tolerance: int = 300) -> bool:
    if not all([timestamp, signature, secret]): return False
    try:
        if abs(time.time() - int(timestamp)) > tolerance: return False
    except ValueError: return False
    base = b"v0:" + timestamp.encode() + b":" + body
    expected = "v0=" + hmac.new(secret.encode(), base, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
