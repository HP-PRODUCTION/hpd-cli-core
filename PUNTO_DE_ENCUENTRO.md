# 📍 PUNTO DE ENCUENTRO — HPD CORE

**Actualizado:** 24 Julio 2026
**Estado:** ✅ Ronda 1 (9/9) + Ronda 2 (6/6) + Ronda 3 (7/7) + Ronda 4 — Gateway (5/5) completadas
**Enfoque:** CLI-first — administración y desarrollo desde terminal

---

## Resumen de lo logrado

### Ronda 1 — Endurecimiento (9/9)
| # | Mejora | Estado |
|---|---|---|
| 1 | 🔀 Merge robust-cli-2026 → master | ✅ |
| 2 | ⚙️ Systemd service (hpd-api.service, puerto 3100) | ✅ |
| 3 | 🚀 Deploy script automatizado | ✅ |
| 4 | 🗄️ Modelos SQLAlchemy + Alembic | ✅ |
| 5 | 🔖 API versionado (/api/v1/) | ✅ |
| 6 | 🔐 GPG Secret Vault | ✅ |
| 7 | 📊 Dashboard Web UI (React SPA en /) | ✅ |
| 8 | ⌨️ Autocompletado CLI (argcomplete) | ✅ |
| 9 | 📝 OpenAPI docs (Swagger + Redoc) | ✅ |

### Ronda 2 — Escalabilidad (6/6)
| # | Mejora | Estado |
|---|---|---|
| 1 | 🐳 **Docker Compose multi-servicio** | ✅ |
| 2 | 🔑 **Autenticación JWT** (HMAC-SHA256) | ✅ |
| 3 | 🐘 **Soporte PostgreSQL** (SQLite + PG) | ✅ |
| 4 | 🔄 **Redis cache + rate limiting distribuido** | ✅ |
| 5 | ⚡ **Workers asíncronos** (background threads) | ✅ |
| 6 | 🤖 **CI/CD completo** (lint → test → docker → deploy) | ✅ |

### Ronda 3 — Mantenimiento y puesta operativa (7/7)
| # | Tarea | Detalle | Estado |
|---|---|---|---|
| 1 | 🐛 **Fix dashboard/data endpoint** | Campos faltantes `secureEnvPerms`, `gitIgnoredSecrets`, `version` en response dict | ✅ |
| 2 | 🌐 **Exponer API via Caddy + subruta** | `ia.matutino.online/hpd/` → `localhost:3100` con SSL automático | ✅ |
| 3 | 🚀 **Commit + Push a GitHub** | Fix commiteado como `8e6e4bd` y pusheado a `origin/master` | ✅ |
| 4 | 📦 **Deploy a VPS** | `git pull` + `systemctl restart hpd-api` desde GitHub | ✅ |
| 5 | ✅ **Health checks verificados** | 6/6 endpoints respondiendo: health, version, dashboard, metrics, swagger, redoc | ✅ |
| 6 | ⌨️ **Autocompletado CLI instalado** | `argcomplete` + `eval "$(register-python-argcomplete hpd)"` en `~/.bashrc` | ✅ |
| 7 | 🔐 **GPG Vault verificado** | Clave RSA 4096 lista, `.env.gpg` operativo | ✅ |

---

## Detalle de implementaciones

### 🐳 Docker Compose
- `Dockerfile` multi-stage (builder + runtime, python:3.11-slim)
- `docker-compose.yml` con hpd-api, redis (profile:full), postgres (profile:full)
- Redis y PostgreSQL como servicios opcionales con `--profile full`
- Health checks, volúmenes persistentes, red interna `hpd-network`

### 🔑 JWT Auth
- Implementación HMAC-SHA256 sin dependencias externas
- Tokens access (1h) y refresh (30d)
- Endpoints: `POST /api/v1/auth/login`, `/refresh`, `GET /api/v1/auth/verify`

