"""DeepSeek provider — R1, V3"""
import os
from typing import Optional
from .openai import OpenAIProvider  # DeepSeek uses OpenAI-compatible API

class DeepSeekProvider(OpenAIProvider):
    def __init__(self, model: str = "deepseek-chat", api_key: Optional[str] = None):
        super().__init__(model=model, api_key=api_key or os.environ.get("DEEPSEEK_API_KEY",""))
        self.base_url = "https://api.deepseek.com/v1"
    
    def chat(self, messages: list, system: Optional[str] = None, max_tokens: int = 4096) -> str:
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            if system:
                messages = [{"role":"system","content":system}] + messages
            resp = client.chat.completions.create(model=self.model, messages=messages, max_tokens=max_tokens)
            return resp.choices[0].message.content
        except ImportError:
            raise ImportError("pip install openai")
        except Exception as e:
            raise RuntimeError(f"DeepSeek error: {e}")
