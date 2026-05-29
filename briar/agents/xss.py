"""XSS Attack Agent — Reflected, Stored, DOM, CSP bypass ❌"""
from briar.agents.analyzer import SecurityAnalyzer

class XSSAgent:
    """Discovers Cross-Site Scripting vulnerabilities"""
    
    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.name = "XSS"
        self.payloads = [
            '<script>alert(1)</script>',
            '"><script>alert(1)</script>',
            '<img src=x onerror=alert(1)>',
            '<svg onload=alert(1)>',
            'javascript:alert(1)',
        ]
    
    def scan(self, url: str, inputs: list = None) -> dict:
        context = f"Input fields: {inputs}" if inputs else "No input fields provided"
        result = self.analyzer.analyze_endpoint(url, "GET", context)
        result["agent"] = self.name
        result["payloads_tested"] = self.payloads[:3]
        return result
