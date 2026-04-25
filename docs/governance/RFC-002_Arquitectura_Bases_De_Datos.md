# RFC-002: Arquitectura Global de Bases de Datos HPD

**Fecha:** 24 de Abril de 2026
**Estado:** Adoptado
**Contexto:** Evolución de la infraestructura HPD hacia múltiples proyectos compartiendo recursos en VPS.
**Objetivo:** Garantizar la "salud mental" operativa, evitar el acoplamiento tóxico (bases de datos globales gigantes) y mantener los costos de infraestructura controlados en fases iniciales.

## 1. El Principio Fundamental
**Bajo ninguna circunstancia se utilizará una única base de datos (e.g. `hpd_global_db`) para almacenar las tablas de múltiples proyectos.**
El acoplamiento de datos a este nivel crea un único punto de fallo catastrófico, corrompe los permisos de acceso y hace imposibles las restauraciones puntuales de backups por proyecto.

## 2. Topología de Despliegue
En la fase actual de HPD, la topología elegida es:
**Instancia Única (VPS Central) + PostgreSQL Central + Múltiples Bases de Datos Lógicas.**

### Esquema de Instancia:
```text
PostgreSQL Server (Dockerizado en VPS)
├── anaconda_db       (Para proyecto_anaconda)
├── dropshipping_db   (Para dropshipping-ebay)
├── deportiva_db      (Para plataforma_deportiva)
├── metabase_db       (Almacenamiento nativo de Metabase)
└── hpd_control_db    (Logística del Control Plane)
```

## 3. Reglas Inquebrantables de Operación (Las 4 Leyes)

1. **Una Base de Datos por Proyecto:** Separación estricta y lógica.
2. **Un Usuario por Proyecto:** Prohibido que las aplicaciones se conecten con el superusuario `postgres`. Cada proyecto requiere credenciales asiladas (`anaconda_user`, `dropshipping_user`, etc.).
3. **Backups Separados:** El proceso de respaldo no realiza un volcado completo de la instancia (evitando restauraciones suicidas). Los volcados se hacen a nivel de base de datos (`pg_dump anaconda_db > backups/anaconda.sql`).
4. **Registro Centralizado en CLI:** El CLI central (`hpd-cli-core`) actuará como el registro de conexiones leyendo el archivo de orquestación global `~/.hpd/config.yaml`.

## 4. Evolución Futura
Cuando el tráfico y los requerimientos de I/O de los proyectos (Dashboards pesados, cientos de workers) saturen el VPS central, la arquitectura permitirá separar la carga limpiamente:
- **Fase Actual:** `VPS (App + DB)`
- **Fase Escala:** `VPS App` + `VPS DB` + `VPS Observabilidad`
Separar prematuramente solo generará complejidad con intereses.

## 5. Implementación en HPD-CLI
El CLI implementará comandos de provisión y respaldo acordes a esta RFC:
- `hpd db provision <project_name>`: Creará la base de datos y su usuario exclusivo.
- `hpd db backup <project_name>`: Ejecutará el volcado lógico aislado.

---
**Veredicto:** El equilibrio correcto entre orden, costo y escalabilidad. Aprobado para implementación inmediata.
