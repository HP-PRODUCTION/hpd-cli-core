# 📍 Punto de Encuentro: HPD CLI Core

**Fecha**: 2026-07-21
**Contexto**: Consolidación del control plane con IA conversacional, soporte para DeepSeek y preparación operativa para despliegue en VPS.

---

## 🛠️ Estado Técnico Actual

### 1. Hardening & Seguridad (EPIC-HARDEN-01)

- **Error Handling**: Eliminados todos los `bare except:`. Captura de excepciones tipadas en todo el core.
- **AI Safety**: Implementada **Denylist de Seguridad** en `build_context` y `ai patch`. Protege archivos `.env`, `secrets`, `keys`, etc.
- **Arquitectura**: `AIRouter` convertido a **Singleton** (`get_ai_router()`) para optimización de recursos.
- **Dependencias**: Formalizadas en `pyproject.toml` (incluyendo `psutil`, `python-dotenv`, `requests`, `rich`, `SQLAlchemy` y `google-genai`).
- **IA operativa**: Añadido soporte nativo para DeepSeek como proveedor principal, con `hpd ai ask` y `hpd ai chat` listos para usarse en local y en VPS.

### 2. Testing & Calidad (EPIC-CI-01)

- **Suite de Pruebas**: 19 tests operativos del router de IA (`pytest -q tests/test_ai_router.py`).
- **Cobertura**: Health checks de proveedores, fallback, configuración por defecto y uso de DeepSeek como proveedor preferido.
- **Integración**: Validado el flujo de `hpd ai chat` y `hpd ai ask` con contexto de repositorio.

### 2.1 AI Local-Aware (EPIC-AI-FS-01)

- **Comandos implementados**:
  - `hpd ai ls`
  - `hpd ai repo scan --path <path> --depth <n> --exclude <terms> --json`
  - `hpd ai repo analyze --path <path> --depth <n> --cache --json`
  - `hpd ai ask --context fs --path <path> --depth <n> "..."`
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

## 🚀 Próximos Pasos (Backlog Inmediato)

1. **Consolidación post-sync**
    - ✅ Sincronización bidireccional local ↔ VPS completada.
    - ✅ Integrados 6 comandos desde VPS (autonomous, agent, diagnose, projects, run, suggest).
    - ✅ 68 tests pasando, push a GitHub, VPS actualizada.
    - ⬜ **Merge robust-cli-2026 → master** para unificar ramas.
    - ⬜ **Systemd service** para `hpd api` en VPS.
    - ⬜ **Deploy script** automatizado (git pull → install → restart).
2. **EPIC-WP-STABILIZE-01 — Endurecimiento de plugins editoriales/económicos**
    - T-01 Validar estado de plugins desde WP-CLI.
    - T-02 Crear smoke test operativo para hpd-auto-publicador.
    - T-03 Crear smoke test operativo para hpd-economico.
    - T-04 Añadir comando `hpd wordpress doctor` al Control Plane.
    - T-05 Actualizar documentación final de WordPress.
3. **EPIC-WP-MONETIZACION-01 — Anuncios, patrocinios y sostenibilidad**
    - Definir inventario de zonas y crear plugin `hpd-monetizacion`.
4. **EPIC-WP-SEO-01 — SEO editorial y técnico**
    - Implementar Schema NewsArticle, Open Graph y News Sitemap.
5. **EPIC-WP-INTEGRATION-01: Dropshipping Bridge (DIFERIDO)**
    - Crear puente para publicar reseñas de productos en WordPress (prioridad baja).

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
> El sistema está en estado **VERDE** — 68 tests pasando, CI con 2 versiones de Python + Docker + Trivy, logging JSON estructurado, métricas Prometheus, contenedor seguro con usuario no-root, API keys funcionales, rate limiting activo.