### 🐘 PostgreSQL
- Auto-detecta PostgreSQL vs SQLite en `db.py`
- Pool settings para producción (`pool_size`, `max_overflow`, `pool_pre_ping`)
- Alembic configurado para ambos motores

### 🔄 Redis Cache
- `hpd_cli/cache.py`: Redis con fallback automático a dict en memoria
- Rate limiters migrados a `check_rate_limit()` con soporte Redis
- Operaciones: get/set/delete/incr/expire

### ⚡ Workers Asíncronos
- `hpd_cli/workers.py`: decorador `@async_task` para background threads
- Endpoints: `POST /api/v1/tasks/health-check`, `GET /api/v1/tasks/{id}`
- Almacenamiento de resultados en Redis o memoria

### 🤖 CI/CD
- 4 jobs: lint (ruff) → test (3.11, 3.12) → docker (Trivy scan) → deploy (SSH)
- Push a GitHub Container Registry (ghcr.io) en master
- Deploy automático a VPS via appleboy/ssh-action

---

## Estado de la infraestructura

| Componente | Estado | Puerto | Acceso |
|---|---|---|---|
| hpd-api (VPS) | ✅ Activo | 3100 | Via Caddy /hpd/ |
| Caddy (SSL) | ✅ Activo | 80/443 | Proxy inverso con TLS |
| DeepSeek API | ✅ Configurado | — | — |
| Docker Daemon | ✅ Activo | — | — |
| Dashboard UI | ✅ Funcional | via /hpd/ | — |
| JWT Auth | ✅ Operativo | — | — |
| CLI local | ✅ 26 comandos | — | `hpd status`, `check`, `vault`, etc. |
| Redis | 🟡 Opcional (profile:full) | 6379 | — |
| PostgreSQL | 🟡 Opcional (profile:full) | 5432 | — |

## Accesos
- **API + Dashboard**: `https://ia.matutino.online/hpd/`
- **API Health**: `https://ia.matutino.online/hpd/api/v1/system/health`
- **API Version**: `https://ia.matutino.online/hpd/api/v1/version`
- **Dashboard Data**: `https://ia.matutino.online/hpd/api/v1/dashboard/data`
- **Swagger Docs**: `https://ia.matutino.online/hpd/docs`
- **Redoc**: `https://ia.matutino.online/hpd/redoc`
- **Prometheus Metrics**: `https://ia.matutino.online/hpd/metrics`

---

## Comandos útiles

```bash
# ========== CLI (local) ==========
hpd status all               # Estado global de proyectos
hpd check all                # Auditoría total (71 PASS / 96 checks)
hpd check all --json         # Salida JSON para scripting
hpd system doctor            # Diagnóstico CPU, RAM, disco, Docker
hpd system doctor --history  # Guardar instantánea histórica
hpd vault init               # Inicializar vault GPG
hpd vault encrypt            # Cifrar ~/.hpd/.env
hpd vault view               # Ver secretos (ocultos parcialmente)
hpd db migrate               # Aplicar migraciones SQLAlchemy/Alembic
hpd completion bash          # Agregar a ~/.bashrc para tab-completion

# ========== API (remoto) ==========
curl -s https://ia.matutino.online/hpd/api/v1/system/health   # Health check
curl -s https://ia.matutino.online/hpd/api/v1/version          # Versión
curl -s https://ia.matutino.online/hpd/api/v1/dashboard/data   # Dashboard data

# ========== Mantenimiento VPS ==========
ssh vps "cd /opt/hpd/hpd-cli-core && systemctl restart hpd-api"  # Reiniciar API
ssh vps "journalctl -u hpd-api -n 20 --no-pager"                 # Logs API
ssh vps "systemctl status caddy --no-pager -l"                    # Estado Caddy

# ========== Docker ==========
cd HPD-CORE && docker compose --profile full up -d     # Full stack (con Redis + PG)
cd HPD-CORE && docker compose up -d                    # Solo API

# ========== Tests ==========
cd HPD-CORE && python -m pytest tests/ -q
```

