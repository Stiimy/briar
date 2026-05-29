"""Authentication Attack Agent — JWT, OAuth, MFA bypass 🔐"""
from briar.agents.analyzer import SecurityAnalyzer

class AuthAgent:
    """Discovers authentication vulnerabilities"""
    
    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.name = "Authentication"
    
    def scan(self, url: str, auth_type: str = "unknown") -> dict:
        context = f"Authentication type: {auth_type}"
        result = self.analyzer.analyze_endpoint(url, "GET", context)
        result["agent"] = self.name
        return result
