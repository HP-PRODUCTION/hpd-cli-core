from hpd_cli.ai.context import build_filesystem_context, format_filesystem_context
from hpd_cli.ai.filesystem import scan_repos
from hpd_cli.ai.repo_analyzer import score_data_repo


def test_scan_repos_detects_project_markers(tmp_path):
    repo = tmp_path / "proyecto_anaconda"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "requirements.txt").write_text("pandas\nsqlalchemy\n", encoding="utf-8")

    ignored = tmp_path / "Downloads"
    ignored.mkdir()

    repos = scan_repos(tmp_path)

    assert len(repos) == 1
    assert repos[0]["name"] == "proyecto_anaconda"
    assert repos[0]["has_git"] is True
    assert repos[0]["has_requirements"] is True


def test_score_data_repo_marks_likely_data_repo(tmp_path):
    repo_path = tmp_path / "etl_dashboard"
    repo_path.mkdir()
    (repo_path / "pyproject.toml").write_text(
        "[project]\ndependencies = ['pandas', 'postgres']\n",
        encoding="utf-8",
    )

    repo = {
        "name": repo_path.name,
        "path": str(repo_path),
        "has_git": False,
        "has_requirements": False,
        "has_pyproject": True,
        "has_docker": False,
        "has_hpd_config": False,
    }

    analyzed = score_data_repo(repo)

    assert analyzed["likely_data_repo"] is True
    assert analyzed["data_score"] >= 3
    assert "pandas" in analyzed["matched_keywords"]


def test_build_filesystem_context_groups_data_repos(tmp_path):
    data_repo = tmp_path / "analytics_stack"
    data_repo.mkdir()
    (data_repo / "pyproject.toml").write_text("[project]\nname = 'analytics-stack'\n", encoding="utf-8")
    (data_repo / "README.md").write_text("Airflow ETL dashboard con postgres", encoding="utf-8")

    app_repo = tmp_path / "website"
    app_repo.mkdir()
    (app_repo / "pyproject.toml").write_text("[project]\nname = 'website'\n", encoding="utf-8")

    ctx = build_filesystem_context(tmp_path)

    assert len(ctx["repos"]) == 2
    assert [repo["name"] for repo in ctx["data_repos"]] == ["analytics_stack"]


def test_format_filesystem_context_is_compact(tmp_path):
    repo = tmp_path / "bi_platform"
    repo.mkdir()
    (repo / "docker-compose.yml").write_text("services:\n  postgres:\n", encoding="utf-8")

    text = format_filesystem_context(tmp_path)

    assert "Context Level: filesystem" in text
    assert "bi_platform" in text
    assert "score=" in text


def test_scan_repos_supports_depth(tmp_path):
    nested = tmp_path / "apps" / "analytics_app"
    nested.mkdir(parents=True)
    (nested / "pyproject.toml").write_text("[project]\nname = 'analytics-app'\n", encoding="utf-8")

    assert scan_repos(tmp_path, depth=1) == []

    repos = scan_repos(tmp_path, depth=2)
    assert [repo["name"] for repo in repos] == ["analytics_app"]


def test_scan_repos_supports_exclude(tmp_path):
    backup_repo = tmp_path / "respaldo_repo"
    backup_repo.mkdir()
    (backup_repo / "pyproject.toml").write_text("[project]\nname = 'backup'\n", encoding="utf-8")

    normal_repo = tmp_path / "analytics_repo"
    normal_repo.mkdir()
    (normal_repo / "pyproject.toml").write_text("[project]\nname = 'analytics'\n", encoding="utf-8")

    repos = scan_repos(tmp_path, depth=1, exclude=["analytics"])

    assert repos == []


def test_build_filesystem_context_cache(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    monkeypatch.setenv("HPD_CACHE_DIR", str(cache_dir))

    repo = tmp_path / "etl_repo"
    repo.mkdir()
    (repo / "pyproject.toml").write_text("[project]\nname = 'etl-repo'\n", encoding="utf-8")

    first = build_filesystem_context(tmp_path, use_cache=True)
    second = build_filesystem_context(tmp_path, use_cache=True)

    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert second["repos"][0]["name"] == "etl_repo"
