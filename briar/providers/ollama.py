"""Ollama provider — local, free, private"""
import json
import requests
from typing import Optional

class OllamaProvider:
    def __init__(self, model: str = "minimax-m2.5:latest", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
    
    def chat(self, messages: list, system: Optional[str] = None, max_tokens: int = 4096) -> str:
        """Send chat completion to Ollama"""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": max_tokens}
        }
        if system:
            payload["system"] = system
        
        try:
            resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=120)
            resp.raise_for_status()
            return resp.json()["message"]["content"]
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Ollama not running at {self.base_url}. Start with: ollama serve")
        except Exception as e:
            raise RuntimeError(f"Ollama error: {e}")
    
    def list_models(self) -> list:
        """List available models"""
        resp = requests.get(f"{self.base_url}/api/tags")
        return [m["name"] for m in resp.json().get("models", [])]
    
    def health_check(self) -> bool:
        """Check if Ollama is running"""
        try:
            requests.get(f"{self.base_url}/api/tags", timeout=5)
            return True
        except:
            return False
