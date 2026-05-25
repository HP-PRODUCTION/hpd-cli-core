import os
import shutil
import subprocess
from pathlib import Path

import yaml

from hpd_cli import logger


def setup_parser(subparsers):
    parser = subparsers.add_parser("setup", help="Configuracion inicial del CLI y entorno HPD")
    parser.add_argument("--force", action="store_true", help="Sobrescribir archivos existentes")
    parser.add_argument("--check", action="store_true", help="Validar entorno sin escribir archivos")
    parser.set_defaults(func=run)


def run(args):
    if args.check:
        run_check()
        return

    hpd_dir = Path.home() / ".hpd"
    hpd_dir.mkdir(exist_ok=True)
    (hpd_dir / "logs").mkdir(exist_ok=True)
    (hpd_dir / "cache").mkdir(exist_ok=True)
    (hpd_dir / "backups").mkdir(exist_ok=True)
    (hpd_dir / "plugins").mkdir(exist_ok=True)

    write_config(hpd_dir / "config.yaml", force=args.force)
    write_env(hpd_dir / ".env", force=args.force)
    check_dependencies()
    check_ai_router()

    logger.info("Configuracion completada. Ejecuta 'hpd system doctor' para validar la maquina.")


def write_config(config_path, force=False):
    if config_path.exists() and not force:
        logger.warning(f"Configuracion ya existe en {config_path}. Usa --force para sobrescribir.")
        return

    hpd_dir = config_path.parent
    default_config = {
        "directories": {
            "projects": str(Path.home() / "hpd-projects"),
            "logs": str(hpd_dir / "logs"),
            "cache": str(hpd_dir / "cache"),
            "backups": str(hpd_dir / "backups"),
        },
        "ai": {
            "default_provider": "gemini",
            "fallback_chain": ["gemini", "deepseek", "openai", "anthropic", "ollama", "cloudflare"],
            "routing_rules": {
                "code_generate": ["openai", "anthropic", "gemini", "deepseek", "ollama", "cloudflare"],
                "architecture_review": ["anthropic", "openai", "gemini", "deepseek", "ollama"],
                "fast_lookup": ["ollama", "deepseek", "cloudflare", "gemini", "openai"],
                "default": ["gemini", "deepseek", "openai", "anthropic", "ollama", "cloudflare"],
            },
            "ollama_url": "http://localhost:11434",
        },
        "system": {
            "docker_socket": "/var/run/docker.sock",
            "backup_dir": str(hpd_dir / "backups"),
        },
    }

    with open(config_path, "w") as f:
        yaml.safe_dump(default_config, f, sort_keys=False)

    logger.success(f"Configuracion creada en {config_path}")


def write_env(env_path, force=False):
    if env_path.exists() and not force:
        logger.warning(f".env ya existe en {env_path}")
        return

    env_content = """# HPD AI Providers
# GEMINI_API_KEY=tu_clave
# GOOGLE_API_KEY=tu_clave
# GEMINI_MODEL=gemini-2.5-flash
# OPENAI_API_KEY=tu_clave
# ANTHROPIC_API_KEY=tu_clave
# ANTHROPIC_MODEL=claude-3-5-haiku-latest
# CLOUDFLARE_API_TOKEN=tu_token
# CLOUDFLARE_ACCOUNT_ID=tu_account_id
# DEEPSEEK_API_KEY=tu_clave
# DEEPSEEK_BASE_URL=https://api.deepseek.com
# DEEPSEEK_MODEL=deepseek-v4-flash
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=llama3.1:8b

# System
# HPD_WORKSPACE_ROOT=/home/usuario/hpd-projects
"""
    env_path.write_text(env_content)
    try:
        os.chmod(env_path, 0o600)
    except OSError:
        logger.warning(f"No se pudieron ajustar permisos de {env_path}")

    logger.success(f"Archivo de entorno creado en {env_path}. Editalo con tus claves API.")


def check_dependencies():
    logger.info("Verificando dependencias del sistema...")
    dependencies = {
        "docker": ["docker", "--version"],
        "docker compose": ["docker", "compose", "version"],
        "git": ["git", "--version"],
        "python3": ["python3", "--version"],
        "ffmpeg": ["ffmpeg", "-version"],
    }

    missing = []
    for name, command in dependencies.items():
        executable = command[0]
        if not shutil.which(executable):
            missing.append(name)
            logger.warning(f"{name} no encontrado")
            continue

        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            logger.debug(f"{name} disponible")
        else:
            missing.append(name)
            logger.warning(f"{name} no disponible correctamente")

    if missing:
        logger.warning(f"Faltan dependencias opcionales: {', '.join(missing)}")
    else:
        logger.success("Todas las dependencias del sistema estan instaladas.")


def check_ai_router():
    try:
        from hpd_cli.ai_router import AIRouter

        AIRouter()
        logger.success("Router de IA inicializado correctamente.")
    except Exception as exc:
        logger.error(f"Error al inicializar router de IA: {exc}")


def run_check():
    from rich.console import Console
    from rich.table import Table
    from hpd_cli.ai_router import AIRouter

    console = Console()
    hpd_dir = Path.home() / ".hpd"
    config_path = hpd_dir / "config.yaml"
    env_path = hpd_dir / ".env"

    table = Table(title="HPD Setup Check", header_style="bold cyan")
    table.add_column("Check")
    table.add_column("Estado")
    table.add_column("Detalle")

    table.add_row("~/.hpd", "OK" if hpd_dir.exists() else "MISSING", str(hpd_dir))
    table.add_row("config.yaml", "OK" if config_path.exists() else "MISSING", str(config_path))
    if env_path.exists():
        mode = oct(env_path.stat().st_mode)[-3:]
        table.add_row(".env permisos", "OK" if mode == "600" else "WARN", mode)
    else:
        table.add_row(".env", "MISSING", str(env_path))

    for name in ("docker", "git", "python3", "ffmpeg", "psql", "pg_restore"):
        table.add_row(name, "OK" if shutil.which(name) else "MISSING", shutil.which(name) or "-")

    try:
        router = AIRouter()
        for name, status in router.get_status().items():
            table.add_row(f"ai:{name}", status, "")
    except Exception as exc:
        table.add_row("ai:router", "ERROR", str(exc)[:80])

    console.print(table)
