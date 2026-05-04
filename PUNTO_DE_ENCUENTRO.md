# 📍 Punto de Encuentro: HPD CLI Core

**Fecha**: 2026-05-04
**Contexto**: Cierre de los sprints de Hardening y CI. El sistema ha pasado de ser un MVP funcional a una plataforma gobernada y segura.

---

## 🛠️ Estado Técnico Actual

### 1. Hardening & Seguridad (EPIC-HARDEN-01)
- **Error Handling**: Eliminados todos los `bare except:`. Captura de excepciones tipadas en todo el core.
- **AI Safety**: Implementada **Denylist de Seguridad** en `build_context` y `ai patch`. Protege archivos `.env`, `secrets`, `keys`, etc.
- **Arquitectura**: `AIRouter` convertido a **Singleton** (`get_ai_router()`) para optimización de recursos.
- **Dependencias**: Formalizadas en `pyproject.toml` (incluyendo `psutil`, `google-generativeai` y `dev` extras).

### 2. Testing & Calidad (EPIC-CI-01)
- **Suite de Pruebas**: 47 tests operativos (`pytest`).
  - Cobertura: System Doctor (scoring/hints), AI Router (fallback/health), System Clean (dry-run safety).
- **Portero (CI)**: GitHub Actions configurado en `.github/workflows/tests.yml`. Ejecución automática en cada push/PR.
- **Badge**: Visible en el `README.md`.

### 2.1 AI Local-Aware (EPIC-AI-FS-01)
- **Comandos implementados**:
  - `hpd ai ls`
  - `hpd ai repo scan --path <path> --depth <n> --exclude <terms> --json`
  - `hpd ai repo analyze --path <path> --depth <n> --cache --json`
  - `hpd ai ask --context fs --path <path> --depth <n> "..."`
- **Cache local**: `~/.hpd/cache`.
- **Fixtures**: `hpd-lab/fixtures/repos/` valida scoring sin depender del filesystem real.
- **Ajuste 2026-05-04**: el scoring evita falsos positivos de keywords cortas como `bi` dentro de palabras comunes.

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

    *   ✅ `hpd system serverize --precheck`: Validación de readiness (host + proyecto).
    *   ⬜ `hpd system serverize --plan`: Generación de ruta de despliegue.
2.  **EPIC-WP-STABILIZE-01 — Endurecimiento de plugins editoriales/económicos**
    *   T-01 Validar estado de plugins desde WP-CLI.
    *   T-02 Crear smoke test operativo para hpd-auto-publicador.
    *   T-03 Crear smoke test operativo para hpd-economico.
    *   T-04 Añadir comando `hpd wordpress doctor` al Control Plane.
    *   T-05 Actualizar documentación final de WordPress.
3.  **EPIC-WP-MONETIZACION-01 — Anuncios, patrocinios y sostenibilidad**
    *   Definir inventario de zonas y crear plugin `hpd-monetizacion`.
4.  **EPIC-WP-SEO-01 — SEO editorial y técnico**
    *   Implementar Schema NewsArticle, Open Graph y News Sitemap.
5.  **EPIC-WP-INTEGRATION-01: Dropshipping Bridge (DIFERIDO)**
    *   Crear puente para publicar reseñas de productos en WordPress (prioridad baja).

---

## 📝 Notas para la siguiente sesión
- **Instalación**: Para desarrollo, usar `pip install -e ".[dev]"`.
- **Tests**: Antes de cualquier cambio, correr `python3 -m pytest -q`.
- **Seguridad**: La Denylist está en `hpd_cli/ai/context.py` y `hpd_cli/commands/ai.py`.

> [!IMPORTANT]
> El sistema está en estado **VERDE** (47/47 tests passing). No se permiten cambios que rompan la suite de pruebas.
