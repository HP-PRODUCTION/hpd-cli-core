import subprocess
from hpd_cli.config import ensure_config
from hpd_cli import logger

def setup_parser(subparsers):
    parser = subparsers.add_parser("services", help="Comandos de Servicios")
    services_subparsers = parser.add_subparsers(dest="services_command", help="Subcomandos de Servicios")
    services_subparsers.required = True
    
    services_subparsers.add_parser("status", help="Ver estado de los servicios (Docker PS)")
    services_subparsers.add_parser("health", help="Prueba de salud profunda de los servicios")
    
    parser.set_defaults(func=execute)

def execute(args):
    ensure_config()
    
    if args.services_command == "status":
        logger.info("HPD Services: Estado actual del entorno...")
        subprocess.run(["docker-compose", "ps"])
    elif args.services_command == "health":
        perform_deep_health_check()

def perform_deep_health_check():
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    import psycopg2
    import requests
    import os
    import time
    import shutil
    from hpd_cli.config import load_config

    config = load_config()
    console = Console()
    console.print("\n[bold cyan]🔍 HPD Deep Health Check (Observabilidad Nivel 4)[/bold cyan]\n")

    services = [
        {"name": "PostgreSQL", "container": "etl_postgres", "type": "db", "port": 5433},
        {"name": "Metabase", "container": "etl_metabase", "type": "http", "port": 3000},
        {"name": "Airflow Web", "container": "airflow_webserver", "type": "http", "port": 8080},
        {"name": "Airflow Sched", "container": "airflow_scheduler", "type": "process", "port": None}
    ]

    table = Table(title="Estado de Infraestructura & Performance", header_style="bold magenta")
    table.add_column("Servicio", style="cyan")
    table.add_column("Status Docker", justify="center")
    table.add_column("Conectividad / Latencia", justify="center")
    table.add_column("Detalles / Métricas", style="dim")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        for svc in services:
            task_id = progress.add_task(f"Analizando {svc['name']}...", total=1)
            
            # 1. Docker Status
            docker_status = "[red]DOWN[/red]"
            try:
                result = subprocess.run(
                    ["docker", "inspect", "-f", "{{.State.Status}}", svc["container"]],
                    capture_output=True, text=True
                )
                if result.stdout.strip() == "running":
                    docker_status = "[green]RUNNING[/green]"
            except: pass

            # 2. Deep Checks
            conn_status = "[red]FAIL[/red]"
            metrics = "N/A"
            
            if svc["type"] == "db" and docker_status == "[green]RUNNING[/green]":
                start = time.time()
                try:
                    conn = psycopg2.connect(
                        dbname=os.getenv("DB_NAME", "etl_db"),
                        user=os.getenv("DB_USER", "etl_user"),
                        password=os.getenv("DB_PASSWORD", "changeme_local"),
                        host="localhost",
                        port=svc["port"],
                        connect_timeout=2
                    )
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1")
                    conn.close()
                    latency = (time.time() - start) * 1000
                    conn_status = f"[green]{latency:.1f}ms[/green]"
                    metrics = "Query Latency OK"
                except Exception as e:
                    metrics = str(e)[:30]
                    
            elif svc["type"] == "http" and docker_status == "[green]RUNNING[/green]":
                try:
                    resp = requests.get(f"http://localhost:{svc['port']}", timeout=3)
                    if resp.status_code < 500:
                        conn_status = "[green]SUCCESS[/green]"
                        metrics = f"HTTP {resp.status_code}"
                except: pass
                
            elif svc["type"] == "process" and docker_status == "[green]RUNNING[/green]":
                conn_status = "[green]OK[/green]"
                metrics = "Container active"

            table.add_row(svc["name"], docker_status, conn_status, metrics)
            progress.update(task_id, completed=1)

    console.print(table)

    # 3. Storage Monitoring & Alerts
    console.print("\n[bold cyan]💾 Monitoreo de Almacenamiento & Alertas[/bold cyan]")
    # Thresholds in Bytes: Logs: 100MB, Backups: 500MB, Staging: 1GB
    THRESHOLDS = {
        "Logs": 100 * 1024 * 1024,
        "Backups": 500 * 1024 * 1024,
        "Staging": 1024 * 1024 * 1024
    }
    
    storage_paths = [
        ("Logs", config.get("directories", {}).get("logs", "data/logs")),
        ("Backups", config.get("directories", {}).get("backups", "data/backups")),
        ("Staging", config.get("directories", {}).get("staging", "data/staging"))
    ]
    
    storage_table = Table(header_style="bold yellow")
    storage_table.add_column("Directorio", style="cyan")
    storage_table.add_column("Archivos", justify="right")
    storage_table.add_column("Tamaño Total", justify="right")
    storage_table.add_column("Alerta", justify="center")
    
    for label, path in storage_paths:
        if os.path.exists(path):
            files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
            total_size = sum(os.path.getsize(os.path.join(path, f)) for f in files)
            
            size_str = f"{total_size / 1024:.1f} KB" if total_size < 1024*1024 else f"{total_size / (1024*1024):.1f} MB"
            
            alert = "[green]OK[/green]"
            if total_size > THRESHOLDS.get(label, 0):
                alert = "[bold red]⚠️ EXCEDIDO[/bold red]"
                logger.warning(f"Alerta de Almacenamiento: {label} superó el límite ({size_str})")
            
            storage_table.add_row(label, str(len(files)), size_str, alert)
        else:
            storage_table.add_row(label, "[red]N/A[/red]", "Folder missing", "[red]ERROR[/red]")
            
    console.print(storage_table)
    console.print(f"\n[dim]Umbrales configurados: Logs: 100MB | Backups: 500MB | Staging: 1GB[/dim]\n")
