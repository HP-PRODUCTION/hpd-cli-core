#!/usr/bin/env bash
# ============================================================
# deploy-gateway.sh — Deploy Traefik API Gateway al VPS
# ============================================================
# Uso:
#   ./deploy-gateway.sh                    # Deploy normal
#   ./deploy-gateway.sh --profile full     # + Portainer
#   ./deploy-gateway.sh --profile debug    # + Whoami test
#   ./deploy-gateway.sh --rollback         # Restaurar Caddy
# ============================================================
set -euo pipefail

GATEWAY_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE="${2:-}"
ROLLBACK=false

# Parse args
for arg in "$@"; do
  case "$arg" in
    --profile) PROFILE="${2:-}"; shift ;;
    --rollback) ROLLBACK=true ;;
  esac
  shift
done

echo "=========================================="
echo "  HPD API Gateway - Deploy Script"
echo "=========================================="
echo "Directorios:"
echo "  Gateway: ${GATEWAY_DIR}"
echo "  Profile: ${PROFILE:-standalone}"

# === Prerrequisitos ===
check_prereqs() {
  if ! command -v docker &>/dev/null; then
    echo "ERROR: Docker no instalado" >&2
    exit 1
  fi
  if ! docker compose version &>/dev/null; then
    echo "ERROR: Docker Compose v2 no disponible" >&2
    exit 1
  fi
}

# === Rollback: restaurar Caddy ===
rollback() {
  echo "→ Restaurando Caddy..."
  
  # Detener y remover Traefik
  cd "${GATEWAY_DIR}"
  docker compose down 2>/dev/null || true
  docker compose --profile full down 2>/dev/null || true
  
  # Iniciar Caddy
  systemctl start caddy 2>/dev/null || true
  systemctl enable caddy 2>/dev/null || true
  
  echo "✅ Rollback completado. Caddy restaurado."
  exit 0
}

# === Deploy ===
deploy() {
  echo "→ Verificando prerrequisitos..."
  check_prereqs
  
  # Crear network si no existe
  docker network inspect hpd-gateway &>/dev/null || \
    docker network create hpd-gateway
  
  # Asegurar permisos del storage ACME
  mkdir -p "${GATEWAY_DIR}/data/acme"
  chmod 600 "${GATEWAY_DIR}/data/acme" 2>/dev/null || true

  # Detener Caddy (comparte puertos 80/443)
  if systemctl is-active --quiet caddy; then
    echo "→ Deteniendo Caddy (puertos 80/443 necesarios para Traefik)..."
    systemctl stop caddy
    systemctl disable caddy
    echo "  Caddy detenido. Se puede restaurar con --rollback"
  fi

  # Desplegar Traefik
  cd "${GATEWAY_DIR}"
  COMPOSE_OPTS=""
  if [ -n "${PROFILE}" ]; then
    COMPOSE_OPTS="--profile ${PROFILE}"
  fi

  echo "→ Desplegando Traefik..."
  docker compose ${COMPOSE_OPTS} pull
  docker compose ${COMPOSE_OPTS} up -d

  # Verificar
  echo "→ Verificando..."
  sleep 5
  if docker ps | grep -q hpd-traefik; then
    echo "✅ Traefik desplegado correctamente"
    echo ""
    echo "📊 Dashboard: https://traefik.ia.matutino.online"
    echo "   (configurar password primero: htpasswd -nb admin <password>)"
    echo ""
    echo "🌐 Servicios enrutados:"
    echo "   - https://ia.matutino.online → AI Gateway"
    echo "   - https://ia.matutino.online/hpd/* → HPD API"
    echo "   - https://cotidianodia.online → WordPress"
    echo "   - https://matutino.online → Matutino"
    echo ""
    echo "📋 Logs: docker compose logs -f"
  else
    echo "❌ ERROR: Traefik no se inició" >&2
    docker compose logs traefik --tail 20
    exit 1
  fi
}

# === Main ===
if [ "${ROLLBACK}" = true ]; then
  rollback
else
  deploy
fi
