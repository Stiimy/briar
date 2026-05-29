"""Reconnaissance Agent — attack surface mapping 🔍"""
import requests
from urllib.parse import urlparse, urljoin

class ReconAgent:
    """Maps the attack surface of a target"""
    
    def __init__(self, provider="ollama"):
        self.name = "Recon"
    
    def scan(self, url: str, **kwargs) -> dict:
        """Discover endpoints, technologies, headers"""
        info = {
            "url": url,
            "agent": self.name,
            "type": "Reconnaissance",
            "severity": "Info",
        }
        
        try:
            resp = requests.get(url, timeout=10, allow_redirects=True)
            info["status"] = resp.status_code
            info["headers"] = dict(resp.headers)
            info["server"] = resp.headers.get("Server", "Unknown")
            
            # Technology detection
            tech = []
            body = resp.text[:5000].lower()
            if "react" in body or "__NEXT_DATA__" in body: tech.append("React/Next.js")
            if "vue" in body or "nuxt" in body: tech.append("Vue/Nuxt")
            if "wp-content" in body: tech.append("WordPress")
            if "laravel" in body: tech.append("Laravel")
            if "django" in body: tech.append("Django")
            if "express" in body: tech.append("Express.js")
            if "nginx" in resp.headers.get("Server",""): tech.append("Nginx")
            if "apache" in resp.headers.get("Server",""): tech.append("Apache")
            info["technologies"] = tech or ["Unknown"]
            
            # Security headers check
            security_headers = {
                "Strict-Transport-Security": resp.headers.get("Strict-Transport-Security"),
                "Content-Security-Policy": resp.headers.get("Content-Security-Policy"),
                "X-Frame-Options": resp.headers.get("X-Frame-Options"),
                "X-Content-Type-Options": resp.headers.get("X-Content-Type-Options"),
            }
            info["security_headers"] = {k: v or "MISSING" for k, v in security_headers.items()}
            
            # Find links/endpoints
            import re
            links = re.findall(r'href=["\']([^"\']+)["\']', resp.text)
            links += re.findall(r'src=["\']([^"\']+)["\']', resp.text)
            info["endpoints_discovered"] = len(set(links))
            info["urls_sample"] = list(set(links))[:5]
            
            info["analysis"] = f"""Reconnaissance complete for {url}

Server: {info['server']}
Technologies: {', '.join(info['technologies'])}
Endpoints discovered: {info['endpoints_discovered']}

Security Headers:
""" + "\n".join(f"  {k}: {v}" for k, v in info["security_headers"].items())
            
        except Exception as e:
            info["error"] = str(e)
            info["analysis"] = f"Recon failed: {e}"
        
        return info
