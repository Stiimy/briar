"""Path Traversal Attack Agent 🗺️"""
from briar.agents.analyzer import SecurityAnalyzer

class TraversalAgent:
    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.name = "PathTraversal"
    def scan(self, url: str, **kwargs) -> dict:
        result = self.analyzer.analyze_endpoint(url, "GET", "Path traversal testing")
        result["agent"] = self.name
        return result
