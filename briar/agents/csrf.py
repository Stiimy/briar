"""CSRF Attack Agent — Cross-Site Request Forgery 🎯"""
from briar.agents.analyzer import SecurityAnalyzer

class CSRFAgent:
    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.name = "CSRF"
    def scan(self, url: str, **kwargs) -> dict:
        result = self.analyzer.analyze_endpoint(url, "POST", "CSRF token analysis")
        result["agent"] = self.name
        return result
