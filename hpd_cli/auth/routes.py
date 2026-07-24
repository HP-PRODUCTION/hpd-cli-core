"""Auth routes: login, refresh, token verification."""
import os
from fastapi import APIRouter, HTTPException, Depends
from hpd_cli.auth.jwt import (
    LoginRequest,
    TokenResponse,
    TokenPayload,
    create_token,
    verify_token,
    require_auth,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse, summary="Iniciar sesion")
def login(body: LoginRequest):
    """Intercambia un token maestro por un par access+refresh JWT.

    El `token` debe coincidir con `HPD_JWT_MASTER_TOKEN` del entorno.
    Si no esta configurado, cualquier token no vacio es aceptado (dev mode).
    """
    master = os.environ.get("HPD_JWT_MASTER_TOKEN", "")
    if master and body.token != master:
        raise HTTPException(status_code=401, detail="Token maestro invalido")

    access = create_token("admin", "access", scope="admin")
    refresh = create_token("admin", "refresh", scope="admin")

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=3600,
    )


@router.post("/refresh", response_model=TokenResponse, summary="Renovar token")
def refresh(token_payload: TokenPayload = Depends(require_auth)):
    """Renueva un access token usando un refresh token valido."""
    if token_payload.typ != "refresh":
        raise HTTPException(status_code=401, detail="Se requiere un refresh token")

    access = create_token(token_payload.sub, "access", scope=token_payload.scp)
    refresh = create_token(token_payload.sub, "refresh", scope=token_payload.scp)

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=3600,
    )


@router.get("/verify", summary="Verificar token")
def verify(token_payload: TokenPayload = Depends(require_auth)):
    """Verifica si el token actual es valido."""
    return {
        "valid": True,
        "subject": token_payload.sub,
        "scope": token_payload.scp,
        "token_type": token_payload.typ,
    }
