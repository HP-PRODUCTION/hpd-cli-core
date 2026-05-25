# Comandos avanzados y robustez

## setup --check

Valida el entorno sin modificar archivos. Revisa:

- Existencia y permisos de ~/.hpd, config.yaml, .env
- Dependencias del sistema (docker, git, python3, ffmpeg, psql, pg_restore)
- Estado de proveedores IA (openai, anthropic, gemini, etc.)

```bash
hpd setup --check
```

## secure audit

Auditoría de seguridad local. Detecta:

- Permisos inseguros en .env
- Archivos sensibles presentes o trackeados por git (.env, id_rsa, secrets)
- Docker socket accesible

```bash
hpd secure audit --path .
hpd secure audit --path . --json
```

## system fix

Reparaciones guiadas no destructivas. Muestra comandos a ejecutar y requiere --apply para aplicar.

```bash
hpd system fix docker         # Reinicia Docker
hpd system fix env-perms     # Corrige permisos de ~/.hpd/.env
hpd system fix ollama-model  # Descarga modelo Ollama
hpd system fix swap          # Reinicia swap

# Para ejecutar realmente:
hpd system fix docker --apply
```

## Logging avanzado

Logs rotativos en ~/.hpd/logs/hpd.log. Niveles controlados por:

- --verbose (DEBUG)
- --quiet (solo errores)

## Escaneo de repositorios

Reconoce markers: Dockerfile, docker-compose.yml, .env.example, Airflow (dags/), WordPress (wp-config.php), SQL, notebooks, etc. Limita profundidad y exclusiones por defecto.

```bash
hpd ai repo scan --path . --depth 1 --json
```

## Pruebas de integración CLI

Incluye tests para:

- setup --help
- system doctor --json
- ai repo scan --json
- services --help
- secure audit --json

## CI

GitHub Actions ejecuta pytest, compileall y lint en cada push.

---
Para más detalles, ver ayuda de cada comando:

```bash
hpd setup --help
hpd secure --help
hpd system fix --help
```

# HPD Platform Engine CLI (Control Plane)

CLI centralizada para la gestión de infraestructura y aplicaciones HPD.

## Namespaces Disponibles

- `anaconda`: Gestión de Proyecto Anaconda (ETL).
- `dropshipping`: Gestión de Dropshipping eBay.
- **`wordpress`**: Gestión de ecosistema WordPress (HPD El Matutino).
- `etl`: Herramientas de observabilidad y pipelines.
- `ai`: Router de IA y scaffolding.

## Uso rápido (WordPress)

```bash
hpd wordpress doctor
hpd wordpress doctor --json --history
```
