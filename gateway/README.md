# 🌐 HPD API Gateway — Traefik

Gateway multi-VPS con Traefik v3, SSL automático (Let's Encrypt), balanceo de carga y dashboard.

## Arquitectura

```
Internet → :80/443 → Traefik (SSL termination)
  ├── ia.matutino.online       → AI Gateway   (:3001)
  │   └── /hpd/*              → HPD API      (:3100, con stripPrefix)
  ├── cotidianodia.online      → WordPress    (:8082)
  ├── matutino.online          → Blog         (:8084)
  ├── traefik.ia.matutino.online → Dashboard   (auth básica)
  ├── portainer.ia.matutino.online → Portainer (profile: full)
  └── [VPS2] vpn wireguard    → Workers      (10.0.0.2:XXXX)
```

## Despliegue rápido

```bash
# 1. Generar password para dashboard
htpasswd -nb admin "tu_password_segura"

# 2. Reemplazar en traefik/dynamic.yml:
#    "admin:$2y$10$PLACEHOLDER_CHANGE_ME" → hash generado

# 3. Desplegar
cd gateway && sudo bash scripts/deploy-gateway.sh

# Con Portainer:
sudo bash scripts/deploy-gateway.sh --profile full

# Rollback a Caddy:
sudo bash scripts/deploy-gateway.sh --rollback
```

## Estructura

```
gateway/
├── docker-compose.yml           # Traefik + servicios opcionales
├── traefik/
│   ├── traefik.yml              # Config estática (entrypoints, providers)
│   └── dynamic.yml              # Config dinámica (routers, services)
├── scripts/
│   └── deploy-gateway.sh        # Deploy + rollback
├── examples/
│   ├── multi-vps.yml            # Backend en VPS secundario
│   └── vpn-wireguard.yml        # VPN entre VPS (próximamente)
└── README.md
```

## Comandos útiles

```bash
# Logs
docker compose logs -f traefik

# Recargar config dinámica sin downtime
docker compose exec traefik kill -HUP 1

# Ver rutas activas
docker compose exec traefik traefik health --ping

# Dashboard API (local)
curl -s http://localhost:8080/api/http/routers | jq
```

## Multi-VPS

1. Instalar WireGuard en ambos VPS
2. Configurar túnel (ver `examples/multi-vps.yml`)
3. Agregar routers/services en `traefik/dynamic.yml`
4. Recargar Traefik: `kill -HUP 1`

## Middlewares disponibles

| Middleware | Descripción |
|-----------|-------------|
| `secHeaders` | Security headers (CSP, XSS, frame deny) |
| `rateLimit` | 30 req/min por IP |
| `circuitBreaker` | Failover si >50% errores o latencia >5s |
| `compress` | Gzip (excepto SSE) |
| `corsHeaders` | CORS para frontend local |
| `dashboardAuth` | Basic auth para dashboard |
| `stripHpdPrefix` | Remueve `/hpd` del path hacia HPD API |

## Rollback a Caddy

```bash
sudo bash scripts/deploy-gateway.sh --rollback
```

Esto detiene Traefik y reactiva Caddy con su configuración original.
