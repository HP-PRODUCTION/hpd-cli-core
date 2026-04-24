import subprocess
from hpd_cli.config import ensure_config
from hpd_cli import logger

def setup_parser(subparsers):
    parser = subparsers.add_parser("docs", help="Comandos de Documentacion")
    docs_subparsers = parser.add_subparsers(dest="docs_command", help="Subcomandos de Docs")
    docs_subparsers.required = True
    
    docs_subparsers.add_parser("build", help="Construir la documentacion")
    
    parser.set_defaults(func=execute)

def execute(args):
    ensure_config()
    
    if args.docs_command == "build":
        logger.info("HPD Docs: Construyendo portal de documentacion...")
        try:
            # Asume que docusaurus u otra herramienta esta instalada
            subprocess.run(["npm", "run", "build"], cwd="portal")
            logger.success("Documentacion construida.")
        except FileNotFoundError:
            logger.error("No se pudo ejecutar la construccion en la carpeta 'portal'.")
