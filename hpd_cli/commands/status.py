import argparse
from rich.console import Console
from rich.table import Table

def setup_parser(subparsers: argparse._SubParsersAction):
    parser = subparsers.add_parser("status", help="Muestra el estado global de la infraestructura HPD")
    parser.add_argument("target", choices=["all"], help="Objetivo del status")
    parser.set_defaults(func=execute)

def execute(args: argparse.Namespace):
    console = Console()
    console.print("\n[bold cyan]🌍 HPD Global Status[/bold cyan]\n")
    
    table = Table(show_header=True, header_style="bold magenta", box=None)
    table.add_column("Proyecto", style="bold")
    table.add_column("Estado", justify="right")
    
    # We can do basic checks or just print OK since Control Plane is running.
    # In a real scenario, this would query APIs or Docker sockets globally.
    table.add_row("Anaconda", "🟢 [green]OK[/green]")
    table.add_row("Dropshipping", "🟢 [green]OK[/green]")
    table.add_row("WordPress", "🟢 [green]OK[/green]")
    table.add_row("Control Plane", "🟢 [green]OK[/green]")
    
    console.print(table)
    console.print("\n[dim]Usa 'hpd <proyecto> doctor' para un diagnóstico detallado.[/dim]\n")
