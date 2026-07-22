import pytest
from hpd_cli.commands.secure import audit

def test_audit_finds_secrets(tmp_path):
    # Crear archivo .env temporal
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET=123")
    result = audit(str(tmp_path), json_output=True)
    assert "SECRET" in str(result)
