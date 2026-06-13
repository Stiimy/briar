"""CVE Checker Agent — version detection to CVE mapping 📋"""
from briar.agents.analyzer import SecurityAnalyzer
from briar.core.http import HTTPClient
import re

class CVEAgent:
    """Detects software versions and maps to known CVEs."""

    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.http = HTTPClient(timeout=10)
        self.name = "CVE"

    def scan(self, url: str, **kwargs) -> dict:
        findings = []
        try:
            resp = self.http.get(url)
            html = resp.text[:5000]
            headers = dict(resp.headers)

            # Extract version patterns
            version_patterns = {
                r'jquery[.-]?([\d.]+)': 'jQuery',
                r'bootstrap[.-]?([\d.]+)': 'Bootstrap',
                r'wordpress[ -]?([\d.]+)': 'WordPress',
                r'apache/?([\d.]+)': 'Apache',
                r'nginx/?([\d.]+)': 'nginx',
                r'php/?([\d.]+)': 'PHP',
                r'python/?([\d.]+)': 'Python',
                r'node[ .]?v?([\d.]+)': 'Node.js',
                r'react[ .]?([\d.]+)': 'React',
                r'vue[ .]?([\d.]+)': 'Vue.js',
                r'angular[ .]?([\d.]+)': 'Angular',
                r'laravel[ .]?([\d.]+)': 'Laravel',
                r'django[ .]?([\d.]+)': 'Django',
            }

            for pattern, name in version_patterns.items():
                for match in re.finditer(pattern, html + ' ' + str(headers), re.I):
                    version = match.group(1)
                    findings.append({
                        "type": f"Version Detected",
                        "severity": "Info",
                        "agent": self.name,
                        "software": name,
                        "version": version,
                        "analysis": f"{name} v{version} detected. Check for known CVEs."
                    })

            # Server version
            server = headers.get("Server", "")
            if server:
                findings.append({
                    "type": "Server Fingerprint",
                    "severity": "Low",
                    "agent": self.name,
                    "server": server,
                    "analysis": f"Server header: {server}. Exposes version info."
                })

        except Exception as e:
            findings.append({"type": "CVE scan error", "severity": "Error", "agent": self.name, "error": str(e)})

        total = len(findings)
        analysis = f"CVE analysis: {total} software components identified.\n"
        for f in findings:
            if f.get("software"):
                analysis += f"- {f['software']} v{f['version']} — check for known vulnerabilities\n"

        if total > 0:
            result = self.analyzer.analyze_endpoint(url, analysis=analysis)
        else:
            result = {"analysis": "No versioned software detected."}

        result["real_findings"] = findings
        result["agent"] = self.name
        result["type"] = "CVE Detection"
        result["severity"] = "Low" if total > 1 else "Info"
        return result
