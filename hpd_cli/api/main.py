import os
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from hpd_cli.api.system_checks import (
    is_postgres_active,
    is_docker_running,
    has_secure_env_perms,
    is_gemini_key_set,
    are_secrets_git_ignored,
    is_ollama_fallback
)

app = FastAPI(title="HPD Control Plane API", version="0.1.0")

api_key_header = APIKeyHeader(name="X-HPD-Token", auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    expected_token = os.environ.get("HPD_UI_TOKEN")
    # Si hay token configurado en backend, exigirlo
    if expected_token and api_key != expected_token:
        raise HTTPException(status_code=401, detail="Token inválido o no proporcionado")
    return api_key

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/system/health")
def get_system_health(api_key: str = Depends(get_api_key)):
    return {
        "hostPostgres": is_postgres_active(),
        "dockerDaemon": is_docker_running(),
        "secureEnvPerms": has_secure_env_perms(),
        "geminiApiKeySet": is_gemini_key_set(),
        "gitIgnoredSecrets": are_secrets_git_ignored(),
        "localOllamaModel": is_ollama_fallback()
    }
