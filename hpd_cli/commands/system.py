import os
import json
import glob
import time
import subprocess
import platform
import shutil
import psutil
from pathlib import Path
from datetime import datetime
from hpd_cli import logger
from hpd_cli.commands.serverize import register_serverize_parser

def setup_parser(subparsers):
    parser = subparsers.add_parser("system", help="Mantenimiento y soporte técnico del sistema")
    system_subparsers = parser.add_subparsers(dest="system_command", help="Subcomandos de sistema")
    system_subparsers.required = True

    # Phase 1: Diagnostics
    doc_parser = system_subparsers.add_parser("doctor", help="Diagnóstico integral del sistema")
    doc_parser.add_argument("--json", action="store_true", help="Salida en formato JSON")
    doc_parser.add_argument("--verbose", "-v", action="store_true", help="Mostrar detalles técnicos completos")
    doc_parser.add_argument("--history", action="store_true", help="Guardar instantánea en el historial")

    system_subparsers.add_parser("trends", help="Analizar tendencias de salud del sistema")
    system_subparsers.add_parser("disks", help="Uso de discos y particiones")
    system_subparsers.add_parser("memory", help="Estado de RAM y Swap")
    system_subparsers.add_parser("cpu", help="Carga y métricas del CPU")
    system_subparsers.add_parser("processes", help="Procesos pesados")
    system_subparsers.add_parser("services", help="Servicios activos y su estado")
    system_subparsers.add_parser("report", help="Generar reporte técnico completo")

    # Phase 2: Cleaning
    clean_parser = system_subparsers.add_parser("clean", help="Limpieza de archivos temporales y basura")
    clean_parser.add_argument("--dry-run", action="store_true", help="Simular limpieza sin borrar nada")
    clean_parser.add_argument("--apply", action="store_true", help="Ejecutar limpieza real")

    fix_parser = system_subparsers.add_parser("fix", help="Reparaciones guiadas no destructivas")
    fix_parser.add_argument("target", choices=["docker", "env-perms", "ollama-model", "swap"], help="Objetivo a corregir")
    fix_parser.add_argument("--apply", action="store_true", help="Ejecutar la reparacion; por defecto solo muestra comandos")
    fix_parser.add_argument("--model", default=os.getenv("OLLAMA_MODEL", "llama3.1:8b"), help="Modelo Ollama para ollama-model")

    register_serverize_parser(system_subparsers)

    parser.set_defaults(func=execute)

def execute(args):
    if args.system_command == "doctor":
        run_doctor(json_format=args.json, verbose=args.verbose, history=args.history)
    elif args.system_command == "trends":
        show_trends()
    elif args.system_command == "disks":
        show_disks()
    elif args.system_command == "memory":
        show_memory()
    elif args.system_command == "cpu":
        show_cpu()
    elif args.system_command == "processes":
        show_processes()
    elif args.system_command == "services":
        show_services()
    elif args.system_command == "report":
        generate_report()
    elif args.system_command == "clean":
        run_clean(dry_run=args.dry_run, apply=args.apply)
    elif args.system_command == "fix":
        run_fix(args.target, apply=args.apply, model=getattr(args, "model", "llama3.1:8b"))

def run_doctor(json_format=False, verbose=False, history=False):
    metrics = collect_metrics(verbose=verbose)
    score, deductions = calculate_score(metrics)

    if history:
        save_history(metrics, score)
        logger.success("Instantánea guardada en el historial.")

    if json_format:
        print(json.dumps({"metrics": metrics, "score": score, "deductions": deductions}, indent=2))
        return

    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    console = Console()

    status_icon = "🟢" if score > 80 else "🟡" if score > 50 else "🔴"
    status_text = "Healthy" if score > 80 else "Warning" if score > 50 else "Critical"

    console.print(f"\n[bold cyan]🩺 HPD SYSTEM DOCTOR[/bold cyan] {status_icon} [bold]{status_text}[/bold]\n")

    # Summary Table
    table = Table(show_header=False, box=None)
    table.add_row("[bold]Host[/bold]", f"{platform.node()} ({platform.system()} {platform.release()})")
    table.add_row("[bold]Uptime[/bold]", get_uptime())
    table.add_row("[bold]Score[/bold]", f"{score}/100")
    console.print(table)

    # Metrics breakdown (simplified for brevity here, logic remains same)
    # ... (existing metrics display logic)

    # Metrics breakdown
    for section, data in metrics.items():
        if section == "host": continue
        color = "green" if not any(d['section'] == section for d in deductions) else "yellow"
        console.print(f"\n[bold {color}] {section.upper()}[/bold {color}]")
        for key, val in data.items():
            if isinstance(val, dict):
                for k, v in val.items():
                    console.print(f"  - {k}: {v}")
            else:
                console.print(f"  - {key}: {val}")

    if deductions:
        console.print("\n[bold red]⚠️ Deducciones de salud:[/bold red]")
        for d in deductions:
            console.print(f" - [red]-{d['points']}[/red] pts: {d['reason']} ({d['section']})")

    # Fix Hints
    hints = generate_hints(metrics, deductions)
    if hints:
        console.print(Panel("\n".join([f"• {h}" for h in hints]), title="💡 Fix Hints", border_style="blue"))

