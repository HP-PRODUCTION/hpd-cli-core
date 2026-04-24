import subprocess
from hpd_cli.config import ensure_config
from hpd_cli import logger

def setup_parser(subparsers):
    parser = subparsers.add_parser("repo", help="Comandos de Repositorio")
    repo_subparsers = parser.add_subparsers(dest="repo_command", help="Subcomandos de Repo")
    repo_subparsers.required = True
    
    repo_subparsers.add_parser("audit", help="Auditar repositorio (lint y seguridad)")
    
    parser.set_defaults(func=execute)

def execute(args):
    ensure_config()
    
    if args.repo_command == "audit":
        logger.info("HPD Repo: Iniciando auditoria de repositorio...")
        try:
            logger.info("--- Linting (flake8) ---")
            subprocess.run(["flake8", "."])
        except FileNotFoundError:
            logger.warning("flake8 no instalado o no encontrado.")
            
        try:
            logger.info("--- Auditoria de dependencias (pip-audit) ---")
            subprocess.run(["pip-audit"])
        except FileNotFoundError:
            logger.warning("pip-audit no instalado. Ignorando.")
        
        logger.success("Auditoria completada.")
