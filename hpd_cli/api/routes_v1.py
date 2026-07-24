"""API v1 versioned routes."""
import os

from fastapi import APIRouter, Depends, HTTPException, Security, Request
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel

from hpd_cli.api.system_checks import (
    is_postgres_active,
    is_docker_running,
    has_secure_env_perms,
    is_deepseek_key_set,
    are_secrets_git_ignored,
    is_ollama_fallback,
)
from hpd_cli.cache import check_rate_limit
from hpd_cli.logger import log_json


# --- Pydantic models ---

class HealthCheckResponse(BaseModel):
    """Respuesta del health check del sistema."""
    hostPostgres: bool
    dockerDaemon: bool
    secureEnvPerms: bool
    deepseekApiKeySet: bool
    gitIgnoredSecrets: bool
    localOllamaModel: bool


class VersionResponse(BaseModel):
    """Informacion de version del API."""
    api: str
    app: str
    version: str


class SystemMetrics(BaseModel):
    """Metricas del sistema."""
    hostname: str
    platform: str
    uptime_seconds: int
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float


class DashboardDataResponse(BaseModel):
    """Datos completos para el dashboard web."""
    system: SystemMetrics
    health: HealthCheckResponse
    version: VersionResponse


# --- Router ---

router = APIRouter(prefix="/api/v1")

api_key_header = APIKeyHeader(name="X-HPD-Token", auto_error=False)

# Rate limiter (Redis o en memoria con fallback)
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "30"))


def _rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    allowed, _ = check_rate_limit(client_ip, RATE_LIMIT_MAX, RATE_LIMIT_WINDOW)
    if not allowed:
        raise HTTPException(
            status_code=429, detail="Demasiadas solicitudes. Intenta de nuevo mas tarde."
        )


def _get_api_key(api_key: str = Security(api_key_header)):
    expected_token = os.environ.get("HPD_UI_TOKEN")
    if expected_token and api_key != expected_token:
        raise HTTPException(status_code=401, detail="Token invalido o no proporcionado")
    return api_key


@router.get(
    "/system/health",
    response_model=HealthCheckResponse,
    tags=["system"],
    summary="Health check del sistema",
    description="""Verifica el estado de todos los servicios y componentes del sistema HPD.

**Retorna:** estado de PostgreSQL, Docker, permisos de env, API key de DeepSeek,
secrets en .gitignore y modelo Ollama local.""",
)
def get_system_health(
    api_key: str = Depends(_get_api_key),
    _=Depends(_rate_limit),
):
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


@router.get(
    "/version",
    response_model=VersionResponse,
    tags=["system"],
    summary="Version del API",
    description="Retorna la version actual del API y la aplicacion.",
)
def get_version():
    return {
        "api": "v1",
        "app": "HPD Control Plane",
        "version": "0.1.0",
    }


@router.get(
    "/dashboard/data",
    response_model=DashboardDataResponse,
    tags=["dashboard"],
    summary="Metricas del sistema para el dashboard",
    description="""Retorna datos agregados del sistema para alimentar el dashboard web.

**Incluye:**
- **system**: hostname, uptime, CPU, memoria y uso de disco
- **health**: estado de servicios (PostgreSQL, Docker, DeepSeek, etc.)
- **version**: version del API y aplicacion""",
)
def get_dashboard_data(
    _=Depends(_get_api_key),
):
    import psutil
    import datetime

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
            "hostPostgres": is_postgres_active(),
            "dockerDaemon": is_docker_running(),
            "secureEnvPerms": has_secure_env_perms(),
            "deepseekApiKeySet": is_deepseek_key_set(),
            "gitIgnoredSecrets": are_secrets_git_ignored(),
            "localOllamaModel": is_ollama_fallback(),
        },
        "version": {
            "api": "v1",
            "app": "HPD Control Plane",
            "version": "0.1.0",
        },
    }
