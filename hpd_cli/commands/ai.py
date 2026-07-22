import os
import json
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
    ask_parser.add_argument("-p", "--provider", default="deepseek", help="Proveedor de IA (deepseek, gemini, openai, anthropic, ollama, cloudflare)")
    ask_parser.add_argument("-c", "--context", choices=["none", "repo", "project", "fs"], default="none", help="Nivel de contexto a enviar")
    ask_parser.add_argument("--path", default=".", help="Directorio base para --context fs")
    ask_parser.add_argument("--depth", type=int, default=1, help="Profundidad de escaneo para --context fs")
    ask_parser.add_argument("--exclude", default="", help="Patrones separados por coma para excluir en --context fs")
    ask_parser.add_argument("--cache", action="store_true", help="Usar cache local para --context fs")
    ask_parser.add_argument("--type", choices=["code_generate", "architecture_review", "fast_lookup"], default="default", help="Tipo de tarea para enrutamiento (legacy)")

    ai_subparsers.add_parser("ls", help="Listar capacidades IA disponibles")

    repo_parser = ai_subparsers.add_parser("repo", help="Analisis local-aware de repositorios")
    repo_subparsers = repo_parser.add_subparsers(dest="repo_command", help="Subcomandos de repo IA")
    repo_subparsers.required = True

    scan_parser = repo_subparsers.add_parser("scan", help="Escanear proyectos locales")
    scan_parser.add_argument("--path", default=".", help="Directorio base a escanear")
    scan_parser.add_argument("--depth", type=int, default=1, help="Profundidad maxima de escaneo")
    scan_parser.add_argument("--exclude", default="", help="Patrones separados por coma para excluir")
    scan_parser.add_argument("--cache", action="store_true", help="Usar cache local del escaneo")
    scan_parser.add_argument("--json", action="store_true", help="Emitir salida JSON")

    analyze_parser = repo_subparsers.add_parser("analyze", help="Detectar repositorios de datos/analitica")
    analyze_parser.add_argument("--path", default=".", help="Directorio base a escanear")
    analyze_parser.add_argument("--depth", type=int, default=1, help="Profundidad maxima de escaneo")
    analyze_parser.add_argument("--exclude", default="", help="Patrones separados por coma para excluir")
    analyze_parser.add_argument("--cache", action="store_true", help="Usar cache local del escaneo")
    analyze_parser.add_argument("--json", action="store_true", help="Emitir salida JSON")

    patch_parser = ai_subparsers.add_parser("patch", help="Aplicar un parche inteligente a un archivo")
    patch_parser.add_argument("file", help="Archivo a modificar")
    patch_parser.add_argument("instruction", nargs="+", help="Instrucción de lo que quieres cambiar")

    ai_subparsers.add_parser("status", help="Ver estado del AI Router y proveedores")

    compare_parser = ai_subparsers.add_parser("compare", help="Comparar respuestas entre proveedores")
    compare_parser.add_argument("query", nargs="+", help="Tu pregunta para comparar")

    ai_subparsers.add_parser("doctor", help="Diagnóstico de conectividad con proveedores")

    chat_parser = ai_subparsers.add_parser("chat", help="Conversación natural con el asistente de IA")
    chat_parser.add_argument("query", nargs="+", help="Tu mensaje en lenguaje natural")
    chat_parser.add_argument("-c", "--context", choices=["none", "repo", "project", "fs"], default="repo", help="Nivel de contexto a enviar")
    chat_parser.add_argument("--path", default=".", help="Directorio base para --context fs")
    chat_parser.add_argument("--depth", type=int, default=1, help="Profundidad de escaneo para --context fs")
    chat_parser.add_argument("--exclude", default="", help="Patrones separados por coma para excluir en --context fs")
    chat_parser.add_argument("--cache", action="store_true", help="Usar cache local para --context fs")

    parser.set_defaults(func=execute)

