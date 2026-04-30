from pathlib import Path


DATA_KEYWORDS = [
    "data",
    "analytics",
    "etl",
    "airflow",
    "metabase",
    "pandas",
    "sqlalchemy",
    "postgres",
    "indicadores",
    "dashboard",
    "warehouse",
    "bi",
]


FILES_TO_CHECK = [
    "requirements.txt",
    "pyproject.toml",
    "README.md",
    "docker-compose.yml",
    "compose.yml",
    "hpd.config.json",
]


def score_data_repo(repo):
    score = 0
    name = repo["name"].lower()
    matched = []

    for keyword in DATA_KEYWORDS:
        if keyword in name:
            score += 2
            matched.append(keyword)

    path = Path(repo["path"])

    for filename in FILES_TO_CHECK:
        file_path = path / filename
        if not file_path.exists() or not file_path.is_file():
            continue

        try:
            content = file_path.read_text(errors="ignore").lower()
        except OSError:
            continue

        for keyword in DATA_KEYWORDS:
            if keyword in content:
                score += 1
                matched.append(keyword)

    return {
        **repo,
        "data_score": score,
        "matched_keywords": sorted(set(matched)),
        "likely_data_repo": score >= 3,
    }
