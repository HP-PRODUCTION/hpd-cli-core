#!/usr/bin/env python3
# hpd_cli/commands/agent.py
# Modo agente: asistente interactivo

import sys
from rich.console import Console
from rich.prompt import Prompt
from hpd_cli.autonomous import run_autonomous

console = Console()

def agent_loop(args):
    console.print("[bold cyan]🤖 HPD AI Agent - Modo Interactivo[/bold cyan]")
    console.print("[dim]Escribe 'salir' o 'exit' para terminar.[/dim]")
    console.print("[dim]Ejemplos: '¿Qué proyectos tengo?', 'ejecuta ls -la', 'diagnostica'[/dim]\n")

    while True:
        try:
            question = Prompt.ask("[bold]>>[/bold]")
            if question.lower() in ["salir", "exit", "quit"]:
                console.print("👋 Hasta luego, capitán.")
                break
            if not question.strip():
                continue

            # Simular args para run_autonomous
            class Args:
                query = question.split()
            args = Args()
            run_autonomous(args)
        except KeyboardInterrupt:
            console.print("\n👋 Hasta luego, capitán.")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

def setup_parser(subparsers):
    parser = subparsers.add_parser("agent", help="Modo agente interactivo")
    parser.set_defaults(func=agent_loop)
