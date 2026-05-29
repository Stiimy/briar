"""Briar HTTP Client — shared request engine for all agents 🌐"""
import re
import time
import requests
from urllib.parse import urlparse, parse_qs, urljoin, urlencode

class HTTPClient:
    """Shared HTTP utilities for all security agents"""

    def __init__(self, timeout: int = 10):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Briar/0.3 Pentest Scanner (https://github.com/Stiimy/briar)"
        })
        self.timeout = timeout

    def get(self, url: str, params: dict = None, **kwargs) -> requests.Response:
        return self.session.get(url, params=params, timeout=self.timeout, **kwargs)

    def post(self, url: str, data: dict = None, json: dict = None, files: dict = None, **kwargs) -> requests.Response:
        return self.session.post(url, data=data, json=json, files=files, timeout=self.timeout, **kwargs)

    def send_payload(self, url: str, param: str, payload: str, method: str = "GET") -> dict:
        """Send a payload via GET or POST and return response metadata"""
        try:
            if method.upper() == "GET":
                resp = self.get(url, params={param: payload})
            else:
                resp = self.post(url, data={param: payload})
            return {
                "status": resp.status_code,
                "length": len(resp.text),
                "time": resp.elapsed.total_seconds(),
                "text_snippet": resp.text[:500],
                "headers": dict(resp.headers),
                "payload": payload,
                "param": param,
            }
        except Exception as e:
            return {"error": str(e), "payload": payload, "param": param}

    def extract_params(self, html: str) -> list:
        """Extract input parameter names from HTML forms"""
        params = set()
        # <input name="xxx">
        params.update(re.findall(r'<input[^>]+name=["\']([^"\']+)["\']', html, re.I))
        # URL query params in href/src
        for url in re.findall(r'(?:href|src|action)=["\']([^"\']+)["\']', html, re.I):
            parsed = urlparse(url)
            params.update(parse_qs(parsed.query).keys())
        return list(params)

    def extract_forms(self, html: str) -> list:
        """Extract form metadata: action, method, inputs"""
        forms = []
        for form_match in re.finditer(r'<form[^>]*>.*?</form>', html, re.I | re.DOTALL):
            form_html = form_match.group(0)
            action = re.search(r'action=["\']([^"\']*)["\']', form_html, re.I)
            method = re.search(r'method=["\']([^"\']*)["\']', form_html, re.I)
            inputs = re.findall(r'<input[^>]+name=["\']([^"\']+)["\']', form_html, re.I)
            uploads = bool(re.search(r'type=["\']file["\']', form_html, re.I))
            csrf = any('csrf' in i.lower() or 'token' in i.lower() or 'nonce' in i.lower() for i in inputs)
            forms.append({
                "action": urljoin("", action.group(1)) if action else "",
                "method": (method.group(1) or "GET").upper() if method else "GET",
                "inputs": inputs,
                "has_upload": uploads,
                "has_csrf_token": csrf,
            })
        return forms

    def has_reflection(self, response_text: str, payload: str) -> bool:
        """Check if a payload is reflected in the response (for XSS detection)"""
        # Check if payload appears unescaped
        if payload in response_text:
            return True
        # Check URL-decoded version
        from urllib.parse import unquote
        if unquote(payload) in unquote(response_text):
            return True
        return False

    def detect_error(self, response_text: str, error_patterns: list = None) -> str:
        """Detect database/application errors in response"""
        if error_patterns is None:
            error_patterns = [
                r"SQL syntax.*?error", r"mysql_fetch", r"ORA-[0-9]{5}",
                r"PostgreSQL.*?ERROR", r"Warning.*?mysql_", r"Unclosed quotation",
                r"Microsoft OLE DB", r"ODBC Driver", r"SQLite.*?error",
                r"Traceback \(most recent call last\)", r"Fatal error",
                r"stack trace:", r"Exception in thread",
            ]
        for pattern in error_patterns:
            if re.search(pattern, response_text, re.I):
                return pattern
        return ""

    def detect_time_based(self, response_time: float, baseline: float = 0.5, threshold: float = 3.0) -> bool:
        """Detect time-based injection (response took significantly longer)"""
        return response_time > max(baseline * 3, threshold)

    def detect_file_content(self, response_text: str) -> str:
        """Detect if response contains file contents (path traversal success)"""
        markers = [
            ("root:", "/etc/passwd"), ("/bin/bash", "/etc/passwd"),
            ("[extensions]", "php.ini"), ("mysql_connect", "PHP config"),
            ("DB_CONNECTION", ".env file"),
        ]
        for marker, file_type in markers:
            if marker in response_text:
                return file_type
        return ""

    def close(self):
        self.session.close()
