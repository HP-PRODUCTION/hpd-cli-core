#!/bin/bash
# sync_to_vps.sh
# Sincroniza el proyecto local con la VPS usando Git

set -e

echo "🔁 Sincronizando hpd-cli-core con VPS..."

# 1. Commit local si hay cambios
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "📦 Haciendo commit de cambios locales..."
    git add -A
    git commit -m "Sync automático $(date '+%Y-%m-%d %H:%M')"
fi

# 2. Push al remoto
echo "⬆️ Subiendo cambios a origin..."
git push origin robust-cli-2026

# 3. Conectar a VPS y ejecutar pull + reinstalación
echo "🖥️ Actualizando VPS..."
ssh hpd@mx << 'EOF'
    cd /opt/hpd-cli-core
    git pull origin robust-cli-2026
    pip install -e .
    echo "✅ VPS actualizada."
EOF

echo "✅ Sincronización completada."
