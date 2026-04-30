# 🚀 HPD Control Plane Documentation

![CI Status](https://img.shields.io/badge/CI-Passing-success)

Enterprise-grade operating manual para el ecosistema HPD:

- HPD CLI Core (Hardened)
- HPD Lab (R&D Center)
- HPD System
- HPD AI
- HPD Anaconda

---

# 🧭 Visión

HPD se divide en tres capas:

```text
HPD Lab
→ experimenta, valida y archiva (legacy/)

HPD CLI Core
→ gobierna, orquesta y testea (pytest)

HPD Projects
→ ejecuta en producción
```

---

# 🛡️ Seguridad y Robustez

- **Secret Sanitization**: Filtro automático de archivos sensibles (.env, secrets, keys) en el contexto de IA.
- **Singleton Architecture**: AIRouter centralizado para eficiencia de recursos.
- **Error Handling**: Captura tipada de excepciones en todo el núcleo.
- **Automated Testing**: Suite de pruebas con Pytest para lógica crítica.
- **CI Governance**: GitHub Actions configurado para validar cada push/PR automáticamente.

---

# 🧩 Dominios

## Inteligencia

- **hpd ai ask**: Consultas con contexto avanzado.
- **hpd ai doctor**: Diagnóstico de salud de proveedores.
- **hpd ai patch**: Edición asistida y segura de archivos.

## Sistema

- **hpd system doctor**: Diagnóstico integral con Health Score.
- **hpd system trends**: Análisis de tendencias históricas.
- **hpd system clean**: Mantenimiento y liberación de recursos.
- **hpd system serverize**: Auditoría de preparación pre-producción.

## Laboratorio

- **hpd lab status**: Estado del entorno I+D.
- **hpd lab benchmark**: Comparativa de latencia y calidad IA.
- **hpd lab sandbox**: Entorno de experimentación aislada.

## Datos

- **hpd anaconda doctor**: Salud de la plataforma ETL.
- **hpd anaconda quality**: Validación de integridad de datos.

---

# 📁 Documentación Detallada

- [Referencia de Comandos (COMMANDS.md)](COMMANDS.md)
- [Guía de Operaciones (RUNBOOK.md)](RUNBOOK.md)

---

# 🎯 Objetivos

- **Seguridad**: Protección de secretos y backups obligatorios.
- **Observabilidad**: Métricas precisas y monitoreo de tendencias.
- **Automatización**: Pipelines de integración y gobierno técnico.
- **Resiliencia**: Fallback inteligente entre proveedores de IA.

---

# 🧬 Roadmap Status

- **EPIC-HARDEN-01**: ✅ **Completado** (Testing, Singleton, Sanitization).
- **EPIC-CI-01**: ✅ **Completado** (GitHub Actions, Dev Dependencies).
- **EPIC-SYS-01**: ✅ **Completado** (Trends, History, Score, Serverize Precheck).
- **EPIC-SYS-02**: 🟡 En progreso (Serverize Profiles).
- **EPIC-AI-01**: 🟡 En progreso (Patching, Context, Agents).
- **EPIC-LAB-01**: ✅ **Completado** (Estructura R&D, Legacy Archive).
- **EPIC-ANACONDA-01**: ⚪ Pendiente (Data Quality, ETL Governance).
