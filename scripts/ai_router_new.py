import os
import time
import json
import logging
import functools
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

# Intentar importar tenacity para retries
try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    # Definir un decorador dummy
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from hpd_cli import logger
from hpd_cli.config import load_config

# ============================================================
# Carga de variables de entorno
# ============================================================

def load_dotenv_files():
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    for env_file in (os.path.expanduser("~/.hpd/.env"), ".env"):
        if os.path.exists(env_file):
            load_dotenv(env_file)

# ============================================================
# Proveedores Base
# ============================================================

class BaseProvider:
    def __init__(self, model_name=None, timeout=60):
        self.model_name = model_name
        self.timeout = timeout
        self._name = self.__class__.__name__.replace("Provider", "").lower()

    def generate(self, prompt: str, context: Optional[str] = None) -> str:
        raise NotImplementedError

    def health_check(self) -> bool:
        raise NotImplementedError

    def get_name(self) -> str:
        return self._name


class GeminiProvider(BaseProvider):
    def __init__(self, model_name=None, timeout=60):
        super().__init__(model_name, timeout)
        self._name = "gemini"

    def api_key(self):
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def health_check(self):
        return self.api_key() is not None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10),
           retry=retry_if_exception_type((Exception,)))
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


class OpenAIProvider(BaseProvider):
    def __init__(self, model_name=None, timeout=60):
        super().__init__(model_name, timeout)
        self._name = "openai"

    def health_check(self):
        return os.getenv("OPENAI_API_KEY") is not None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10),
           retry=retry_if_exception_type((Exception,)))
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
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"]


class AnthropicProvider(BaseProvider):
    def __init__(self, model_name=None, timeout=60):
        super().__init__(model_name, timeout)
        self._name = "anthropic"

    def health_check(self):
        return os.getenv("ANTHROPIC_API_KEY") is not None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10),
           retry=retry_if_exception_type((Exception,)))
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
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": full_prompt}],
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return "".join(block.get("text", "") for block in payload.get("content", []) if block.get("type") == "text")


class DeepSeekProvider(BaseProvider):
    def __init__(self, model_name=None, timeout=60):
        super().__init__(model_name, timeout)
        self._name = "deepseek"

    def health_check(self):
        return os.getenv("DEEPSEEK_API_KEY") is not None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10),
           retry=retry_if_exception_type((Exception,)))
    def generate(self, prompt, context=None):
        import requests

        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("Falta DEEPSEEK_API_KEY")

        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
        model_name = self.model_name or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
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
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"]


class DeepSeekReasonerProvider(DeepSeekProvider):
    """Versión optimizada para tareas de razonamiento complejo (deepseek-reasoner)"""
    def __init__(self, timeout=90):
        super().__init__(model_name="deepseek-reasoner", timeout=timeout)
        self._name = "deepseek-reasoner"


class OllamaProvider(BaseProvider):
    def __init__(self, model_name=None, timeout=120):
        super().__init__(model_name, timeout)
        self._name = "ollama"

    def health_check(self):
        import requests
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except (requests.ConnectionError, requests.Timeout, Exception):
            return False

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=8),
           retry=retry_if_exception_type((Exception,)))
    def generate(self, prompt, context=None):
        import requests
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model_name = self.model_name or os.getenv("OLLAMA_MODEL", "llama3.1:8b")

        full_prompt = f"{context}\n\n{prompt}" if context else prompt

        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model_name,
                "prompt": full_prompt,
                "stream": False,
            },
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json().get("response", "")


# ============================================================
# Policy Engine Mejorado
# ============================================================

