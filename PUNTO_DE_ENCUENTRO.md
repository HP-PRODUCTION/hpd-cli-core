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

1. **Despliegue operativo en VPS**
    - ✅ Instalación del CLI vía `pip install -e .`.
    - ✅ Configuración de `~/.hpd/.env` con DeepSeek.
    - ⬜ Automatizar el arranque del CLI en servicio de la VPS.
    - ⬜ Añadir un script de despliegue para sincronizar proyectos desde la VPS.
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

> [!IMPORTANT]
> El sistema está en estado **VERDE** para la ruta de IA y control plane. No se permiten cambios que rompan la integración de DeepSeek ni el flujo del CLI.