def execute(args):
    config = ensure_config()

    if args.ai_command == "generate":
        if args.type == "module":
            generate_module(args.name, config)
    elif args.ai_command == "ask":
        question = " ".join(args.query)
        ask_ai(question, config,
               provider=getattr(args, "provider", "gemini_flash"),
               context_level=getattr(args, "context", "none"),
               fs_path=getattr(args, "path", "."),
               fs_depth=getattr(args, "depth", 1),
               fs_exclude=parse_excludes(getattr(args, "exclude", "")),
               fs_cache=getattr(args, "cache", False),
               task_type=getattr(args, "type", "default"))
    elif args.ai_command == "ls":
        list_ai_capabilities()
    elif args.ai_command == "repo":
        if args.repo_command == "scan":
            repo_scan(args.path, args.depth, parse_excludes(args.exclude), args.cache, args.json)
        elif args.repo_command == "analyze":
            repo_analyze(args.path, args.depth, parse_excludes(args.exclude), args.cache, args.json)
    elif args.ai_command == "patch":
        patch_file(args.file, args.instruction, config)
    elif args.ai_command == "status":
        show_status()
    elif args.ai_command == "compare":
        question = " ".join(args.query)
        compare_providers(question, config)
    elif args.ai_command == "doctor":
        run_doctor()
    elif args.ai_command == "chat":
        question = " ".join(args.query)
        ask_ai(question, config,
               provider="deepseek",
               context_level=getattr(args, "context", "repo"),
               fs_path=getattr(args, "path", "."),
               fs_depth=getattr(args, "depth", 1),
               fs_exclude=parse_excludes(getattr(args, "exclude", "")),
               fs_cache=getattr(args, "cache", False),
               task_type="default")

def list_ai_capabilities():
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="HPD AI Local-Aware", header_style="bold cyan")
    table.add_column("Comando", style="magenta")
    table.add_column("Proposito")

    table.add_row("hpd ai status", "Estado de proveedores y metricas")
    table.add_row("hpd ai doctor", "Diagnostico de credenciales, permisos y latencia")
    table.add_row("hpd ai repo scan", "Escanea proyectos locales con marcadores tecnicos")
    table.add_row("hpd ai repo analyze", "Detecta repositorios de datos/BI/ETL")
    table.add_row("hpd ai ask --context repo", "Habla con el asistente en lenguaje natural usando DeepSeek con contexto del repositorio")
    table.add_row("hpd ai ask --context project", "Usa el contexto del proyecto actual para responder preguntas y planificar cambios")
    table.add_row("hpd ai ask --context fs", "Pregunta al LLM con contexto del filesystem local")
    table.add_row("hpd ai patch", "Edicion asistida con diff y aprobacion manual")

    console.print(table)

def parse_excludes(value):
    if not value:
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]

def repo_scan(path, depth=1, exclude=None, use_cache=False, as_json=False):
    from rich.console import Console
    from rich.table import Table
    from hpd_cli.ai.context import build_filesystem_context

    ctx = build_filesystem_context(path, depth=depth, exclude=exclude, use_cache=use_cache)
    if as_json:
        print(json.dumps(ctx, indent=2, ensure_ascii=False))
        return

    console = Console()
    cache_note = " cache" if ctx.get("cache_hit") else ""
    table = Table(title=f"Repos encontrados en {ctx['base_path']} (depth={ctx['depth']}{cache_note})", header_style="bold cyan")
    table.add_column("Nombre", style="magenta")
    table.add_column("Path")
    table.add_column("Git")
    table.add_column("Python")
    table.add_column("Docker")
    table.add_column("Score", justify="right")

    for repo in ctx["repos"]:
        table.add_row(
            repo["name"],
            repo["path"],
            "yes" if repo["has_git"] else "no",
            "yes" if repo["has_pyproject"] or repo["has_requirements"] else "no",
            "yes" if repo["has_docker"] else "no",
            str(repo["data_score"]),
        )

    console.print(table)
    if not ctx["repos"]:
        console.print("[yellow]No se encontraron proyectos con marcadores reconocidos.[/yellow]")

