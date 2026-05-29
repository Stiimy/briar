"""Briar Security Agents 🛡️"""
from .analyzer import SecurityAnalyzer
from .injection import InjectionAgent
from .xss import XSSAgent
from .ssrf import SSRFAgent
from .auth import AuthAgent

AGENTS = {
    "recon": None,  # TODO
    "injection": InjectionAgent,
    "xss": XSSAgent,
    "ssrf": SSRFAgent,
    "auth": AuthAgent,
    "authz": None,  # TODO
}

def run_agent(name, provider="ollama", **kwargs):
    if name not in AGENTS or AGENTS[name] is None:
        return {"error": f"Agent '{name}' not yet implemented"}
    agent = AGENTS[name](provider)
    return agent.scan(**kwargs)
