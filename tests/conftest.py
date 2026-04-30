import pytest

# --- Fixtures for mocking system metrics ---

@pytest.fixture
def healthy_metrics():
    """System with no issues at all."""
    return {
        "host": {"name": "test-host", "os": "Linux", "uptime": "up 1 day"},
        "cpu": {"usage_pct": 25.0, "load_avg": (1.0, 0.8, 0.5)},
        "memory": {"ram_used_pct": 45.0, "ram_available_mb": 6000, "swap_used_pct": 5.0},
        "disk": {"/": {"used_pct": 40.0, "free_gb": 200}},
        "docker": {"running": True, "containers_total": 4, "containers_running": 4, "images": 6}
    }

@pytest.fixture
def critical_metrics():
    """System in terrible shape."""
    return {
        "host": {"name": "dying-host", "os": "Linux", "uptime": "up 90 days"},
        "cpu": {"usage_pct": 98.0, "load_avg": (24.0, 20.0, 18.0)},
        "memory": {"ram_used_pct": 95.0, "ram_available_mb": 200, "swap_used_pct": 80.0},
        "disk": {"/": {"used_pct": 95.0, "free_gb": 5}, "/var": {"used_pct": 92.0, "free_gb": 2}},
        "docker": {"running": False, "containers_total": 0, "containers_running": 0}
    }

@pytest.fixture
def warning_metrics():
    """System under moderate pressure."""
    return {
        "host": {"name": "busy-host", "os": "Linux", "uptime": "up 3 days"},
        "cpu": {"usage_pct": 75.0, "load_avg": (5.0, 4.0, 3.0)},
        "memory": {"ram_used_pct": 82.0, "ram_available_mb": 2000, "swap_used_pct": 30.0},
        "disk": {"/": {"used_pct": 60.0, "free_gb": 100}},
        "docker": {"running": True, "containers_total": 10, "containers_running": 8, "images": 12}
    }