def repo_analyze(path, depth=1, exclude=None, use_cache=False, as_json=False):
    from rich.console import Console
    from rich.table import Table
    from hpd_cli.ai.context import build_filesystem_context

    ctx = build_filesystem_context(path, depth=depth, exclude=exclude, use_cache=use_cache)
    if as_json:
        print(json.dumps({
            "base_path": ctx["base_path"],
            "depth": ctx["depth"],
            "exclude": ctx["exclude"],
            "cache_hit": ctx["cache_hit"],
            "data_repos": ctx["data_repos"],
        }, indent=2, ensure_ascii=False))
        return

    console = Console()
    cache_note = " cache" if ctx.get("cache_hit") else ""
    table = Table(title=f"Repos de analisis de datos detectados (depth={ctx['depth']}{cache_note})", header_style="bold green")
    table.add_column("Nombre", style="magenta")
    table.add_column("Score", justify="right")
    table.add_column("Keywords")
    table.add_column("Path")

    for repo in ctx["data_repos"]:
        table.add_row(
            repo["name"],
            str(repo["data_score"]),
            ", ".join(repo["matched_keywords"]) or "-",
            repo["path"],
        )

    console.print(table)
    if not ctx["data_repos"]:
        console.print("[yellow]No se detectaron repos de datos con score suficiente.[/yellow]")

def ask_ai(
    question,
    config,
    provider="deepseek",
    context_level="none",
    fs_path=".",
    fs_depth=1,
    fs_exclude=None,
    fs_cache=False,
    task_type="default",
):
    logger.info(f"Analizando tu pregunta con HPD AI (Proveedor: {provider}, Contexto: {context_level})...")
    try:
        from hpd_cli.ai.context import build_context
        from hpd_cli.ai.providers import ask_provider
        from rich.markdown import Markdown
        from rich.console import Console

        # Build Context
        context = build_context(
            context_level,
            fs_path=fs_path,
            fs_depth=fs_depth,
            fs_exclude=fs_exclude,
            fs_cache=fs_cache,
        )

        # Call AI
        response_text = ask_provider(provider, question, context=context)

        console = Console()
        console.print("\n" + "─" * 40)
        console.print(Markdown(response_text))
        console.print("─" * 40 + "\n")
    except Exception as e:
        logger.error(f"Error en AI Engine: {e}")

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
    for name in ["deepseek", "gemini", "openai", "anthropic"]:
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
    from rich.table import Table
    import os
    import time
    from dotenv import load_dotenv

    console = Console()
    console.print("\n[bold cyan]🩺 HPD AI Doctor - Diagnóstico Avanzado[/bold cyan]\n")

    env_file = os.path.expanduser("~/.hpd/.env")
    if os.path.exists(env_file):
        load_dotenv(env_file)

    router = AIRouter()

    # 1. Credenciales y Permisos
    table_keys = Table(title="1. Credenciales & Seguridad", header_style="bold magenta")
    table_keys.add_column("Variable", style="dim")
    table_keys.add_column("Estado")
    table_keys.add_column("Permisos (600)")

    keys = [
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "CLOUDFLARE_API_TOKEN",
        "DEEPSEEK_API_KEY",
    ]
    perms_ok = False
    if os.path.exists(env_file):
        mode = oct(os.stat(env_file).st_mode)[-3:]
        perms_ok = (mode == "600")

    for key in keys:
        val = os.getenv(key)
        status = "[green]✓ OK[/green]" if val else "[yellow]⚠ MISSING[/yellow]"
        table_keys.add_row(key, status, "[green]✓ OK[/green]" if perms_ok else "[red]✗ FAIL[/red]")

    console.print(table_keys)

    # 2. Conectividad y Latencia
    table_conn = Table(title="2. Proveedores & Latencia", header_style="bold green")
    table_conn.add_column("Proveedor")
    table_conn.add_column("Estado")
    table_conn.add_column("Latencia")
    table_conn.add_column("Detalle")

    for name, provider in router.providers.items():
        start = time.time()
        is_up, detail = health_check_provider(provider)
        latency = f"{(time.time() - start)*1000:.0f}ms" if is_up else "N/A"
        status = "[green]ONLINE[/green]" if is_up else "[red]OFFLINE[/red]"
        table_conn.add_row(name.capitalize(), status, latency, detail)

    console.print(table_conn)

    # 3. Fallback Chain
    console.print("\n[bold yellow]3. Fallback Chain (Default):[/bold yellow]")
    chain = router.policy_engine.get_providers("default")
    console.print(f" -> {' -> '.join(chain)}")

    console.print("\n[dim]Sugerencia: Usa 'hpd ai ask \"hola\" --provider ollama' para probar localmente.[/dim]\n")

