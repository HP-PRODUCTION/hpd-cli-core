#!/usr/bin/env bash
set -euo pipefail

# Simple VPS deploy helper for HPD CLI Core
# Usage: sudo ./scripts/deploy_vps.sh [--user hpd] [--app-dir /home/hpd/hpd-cli-core]

USER=${1:-hpd}
APP_DIR=${2:-/home/${USER}/hpd-cli-core}
VENV_DIR=${3:-${APP_DIR}/venv}
SERVICE_FILE=/etc/systemd/system/hpd-cli.service

echo "Deploying HPD CLI Core to VPS"
echo "App dir: ${APP_DIR}"

# Ensure app dir exists
if [ ! -d "${APP_DIR}" ]; then
  echo "ERROR: App directory ${APP_DIR} does not exist. Clone or copy the repo before running this script." >&2
  exit 2
fi

# Create venv
if [ ! -d "${VENV_DIR}" ]; then
  python3 -m venv "${VENV_DIR}"
fi

# Activate and install
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
python -m pip install -e "${APP_DIR}"

# Create user-wide config dir
HPD_HOME="/home/${USER}/.hpd"
mkdir -p "${HPD_HOME}"
chown -R ${USER}:${USER} "${HPD_HOME}"

# Reminder for .env
if [ ! -f "${HPD_HOME}/.env" ]; then
  cat > "${HPD_HOME}/.env" <<EOF
# HPD global env - add your secrets here
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-chat
EOF
  chown ${USER}:${USER} "${HPD_HOME}/.env"
  echo "Created ${HPD_HOME}/.env - edit it to add DEEPSEEK_API_KEY"
fi

# Install systemd service (requires sudo)
if [ "$(id -u)" -ne 0 ]; then
  echo "To install systemd unit you need to run this script as root (sudo)."
  echo "You can still run the app using: source ${VENV_DIR}/bin/activate && hpd ai chat \"hola\""
  exit 0
fi

# write service file
cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=HPD CLI Core API
After=network.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${APP_DIR}
ExecStart=${VENV_DIR}/bin/uvicorn hpd_cli.api.main:app --host 0.0.0.0 --port 3001
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable hpd-cli.service
systemctl restart hpd-cli.service

echo "Service installed and started: systemctl status hpd-cli.service"

exit 0
