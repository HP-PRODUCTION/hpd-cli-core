# 🧠 HPD Operational Runbook

---

# ☀ Chequeo Diario (Mantenimiento Preventivo)

Ejecutar cada mañana para asegurar la estabilidad del entorno:
```bash
hpd system doctor
hpd ai doctor
hpd status
```

---

# 📈 Gestión de Degradación

Si notas lentitud o el **Health Score** baja:
```bash
hpd system doctor --history
hpd system trends
```
**Acciones recomendadas**:
- Si el score < 80: Revisar espacio en disco.
- Si el score < 50: Detener servicios no esenciales (`hpd system clean`).

---

# 🧹 Limpieza de Sistema

Siempre verificar antes de borrar:
```bash
hpd system clean --dry-run
```
Si la lista es correcta, proceder:
```bash
hpd system clean --apply
```

---

# 🔧 Flujo de Edición Segura (AI Patch)

Nunca aplicar parches directamente en repositorios de producción sin validación previa.

1. **Inicializar Sandbox**:
   ```bash
   hpd lab sandbox init
   ```
2. **Probar Parche**:
   ```bash
   hpd ai patch /home/hpd/hpd-lab/sandbox/test_script.py "refactoriza logging"
   ```
3. **Validar**: Ejecutar tests en el laboratorio.
4. **Promover**: Una vez validado, aplicar el mismo comando en el repositorio destino.

---

# 🧪 Verificación de Salud del Código (DevOps)

Antes de promover cualquier cambio o después de un update:
```bash
pytest /home/hpd/hpd-cli-core/tests
```
**Regla**: Todos los tests (47+) deben estar en verde. Si un test falla, el Control Plane se considera en estado "Inestable".

## 🗺️ Inventario Local-Aware Del Workspace

Para revisar el workspace HPD completo antes de tocar un proyecto:

```bash
hpd ai repo scan --path /home/hpd --depth 1 --exclude respaldo,node_modules,venv,.cache --json
hpd ai repo analyze --path /home/hpd --depth 2 --exclude respaldo,node_modules,venv,.cache --json
```

Lectura esperada:
- `proyecto_anaconda`: plataforma data/ETL principal.
- `wordpress-docker`: plataforma editorial con observabilidad y datos operativos.
- `dropshipping-ebay`: dominio comercial con señales data/ETL.
- `hpd-lab`: laboratorio/fixtures para validar heurísticas.

Si un repo aparece como data repo por una keyword débil, agregar fixture y test antes de ajustar scoring.

---

# 🛡️ Hardening Check

Para verificar que las protecciones de secretos están activas:
1. Crea un archivo `.env` en la raíz.
2. Ejecuta `hpd ai ask "qué archivos ves?" --context project`.
3. El archivo `.env` **no** debe aparecer en el reporte de archivos leídos.

---

# 🚨 Respuesta a Incidentes

### Fallo en Docker
1. Verificar estado: `hpd system services`
2. Ver contenedores: `docker ps`
3. Analizar host: `hpd system doctor`

### Fallo en Proveedor de IA
Si Gemini no responde:
1. Verificar conectividad: `hpd ai doctor`
2. Cambiar a fallback local:
   ```bash
   hpd ai ask "pregunta" --provider ollama
   ```

---

# 🧪 Chaos Engineering (Simulaciones)

Para validar que el sistema detecta fallos correctamente, puedes simular estrés:
```bash
# Simular presión de memoria (80%)
stress-ng --vm 2 --vm-bytes 80%
```
Luego ejecuta `hpd system doctor` y verifica que el Health Score refleje la deducción correspondiente.
