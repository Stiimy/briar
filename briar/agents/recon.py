"""Reconnaissance Agent — attack surface mapping + port scanning 🔍"""
import re, socket
import requests
from urllib.parse import urlparse, urljoin

COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 143, 443, 465, 587, 993, 995,
                1433, 1521, 3306, 3389, 5432, 6379, 8080, 8443, 9000, 27017]

PORT_SERVICES = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 465: "SMTPS",
    587: "SMTP", 993: "IMAPS", 995: "POP3S", 1433: "MSSQL", 1521: "Oracle",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 6379: "Redis",
    8080: "HTTP-Alt", 8443: "HTTPS-Alt", 9000: "PHP-FPM", 27017: "MongoDB"
}

class ReconAgent:
    """Maps the attack surface of a target"""
    
    def __init__(self, provider="ollama"):
        self.name = "Recon"
    
    def port_scan(self, hostname: str, ports: list = None, timeout: float = 1.5) -> list:
        """TCP connect scan on common ports"""
        if ports is None:
            ports = COMMON_PORTS
        open_ports = []
        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((hostname, port))
            if result == 0:
                service = PORT_SERVICES.get(port, "Unknown")
                open_ports.append({"port": port, "service": service})
            sock.close()
        return open_ports
    
    def scan(self, url: str, **kwargs) -> dict:
        """Discover endpoints, technologies, headers, open ports"""
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
            links = re.findall(r'href=["\']([^"\']+)["\']', resp.text)
            links += re.findall(r'src=["\']([^"\']+)["\']', resp.text)
            info["endpoints_discovered"] = len(set(links))
            info["urls_sample"] = list(set(links))[:5]
            
            # Port scanning
            hostname = urlparse(url).hostname
            open_ports = []
            if hostname:
                open_ports = self.port_scan(hostname)
            info["open_ports"] = open_ports
            
            info["analysis"] = f"""Reconnaissance complete for {url}

Server: {info['server']}
Technologies: {', '.join(info['technologies'])}
Endpoints discovered: {info['endpoints_discovered']}

Security Headers:
""" + "\n".join(f"  {k}: {v}" for k, v in info["security_headers"].items()) + f"""

Open Ports ({len(open_ports)}):
""" + ("\n".join(f"  {p['port']}/tcp - {p['service']}" for p in open_ports) if open_ports else "  No open ports detected")
            
        except Exception as e:
            info["error"] = str(e)
            info["analysis"] = f"Recon failed: {e}"
        
        return info
