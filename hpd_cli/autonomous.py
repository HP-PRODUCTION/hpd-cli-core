#!/usr/bin/env python3
# hpd_cli/autonomous.py - Función de modo autónomo
import os
import json
import re
from rich.console import Console
from hpd_cli.commands.ai import ask_ai
from hpd_cli.commands.run import run_command
from hpd_cli.commands.projects import list_projects

console = Console()

def run_autonomous(args):
    """Modo autónomo: el asistente ejecuta tareas sin intervención."""
    if not args.query:
        console.print("[yellow]Modo autónomo: necesitas especificar una tarea.[/yellow]")
        return

    question = " ".join(args.query)

    # Actualizar índice si no existe
    index_file = os.path.expanduser("~/.hpd/projects_index.json")
    if not os.path.exists(index_file):
        console.print("[cyan]📁 Actualizando índice de proyectos...[/cyan]")
        list_projects(args)

    # Cargar el índice
    context = None
    if os.path.exists(index_file):
        try:
            with open(index_file, "r") as f:
                projects_data = json.load(f)
            context = "Contexto de proyectos en esta VPS:\n" + "\n".join([f"- {p['name']} ({p['type']}) en {p['path']}" for p in projects_data])
        except Exception as e:
            console.print(f"[red]Error al cargar índice: {e}[/red]")

    # Comandos especiales
    if any(kw in question.lower() for kw in ["ejecuta", "run", "comando"]):
        match = re.search(r'(ejecuta|run|comando)\s+(.+)', question, re.IGNORECASE)
        if match:
            command = match.group(2).strip()
            console.print(f"[bold cyan]⚡ Ejecutando comando:[/bold cyan] {command}")
            result = run_command(command)
            console.print(result)
            return
        else:
            console.print("[yellow]No pude extraer el comando. Usa: 'ejecuta <comando>'[/yellow]")
            return

    elif "diagnostica" in question.lower():
        console.print("[bold cyan]🩺 Ejecutando diagnóstico del sistema...[/bold cyan]")
        result = run_command("hpd system doctor")
        console.print(result)
        return

    elif "monitorea" in question.lower():
        console.print("[bold cyan]📊 Monitoreo del sistema:[/bold cyan]")
        result = run_command("docker ps --format 'table {{.Names}}\t{{.Status}}'")
        console.print(result)
        result2 = run_command("df -h / | tail -1")
        console.print(result2)
        return

    # Pregunta normal con contexto (si es sobre proyectos) o sin contexto
    if any(kw in question.lower() for kw in ["proyecto", "proyectos", "directorio", "directorios", "repositorio", "repo", "carpeta"]):
        ask_ai(question, config=None, provider="deepseek", context=context, task_type="default")
    else:
        ask_ai(question, config=None, provider="deepseek", context=None, task_type="default")
