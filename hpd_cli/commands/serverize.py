from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class CheckStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    message: str
    project: str | None = None
    details: dict[str, Any] | None = None


PROJECTS: dict[str, dict[str, Any]] = {
    "hpd-cli-core": {
        "path": "/home/hpd/hpd-cli-core",
        "kind": "python-cli",
        "prod_files": ["pyproject.toml", ".github/workflows/tests.yml"],
        "ports": [],
    },
    "hpd-lab": {
        "path": "/home/hpd/hpd-lab",
        "kind": "python-lab",
        "prod_files": ["pyproject.toml", "README.md"],
        "ports": [],
    },
    "proyecto_anaconda": {
        "path": "/home/hpd/proyecto_anaconda",
        "kind": "docker-fastapi-airflow",
        "prod_files": ["docker-compose.prod.yml", "alembic.ini", "Makefile"],
        "compose_files": ["docker-compose.yml", "docker-compose.prod.yml"],
        "ports": [5433, 8081, 3000, 8000],
    },
    "dropshipping-ebay": {
        "path": "/home/hpd/dropshipping-ebay",
        "kind": "docker-fastapi",
        "prod_files": ["docker-compose.prod.yml", "alembic.ini"],
        "compose_files": ["docker-compose.yml", "docker-compose.prod.yml"],
        "ports": [8010],
    },
    "wordpress-docker": {
        "path": "/home/hpd/wordpress-docker",
        "kind": "docker-wordpress",
        "prod_files": ["docker-compose.yml"],
        "compose_files": ["docker-compose.yml"],
        "ports": [9001, 6379],
    },
    "Plataforma_deportiva": {
        "path": "/home/hpd/Plataforma_deportiva",
        "kind": "fastapi-render",
        "prod_files": ["render.yaml", "requirements.txt"],
        "ports": [],
    },
    "palabra-viva-factory": {
        "path": "/home/hpd/palabra-viva-factory",
        "kind": "python-video-factory",
        "prod_files": ["requirements.txt"],
        "ports": [],
    },
    "inversiones": {
        "path": "/home/hpd/inversiones",
        "kind": "python-node-trading",
        "prod_files": ["Makefile", "requirements.txt"],
        "ports": [],
    },
}

MIN_DISK_FREE_GB = 20
MIN_MEMORY_FREE_GB = 2


def run_command(
    args: list[str],
    cwd: Path | None = None,
    timeout: int = 15,
) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return completed.returncode, completed.stdout.strip(), completed.stderr.strip()
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired as exc:
        return 124, exc.stdout or "", exc.stderr or "Command timed out"


def bytes_to_gb(value: int) -> float:
    return round(value / (1024**3), 2)


def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex((host, port)) == 0


def get_compose_command() -> list[str] | None:
    if shutil.which("docker"):
        code, _, _ = run_command(["docker", "compose", "version"], timeout=8)
        if code == 0:
            return ["docker", "compose"]

    if shutil.which("docker-compose"):
        code, _, _ = run_command(["docker-compose", "version"], timeout=8)
        if code == 0:
            return ["docker-compose"]

    return None


def check_docker_available() -> CheckResult:
    if not shutil.which("docker"):
        return CheckResult(
            name="docker.installed",
            status=CheckStatus.FAIL,
            message="Docker no está instalado o no está disponible en PATH.",
        )

    code, stdout, stderr = run_command(["docker", "info"], timeout=10)
    if code != 0:
        return CheckResult(
            name="docker.running",
            status=CheckStatus.FAIL,
            message="Docker está instalado, pero el daemon no responde.",
            details={"stderr": stderr[-500:]},
        )

    return CheckResult(
        name="docker.running",
        status=CheckStatus.PASS,
        message="Docker está instalado y activo.",
        details={"info": stdout[:200]},
    )


def check_docker_compose_available() -> CheckResult:
    compose = get_compose_command()
    if compose is None:
        return CheckResult(
            name="docker.compose",
            status=CheckStatus.FAIL,
            message="No se encontró Docker Compose compatible.",
        )

    code, stdout, stderr = run_command([*compose, "version"], timeout=8)
    if code != 0:
        return CheckResult(
            name="docker.compose",
            status=CheckStatus.FAIL,
            message="Docker Compose existe, pero no responde correctamente.",
            details={"stderr": stderr[-500:]},
        )

    return CheckResult(
        name="docker.compose",
        status=CheckStatus.PASS,
        message=f"Docker Compose disponible: {' '.join(compose)}.",
        details={"version": stdout},
    )


