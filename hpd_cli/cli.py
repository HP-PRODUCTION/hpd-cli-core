import argparse
import sys
from hpd_cli import logger

from hpd_cli.commands import (
    init,
    ai,
    etl,
    deploy,
    db,
    repo,
    docs,
    services,
    backup,
    status,
    check,
    integrate,
    system,
    lab,
    wordpress,
    plataforma,
    inversiones,
    setup,
    secure,
    ui,
    projects,
    agent,
    diagnose,
    run,
    suggest,
)
import os
import hashlib
import importlib.util


# Lista blanca de hashes SHA-256 de plugins permitidos (vacia = solo plugins firmados)
ALLOWED_PLUGIN_HASHES: set[str] = set()
PLUGINS_ENABLED = os.getenv("HPD_PLUGINS_ENABLED", "").lower() in ("1", "true", "yes")


def _is_plugin_allowed(filepath: str) -> bool:
    """Verifica que el plugin este en la lista blanca de hashes conocidos."""
    if not ALLOWED_PLUGIN_HASHES:
        return False  # Sin lista blanca configurada, no se cargan plugins
    try:
        with open(filepath, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        return digest in ALLOWED_PLUGIN_HASHES
    except Exception:
        return False


def load_plugins(subparsers):
    if not PLUGINS_ENABLED:
        return  # Plugins deshabilitados por defecto

    plugins_dir = os.path.expanduser("~/.hpd/plugins")
    if not os.path.exists(plugins_dir):
        return

    if not os.access(plugins_dir, os.R_OK | os.X_OK):
        print(f"⚠ Sin permisos de lectura en {plugins_dir}")
        return

    for filename in sorted(os.listdir(plugins_dir)):
        if filename.endswith(".py"):
            plugin_name = filename[:-3]
            filepath = os.path.join(plugins_dir, filename)

            if not _is_plugin_allowed(filepath):
                print(f"⚠ Plugin '{plugin_name}' omitido: no esta en la lista blanca de confianza.")
                continue

            spec = importlib.util.spec_from_file_location(plugin_name, filepath)
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                if hasattr(module, "setup_parser"):
                    module.setup_parser(subparsers)
            except Exception as e:
                print(f"Error cargando plugin {plugin_name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="HPD Platform Engine CLI", prog="hpd")
    parser.add_argument("--verbose", "-v", action="store_true", help="Mostrar logs de depuracion")
    parser.add_argument("--quiet", "-q", action="store_true", help="Mostrar solo errores")

    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")
    subparsers.required = True

    # Register subparsers
    init.setup_parser(subparsers)
    ai.setup_parser(subparsers)
    etl.setup_parser(subparsers)
    deploy.setup_parser(subparsers)
    db.setup_parser(subparsers)
    repo.setup_parser(subparsers)
    docs.setup_parser(subparsers)
    services.setup_parser(subparsers)
    backup.setup_parser(subparsers)
    status.setup_parser(subparsers)
    check.setup_parser(subparsers)
    integrate.setup_parser(subparsers)
    system.setup_parser(subparsers)
    lab.setup_parser(subparsers)
    wordpress.setup_parser(subparsers)
    plataforma.setup_parser(subparsers)
    inversiones.setup_parser(subparsers)
    setup.setup_parser(subparsers)
    secure.setup_parser(subparsers)
    ui.setup_parser(subparsers)
    projects.setup_parser(subparsers)
    agent.setup_parser(subparsers)
    diagnose.setup_parser(subparsers)
    run.setup_parser(subparsers)
    suggest.setup_parser(subparsers)

    # Load Plugins dynamically
    load_plugins(subparsers)

    # fallback if no arguments are passed
    if len(sys.argv) == 1:
        from rich.panel import Panel
        from rich.console import Console

        console = Console()
        console.print(
            Panel(
                "[bold cyan]HPD Platform Engine[/bold cyan]\n"
                "[dim]Tu centro de mando para automatizacion, ETL e IA[/dim]\n\n"
                "Usa los comandos de abajo para empezar.",
                title="Bienvenido",
                border_style="blue",
            )
        )
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    logger.configure(quiet=args.quiet, verbose=args.verbose)

    # Dispatch execution
    if hasattr(args, "func"):
        result = args.func(args)
        if isinstance(result, int):
            sys.exit(result)
    else:
        print(f"Comando '{args.command}' no implementado todavia.")


if __name__ == "__main__":
    main()
