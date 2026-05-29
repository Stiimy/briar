from .ollama import OllamaProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .deepseek import DeepSeekProvider
from .groq import GroqProvider
from .mistral import MistralProvider
from .xai import XAIProvider
from .google import GoogleProvider
from .openrouter import OpenRouterProvider

PROVIDERS = {
    "ollama": OllamaProvider, "openai": OpenAIProvider, "anthropic": AnthropicProvider,
    "deepseek": DeepSeekProvider, "groq": GroqProvider, "mistral": MistralProvider,
    "xai": XAIProvider, "google": GoogleProvider, "openrouter": OpenRouterProvider, "together": TogetherProvider, "custom": CustomProvider,
}

def get_provider(name, **kwargs):
    name = name.lower()
    if name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {name}. Available: {list(PROVIDERS.keys())}")
    return PROVIDERS[name](**kwargs)
from .together import TogetherProvider
from .custom import CustomProvider