def collect_metrics(verbose=False):
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    load = os.getloadavg()
    cpu_usage = psutil.cpu_percent(interval=0.5)

    metrics = {
        "host": {
            "name": platform.node(),
            "os": platform.platform(),
            "uptime": get_uptime()
        },
        "cpu": {
            "usage_pct": cpu_usage,
            "load_avg": load
        },
        "memory": {
            "ram_used_pct": mem.percent,
            "ram_available_mb": mem.available // (1024**2),
            "swap_used_pct": swap.percent
        },
        "disk": {},
        "docker": {
            "running": False,
            "containers_total": 0,
            "containers_running": 0,
            "error": None,
        }
    }

    # Disk metrics
    seen_devices = set()
    for part in psutil.disk_partitions():
        if 'loop' in part.device or 'snap' in part.device or not part.fstype: continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
            # Avoid redundant partitions (like /var/lib/docker which is often same as /)
            # We use (total_size, fstype) as a proxy for unique physical device/partition
            dev_id = (usage.total, part.fstype)
            if dev_id in seen_devices and not verbose: continue

            metrics["disk"][part.mountpoint] = {
                "used_pct": usage.percent,
                "free_gb": usage.free // (1024**3)
            }
            seen_devices.add(dev_id)
        except (OSError, PermissionError):
            pass

    # Docker metrics
    try:
        docker_result = subprocess.run(
            ["docker", "info", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if docker_result.returncode != 0:
            metrics["docker"]["error"] = (docker_result.stderr or docker_result.stdout).strip()
            return metrics

        info = json.loads(docker_result.stdout)
        server_errors = info.get("ServerErrors") or []
        if server_errors:
            metrics["docker"]["error"] = "; ".join(server_errors)
            return metrics

        if not server_errors:
            metrics["docker"] = {
                "running": True,
                "containers_total": info.get("Containers", 0),
                "containers_running": info.get("ContainersRunning", 0),
                "images": info.get("Images", 0),
                "error": None,
            }
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        metrics["docker"]["error"] = str(exc)

    return metrics

def get_uptime():
    if shutil.which("uptime"):
        try:
            return subprocess.check_output(["uptime", "-p"], text=True).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    boot_time = datetime.fromtimestamp(psutil.boot_time())
    delta = datetime.now() - boot_time
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    parts = []
    if days:
        parts.append(f"{days} days")
    if hours:
        parts.append(f"{hours} hours")
    parts.append(f"{minutes} minutes")
    return "up " + ", ".join(parts)

def get_service_manager():
    if shutil.which("systemctl") and Path("/run/systemd/system").exists():
        return "systemd"
    if shutil.which("service") and Path("/etc/init.d").exists():
        return "sysvinit"
    return "none"

def service_status(service_name):
    manager = get_service_manager()
    if manager == "systemd":
        result = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True, check=False)
        return result.stdout.strip() or "inactive"
    if manager == "sysvinit":
        result = subprocess.run(["service", service_name, "status"], capture_output=True, text=True, check=False)
        return "active" if result.returncode == 0 else "inactive"

    if service_name == "docker" and shutil.which("docker"):
        result = subprocess.run(["docker", "info"], capture_output=True, text=True, check=False)
        return "active" if result.returncode == 0 else "inactive"
    return "unknown"

def calculate_score(metrics):
    score = 100
    deductions = []

    # RAM check
    if metrics["memory"]["ram_used_pct"] > 90:
        deductions.append({"section": "memory", "points": 15, "reason": "RAM usage > 90%"})
    elif metrics["memory"]["ram_used_pct"] > 80:
        deductions.append({"section": "memory", "points": 5, "reason": "RAM usage > 80%"})

    # Swap check
    if metrics["memory"]["swap_used_pct"] > 50:
        deductions.append({"section": "memory", "points": 10, "reason": "Swap usage > 50%"})
    elif metrics["memory"]["swap_used_pct"] > 20:
        deductions.append({"section": "memory", "points": 5, "reason": "Swap usage > 20%"})

    # CPU Load check
    load1 = metrics["cpu"]["load_avg"][0]
    cores = psutil.cpu_count()
    if load1 > cores * 2:
        deductions.append({"section": "cpu", "points": 15, "reason": "Extreme Load Average"})
    elif load1 > cores:
        deductions.append({"section": "cpu", "points": 5, "reason": "High Load Average"})

    # Disk check
    for mount, d in metrics["disk"].items():
        if d["used_pct"] > 90:
            deductions.append({"section": "disk", "points": 15, "reason": f"Disk {mount} > 90% full"})
        elif d["used_pct"] > 80:
            deductions.append({"section": "disk", "points": 5, "reason": f"Disk {mount} > 80% full"})

    # Docker check
    if not metrics["docker"]["running"]:
        docker_error = metrics["docker"].get("error")
        if docker_error and "permission denied" in docker_error.lower():
            reason = "Docker daemon inaccessible: permission denied"
        else:
            reason = "Docker daemon not running"
        deductions.append({"section": "docker", "points": 20, "reason": reason})

    total_deduction = sum(d["points"] for d in deductions)
    score = max(0, 100 - total_deduction)
    return score, deductions

def generate_hints(metrics, deductions):
    hints = []
    sections = [d["section"] for d in deductions]

    if "memory" in sections:
        hints.append("Ejecuta 'hpd system processes' para identificar fugas de memoria.")
    if "disk" in sections:
        hints.append("Usa 'hpd system clean --dry-run' para ver qué archivos puedes borrar.")
    if "docker" in sections:
        if not metrics["docker"]["running"]:
            manager = get_service_manager()
            if manager == "systemd":
                hints.append("Intenta reiniciar Docker: 'sudo systemctl restart docker'.")
            elif manager == "sysvinit":
                hints.append("Intenta reiniciar Docker: 'sudo service docker restart'.")
            elif "permission denied" in str(metrics["docker"].get("error", "")).lower():
                hints.append("Docker esta activo, pero el usuario/sandbox no puede acceder a /var/run/docker.sock.")
            else:
                hints.append("Verifica Docker con 'docker info' o inicia Docker Desktop/daemon.")
        elif metrics["docker"]["containers_total"] > metrics["docker"]["containers_running"]:
            hints.append("Tienes contenedores detenidos. Considera 'hpd system clean' para podarlos.")

    if metrics["cpu"]["usage_pct"] > 70:
        hints.append("El CPU está bajo presión. Revisa procesos en segundo plano.")

    return hints

def show_disks():
    logger.info("💾 Estado de Discos:")
    for part in psutil.disk_partitions():
        if 'loop' in part.device: continue
        usage = psutil.disk_usage(part.mountpoint)
        print(f" - {part.device} ({part.mountpoint}): {usage.percent}% usado ({usage.free // (1024**3)} GB libres)")

def show_memory():
    logger.info("🧠 Estado de Memoria:")
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    print(f" - RAM: {mem.percent}% usado ({mem.available // (1024**2)} MB disponibles de {mem.total // (1024**2)} MB)")
    print(f" - Swap: {swap.percent}% usado ({swap.free // (1024**2)} MB libres)")

def show_cpu():
    logger.info("⚡ Estado de CPU:")
    load = os.getloadavg()
    print(f" - Load Average (1, 5, 15 min): {load}")
    print(f" - Uso actual: {psutil.cpu_percent(interval=0.5)}%")

def show_processes():
    logger.info("📊 Procesos Pesados (Top 5 CPU):")
    # Sample for 1 second to get accurate %CPU
    for proc in psutil.process_iter():
        proc.cpu_percent(interval=None) # Start sampling
    time.sleep(0.5)

    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    top_cpu = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:5]
    for p in top_cpu:
        print(f" - [{p['pid']}] {p['name']}: {p['cpu_percent']}% CPU, {p['memory_percent']:.1f}% MEM")

