# 🛠️ HPD Command Reference

---

# 🤖 hpd ai

## Diagnóstico
```bash
hpd ai doctor
```
Verifica:
- Providers activos (Gemini, OpenAI, Ollama).
- Fallback chain y latencia.
- Permisos de secretos (`~/.hpd/.env`).

## Consulta con contexto
```bash
hpd ai ask "analiza este repo" --context repo
hpd ai ask --context fs --path /home/hpd --depth 2 "cuales repos de datos tengo aqui"
```
Incluye archivos clave y estado de Git en el prompt.

## Contexto local-aware
```bash
hpd ai ls
hpd ai repo scan --path ~ --depth 2 --exclude respaldo,node_modules,venv,.cache
hpd ai repo analyze --path ~ --depth 2 --json
```
Detecta proyectos locales, marcadores tecnicos y posibles repos de datos/BI/ETL antes de consultar al LLM.

## Edición asistida
```bash
hpd ai patch archivo.py "mejorar manejo de errores"
```
**Flujo de Seguridad**:
1. Genera diff estilizado.
2. Pide aprobación manual (`y/N`).
3. Crea backup `.bak`.
4. Aplica cambios en disco.

---

# 🖥️ hpd system

## Salud general
```bash
hpd system doctor
```
Genera un **Health Score (0-100)** analizando CPU, RAM, Disco y Docker.

## Historial
```bash
hpd system doctor --history
```
Guarda un snapshot de las métricas para análisis posterior.

## Tendencias
```bash
hpd system trends
```
Compara el score actual con registros previos para detectar degradación.

## Limpieza
```bash
hpd system clean --dry-run
```
Identifica archivos temporales y basura de Docker de forma segura.

---

# 🧪 hpd lab

## Estado
```bash
hpd lab status
```
Muestra la ocupación y salud de las carpetas de I+D.

## Sandbox
```bash
hpd lab sandbox init
```
Prepara archivos de prueba para validar comandos como `ai patch`.

## Benchmarks
```bash
hpd lab benchmark ollama
```
Mide el rendimiento del modelo local configurado.

---

# 📊 hpd anaconda

```bash
hpd anaconda doctor
hpd anaconda quality
```
Operaciones específicas para la plataforma de datos.

---

# ⚠ Seguridad

**REGLA DE ORO**: Nunca usar `ai patch` sobre archivos que contengan secretos o configuraciones de sistema críticas:
- `.env`
- `secrets/*`
- `~/.ssh/*`
- `/etc/*`
