from __future__ import annotations

import argparse

from hpd_cli.commands.serverize import run_precheck, select_projects


def setup_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "check",
        help="Ejecuta chequeos transversales del ecosistema HPD.",
    )
    parser.add_argument(
        "target",
        nargs="?",
        default="all",
        help="Proyecto a validar o 'all' para todo el ecosistema.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Salida JSON para automatizacion.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Trata WARN como bloqueo.",
    )
    parser.set_defaults(func=execute)


def execute(args: argparse.Namespace) -> int:
    try:
        select_projects(args.target)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2

    return run_precheck(
        project=args.target,
        json_output=args.json,
        strict=args.strict,
    )