def show_services():
    logger.info("🛠️ Servicios Críticos:")
    services = ["docker", "ssh", "apache2", "nginx", "mariadb", "postgresql", "redis"]
    for s in services:
        status = service_status(s)
        if status != "unknown":
            print(f" - {s}: {status}")

def run_clean(dry_run=True, apply=False):
    if not apply and not dry_run:
        logger.error("Debe especificar --dry-run o --apply")
        return

    mode = "SIMULACIÓN" if dry_run else "EJECUCIÓN REAL"
    logger.info(f"🧹 Iniciando limpieza de sistema ({mode})...")

    tasks = [
        ("Caché APT", ["apt-get", "clean"], shutil.which("apt-get") is not None),
        ("Paquetes huerfanos", ["apt-get", "autoremove", "-y"], shutil.which("apt-get") is not None),
        ("Logs antiguos (journald)", ["journalctl", "--vacuum-time=7d"], get_service_manager() == "systemd" and shutil.which("journalctl") is not None),
        ("Contenedores Docker detenidos", ["docker", "container", "prune", "-f"], shutil.which("docker") is not None),
        ("Imagenes Docker huerfanas", ["docker", "image", "prune", "-f"], shutil.which("docker") is not None),
        ("Volumenes Docker huerfanos", ["docker", "volume", "prune", "-f"], shutil.which("docker") is not None),
        ("Redes Docker huerfanas", ["docker", "network", "prune", "-f"], shutil.which("docker") is not None),
    ]

    for desc, cmd, enabled in tasks:
        cmd_text = " ".join(cmd)
        if not enabled:
            print(f" [SKIP] No disponible en este sistema: {cmd_text} ({desc})")
            continue
        if dry_run:
            print(f" [SKIP] Se ejecutaria: {cmd_text} ({desc})")
        else:
            print(f" [RUN] Ejecutando: {cmd_text} ({desc})")
            try:
                subprocess.run(cmd, check=False, capture_output=True)
            except Exception as e:
                print(f"  Error: {e}")

