import os
import subprocess
from hpd_cli import logger

LAB_DIR = os.getenv("HPD_LAB_DIR", os.path.expanduser("~/hpd-lab"))

def setup_parser(subparsers):
    parser = subparsers.add_parser("lab", help="HPD Experimental Lab & R&D")
    lab_subparsers = parser.add_subparsers(dest="lab_command", help="Subcomandos de laboratorio")
    lab_subparsers.required = True

    lab_subparsers.add_parser("status", help="Estado del laboratorio y experimentos")

    bench_parser = lab_subparsers.add_parser("benchmark", help="Ejecutar benchmarks de IA")
    bench_parser.add_argument("provider", choices=["gemini", "openai", "ollama"], help="Proveedor a probar")

    sandbox_parser = lab_subparsers.add_parser("sandbox", help="Gestión del entorno sandbox")
    sandbox_parser.add_argument("action", choices=["reset", "init"], help="Acción a realizar")

    parser.set_defaults(func=execute)

def execute(args):
    if args.lab_command == "status":
        show_status()
    elif args.lab_command == "benchmark":
        run_benchmark(args.provider)
    elif args.lab_command == "sandbox":
        handle_sandbox(args.action)

def show_status():
    from rich.console import Console
    from rich.table import Table
    console = Console()

    console.print("\n[bold magenta]🧪 HPD Experimental Lab Status[/bold magenta]\n")

    # Check directory structure
    dirs = ["experiments", "benchmarks", "sandbox", "fixtures", "prototypes", "attack-sims"]
    table = Table(title="Estructura de R&D")
    table.add_column("Directorio")
    table.add_column("Estado")
    table.add_column("Archivos")

    for d in dirs:
        path = os.path.join(LAB_DIR, d)
        exists = os.path.exists(path)
        count = len(os.listdir(path)) if exists else 0
        status = "[green]OK[/green]" if exists else "[red]Missing[/red]"
        table.add_row(d, status, str(count))

    console.print(table)

def run_benchmark(provider):
    import time
    from hpd_cli.ai.providers import ask_provider
    logger.info(f"Iniciando benchmark para {provider}...")

    test_prompt = "Responde exactamente con la palabra 'HPD-BENCHMARK-OK' y nada más."
    start = time.time()
    try:
        res = ask_provider(provider, test_prompt)
        latency = time.time() - start
        success = "HPD-BENCHMARK-OK" in res
        status = "[green]SUCCESS[/green]" if success else "[red]FAILED[/red]"
        print(f" - Resultado: {status}")
        print(f" - Latencia: {latency:.2f}s")
        print(f" - Respuesta: {res[:50]}...")
    except Exception as e:
        logger.error(f"Error en benchmark: {e}")

def handle_sandbox(action):
    if action == "reset":
        logger.warning("Limpiando sandbox de experimentos...")
        sandbox_path = os.path.join(LAB_DIR, "sandbox")
        for f in os.listdir(sandbox_path):
            file_path = os.path.join(sandbox_path, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print(f"Sandbox {sandbox_path} reseteado.")
    elif action == "init":
        logger.info("Inicializando entorno de pruebas en sandbox...")
        sandbox_path = os.path.join(LAB_DIR, "sandbox")
        os.makedirs(sandbox_path, exist_ok=True)
        # Create some dummy files for testing ai patch
        with open(os.path.join(sandbox_path, "test_script.py"), "w") as f:
            f.write("def hello():\n    print('hello lab')\n")
        print("Entorno inicializado en sandbox/test_script.py")
