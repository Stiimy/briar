"""Secrets Detection Agent — hardcoded keys, .env, tokens 🔑"""
import os, re

class SecretsAgent:
    def __init__(self, provider="ollama"):
        self.name = "Secrets"
        self.patterns = [
            (r'(?:api|auth|token|key|secret|password|passwd)[\"\'\s:=]+([a-zA-Z0-9_\-]{20,})', 'API Key/Token'),
            (r'sk-[a-zA-Z0-9]{32,}', 'OpenAI Key'),
            (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Token'),
            (r'AKIA[0-9A-Z]{16}', 'AWS Access Key'),
            (r'(?:mongodb|postgres|mysql)://[^@]+@', 'Database URL'),
        ]
    
    def scan(self, url: str = "", repo_path: str = None, **kwargs) -> dict:
        findings = []
        if repo_path and os.path.isdir(repo_path):
            for root, _, files in os.walk(repo_path):
                for f in files:
                    if f.endswith(('.py','.js','.ts','.yml','.yaml','.env','.json','.go')):
                        try:
                            with open(os.path.join(root,f), errors='ignore') as fh:
                                content = fh.read()
                                for pattern, name in self.patterns:
                                    matches = re.findall(pattern, content, re.I)
                                    if matches:
                                        findings.append(f"[SECRETS] {name} in {f}: {len(matches)} matches")
                        except: pass
        
        return {
            "agent": self.name,
            "url": url,
            "type": "Secrets Detection",
            "severity": "Critical" if findings else "Low",
            "analysis": "\n".join(findings) if findings else "No hardcoded secrets found",
            "findings_count": len(findings)
        }
