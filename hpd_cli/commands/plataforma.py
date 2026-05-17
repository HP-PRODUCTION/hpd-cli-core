from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path

from rich.console import Console
from rich.table import Table

REPO_PATH = Path("/home/hpd/Plataforma_deportiva")
LOG_DIR = REPO_PATH / "logs"
RENDER_FILE = REPO_PATH / "render.yaml"
DATABASE_FILE = REPO_PATH / "app" / "database.py"
SMOKE_SCRIPT = REPO_PATH / "scripts" / "smoke_post_deploy.py"
CUTOVER_SCRIPT = REPO_PATH / "scripts" / "cutover_sqlite_to_postgres.py"


def _default_base_url() -> str:
    return os.getenv(
        "PLATAFORMA_BASE_URL", "https://plataforma-deportiva-28vv.onrender.com"
    )


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


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _database_default_mode() -> str:
    content = _read_text(DATABASE_FILE)
    if (
        'ENVIRONMENT == "production" and not os.getenv("DATABASE_URL", "").strip()'
        in content
    ):
        return "production-requires-database-url"

    match = re.search(
        r'DATABASE_URL\s*=\s*os\.getenv\("DATABASE_URL",\s*"([^"]+)"\)',
        content,
    )
    if not match:
        return "unknown"
    default_url = match.group(1)
    if default_url.startswith("sqlite"):
        return "sqlite-fallback"
    return "external-db-default"


def _render_has_database_url() -> bool:
    return "- key: DATABASE_URL" in _read_text(RENDER_FILE)


def _render_has_database_binding() -> bool:
    content = _read_text(RENDER_FILE)
    return (
        "fromDatabase:" in content
        and "name: plataforma-deportiva-db" in content
        and "property: connectionString" in content
    )


def setup_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "plataforma", help="Operacion de Plataforma_deportiva"
    )
    plataforma_subparsers = parser.add_subparsers(
        dest="plataforma_command", help="Subcomandos"
    )
    plataforma_subparsers.required = True

    doctor_parser = plataforma_subparsers.add_parser(
        "doctor", help="Diagnostico rapido del servicio"
    )
    doctor_parser.set_defaults(func=doctor)

    test_parser = plataforma_subparsers.add_parser(
        "test", help="Ejecuta pytest del proyecto"
    )
    test_parser.set_defaults(func=run_tests)

    migrate_parser = plataforma_subparsers.add_parser(
        "migrate", help="Ejecuta alembic upgrade head"
    )
    migrate_parser.add_argument(
        "--adopt-existing",
        action="store_true",
        help="Hace 'alembic stamp head' antes de migrar para bases existentes sin historial",
    )
    migrate_parser.set_defaults(func=run_migrations)

    logs_parser = plataforma_subparsers.add_parser(
        "logs", help="Muestra las ultimas lineas de logs"
    )
    logs_parser.add_argument(
        "--lines", type=int, default=20, help="Cantidad de lineas a mostrar"
    )
    logs_parser.set_defaults(func=show_logs)

    persistency_parser = plataforma_subparsers.add_parser(
        "persistency-check",
        help="Verifica si la configuracion actual garantiza persistencia real",
    )
    persistency_parser.set_defaults(func=check_persistency)

    smoke_parser = plataforma_subparsers.add_parser(
        "smoke",
        help="Ejecuta smoke post deploy de Plataforma_deportiva",
    )
    smoke_parser.add_argument(
        "--base-url",
        default=_default_base_url(),
        help="URL base del servicio desplegado",
    )
    smoke_parser.add_argument(
        "--timeout",
        type=int,
        default=45,
        help="Timeout por request en segundos",
    )
    smoke_parser.add_argument(
        "--retries",
        type=int,
        default=4,
        help="Cantidad de reintentos para checks HTTP",
    )
    smoke_parser.add_argument(
        "--check-remote-integrations",
        action="store_true",
        help="Verifica conectividad remota real de integraciones",
    )
    smoke_parser.set_defaults(func=run_smoke)

    cutover_parser = plataforma_subparsers.add_parser(
        "cutover",
        help="Ejecuta migracion de datos SQLite -> PostgreSQL",
    )
    cutover_parser.add_argument(
        "--source-sqlite",
        default=str(REPO_PATH / "sports_app.db"),
        help="Ruta al archivo SQLite origen",
    )
    cutover_parser.add_argument(
        "--target-url",
        default=os.getenv("DATABASE_URL", ""),
        help="URL de base de datos destino",
    )
    cutover_parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica la migracion de datos (por defecto solo dry-run)",
    )
    cutover_parser.set_defaults(func=run_cutover)


