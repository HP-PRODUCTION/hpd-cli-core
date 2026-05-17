from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from rich.console import Console
from rich.table import Table

REPO_PATH = Path("/home/hpd/inversiones")
LOG_DIR = REPO_PATH / "logs"


def _project_python() -> str:
    candidates = [
        REPO_PATH / ".venv" / "bin" / "python",
        REPO_PATH / "venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return "python"


def _run(command: list[str]) -> int:
    result = subprocess.run(command, cwd=REPO_PATH, check=False)
    return result.returncode


def _tail_log(lines: int) -> str:
    log_files = sorted(
        LOG_DIR.glob("*.log"), key=lambda path: path.stat().st_mtime, reverse=True
    )
    if not log_files:
        return "No log files found."

    content = log_files[0].read_text(encoding="utf-8", errors="replace").splitlines()
    selected = content[-lines:]
    header = f"Showing {len(selected)} lines from {log_files[0].name}"
    return header + "\n" + "\n".join(selected)


def setup_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("inversiones", help="Operacion de inversiones")
    inversiones_subparsers = parser.add_subparsers(
        dest="inversiones_command", help="Subcomandos"
    )
    inversiones_subparsers.required = True

    doctor_parser = inversiones_subparsers.add_parser(
        "doctor", help="Diagnostico rapido del bot"
    )
    doctor_parser.set_defaults(func=doctor)

    test_parser = inversiones_subparsers.add_parser(
        "test", help="Ejecuta pruebas operativas del proyecto"
    )
    test_parser.set_defaults(func=run_tests)

    logs_parser = inversiones_subparsers.add_parser(
        "logs", help="Muestra las ultimas lineas de logs"
    )
    logs_parser.add_argument(
        "--lines", type=int, default=20, help="Cantidad de lineas a mostrar"
    )
    logs_parser.set_defaults(func=show_logs)


def doctor(args: argparse.Namespace) -> None:
    del args
    console = Console()
    console.print("\n[bold cyan]Inversiones Doctor[/bold cyan]\n")

    checks = [
        ("Repositorio", REPO_PATH.exists()),
        ("requirements.txt", (REPO_PATH / "requirements.txt").exists()),
        ("automation/local_bot.py", (REPO_PATH / "automation/local_bot.py").exists()),
        ("TASKLIST.md", (REPO_PATH / "TASKLIST.md").exists()),
    ]

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Check")
    table.add_column("Estado", justify="center")

    for name, ok in checks:
        table.add_row(name, "[green]OK[/green]" if ok else "[red]FALTA[/red]")

    env_table = Table(show_header=True, header_style="bold blue")
    env_table.add_column("Variable")
    env_table.add_column("Estado", justify="center")

    required_env = ["BOT_WEBHOOK_URL"]
    for key in required_env:
        value = os.getenv(key, "").strip()
        env_table.add_row(
            key, "[green]SET[/green]" if value else "[yellow]MISSING[/yellow]"
        )

    console.print(table)
    console.print()
    console.print(env_table)
    console.print()


def run_tests(args: argparse.Namespace) -> None:
    del args
    raise_code = _run([_project_python(), "-m", "pytest", "-q"])
    raise SystemExit(raise_code)


def show_logs(args: argparse.Namespace) -> None:
    console = Console()
    console.print(_tail_log(args.lines))
