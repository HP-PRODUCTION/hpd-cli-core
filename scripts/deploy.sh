#!/usr/bin/env bash
set -euo pipefail

# deploy.sh — Deploy hpd-cli-core from GitHub to VPS
# Usage: bash scripts/deploy.sh [--branch master] [--port 3100]
#
# Assumptions:
#   - Repo cloned at /opt/hpd/hpd-cli-core
#   - Pip installed system-wide (--break-system-packages)
#   - systemd service: hpd-api.service (puerto 3100)

APP_DIR="/opt/hpd/hpd-cli-core"
BRANCH="master"
PORT=3100
SERVICE="hpd-api"

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch) BRANCH="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --dir) APP_DIR="$2"; shift 2 ;;
    *) echo "Usage: $0 [--branch master] [--port 3100] [--dir /opt/hpd/hpd-cli-core]"; exit 1 ;;
  esac
done

echo "==================================="
echo "🚀 HPD Deploy Script"
echo "   Dir:    ${APP_DIR}"
echo "   Branch: ${BRANCH}"
echo "   Port:   ${PORT}"
echo "==================================="

# 1. Pull latest code
echo ""
echo "📦 Pulling ${BRANCH} from GitHub..."
cd "${APP_DIR}"
git fetch origin
git checkout "${BRANCH}"
git pull origin "${BRANCH}"
echo "   ✅ HEAD: $(git log --oneline -1)"

# 2. Display changelog
echo ""
echo "📋 Últimos cambios:"
git log --oneline -5

# 3. Install dependencies
echo ""
echo "📦 Instalando dependencias..."
pip install --break-system-packages --ignore-installed typing_extensions -e "${APP_DIR}" 2>&1 | tail -3
echo "   ✅ Instalación completa"

# 4. Restart service
echo ""
echo "🔄 Reiniciando ${SERVICE}..."
if systemctl is-active --quiet "${SERVICE}"; then
    systemctl restart "${SERVICE}"
    echo "   ✅ Servicio reiniciado"
else
    echo "   ⚠️  Servicio no activo — intentando iniciar..."
    systemctl start "${SERVICE}" || true
fi

# 5. Health check
echo ""
echo "🩺 Verificando salud..."
sleep 2
HEALTH=$(curl -sf "http://localhost:${PORT}/api/v1/system/health" 2>/dev/null || echo "")
if [ -n "${HEALTH}" ]; then
    echo "${HEALTH}" | python3 -m json.tool 2>/dev/null || echo "   ⚠️  Respuesta: ${HEALTH}"
    echo "   ✅ Health check OK (puerto ${PORT})"
else
    echo "   ❌ Health check falló en puerto ${PORT}"
    journalctl -u "${SERVICE}" --no-pager -n 10
fi

# 6. Final status
echo ""
echo "📊 Estado final:"
systemctl status "${SERVICE}" --no-pager 2>&1 | head -6
echo ""
echo "==================================="
echo "✅ Deploy completado"
echo "==================================="