---

## Próximos pasos (propuestos)

- 🔴 API Gateway (Traefik/NGINX) para SSL + routing multi-VPS
- 🟡 Health check con alertas (Telegram/Discord)
- 🟢 Plugin Marketplace firmado con GPG
- 🟢 Modo cluster multi-worker (gunicorn)
- 🟢 Pruebas de integración asíncronas (pytest-asyncio)
  - `hpd ai chat "..." --context repo`
- **Cache local**: `~/.hpd/cache`.
- **Accesos rápidos**: `hpdai "..."` y `hpdask "..."` para usar el asistente desde cualquier carpeta.
- **Entorno global**: Compatible con uso en local y en VPS mediante el ejecutable `hpd` y la configuración en `~/.hpd/.env`.

### 3. WordPress Editorial & Económico (EPIC-WP-ECO-02)

- **Categorías Dinámicas**: Implementada resolución automática de categorías WP en el plugin `hpd-auto-publicador` (v2.14.0).
- **Módulo Económico v2.2.0**:
  - Implementadas tablas `wp_hpd_entidades_financieras` y `wp_hpd_tasas_entidades`.
  - Catálogo inicial de 7 entidades (Popular, Banreservas, BHD, Qik, etc.) operativas.
  - Shortcodes `[hpd_eco_tasas]` y `[hpd_eco_calculadora]` funcionales.
  - Comandos WP-CLI (`wp hpd_eco tasas`) integrados.

### 4. HPD Lab (EPIC-LAB-01)

- **Entorno Limpio**: Estructura R&D operativa.
- **Archivo**: Material legacy movido a `archive/legacy/`.
- **Config**: `LAB_DIR` ahora es dinámico.
- **Validación actual**: 2 tests verdes en `hpd-lab`.

---

## 🚀 Próximos Pasos — CLI-First Roadmap

### 🔴 Fase crítica (prioridad máxima)
| # | Tarea | Área | Dependencias |
|---|-------|------|-------------|
| 1 | **Migrar a PostgreSQL** — Migrar de SQLite a Postgres con pool de conexiones para escalar multi-usuario | CLI (`hpd db`) + API | — |
| 2 | **Autenticación JWT completa** — JWT con refresh tokens y RBAC para sesiones persistentes desde CLI | CLI (`hpd auth`) + API | — |
| 3 | **Workers asíncronos** — Tareas largas (ETL, deploys) ejecutándose en background desde CLI | CLI (`hpd task`) | — |
| 4 | **Docker Compose producción** — Unificar API, DB, dashboard y workers en containers reproducibles | Deploy | — |

### 🟡 Fase mejoras
| # | Tarea | Área |
|---|-------|------|
| 5 | **Redis cache + rate limiting** — Rate limiting persistente y caché de respuestas | CLI + API |
| 6 | **CI/CD tests integración** — pytest-asyncio + GitHub Actions + deploy automático | Calidad |
| 7 | **Modo cluster multi-worker** — gunicorn + uvicorn workers para throughput | Deploy |

### 🟢 Fase visión
| # | Tarea |
|---|-------|
| 8 | **Plugin Marketplace** — Plugins firmados con GPG desde CLI (`hpd plugin`) |
| 9 | **API Gateway distribuido** — Traefik/NGINX multi-VPS |
| 10 | **Health check con alertas** — Notificaciones Telegram/Discord |

### EPIC-WP (paralelo)
- **WP-STABILIZE-01**: Endurecimiento plugins editoriales/económicos
- **WP-MONETIZACION-01**: Anuncios, patrocinios y sostenibilidad
- **WP-SEO-01**: Schema NewsArticle, Open Graph, News Sitemap
- **WP-INTEGRATION-01**: Dropshipping Bridge (diferido)

---

---

## 🌐 Ronda 4 — API Gateway Multi-VPS (Traefik) (5/5)

