import json
import subprocess
import sys


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "hpd_cli.cli", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_setup_help():
    result = run_cli("setup", "--help")
    assert result.returncode == 0
    assert "--check" in result.stdout


def test_system_doctor_json():
    result = run_cli("system", "doctor", "--json")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert "score" in payload
    assert "metrics" in payload


def test_ai_repo_scan_json():
    result = run_cli("ai", "repo", "scan", "--path", ".", "--depth", "0", "--json")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert "repos" in payload


def test_services_help():
    result = run_cli("services", "--help")
    assert result.returncode == 0
    assert "up" in result.stdout


def test_secure_audit_json():
    result = run_cli("secure", "audit", "--path", ".", "--json")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert "findings" in payload
