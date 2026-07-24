#!/usr/bin/env bash
set -euo pipefail

# Non-interactive VPS bootstrap for HPD CLI Core
# Usage (as root):
# DEPLOY_USER=hpd GIT_URL=https://... DEEPSEEK_API_KEY=sk-... bash deploy_vps_noninteractive.sh

DEPLOY_USER=${DEPLOY_USER:-hpd}
APP_DIR=${APP_DIR:-/home/${DEPLOY_USER}/hpd-cli-core}
GIT_URL=${GIT_URL:-}
VENV_DIR=${VENV_DIR:-${APP_DIR}/venv}
SERVICE_PATH=${SERVICE_PATH:-/etc/systemd/system/hpd-cli.service}

if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run as root" >&2
  exit 2
fi

apt update
apt install -y git python3-venv python3-pip

if ! id -u "${DEPLOY_USER}" >/dev/null 2>&1; then
  adduser --disabled-password --gecos "" "${DEPLOY_USER}"
fi

# Clone or use existing
if [ -n "${GIT_URL}" ]; then
  rm -rf "${APP_DIR}"
  sudo -u "${DEPLOY_USER}" git clone "${GIT_URL}" "${APP_DIR}"
fi

if [ ! -d "${APP_DIR}" ]; then
  echo "ERROR: ${APP_DIR} not found. Provide GIT_URL to clone or create the directory first." >&2
  exit 3
fi

# Create venv and install
sudo -u "${DEPLOY_USER}" python3 -m venv "${VENV_DIR}"
sudo -iu "${DEPLOY_USER}" bash -lc "source '${VENV_DIR}/bin/activate' && python -m pip install --upgrade pip && python -m pip install -e '${APP_DIR}'"

# Create HPD home and .env with provided key
HPD_HOME="/home/${DEPLOY_USER}/.hpd"
mkdir -p "${HPD_HOME}"
chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "${HPD_HOME}"
chmod 700 "${HPD_HOME}"

if [ -n "${DEEPSEEK_API_KEY:-}" ]; then
  cat > "${HPD_HOME}/.env" <<EOF
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
DEEPSEEK_MODEL=deepseek-chat
EOF
  chown "${DEPLOY_USER}:${DEPLOY_USER}" "${HPD_HOME}/.env"
  chmod 600 "${HPD_HOME}/.env"
else
  if [ ! -f "${HPD_HOME}/.env" ]; then
    cat > "${HPD_HOME}/.env" <<EOF
# Add your DEEPSEEK_API_KEY here
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-chat
EOF
    chown "${DEPLOY_USER}:${DEPLOY_USER}" "${HPD_HOME}/.env"
    chmod 600 "${HPD_HOME}/.env"
  fi
fi

# Install systemd unit
TEMPLATE="${APP_DIR}/deploy/hpd-cli.service.template"
if [ -f "${TEMPLATE}" ]; then
  cp "${TEMPLATE}" "${SERVICE_PATH}"
  sed -i "s|User=hpd|User=${DEPLOY_USER}|g" "${SERVICE_PATH}"
  sed -i "s|WorkingDirectory=/home/hpd/hpd-cli-core|WorkingDirectory=${APP_DIR}|g" "${SERVICE_PATH}"
  sed -i "s|/home/hpd/hpd-cli-core/venv|${VENV_DIR}|g" "${SERVICE_PATH}"
else
  cat > "${SERVICE_PATH}" <<EOF
[Unit]
Description=HPD CLI Core API
After=network.target

[Service]
Type=simple
User=${DEPLOY_USER}
WorkingDirectory=${APP_DIR}
ExecStart=${VENV_DIR}/bin/uvicorn hpd_cli.api.main:app --host 0.0.0.0 --port 3001
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
fi

chmod 644 "${SERVICE_PATH}"
systemctl daemon-reload
systemctl enable --now hpd-cli.service

echo "Service installed and started. Check: systemctl status hpd-cli.service"