| # | Tarea | Estado |
|---|-------|--------|
| 1 | **Config Traefik estática** — entry points, SSL Let's Encrypt, providers Docker + file | ✅ |
| 2 | **Config Traefik dinámica** — routers, services, middlewares (secHeaders, rateLimit, CORS, circuitBreaker, stripPrefix) | ✅ |
| 3 | **Docker Compose gateway** — Traefik + Portainer (profile:full) + Whoami debug (profile:debug) | ✅ |
| 4 | **Script deploy + rollback** — `deploy-gateway.sh` con rollback a Caddy | ✅ |
| 5 | **Documentación + multi-VPS** — README, ejemplo WireGuard + backend VPS2 | ✅ |

### 🌐 Routing configurado

| Dominio | Destino | Middleware |
|---------|---------|------------|
| `ia.matutino.online` | AI Gateway (:3001) | secHeaders, rateLimit |
| `ia.matutino.online/hpd/*` | HPD API (:3100, strip /hpd) | secHeaders, rateLimit, stripHpdPrefix |
| `cotidianodia.online` | WordPress (:8082) | secHeaders |
| `matutino.online` | Blog (:8084) | secHeaders |
| `traefik.ia.matutino.online` | Dashboard Traefik | secHeaders, dashboardAuth |
| `portainer.ia.matutino.online` | Portainer (profile:full) | secHeaders, dashboardAuth |

### 🛡️ Middlewares

| Middleware | Función |
|-----------|---------|
| `secHeaders` | Security headers (CSP, XSS, frame deny, referrer policy) |
| `rateLimit` | 30 req/min por IP |
| `circuitBreaker` | Failover si >50% errores o latencia >5s |
| `compress` | Gzip (excepto SSE) |
| `corsHeaders` | CORS para frontend local |
| `dashboardAuth` | Basic auth para dashboards |
| `stripHpdPrefix` | Remueve `/hpd` del path hacia HPD API |

### 🔜 Multi-VPS (próximo)

Cuando haya un segundo VPS:
1. WireGuard VPN entre VPS (ejemplo en `gateway/examples/vpn-wireguard.yml`)
2. Agregar routers/services en `traefik/dynamic.yml` apuntando a IP interna 10.0.0.x
3. Recargar Traefik sin downtime: `kill -HUP 1`

---

## 📝 Notas para la siguiente sesión

- **Instalación**: Para desarrollo, usar `pip install -e ".[dev]"`.
- **Tests**: Antes de cualquier cambio, correr `python3 -m pytest -q`.
- **Seguridad**: La Denylist está en `hpd_cli/ai/context.py` y `hpd_cli/commands/ai.py`.

---

## 🛡️ Hardening de Seguridad (Completado 2026-07-23)

### EPIC-HARDEN-02 — Endurecimiento estructural

| # | Tarea | Archivo | Estado |
|---|-------|---------|--------|
| 1 | **Plugins inseguros** — `load_plugins()` exige `HPD_PLUGINS_ENABLED=true` + whitelist SHA-256 | `hpd_cli/cli.py` | ✅ |
| 2 | **CORS con lista blanca** — lee `CORS_ORIGINS` del entorno (default localhost) | `hpd_cli/api/main.py` | ✅ |
| 3 | **Token hardcodeado** — `HPD_UI_TOKEN` via env var con fallback seguro | `docker-compose.yml` | ✅ |
| 4 | **Permisos .env** — `chmod 600` en script de deploy | `scripts/deploy_vps.sh` | ✅ |
| 5 | **API keys rotas** — `OpenAIProvider` y `DeepSeekProvider` enviaban `******` literal; corregido a `Bearer {api_key}` | `hpd_cli/ai_router.py` | ✅ |
| 6 | **tenacity** en dependencias — requerido por retry logic ya en uso | `pyproject.toml` | ✅ |
| 7 | **Rate limiting** — `/api/system/health` limitado a 30 req/60s por IP | `hpd_cli/api/main.py` | ✅ |
| 8 | **Health check DeepSeek** — verifica `DEEPSEEK_API_KEY` en vez de `GEMINI_API_KEY` | `hpd_cli/api/system_checks.py` | ✅ |

