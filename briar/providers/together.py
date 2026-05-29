"""Together AI provider"""
import os
class TogetherProvider:
    def __init__(self, model="mistralai/Mixtral-8x7B-Instruct-v0.1", api_key=None):
        self.model = model
        self.api_key = api_key or os.environ.get("TOGETHER_API_KEY","")
    def chat(self, messages, system=None, max_tokens=4096):
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url="https://api.together.xyz/v1")
        if system: messages = [{"role":"system","content":system}] + messages
        return client.chat.completions.create(model=self.model, messages=messages, max_tokens=max_tokens).choices[0].message.content
    def health_check(self): return bool(self.api_key)
