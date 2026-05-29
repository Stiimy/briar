"""API Security Agent — GraphQL, REST, rate limiting 📡"""
from briar.agents.analyzer import SecurityAnalyzer

class APIAgent:
    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.name = "API"
    def scan(self, url: str, **kwargs) -> dict:
        result = self.analyzer.analyze_endpoint(url, "GET", "API security testing")
        result["agent"] = self.name
        return result
