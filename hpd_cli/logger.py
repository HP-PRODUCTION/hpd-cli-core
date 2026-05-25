import os
import datetime
import logging
from logging.handlers import RotatingFileHandler
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

_LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "SUCCESS": 20}
_console_level = _LEVELS.get(os.getenv("HPD_LOG_LEVEL", "INFO").upper(), 20)
_file_logger = None

def _get_file_logger():
    global _file_logger
    if _file_logger:
        return _file_logger

    from hpd_cli.config import load_config

    config = load_config().get("logging", {})
    log_file = os.path.join(LOGS_DIR, "hpd.log")
    handler = RotatingFileHandler(
        log_file,
        maxBytes=int(config.get("max_bytes", 1048576)),
        backupCount=int(config.get("backup_count", 5)),
    )
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S"))
    _file_logger = logging.getLogger("hpd_cli")
    _file_logger.setLevel(logging.DEBUG)
    _file_logger.handlers = [handler]
    _file_logger.propagate = False
    return _file_logger

def configure(level=None, quiet=False, verbose=False):
    global _console_level
    if quiet:
        _console_level = _LEVELS["ERROR"]
    elif verbose:
        _console_level = _LEVELS["DEBUG"]
    elif level:
        _console_level = _LEVELS.get(str(level).upper(), _console_level)

def _write_log(level, message):
    _get_file_logger().log(_LEVELS.get(level, logging.INFO), message)

def _should_print(level):
    return _LEVELS.get(level, 20) >= _console_level

def info(message):
    if _should_print("INFO"):
        console.print(f"[info]ℹ {message}[/info]")
    _write_log("INFO", message)

def success(message):
    if _should_print("SUCCESS"):
        console.print(f"[success]✔ {message}[/success]")
    _write_log("SUCCESS", message)

def warning(message):
    if _should_print("WARNING"):
        console.print(f"[warning]⚠ {message}[/warning]")
    _write_log("WARNING", message)

def error(message):
    if _should_print("ERROR"):
        console.print(f"[error]✖ {message}[/error]")
    _write_log("ERROR", message)

def debug(message):
    if _should_print("DEBUG"):
        console.print(f"[dim]· {message}[/dim]")
    _write_log("DEBUG", message)

def ask(question):
    return console.input(f"[highlight]? {question}[/highlight] ")
