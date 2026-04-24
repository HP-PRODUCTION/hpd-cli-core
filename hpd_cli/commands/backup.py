import subprocess
import datetime
import os
import glob
from hpd_cli.config import load_config, ensure_config
from hpd_cli import logger

def setup_parser(subparsers):
    parser = subparsers.add_parser("backup", help="Comandos de Respaldo")
    backup_subparsers = parser.add_subparsers(dest="backup_command", help="Subcomandos de Backup")
    backup_subparsers.required = True
    
    run_parser = backup_subparsers.add_parser("run", help="Ejecutar respaldo de DB")
    run_parser.add_argument("--keep", type=int, default=5, help="Número de respaldos a mantener")
    
    parser.set_defaults(func=execute)

def execute(args):
    config = ensure_config()
    
    if args.backup_command == "run":
        run_backup(config, args.keep)

def run_backup(config, keep):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = config.get("directories", {}).get("backups", "data/backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    filename = f"hpd_backup_{timestamp}.sql.gz"
    filepath = os.path.join(backup_dir, filename)
    
    logger.info(f"HPD Backup: Iniciando respaldo real en {filepath}...")
    
    # Comandos para respaldo via Docker
    # Usamos pg_dump dentro del contenedor y pipe a gzip en el host
    try:
        db_name = os.getenv("DB_NAME", "etl_db")
        db_user = os.getenv("DB_USER", "etl_user")
        
        cmd = f"docker exec etl_postgres pg_dump -U {db_user} {db_name} | gzip > {filepath}"
        
        logger.info("Ejecutando volcado comprimido de PostgreSQL...")
        subprocess.run(cmd, shell=True, check=True)
        
        logger.success(f"Respaldo completado con éxito: {filename}")
        
        # Rotación de backups
        rotate_backups(backup_dir, keep)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Fallo al ejecutar el respaldo: {e}")
    except Exception as e:
        logger.error(f"Error inesperado: {e}")

def rotate_backups(backup_dir, keep):
    """Mantiene solo los últimos N archivos de respaldo."""
    files = glob.glob(os.path.join(backup_dir, "hpd_backup_*.sql.gz"))
    files.sort(key=os.path.getmtime)
    
    if len(files) > keep:
        to_delete = files[:-keep]
        for f in to_delete:
            os.remove(f)
            logger.info(f"Rotación: Eliminado respaldo antiguo {os.path.basename(f)}")
