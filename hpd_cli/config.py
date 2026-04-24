import json
import os

CONFIG_FILE = "hpd.config.json"

DEFAULT_CONFIG = {
    "project_name": "HPD Platform",
    "version": "1.0.0",
    "env": "development",
    "directories": {
        "modules": "modules",
        "docs": "docs",
        "etl": "etl",
        "dags": "airflow/dags",
        "logs": "data/logs",
        "staging": "data/staging",
        "backups": "data/backups"
    }
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        from hpd_cli import logger
        logger.error(f"{CONFIG_FILE} no es un JSON valido.")
        return None

def save_config(config_data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=4)
    from hpd_cli import logger
    logger.success(f"Configuracion guardada en {CONFIG_FILE}")

def ensure_config():
    config = load_config()
    if not config:
        from hpd_cli import logger
        logger.error("El proyecto no esta inicializado. Ejecuta 'hpd init' primero.")
        exit(1)
    return config

def validate_env():
    from hpd_cli import logger
    from dotenv import load_dotenv
    # Cargar .env_hpd global y .env local
    global_env = os.path.expanduser("~/.hpd/.env_hpd")
    if os.path.exists(global_env):
        load_dotenv(global_env)
    
    local_env = ".env"
    if os.path.exists(local_env):
        load_dotenv(local_env)
        
    # Verificar credenciales necesarias
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        logger.warning("No se encontro GEMINI_API_KEY ni OPENAI_API_KEY en el entorno.")
        logger.info("El modulo 'hpd ai' funcionara en modo simulado o arrojara error.")
