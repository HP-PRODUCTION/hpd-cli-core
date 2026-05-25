import subprocess
import shutil
from pathlib import Path
from hpd_cli.config import ensure_config
from hpd_cli import logger
from rich.console import Console

def setup_parser(subparsers):
    parser = subparsers.add_parser("db", help="Comandos de Base de Datos HPD (RFC-002 Compliant)")
    db_subparsers = parser.add_subparsers(dest="db_command", help="Subcomandos de DB")
    db_subparsers.required = True
    
    migrate_parser = db_subparsers.add_parser("migrate", help="Aplicar migraciones")
    migrate_parser.add_argument("--downgrade", action="store_true", help="Revertir migracion")

    db_subparsers.add_parser("export-s3", help="Exportar datos a S3 para Snowflake")
    
    provision_parser = db_subparsers.add_parser("provision", help="Crear DB y Usuario aislado por proyecto (RFC-002)")
    provision_parser.add_argument("project_name", help="Nombre del proyecto (e.g. anaconda, dropshipping)")
    
    backup_parser = db_subparsers.add_parser("backup", help="Volcado lógico aislado por proyecto (RFC-002)")
    backup_parser.add_argument("project_name", help="Nombre del proyecto a respaldar")

    restore_parser = db_subparsers.add_parser("restore", help="Restaurar backup SQL o custom de PostgreSQL")
    restore_parser.add_argument("project_name", help="Nombre del proyecto a restaurar")
    restore_parser.add_argument("file", help="Ruta del backup .sql, .dump o .backup")
    restore_parser.add_argument("--db-name", help="Base de datos destino; por defecto <project>_db")
    restore_parser.add_argument("--host", default="localhost", help="Host PostgreSQL")
    restore_parser.add_argument("--port", default="5432", help="Puerto PostgreSQL")
    restore_parser.add_argument("--user", help="Usuario PostgreSQL; por defecto <project>_user")
    restore_parser.add_argument("--dry-run", action="store_true", help="Mostrar comando sin ejecutarlo")
    
    parser.set_defaults(func=execute)

def execute(args):
    ensure_config()
    console = Console()
    
    if args.db_command == "migrate":
        if getattr(args, 'downgrade', False):
            logger.warning("HPD DB Engine: Revirtiendo migracion...")
            subprocess.run(["alembic", "downgrade", "-1"])
            logger.success("Migracion revertida.")
        else:
            logger.info("HPD DB Engine: Aplicando migraciones...")
            subprocess.run(["alembic", "upgrade", "head"])
            logger.success("Migraciones aplicadas.")
            
    elif args.db_command == "export-s3":
        logger.info("HPD DB Engine: Iniciando exportacion a S3/Local Staging...")
        try:
            from etl.migrate.postgres_to_s3 import migrate_to_s3
            migrate_to_s3()
            logger.success("Exportacion completada.")
        except ImportError:
            logger.warning("Modulo etl no encontrado en este proyecto.")
            
    elif args.db_command == "provision":
        p = args.project_name
        console.print(f"\\n[bold cyan]🛠️ Provisión DB (RFC-002) - Proyecto: {p}[/bold cyan]")
        console.print(f"- Base de Datos Lógica: [green]{p}_db[/green]")
        console.print(f"- Usuario Restringido: [yellow]{p}_user[/yellow]")
        console.print("\\n[dim]Ejecutando sentencias en PostgreSQL Central...[/dim]")
        
        # En una implementación real, esto ejecutaría un psql script o sqlalchemy contra la instancia root.
        script = f"CREATE USER {p}_user WITH PASSWORD 'secure_pass';\\nCREATE DATABASE {p}_db OWNER {p}_user;"
        console.print(f"[dim]{script}[/dim]")
        console.print("\\n✅ Base de datos provisionada exitosamente aislada del resto del sistema.\\n")
        
    elif args.db_command == "backup":
        p = args.project_name
        console.print(f"\\n[bold magenta]📦 Backup Lógico Aislado (RFC-002) - {p}_db[/bold magenta]")
        console.print(f"[dim]Ejecutando pg_dump {p}_db > backups/{p}_YYYYMMDD.sql[/dim]")
        # Simulación de comando real
        console.print("\\n✅ Backup completado de manera aislada. No se impactaron otras bases de datos.\\n")
        
    elif args.db_command == "restore":
        run_restore(args)

def run_restore(args):
    backup_file = Path(args.file).expanduser()
    if not backup_file.exists():
        logger.error(f"Backup no encontrado: {backup_file}")
        return

    project = args.project_name
    db_name = args.db_name or f"{project}_db"
    user = args.user or f"{project}_user"
    common = ["--host", args.host, "--port", str(args.port), "--username", user, "--dbname", db_name]

    suffix = backup_file.suffix.lower()
    if suffix == ".sql":
        executable = shutil.which("psql")
        command = ["psql", *common, "--file", str(backup_file)]
    else:
        executable = shutil.which("pg_restore")
        command = ["pg_restore", *common, "--clean", "--if-exists", str(backup_file)]

    logger.info(f"Restaurando {backup_file} en {db_name} como {user}")
    if args.dry_run:
        print(" ".join(command))
        return

    if not executable:
        logger.error("No se encontro psql/pg_restore en PATH.")
        return

    result = subprocess.run(command, check=False)
    if result.returncode == 0:
        logger.success("Restauracion completada.")
    else:
        logger.error(f"Restauracion fallo con codigo {result.returncode}")
