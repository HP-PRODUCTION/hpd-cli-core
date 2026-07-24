"""JWT token creation, verification and dependency injection for FastAPI."""
import os
import time
import hashlib
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel


# === Constants =============================================

SECRET_KEY = os.getenv("HPD_JWT_SECRET", hashlib.sha256(os.urandom(64)).hexdigest())
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = int(os.getenv("HPD_JWT_ACCESS_EXPIRE", "3600"))       # 1h
REFRESH_TOKEN_EXPIRE = int(os.getenv("HPD_JWT_REFRESH_EXPIRE", "2592000"))  # 30d

security_scheme = HTTPBearer(auto_error=False)


# === Models ================================================

class TokenPayload(BaseModel):
    sub: str       # subject (user/role)
    exp: int       # expiry timestamp
    iat: int       # issued at
    typ: str       # "access" | "refresh"
    scp: str = ""  # scope (role)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    token: str


# === PyJWT-less implementation (uses HMAC via hashlib + base64) ===

import hmac
import base64
import json


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64decode(s: str) -> bytes:
    s += "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


def _hmac_sign(payload: str) -> str:
    sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).digest()
    return _b64url(sig)


def _encode_jwt(header: dict, payload: dict) -> str:
    h = _b64url(json.dumps(header).encode())
    p = _b64url(json.dumps(payload).encode())
    s = _hmac_sign(f"{h}.{p}")
    return f"{h}.{p}.{s}"


def _decode_jwt(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        h, p, s = parts
        expected = _hmac_sign(f"{h}.{p}")
        if not hmac.compare_digest(s, expected):
            return None
        return json.loads(_b64decode(p))
    except Exception:
        return None


# === Public API ============================================

def create_token(subject: str, token_type: str = "access",
                 expires_in: Optional[int] = None, scope: str = "") -> str:
    """Create a JWT token (access or refresh)."""
    now = int(time.time())
    exp = expires_in or (ACCESS_TOKEN_EXPIRE if token_type == "access" else REFRESH_TOKEN_EXPIRE)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + exp,
        "typ": token_type,
        "scp": scope,
    }
    header = {"alg": "HS256", "typ": "JWT"}
    return _encode_jwt(header, payload)


def verify_token(token: str, expected_type: str = "access") -> Optional[TokenPayload]:
    """Verify and decode a JWT token."""
    data = _decode_jwt(token)
    if not data:
        return None
    now = time.time()
    if data.get("exp", 0) < now:
        return None
    if data.get("typ") != expected_type:
        return None
    return TokenPayload(
        sub=data["sub"],
        exp=data["exp"],
        iat=data.get("iat", 0),
        typ=data["typ"],
        scp=data.get("scp", ""),
    )


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
) -> TokenPayload:
    """FastAPI dependency: requires valid access token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere token de autenticacion",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = verify_token(credentials.credentials, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
) -> Optional[TokenPayload]:
    """FastAPI dependency: optional auth (returns None if no token)."""
    if not credentials:
        return None
    return verify_token(credentials.credentials, "access")
