import hmac
import hashlib
import time
import uuid
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from server.api.security import require_auth, _parse_token_map, _verify_replay_protection
from server.api.nonce_store import NonceStore
from server.config import settings


def test_require_auth_rejects_missing_token():
    with pytest.raises(HTTPException):
        require_auth(None)


def test_require_auth_accepts_configured_token():
    user = require_auth(HTTPAuthorizationCredentials(scheme='Bearer', credentials=settings.api_auth_token))
    assert user.role == 'sre'
    assert user.id == 'test-sre'


def test_require_auth_accepts_secondary_approver_token():
    user = require_auth(HTTPAuthorizationCredentials(scheme='Bearer', credentials='test-approver-token'))
    assert user.id == 'test-commander'
    assert user.role == 'incident-commander'


def test_hmac_signature_format_example():
    body = b'{"status":"firing"}'
    sig = 'sha256=' + hmac.new(settings.alertmanager_webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    assert sig.startswith('sha256=')


def test_token_map_is_not_cached_for_runtime_revocation():
    first = _parse_token_map()
    second = _parse_token_map()
    assert first == second
    assert not hasattr(_parse_token_map, "cache_info")


# ── Replay protection ────────────────────────────────────────────────────

def fresh_nonce() -> str:
    return str(uuid.uuid4())


def test_replay_protection_accepts_fresh_timestamp_and_nonce():
    ts = str(int(time.time()))
    nonce = fresh_nonce()
    # Must not raise
    _verify_replay_protection(ts, nonce, tolerance=300)


def test_replay_protection_rejects_missing_timestamp():
    with pytest.raises(HTTPException) as exc:
        _verify_replay_protection(None, fresh_nonce(), tolerance=300)
    assert exc.value.status_code == 401
    assert 'X-Timestamp' in exc.value.detail


def test_replay_protection_rejects_non_integer_timestamp():
    with pytest.raises(HTTPException) as exc:
        _verify_replay_protection('not-a-number', fresh_nonce(), tolerance=300)
    assert exc.value.status_code == 400


def test_replay_protection_rejects_stale_timestamp():
    stale = str(int(time.time()) - 400)  # 400s ago, tolerance=300
    with pytest.raises(HTTPException) as exc:
        _verify_replay_protection(stale, fresh_nonce(), tolerance=300)
    assert exc.value.status_code == 401
    assert 'replay' in exc.value.detail.lower() or 'tolerance' in exc.value.detail.lower()


def test_replay_protection_rejects_future_timestamp():
    future = str(int(time.time()) + 400)  # 400s in future, tolerance=300
    with pytest.raises(HTTPException) as exc:
        _verify_replay_protection(future, fresh_nonce(), tolerance=300)
    assert exc.value.status_code == 401


def test_replay_protection_rejects_missing_nonce():
    ts = str(int(time.time()))
    with pytest.raises(HTTPException) as exc:
        _verify_replay_protection(ts, None, tolerance=300)
    assert exc.value.status_code == 401
    assert 'X-Nonce' in exc.value.detail


def test_replay_protection_rejects_reused_nonce():
    store = NonceStore()   # fresh in-memory store for isolation
    ts = str(int(time.time()))
    nonce = fresh_nonce()
    # First use: accepted
    assert store.consume(nonce, ttl=60) is True
    # Second use (replay): rejected
    assert store.consume(nonce, ttl=60) is False


def test_nonce_store_allows_different_nonces():
    store = NonceStore()
    n1, n2 = fresh_nonce(), fresh_nonce()
    assert store.consume(n1, ttl=60) is True
    assert store.consume(n2, ttl=60) is True


def test_replay_protection_full_path_rejects_replay(monkeypatch):
    """Simulate the complete accept-then-replay flow using _verify_replay_protection directly."""
    # Monkeypatch the module-level nonce_store so each test gets a clean store
    from server.api import security as sec_module
    fresh_store = NonceStore()
    monkeypatch.setattr(sec_module, 'nonce_store', fresh_store)

    ts = str(int(time.time()))
    nonce = fresh_nonce()

    # First request: accepted
    _verify_replay_protection(ts, nonce, tolerance=300)

    # Immediate replay with same nonce: rejected
    with pytest.raises(HTTPException) as exc:
        _verify_replay_protection(ts, nonce, tolerance=300)
    assert exc.value.status_code == 401
    assert 'replay' in exc.value.detail.lower()
