# 📊 Arquitectura Visual HPD (RFC-002)

Este documento complementa la **RFC-002** con diagramas esquemáticos y de flujo para visualizar el aislamiento y la gestión de datos.

## 1. Estructura de Aislamiento (Esquemático)
Muestra cómo conviven los proyectos en un mismo VPS pero con fronteras de datos infranqueables.

```mermaid
graph TD
    subgraph "VPS Central HPD"
        Proxy[Nginx Proxy]
        
        subgraph "Contenedores de Aplicación"
            App1[Proyecto Anaconda]
            App2[Dropshipping eBay]
            App3[Plataforma Deportiva]
            App4[Metabase OSS]
        end

        subgraph "Instancia PostgreSQL (Docker)"
            DB_Admin[(Postgres Root)]
            
            subgraph "Bases de Datos Aisladas"
                DB1[(anaconda_db)]
                DB2[(dropshipping_db)]
                DB3[(deportiva_db)]
                DB4[(metabase_db)]
            end
        end
    end

    %% Conexiones con usuarios dedicados
    App1 -- "anaconda_user" --> DB1
    App2 -- "dropshipping_user" --> DB2
    App3 -- "deportiva_user" --> DB3
    App4 -- "metabase_user" --> DB4

    style DB_Admin fill:#f96,stroke:#333,stroke-width:2px
    style VPS Central HPD fill:#f5f5f5,stroke:#333,stroke-dasharray: 5 5
```

## 2. Flujo de Provisión (`hpd db provision`)
Muestra el proceso creativo de dar vida a un nuevo proyecto en el ecosistema.

```mermaid
sequenceDiagram
    participant U as Usuario (hpd cli)
    participant C as HPD Control Plane
    participant DB as Postgres Engine
    participant FS as File System (~/.hpd)

    U->>C: hpd db provision <proyecto>
    C->>C: Validar nombre y RFC-002
    C->>DB: CREATE USER <proyecto>_user
    C->>DB: CREATE DATABASE <proyecto>_db OWNER <proyecto>_user
    DB-->>C: Confirmación de creación
    C->>FS: Registrar conexión en config.yaml
    C-->>U: ✅ Entorno de datos listo y aislado
```

## 3. Flujo de Backup Aislado (`hpd db backup`)
Garantiza que un fallo en el respaldo de un proyecto no afecte la disponibilidad de los demás.

```mermaid
graph LR
    subgraph "Operación de Respaldo"
        CMD[hpd db backup] --> Target{¿Qué proyecto?}
        Target -- "Anaconda" --> Dump1[pg_dump anaconda_db]
        Target -- "Dropshipping" --> Dump2[pg_dump dropshipping_db]
    end

    Dump1 --> S3[(Backups S3 / Local)]
    Dump2 --> S3

    note right of Dump1: Solo extrae datos de Anaconda
    note right of Dump2: No toca anaconda_db ni deportiva_db
```

---
*Diagramas generados para soporte de salud mental y claridad técnica del equipo HPD.*