def check_disk_space() -> CheckResult:
    usage = shutil.disk_usage("/")
    free_gb = bytes_to_gb(usage.free)

    if free_gb < MIN_DISK_FREE_GB:
        return CheckResult(
            name="host.disk_free",
            status=CheckStatus.FAIL,
            message=f"Espacio libre insuficiente: {free_gb} GB disponibles.",
            details={"minimum_gb": MIN_DISK_FREE_GB},
        )

    return CheckResult(
        name="host.disk_free",
        status=CheckStatus.PASS,
        message=f"Espacio libre suficiente: {free_gb} GB disponibles.",
        details={"minimum_gb": MIN_DISK_FREE_GB},
    )


def check_memory_available() -> CheckResult:
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return CheckResult(
            name="host.memory_available",
            status=CheckStatus.SKIP,
            message="No se pudo leer /proc/meminfo.",
        )

    available_kb: int | None = None
    for line in meminfo.read_text().splitlines():
        if line.startswith("MemAvailable:"):
            available_kb = int(line.split()[1])
            break

    if available_kb is None:
        return CheckResult(
            name="host.memory_available",
            status=CheckStatus.SKIP,
            message="No se encontró MemAvailable en /proc/meminfo.",
        )

    available_gb = round(available_kb / 1024 / 1024, 2)

    if available_gb < MIN_MEMORY_FREE_GB:
        return CheckResult(
            name="host.memory_available",
            status=CheckStatus.WARN,
            message=f"Memoria disponible baja: {available_gb} GB.",
            details={"minimum_gb": MIN_MEMORY_FREE_GB},
        )

    return CheckResult(
        name="host.memory_available",
        status=CheckStatus.PASS,
        message=f"Memoria disponible suficiente: {available_gb} GB.",
        details={"minimum_gb": MIN_MEMORY_FREE_GB},
    )


def check_project_exists(project: str, root: Path) -> CheckResult:
    if not root.exists():
        return CheckResult(
            name="project.exists",
            project=project,
            status=CheckStatus.FAIL,
            message=f"No existe la ruta del proyecto: {root}",
        )

    return CheckResult(
        name="project.exists",
        project=project,
        status=CheckStatus.PASS,
        message=f"Proyecto encontrado: {root}",
    )


def check_git_status(project: str, root: Path) -> CheckResult:
    if not (root / ".git").exists():
        return CheckResult(
            name="git.repository",
            project=project,
            status=CheckStatus.WARN,
            message="El proyecto no parece ser un repositorio Git.",
        )

    code, stdout, stderr = run_command(["git", "status", "--porcelain"], cwd=root)
    if code != 0:
        return CheckResult(
            name="git.status",
            project=project,
            status=CheckStatus.WARN,
            message="No se pudo leer el estado Git.",
            details={"stderr": stderr[-500:]},
        )

    if stdout:
        return CheckResult(
            name="git.clean",
            project=project,
            status=CheckStatus.WARN,
            message="El working tree tiene cambios sin commit.",
            details={"changes": stdout.splitlines()[:20]},
        )

    return CheckResult(
        name="git.clean",
        project=project,
        status=CheckStatus.PASS,
        message="Working tree limpio.",
    )


def check_git_remote(project: str, root: Path) -> CheckResult:
    if not (root / ".git").exists():
        return CheckResult(
            name="git.remote",
            project=project,
            status=CheckStatus.SKIP,
            message="No aplica porque no hay repositorio Git.",
        )

    code, stdout, _ = run_command(["git", "remote", "-v"], cwd=root)
    if code != 0 or not stdout:
        return CheckResult(
            name="git.remote",
            project=project,
            status=CheckStatus.WARN,
            message="No hay remote Git configurado.",
        )

    return CheckResult(
        name="git.remote",
        project=project,
        status=CheckStatus.PASS,
        message="Remote Git configurado.",
    )


def check_env_not_tracked(project: str, root: Path) -> CheckResult:
    if not (root / ".git").exists():
        return CheckResult(
            name="security.env_not_tracked",
            project=project,
            status=CheckStatus.SKIP,
            message="No aplica porque no hay repositorio Git.",
        )

    code, stdout, stderr = run_command(
        ["git", "ls-files", ".env", "*.env", ".env.*"],
        cwd=root,
    )

    if code != 0:
        return CheckResult(
            name="security.env_not_tracked",
            project=project,
            status=CheckStatus.WARN,
            message="No se pudo verificar si hay archivos .env versionados.",
            details={"stderr": stderr[-500:]},
        )

    tracked = [
        item
        for item in stdout.splitlines()
        if item.strip()
        and not item.endswith(".example")
        and not item.endswith(".template")
        and not item.endswith(".sample")
    ]

    if tracked:
        return CheckResult(
            name="security.env_not_tracked",
            project=project,
            status=CheckStatus.FAIL,
            message="Hay archivos de entorno sensibles versionados.",
            details={"tracked_env_files": tracked},
        )

    return CheckResult(
        name="security.env_not_tracked",
        project=project,
        status=CheckStatus.PASS,
        message="No se detectaron archivos .env sensibles versionados.",
    )