def run_fix(target, apply=False, model="llama3.1:8b"):
    commands = []
    if target == "docker":
        manager = get_service_manager()
        if manager == "systemd":
            commands = [["sudo", "systemctl", "restart", "docker"], ["docker", "info"]]
        elif manager == "sysvinit":
            commands = [["sudo", "service", "docker", "restart"], ["docker", "info"]]
        else:
            logger.warning("No se detecto gestor de servicios. Verifica Docker Desktop/daemon manualmente.")
            commands = [["docker", "info"]]
    elif target == "env-perms":
        commands = [["chmod", "600", os.path.expanduser("~/.hpd/.env")]]
    elif target == "ollama-model":
        commands = [["ollama", "pull", model], ["ollama", "list"]]
    elif target == "swap":
        commands = [["sudo", "swapoff", "-a"], ["sudo", "swapon", "-a"]]

    if not apply:
        logger.info("Dry-run. Usa --apply para ejecutar.")
        for command in commands:
            print(" ".join(command))
        return

    for command in commands:
        logger.info(f"Ejecutando: {' '.join(command)}")
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            logger.error(f"Comando fallo con codigo {result.returncode}: {' '.join(command)}")
            return
    logger.success(f"Fix aplicado: {target}")

def generate_report():
    report_file = "hpd_system_report.txt"
    logger.info(f"📝 Generando reporte en {report_file}...")
    with open(report_file, "w") as f:
        f.write("HPD System Maintenance Report\n")
        f.write("============================\n")
        # In a real impl, we would redirect stdout of other functions here
        f.write(f"Timestamp: {subprocess.check_output(['date'], text=True)}")
    logger.success("Reporte generado exitosamente.")

def save_history(metrics, score):
    history_dir = os.path.expanduser("~/.hpd/system/history")
    os.makedirs(history_dir, exist_ok=True)

    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "score": score,
        "cpu_usage": metrics["cpu"]["usage_pct"],
        "ram_usage": metrics["memory"]["ram_used_pct"],
        "disk_usage": max([d["used_pct"] for d in metrics["disk"].values()]) if metrics["disk"] else 0,
        "docker_running": metrics["docker"]["running"]
    }

    filename = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(os.path.join(history_dir, filename), "w") as f:
        json.dump(snapshot, f, indent=2)

def show_trends():
    from rich.console import Console
    from rich.table import Table

    console = Console()
    history_dir = os.path.expanduser("~/.hpd/system/history")
    files = sorted(glob.glob(os.path.join(history_dir, "snapshot_*.json")))

    if not files:
        logger.warning("No hay historial disponible aún. Ejecuta 'hpd system doctor --history' primero.")
        return

    table = Table(title="📈 Tendencias de Salud del Sistema", header_style="bold magenta")
    table.add_column("Fecha/Hora")
    table.add_column("Score", justify="right")
    table.add_column("CPU %", justify="right")
    table.add_column("RAM %", justify="right")
    table.add_column("Disk %", justify="right")

    # Show last 10 snapshots
    for f in files[-10:]:
        with open(f, "r") as file:
            data = json.load(file)
            color = "green" if data["score"] > 80 else "yellow" if data["score"] > 50 else "red"
            table.add_row(
                data["timestamp"].replace("T", " ")[:19],
                f"[{color}]{data['score']}[/{color}]",
                f"{data['cpu_usage']}%",
                f"{data['ram_usage']}%",
                f"{data['disk_usage']}%"
            )

    console.print(table)

    if len(files) > 1:
        # Simple trend analysis
        with open(files[-1], "r") as f1, open(files[-2], "r") as f2:
            last = json.load(f1)
            prev = json.load(f2)
            diff = last["score"] - prev["score"]
            trend = "mejorando 📈" if diff > 0 else "degradándose 📉" if diff < 0 else "estable ➡"
            console.print(f"\n[bold]Tendencia:[/bold] El sistema está {trend} (Cambio: {diff:+} pts)")
