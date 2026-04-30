"""Tests for hpd system doctor: scoring, deductions, hints, and JSON output."""
import json
import pytest
from hpd_cli.commands.system import calculate_score, generate_hints, collect_metrics


class TestCalculateScore:
    """Validate that the health scoring engine produces correct results."""

    def test_healthy_system_scores_100(self, healthy_metrics):
        score, deductions = calculate_score(healthy_metrics)
        assert score == 100
        assert deductions == []

    def test_critical_system_scores_below_50(self, critical_metrics):
        score, deductions = calculate_score(critical_metrics)
        assert score < 50
        assert len(deductions) >= 3  # RAM, swap, disk, docker, cpu all hit

    def test_warning_system_scores_between_50_and_100(self, warning_metrics):
        score, deductions = calculate_score(warning_metrics)
        assert 50 <= score < 100
        assert len(deductions) >= 1

    def test_ram_above_90_deducts_15(self):
        metrics = {
            "cpu": {"usage_pct": 10, "load_avg": (0.5, 0.5, 0.5)},
            "memory": {"ram_used_pct": 95, "ram_available_mb": 500, "swap_used_pct": 0},
            "disk": {},
            "docker": {"running": True}
        }
        score, deductions = calculate_score(metrics)
        ram_deductions = [d for d in deductions if d["reason"] == "RAM usage > 90%"]
        assert len(ram_deductions) == 1
        assert ram_deductions[0]["points"] == 15

    def test_docker_down_deducts_20(self):
        metrics = {
            "cpu": {"usage_pct": 10, "load_avg": (0.5, 0.5, 0.5)},
            "memory": {"ram_used_pct": 30, "ram_available_mb": 8000, "swap_used_pct": 0},
            "disk": {},
            "docker": {"running": False}
        }
        score, deductions = calculate_score(metrics)
        assert score == 80  # only docker deduction
        docker_deductions = [d for d in deductions if d["section"] == "docker"]
        assert docker_deductions[0]["points"] == 20

    def test_multiple_disk_warnings_stack(self):
        metrics = {
            "cpu": {"usage_pct": 10, "load_avg": (0.5, 0.5, 0.5)},
            "memory": {"ram_used_pct": 30, "ram_available_mb": 8000, "swap_used_pct": 0},
            "disk": {
                "/": {"used_pct": 85, "free_gb": 50},
                "/var": {"used_pct": 92, "free_gb": 5}
            },
            "docker": {"running": True}
        }
        score, deductions = calculate_score(metrics)
        disk_deductions = [d for d in deductions if d["section"] == "disk"]
        assert len(disk_deductions) == 2  # one warning, one critical
        assert score == 80  # -5 for /root >80, -15 for /var >90

    def test_score_never_goes_below_zero(self):
        """Even with every possible deduction, score should be >= 0."""
        metrics = {
            "cpu": {"usage_pct": 99, "load_avg": (100.0, 90.0, 80.0)},
            "memory": {"ram_used_pct": 99, "ram_available_mb": 50, "swap_used_pct": 99},
            "disk": {"/": {"used_pct": 99, "free_gb": 0}},
            "docker": {"running": False}
        }
        score, _ = calculate_score(metrics)
        assert score >= 0


class TestGenerateHints:
    """Validate that fix hints are generated based on deductions."""

    def test_no_hints_for_healthy_system(self, healthy_metrics):
        _, deductions = calculate_score(healthy_metrics)
        hints = generate_hints(healthy_metrics, deductions)
        assert hints == []

    def test_memory_hint_when_ram_high(self):
        metrics = {
            "cpu": {"usage_pct": 10, "load_avg": (0.5, 0.5, 0.5)},
            "memory": {"ram_used_pct": 95, "ram_available_mb": 500, "swap_used_pct": 0},
            "disk": {},
            "docker": {"running": True}
        }
        _, deductions = calculate_score(metrics)
        hints = generate_hints(metrics, deductions)
        assert any("processes" in h for h in hints)

    def test_docker_hint_when_daemon_down(self):
        metrics = {
            "cpu": {"usage_pct": 10, "load_avg": (0.5, 0.5, 0.5)},
            "memory": {"ram_used_pct": 30, "ram_available_mb": 8000, "swap_used_pct": 0},
            "disk": {},
            "docker": {"running": False}
        }
        _, deductions = calculate_score(metrics)
        hints = generate_hints(metrics, deductions)
        assert any("Docker" in h or "docker" in h for h in hints)

    def test_cpu_hint_when_usage_high(self):
        metrics = {
            "cpu": {"usage_pct": 85, "load_avg": (0.5, 0.5, 0.5)},
            "memory": {"ram_used_pct": 30, "ram_available_mb": 8000, "swap_used_pct": 0},
            "disk": {},
            "docker": {"running": True}
        }
        hints = generate_hints(metrics, [])
        assert any("CPU" in h for h in hints)


class TestCollectMetrics:
    """Validate that collect_metrics returns the expected structure."""

    def test_returns_all_sections(self):
        metrics = collect_metrics(verbose=False)
        assert "host" in metrics
        assert "cpu" in metrics
        assert "memory" in metrics
        assert "disk" in metrics
        assert "docker" in metrics

    def test_cpu_has_required_fields(self):
        metrics = collect_metrics(verbose=False)
        assert "usage_pct" in metrics["cpu"]
        assert "load_avg" in metrics["cpu"]
        assert isinstance(metrics["cpu"]["load_avg"], tuple)

    def test_memory_has_required_fields(self):
        metrics = collect_metrics(verbose=False)
        assert "ram_used_pct" in metrics["memory"]
        assert "ram_available_mb" in metrics["memory"]
        assert "swap_used_pct" in metrics["memory"]
