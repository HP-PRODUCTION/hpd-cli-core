import os
import time
from hpd_cli.config import save_config, DEFAULT_CONFIG
from hpd_cli import logger
from rich.panel import Panel
from rich.table import Table
from rich.console import Console

def setup_parser(subparsers):
    parser = subparsers.add_parser("init", help="Inicializa el entorno HPD Platform")
    parser.set_defaults(func=execute)

def execute(args):
    console = Console()
    
    with console.status("[bold green]Configurando entorno HPD Platform...") as status:
        # Create config file
        save_config(DEFAULT_CONFIG)
        time.sleep(0.5)
        
        # Create basic directory structure
        dirs_to_create = [
            DEFAULT_CONFIG["directories"]["modules"],
            DEFAULT_CONFIG["directories"]["docs"],
            DEFAULT_CONFIG["directories"]["etl"],
            DEFAULT_CONFIG["directories"]["dags"],
        ]
        
        table = Table(title="Estructura Creada", show_header=True, header_style="bold magenta")
        table.add_column("Carpeta", style="dim")
        table.add_column("Estado")
        
        for d in dirs_to_create:
            os.makedirs(d, exist_ok=True)
            table.add_row(d, "[green]✔ Lista[/green]")
            if d.startswith("modules"):
                init_file = os.path.join(d, "__init__.py")
                if not os.path.exists(init_file):
                    with open(init_file, 'w') as f:
                        f.write('"""HPD Modules"""\n')
        
        time.sleep(0.5)

    console.print(Panel.fit(
        "[bold cyan]¡HPD Platform Inicializada![/bold cyan]\n\n"
        "Tu entorno esta listo para escalar.\n"
        "Usa [yellow]hpd --help[/yellow] para ver los comandos disponibles.",
        title="Éxito",
        border_style="green"
    ))
    
    console.print(table)
    logger.success("Proceso de inicializacion completado.")