class PolicyEngine:
    def __init__(self, routing_rules=None, fallback_chain=None, default_chain=None):
        # Reglas por tipo de tarea
        default_rules = {
            "code_generate": ["deepseek", "openai", "anthropic", "gemini", "ollama"],
            "architecture_review": ["deepseek-reasoner", "deepseek", "anthropic", "openai", "gemini"],
            "fast_lookup": ["deepseek", "ollama", "gemini", "openai"],
            "analysis_deep": ["deepseek-reasoner", "anthropic", "deepseek", "openai"],
            "default": ["deepseek", "openai", "anthropic", "gemini", "ollama"]
        }
        self.routing_rules = routing_rules or default_rules
        # Cadena de fallback adicional
        self.fallback_chain = fallback_chain or ["deepseek", "openai", "gemini"]
        # Cadena por defecto
        self.default_chain = default_chain or self.routing_rules["default"]

    def get_providers(self, task_type: str) -> List[str]:
        """Devuelve la lista de proveedores para un tipo de tarea, priorizando los disponibles."""
        chain = self.routing_rules.get(task_type, self.default_chain)
        # Si se define cadena de fallback global, añadirla al final
        if self.fallback_chain:
            # Añadir solo proveedores que no estén ya en la cadena
            for p in self.fallback_chain:
                if p not in chain:
                    chain = list(chain) + [p]
        return chain


# ============================================================
# Usage Tracker Mejorado
# ============================================================

