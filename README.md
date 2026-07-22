# HPD CLI Core

CLI centralizada para administrar infraestructura, proyectos y asistencias de IA desde un entorno local o una VPS.

## Puertos asignados

Consulta la lista oficial en ../PUERTOS_HPD.md.

## Comandos más útiles

### 1. IA conversacional con DeepSeek

```bash
hpd ai chat "Explícame qué hace este proyecto"
hpd ai ask "Resume este repositorio" --context repo
```

### 2. Análisis de repositorios

```bash
hpd ai repo scan --path . --depth 2
hpd ai repo analyze --path . --depth 2
```

### 3. Diagnóstico del entorno

```bash
hpd setup --check
hpd ai doctor
hpd ai status
```

### 4. Auditoría de seguridad

```bash
hpd secure audit --path .
hpd secure audit --path . --json
```

### 5. Aliases cortos para trabajar desde cualquier carpeta

```bash
hpdai "tu pregunta"
hpdask "tu pregunta"
```

Estos aliases se pueden usar desde la máquina local o desde la VPS para conversar con el asistente sin entrar al repositorio.

## Variables de entorno recomendadas

Asegúrate de tener configuradas estas variables en ~/.hpd/.env o en el entorno de la VPS:

```bash
DEEPSEEK_API_KEY=tu_clave
DEEPSEEK_MODEL=deepseek-chat
```

## Despliegue en VPS

Para usar este CLI en una VPS, lo más simple es:

```bash
cd /path/to/hpd-cli-core
python -m pip install -e .
```

Y después comprobar:

```bash
hpd --help
hpd ai chat "Hola"
```

## Pruebas

```bash
pytest -q tests/test_ai_router.py
```
