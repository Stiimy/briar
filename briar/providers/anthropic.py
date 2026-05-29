"""Anthropic provider — Claude Opus/Sonnet/Haiku"""
import os
from typing import Optional

class AnthropicProvider:
    def __init__(self, model: str = "claude-sonnet-4-6", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    
    def chat(self, messages: list, system: Optional[str] = None, max_tokens: int = 4096) -> str:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            resp = client.messages.create(
                model=self.model, max_tokens=max_tokens,
                system=system or "", messages=messages
            )
            return resp.content[0].text
        except ImportError:
            raise ImportError("pip install anthropic")
        except Exception as e:
            raise RuntimeError(f"Anthropic error: {e}")
    
    def health_check(self) -> bool:
        return bool(self.api_key)
