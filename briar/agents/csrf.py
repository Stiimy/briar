"""CSRF Attack Agent — Cross-Site Request Forgery detection 🎯"""
from briar.agents.analyzer import SecurityAnalyzer
from briar.core.http import HTTPClient

class CSRFAgent:
    """Detects missing CSRF protections with real form analysis"""

    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.http = HTTPClient(timeout=10)
        self.name = "CSRF"

    def scan(self, url: str, tech_context: str = "", **kwargs) -> dict:
        """Scan for CSRF vulnerabilities by analyzing forms"""
        findings = []

        try:
            resp = self.http.get(url)
            html = resp.text
            forms = self.http.extract_forms(html)

            for form in forms:
                if form["method"] == "POST" and form["inputs"]:
                    if not form["has_csrf_token"]:
                        # Try to submit the form without CSRF token
                        data = {inp: "test" for inp in form["inputs"] if inp not in ["submit", "button"]}
                        try:
                            form_url = form["action"] or url
                            post_resp = self.http.post(form_url, data=data)
                            if post_resp.status_code in [200, 302]:
                                findings.append({
                                    "type": "CSRF — Missing Token",
                                    "severity": "High",
                                    "form_action": form_url,
                                    "form_method": form["method"],
                                    "inputs": form["inputs"],
                                    "post_response": post_resp.status_code,
                                })
                        except:
                            findings.append({
                                "type": "CSRF — Missing Token (untested)",
                                "severity": "Medium",
                                "form_action": form["action"] or url,
                                "inputs": form["inputs"],
                            })

            # Also check headers
            csrf_headers = ["X-CSRF-Token", "X-XSRF-Token", "X-CSRFToken"]
            has_csrf_header = any(h in resp.headers for h in csrf_headers)
            if not has_csrf_header and any(f["method"] == "POST" for f in forms):
                findings.append({
                    "type": "CSRF — No CSRF headers",
                    "severity": "Low",
                    "checked_headers": csrf_headers,
                })

        except Exception as e:
            findings.append({"type": "CSRF scan error", "error": str(e)})

        analysis = f"CSRF scan complete for {url}\n\n"
        analysis += f"Forms found: {len(forms) if 'forms' in dir() else 0}\n\n"
        if findings:
            analysis += f"**{len(findings)} CSRF issues found:**\n\n"
            for f in findings:
                if "form_action" in f:
                    analysis += f"- Missing CSRF token on `{f['form_action']}` ({f.get('form_method','GET')}) — inputs: {f.get('inputs',[])}\n"
        else:
            analysis += "No CSRF vulnerabilities detected.\n"

        analysis += "\n---\n\nLLM analysis:\n"
        result = self.analyzer.analyze_endpoint(url, "POST", tech_context=tech_context, source_hint= analysis)
        result["real_findings"] = findings
        result["agent"] = self.name
        result["type"] = "CSRF"
        result["severity"] = "High" if any(f.get("severity","") == "High" for f in findings) else ("Medium" if findings else "Info")
        return result
