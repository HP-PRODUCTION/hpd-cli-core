import os
import psutil
import subprocess
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def diagnose(args):
    console.print(Panel.fit("🩺 Diagnóstico del Sistema HPD", style="bold cyan"))

    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_cores = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0

    # Memoria
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # Disco
    disk = psutil.disk_usage('/')

    # Docker
    docker_status = "❌ No disponible"
    containers = 0
    running = 0
    try:
        result = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True, timeout=5)
        containers = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        result_running = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True, timeout=5)
        running = len(result_running.stdout.strip().split('\n')) if result_running.stdout.strip() else 0
        docker_status = f"✅ {running}/{containers} contenedores activos"
    except:
        pass

    # Servicios críticos
    services = {}
    for svc in ["ssh", "docker", "nginx", "postgresql", "mysql"]:
        try:
            result = subprocess.run(["systemctl", "is-active", svc], capture_output=True, text=True, timeout=3)
            services[svc] = "🟢 Activo" if result.stdout.strip() == "active" else "🔴 Inactivo"
        except:
            services[svc] = "❌ Desconocido"

    # Tabla de diagnóstico
    table = Table(title="📊 Estado del Sistema")
    table.add_column("Componente", style="cyan")
    table.add_column("Valor", style="green")

    table.add_row("CPU", f"{cpu_percent}% ({cpu_cores} cores, {cpu_freq:.0f} MHz)")
    table.add_row("RAM", f"{mem.used / 1024**3:.1f} GB / {mem.total / 1024**3:.1f} GB ({mem.percent}%)")
    table.add_row("Swap", f"{swap.used / 1024**3:.1f} GB / {swap.total / 1024**3:.1f} GB ({swap.percent}%)")
    table.add_row("Disco /", f"{disk.used / 1024**3:.1f} GB / {disk.total / 1024**3:.1f} GB ({disk.percent}%)")
    table.add_row("Docker", docker_status)

    console.print(table)

    # Servicios
    console.print("\n[bold]Servicios[/bold]")
    for svc, status in services.items():
        console.print(f"  {svc}: {status}")

def setup_parser(subparsers):
    parser = subparsers.add_parser("diagnose", help="Diagnóstico completo del sistema")
    parser.set_defaults(func=diagnose)
