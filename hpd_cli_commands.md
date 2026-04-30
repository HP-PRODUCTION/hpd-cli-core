# 🛠️ HPD-CLI Control Plane: Catálogo de Comandos

Este documento consolida todos los comandos disponibles en `hpd-cli-core` hasta la fecha (**2026-04-26**), su propósito y la visión de expansión del ecosistema HPD.

---

## 🤖 Módulo: `hpd ai`
Asistente técnico inteligente y gestión de LLMs.

| Comando | Uso | Descripción |
| :--- | :--- | :--- |
| `ask` | `hpd ai ask "pregunta" --context repo` | Consulta al AI con contexto de repo, proyecto o nulo. |
| `ask --context fs` | `hpd ai ask --context fs --path /home/hpd "pregunta"` | Consulta al AI con contexto escaneado del filesystem local. |
| `ls` | `hpd ai ls` | Lista capacidades IA y comandos local-aware disponibles. |
| `repo scan` | `hpd ai repo scan --path ~ --depth 2 --exclude respaldo,venv --json` | Escanea proyectos locales con marcadores tecnicos. |
| `repo analyze` | `hpd ai repo analyze --path ~ --depth 2 --cache` | Detecta repositorios probables de datos, BI o ETL. |
| `patch` | `hpd ai patch file.txt "cambio"` | Edición asistida de archivos con diff y backup. |
| `doctor` | `hpd ai doctor` | Diagnóstico de API keys, latencia y fallback chain. |
| `status` | `hpd ai status` | Métricas de uso y estado de los proveedores (Gemini, OpenAI, etc). |
| `compare`| `hpd ai compare "pregunta"` | Compara respuestas de múltiples proveedores en paralelo. |
| `generate`| `hpd ai generate module <name>` | Generación de plantillas de código para nuevos módulos. |

---

## 🖥️ Módulo: `hpd system`
Mantenimiento, observabilidad y soporte técnico del host.

| Comando | Uso | Descripción |
| :--- | :--- | :--- |
| `doctor` | `hpd system doctor [--history]` | Salud integral con Health Score (0-100). |
| `trends` | `hpd system trends` | Análisis de tendencias basado en historial de snapshots. |
| `clean` | `hpd system clean --dry-run` | Limpieza de logs, caché APT y basura de Docker. |
| `processes`| `hpd system processes` | Identifica procesos pesados con muestreo de precisión. |
| `services` | `hpd system services` | Estado de servicios críticos (SSH, Docker, DBs). |
| `memory` | `hpd system memory` | Reporte de RAM y Swap. |
| `disks` | `hpd system disks` | Reporte de particiones y espacio libre. |
| `serverize`| `hpd system serverize --precheck` | Validación de readiness pre-producción. |

---

## ⚙️ Módulos de Infraestructura y Operación

### `hpd init`
*   **Propósito**: Inicializa un nuevo proyecto HPD.
*   **Uso**: `hpd init <project_name>`
*   **Acción**: Crea `hpd.config.json` y estructura de carpetas base.

### `hpd integrate`
*   **Propósito**: Orquestación entre módulos (ej: Anaconda -> WordPress).
*   **Uso**: `hpd integrate <source> <target>`
*   **Acción**: Ejecuta pipelines de migración o sincronización de datos.

### `hpd services`
*   **Propósito**: Gestión de contenedores Docker.
*   **Uso**: `hpd services up`, `hpd services stop`, `hpd services logs`.

### `hpd db`
*   **Propósito**: Operaciones de base de datos.
*   **Uso**: `hpd db backup`, `hpd db restore`, `hpd db shell`.

### `hpd status`
*   **Propósito**: Resumen ejecutivo del proyecto actual.
*   **Uso**: `hpd status`

---

## 🔮 Futuros Comandos y Expansión (Roadmap)

### Fase 3: Seguridad y Hardening (`hpd secure`)
*   `hpd secure audit`: Escaneo de vulnerabilidades en contenedores y dependencias.
*   `hpd secure firewall`: Configuración simplificada de `ufw` para perfiles HPD.
*   `hpd secure rotate`: Rotación automática de passwords y API keys.

### Fase 4: Conversión a Servidor (`hpd system serverize`)
*   ✅ `--precheck`: Auditoría de preparación (host + proyectos).
*   ⬜ `--profile <web|docker|basic>`: Configuración automática de perfiles de servidor.

### Fase 5: AI Avanzada (`hpd ai agent`)
*   `hpd ai plan`: Crea un plan de ejecución para tareas complejas.
*   `hpd ai fix`: Intenta corregir errores detectados por `system doctor` automáticamente.
*   `hpd ai logs`: Analiza logs de Docker para encontrar causas raíz de fallos.

---

> [!TIP]
> Puedes ver la ayuda detallada de cualquier comando usando el flag `--help`. Ej: `hpd system doctor --help`.