---

## 📈 Robustecimiento para escalar (Completado 2026-07-23)

### EPIC-ROBUSTEZ-01 — CI/CD, monitoreo y contenedores seguros

| # | Tarea | Archivos | Estado |
|---|-------|----------|--------|
| 1 | **Tests en CI** — 68 tests pasando (antes 59/60), cobertura de rate limiter, health checks, métricas Prometheus y validación de tokens. CI matrix Python 3.11 + 3.12 en todos los branches | `.github/workflows/ci.yml`, `tests/test_api_health.py`, `tests/test_ai_router.py` | ✅ |
| 2 | **Logging JSON estructurado** — Nuevo `log_json()` que escribe a `~/.hpd/logs/hpd.jsonl`. Activado con `HPD_JSON_LOG=true`. Registro estructurado de health checks | `hpd_cli/logger.py`, `hpd_cli/api/main.py` | ✅ |
| 3 | **Métricas Prometheus** — Endpoint `/metrics` con contadores de requests, latencia, health checks y requests activos. Middleware ASGI automático | `hpd_cli/api/metrics.py`, `hpd_cli/api/main.py` | ✅ |
| 4 | **Docker seguro** — Multi-stage build (builder + runtime slim), usuario `hpd` no-root (uid 999), `.dockerignore` con exclusión de secretos/cachés/entornos | `Dockerfile`, `.dockerignore` | ✅ |
| 5 | **Escaneo Trivy** — Job Docker en CI que construye la imagen y escanea vulnerabilidades HIGH/CRITICAL | `.github/workflows/ci.yml` | ✅ |

### 🔬 Detalle técnico

```
# La imagen Docker final:
USER hpd                    # No-root
FROM python:3.11-slim       # Base mínima
.dockerignore               # Excluye .env, venv, cachés, tests, docs, .git, .github

# Prometheus en /metrics:
hpd_http_requests_total         # Total requests (method, endpoint, status)
hpd_http_request_duration_seconds  # Latencia en buckets
hpd_health_checks_total         # Health checks acumulados
hpd_active_requests             # Requests concurrentes

# JSON logging (HPD_JSON_LOG=true):
~/.hpd/logs/hpd.jsonl → {"timestamp":"...", "level":"INFO", "event":"health_check", "checks":{...}}

# CI matrix:
Python 3.11 + 3.12 → compileall + pytest → Docker build → Trivy scan
```

---

---

## 🔄 Sincronización VPS (Completado 2026-07-23)

### EPIC-SYNC-01 — Integración bidireccional local ↔ VPS

| # | Tarea | Estado |
|---|-------|--------|
| 1 | **Recuperar módulos experimentales VPS** — 6 archivos: `autonomous.py`, `agent.py`, `diagnose.py`, `projects.py`, `run.py`, `suggest.py` (335 líneas) | ✅ |
| 2 | **Integrar en CLI local** — imports + `setup_parser` para los 6 comandos nuevos | ✅ |
| 3 | **Fix import run_command** — `autonomous.py` importaba de `commands.ai` (no existía); corregido a `commands.run` + adaptación string/args | ✅ |
| 4 | **68 tests pasando** — Verificados post-integración | ✅ |
| 5 | **Commit + Push** a `origin/robust-cli-2026` (d0cf1c9, 21 archivos, +820 líneas) | ✅ |
| 6 | **VPS actualizada** — `git checkout -B robust-cli-2026`, `pip install -e .` exitoso | ✅ |
| 7 | **Verificación VPS** — `hpd --help` muestra los 25 comandos incluyendo `projects`, `agent`, `diagnose`, `run`, `suggest` | ✅ |

