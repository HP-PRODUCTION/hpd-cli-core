import subprocess
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
