import os
import time
from hpd_cli import logger
from hpd_cli.config import load_config


def load_dotenv_files():
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    for env_file in (os.path.expanduser("~/.hpd/.env"), ".env"):
        if os.path.exists(env_file):
            load_dotenv(env_file)

class BaseProvider:
    def __init__(self, model_name=None):
        self.model_name = model_name

    def generate(self, prompt, context=None):
        raise NotImplementedError

    def health_check(self):
        raise NotImplementedError

class GeminiProvider(BaseProvider):
    def api_key(self):
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def generate(self, prompt, context=None):
        try:
            from google import genai
        except ImportError as exc:
            raise ImportError("Instala google-genai para usar Gemini: pip install google-genai") from exc

        api_key = self.api_key()
        if not api_key:
            raise ValueError("Falta GEMINI_API_KEY o GOOGLE_API_KEY")

        client = genai.Client(api_key=api_key)
        model_name = self.model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        response = client.models.generate_content(
            model=model_name,
            contents=full_prompt,
        )
        return response.text

    def health_check(self):
        return self.api_key() is not None

class OpenAIProvider(BaseProvider):
    def generate(self, prompt, context=None):
        import requests

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Falta OPENAI_API_KEY")

        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        model_name = self.model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})

        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model_name, "messages": messages},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"]

    def health_check(self):
        return os.getenv("OPENAI_API_KEY") is not None

class AnthropicProvider(BaseProvider):
    def generate(self, prompt, context=None):
        import requests

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Falta ANTHROPIC_API_KEY")

        model_name = self.model_name or os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": model_name,
                "max_tokens": 256,
                "messages": [{"role": "user", "content": full_prompt}],
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        return "".join(block.get("text", "") for block in payload.get("content", []) if block.get("type") == "text")

    def health_check(self):
        return os.getenv("ANTHROPIC_API_KEY") is not None

class CloudflareProvider(BaseProvider):
    def generate(self, prompt, context=None):
        import requests
        api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        if not api_token or not account_id:
            raise ValueError("Faltan credenciales de Cloudflare")

        # Gateway ID from config would be better, but using default for now
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/meta/llama-3-8b-instruct"
        headers = {"Authorization": f"Bearer {api_token}"}

        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        response = requests.post(url, headers=headers, json={"prompt": full_prompt})

        if response.status_code != 200:
            raise Exception(f"Cloudflare AI Error: {response.text}")

        return response.json()["result"]["response"]

    def health_check(self):
        return all([os.getenv("CLOUDFLARE_API_TOKEN"), os.getenv("CLOUDFLARE_ACCOUNT_ID")])

class DeepSeekProvider(BaseProvider):
    def generate(self, prompt, context=None):
        import requests

        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("Falta DEEPSEEK_API_KEY")

        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
        model_name = self.model_name or os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
        full_prompt = f"{context}\n\n{prompt}" if context else prompt

        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_name,
                "messages": [{"role": "user", "content": full_prompt}],
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"]

    def health_check(self):
        return os.getenv("DEEPSEEK_API_KEY") is not None

class OllamaProvider(BaseProvider):
    def generate(self, prompt, context=None):
        import requests
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model_name = self.model_name or os.getenv("OLLAMA_MODEL", "llama3.1:8b")

        full_prompt = f"{context}\n\n{prompt}" if context else prompt

        try:
            response = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": full_prompt,
                    "stream": False,
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            raise Exception(f"Ollama Error: {e}")

    def health_check(self):
        import requests
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except (requests.ConnectionError, requests.Timeout, Exception):
            return False

class PolicyEngine:
    def __init__(self, routing_rules=None, fallback_chain=None):
        default_rules = {
            "code_generate": ["openai", "anthropic", "gemini", "deepseek", "ollama", "cloudflare"],
            "architecture_review": ["anthropic", "openai", "gemini", "deepseek", "ollama"],
            "fast_lookup": ["ollama", "deepseek", "cloudflare", "gemini", "openai"],
            "default": ["gemini", "deepseek", "openai", "anthropic", "ollama", "cloudflare"]
        }
        self.routing_rules = routing_rules or default_rules
        if fallback_chain:
            self.routing_rules["default"] = fallback_chain

    def get_providers(self, task_type):
        return self.routing_rules.get(task_type, self.routing_rules["default"])

import json
from datetime import datetime

class UsageTracker:
    def __init__(self, log_file=None):
        if log_file is None:
            config = load_config()
            log_dir = config.get("directories", {}).get("logs", "data/logs") if config else "data/logs"
            log_file = os.path.join(log_dir, "ai_usage.jsonl")

        self.log_file = log_file
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def log_request(self, provider, task_type, latency, status, error=None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "task_type": task_type,
            "latency_ms": round(latency * 1000, 2),
            "status": status,
            "error": str(error) if error else None
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

class AIRouter:
    def __init__(self):
        load_dotenv_files()
        self.config = load_config()
        ai_config = self.config.get("ai", {})
        self.providers = {
            "gemini": GeminiProvider(),
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "cloudflare": CloudflareProvider(),
            "deepseek": DeepSeekProvider(),
            "ollama": OllamaProvider()
        }
        self.policy_engine = PolicyEngine(
            routing_rules=ai_config.get("routing_rules"),
            fallback_chain=ai_config.get("fallback_chain"),
        )
        self.tracker = UsageTracker()

    def generate_content(self, prompt, context=None, task_type="default", policy="balanced"):
        target_providers = self.policy_engine.get_providers(task_type)

        last_error = None
        for provider_name in target_providers:
            start_time = time.time()
            try:
                provider = self.providers.get(provider_name)
                if not provider:
                    continue

                if not provider.health_check():
                    continue

                logger.info(f"Ruteando a {provider_name} (Tarea: {task_type})...")
                response = provider.generate(prompt, context)

                latency = time.time() - start_time
                self.tracker.log_request(provider_name, task_type, latency, "SUCCESS")
                return response

            except Exception as e:
                latency = time.time() - start_time
                self.tracker.log_request(provider_name, task_type, latency, "FAILED", error=e)
                logger.warning(f"Fallo en proveedor {provider_name}: {e}")
                last_error = e
                continue

        raise Exception(f"Todos los proveedores fallaron o no están configurados. Último error: {last_error}")

    def get_status(self):
        status = {}
        for name, provider in self.providers.items():
            status[name] = "AVAILABLE" if provider.health_check() else "UNAVAILABLE"
        return status

    def get_metrics(self, days=7):
        """Calcula métricas básicas desde los logs"""
        if not os.path.exists(self.tracker.log_file):
            return None

        metrics = {}
        with open(self.tracker.log_file, "r") as f:
            for line in f:
                data = json.loads(line)
                p = data["provider"]
                if p not in metrics:
                    metrics[p] = {"requests": 0, "success": 0, "latencies": []}

                metrics[p]["requests"] += 1
                if data["status"] == "SUCCESS":
                    metrics[p]["success"] += 1
                metrics[p]["latencies"].append(data["latency_ms"])

        for p in metrics:
            m = metrics[p]
            m["avg_latency"] = round(sum(m["latencies"]) / len(m["latencies"]), 2) if m["latencies"] else 0
            m["success_rate"] = round((m["success"] / m["requests"]) * 100, 2) if m["requests"] else 0

        return metrics

# Singleton instance
_router_instance = None

def get_ai_router():
    global _router_instance
    if _router_instance is None:
        _router_instance = AIRouter()
    return _router_instance
