"""Authorization Attack Agent — IDOR, privilege escalation 👤"""
import re
from briar.agents.analyzer import SecurityAnalyzer
from briar.core.http import HTTPClient

class AuthZAgent:
    """Discovers authorization vulnerabilities (IDOR, missing access control)"""

    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.http = HTTPClient(timeout=10)
        self.name = "Authorization"

    def _extract_ids(self, url: str, html: str) -> list:
        """Extract numeric IDs from URLs and page content"""
        ids = set()
        # From the URL itself
        for match in re.finditer(r'/(\d+)(?:/|\.|$|\?)', url):
            ids.add(int(match.group(1)))
        # From href/src attributes
        for match in re.finditer(r'/(\d+)(?:/|\.|$|\?)', html):
            ids.add(int(match.group(1)))
        return list(ids)

    def scan(self, url: str, **kwargs) -> dict:
        """Scan for authorization vulnerabilities (IDOR testing)"""
        findings = []

        try:
            resp = self.http.get(url)
            html = resp.text
            base_len = len(html)

            # Extract IDs from the page
            ids = self._extract_ids(url, html)
            if not ids:
                ids = [1, 2, 0, -1, 999999]  # Default test IDs

            # Test IDOR: replace IDs and check response differences
            for test_id in ids[:5]:
                # Build test URL by replacing numeric IDs in the path
                test_url = re.sub(r'/(\d+)(/|\.|$|\?)', f'/{test_id}\\2', url)
                if test_url == url:
                    continue

                try:
                    test_resp = self.http.get(test_url)
                    test_len = len(test_resp.text)

                    # Same length = potential IDOR (same content for different ID)
                    if abs(test_len - base_len) < 50 and test_resp.status_code == 200:
                        findings.append({
                            "type": "IDOR — Potential",
                            "severity": "High",
                            "original_url": url,
                            "test_url": test_url,
                            "original_len": base_len,
                            "test_len": test_len,
                            "test_id": test_id,
                            "status": test_resp.status_code,
                        })
                        break  # Found one, stop
                except:
                    pass

            # Check for missing auth headers
            auth_headers = ["Authorization", "X-Auth-Token", "X-API-Key", "Session"]
            has_auth_headers = any(h in resp.headers for h in auth_headers)

            if not has_auth_headers and not findings:
                findings.append({
                    "type": "No authorization headers detected",
                    "severity": "Low",
                    "checked_headers": auth_headers,
                })

        except Exception as e:
            findings.append({"type": "AuthZ scan error", "error": str(e)})

        analysis = f"Authorization scan complete for {url}\n\n"
        if findings:
            analysis += f"**{len(findings)} authorization issues found:**\n\n"
            for f in findings:
                if "idor" in str(f.get("type", "")).lower():
                    analysis += f"- **{f['type']}**: `{f['test_url']}` returned same content as original ({f['test_len']} vs {f['original_len']} bytes)\n"
                else:
                    analysis += f"- {f.get('type','?')}\n"
            analysis += "\n---\n\nLLM analysis of authz findings:\n"

        result = self.analyzer.analyze_endpoint(url, "GET", analysis)
        result["real_findings"] = findings
        result["agent"] = self.name
        result["type"] = "Authorization"
        result["severity"] = "High" if any("IDOR" in str(f.get("type","")) for f in findings) else ("Medium" if findings else "Info")
        return result
