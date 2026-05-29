from .analyzer import SecurityAnalyzer
from .injection import InjectionAgent
from .xss import XSSAgent
from .ssrf import SSRFAgent
from .auth import AuthAgent
from .authz import AuthZAgent
from .csrf import CSRFAgent
from .upload import UploadAgent
from .traversal import TraversalAgent
from .rce import RCEAgent
from .api import APIAgent
from .secrets import SecretsAgent

AGENTS = {
    "injection": InjectionAgent, "xss": XSSAgent, "ssrf": SSRFAgent,
    "auth": AuthAgent, "authz": AuthZAgent, "csrf": CSRFAgent,
    "upload": UploadAgent, "traversal": TraversalAgent,
    "rce": RCEAgent, "api": APIAgent, "secrets": SecretsAgent,
}

def run_agent(name, provider="ollama", **kwargs):
    if name not in AGENTS:
        return {"error": f"Agent '{name}' not found. Available: {list(AGENTS.keys())}"}
    return AGENTS[name](provider).scan(**kwargs)