def check_prod_files(project: str, root: Path, prod_files: list[str]) -> list[CheckResult]:
    results: list[CheckResult] = []

    for relative_file in prod_files:
        file_path = root / relative_file
        if file_path.exists():
            results.append(
                CheckResult(
                    name="project.prod_file",
                    project=project,
                    status=CheckStatus.PASS,
                    message=f"Archivo requerido encontrado: {relative_file}",
                )
            )
        else:
            results.append(
                CheckResult(
                    name="project.prod_file",
                    project=project,
                    status=CheckStatus.WARN,
                    message=f"Archivo recomendado no encontrado: {relative_file}",
                )
            )

    return results


def check_compose_config(
    project: str,
    root: Path,
    compose_files: list[str],
) -> list[CheckResult]:
    results: list[CheckResult] = []
    compose = get_compose_command()

    if not compose:
        return [
            CheckResult(
                name="docker.compose.config",
                project=project,
                status=CheckStatus.SKIP,
                message="No se valida Compose porque Docker Compose no está disponible.",
            )
        ]

    for relative_file in compose_files:
        compose_path = root / relative_file

        if not compose_path.exists():
            results.append(
                CheckResult(
                    name="docker.compose.config",
                    project=project,
                    status=CheckStatus.WARN,
                    message=f"No existe {relative_file}.",
                )
            )
            continue

        code, stdout, stderr = run_command(
            [*compose, "-f", relative_file, "config"],
            cwd=root,
            timeout=20,
        )

        if code != 0:
            results.append(
                CheckResult(
                    name="docker.compose.config",
                    project=project,
                    status=CheckStatus.FAIL,
                    message=f"Compose inválido: {relative_file}",
                    details={"stderr": stderr[-1000:]},
                )
            )
        else:
            results.append(
                CheckResult(
                    name="docker.compose.config",
                    project=project,
                    status=CheckStatus.PASS,
                    message=f"Compose válido: {relative_file}",
                    details={"bytes": len(stdout)},
                )
            )

    return results


def check_ports(project: str, ports: list[int]) -> list[CheckResult]:
    if not ports:
        return [
            CheckResult(
                name="network.ports",
                project=project,
                status=CheckStatus.SKIP,
                message="El proyecto no tiene puertos reservados en el registro HPD.",
            )
        ]

    results: list[CheckResult] = []
    for port in ports:
        try:
            in_use = is_port_open(port)
        except OSError as exc:
            results.append(
                CheckResult(
                    name="network.port_available",
                    project=project,
                    status=CheckStatus.SKIP,
                    message=f"No se pudo validar el puerto {port}: {exc}.",
                    details={"port": port},
                )
            )
            continue

        if in_use:
            results.append(
                CheckResult(
                    name="network.port_available",
                    project=project,
                    status=CheckStatus.WARN,
                    message=f"Puerto {port} está en uso localmente.",
                    details={"port": port},
                )
            )
        else:
            results.append(
                CheckResult(
                    name="network.port_available",
                    project=project,
                    status=CheckStatus.PASS,
                    message=f"Puerto {port} disponible localmente.",
                    details={"port": port},
                )
            )

    return results


def check_tests_present(project: str, root: Path) -> CheckResult:
    candidates = [
        root / "tests",
        root / "pytest.ini",
        root / "pyproject.toml",
        root / "package.json",
    ]

    if any(path.exists() for path in candidates):
        return CheckResult(
            name="quality.tests_present",
            project=project,
            status=CheckStatus.PASS,
            message="Se detectó estructura de pruebas o configuración de proyecto.",
        )

    return CheckResult(
        name="quality.tests_present",
        project=project,
        status=CheckStatus.WARN,
        message="No se detectó carpeta tests ni configuración clara de pruebas.",
    )


def check_backup_readiness(project: str, root: Path) -> CheckResult:
    candidates = [
        root / "scripts",
        root / "backup",
        root / "backups",
        root / "data" / "backups",
        root / "Makefile",
    ]

    if any(path.exists() for path in candidates):
        return CheckResult(
            name="ops.backup_readiness",
            project=project,
            status=CheckStatus.PASS,
            message="Se detectaron recursos potenciales de backup/operación.",
        )

    return CheckResult(
        name="ops.backup_readiness",
        project=project,
        status=CheckStatus.WARN,
        message="No se detectaron recursos claros de backup/operación.",
    )


