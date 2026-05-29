"""Authorization Attack Agent — IDOR, privilege escalation 👤"""
from briar.agents.analyzer import SecurityAnalyzer

class AuthZAgent:
    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.name = "Authorization"
    def scan(self, url: str, **kwargs) -> dict:
        result = self.analyzer.analyze_endpoint(url, "GET", "Authorization testing")
        result["agent"] = self.name
        return result
