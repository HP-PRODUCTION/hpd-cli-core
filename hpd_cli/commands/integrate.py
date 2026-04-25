import argparse
import subprocess
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

def setup_parser(subparsers: argparse._SubParsersAction):
    parser = subparsers.add_parser("integrate", help="Orquestación entre dominios HPD")
    int_subparsers = parser.add_subparsers(dest="int_command", help="Operaciones de integración")
    int_subparsers.required = True
    
    # anaconda -> wordpress
    ana_wp = int_subparsers.add_parser("anaconda", help="Publicar indicadores de Anaconda en WordPress")
    ana_wp.add_argument("target", choices=["wordpress"], help="Destino de la integración")
    ana_wp.add_argument("--dry-run", action="store_true", help="Simular sin publicar")
    ana_wp.add_argument("--draft", action="store_true", help="Publicar como borrador")
    ana_wp.add_argument("--publish", action="store_true", help="Publicar oficialmente")
    ana_wp.add_argument("--non-interactive", action="store_true", help="Omitir confirmaciones")
    
    # dropshipping -> wordpress
    drop_wp = int_subparsers.add_parser("dropshipping", help="Publicar reseñas de productos en WordPress")
    drop_wp.add_argument("target", choices=["wordpress"], help="Destino de la integración")
    drop_wp.add_argument("--dry-run", action="store_true", help="Simular sin publicar")
    drop_wp.add_argument("--draft", action="store_true", help="Publicar como borrador")
    drop_wp.add_argument("--publish", action="store_true", help="Publicar oficialmente")
    drop_wp.add_argument("--non-interactive", action="store_true", help="Omitir confirmaciones")
    
    # status (integrated status)
    status = int_subparsers.add_parser("status", help="Estado integrado de todos los dominios")
    
    parser.set_defaults(func=execute)

def execute(args: argparse.Namespace):
    if args.int_command == "anaconda":
        run_anaconda_wordpress(args)
    elif args.int_command == "dropshipping":
        run_dropshipping_wordpress(args)
    elif args.int_command == "status":
        from . import status as status_cmd
        status_cmd.execute(args)

def run_anaconda_wordpress(args):
    anaconda_dir = Path("/home/hpd/proyecto_anaconda")
    
    if args.target != "wordpress":
        console.print(f"[red]Destino no soportado:[/red] {args.target}")
        return

    console.print(Panel("Iniciando Integración: [bold cyan]Anaconda ➔ WordPress[/bold cyan]", title="HPD Integrate"))

    python_bin = anaconda_dir / "venv" / "bin" / "python3"
    if not python_bin.exists():
        python_bin = "python3"
    
    cmd = [str(python_bin), "-m", "etl.publishers.wordpress.publisher"]
    if args.dry_run: cmd.append("--dry-run")
    if args.draft: cmd.append("--draft")
    if args.publish: cmd.append("--publish")
    if args.non_interactive: cmd.append("--non-interactive")

    try:
        # We need to set PYTHONPATH so it can find the etl package
        env = os.environ.copy()
        env["PYTHONPATH"] = str(anaconda_dir)
        
        result = subprocess.run(
            cmd,
            cwd=str(anaconda_dir),
            env=env,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            console.print("\n[green]Integración ejecutada correctamente.[/green]")
        else:
            console.print(f"\n[red]Error en la integración (Código {result.returncode})[/red]")
            
    except Exception as e:
        console.print(f"[red]Error ejecutando el publisher:[/red] {e}")
def run_dropshipping_wordpress(args):
    drop_dir = Path("/home/hpd/dropshipping-ebay")
    
    if args.target != "wordpress":
        console.print(f"[red]Destino no soportado:[/red] {args.target}")
        return

    console.print(Panel("Iniciando Integración: [bold yellow]Dropshipping ➔ WordPress[/bold yellow]", title="HPD Integrate"))

    python_bin = drop_dir / "venv" / "bin" / "python3"
    if not python_bin.exists():
        python_bin = "python3"

    cmd = [str(python_bin), "-m", "app.services.dropshipping_publisher"]
    if args.dry_run: cmd.append("--dry-run")
    if args.draft: cmd.append("--draft")
    if args.publish: cmd.append("--publish")
    if args.non_interactive: cmd.append("--non-interactive")

    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(drop_dir)
        
        result = subprocess.run(
            cmd,
            cwd=str(drop_dir),
            env=env,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            console.print("\n[green]Integración ejecutada correctamente.[/green]")
        else:
            console.print(f"\n[red]Error en la integración (Código {result.returncode})[/red]")
            
    except Exception as e:
        console.print(f"[red]Error ejecutando el publisher:[/red] {e}")
