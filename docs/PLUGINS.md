# Plugins HPD CLI

HPD carga plugins Python desde `~/.hpd/plugins`. Cada archivo `*.py` puede registrar comandos nuevos si expone una funcion `setup_parser(subparsers)`.

Ejemplo minimo:

```python
from hpd_cli import logger


def setup_parser(subparsers):
    parser = subparsers.add_parser("hello", help="Plugin de ejemplo")
    parser.set_defaults(func=run)


def run(args):
    logger.success("Plugin cargado correctamente")
```

Instalacion local:

```bash
mkdir -p ~/.hpd/plugins
cp hello.py ~/.hpd/plugins/
hpd hello
```

Convenciones recomendadas:

- No ejecutes trabajo pesado durante el import del plugin.
- Usa `parser.set_defaults(func=...)` para delegar la ejecucion.
- Lee configuracion desde `hpd_cli.config.load_config()` o `~/.hpd/.env`.
- Evita imprimir secretos o contenido de archivos sensibles.
