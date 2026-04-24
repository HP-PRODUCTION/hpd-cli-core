import os
import time
from hpd_cli import logger

class BaseProvider:
    def __init__(self, model_name=None):
        self.model_name = model_name

    def generate(self, prompt, context=None):
        raise NotImplementedError

    def health_check(self):
        raise NotImplementedError

class GeminiProvider(BaseProvider):
    def generate(self, prompt, context=None):
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Falta GEMINI_API_KEY")
        
        genai.configure(api_key=api_key)
        model_name = self.model_name or "gemini-1.5-flash"
        model = genai.GenerativeModel(model_name)
        
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        response = model.generate_content(full_prompt)
        return response.text

    def health_check(self):
        return os.getenv("GEMINI_API_KEY") is not None

class OpenAIProvider(BaseProvider):
    def generate(self, prompt, context=None):
        # Implementación simplificada para v1
        return f"[AI Router - OpenAI Simulator] Simulando respuesta para: {prompt[:50]}..."

    def health_check(self):
        # Siempre disponible en v1 como simulador
        return True

class AnthropicProvider(BaseProvider):
    def generate(self, prompt, context=None):
        # Implementación simplificada para v1
        return f"[AI Router - Anthropic Simulator] Simulando respuesta para: {prompt[:50]}..."

    def health_check(self):
        # Siempre disponible en v1 como simulador
        return True

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

class PolicyEngine:
    def __init__(self):
        self.routing_rules = {
            "code_generate": ["openai", "anthropic", "gemini", "cloudflare"],
            "architecture_review": ["anthropic", "openai", "gemini"],
            "fast_lookup": ["cloudflare", "gemini", "openai"],
            "default": ["gemini", "openai", "anthropic", "cloudflare"]
        }

    def get_providers(self, task_type):
        return self.routing_rules.get(task_type, self.routing_rules["default"])

import json
from datetime import datetime

from hpd_cli.config import load_config

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
        self.providers = {
            "gemini": GeminiProvider(),
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "cloudflare": CloudflareProvider()
        }
        self.policy_engine = PolicyEngine()
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
