"""RCE Attack Agent — Remote Code Execution 🤖"""
from briar.agents.analyzer import SecurityAnalyzer

class RCEAgent:
    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.name = "RCE"
    def scan(self, url: str, **kwargs) -> dict:
        result = self.analyzer.analyze_endpoint(url, "GET", "RCE testing — deserialization, eval, exec")
        result["agent"] = self.name
        return result
