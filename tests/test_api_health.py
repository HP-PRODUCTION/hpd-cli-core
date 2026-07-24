"""Tests for the API health endpoint, rate limiter, and system checks."""
import os
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from hpd_cli.api.main import app, rate_limit, RATE_LIMIT_WINDOW, RATE_LIMIT_MAX

client = TestClient(app)


class TestRateLimiter:
    """Validate the rate limiter (Redis-backed with in-memory fallback)."""

    def test_allows_requests_under_limit(self):
        """Should allow requests up to the limit."""
        for _ in range(RATE_LIMIT_MAX):
            response = client.get("/api/system/health", headers={"X-HPD-Token": ""})
            assert response.status_code == 200

    def test_blocks_requests_over_limit(self):
        """Should return 429 when limit is exceeded."""
        for _ in range(RATE_LIMIT_MAX):
            client.get("/api/system/health", headers={"X-HPD-Token": ""})

        response = client.get("/api/system/health", headers={"X-HPD-Token": ""})
        assert response.status_code == 429
        assert "Demasiadas solicitudes" in response.json()["detail"]

    def test_resets_after_window_expires(self):
        """Should allow requests again after the window passes."""
        # Forzar limpieza del cache de rate limiting
        from hpd_cli.cache import cache
        cache.flush()

        for _ in range(RATE_LIMIT_MAX):
            client.get("/api/system/health", headers={"X-HPD-Token": ""})

        # Limpiar cache para simular nueva ventana
        cache.flush()

        response = client.get("/api/system/health", headers={"X-HPD-Token": ""})
        assert response.status_code == 200

        response = client.get("/api/system/health", headers={"X-HPD-Token": ""})
        assert response.status_code == 200


class TestHealthEndpoint:
    """Validate the /api/system/health endpoint response."""

    def setup_method(self):
        from hpd_cli.cache import cache
        cache.flush()

    def test_returns_expected_structure(self):
        response = client.get("/api/system/health", headers={"X-HPD-Token": ""})
        assert response.status_code == 200
        data = response.json()
        assert "hostPostgres" in data
        assert "dockerDaemon" in data
        assert "secureEnvPerms" in data
        assert "deepseekApiKeySet" in data
        assert "gitIgnoredSecrets" in data
        assert "localOllamaModel" in data

    @patch.dict("os.environ", {"DEEPSEEK_API_KEY": "test-key-123"}, clear=False)
    def test_deepseek_key_reports_available(self):
        """With DEEPSEEK_API_KEY set, should report True."""
        import importlib
        from hpd_cli.api import system_checks
        importlib.reload(system_checks)
        response = client.get("/api/system/health", headers={"X-HPD-Token": ""})
        data = response.json()
        assert data["deepseekApiKeySet"] is True

    def test_rejects_invalid_token(self):
        with patch.dict("os.environ", {"HPD_UI_TOKEN": "secret-token"}):
            response = client.get("/api/system/health", headers={"X-HPD-Token": "wrong-token"})
            assert response.status_code == 401


class TestMetricsEndpoint:
    """Validate the /metrics Prometheus endpoint."""

    def test_returns_prometheus_metrics(self):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        assert "hpd_http_requests_total" in response.text
        assert "hpd_health_checks_total" in response.text
        assert "hpd_http_request_duration_seconds" in response.text
        assert "hpd_active_requests" in response.text

    def test_metrics_contains_health_checks_counter(self):
        response = client.get("/metrics")
        assert "hpd_health_checks_total" in response.text
        for line in response.text.splitlines():
            if line.startswith("hpd_health_checks_total"):
                val = float(line.split()[-1])
                assert val >= 0


class TestAPIVersioning:
    """Tests for API versioning (/api/v1/...)"""

    def test_v1_version_endpoint(self):
        """GET /api/v1/version returns version info."""
        response = client.get("/api/v1/version", headers={"X-HPD-Token": ""})
        assert response.status_code == 200
        data = response.json()
        assert data["api"] == "v1"
        assert data["app"] == "HPD Control Plane"

    def test_v1_health_endpoint(self):
        """GET /api/v1/system/health returns health data."""
        response = client.get("/api/v1/system/health", headers={"X-HPD-Token": ""})
        assert response.status_code == 200
        data = response.json()
        assert "deepseekApiKeySet" in data
        assert "dockerDaemon" in data

    def test_legacy_health_still_works(self):
        """Old /api/system/health still works (backward compat)."""
        response = client.get("/api/system/health", headers={"X-HPD-Token": ""})
        assert response.status_code == 200
