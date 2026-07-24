import os
import time
import json
from pathlib import Path
from collections import defaultdict
from fastapi import FastAPI, Depends, HTTPException, Security, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from hpd_cli.api.system_checks import (
    is_postgres_active,
    is_docker_running,
    has_secure_env_perms,
    is_deepseek_key_set,
    are_secrets_git_ignored,
    is_ollama_fallback
)
from hpd_cli.api.metrics import prometheus_metrics, metrics_endpoint
from hpd_cli.api.routes_v1 import router as router_v1
from hpd_cli.auth.routes import router as auth_router
from hpd_cli.logger import log_json

app = FastAPI(
    title="HPD Control Plane API",
    description="""API del **HPD Control Plane** - Centro de mando para HPD Platform Engine.

## Endpoints disponibles
- `/api/v1/system/health` — Estado de todos los servicios
- `/api/v1/version` — Version del API y aplicacion
- `/api/v1/dashboard/data` — Metricas del sistema para el dashboard
- `/api/system/health` (legacy) — Version anterior del health check
- `/metrics` — Metricas Prometheus
- `/dashboard/` — Interfaz web del Control Plane (React SPA)
""",
    version="0.2.0",
    contact={
        "name": "HP Production",
        "url": "https://github.com/HP-PRODUCTION/hpd-cli-core",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[{"url": "/", "description": "Default server"}],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "system", "description": "Estado y monitoreo del sistema"},
        {"name": "dashboard", "description": "Datos para el panel de control web"},
        {"name": "auth", "description": "Autenticacion JWT (login, refresh, verify)"},
        {"name": "legacy", "description": "Endpoints legacy para compatibilidad hacia atras"},
    ],
)

# Middleware de métricas Prometheus
app.middleware("http")(prometheus_metrics)

api_key_header = APIKeyHeader(name="X-HPD-Token", auto_error=False)

# Rate limiter simple (ventana deslizante en memoria)
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "30"))
_request_log: defaultdict = defaultdict(list)

def rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    # Limpiar entradas viejas
    _request_log[client_ip] = [t for t in _request_log[client_ip] if t > window_start]
    if len(_request_log[client_ip]) >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Demasiadas solicitudes. Intenta de nuevo más tarde.")
    _request_log[client_ip].append(now)

def get_api_key(api_key: str = Security(api_key_header)):
    expected_token = os.environ.get("HPD_UI_TOKEN")
    # Si hay token configurado en backend, exigirlo
    if expected_token and api_key != expected_token:
        raise HTTPException(status_code=401, detail="Token inválido o no proporcionado")
    return api_key

# Leer origenes permitidos desde variable de entorno, separados por coma
# Por defecto: solo el control plane local
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dashboard Web UI (React SPA) ---
DIST_DIR = Path(__file__).resolve().parent.parent.parent / "control-plane" / "dist"
if DIST_DIR.exists() and (DIST_DIR / "index.html").exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/dashboard", StaticFiles(directory=str(DIST_DIR), html=True), name="dashboard")
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

    @app.get("/")
    async def root_redirect():
        return RedirectResponse(url="/dashboard/index.html")
else:
    @app.get("/")
    async def root_ok():
        return {"status": "ok", "app": "HPD Control Plane API", "docs": "/docs"}

# --- Rutas versionadas (v1) ---
app.include_router(router_v1)

# --- Rutas de autenticacion ---
app.include_router(auth_router)

# --- Rutas legacy (backward compatible) ---

@app.get("/api/system/health", tags=["legacy"])
def get_system_health_legacy(api_key: str = Depends(get_api_key), _=Depends(rate_limit)):
    """[DEPRECATED] Usar /api/v1/system/health en su lugar. Se eliminara en v2."""
    result = {
        "hostPostgres": is_postgres_active(),
        "dockerDaemon": is_docker_running(),
        "secureEnvPerms": has_secure_env_perms(),
        "deepseekApiKeySet": is_deepseek_key_set(),
        "gitIgnoredSecrets": are_secrets_git_ignored(),
        "localOllamaModel": is_ollama_fallback()
    }
    log_json("INFO", "health_check", checks=result)
    return result

@app.get("/metrics", tags=["legacy"])
async def get_metrics(request: Request):
    return await metrics_endpoint(request)
