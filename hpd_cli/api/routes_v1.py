"""API v1 versioned routes."""
import os
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Security, Request
from fastapi.security.api_key import APIKeyHeader
from hpd_cli.api.system_checks import (
    is_postgres_active,
    is_docker_running,
    has_secure_env_perms,
    is_deepseek_key_set,
    are_secrets_git_ignored,
    is_ollama_fallback,
)
from hpd_cli.logger import log_json

router = APIRouter(prefix="/api/v1")

api_key_header = APIKeyHeader(name="X-HPD-Token", auto_error=False)

# Rate limiter (ventana deslizante en memoria)
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "30"))
_request_log: defaultdict = defaultdict(list)


def _rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    _request_log[client_ip] = [t for t in _request_log[client_ip] if t > window_start]
    if len(_request_log[client_ip]) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=429, detail="Demasiadas solicitudes. Intenta de nuevo mas tarde."
        )
    _request_log[client_ip].append(now)


def _get_api_key(api_key: str = Security(api_key_header)):
    expected_token = os.environ.get("HPD_UI_TOKEN")
    if expected_token and api_key != expected_token:
        raise HTTPException(status_code=401, detail="Token invalido o no proporcionado")
    return api_key


@router.get("/system/health")
def get_system_health(
    api_key: str = Depends(_get_api_key),
    _=Depends(_rate_limit),
):
    """Health check del sistema HPD. Requiere X-HPD-Token si esta configurado."""
    result = {
        "hostPostgres": is_postgres_active(),
        "dockerDaemon": is_docker_running(),
        "secureEnvPerms": has_secure_env_perms(),
        "deepseekApiKeySet": is_deepseek_key_set(),
        "gitIgnoredSecrets": are_secrets_git_ignored(),
        "localOllamaModel": is_ollama_fallback(),
    }
    log_json("INFO", "health_check", checks=result)
    return result


@router.get("/version")
def get_version():
    """Informacion de version del API."""
    return {
        "api": "v1",
        "app": "HPD Control Plane",
        "version": "0.1.0",
    }


@router.get("/dashboard/data")
def get_dashboard_data(
    _=Depends(_get_api_key),
):
    """Datos agregados para el dashboard UI."""
    import psutil
    import datetime

    # Sistema
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot_time
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "system": {
            "hostname": os.uname().nodename,
            "platform": os.uname().sysname,
            "uptime_seconds": int(uptime.total_seconds()),
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
        },
        "health": {
            "deepseekApiKeySet": is_deepseek_key_set(),
            "dockerDaemon": is_docker_running(),
            "hostPostgres": is_postgres_active(),
            "localOllamaModel": is_ollama_fallback(),
        },
        "version": {
            "api": "v1",
            "app": "HPD Control Plane",
        },
    }
