import subprocess
from hpd_cli.config import ensure_config
from hpd_cli import logger

def setup_parser(subparsers):
    parser = subparsers.add_parser("db", help="Comandos de Base de Datos")
    db_subparsers = parser.add_subparsers(dest="db_command", help="Subcomandos de DB")
    db_subparsers.required = True
    
    migrate_parser = db_subparsers.add_parser("migrate", help="Aplicar migraciones")
    migrate_parser.add_argument("--downgrade", action="store_true", help="Revertir migracion")

    db_subparsers.add_parser("export-s3", help="Exportar datos a S3 para Snowflake")
    
    parser.set_defaults(func=execute)

def execute(args):
    ensure_config()
    
    if args.db_command == "migrate":
        if args.downgrade:
            logger.warning("HPD DB Engine: Revirtiendo migracion...")
            subprocess.run(["alembic", "downgrade", "-1"])
            logger.success("Migracion revertida.")
        else:
            logger.info("HPD DB Engine: Aplicando migraciones...")
            subprocess.run(["alembic", "upgrade", "head"])
            logger.success("Migraciones aplicadas.")
    elif args.db_command == "export-s3":
        logger.info("HPD DB Engine: Iniciando exportacion a S3/Local Staging...")
        from etl.migrate.postgres_to_s3 import migrate_to_s3
        migrate_to_s3()
        logger.success("Exportacion completada.")
