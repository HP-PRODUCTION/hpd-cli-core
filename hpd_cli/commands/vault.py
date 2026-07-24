"""hpd vault — Gestión de secretos cifrados con GPG.

Cifra ~/.hpd/.env → ~/.hpd/.env.gpg usando tu clave GPG.
El config loader detecta .env.gpg y lo descifra automáticamente.
"""
import os
import subprocess
import sys
from pathlib import Path
from getpass import getpass
from rich.console import Console
from rich.table import Table

console = Console()
HPD_HOME = Path(os.environ.get("HPD_HOME", Path.home() / ".hpd"))
ENV_FILE = HPD_HOME / ".env"
ENV_GPG = HPD_HOME / ".env.gpg"


def _gpg_cmd(*args: str) -> list[str]:
    return ["gpg", "--batch", "--yes", *args]


def _gpg_available() -> bool:
    try:
        subprocess.run(["gpg", "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def _get_key_id() -> str | None:
    """Return the HPD GPG key ID, or None."""
    result = subprocess.run(
        _gpg_cmd("--list-secret-keys", "--keyid-format=long"),
        capture_output=True, text=True,
    )
    for line in result.stdout.splitlines():
        if "sec" in line or "ssb" in line:
            parts = line.split("/")
            if len(parts) > 1:
                return parts[1].split()[0]
    return None


def cmd_init(args):
    """Inicializa el vault GPG: crea clave si no existe, cifra .env."""
    if not _gpg_available():
        console.print("[red]❌ GPG no encontrado. Instala gnupg: apt install gnupg[/red]")
        return

    key_id = _get_key_id()
    if key_id:
        console.print(f"[green]✅ Clave GPG encontrada: {key_id}[/green]")
    else:
        console.print("[yellow]🔑 No hay clave GPG. Creando una automaticamente...[/yellow]")
        name = getattr(args, "name", "HPD Vault")
        email = getattr(args, "email", "hpd@localhost")
        batch = (
            f"Key-Type: RSA\nKey-Length: 4096\n"
            f"Name-Real: {name}\nName-Email: {email}\n"
            f"Expire-Date: 0\n%no-protection\n%commit\n"
        )
        proc = subprocess.run(
            ["gpg", "--batch", "--gen-key"],
            input=batch, capture_output=True, text=True,
        )
        if proc.returncode == 0:
            console.print("[green]✅ Clave GPG creada[/green]")
        else:
            console.print(f"[red]❌ Error: {proc.stderr}[/red]")
            return

    # Cifrar .env si existe
    if ENV_FILE.exists():
        cmd_encrypt(args)
    else:
        console.print("[yellow]⚠️  No hay ~/.hpd/.env para cifrar[/yellow]")


def cmd_encrypt(args):
    """Cifra ~/.hpd/.env → ~/.hpd/.env.gpg y elimina el plano."""
    if not _gpg_available():
        console.print("[red]❌ GPG no disponible[/red]")
        return
    if not ENV_FILE.exists():
        console.print("[yellow]⚠️  ~/.hpd/.env no existe[/yellow]")
        return

    key_id = _get_key_id()
    if not key_id:
        console.print("[red]❌ No hay clave GPG. Ejecuta 'hpd vault init' primero[/red]")
        return

    with open(ENV_FILE) as f:
        content = f.read()

    proc = subprocess.run(
        _gpg_cmd("--encrypt", "--recipient", key_id, "--output", str(ENV_GPG)),
        input=content, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        console.print(f"[red]❌ Error al cifrar: {proc.stderr}[/red]")
        return

    os.remove(ENV_FILE)
    ENV_GPG.chmod(0o600)
    console.print(f"[green]✅ .env cifrado → {ENV_GPG}[/green]")
    console.print("[yellow]⚠️  .env original eliminado. Usa 'hpd vault decrypt' para verlo[/yellow]")


def cmd_decrypt(args):
    """Descifra ~/.hpd/.env.gpg y muestra el contenido."""
    return _show_decrypted(raw=False)


def cmd_view(args):
    """Descifra y muestra valores ocultando parcialmente los secretos."""
    return _show_decrypted(raw=True)


def _show_decrypted(raw: bool = False):
    if not ENV_GPG.exists():
        console.print("[yellow]⚠️  No hay ~/.hpd/.env.gpg[/yellow]")
        return

    proc = subprocess.run(
        _gpg_cmd("--decrypt", str(ENV_GPG)),
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        console.print(f"[red]❌ Error al descifrar: {proc.stderr}[/red]")
        return

    content = proc.stdout.strip()
    if not content:
        console.print("[yellow]⚠️  Archivo vacío[/yellow]")
        return

    if raw:
        # Mostrar valores enmascarados
        table = Table(title="🔐 Secretos HPD (parcialmente ocultos)")
        table.add_column("Variable", style="cyan")
        table.add_column("Valor", style="yellow")
        for line in content.splitlines():
            if "=" in line and not line.startswith("#"):
                key, val = line.split("=", 1)
                if val and val.strip():
                    visible = val[:4] + "*" * (len(val) - 8) + val[-4:] if len(val) > 8 else "***"
                else:
                    visible = "(vacío)"
                table.add_row(key, visible)
        console.print(table)
    else:
        console.print(content)


# --- Auto-decrypt hook para config.py ---
def ensure_env_decrypted() -> bool:
    """Si existe .env.gpg y no .env, descifra automáticamente.
    Returns True si el archivo .env está disponible después."""
    if ENV_FILE.exists():
        return True
    if not ENV_GPG.exists():
        return False
    if not _gpg_available():
        return False

    proc = subprocess.run(
        _gpg_cmd("--decrypt", str(ENV_GPG)),
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return False

    # Escribir .env temporal con permisos seguros
    ENV_FILE.write_text(proc.stdout)
    ENV_FILE.chmod(0o600)
    return True


# --- Setup del parser ---
def setup_parser(subparsers):
    parser = subparsers.add_parser("vault", help="Gestión de secretos cifrados con GPG")
    vault_sub = parser.add_subparsers(dest="vault_command", required=True)

    p_init = vault_sub.add_parser("init", help="Inicializa el vault (crea clave GPG si no existe)")
    p_init.add_argument("--name", default="HPD Vault", help="Nombre real para la clave GPG")
    p_init.add_argument("--email", default="hpd@localhost", help="Email para la clave GPG")
    p_init.set_defaults(func=cmd_init)

    p_enc = vault_sub.add_parser("encrypt", help="Cifra ~/.hpd/.env → ~/.hpd/.env.gpg")
    p_enc.set_defaults(func=cmd_encrypt)

    p_dec = vault_sub.add_parser("decrypt", help="Descifra y muestra .env completo")
    p_dec.set_defaults(func=cmd_decrypt)

    p_view = vault_sub.add_parser("view", help="Descifra y muestra secretos ocultos")
    p_view.set_defaults(func=cmd_view)
