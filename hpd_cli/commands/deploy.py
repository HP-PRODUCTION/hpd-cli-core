import subprocess
from hpd_cli.config import ensure_config
from hpd_cli import logger

def setup_parser(subparsers):
    parser = subparsers.add_parser("deploy", help="Comandos de Despliegue")
    parser.add_argument("environment", choices=["local", "prod"], help="Entorno de despliegue")
    parser.add_argument("--down", action="store_true", help="Detener los contenedores")
    parser.set_defaults(func=execute)

def execute(args):
    ensure_config()
    
    if args.environment == "local":
        if args.down:
            logger.info("HPD Deploy: Deteniendo entorno local...")
            subprocess.run(["docker-compose", "down"])
            logger.success("Entorno local detenido.")
        else:
            logger.info("HPD Deploy: Levantando entorno local...")
            subprocess.run(["docker-compose", "up", "-d"])
            logger.success("Entorno local levantado exitosamente.")
    else:
        logger.warning(f"Despliegue para entorno '{args.environment}' no esta implementado todavia.")
