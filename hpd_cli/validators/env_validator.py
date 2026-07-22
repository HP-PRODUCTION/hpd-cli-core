# hpd_cli/validators/env_validator.py
import os
import requests
from rich.console import Console
from rich.table import Table

console = Console()

def validate_deepseek():
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        return "❌ Faltante"
    try:
        # Hacer una petición simple de prueba
        headers = {"Authorization": f"Bearer {key}"}
        response = requests.get("https://api.deepseek.com/v1/models", headers=headers, timeout=5)
        if response.status_code == 200:
            return "✅ OK"
        else:
            return f"⚠️ Error {response.status_code}"
    except Exception as e:
        return f"❌ {str(e)}"

def main():
    table = Table(title="Validación de Entorno")
    table.add_column("Variable", style="cyan")
    table.add_column("Estado", style="green")
    table.add_row("DEEPSEEK_API_KEY", validate_deepseek())
    # Añadir más validaciones
    console.print(table)
