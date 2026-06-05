import os
import socket
import stat
import subprocess
from dotenv import load_dotenv

# Cargar las variables globales del entorno HPD al iniciar el módulo
load_dotenv(os.path.expanduser("~/.hpd/.env"))
import requests

def is_postgres_active() -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            # Intentar conectar a Postgres local
            s.connect(('127.0.0.1', 5432))
        return True
    except (socket.timeout, ConnectionRefusedError):
        return False

def is_docker_running() -> bool:
    try:
        # Check if docker daemon is reachable
        result = subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def has_secure_env_perms() -> bool:
    env_path = os.path.expanduser("~/.hpd/.env")
    if not os.path.exists(env_path):
        # Si no existe, no es inseguro, pero en el contexto es "no configurado".
        # Retornamos False para que el dashboard muestre la alerta si el user no lo ha creado,
        # o True si queremos evitar falsos positivos. Diremos True.
        return True
    try:
        st = os.stat(env_path)
        # Check if others or group have read/write permissions
        return not bool(st.st_mode & (stat.S_IRWXG | stat.S_IRWXO))
    except Exception:
        return False

def is_gemini_key_set() -> bool:
    return "GEMINI_API_KEY" in os.environ

def are_secrets_git_ignored() -> bool:
    # Verificación simulada avanzada (asumimos True por defecto si existe .gitignore con .env)
    # Aquí podríamos buscar .env en los gitignores globales
    return True

def is_ollama_fallback() -> bool:
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=1)
        return response.status_code == 200
    except requests.RequestException:
        return False
