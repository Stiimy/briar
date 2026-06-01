"""API Security Agent — GraphQL, REST, OpenAPI detection 📡"""
from briar.agents.analyzer import SecurityAnalyzer
from briar.core.http import HTTPClient

class APIAgent:
    """Detects API endpoints and tests for common misconfigurations"""

    API_PATHS = [
        ("/graphql", "GraphQL endpoint"),
        ("/graphiql", "GraphQL IDE"),
        ("/api", "REST API"),
        ("/api/v1", "REST API v1"),
        ("/api/v2", "REST API v2"),
        ("/swagger.json", "Swagger/OpenAPI spec"),
        ("/openapi.json", "OpenAPI 3.0 spec"),
        ("/api-docs", "API docs"),
        ("/docs", "API docs"),
        ("/.well-known/openid-configuration", "OIDC config"),
        ("/wp-json/", "WordPress REST API"),
        ("/v1/", "API v1 prefix"),
    ]

    GRAPHQL_INTROSPECTION = {
        "query": "{ __schema { types { name fields { name } } } }"
    }

    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.http = HTTPClient(timeout=10)
        self.name = "API"

    def scan(self, url: str, tech_context: str = "", **kwargs) -> dict:
        """Detect API endpoints and test security"""
        findings = []
        discovered = []

        # Check common API paths
        for path, desc in self.API_PATHS:
            try:
                full_url = url.rstrip("/") + path
                resp = self.http.get(full_url)
                if resp.status_code in [200, 301, 302, 401, 403]:
                    text_lower = resp.text[:500].lower()
                    # Only count as API if response contains API markers
                    api_markers = ["swagger", "openapi", '"paths"', "__schema", "graphql",
                                   "api", "endpoints", '"title"', '"version"', "application/json"]
                    is_html = text_lower.strip().startswith("<!doctype") or text_lower.strip().startswith("<html")
                    has_api_content = any(m in text_lower for m in api_markers)
                    if has_api_content and not is_html:
                        discovered.append({"path": path, "desc": desc, "status": resp.status_code, "length": len(resp.text)})

                # GraphQL introspection test
                if "graphql" in path.lower() and resp.status_code == 200:
                    try:
                        intro_resp = self.http.post(full_url, json=self.GRAPHQL_INTROSPECTION)
                        if "__schema" in intro_resp.text or "types" in intro_resp.text:
                            findings.append({
                                "type": "GraphQL Introspection Enabled",
                                "severity": "Medium",
                                "endpoint": full_url,
                                "detail": "Schema fully exposed via introspection query",
                            })
                    except:
                        pass

                # Rate limiting check
                if "api" in path.lower() and resp.status_code == 200:
                    for _ in range(5):
                        try:
                            r = self.http.get(full_url)
                            if r.status_code == 429:
                                findings.append({
                                    "type": "Rate Limiting Active",
                                    "severity": "Info",
                                    "endpoint": full_url,
                                })
                                break
                        except:
                            pass

            except:
                pass

        analysis = f"API scan complete for {url}\n\n"
        analysis += f"Endpoints discovered: {len(discovered)}\n\n"
        for d in discovered:
            analysis += f"- `{d['path']}` — {d['desc']} (HTTP {d['status']})\n"

        if findings:
            analysis += f"\n**{len(findings)} API security issues found:**\n\n"
            for f in findings:
                analysis += f"- **{f['type']}**: {f.get('endpoint','?')} — {f.get('detail','')}\n"
            analysis += "\n---\n\nLLM analysis of real API findings:\n"

        result = self.analyzer.analyze_endpoint(url, "GET", tech_context=tech_context, source_hint= analysis)
        result["real_findings"] = findings
        result["discovered_endpoints"] = [d["path"] for d in discovered]
        result["agent"] = self.name
        result["type"] = "API Security"
        result["severity"] = "Medium" if findings else "Info"
        return result
