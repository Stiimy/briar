"""Git & Backup Finder Agent — exposed sensitive files 🔍"""
from briar.agents.analyzer import SecurityAnalyzer
from briar.core.http import HTTPClient

class GitBackupAgent:
    """Scans for exposed .git, .env, backup files, and other sensitive paths."""

    SENSITIVE_PATHS = [
        ("/.git/HEAD", "Git repository exposed"),
        ("/.git/config", "Git config exposed"),
        ("/.env", "Environment file exposed"),
        ("/.env.local", "Local env exposed"),
        ("/.env.production", "Production env exposed"),
        ("/backup.zip", "Backup archive exposed"),
        ("/backup.tar.gz", "Backup archive exposed"),
        ("/backup.sql", "Database backup exposed"),
        ("/dump.sql", "SQL dump exposed"),
        ("/db.sql", "Database export exposed"),
        ("/wp-config.php.bak", "WordPress backup"),
        ("/config.php.bak", "Config backup"),
        ("/robots.txt", "Robots (info disclosure)"),
        ("/sitemap.xml", "Sitemap (info disclosure)"),
        ("/.gitignore", "Git ignore exposed"),
        ("/.htaccess", "htaccess exposed"),
        ("/phpinfo.php", "PHP info exposed"),
        ("/server-status", "Apache status exposed"),
        ("/crossdomain.xml", "Flash crossdomain"),
        ("/web.config", "IIS config exposed"),
        ("/package.json", "npm packages exposed"),
        ("/composer.json", "PHP dependencies"),
        ("/Gemfile", "Ruby dependencies"),
        ("/Dockerfile", "Docker config exposed"),
        ("/docker-compose.yml", "Docker compose exposed"),
        ("/README.md", "Readme exposure"),
        ("/CHANGELOG.md", "Changelog exposure"),
    ]

    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.http = HTTPClient(timeout=6)
        self.name = "GitBackup"

    def scan(self, url: str, **kwargs) -> dict:
        findings = []
        base = url.rstrip("/")

        for path, desc in self.SENSITIVE_PATHS[:20]:
            try:
                full_url = base + path
                resp = self.http.get(full_url)
                if resp.status_code in [200, 301, 302, 403]:
                    sev = "High"
                    if "backup" in path.lower() or ".env" in path.lower():
                        sev = "Critical"
                    elif path in ["/robots.txt", "/sitemap.xml", "/README.md"]:
                        sev = "Low"

                    findings.append({
                        "type": f"Exposed: {desc}",
                        "severity": sev,
                        "agent": self.name,
                        "path": path,
                        "status": resp.status_code,
                        "confirmed": resp.status_code == 200,
                    })
            except:
                pass

        total = len(findings)
        analysis = f"Backup & sensitive file scan: {total} exposed files found.\n"
        for f in findings:
            analysis += f"- [{f['severity']}] {f['path']}: {f['type']} (HTTP {f['status']})\n"

        if total > 0:
            result = self.analyzer.analyze_endpoint(url, analysis=analysis)
        else:
            result = {"analysis": "No exposed sensitive files detected."}

        result["real_findings"] = findings
        result["agent"] = self.name
        result["type"] = "Sensitive Files"
        result["severity"] = "Critical" if any(f["severity"] == "Critical" for f in findings) else ("High" if findings else "Info")
        return result
