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
    },
    "ai": {
        "default_provider": "gemini",
        "fallback_chain": ["gemini", "deepseek", "openai", "anthropic", "ollama", "cloudflare"],
        "routing_rules": {
            "code_generate": ["openai", "anthropic", "gemini", "deepseek", "ollama", "cloudflare"],
            "architecture_review": ["anthropic", "openai", "gemini", "deepseek", "ollama"],
            "fast_lookup": ["ollama", "deepseek", "cloudflare", "gemini", "openai"],
            "default": ["gemini", "deepseek", "openai", "anthropic", "ollama", "cloudflare"]
        }
    },
    "logging": {
        "level": "INFO",
        "max_bytes": 1048576,
        "backup_count": 5
    }
}

def deep_merge(base, override):
    result = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def load_config():
    # Load global config first
    global_config_path = os.path.expanduser("~/.hpd/config.yaml")
    config = deep_merge({}, DEFAULT_CONFIG)

    if os.path.exists(global_config_path):
        try:
            import yaml
            with open(global_config_path, "r") as f:
                global_config = yaml.safe_load(f)
                if global_config:
                    config = deep_merge(config, global_config)
        except Exception:
            pass

    # Load local config and override
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                local_config = json.load(f)
                if local_config:
                    config = deep_merge(config, local_config)
        except json.JSONDecodeError:
            from hpd_cli import logger
            logger.error(f"{CONFIG_FILE} no es un JSON valido.")

    return config

def save_config(config_data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=4)
    from hpd_cli import logger
    logger.success(f"Configuracion guardada en {CONFIG_FILE}")

def ensure_config():
    config = load_config()
    # If no local config and no global config was merged, we still have DEFAULT_CONFIG
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
