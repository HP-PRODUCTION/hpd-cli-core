#!/usr/bin/env python3
# hpd_cli/commands/projects.py
# Comando para listar y analizar proyectos en la VPS

import os
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def list_projects(args):
    """Lista y analiza proyectos en el VPS."""
    console.print(Panel.fit("🔍 Explorando proyectos en el VPS...", style="bold cyan"))

    search_paths = ["/opt", "/var/www", "/home", "/srv", "/usr/local"]
    results = []

    for base_path in search_paths:
        if not os.path.exists(base_path):
            continue
        for root, dirs, files in os.walk(base_path, topdown=True, followlinks=False):
            depth = root.replace(base_path, "").count(os.sep)
            if depth > 3:
                continue

            project_type = None
            indicators = []
            if "package.json" in files:
                project_type = "Node.js"
                indicators.append("package.json")
            if "setup.py" in files or "pyproject.toml" in files:
                project_type = "Python"
                indicators.append("setup.py/pyproject")
            if "docker-compose.yml" in files or "docker-compose.yaml" in files:
                project_type = "Docker" if not project_type else f"{project_type}+Docker"
                indicators.append("docker-compose")
            if "wp-config.php" in files:
                project_type = "WordPress"
                indicators.append("wp-config.php")
            if "pom.xml" in files:
                project_type = "Java Maven"
                indicators.append("pom.xml")
            if "requirements.txt" in files:
                if not project_type:
                    project_type = "Python (requirements)"
                indicators.append("requirements.txt")
            if ".git" in dirs:
                indicators.append("git")

            if project_type:
                results.append({
                    "path": root,
                    "name": os.path.basename(root),
                    "type": project_type,
                    "indicators": ", ".join(indicators)
                })

    table = Table(title="📁 Proyectos detectados en la VPS")
    table.add_column("Nombre", style="cyan", no_wrap=True)
    table.add_column("Tipo", style="green")
    table.add_column("Indicadores", style="dim")
    table.add_column("Ruta", style="dim")

    for p in results:
        table.add_row(p["name"], p["type"], p["indicators"], p["path"])

    console.print(table)
    console.print(f"\n✅ Total: {len(results)} proyectos detectados.")

    cache_dir = os.path.expanduser("~/.hpd")
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, "projects_index.json")
    with open(cache_file, "w") as f:
        json.dump(results, f, indent=2)

    console.print(f"📦 Índice guardado en {cache_file}")
    return results

def setup_parser(subparsers):
    parser = subparsers.add_parser("projects", help="Listar y analizar proyectos en el VPS")
    parser.set_defaults(func=list_projects)
