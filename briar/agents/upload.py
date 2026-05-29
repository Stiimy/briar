"""File Upload Attack Agent 📁"""
from briar.agents.analyzer import SecurityAnalyzer

class UploadAgent:
    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.name = "FileUpload"
    def scan(self, url: str, **kwargs) -> dict:
        result = self.analyzer.analyze_endpoint(url, "POST", "File upload testing")
        result["agent"] = self.name
        return result
