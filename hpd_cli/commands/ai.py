import os
from hpd_cli.config import ensure_config
from hpd_cli import logger

def setup_parser(subparsers):
    parser = subparsers.add_parser("ai", help="Comandos de IA de HPD")
    ai_subparsers = parser.add_subparsers(dest="ai_command", help="Subcomandos de IA")
    ai_subparsers.required = True
    
    gen_parser = ai_subparsers.add_parser("generate", help="Generar codigo con IA")
    gen_parser.add_argument("type", choices=["module"], help="Tipo de componente a generar")
    gen_parser.add_argument("name", help="Nombre del componente")
    
    ask_parser = ai_subparsers.add_parser("ask", help="Preguntar al asistente de IA")
    ask_parser.add_argument("query", nargs="+", help="Tu pregunta para el AI")
    ask_parser.add_argument("--type", choices=["code_generate", "architecture_review", "fast_lookup"], default="default", help="Tipo de tarea para enrutamiento")

    ai_subparsers.add_parser("status", help="Ver estado del AI Router y proveedores")
    
    compare_parser = ai_subparsers.add_parser("compare", help="Comparar respuestas entre proveedores")
    compare_parser.add_argument("query", nargs="+", help="Tu pregunta para comparar")

    ai_subparsers.add_parser("doctor", help="Diagnóstico de conectividad con proveedores")
    
    parser.set_defaults(func=execute)

def execute(args):
    config = ensure_config()
    
    if args.ai_command == "generate":
        if args.type == "module":
            generate_module(args.name, config)
    elif args.ai_command == "ask":
        question = " ".join(args.query)
        ask_ai(question, config, task_type=getattr(args, "type", "default"))
    elif args.ai_command == "status":
        show_status()
    elif args.ai_command == "compare":
        question = " ".join(args.query)
        compare_providers(question, config)
    elif args.ai_command == "doctor":
        run_doctor()

def ask_ai(question, config, task_type="default"):
    logger.info(f"Analizando tu pregunta con HPD AI Router (Tarea: {task_type})...")
    try:
        from hpd_cli.ai_router import AIRouter
        from rich.markdown import Markdown
        from rich.console import Console

        router = AIRouter()
        
        # Inyectar un poco de contexto
        context = f"Eres el asistente HPD-CLI. El usuario trabaja en un proyecto llamado '{config.get('project_name')}'. Responde de forma concisa y profesional."
        
        response_text = router.generate_content(question, context=context, task_type=task_type)
        
        console = Console()
        console.print(Markdown(response_text))
    except Exception as e:
        logger.error(f"Error en AI Router: {e}")

def show_status():
    from hpd_cli.ai_router import AIRouter
    from rich.console import Console
    from rich.table import Table
    
    router = AIRouter()
    status = router.get_status()
    metrics = router.get_metrics()
    
    console = Console()
    table = Table(title="HPD AI Router Status & Metrics", header_style="bold cyan")
    table.add_column("Proveedor", style="magenta")
    table.add_column("Estado")
    table.add_column("Requests", justify="right")
    table.add_column("Success %", justify="right")
    table.add_column("Avg Latency (ms)", justify="right")
    
    for name, st in status.items():
        color = "green" if st == "AVAILABLE" else "red"
        m = metrics.get(name, {"requests": 0, "success_rate": 0, "avg_latency": 0}) if metrics else {"requests": 0, "success_rate": 0, "avg_latency": 0}
        
        table.add_row(
            name.capitalize(), 
            f"[{color}]{st}[/{color}]",
            str(m["requests"]),
            f"{m['success_rate']}%",
            f"{m['avg_latency']}ms"
        )
        
    console.print(table)
    
    if not metrics:
        console.print("[dim]No se detectaron métricas de uso aún.[/dim]")
    else:
        # Mostrar últimos errores
        show_recent_errors(console)

def show_recent_errors(console):
    from hpd_cli.ai_router import AIRouter
    import json
    import os
    
    router = AIRouter()
    log_file = router.tracker.log_file
    
    if not os.path.exists(log_file):
        return
        
    errors = []
    with open(log_file, "r") as f:
        lines = f.readlines()
        for line in reversed(lines):
            data = json.loads(line)
            if data["status"] == "FAILED":
                errors.append(data)
            if len(errors) >= 3:
                break
                
    if errors:
        console.print("\n[bold red]⚠️ Últimos Errores Detectados:[/bold red]")
        for err in errors:
            console.print(f"[red]• {err['timestamp']} [{err['provider']}]: {err['error']}[/red]")

def compare_providers(question, config):
    from hpd_cli.ai_router import AIRouter
    from rich.console import Console
    from rich.panel import Panel
    from rich.columns import Columns
    
    router = AIRouter()
    console = Console()
    
    console.print(f"\n[bold yellow]Comparando respuestas para:[/bold yellow] {question}\n")
    
    panels = []
    for name in ["gemini", "openai", "anthropic"]:
        try:
            provider = router.providers[name]
            if provider.health_check():
                res = provider.generate(question)
                panels.append(Panel(res, title=f"[bold]{name.capitalize()}[/bold]", width=60))
            else:
                panels.append(Panel("[red]Proveedor no disponible[/red]", title=name.capitalize(), width=60))
        except Exception as e:
            panels.append(Panel(f"[red]Error: {e}[/red]", title=name.capitalize(), width=60))
            
    console.print(Columns(panels))

def run_doctor():
    from hpd_cli.ai_router import AIRouter
    from rich.console import Console
    import os
    
    console = Console()
    console.print("\n[bold cyan]🩺 HPD AI Doctor - Diagnóstico[/bold cyan]\n")
    
    keys = {
        "GEMINI_API_KEY": "Google Gemini",
        "OPENAI_API_KEY": "OpenAI",
        "ANTHROPIC_API_KEY": "Anthropic"
    }
    
    for key, name in keys.items():
        val = os.getenv(key)
        status = "[green]✓ CONFIGURADA[/green]" if val else "[red]✗ NO DETECTADA[/red]"
        console.print(f"* {name}: {status}")
        
    console.print("\n[dim]Asegúrate de definir estas variables en tu entorno para habilitar todos los proveedores.[/dim]\n")

def generate_module(name, config):
    logger.info(f"HPD AI Engine: Generando modulo '{name}'...")
    module_dir = os.path.join(config["directories"]["modules"], name)
    
    if os.path.exists(module_dir):
        logger.warning(f"El modulo '{name}' ya existe.")
        return
        
    os.makedirs(module_dir)
    
    with open(os.path.join(module_dir, "__init__.py"), 'w') as f:
        f.write(f'"""Modulo {name}"""\n')
        
    with open(os.path.join(module_dir, "models.py"), 'w') as f:
        f.write(f'# Modelos para {name}\n')
        
    with open(os.path.join(module_dir, "services.py"), 'w') as f:
        f.write(f'# Servicios para {name}\n')

    logger.success(f"Modulo '{name}' generado exitosamente en {module_dir}/")
