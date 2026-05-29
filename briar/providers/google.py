"""Google provider — Gemini"""
import os

class GoogleProvider:
    def __init__(self, model="gemini-2.5-pro-exp-03-25", api_key=None):
        self.model = model
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY","")
    def chat(self, messages, system=None, max_tokens=4096):
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            prompt = (system + "\n\n" if system else "") + messages[-1]["content"]
            return genai.GenerativeModel(self.model).generate_content(prompt).text
        except ImportError: raise ImportError("pip install google-generativeai")
    def health_check(self): return bool(self.api_key)
