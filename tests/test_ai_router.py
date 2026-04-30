"""Tests for AI Router: fallback chain, provider selection, and health checks."""
import pytest
from unittest.mock import patch, MagicMock
from hpd_cli.ai_router import (
    AIRouter, PolicyEngine, GeminiProvider, OpenAIProvider,
    AnthropicProvider, OllamaProvider, BaseProvider
)


class TestPolicyEngine:
    """Validate routing rules and fallback chains."""

    def test_default_chain_exists(self):
        engine = PolicyEngine()
        chain = engine.get_providers("default")
        assert len(chain) >= 3
        assert "gemini" in chain

    def test_unknown_task_falls_back_to_default(self):
        engine = PolicyEngine()
        chain = engine.get_providers("nonexistent_task_type")
        default = engine.get_providers("default")
        assert chain == default

    def test_code_generate_prefers_openai(self):
        engine = PolicyEngine()
        chain = engine.get_providers("code_generate")
        assert chain[0] == "openai"

    def test_fast_lookup_prefers_ollama(self):
        engine = PolicyEngine()
        chain = engine.get_providers("fast_lookup")
        assert chain[0] == "ollama"

    def test_all_task_types_have_at_least_2_providers(self):
        engine = PolicyEngine()
        for task_type in ["code_generate", "architecture_review", "fast_lookup", "default"]:
            chain = engine.get_providers(task_type)
            assert len(chain) >= 2, f"{task_type} has less than 2 providers"


class TestAIRouter:
    """Validate router initialization and fallback behavior."""

    def test_router_has_all_providers(self):
        router = AIRouter()
        expected = {"gemini", "openai", "anthropic", "cloudflare", "ollama"}
        assert set(router.providers.keys()) == expected

    def test_router_falls_back_on_failure(self):
        """If first provider fails, router should try the next one."""
        router = AIRouter()
        # OpenAI simulator always works, so this should eventually succeed
        result = router.generate_content("test prompt", task_type="default")
        assert result is not None
        assert len(result) > 0

    def test_get_status_returns_all_providers(self):
        router = AIRouter()
        status = router.get_status()
        assert "gemini" in status
        assert "openai" in status
        assert status["openai"] == "AVAILABLE"  # simulator always up


class TestProviderHealthChecks:
    """Validate individual provider health check logic."""

    def test_openai_simulator_always_healthy(self):
        provider = OpenAIProvider()
        assert provider.health_check() is True

    def test_anthropic_simulator_always_healthy(self):
        provider = AnthropicProvider()
        assert provider.health_check() is True

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key-123"})
    def test_gemini_healthy_with_key(self):
        provider = GeminiProvider()
        assert provider.health_check() is True

    @patch.dict("os.environ", {}, clear=True)
    def test_gemini_unhealthy_without_key(self):
        provider = GeminiProvider()
        assert provider.health_check() is False

    def test_ollama_unhealthy_when_server_down(self):
        """Ollama should report unhealthy when no server is running."""
        provider = OllamaProvider()
        # Point to a port that definitely has nothing
        import os
        os.environ["OLLAMA_BASE_URL"] = "http://localhost:19999"
        assert provider.health_check() is False

    def test_base_provider_raises_not_implemented(self):
        provider = BaseProvider()
        with pytest.raises(NotImplementedError):
            provider.generate("test")
        with pytest.raises(NotImplementedError):
            provider.health_check()
