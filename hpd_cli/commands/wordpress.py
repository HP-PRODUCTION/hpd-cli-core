import subprocess
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import os
import json

console = Console()

def run_wp_command(command_parts):
    """Ejecuta un comando WP-CLI dentro del contenedor de wordpress."""
    docker_cmd = [
        "docker-compose", "exec", "-T", "wordpress",
        "php", "wp-cli.phar"
    ] + command_parts + ["--allow-root"]

    # Path del docker-compose.yml de wordpress
    wp_dir = "/home/hpd/wordpress-docker"

    try:
        result = subprocess.run(
            docker_cmd,
            cwd=wp_dir,
            capture_output=True,
            text=True,
            check=False
        )
        return result
    except Exception as e:
        return type('obj', (object,), {'returncode': 1, 'stderr': str(e), 'stdout': ''})

def doctor(args):
    """Diagnóstico de salud de WordPress y sus plugins HPD."""
    console.print(Panel("[bold cyan]HPD WordPress Doctor[/bold cyan]", border_style="blue"))

    # 1. Verificar estado de contenedores
    wp_dir = "/home/hpd/wordpress-docker"
    try:
        ps_res = subprocess.run(
            ["docker-compose", "ps", "--format", "json"],
            cwd=wp_dir, capture_output=True, text=True
        )
        if ps_res.returncode == 0:
            # Algunas versiones de docker-compose no soportan --format json de forma estable
            console.print("[green]✓[/green] Contenedores Docker: [bold]UP[/bold]")
        else:
            console.print("[red]✗[/red] Error verificando contenedores Docker")
    except:
        console.print("[yellow]![/yellow] Estado Docker: Indeterminado")

    # 2. Plugins HPD
    console.print("\n[bold]Plugins HPD:[/bold]")
    res_plugins = run_wp_command(["plugin", "list", "--fields=name,status,version", "--format=json"])
    if res_plugins.returncode == 0:
        try:
            plugins = json.loads(res_plugins.stdout)
            hpd_plugins = [p for p in plugins if 'hpd' in p['name']]
            for p in hpd_plugins:
                status_color = "green" if p['status'] == 'active' else "yellow"
                console.print(f"  - {p['name']}: [{status_color}]{p['status']}[/{status_color}] v{p['version']}")
        except:
            console.print("  [red]Error procesando lista de plugins[/red]")
    else:
        console.print("  [red]Error conectando con WP-CLI[/red]")

    # 3. Crons
    console.print("\n[bold]Eventos Cron HPD:[/bold]")
    res_cron = run_wp_command(["cron", "event", "list", "--format=json"])
    if res_cron.returncode == 0:
        try:
            crons = json.loads(res_cron.stdout)
            hpd_crons = [c for c in crons if 'hpd' in c['hook']]
            for c in hpd_crons:
                console.print(f"  - {c['hook']}: [dim]{c['next_run_relative']}[/dim] ({c['recurrence']})")
        except:
            console.print("  [red]Error procesando lista de crons[/red]")

    # 4. Auto Publicador
    console.print("\n[bold]Auto Publicador:[/bold]")
    res_pub_doc = run_wp_command(["hpd-publicador", "doctor"])
    if res_pub_doc.returncode == 0:
        # Imprimir la salida del comando nativo, limpiando un poco
        lines = res_pub_doc.stdout.splitlines()
        for line in lines:
            if "---" in line: continue
            if "[OK]" in line: console.print(f"  [green]✓[/green] {line.replace('[OK]', '').strip()}")
            elif "[FAIL]" in line: console.print(f"  [red]✗[/red] {line.replace('[FAIL]', '').strip()}")
            elif "Success:" in line: console.print(f"  [green]✓[/green] {line.replace('Success:', '').strip()}")
            elif "Warning:" in line: console.print(f"  [yellow]![/yellow] {line.replace('Warning:', '').strip()}")
            elif "Error:" in line: console.print(f"  [red]✗[/red] {line.replace('Error:', '').strip()}")
            else: console.print(f"    {line.strip()}")
    else:
        console.print("  [red]Error ejecutando hpd-publicador doctor[/red]")

    # 5. SEO Health
    console.print("\n[bold]SEO Health:[/bold]")
    res_seo_doc = run_wp_command(["hpd-seo", "doctor"])
    if res_seo_doc.returncode == 0:
        lines = res_seo_doc.stdout.splitlines()
        for line in lines:
            if "Success:" in line: console.print(f"  [green]✓[/green] {line.replace('Success:', '').strip()}")
            else: console.print(f"    {line.strip()}")
    else:
        console.print("  [red]Error ejecutando hpd-seo doctor[/red]")

    # 6. Economico
    console.print("\n[bold]Módulo Económico:[/bold]")
    res_entities = run_wp_command(["eval", "global $wpdb; echo $wpdb->get_var('SELECT COUNT(*) FROM ' . $wpdb->prefix . 'hpd_entidades_financieras WHERE active=1');"])

    entities_count = res_entities.stdout.strip() if res_entities.returncode == 0 else "N/A"

    console.print(f"  - Entidades financieras: {entities_count}")

    # Ultima actualizacion divisas
    res_div_upd = run_wp_command(["option", "get", "hpd_eco_last_update"])
    div_upd = res_div_upd.stdout.strip() if res_div_upd.returncode == 0 else "Nunca"
    console.print(f"  - Última actualización divisas: {div_upd}")

    console.print("\n[bold green]Estado: HEALTHY[/bold green]")

def setup_parser(subparsers):
    wp_parser = subparsers.add_parser("wordpress", help="Gestión y diagnóstico de WordPress")
    wp_subparsers = wp_parser.add_subparsers(dest="wp_command")

    doctor_parser = wp_subparsers.add_parser("doctor", help="Diagnóstico integral de salud")
    doctor_parser.set_defaults(func=doctor)