def doctor(args: argparse.Namespace) -> None:
    del args
    console = Console()
    console.print("\n[bold cyan]Plataforma_deportiva Doctor[/bold cyan]\n")

    checks = [
        ("Repositorio", REPO_PATH.exists()),
        ("requirements.txt", (REPO_PATH / "requirements.txt").exists()),
        ("alembic.ini", (REPO_PATH / "alembic.ini").exists()),
        ("app/main.py", (REPO_PATH / "app/main.py").exists()),
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

    required_env = ["DATABASE_URL", "TELEGRAM_BOT_TOKEN", "TELEGRAM_ADMIN_CHAT_ID"]
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


def run_migrations(args: argparse.Namespace) -> None:
    if args.adopt_existing:
        stamp_code = _run([_project_python(), "-m", "alembic", "stamp", "head"])
        if stamp_code != 0:
            raise SystemExit(stamp_code)

    raise_code = _run([_project_python(), "-m", "alembic", "upgrade", "head"])
    raise SystemExit(raise_code)


def show_logs(args: argparse.Namespace) -> None:
    console = Console()
    console.print(_tail_log(args.lines))


def check_persistency(args: argparse.Namespace) -> None:
    del args
    console = Console()
    console.print("\n[bold cyan]Plataforma Persistency Check[/bold cyan]\n")

    current_env_url = os.getenv("DATABASE_URL", "").strip()
    default_mode = _database_default_mode()
    render_has_database_url = _render_has_database_url()
    render_has_database_binding = _render_has_database_binding()
    sqlite_file_exists = (REPO_PATH / "sports_app.db").exists()

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Check")
    table.add_column("Resultado")
    table.add_column("Detalle")

    table.add_row(
        "DATABASE_URL en entorno actual",
        "[green]SET[/green]" if current_env_url else "[yellow]MISSING[/yellow]",
        current_env_url or "No definida en el entorno actual",
    )
    table.add_row(
        "Fallback en app/database.py",
        (
            "[red]RIESGO[/red]"
            if default_mode == "sqlite-fallback"
            else "[green]OK[/green]"
        ),
        default_mode,
    )
    table.add_row(
        "render.yaml define DATABASE_URL",
        "[green]OK[/green]" if render_has_database_url else "[red]FALTA[/red]",
        (
            "Declarada en envVars"
            if render_has_database_url
            else "No aparece en render.yaml"
        ),
    )
    table.add_row(
        "render.yaml enlaza DB real",
        "[green]OK[/green]" if render_has_database_binding else "[red]FALTA[/red]",
        (
            "DATABASE_URL via fromDatabase"
            if render_has_database_binding
            else "Sin fromDatabase connectionString"
        ),
    )
    table.add_row(
        "Archivo SQLite local detectado",
        "[yellow]SI[/yellow]" if sqlite_file_exists else "[green]NO[/green]",
        "sports_app.db presente" if sqlite_file_exists else "Sin archivo SQLite local",
    )

    console.print(table)
    console.print()

    deployment_database_configured = (
        bool(current_env_url) or render_has_database_binding
    )
    if (
        not deployment_database_configured
        or default_mode == "sqlite-fallback"
        or not render_has_database_url
    ):
        console.print("[bold red]Resultado: persistencia NO garantizada[/bold red]")
        raise SystemExit(1)

    console.print("[bold green]Resultado: persistencia configurada[/bold green]")


def run_smoke(args: argparse.Namespace) -> None:
    if not SMOKE_SCRIPT.exists():
        raise SystemExit("Smoke script not found: scripts/smoke_post_deploy.py")

    command = [
        _project_python(),
        str(SMOKE_SCRIPT),
        "--base-url",
        args.base_url,
        "--timeout",
        str(args.timeout),
        "--retries",
        str(args.retries),
    ]

    if args.check_remote_integrations:
        command.append("--check-remote-integrations")

    raise_code = _run(command)
    raise SystemExit(raise_code)


def run_cutover(args: argparse.Namespace) -> None:
    if not CUTOVER_SCRIPT.exists():
        raise SystemExit(
            "Cutover script not found: scripts/cutover_sqlite_to_postgres.py"
        )

    command = [
        _project_python(),
        str(CUTOVER_SCRIPT),
        "--source-sqlite",
        args.source_sqlite,
    ]

    if args.target_url:
        command.extend(["--target-url", args.target_url])

    if args.apply:
        command.append("--apply")

    raise_code = _run(command)
    raise SystemExit(raise_code)
