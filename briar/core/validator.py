"""Briar Exploit Validator — rejoue les findings pour confirmer ou jeter 🎯"""
from briar.core.http import HTTPClient

class ExploitValidator:
    """Replays payloads to confirm findings before reporting them.
    
    Shannon-style: no exploit, no report.
    """

    def __init__(self):
        self.http = HTTPClient(timeout=10)
        self.results = []

    def validate(self, finding: dict, url: str) -> dict:
        """Replay a finding's payload and confirm reproducibility."""
        param = finding.get("param")
        payload = finding.get("payload")
        if not param or not payload:
            return {**finding, "confirmed": False, "replay_reason": "no_param_or_payload"}

        # Replay the exact payload
        try:
            resp = self.http.send_payload(url, param, payload)
            if "error" in resp:
                return {**finding, "confirmed": False, "replay_reason": f"http_error: {resp['error']}"}

            # Build curl PoC
            poc = self._build_curl(url, param, payload, finding.get("method", "GET"))
            finding["poc"] = poc
            finding["replay_status"] = resp["status"]
            finding["replay_length"] = resp["length"]
            finding["confirmed"] = True

        except Exception as e:
            finding["confirmed"] = False
            finding["replay_reason"] = str(e)

        return finding

    def validate_all(self, findings: list, url: str) -> list:
        """Validate all findings, flagging unconfirmed ones."""
        validated = []
        for f in findings:
            sev = f.get("severity", "Info")

            # Only re-validate High/Critical findings (Info/Low don't need PoC)
            if sev in ("Critical", "High") and f.get("payload") and f.get("param"):
                v = self.validate(f, url)
                if not v.get("confirmed"):
                    # Downgrade unconfirmed findings
                    v["severity"] = "Low"
                    v["type"] = f"{v.get('type', '?')} ⚠️"
                    v["analysis"] = (v.get("analysis", "") +
                        f"\n\n⚠️ UNABLE TO REPRODUCE: {v.get('replay_reason', 'unknown')}")
                validated.append(v)
            else:
                # Info/Low or no payload — keep as is
                validated.append(f)

        self.results = validated
        return validated

    def _build_curl(self, url: str, param: str, payload: str, method: str = "GET") -> str:
        """Generate copy-paste curl command for PoC."""
        from urllib.parse import quote
        encoded = quote(payload, safe='')
        if method.upper() == "GET":
            return f"curl -s '{url}?{param}={encoded}'"
        elif method.upper() == "POST":
            return f"curl -s -X POST '{url}' -d '{param}={encoded}'"
        return f"curl -s -X {method} '{url}?{param}={encoded}'"

    def summary(self) -> str:
        """Return a summary of validation results."""
        total = len(self.results)
        confirmed = sum(1 for r in self.results if r.get("confirmed"))
        unconfirmed = total - confirmed
        return f"Validated {total} findings: {confirmed} confirmed, {unconfirmed} unconfirmed (downgraded)"
