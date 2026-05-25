from pathlib import Path


PROJECT_MARKERS = (
    ".git",
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "hpd.config.json",
    ".env.example",
    "docker-compose.yml",
    "compose.yml",
    "Dockerfile",
    "wp-config.php",
)

DEFAULT_EXCLUDES = (
    ".cache",
    ".git",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "respaldo",
    "backup",
    "Downloads",
    "miniconda3",
    ".local",
)


def normalize_excludes(exclude=None):
    values = list(DEFAULT_EXCLUDES)
    if exclude:
        for item in exclude:
            values.extend(part.strip() for part in str(item).split(",") if part.strip())
    return tuple(dict.fromkeys(value.lower() for value in values))


def is_excluded(path, exclude_terms):
    name = path.name.lower()
    return any(term and term in name for term in exclude_terms)


def has_project_marker(path):
    if any((path / marker).exists() for marker in PROJECT_MARKERS):
        return True
    return any((path / marker).exists() for marker in ("dags", "notebooks", "migrations"))


def project_info(path):
    markers = {marker: (path / marker).exists() for marker in PROJECT_MARKERS}
    return {
        "name": path.name,
        "path": str(path),
        "has_git": markers[".git"],
        "has_requirements": markers["requirements.txt"],
        "has_pyproject": markers["pyproject.toml"],
        "has_docker": markers["docker-compose.yml"] or markers["compose.yml"] or markers["Dockerfile"],
        "has_hpd_config": markers["hpd.config.json"],
        "has_package_json": markers["package.json"],
        "has_env_example": markers[".env.example"],
        "has_wordpress": markers["wp-config.php"] or (path / "wp-content").exists(),
        "has_airflow": (path / "dags").exists() or any(path.glob("*_dag.py")),
        "has_sql": any(path.glob("*.sql")),
        "has_notebooks": any(path.glob("*.ipynb")) or (path / "notebooks").exists(),
    }


def scan_repos(base_path=".", depth=1, exclude=None, max_dirs=5000):
    """Scan local project folders up to a bounded depth."""
    base = Path(base_path).expanduser().resolve()
    repos = []
    seen = set()
    exclude_terms = normalize_excludes(exclude)
    max_depth = max(0, int(depth))
    visited = 0

    if not base.exists() or not base.is_dir():
        return repos

    def walk(current, current_depth):
        nonlocal visited
        visited += 1
        if visited > max_dirs:
            return

        if current_depth > max_depth:
            return

        if current != base and is_excluded(current, exclude_terms):
            return

        if current != base and has_project_marker(current):
            resolved = str(current)
            if resolved not in seen:
                seen.add(resolved)
                repos.append(project_info(current))

        if current_depth == max_depth:
            return

        try:
            children = sorted(current.iterdir(), key=lambda item: item.name.lower())
        except OSError:
            return

        for child in children:
            if child.is_dir():
                walk(child, current_depth + 1)

    if has_project_marker(base):
        repos.append(project_info(base))
        seen.add(str(base))

    if max_depth > 0:
        walk(base, 0)

    return repos
