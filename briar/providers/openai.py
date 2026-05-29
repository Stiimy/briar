"""OpenAI provider — ChatGPT, GPT-4"""
import os
from typing import Optional

class OpenAIProvider:
    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
    
    def chat(self, messages: list, system: Optional[str] = None, max_tokens: int = 4096) -> str:
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            if system:
                messages = [{"role": "system", "content": system}] + messages
            resp = client.chat.completions.create(model=self.model, messages=messages, max_tokens=max_tokens)
            return resp.choices[0].message.content
        except ImportError:
            raise ImportError("Install openai: pip install openai")
        except Exception as e:
            raise RuntimeError(f"OpenAI error: {e}")
    
    def health_check(self) -> bool:
        return bool(self.api_key)
