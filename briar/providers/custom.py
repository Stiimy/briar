"""Custom provider — any OpenAI-compatible endpoint"""
import os
class CustomProvider:
    def __init__(self, model="gpt-4", api_key=None, base_url=None):
        self.model = model
        self.api_key = api_key or os.environ.get("CUSTOM_API_KEY","")
        self.base_url = base_url or os.environ.get("CUSTOM_BASE_URL","http://localhost:8080/v1")
    def chat(self, messages, system=None, max_tokens=4096):
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        if system: messages = [{"role":"system","content":system}] + messages
        return client.chat.completions.create(model=self.model, messages=messages, max_tokens=max_tokens).choices[0].message.content
    def health_check(self): return bool(self.api_key)