### 📦 Módulos recuperados e integrados

| Módulo | Líneas | Descripción |
|--------|--------|-------------|
| `hpd_cli/autonomous.py` | 67 | Modo autónomo: ejecuta tareas sin intervención usando IA |
| `hpd_cli/commands/agent.py` | 39 | Agente interactivo para asistencias contextuales |
| `hpd_cli/commands/diagnose.py` | 67 | Diagnóstico del sistema (CPU, RAM, disco, Docker) |
| `hpd_cli/commands/projects.py` | 83 | Inventario de proyectos VPS con metadatos |
| `hpd_cli/commands/run.py` | 37 | Ejecución segura de comandos con denylist |
| `hpd_cli/commands/suggest.py` | 46 | Sugerencias de mejora vía DeepSeek |

---

## ⚙️ Configuración activa

- **API Key**: `DEEPSEEK_API_KEY` configurada en `~/.hpd/.env`
- **Modelo**: `deepseek-chat`
- **Rate limit**: 30 requests / 60s ventana (configurable vía `RATE_LIMIT_WINDOW_SECONDS` y `RATE_LIMIT_MAX_REQUESTS`)
- **CORS**: `http://localhost:5173,http://localhost:3000` (default)
- **JSON log**: `HPD_JSON_LOG=true` para logging estructurado
- **Docker**: Usuario `hpd`, multi-stage, `.dockerignore`

---

## 📋 Recomendaciones para escalar HPD AI / hpd-cli-core

### 🟢 Alta prioridad — Consolidación post-sync

| # | Tarea | Impacto |
|---|-------|---------|
| 1 | **Merge robust-cli-2026 → master** | Unificar la historia en `master` como rama principal definitiva |
| 2 | **Systemd service** | Crear unit para `hpd api` como servicio administrable (`systemctl start hpd-api`) |
| 3 | **Script de deploy automatizado** | `deploy_vps.sh` que haga git pull, reinstale y reinicie servicios |

### 🟡 Prioridad media (próximas candidatas)

| # | Tarea | Impacto |
|---|-------|---------|
| 1 | **Base de datos y migraciones** | SQLAlchemy ya en deps pero sin uso. Definir modelos + Alembic |
| 2 | **API versionada** | Migrar `/api/...` → `/api/v1/...` para evolución sin romper |
| 3 | **Manejo de secretos** | Migrar de `.env` a vault (Doppler, Bitwarden, o GPG cifrado) |
| 4 | **Dashboard web** | UI simple con métricas Prometheus visibles |
| 5 | **Autocompletado CLI** | Completado para `hpd` (argparse-completion) |
| 6 | **OpenAPI docs** | Documentar endpoints existentes para `/docs` de FastAPI |

> [!IMPORTANT]
> ## Estado actual del sistema (24 Jul 2026)
>
> ### ✅ Operativo
> - **API**: `https://ia.matutino.online/hpd/` — Health, Version, Dashboard, Metrics, Docs
> - **CLI (local)**: 26 comandos — 71 tests PASS, 0 FAIL, 96 checks totales
> - **Autocompletado**: Tab-completion activo en bash
> - **Vault GPG**: Clave RSA 4096 con cifrado de `.env`
> - **Git**: Commit `8e6e4bd` en `origin/master`, VPS sincronizado
> - **Caddy**: Proxy inverso con SSL automático, ruta `/hpd/` → hpd-api
>
> ### 📊 Métricas
> | Indicador | Valor |
> |-----------|-------|
> | Tests | 71 PASS / 0 FAIL / 96 total |
> | CLI commands | 26 |
> | API endpoints | 6 rutas activas |
> | Vault | GPG 4096-bit RSA |
> | CI/CD | GitHub Actions (lint + test + docker + deploy) |
>
> ### 🔜 Siguiente
> Próxima sesión: **Fase crítica** — PostgreSQL, JWT, Workers asíncronos