class UsageTracker:
    def __init__(self, log_file=None):
        if log_file is None:
            config = load_config()
            log_dir = config.get("directories", {}).get("logs", "data/logs") if config else "data/logs"
            log_file = os.path.join(log_dir, "ai_usage.jsonl")

        self.log_file = log_file
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def log_request(self, provider, task_type, latency, status, error=None, model=None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "model": model or "unknown",
            "task_type": task_type,
            "latency_ms": round(latency * 1000, 2),
            "status": status,
            "error": str(error) if error else None
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_metrics(self, days=7):
        """Calcula métricas agregadas de los últimos N días"""
        import time
        if not os.path.exists(self.log_file):
            return None

        cutoff = time.time() - (days * 86400)
        metrics = {}
        with open(self.log_file, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    ts = datetime.fromisoformat(data["timestamp"]).timestamp()
                    if ts < cutoff:
                        continue
                    p = data["provider"]
                    if p not in metrics:
                        metrics[p] = {"requests": 0, "success": 0, "latencies": [], "errors": 0}
                    metrics[p]["requests"] += 1
                    if data["status"] == "SUCCESS":
                        metrics[p]["success"] += 1
                    else:
                        metrics[p]["errors"] += 1
                    metrics[p]["latencies"].append(data["latency_ms"])
                except (KeyError, json.JSONDecodeError):
                    continue

        for p in metrics:
            m = metrics[p]
            m["avg_latency"] = round(sum(m["latencies"]) / len(m["latencies"]), 2) if m["latencies"] else 0
            m["success_rate"] = round((m["success"] / m["requests"]) * 100, 2) if m["requests"] else 0
            m.pop("latencies", None)  # Limpiar para no sobrecargar
        return metrics


# ============================================================
# Cache de Respuestas (TTL)
# ============================================================

class ResponseCache:
    def __init__(self, ttl_seconds=300, max_size=100):
        self.cache = {}
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._access_order = []

    def get(self, key):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                # Actualizar orden de acceso
                self._access_order.remove(key)
                self._access_order.append(key)
                return value
            else:
                del self.cache[key]
                self._access_order.remove(key)
        return None

    def set(self, key, value):
        if len(self.cache) >= self.max_size:
            # Eliminar el menos recientemente usado
            oldest = self._access_order.pop(0)
            del self.cache[oldest]
        self.cache[key] = (value, time.time())
        self._access_order.append(key)

    def clear(self):
        self.cache.clear()
        self._access_order.clear()


# ============================================================
# AIRouter Mejorado
# ============================================================

class AIRouter:
    def __init__(self, use_cache=True):
        load_dotenv_files()
        self.config = load_config()
        ai_config = self.config.get("ai", {})
        self.use_cache = use_cache
        self.cache = ResponseCache(ttl_seconds=ai_config.get("cache_ttl", 300))

        # Inicializar proveedores
        self.providers = {
            "gemini": GeminiProvider(),
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "deepseek": DeepSeekProvider(),
            "deepseek-reasoner": DeepSeekReasonerProvider(),
            "ollama": OllamaProvider(),
        }
        # Filtrar proveedores no saludables
        self._refresh_health()

        # Policy Engine con reglas personalizadas
        self.policy_engine = PolicyEngine(
            routing_rules=ai_config.get("routing_rules"),
            fallback_chain=ai_config.get("fallback_chain"),
            default_chain=ai_config.get("default_chain"),
        )
        self.tracker = UsageTracker()
        logger.info("AIRouter inicializado con proveedores: %s", list(self.providers.keys()))

    def _refresh_health(self):
        """Actualiza el estado de salud de los proveedores y elimina los no disponibles."""
        healthy = {}
        for name, provider in self.providers.items():
            try:
                if provider.health_check():
                    healthy[name] = provider
                else:
                    logger.debug(f"Proveedor {name} no disponible (health_check falló)")
            except Exception as e:
                logger.warning(f"Error en health_check de {name}: {e}")
        self.providers = healthy
        if not self.providers:
            logger.warning("No hay proveedores disponibles. Revisa tus API keys.")

    def _get_cache_key(self, prompt, context, task_type):
        """Genera una clave de caché basada en prompt, contexto y tipo."""
        import hashlib
        content = f"{task_type}:{context}:{prompt}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def generate_content(self, prompt: str, context: Optional[str] = None,
                         task_type: str = "default", use_cache: bool = True) -> str:
        """
        Genera contenido usando el mejor proveedor disponible según la política.
        """
        # Verificar caché
        if use_cache and self.use_cache:
            cache_key = self._get_cache_key(prompt, context, task_type)
            cached = self.cache.get(cache_key)
            if cached is not None:
                logger.info(f"Respuesta desde caché para tarea '{task_type}'")
                return cached

        # Obtener lista de proveedores según política
        providers_chain = self.policy_engine.get_providers(task_type)
        # Filtrar solo los que están disponibles
        available_chain = [p for p in providers_chain if p in self.providers]

        if not available_chain:
            raise Exception("No hay proveedores disponibles para la tarea solicitada. Revisa tus API keys.")

        last_error = None
        for provider_name in available_chain:
            start_time = time.time()
            try:
                provider = self.providers.get(provider_name)
                if not provider:
                    continue

                logger.info(f"Ruteando a {provider_name} (Tarea: {task_type})...")
                response = provider.generate(prompt, context)

                latency = time.time() - start_time
                self.tracker.log_request(provider_name, task_type, latency, "SUCCESS", model=provider.model_name)
                logger.debug(f"Respuesta de {provider_name} en {latency:.2f}s")

                # Guardar en caché
                if use_cache and self.use_cache:
                    self.cache.set(cache_key, response)

                return response

            except Exception as e:
                latency = time.time() - start_time
                self.tracker.log_request(provider_name, task_type, latency, "FAILED", error=e)
                logger.warning(f"Fallo en proveedor {provider_name}: {e}")
                last_error = e
                continue

        # Si todos fallaron
        raise Exception(f"Todos los proveedores fallaron. Último error: {last_error}")

    def get_status(self) -> Dict[str, str]:
        """Devuelve estado de cada proveedor."""
        self._refresh_health()
        status = {name: "AVAILABLE" for name in self.providers}
        # Añadir proveedores que no están disponibles
        all_providers = ["gemini", "openai", "anthropic", "deepseek", "deepseek-reasoner", "ollama"]
        for name in all_providers:
            if name not in status:
                status[name] = "UNAVAILABLE"
        return status

    def get_metrics(self, days: int = 7) -> Optional[Dict]:
        """Devuelve métricas de uso."""
        return self.tracker.get_metrics(days)

    def clear_cache(self):
        """Limpia la caché de respuestas."""
        self.cache.clear()
        logger.info("Caché de respuestas limpiada.")


# ============================================================
# Singleton
# ============================================================

_router_instance = None

def get_ai_router() -> AIRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = AIRouter()
    return _router_instance
EOF