def run_host_checks() -> list[CheckResult]:
    return [
        check_docker_available(),
        check_docker_compose_available(),
        check_disk_space(),
        check_memory_available(),
    ]


def run_project_checks(project: str, config: dict[str, Any]) -> list[CheckResult]:
    root = Path(config["path"]).expanduser()
    results: list[CheckResult] = []

    exists_result = check_project_exists(project, root)
    results.append(exists_result)

    if exists_result.status == CheckStatus.FAIL:
        return results

    results.append(check_git_status(project, root))
    results.append(check_git_remote(project, root))
    results.append(check_env_not_tracked(project, root))
    results.extend(check_prod_files(project, root, config.get("prod_files", [])))
    results.extend(check_compose_config(project, root, config.get("compose_files", [])))
    results.extend(check_ports(project, config.get("ports", [])))
    results.append(check_tests_present(project, root))
    results.append(check_backup_readiness(project, root))

    return results


def summarize(results: list[CheckResult], strict: bool = False) -> dict[str, Any]:
    counts = {status.value: 0 for status in CheckStatus}
    for result in results:
        counts[result.status.value] += 1

    hard_fail = counts["FAIL"] > 0
    strict_fail = strict and counts["WARN"] > 0

    return {
        "total": len(results),
        "pass": counts["PASS"],
        "warn": counts["WARN"],
        "fail": counts["FAIL"],
        "skip": counts["SKIP"],
        "strict": strict,
        "ok": not hard_fail and not strict_fail,
    }


def print_human_report(results: list[CheckResult], strict: bool = False) -> None:
    summary = summarize(results, strict=strict)

    print("")
    print("HPD Serverize Precheck")
    print("=" * 72)

    current_project: str | None = None

    for result in results:
        if result.project != current_project:
            current_project = result.project
            label = current_project or "host"
            print("")
            print(f"[{label}]")

        marker = {
            CheckStatus.PASS: "✅",
            CheckStatus.WARN: "⚠️ ",
            CheckStatus.FAIL: "❌",
            CheckStatus.SKIP: "⏭️ ",
        }[result.status]

        print(f"{marker} {result.status.value:<4} {result.name:<28} {result.message}")

    print("")
    print("-" * 72)
    print(
        "Resumen: "
        f"PASS={summary['pass']} "
        f"WARN={summary['warn']} "
        f"FAIL={summary['fail']} "
        f"SKIP={summary['skip']} "
        f"TOTAL={summary['total']}"
    )

    if summary["ok"]:
        print("Resultado: OK para continuar con preparación de producción.")
    else:
        print("Resultado: BLOQUEADO. Corrige FAIL/WARN según modo strict.")
    print("")


def select_projects(project: str | None) -> dict[str, dict[str, Any]]:
    if project in (None, "", "all"):
        return PROJECTS

    if project not in PROJECTS:
        available = ", ".join(sorted(PROJECTS))
        raise ValueError(f"Proyecto desconocido: {project}. Disponibles: {available}")

    return {project: PROJECTS[project]}


def run_precheck(
    project: str | None = None,
    json_output: bool = False,
    strict: bool = False,
) -> int:
    results: list[CheckResult] = []
    selected = select_projects(project)

    results.extend(run_host_checks())

    for project_name, project_config in selected.items():
        results.extend(run_project_checks(project_name, project_config))

    summary = summarize(results, strict=strict)

    if json_output:
        payload = {
            "summary": summary,
            "results": [asdict(result) for result in results],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_human_report(results, strict=strict)

    return 0 if summary["ok"] else 1


def register_serverize_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "serverize",
        help="Prepara y valida proyectos HPD antes de producción.",
    )
    parser.add_argument(
        "--precheck",
        action="store_true",
        help="Ejecuta validaciones sin modificar archivos ni servicios.",
    )
    parser.add_argument(
        "--project",
        default="all",
        help="Proyecto a validar. Usa 'all' para todo el ecosistema.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Salida JSON para automatización.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Trata WARN como bloqueo.",
    )
    parser.set_defaults(func=handle_serverize)


def handle_serverize(args: argparse.Namespace) -> int:
    if not args.precheck:
        print("Uso requerido: hpd system serverize --precheck")
        return 2

    try:
        return run_precheck(
            project=args.project,
            json_output=args.json,
            strict=args.strict,
        )
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2
