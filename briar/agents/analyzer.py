"""Briar AI Analysis Engine — the brain of the pentest 🧠"""
from typing import Optional
from briar.providers import get_provider

SECURITY_ANALYST_PROMPT = """You are an elite security researcher performing a penetration test.
Analyze the target and identify vulnerabilities. For each finding, provide:

1. VULNERABILITY TYPE (OWASP category)
2. SEVERITY (Critical/High/Medium/Low)
3. CVSS SCORE (0.0-10.0)
4. ENDPOINT / LOCATION
5. DESCRIPTION (what the vuln is)
6. EXPLOIT STEPS (how to reproduce)
7. IMPACT (what an attacker can do)
8. REMEDIATION (how to fix)

Be specific. Include exact URLs, parameters, payloads. Think like an attacker."""

class SecurityAnalyzer:
    """Core AI security analysis engine"""
    
    def __init__(self, provider: str = "ollama", model: Optional[str] = None):
        self.provider = get_provider(provider, model=model) if model else get_provider(provider)
    
    def analyze_endpoint(self, url: str, method: str = "GET", source_hint: str = "") -> dict:
        """Analyze a single endpoint for vulnerabilities"""
        prompt = f"""Analyze this endpoint for security vulnerabilities:

URL: {url}
Method: {method}
{f'Source code context: {source_hint}' if source_hint else ''}

List ALL potential vulnerabilities you find. For each one, provide the full details as specified."""
        
        messages = [{"role": "user", "content": prompt}]
        response = self.provider.chat(messages, system=SECURITY_ANALYST_PROMPT, max_tokens=4096)
        return {"url": url, "analysis": response, "raw": response}
    
    def analyze_code(self, code: str, filepath: str = "") -> dict:
        """Analyze source code for vulnerabilities"""
        prompt = f"""Analyze this source code for security vulnerabilities:

File: {filepath}

``` 
{code[:8000]} 
```

Find: SQL injection, XSS, SSRF, command injection, path traversal, auth bypass, 
deserialization, hardcoded secrets, unsafe eval, etc.

For each finding, specify the exact line and how to exploit it."""
        
        messages = [{"role": "user", "content": prompt}]
        response = self.provider.chat(messages, system=SECURITY_ANALYST_PROMPT, max_tokens=4096)
        return {"file": filepath, "analysis": response}
    
    def generate_report(self, findings: list, target: str) -> str:
        """Generate a comprehensive security report"""
        findings_text = "\n\n---\n\n".join([
            f"## Finding {i+1}\n{f.get('analysis', f.get('raw',''))}"
            for i, f in enumerate(findings)
        ])
        
        prompt = f"""Generate a PROFESSIONAL penetration test report for {target}.

Findings:
{findings_text[:6000]}

Create a structured report with:
1. Executive Summary
2. Methodology
3. Findings (detailed per vulnerability)
4. Risk Matrix
5. Recommendations
6. Conclusion

Format in Markdown. Be professional and precise."""
        
        messages = [{"role": "user", "content": prompt}]
        return self.provider.chat(messages, system="You are a senior security consultant writing a pentest report.", max_tokens=8192)
