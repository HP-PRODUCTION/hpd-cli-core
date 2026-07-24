# hpd_cli/commands/suggest.py
import json
from rich.console import Console
from hpd_cli.ai_router import get_ai_router
from hpd_cli.commands.diagnose import diagnose

console = Console()

def suggest(args):
    console.print("[bold cyan]🤖 Generando sugerencias inteligentes...[/bold cyan]")

    # Obtener diagnóstico en formato JSON
    # Para simplificar, ejecutamos diagnose y capturamos la salida (o reutilizamos lógica)
    # Aquí usamos una versión simplificada
    import psutil
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    docker_status = "OK"  # Simulado

    context = f"""
    Diagnóstico del sistema:
    - RAM: {mem.percent}% usado
    - Disco: {disk.percent}% usado
    - Docker: {docker_status}
    - Proyectos: (ejecuta 'hpd projects' para verlos)
    """

    router = get_ai_router()
    prompt = f"""
    Basado en el siguiente estado del sistema, sugiere acciones concretas para:
    1. Mejorar el rendimiento
    2. Liberar espacio en disco
    3. Optimizar el uso de recursos
    4. Acciones de mantenimiento recomendadas

    Contexto:
    {context}

    Devuelve una lista numerada de sugerencias prácticas.
    """
    response = router.generate_content(prompt, task_type="default")
    console.print(response)

def setup_parser(subparsers):
    parser = subparsers.add_parser("suggest", help="Sugerencias inteligentes para el sistema")
    parser.set_defaults(func=suggest)
