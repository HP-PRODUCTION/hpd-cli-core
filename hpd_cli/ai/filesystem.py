from pathlib import Path


PROJECT_MARKERS = (
    ".git",
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "hpd.config.json",
    "docker-compose.yml",
    "compose.yml",
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
    return any((path / marker).exists() for marker in PROJECT_MARKERS)


def project_info(path):
    markers = {marker: (path / marker).exists() for marker in PROJECT_MARKERS}
    return {
        "name": path.name,
        "path": str(path),
        "has_git": markers[".git"],
        "has_requirements": markers["requirements.txt"],
        "has_pyproject": markers["pyproject.toml"],
        "has_docker": markers["docker-compose.yml"] or markers["compose.yml"],
        "has_hpd_config": markers["hpd.config.json"],
    }


def scan_repos(base_path=".", depth=1, exclude=None):
    """Scan local project folders up to a bounded depth."""
    base = Path(base_path).expanduser().resolve()
    repos = []
    seen = set()
    exclude_terms = normalize_excludes(exclude)
    max_depth = max(0, int(depth))

    if not base.exists() or not base.is_dir():
        return repos

    def walk(current, current_depth):
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

    if max_depth == 0 and has_project_marker(base):
        repos.append(project_info(base))
    else:
        walk(base, 0)

    return repos
