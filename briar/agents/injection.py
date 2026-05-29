"""Injection Attack Agent — SQL, NoSQL, Command, LDAP, SSTI 💉"""
from briar.agents.analyzer import SecurityAnalyzer

class InjectionAgent:
    """Discovers and exploits injection vulnerabilities"""
    
    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.name = "Injection"
    
    def scan(self, url: str, params: list = None, forms: list = None) -> dict:
        """Scan for injection vulnerabilities"""
        context = f"Parameters: {params}" if params else ""
        context += f"\nForms: {forms}" if forms else ""
        result = self.analyzer.analyze_endpoint(url, "GET/POST", context)
        result["agent"] = self.name
        return result
    
    def exploit(self, url: str, vuln_type: str, payload: str) -> dict:
        """Attempt to exploit an injection vulnerability"""
        # In full version: execute actual HTTP request with payload
        return {
            "url": url,
            "type": vuln_type,
            "payload": payload,
            "status": "analyzed",
            "note": "Full exploitation requires live target access"
        }
