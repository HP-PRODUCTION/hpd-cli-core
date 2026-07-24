import argparse
import subprocess
import os
import sys
import secrets
from pathlib import Path

TOKEN_FILE = Path.home() / ".hpd" / "ui_token"

def _load_or_create_token() -> str:
    """Lee el token persistente o genera uno nuevo y lo guarda."""
    # Primero verificar variable de entorno (permite override manual)
    token = os.environ.get("HPD_UI_TOKEN")
    if token:
        return token
    
    # Leer desde archivo persistente
    if TOKEN_FILE.exists():
        token = TOKEN_FILE.read_text().strip()
        if token:
            return token
    
    # Generar token nuevo y guardarlo
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    token = secrets.token_hex(16)
    TOKEN_FILE.write_text(token)
    TOKEN_FILE.chmod(0o600)  # Solo lectura para el propietario
    return token

def setup_parser(subparsers):
    parser = subparsers.add_parser("ui", help="Inicia el Control Plane UI (React + FastAPI)")
    parser.add_argument("--reset-token", action="store_true", help="Genera un nuevo token de acceso")
    parser.set_defaults(func=run_ui)

def run_ui(args):
    print("Iniciando HPD Control Plane...")

    if getattr(args, "reset_token", False) and TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
        print("🔄 Token anterior eliminado. Se generará uno nuevo.")

    token = _load_or_create_token()
    os.environ["HPD_UI_TOKEN"] = token

    print("\n" + "="*50)
    print("🔒 Token de Acceso (persiste entre reinicios):")
    print(f"   {token}")
    print(f"   Guardado en: {TOKEN_FILE}")
    print("="*50 + "\n")

    # Iniciar FastAPI
    api_cmd = [sys.executable, "-m", "uvicorn", "hpd_cli.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
    api_process = subprocess.Popen(api_cmd)
    print("✓ Backend FastAPI iniciado en http://localhost:8000")

    # Iniciar React
    ui_dir = os.path.join(os.getcwd(), "control-plane")
    ui_process = None
    if os.path.exists(ui_dir):
        print("Iniciando React Frontend...")
        ui_process = subprocess.Popen(["npm", "run", "dev"], cwd=ui_dir)
    else:
        print(f"Advertencia: No se encontró el directorio '{ui_dir}'. Frontend no iniciado.")

    try:
        api_process.wait()
        if ui_process:
            ui_process.wait()
    except KeyboardInterrupt:
        print("\nApagando servidores...")
        api_process.terminate()
        if ui_process:
            ui_process.terminate()

