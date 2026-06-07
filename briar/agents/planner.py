"""Briar Planner Agent — strategy before attack 🎯"""
from briar.agents.analyzer import SecurityAnalyzer

PLANNER_PROMPT = """You are a senior penetration tester planning an attack strategy.
Based on the reconnaissance data below, create a targeted attack plan.

For each finding category below, rate the likelihood of finding vulnerabilities (1-10) and explain why.
Then list the TOP 5 most likely attack vectors with specific payloads to try.

Output your plan in this structure:

## Risk Assessment
[rate each category 1-10 with reasoning]

## Priority Targets
[top 5 endpoints/params to attack first]

## Recommended Payloads  
[specific payloads for each vector]

## Strategy
[2-3 sentence summary of overall approach]

Be CONCISE. Focus on actionable intelligence, not theory."""

class PlannerAgent:
    """Analyzes recon data and creates an attack strategy."""

    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.name = "Planner"

    def scan(self, url: str, recon_data: dict = None, **kwargs) -> dict:
        """Generate attack strategy from recon data."""
        if not recon_data:
            return {"type": "Strategy", "severity": "Info", "agent": self.name,
                    "url": url, "analysis": "No recon data available to plan.",
                    "plan_json": {"strategy": "scan_all"}}

        # Build context from recon
        server = recon_data.get("server", "Unknown")
        techs = recon_data.get("technologies", [])
        headers = recon_data.get("security_headers", {})
        ports = recon_data.get("open_ports", [])
        endpoints = recon_data.get("endpoints_discovered", 0)
        urls_sample = recon_data.get("urls_sample", [])

        context = f"""RECONNAISSANCE DATA:

Server: {server}
Technologies: {', '.join(techs)}
Endpoints discovered: {endpoints}
Sample URLs: {', '.join(urls_sample[:5])}
Open ports: {', '.join(f"{p['port']}/{p['service']}" for p in ports) if ports else 'None'}

Security headers:
{chr(10).join(f'  {k}: {v}' for k,v in headers.items())}

Based on this data, plan the attack."""

        result = self.analyzer.analyze_endpoint(url, plan_context=context)
        result["agent"] = self.name
        result["type"] = "Strategy"
        result["severity"] = "Info"

        # Build plan JSON for downstream agents
        plan_json = {
            "strategy": "scan_all",
            "priority_params": [],
            "recommended_agents": [],
        }

        # Smart recommendations based on recon
        analysis_lower = result.get("analysis", "").lower()
        if any(p["port"] in (3306, 5432, 1433) for p in ports):
            plan_json["recommended_agents"].append("injection")
            plan_json["strategy"] = "sql_first"
        if any(h == "MISSING" for h in headers.values()):
            plan_json["recommended_agents"].append("csrf")
        if "php" in server.lower() or "apache" in server.lower():
            plan_json["priority_params"].extend(["file", "path", "page"])
            plan_json["recommended_agents"].append("traversal")
        if "wp-content" in " ".join(techs).lower():
            plan_json["recommended_agents"].extend(["injection", "upload"])
            plan_json["priority_params"].extend(["p", "page_id", "author"])
        if any(t.lower() in str(techs).lower() for t in ["react", "next", "vue", "angular"]):
            plan_json["recommended_agents"].extend(["api", "xss"])
            plan_json["strategy"] = "spa_audit"

        result["plan_json"] = plan_json
        return result
