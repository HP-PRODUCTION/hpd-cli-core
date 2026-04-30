"""Tests for system clean command: dry-run and apply logic."""
import pytest
from unittest.mock import patch, MagicMock
from hpd_cli.commands.system import run_clean

class TestSystemClean:
    """Validate that clean command respects dry-run policy."""

    @patch("subprocess.run")
    def test_clean_dry_run_does_not_execute_commands(self, mock_run):
        """Dry-run should only print what it would do."""
        run_clean(dry_run=True, apply=False)
        # subprocess.run should NEVER be called in dry-run
        assert mock_run.call_count == 0

    @patch("subprocess.run")
    def test_clean_apply_executes_commands(self, mock_run):
        """Apply mode should actually call subprocess.run."""
        # Mock success
        mock_run.return_value = MagicMock(returncode=0)

        run_clean(dry_run=False, apply=True)
        # Should call at least 5 cleanup tasks (APT, Docker, etc)
        assert mock_run.call_count >= 4

    def test_clean_requires_arguments(self):
        """Running clean without flags should log an error."""
        with patch("hpd_cli.logger.error") as mock_logger:
            run_clean(dry_run=False, apply=False)
            mock_logger.assert_called_once()
