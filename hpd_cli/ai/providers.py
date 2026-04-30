import os
import yaml
from hpd_cli import logger
from hpd_cli.ai_router import AIRouter

def load_global_config():
    config_path = os.path.expanduser("~/.hpd/config.yaml")
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def ask_provider(provider_name, prompt, context=""):
    config = load_global_config()

    # Load .env if it exists
    env_path = os.path.expanduser("~/.hpd/.env")
    if os.path.exists(env_path):
        from dotenv import load_dotenv
        load_dotenv(env_path)

    from hpd_cli.ai_router import get_ai_router
    router = get_ai_router()

    try:
        # If a specific provider is requested, we try it first
        if provider_name and provider_name in router.providers:
            # We override the policy engine for this call
            provider = router.providers[provider_name]
            if provider.health_check():
                logger.info(f"Forzando proveedor: {provider_name}")
                return provider.generate(prompt, context)
            else:
                logger.warning(f"Proveedor {provider_name} no está disponible. Usando router por defecto.")

        response = router.generate_content(prompt, context=context, task_type="default")
        return response
    except Exception as e:
        logger.error(f"Error calling AI provider: {e}")
        return f"Error: {e}"
