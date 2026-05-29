"""Mistral AI provider 🇫🇷"""
import os
from typing import Optional

class MistralProvider:
    def __init__(self, model: str = "mistral-large-latest", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.environ.get("MISTRAL_API_KEY", "")
    
    def chat(self, messages: list, system: Optional[str] = None, max_tokens: int = 4096) -> str:
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.api_key)
            if system:
                messages = [{"role":"system","content":system}] + messages
            resp = client.chat.complete(model=self.model, messages=messages, max_tokens=max_tokens)
            return resp.choices[0].message.content
        except ImportError:
            raise ImportError("pip install mistralai")
        except Exception as e:
            raise RuntimeError(f"Mistral error: {e}")
    
    def health_check(self) -> bool:
        return bool(self.api_key)
