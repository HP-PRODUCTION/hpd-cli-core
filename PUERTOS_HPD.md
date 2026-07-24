# 🚦 Puertos estándar HPD

Asignación oficial de puertos para todos los proyectos del ecosistema HPD.
**Este documento es la fuente única de verdad.** Respétalo para evitar conflictos.

## 📊 Tabla de asignación

| Proyecto               | Rango exclusivo       | Puertos en uso actual         |
|------------------------|-----------------------|-------------------------------|
| `palabra-viva-factory` | **3000 – 3015**       | 3000 (Metabase), 3001 (HPD Control Plane) |
| `anaconda`             | **8080 – 8089**       | 8080 (interfaz principal)     |
|                        | (DB aislada: `5433`)  | 5433 (PostgreSQL)             |
| `Plataforma_deportiva` | **8000 – 8009**       | 8000 (API)                    |
| `dropshipping-ebay`    | **8010 – 8019**       | 8010 (API)                    |
| `inversiones`          | **3020 – 3029**       | 3020 (aplicación)             |
| `FitSupport-Services`  | **7000 – 7009**       | 7000 (API)                    |
| `wordpress-docker`     | **8100 – 8109**       | 8100 (WordPress HTTP)         |
|                        | (MySQL: `3307`)       | 3307 (base de datos)          |
| `hpd-cli-core`         | **9000 – 9009**       | 9000 (API si aplica)          |
| `hpd/lab`              | **9010 – 9019**       | 9010 (pruebas)                |

## 🔑 Token de acceso para HPD Control Plane

Para iniciar sesión en HPD Control Plane (puerto 3001), es necesario un token de autenticación. Solicítalo al administrador o sigue el flujo de autenticación documentado en el README del proyecto.

- El token es obligatorio para acceder a las funciones administrativas y de monitoreo.
- No compartas tu token públicamente.
- Si tienes problemas de acceso, revisa la sección de troubleshooting en la documentación del Control Plane.

## 📌 Reglas de uso

1. **Solo puedes usar puertos de tu propio rango.**
   Por ejemplo, `palabra-viva-factory` solo debe escuchar entre 3000‑3015.
2. Si el puerto que necesitas dentro de tu rango ya está ocupado, elige otro libre **dentro del mismo rango**.
3. Si tu proyecto crece y necesitas más puertos, **actualiza este documento** (con acuerdo del equipo) y luego propágalo a todos los repositorios.
4. Los puertos de bases de datos (5433, 3307) están fuera de los rangos para no interferir con servicios del sistema.

## 🔍 Verificar puertos en uso

Para comprobar qué puertos de tu rango están realmente ocupados:

```bash
# Cambia el rango por el de tu proyecto
lsof -iTCP:3000-3015 -sTCP:LISTEN -P -n
```

O ejecuta el script `dev-ports-status` si está disponible en tu entorno.

---

> 📅 Última actualización: 2026-05-28
> Mantenido por el equipo HPD. Cualquier modificación debe reflejarse en todos los proyectos.
