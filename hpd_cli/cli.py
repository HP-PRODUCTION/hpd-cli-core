import argparse
import sys

from hpd_cli.commands import init, ai, etl, deploy, db, repo, docs, services, backup, status, integrate, system, lab, wordpress
import os
import importlib.util

def load_plugins(subparsers):
    plugins_dir = os.path.expanduser("~/.hpd/plugins")
    if not os.path.exists(plugins_dir):
        return
        
    for filename in os.listdir(plugins_dir):
        if filename.endswith(".py"):
            plugin_name = filename[:-3]
            filepath = os.path.join(plugins_dir, filename)
            
            spec = importlib.util.spec_from_file_location(plugin_name, filepath)
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                if hasattr(module, 'setup_parser'):
                    module.setup_parser(subparsers)
            except Exception as e:
                print(f"Error cargando plugin {plugin_name}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="HPD Platform Engine CLI",
        prog="hpd"
    )
    
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
    integrate.setup_parser(subparsers)
    system.setup_parser(subparsers)
    lab.setup_parser(subparsers)
    wordpress.setup_parser(subparsers)
    
    # Load Plugins dynamically
    load_plugins(subparsers)
    
    # fallback if no arguments are passed
    if len(sys.argv) == 1:
        from rich.panel import Panel
        from rich.console import Console
        console = Console()
        console.print(Panel(
            "[bold cyan]HPD Platform Engine[/bold cyan]\n"
            "[dim]Tu centro de mando para automatizacion, ETL e IA[/dim]\n\n"
            "Usa los comandos de abajo para empezar.",
            title="Bienvenido",
            border_style="blue"
        ))
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    
    # Dispatch execution
    if hasattr(args, 'func'):
        args.func(args)
    else:
        print(f"Comando '{args.command}' no implementado todavia.")

if __name__ == "__main__":
    main()
