"""xAI provider — Grok-3"""
import os

class XAIProvider:
    def __init__(self, model="grok-3", api_key=None):
        self.model = model
        self.api_key = api_key or os.environ.get("XAI_API_KEY","")
    def chat(self, messages, system=None, max_tokens=4096):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url="https://api.x.ai/v1")
            if system: messages = [{"role":"system","content":system}] + messages
            return client.chat.completions.create(model=self.model, messages=messages, max_tokens=max_tokens).choices[0].message.content
        except ImportError: raise ImportError("pip install openai")
    def health_check(self): return bool(self.api_key)