def health_check_provider(provider):
    if not provider.health_check():
        return False, "Sin credenciales o servicio local no disponible"

    try:
        response = provider.generate("Respond with exactly: OK", context="")
        if response and "OK" in response.upper():
            return True, "Respuesta OK"
        if response:
            return True, "Conectado; respuesta inesperada"
        return False, "Respuesta vacia"
    except Exception as exc:
        detail = str(exc)
        if "401" in detail and "Unauthorized" in detail:
            return False, "Credencial invalida o sin permisos para este proveedor"
        if "402" in detail and "Payment Required" in detail:
            return False, "Cuenta sin saldo/facturacion para este proveedor"
        if "404" in detail and "api/generate" in detail:
            return False, "Servicio local responde, pero el modelo/configuracion no existe"
        return False, detail[:80]

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

def patch_file(filename, instruction_list, config):
    import difflib
    import shutil
    from hpd_cli.ai.providers import ask_provider
    from rich.console import Console
    from rich.syntax import Syntax

    instruction = " ".join(instruction_list)
    console = Console()

    if not os.path.exists(filename):
        logger.error(f"El archivo {filename} no existe.")
        return

    # Security: Denylist check
    denylist = [".env", "secrets", "key", "cert", "password", "token"]
    if any(bad in filename.lower() for bad in denylist):
        logger.error(f"SEGURIDAD: No se permite parchar archivos sensibles ({filename})")
        return

    try:
        with open(filename, "r") as f:
            original_content = f.read()
    except Exception as e:
        logger.error(f"No se pudo leer el archivo: {e}")
        return

    logger.info(f"Generando parche para {filename}...")

    prompt = f"""
Actúa como un asistente de edición de código experto.
Recibirás el contenido de un archivo y una instrucción.
Debes devolver el contenido COMPLETO del archivo modificado.
No incluyas explicaciones, solo el código.

ARCHIVO: {filename}
CONTENIDO ACTUAL:
{original_content}

INSTRUCCIÓN: {instruction}
"""

    # We use a reliable provider for patching
    new_content = ask_provider("gemini_flash", prompt, context="System: Eres un editor de archivos. Devuelve solo el contenido del archivo.")

    # Clean up markdown if the AI wrapped it in code blocks
    new_content = new_content.strip()
    if new_content.startswith("```"):
        lines = new_content.splitlines()
        # Remove first line if it's ```language
        if lines[0].startswith("```"): lines = lines[1:]
        # Remove last line if it's ```
        if lines and lines[-1].strip() == "```": lines = lines[:-1]
        new_content = "\n".join(lines)

    # Show Diff
    diff = difflib.unified_diff(
        original_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}"
    )

    diff_text = "".join(diff)
    if not diff_text:
        console.print("\n[yellow]No se detectaron cambios necesarios o el AI devolvió el mismo contenido.[/yellow]")
        return

    console.print("\n[bold yellow]Parche propuesto:[/bold yellow]")
    console.print(Syntax(diff_text, "diff", theme="monokai"))

    try:
        confirm = console.input("\n¿Deseas aplicar estos cambios? [y/N]: ")
    except EOFError:
        confirm = "n"

    if confirm.lower() == 'y':
        # Backup
        shutil.copy2(filename, f"{filename}.bak")

        with open(filename, "w") as f:
            f.write(new_content)

        logger.success(f"Cambios aplicados exitosamente. Respaldo creado en {filename}.bak")
    else:
        logger.info("Operación cancelada por el usuario.")
