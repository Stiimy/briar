"""Briar AI Analysis Engine — the brain of the pentest 🧠"""
from typing import Optional
from briar.providers import get_provider

SECURITY_ANALYST_PROMPT = """You are an elite penetration tester. Analyze the target and provide actionable findings.

For EACH vulnerability found, you MUST provide ALL 8 sections below. Do NOT skip any section.

## 1. VULNERABILITY TYPE
OWASP category (e.g. A01:2021 Broken Access Control)

## 2. SEVERITY & CVSS
Critical / High / Medium / Low + CVSS 3.1 score (0.0-10.0)

## 3. ENDPOINT / LOCATION
Exact URL, HTTP method, vulnerable parameter name

## 4. DESCRIPTION
What the vulnerability is, why it exists, how it can be found

## 5. EXPLOIT STEPS
Copy-paste ready commands (curl, Python, browser). MUST include exact URLs, payloads, headers. 
At least 3 different exploitation techniques per vulnerability.

## 6. IMPACT
What an attacker achieves: data exposure, RCE, privilege escalation, etc.
Quantify: "can read all user passwords", "can execute commands as root", etc.

## 7. REMEDIATION — TECHNOLOGY-SPECIFIC
CRITICAL: Provide remediation SPECIFIC to the technology stack detected.
- If nginx: show nginx config directives
- If Apache: show .htaccess or httpd.conf rules
- If gunicorn/Python: show Flask/Django middleware code
- If Node.js/Express: show npm packages + middleware
- If PHP: show php.ini settings + code fixes
- If React/Next.js: show next.config.js settings + server-side validation
- If WordPress: show wp-config.php changes + security plugins

Each remediation MUST include:
a) Configuration change (exact file + directive)
b) Code fix (if applicable — copy-paste ready)
c) Verification command to test the fix worked

## 8. REFERENCES
OWASP cheat sheet URL, CWE ID, relevant CVEs if applicable.

---
RULES:
- Never say "implement proper validation" without showing the EXACT code
- Never say "configure the firewall" without the EXACT rule/command
- Every remediation must be COPY-PASTE READY
- Include verification: "After applying this fix, run <command> to verify"
"""

TECH_REMEDIATION_TEMPLATES = {
    "nginx": """For nginx, add to server block:
```nginx
# Prevent path traversal
location ~ \.\./ { deny all; }
# Limit file access
location /files/ {
    root /var/www/uploads;
    internal;  # blocks direct external access
}
```""",
    "apache": """For Apache, add to .htaccess or httpd.conf:
```apache
# Prevent path traversal
RewriteEngine On
RewriteCond %{REQUEST_URI} \.\./
RewriteRule .* - [F]
# Disable directory listing
Options -Indexes
```""",
    "gunicorn": """For gunicorn/Python, add to your app:
```python
from werkzeug.utils import secure_filename
from pathlib import Path
import os

UPLOAD_DIR = Path("/var/www/uploads").resolve()
def safe_serve(filename):
    filepath = (UPLOAD_DIR / filename).resolve()
    if not str(filepath).startswith(str(UPLOAD_DIR)):
        raise ValueError("Path traversal blocked")
    return filepath
```""",
    "flask": """For Flask:
```python
from flask import send_from_directory
@app.route('/files/<path:filename>')
def serve_file(filename):
    return send_from_directory('/var/www/uploads', filename)
```""",
    "express": """For Express.js:
```javascript
const path = require('path');
const helmet = require('helmet');
app.use(helmet());
app.use('/files', express.static('/var/www/uploads', {dotfiles: 'deny'}));
```""",
    "php": """For PHP, in php.ini:
```ini
open_basedir = /var/www:/tmp
allow_url_fopen = Off
disable_functions = exec,passthru,shell_exec,system,proc_open,popen
```
In your file handler:
```php
$base = realpath('/var/www/uploads');
$file = realpath($base . '/' . $_GET['file']);
if (strpos($file, $base) !== 0) { die('Blocked'); }
```""",
    "wordpress": """For WordPress, in wp-config.php:
```php
define('DISALLOW_FILE_EDIT', true);
define('FORCE_SSL_ADMIN', true);
```
Install & configure: Wordfence Security or iThemes Security plugin.""",
}

