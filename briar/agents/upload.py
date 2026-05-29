"""File Upload Attack Agent — real upload testing 📁"""
import os, tempfile
from briar.agents.analyzer import SecurityAnalyzer
from briar.core.http import HTTPClient

class UploadAgent:
    """Detects file upload vulnerabilities with real upload attempts"""

    TEST_FILES = [
        ("test.php", "application/x-php", b"<?php echo 'BRIAR_TEST'; ?>", "php_webshell"),
        ("test.php.jpg", "image/jpeg", b"<?php echo 'BRIAR_TEST'; ?>", "double_extension"),
        ("test.php5", "application/x-php", b"<?php echo 'BRIAR_TEST'; ?>", "alt_php_ext"),
        ("test.svg", "image/svg+xml", b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>', "svg_xss"),
        ("test.phtml", "application/x-php", b"<?php echo 'BRIAR_TEST'; ?>", "phtml"),
        ("test.html", "text/html", b"<script>alert(1)</script>", "html_xss"),
    ]

    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.http = HTTPClient(timeout=10)
        self.name = "FileUpload"

    def scan(self, url: str, **kwargs) -> dict:
        """Scan for file upload vulnerabilities"""
        findings = []
        upload_forms = []

        try:
            resp = self.http.get(url)
            html = resp.text
            forms = self.http.extract_forms(html)
            upload_forms = [f for f in forms if f["has_upload"]]

            for form in upload_forms:
                form_url = form["action"] or url
                for filename, mime, content, test_type in self.TEST_FILES[:4]:
                    try:
                        tmp = tempfile.NamedTemporaryFile(suffix=f"_{filename}", delete=False)
                        tmp.write(content)
                        tmp.close()

                        with open(tmp.name, "rb") as f:
                            files = {"file": (filename, f, mime)}
                            upload_resp = self.http.post(form_url, files=files)

                        os.unlink(tmp.name)

                        if upload_resp.status_code in [200, 201, 302]:
                            findings.append({
                                "type": f"File Upload — {test_type} accepted",
                                "severity": "Critical" if "php" in test_type else "High",
                                "form_action": form_url,
                                "filename": filename,
                                "mime_type": mime,
                                "upload_status": upload_resp.status_code,
                            })
                    except:
                        pass

            if not upload_forms:
                findings.append({
                    "type": "File Upload — no upload forms found",
                    "severity": "Info",
                })

        except Exception as e:
            findings.append({"type": "Upload scan error", "error": str(e)})

        analysis = f"File upload scan complete for {url}\n\n"
        analysis += f"Upload forms found: {len(upload_forms)}\n\n"
        if any("accepted" in str(f.get("type","")) for f in findings):
            analysis += f"**{len([f for f in findings if 'accepted' in str(f.get('type',''))])} dangerous files accepted:**\n\n"
            for f in findings:
                if "accepted" in str(f.get("type", "")):
                    analysis += f"- **{f['filename']}** ({f['mime_type']}) uploaded to `{f['form_action']}` — {f['upload_status']}\n"
            analysis += "\n---\n\nLLM analysis of real upload findings:\n"
        else:
            analysis += "No dangerous file uploads detected.\n\nLLM analysis:\n"

        result = self.analyzer.analyze_endpoint(url, "POST", analysis)
        result["real_findings"] = findings
        result["agent"] = self.name
        result["type"] = "File Upload"
        result["severity"] = "Critical" if any("php" in str(f.get("type","")) for f in findings) else ("High" if findings else "Info")
        return result
