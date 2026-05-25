import os
import stat
import subprocess
from pathlib import Path

from rich.console import Console
from rich.table import Table

from hpd_cli import logger


SECRET_PATTERNS = (
    "api_key",
    "secret",
    "token",
    "password",
    "private_key",
)


def setup_parser(subparsers):
    parser = subparsers.add_parser("secure", help="Auditoria de seguridad HPD")
    secure_subparsers = parser.add_subparsers(dest="secure_command", help="Subcomandos de seguridad")
    secure_subparsers.required = True

    audit = secure_subparsers.add_parser("audit", help="Auditar secretos, permisos y superficie local")
    audit.add_argument("--path", default=".", help="Ruta del proyecto a auditar")
    audit.add_argument("--json", action="store_true", help="Salida JSON")
    parser.set_defaults(func=execute)


def execute(args):
    if args.secure_command == "audit":
        run_audit(args.path, as_json=args.json)


def run_audit(path=".", as_json=False):
    import json

    findings = []
    root = Path(path).expanduser().resolve()
    env_path = Path.home() / ".hpd" / ".env"

    if env_path.exists():
        mode = stat.S_IMODE(env_path.stat().st_mode)
        if mode != 0o600:
            findings.append({"severity": "high", "check": "env_perms", "detail": f"{env_path} mode {oct(mode)}"})
    else:
        findings.append({"severity": "medium", "check": "env_exists", "detail": f"{env_path} no existe"})

    docker_sock = Path("/var/run/docker.sock")
    if docker_sock.exists():
        mode = stat.S_IMODE(docker_sock.stat().st_mode)
        findings.append({"severity": "info", "check": "docker_socket", "detail": f"{docker_sock} mode {oct(mode)}"})

    findings.extend(scan_sensitive_files(root))
    findings.extend(scan_git_tracked_sensitive_files(root))

    if as_json:
        print(json.dumps({"path": str(root), "findings": findings}, indent=2))
        return

    console = Console()
    table = Table(title=f"HPD Secure Audit: {root}", header_style="bold red")
    table.add_column("Severidad")
    table.add_column("Check")
    table.add_column("Detalle")

    for finding in findings:
        table.add_row(finding["severity"], finding["check"], finding["detail"])

    console.print(table)
    if not findings:
        logger.success("No se encontraron hallazgos de seguridad.")


def scan_sensitive_files(root):
    findings = []
    candidates = [".env", ".env.local", "id_rsa", "id_ed25519"]
    for candidate in candidates:
        for file_path in root.rglob(candidate):
            if any(part in {".git", "node_modules", ".venv", "venv"} for part in file_path.parts):
                continue
            findings.append({"severity": "high", "check": "sensitive_file", "detail": str(file_path)})
    return findings


def scan_git_tracked_sensitive_files(root):
    if not (root / ".git").exists():
        return []

    result = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return []

    findings = []
    for relpath in result.stdout.splitlines():
        lowered = relpath.lower()
        if any(pattern in lowered for pattern in SECRET_PATTERNS) or lowered.endswith(".env"):
            findings.append({"severity": "high", "check": "git_tracked_secret", "detail": relpath})
    return findings
