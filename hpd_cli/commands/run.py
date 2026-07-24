# hpd_cli/commands/run.py
import subprocess
import shlex
from rich.console import Console
from rich.panel import Panel

console = Console()

def run_command(args):
    if isinstance(args, str):
        cmd = args
    else:
        cmd = " ".join(args.command)
    console.print(Panel.fit(f"🔧 Ejecutando: {cmd}", style="bold yellow"))

    # Denylist básica (mejorar después)
    dangerous = ["rm -rf", "dd if=", "mkfs", "chmod 777", "sudo"]
    for d in dangerous:
        if d in cmd:
            console.print(f"[red]❌ Comando bloqueado por seguridad: {d}[/red]")
            return

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.stdout:
            console.print(result.stdout)
        if result.stderr:
            console.print(f"[yellow]stderr:[/yellow]\n{result.stderr}")
        console.print(f"\n✅ Código de salida: {result.returncode}")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")

def setup_parser(subparsers):
    parser = subparsers.add_parser("run", help="Ejecuta un comando del sistema (con seguridad)")
    parser.add_argument("command", nargs="+", help="Comando a ejecutar")
    parser.set_defaults(func=run_command)
