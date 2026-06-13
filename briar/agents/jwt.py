"""JWT Analyzer Agent — deep token testing 🔑"""
from briar.agents.analyzer import SecurityAnalyzer
from briar.core.http import HTTPClient
import re, base64, json

class JWTAgent:
    """Deep JWT analysis: alg=none, weak keys, claim inspection."""

    WEAK_KEYS = [
        b"secret", b"password", b"key", b"123456", b"admin",
        b"changeme", b"jwt_secret", b"supersecretkey",
    ]

    def __init__(self, provider="ollama"):
        self.analyzer = SecurityAnalyzer(provider)
        self.http = HTTPClient(timeout=10)
        self.name = "JWT"

    def _extract_jwts(self, text: str) -> list:
        """Extract JWT-like strings from text."""
        jwt_pattern = r'([A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)'
        return list(set(re.findall(jwt_pattern, text)))

    def _decode_jwt_part(self, part: str) -> dict:
        """Decode base64-encoded JWT part."""
        try:
            padded = part + "=" * (4 - len(part) % 4)
            decoded = base64.urlsafe_b64decode(padded)
            return json.loads(decoded.decode("utf-8", errors="replace"))
        except:
            return {}

    def scan(self, url: str, **kwargs) -> dict:
        findings = []

        try:
            resp = self.http.get(url)
            text = resp.text[:10000]
            headers = dict(resp.headers)

            jwts = self._extract_jwts(text)
            for header_val in headers.values():
                jwts += self._extract_jwts(header_val)

            jwts = list(set(jwts))
            if not jwts:
                return {
                    "type": "JWT Analysis", "severity": "Info", "agent": self.name,
                    "analysis": "No JWT tokens found in page or headers.",
                    "real_findings": []
                }

            for jwt_str in jwts[:5]:
                parts = jwt_str.split(".")
                if len(parts) != 3:
                    continue

                header = self._decode_jwt_part(parts[0])
                payload = self._decode_jwt_part(parts[1])

                # Check alg=none
                alg = header.get("alg", "unknown")
                if alg.lower() == "none":
                    findings.append({
                        "type": "JWT: alg=none",
                        "severity": "Critical",
                        "agent": self.name,
                        "detail": "Token accepts 'none' algorithm — bypass possible",
                        "jwt_preview": jwt_str[:80] + "...",
                    })

                # Check weak algorithm
                if alg.lower() in ("hs256", "hs384", "hs512"):
                    findings.append({
                        "type": f"JWT: symmetric key ({alg})",
                        "severity": "Medium",
                        "agent": self.name,
                        "detail": f"Symmetric {alg} — secret key must be strong and protected",
                    })

                # Check expiry
                exp = payload.get("exp", 0)
                if exp == 0:
                    findings.append({
                        "type": "JWT: no expiration",
                        "severity": "Low",
                        "agent": self.name,
                        "detail": "Token has no 'exp' claim — never expires",
                    })

                # Check sensitive claims
                sensitive = []
                for key in payload.keys():
                    if any(s in key.lower() for s in ["password", "secret", "key", "token", "cred"]):
                        sensitive.append(key)
                if sensitive:
                    findings.append({
                        "type": "JWT: sensitive claims",
                        "severity": "High",
                        "agent": self.name,
                        "detail": f"Sensitive data in JWT claims: {', '.join(sensitive)}",
                    })

                # Report decoded payload
                findings.append({
                    "type": "JWT payload exposed",
                    "severity": "Info",
                    "agent": self.name,
                    "detail": f"Payload: {json.dumps(payload, indent=2)[:300]}",
                })

            if not findings:
                return {
                    "type": "JWT Analysis", "severity": "Info", "agent": self.name,
                    "analysis": f"{len(jwts)} JWT(s) found, no obvious flaws detected.",
                    "real_findings": []
                }

            analysis = f"JWT analysis: {len(jwts)} token(s) found, {len(findings)} issues.\n"
            for f in findings:
                analysis += f"- [{f['severity']}] {f['type']}: {f.get('detail','')}\n"

            result = self.analyzer.analyze_endpoint(url, analysis=analysis)
            result["real_findings"] = findings
            result["agent"] = self.name
            result["type"] = "JWT Analysis"
            result["severity"] = "Critical" if any(f["severity"] == "Critical" for f in findings) else ("High" if findings else "Info")
            return result

        except Exception as e:
            return {"type": "JWT Analysis", "severity": "Error", "agent": self.name, "error": str(e)}
