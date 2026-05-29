"""Groq provider — Llama 4, Mixtral (free tier available)"""
import os
from typing import Optional

class GroqProvider:
    def __init__(self, model: str = "llama-3.3-70b-versatile", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
    
    def chat(self, messages: list, system: Optional[str] = None, max_tokens: int = 4096) -> str:
        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)
            if system:
                messages = [{"role":"system","content":system}] + messages
            resp = client.chat.completions.create(model=self.model, messages=messages, max_tokens=max_tokens)
            return resp.choices[0].message.content
        except ImportError:
            raise ImportError("pip install groq")
        except Exception as e:
            raise RuntimeError(f"Groq error: {e}")
    
    def health_check(self) -> bool:
        return bool(self.api_key)
