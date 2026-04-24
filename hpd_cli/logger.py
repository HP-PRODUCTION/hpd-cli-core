import os
import datetime
from rich.console import Console
from rich.theme import Theme

# Define custom themes for the HPD Platform
hpd_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "highlight": "bold magenta"
})

console = Console(theme=hpd_theme)

# Configurar directorio global de logs
GLOBAL_HPD_DIR = os.path.expanduser("~/.hpd")
LOGS_DIR = os.path.join(GLOBAL_HPD_DIR, "logs")

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR, exist_ok=True)

def _write_log(level, message):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.datetime.now().strftime("%H:%M:%S")
    log_file = os.path.join(LOGS_DIR, f"hpd_{date_str}.log")
    
    with open(log_file, "a") as f:
        f.write(f"[{time_str}] [{level}] {message}\n")

def info(message):
    console.print(f"[info]ℹ {message}[/info]")
    _write_log("INFO", message)

def success(message):
    console.print(f"[success]✔ {message}[/success]")
    _write_log("SUCCESS", message)

def warning(message):
    console.print(f"[warning]⚠ {message}[/warning]")
    _write_log("WARNING", message)

def error(message):
    console.print(f"[error]✖ {message}[/error]")
    _write_log("ERROR", message)

def debug(message):
    # Solo loguear a archivo, no a consola para no saturar
    _write_log("DEBUG", message)

def ask(question):
    return console.input(f"[highlight]? {question}[/highlight] ")