def build_tech_context(recon_finding: Optional[dict] = None) -> str:
    """Build technology context string from reconnaissance data."""
    if not recon_finding:
        return ""
    server = recon_finding.get("server", "Unknown")
    techs = recon_finding.get("technologies", [])
    headers = recon_finding.get("security_headers", {})

    context = f"\n\n## TARGET TECHNOLOGY STACK (detected by reconnaissance):\n"
    context += f"- Server: {server}\n"
    if techs:
        context += f"- Frameworks: {', '.join(techs)}\n"
    context += f"- Missing security headers: {', '.join(k for k,v in headers.items() if v=='MISSING')}\n"
    context += "\nREMEDIATION MUST target this EXACT stack. Use the specific config/code for this technology.\n"

    # Add template for detected tech
    server_lower = server.lower()
    for tech_key in ["nginx", "apache", "gunicorn", "flask", "express", "php", "wordpress"]:
        if tech_key in server_lower or any(tech_key in t.lower() for t in techs):
            context += f"\nApply {tech_key}-specific fixes. Example pattern:\n"
            context += TECH_REMEDIATION_TEMPLATES.get(tech_key, "")
            break

    return context

class SecurityAnalyzer:
    """Core AI security analysis engine"""

    def __init__(self, provider: str = "ollama", model: Optional[str] = None):
        self.provider = get_provider(provider, model=model) if model else get_provider(provider)

    def analyze_endpoint(self, url: str, method: str = "GET", source_hint: str = "",
                         tech_context: str = "") -> dict:
        """Analyze a single endpoint for vulnerabilities."""
        prompt = f"""Analyze this endpoint for security vulnerabilities:

URL: {url}
Method: {method}
{f'Source code context: {source_hint}' if source_hint else ''}
{tech_context}

REQUIREMENT: For each vulnerability, provide COPY-PASTE READY remediation specific to the technology stack.
Include exact nginx/Apache/gunicorn/Flask/Express/PHP config, exact code fixes, and verification commands.
"""
        messages = [{"role": "user", "content": prompt}]
        response = self.provider.chat(messages, system=SECURITY_ANALYST_PROMPT, max_tokens=4096)
        return {"url": url, "analysis": response, "raw": response}

    def analyze_code(self, code: str, filepath: str = "") -> dict:
        prompt = f"""Analyze this source code for vulnerabilities:

File: {filepath}

```
{code[:8000]}
```

Find: SQL injection, XSS, SSRF, command injection, path traversal, auth bypass,
deserialization, hardcoded secrets, unsafe eval, etc.

For each finding, specify the exact line and how to exploit it."""
        messages = [{"role": "user", "content": prompt}]
        response = self.provider.chat(messages, system=SECURITY_ANALYST_PROMPT, max_tokens=4096)
        return {"file": filepath, "analysis": response}

    def generate_report(self, findings: list, target: str) -> str:
        findings_text = "\n\n---\n\n".join([
            f"## Finding {i+1}\n{f.get('analysis', f.get('raw',''))}"
            for i, f in enumerate(findings)
        ])
        prompt = f"""Generate a PROFESSIONAL penetration test report for {target}.

Findings:
{findings_text[:6000]}

Create a structured report with:
1. Executive Summary
2. Methodology
3. Findings (detailed per vulnerability)
4. Risk Matrix
5. Recommendations
6. Conclusion

Format in Markdown. Be professional and precise."""
        messages = [{"role": "user", "content": prompt}]
        return self.provider.chat(messages, system="You are a senior security consultant writing a pentest report.", max_tokens=8192)
