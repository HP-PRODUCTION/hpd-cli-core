# Deploy HPD CLI Core to a VPS

This guide explains a minimal, reproducible way to deploy the `hpd-cli-core` app on a Linux VPS (Debian/Ubuntu).

Prerequisites on VPS

- Python 3.11+ and `python3-venv` package
- git
- sudo privileges for the deploy user

Quick steps

```bash
# on the VPS
sudo apt update && sudo apt install -y python3-venv python3-pip git
# clone the repo (or rsync the project)
git clone <your-repo-url> /home/hpd/hpd-cli-core
cd /home/hpd/hpd-cli-core
# create a venv and install editable
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
# create global config dir and add secrets
mkdir -p ~/.hpd
cat > ~/.hpd/.env <<EOF
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_MODEL=deepseek-chat
EOF
# install systemd unit (as root)
sudo cp deploy/hpd-cli.service.template /etc/systemd/system/hpd-cli.service
sudo systemctl daemon-reload
sudo systemctl enable --now hpd-cli.service
sudo journalctl -u hpd-cli.service -f
```

Optional: Use the provided helper script

If you copied the repository to the VPS, you can use the helper script:

```bash
# run as the deploy user to prepare venv/install
bash scripts/deploy_vps.sh hpd /home/hpd/hpd-cli-core
# then run as root to write the systemd unit and start the service
sudo bash scripts/deploy_vps.sh hpd /home/hpd/hpd-cli-core
```

Testing

- Verify the CLI is available: `hpd --help`
- Test an AI chat (requires `DEEPSEEK_API_KEY` in `~/.hpd/.env`):

```bash
hpdai "Resume brevemente este repositorio"
```

Notes

- The script is intentionally minimal and safe: it will not overwrite your project directory.
- You should secure `~/.hpd/.env` (chmod 600) and avoid committing secrets to git.
