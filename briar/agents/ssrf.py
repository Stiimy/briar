"""SSRF Attack Agent — Server-Side Request Forgery 🌐"""
from briar.agents.analyzer import SecurityAnalyzer

class SSRFAgent:
    """Discovers SSRF vulnerabilities"""
    
    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.name = "SSRF"
        self.test_urls = [
            "http://169.254.169.254/latest/meta-data/",  # AWS
            "http://metadata.google.internal/",            # GCP
            "http://127.0.0.1:8080/",                      # Localhost
            "file:///etc/passwd",                          # LFI
        ]
    
    def scan(self, url: str, param_name: str = None) -> dict:
        context = f"SSRF test parameter: {param_name}" if param_name else ""
        result = self.analyzer.analyze_endpoint(url, "GET", context)
        result["agent"] = self.name
        result["test_payloads"] = self.test_urls[:3]
        return result
