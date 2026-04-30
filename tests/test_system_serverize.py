from pathlib import Path
from hpd_cli.commands import serverize
from hpd_cli.commands.serverize import CheckStatus


def test_select_projects_single_project():
    selected = serverize.select_projects("hpd-cli-core")

    assert list(selected.keys()) == ["hpd-cli-core"]


def test_select_projects_all():
    selected = serverize.select_projects("all")

    assert "hpd-cli-core" in selected
    assert "proyecto_anaconda" in selected
    assert "dropshipping-ebay" in selected


def test_select_projects_unknown():
    try:
        serverize.select_projects("unknown-project")
    except ValueError as exc:
        assert "Proyecto desconocido" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_summarize_ok_without_fail_or_strict_warn():
    results = [
        serverize.CheckResult(
            name="sample.pass",
            status=CheckStatus.PASS,
            message="ok",
        ),
        serverize.CheckResult(
            name="sample.warn",
            status=CheckStatus.WARN,
            message="warn",
        ),
    ]

    summary = serverize.summarize(results, strict=False)

    assert summary["ok"] is True
    assert summary["pass"] == 1
    assert summary["warn"] == 1
    assert summary["fail"] == 0


def test_summarize_strict_blocks_warn():
    results = [
        serverize.CheckResult(
            name="sample.warn",
            status=CheckStatus.WARN,
            message="warn",
        )
    ]

    summary = serverize.summarize(results, strict=True)

    assert summary["ok"] is False


def test_summarize_fail_blocks():
    results = [
        serverize.CheckResult(
            name="sample.fail",
            status=CheckStatus.FAIL,
            message="fail",
        )
    ]

    summary = serverize.summarize(results, strict=False)

    assert summary["ok"] is False


def test_check_project_exists_pass(tmp_path: Path):
    result = serverize.check_project_exists("demo", tmp_path)

    assert result.status == CheckStatus.PASS


def test_check_project_exists_fail(tmp_path: Path):
    missing = tmp_path / "missing"

    result = serverize.check_project_exists("demo", missing)

    assert result.status == CheckStatus.FAIL
