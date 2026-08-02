from __future__ import annotations
import hmac
import hashlib
import time
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from server.config import settings
from server.models.schemas import UserContext
from server.api.nonce_store import nonce_store

bearer_scheme = HTTPBearer(auto_error=False)


def _parse_token_map_cached(raw_tokens: str, primary_token: str, user_id: str, user_role: str, user_team: str) -> tuple[tuple[str, UserContext], ...]:
    entries: list[tuple[str, UserContext]] = []
    for item in [part.strip() for part in raw_tokens.split(',') if part.strip()]:
        pieces = item.split(':')
        if len(pieces) != 4:
            continue
        token, mapped_user_id, role, team = pieces
        entries.append((token, UserContext(id=mapped_user_id, role=role, team=team)))
    entries.append((primary_token, UserContext(id=user_id, role=user_role, team=user_team)))
    return tuple(entries)


def _parse_token_map() -> tuple[tuple[str, UserContext], ...]:
    return _parse_token_map_cached(
        settings.api_auth_tokens or '',
        settings.api_auth_token,
        settings.api_user_id,
        settings.api_user_role,
        settings.api_user_team,
    )


def require_auth(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> UserContext:
    if not credentials or credentials.scheme.lower() != 'bearer':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing bearer token')
    for token, user in _parse_token_map():
        if hmac.compare_digest(credentials.credentials, token):
            return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid bearer token')


def _verify_replay_protection(
    x_timestamp: str | None,
    x_nonce: str | None,
    tolerance: int | None = None,
) -> None:
    """Enforce freshness (X-Timestamp) and uniqueness (X-Nonce) on webhook requests.

    Both headers must be present. The timestamp must be within tolerance of
    server time. The nonce must not have been seen before (Redis SET nx ex).
    """
    tol = tolerance if tolerance is not None else settings.webhook_timestamp_tolerance_seconds

    if not x_timestamp:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Missing X-Timestamp header (replay protection required)')
    try:
        ts = int(x_timestamp)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Invalid X-Timestamp: must be a Unix epoch integer')
    age = abs(time.time() - ts)
    if age > tol:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f'Timestamp out of tolerance (age={age:.0f}s, max={tol}s). Possible replay.')

    if not x_nonce:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Missing X-Nonce header (replay protection required)')
    if not nonce_store.consume(x_nonce, ttl=tol * 2):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Nonce already used — replay attack rejected')


async def require_alertmanager_signature(
    request: Request,
    x_incident_signature: str | None = Header(default=None, alias='X-Incident-Signature'),
    x_timestamp: str | None = Header(default=None, alias='X-Timestamp'),
    x_nonce: str | None = Header(default=None, alias='X-Nonce'),
) -> bytes:
    body = await request.body()
    expected = 'sha256=' + hmac.new(
        settings.alertmanager_webhook_secret.encode('utf-8'),
        body,
        hashlib.sha256,
    ).hexdigest()
    if not x_incident_signature or not hmac.compare_digest(x_incident_signature, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Invalid Alertmanager webhook signature')
    _verify_replay_protection(x_timestamp, x_nonce)
    return body


async def require_falco_signature(
    request: Request,
    x_incident_signature: str | None = Header(default=None, alias='X-Incident-Signature'),
    x_timestamp: str | None = Header(default=None, alias='X-Timestamp'),
    x_nonce: str | None = Header(default=None, alias='X-Nonce'),
) -> bytes:
    body = await request.body()
    expected = 'sha256=' + hmac.new(
        settings.falco_webhook_secret.encode('utf-8'),
        body,
        hashlib.sha256,
    ).hexdigest()
    if not x_incident_signature or not hmac.compare_digest(x_incident_signature, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Invalid Falco webhook signature')
    _verify_replay_protection(x_timestamp, x_nonce)
    return body
