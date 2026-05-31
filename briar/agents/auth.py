"""Authentication Attack Agent — JWT, brute force, token analysis 🔐"""
import re
from briar.agents.analyzer import SecurityAnalyzer
from briar.core.http import HTTPClient

class AuthAgent:
    """Discovers authentication vulnerabilities"""

    WEAK_CREDS = [
        ("admin", "admin"), ("admin", "password"), ("admin", "123456"),
        ("test", "test"), ("guest", "guest"), ("user", "user"),
        ("root", "root"), ("admin", ""), ("administrator", "administrator"),
    ]

    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.http = HTTPClient(timeout=10)
        self.name = "Authentication"

    def _detect_login_form(self, html: str) -> list:
        """Find login forms by looking for password inputs"""
        login_forms = []
        forms = self.http.extract_forms(html)
        for form in forms:
            if any("pass" in i.lower() for i in form["inputs"]):
                login_forms.append(form)
        return login_forms

    def _test_jwt(self, jwt_str: str) -> list:
        """Test JWT for common vulnerabilities"""
        import base64, json
        findings = []
        try:
            parts = jwt_str.split(".")
            if len(parts) != 3:
                return findings

            # Decode without verification
            for i, part in enumerate(parts[:2]):
                # Add padding
                padded = part + "=" * (4 - len(part) % 4)
                try:
                    decoded = base64.urlsafe_b64decode(padded)
                    findings.append({
                        "type": "JWT decoded without verification",
                        "severity": "Low",
                        "part": "header" if i == 0 else "payload",
                        "content": decoded.decode("utf-8", errors="replace")[:200],
                    })
                except:
                    pass

            # Check alg:none
            header = parts[0]
            padded = header + "=" * (4 - len(header) % 4)
            decoded_header = base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")
            if '"none"' in decoded_header.lower() or '"None"' in decoded_header:
                findings.append({
                    "type": "JWT alg:none accepted",
                    "severity": "Critical",
                    "detail": "Algorithm allows 'none' — signature bypass possible",
                })

        except:
            pass
        return findings

    def scan(self, url: str, auth_type: str = "unknown", **kwargs) -> dict:
        """Scan for authentication vulnerabilities"""
        findings = []

        try:
            resp = self.http.get(url)
            html = resp.text

            # Check for JWT in cookies/headers
            jwt_pattern = r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'
            for header_val in resp.headers.values():
                for match in re.finditer(jwt_pattern, header_val):
                    jwt_findings = self._test_jwt(match.group(0))
                    findings.extend(jwt_findings)
            for match in re.finditer(jwt_pattern, resp.text[:2000]):
                jwt_findings = self._test_jwt(match.group(0))
                findings.extend(jwt_findings)

            # Find login forms and test weak creds
            login_forms = self._detect_login_form(html)
            for form in login_forms:
                form_url = form["action"] or url
                for username, password in self.WEAK_CREDS[:5]:
                    try:
                        data = {}
                        for inp in form["inputs"]:
                            if "user" in inp.lower() or "email" in inp.lower() or "login" in inp.lower():
                                data[inp] = username
                            elif "pass" in inp.lower():
                                data[inp] = password
                            else:
                                data[inp] = username

                        login_resp = self.http.post(form_url, data=data, allow_redirects=False)
                        if login_resp.status_code in [302, 200]:
                            # Check if login succeeded (no error message, redirect to dashboard)
                            text_lower = login_resp.text.lower()
                            if not any(e in text_lower for e in ["invalid", "incorrect", "wrong", "error", "failed"]):
                                findings.append({
                                    "type": "Weak credentials",
                                    "severity": "Critical",
                                    "endpoint": form_url,
                                    "credentials": f"{username}:{password}",
                                    "response_status": login_resp.status_code,
                                })
                                break
                    except:
                        pass

                if findings:
                    break  # Found vuln, stop brute force

            if not login_forms:
                findings.append({"type": "No login form found", "severity": "Info"})

        except Exception as e:
            findings.append({"type": "Auth scan error", "error": str(e)})

        analysis = f"Authentication scan complete for {url}\n\n"
        if findings:
            analysis += f"**{len(findings)} authentication issues found:**\n\n"
            for f in findings:
                if "credential" in str(f.get("type", "")).lower():
                    analysis += f"- **Weak credentials**: `{f.get('credentials','?')}` → {f.get('endpoint','?')}\n"
                elif "jwt" in str(f.get("type", "")).lower():
                    analysis += f"- **{f['type']}**: {f.get('detail', f.get('content',''))}\n"
            analysis += "\n---\n\nLLM analysis of auth findings:\n"

        result = self.analyzer.analyze_endpoint(url, "GET/POST", tech_context=tech_context, source_hint= analysis)
        result["real_findings"] = findings
        result["agent"] = self.name
        result["type"] = "Authentication"
        result["severity"] = "Critical" if any(f.get("severity","") == "Critical" for f in findings) else ("High" if findings else "Info")
        return result
