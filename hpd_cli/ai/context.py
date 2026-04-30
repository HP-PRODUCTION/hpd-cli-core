import os
import subprocess
import hashlib
import json
import time
from pathlib import Path

from hpd_cli.ai.filesystem import scan_repos
from hpd_cli.ai.repo_analyzer import score_data_repo


def get_cache_dir():
    return Path(os.getenv("HPD_CACHE_DIR", Path.home() / ".hpd" / "cache")).expanduser()


def get_cache_file(base_path, depth, exclude):
    payload = {
        "base_path": str(Path(base_path).expanduser().resolve()),
        "depth": int(depth),
        "exclude": sorted(exclude or []),
    }
    key = hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return get_cache_dir() / f"repo_scan_{key}.json"


def load_cached_context(base_path, depth, exclude, ttl_seconds):
    cache_file = get_cache_file(base_path, depth, exclude)
    if not cache_file.exists():
        return None

    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if time.time() - float(data.get("created_at", 0)) > ttl_seconds:
        return None

    return data.get("context")


def save_cached_context(base_path, depth, exclude, context):
    cache_file = get_cache_file(base_path, depth, exclude)
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(
            json.dumps({"created_at": time.time(), "context": context}, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def build_filesystem_context(base_path=".", depth=1, exclude=None, use_cache=False, cache_ttl=300):
    exclude = exclude or []

    if use_cache:
        cached = load_cached_context(base_path, depth, exclude, cache_ttl)
        if cached:
            cached["cache_hit"] = True
            return cached

    repos = scan_repos(base_path, depth=depth, exclude=exclude)
    analyzed = [score_data_repo(repo) for repo in repos]

    ctx = {
        "base_path": str(Path(base_path).expanduser().resolve()),
        "depth": int(depth),
        "exclude": list(exclude),
        "cache_hit": False,
        "repos": analyzed,
        "data_repos": [
            repo for repo in analyzed
            if repo["likely_data_repo"]
        ],
    }

    if use_cache:
        save_cached_context(base_path, depth, exclude, ctx)

    return ctx


def format_filesystem_context(base_path=".", depth=1, exclude=None, use_cache=False):
    ctx = build_filesystem_context(base_path, depth=depth, exclude=exclude, use_cache=use_cache)
    lines = [
        "Context Level: filesystem",
        f"Base Path: {ctx['base_path']}",
        f"Depth: {ctx['depth']}",
        f"Projects Found: {len(ctx['repos'])}",
        f"Likely Data Repos: {len(ctx['data_repos'])}",
    ]

    for repo in ctx["repos"][:30]:
        markers = []
        if repo["has_git"]:
            markers.append("git")
        if repo["has_pyproject"]:
            markers.append("pyproject")
        if repo["has_requirements"]:
            markers.append("requirements")
        if repo["has_docker"]:
            markers.append("docker")
        if repo["has_hpd_config"]:
            markers.append("hpd")

        keywords = ", ".join(repo["matched_keywords"]) or "-"
        lines.append(
            "- {name} | score={score} | data={data} | markers={markers} | keywords={keywords} | path={path}".format(
                name=repo["name"],
                score=repo["data_score"],
                data="yes" if repo["likely_data_repo"] else "no",
                markers=", ".join(markers) or "-",
                keywords=keywords,
                path=repo["path"],
            )
        )

    if len(ctx["repos"]) > 30:
        lines.append(f"... {len(ctx['repos']) - 30} projects omitted")

    return "\n".join(lines)

def build_context(context_type, fs_path=".", fs_depth=1, fs_exclude=None, fs_cache=False):
    if context_type == "none":
        return "Context: None\n"

    if context_type == "fs":
        context = [format_filesystem_context(fs_path, depth=fs_depth, exclude=fs_exclude, use_cache=fs_cache)]
    else:
        context = [f"Context Level: {context_type}"]

    if context_type in ["repo", "project"]:
        # Basic Repo info
        context.append(f"Current Directory: {os.getcwd()}")
        try:
            # Check if git is available and it's a repo
            if os.path.exists(".git"):
                branch = subprocess.check_output(["git", "branch", "--show-current"], stderr=subprocess.DEVNULL, text=True).strip()
                context.append(f"Git Branch: {branch}")
                status = subprocess.check_output(["git", "status", "--short"], stderr=subprocess.DEVNULL, text=True).strip()
                context.append(f"Git Status:\n{status}")
        except Exception:
            pass

        # Key files (Sanitized)
        key_files = ["README.md", "TASKLIST.md", "STATUS.md", "PUNTO_DE_ENCUENTRO.md", "project_status.md"]
        denylist = [".env", "secrets", "key", "cert", "password", "token"]

        for f in key_files:
            if os.path.exists(f):
                # Extra safety: skip if filename matches denylist
                if any(bad in f.lower() for bad in denylist):
                    continue
                try:
                    with open(f, "r") as file:
                        content = file.read()
                        # Limit content to first 2000 chars to avoid token blowup
                        if len(content) > 2000:
                            content = content[:2000] + "\n... [truncated]"
                        context.append(f"\n--- File: {f} ---\n{content}")
                except Exception:
                    pass

    if context_type == "project":
        config_path = os.path.expanduser("~/.hpd/config.yaml")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    context.append(f"\n--- Global Config (~/.hpd/config.yaml) ---\n{f.read()}")
            except Exception:
                pass

    # Base Instruction
    base_instruction = """
Eres HPD AI Assistant.
Responde como copiloto técnico del ecosistema HPD.
Prioriza seguridad, producción, Docker, PostgreSQL, Airflow, WordPress, CLI y automatización.
No inventes comandos destructivos.
Si una acción puede romper producción, sugiere dry-run primero.
"""
    context.insert(0, base_instruction)

    return "\n".join(context)
