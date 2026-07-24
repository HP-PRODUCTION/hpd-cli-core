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

# 3. Conectar a VPS y ejecutar actualización
echo "🖥️ Actualizando VPS..."

ssh vps << 'ENDSSH'
    set -e

    # Ruta correcta en la VPS
    PROJECT_DIR="/opt/hpd/hpd-cli-core"
    VENV_DIR="$PROJECT_DIR/venv"

    echo "📂 Usando directorio: $PROJECT_DIR"

    # Si no existe el directorio, clonar
    if [ ! -d "$PROJECT_DIR" ]; then
        echo "📥 Clonando repositorio en $PROJECT_DIR..."
        sudo mkdir -p "$(dirname $PROJECT_DIR)"
        sudo git clone https://github.com/HP-PRODUCTION/hpd-cli-core.git "$PROJECT_DIR"
        sudo chown -R $USER:$USER "$PROJECT_DIR"
    fi

    cd "$PROJECT_DIR"

    # Traer cambios
    git pull origin robust-cli-2026

    # Crear entorno virtual si no existe
    if [ ! -d "$VENV_DIR" ]; then
        echo "🐍 Creando entorno virtual en $VENV_DIR..."
        python3 -m venv "$VENV_DIR"
    fi

    # Activar entorno e instalar
    echo "📦 Instalando hpd-cli-core en el entorno virtual..."
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install -e .

    # Crear alias global para hpd
    if ! grep -q "alias hpd=" ~/.bashrc; then
        echo "🔗 Añadiendo alias hpd a ~/.bashrc..."
        echo "alias hpd='$VENV_DIR/bin/hpd'" >> ~/.bashrc
        echo "alias hpdai='$VENV_DIR/bin/hpd ai ask'" >> ~/.bashrc
        echo "alias hpdask='$VENV_DIR/bin/hpd ai ask'" >> ~/.bashrc
    fi

    # Verificar instalación
    echo "✅ Instalación completada. Probando comando..."
    $VENV_DIR/bin/hpd ai status || echo "⚠️ El comando falló, pero el alias se creó."

    echo "✅ VPS actualizada."
    echo "⚠️ Para usar 'hpd' sin ruta completa, ejecuta: source ~/.bashrc"
ENDSSH

echo "✅ Sincronización completada."# (pega el contenido de arriba)
