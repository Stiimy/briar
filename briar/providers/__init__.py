"""Multi-provider AI backends for Briar"""
from .ollama import OllamaProvider
from .openai import OpenAIProvider

PROVIDERS = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
}

def get_provider(name, **kwargs):
    if name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {name}. Available: {list(PROVIDERS.keys())}")
    return PROVIDERS[name](**kwargs)
