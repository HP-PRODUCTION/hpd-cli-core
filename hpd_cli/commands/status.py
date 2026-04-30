import argparse
from pathlib import Path

from rich.console import Console
from rich.table import Table
from hpd_cli.commands.serverize import PROJECTS

def setup_parser(subparsers: argparse._SubParsersAction):
    parser = subparsers.add_parser("status", help="Muestra el estado global de la infraestructura HPD")
    parser.add_argument("target", choices=["all"], help="Objetivo del status")
    parser.set_defaults(func=execute)

def execute(args: argparse.Namespace):
    console = Console()
    console.print("\n[bold cyan]🌍 HPD Global Status[/bold cyan]\n")
    
    table = Table(show_header=True, header_style="bold magenta", box=None)
    table.add_column("Proyecto", style="bold")
    table.add_column("Tipo")
    table.add_column("Estado", justify="right")
    
    for name, config in PROJECTS.items():
        path = Path(config["path"])
        if path.exists():
            status = "[green]OK[/green]"
        else:
            status = "[red]MISSING[/red]"
        table.add_row(name, config.get("kind", "unknown"), status)
    
    console.print(table)
    console.print("\n[dim]Usa 'hpd <proyecto> doctor' para un diagnóstico detallado.[/dim]\n")
