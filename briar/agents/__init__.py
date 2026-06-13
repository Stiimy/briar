from .analyzer import SecurityAnalyzer
from .recon import ReconAgent
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
from .planner import PlannerAgent
from .cve import CVEAgent
from .gitbackup import GitBackupAgent
from .jwt import JWTAgent

AGENTS = {
    "recon": ReconAgent, "injection": InjectionAgent, "xss": XSSAgent, "ssrf": SSRFAgent,
    "auth": AuthAgent, "authz": AuthZAgent, "csrf": CSRFAgent,
    "upload": UploadAgent, "traversal": TraversalAgent,
    "rce": RCEAgent, "api": APIAgent, "secrets": SecretsAgent,
    "planner": PlannerAgent,
    "cve": CVEAgent,
    "gitbackup": GitBackupAgent,
    "jwt": JWTAgent,
}

def run_agent(name, provider="ollama", **kwargs):
    if name not in AGENTS:
        return {"error": f"Agent '{name}' not found. Available: {list(AGENTS.keys())}"}
    agent = AGENTS[name](provider)
    # Inject tech context if analyzer supports it
    recon_data = kwargs.pop("recon_data", None)
    if recon_data and hasattr(agent, 'analyzer'):
        from briar.agents.analyzer import build_tech_context
        kwargs["tech_context"] = build_tech_context(recon_data)
    return agent.scan(**kwargs)
