"""Briar Obsidian LLM-Wiki Generator — persistent, compounding knowledge base 📓
Inspired by Karpathy's LLM-Wiki pattern: incremental, interlinked, LLM-maintained.
"""
import os, json, re
from datetime import datetime

class ObsidianGenerator:
    """Generates an interlinked Obsidian vault that grows with every scan."""

    def __init__(self, target: str, findings: list, output_dir: str = "./reports/obsidian"):
        self.target = target
        self.findings = findings
        self.output_dir = output_dir
        self.target_slug = target.replace("://", "_").replace("/", "_").replace(":", "_").replace(".", "_")[:50]
        self.scan_date = datetime.now().strftime('%Y-%m-%d')
        self.scan_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        self.scan_id = datetime.now().strftime('%Y%m%d%H%M%S')
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "findings"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "endpoints"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "scans"), exist_ok=True)

    def generate(self) -> str:
        """Generate the full LLM-Wiki structure."""
        self._generate_findings()
        self._generate_index()
        self._generate_log()
        self._generate_overview()
        self._generate_endpoints()
        self._generate_canvas()
        self._generate_scan_report()
        return self.output_dir

    def _severity_color(self, sev: str) -> str:
        return {"Critical":"1","High":"2","Medium":"3","Low":"4"}.get(sev, "0")

    def _severity_emoji(self, sev: str) -> str:
        return {"Critical":"🔴","High":"🟠","Medium":"🟡","Low":"🟢"}.get(sev, "⚪")

    def _frontmatter(self, **fields) -> str:
        lines = ["---"]
        for k, v in fields.items():
            if isinstance(v, list):
                lines.append(f"{k}: [{', '.join(v)}]")
            elif isinstance(v, bool):
                lines.append(f"{k}: {str(v).lower()}")
            elif isinstance(v, str) and (' ' in v or '/' in v):
                lines.append(f'{k}: "{v}"')
            else:
                lines.append(f"{k}: {v}")
        lines.append("---\n")
        return "\n".join(lines)

    def _generate_findings(self):
        """Create one page per finding with full frontmatter."""
        for i, f in enumerate(self.findings):
            fid = f"FIN-{i+1:03d}"
            sev = f.get("severity", "Info")
            ftype = f.get("type", "Unknown")
            agent = f.get("agent", "?")
            endpoint = f.get("url", self.target)
            param = f.get("param", "")
            payload = f.get("payload", "")
            confirmed = f.get("confirmed", sev in ("Critical", "High"))
            poc = f.get("poc", "")
            analysis = f.get("analysis", f.get("raw", "No details available."))
            real_findings = f.get("real_findings", [])

            # Endpoint slug for linking
            endpoint_slug = endpoint.replace("://", "_").replace("/", "_")[:40]
            ftype_slug = ftype.lower().replace(" ", "_").replace("(", "").replace(")", "")[:30]

            fm = self._frontmatter(
                id=fid, severity=sev, type=ftype, agent=agent,
                endpoint=endpoint, param=param, payload=payload,
                confirmed=confirmed, date=self.scan_date, scan_id=self.scan_id,
                tags=[ftype_slug, sev.lower(), agent.lower(), "confirmed" if confirmed else "unconfirmed"]
            )

            # Build linked body
            body = f"# {fid}: {ftype}\n\n"
            body += f"**Severity:** {self._severity_emoji(sev)} {sev}\n\n"
            body += f"- **Type:** [[{ftype_slug}|{ftype}]]\n"
            body += f"- **Endpoint:** [[endpoints/{endpoint_slug}|{endpoint}]]\n"
            if param:
                body += f"- **Parameter:** `{param}`\n"
            if payload:
                body += f"- **Payload:** `{payload}`\n"
            if confirmed:
                body += f"- **Status:** ✅ Confirmed\n"
            else:
                body += f"- **Status:** ⚠️ Unconfirmed\n"
            if poc:
                body += f"- **PoC:** `{poc}`\n"

            body += f"\n---\n\n## Analysis\n\n{analysis}\n"

            # Cross-reference other findings sharing same endpoint
            related = [ff for ff in self.findings if ff != f and ff.get("url") == endpoint]
            if related:
                body += "\n## Related Findings\n\n"
                for ri, rf in enumerate(related):
                    rid = f"FIN-{list(self.findings).index(rf)+1:03d}"
                    body += f"- [[../findings/{rid}|{rid}: {rf.get('type','?')}]]\n"

            body += f"\n---\n*Scanned: {self.scan_time} | Scan: [[../scans/{self.scan_id}-scan|{self.scan_id}]]*"

            path = os.path.join(self.output_dir, "findings", f"{fid}.md")
            with open(path, "w") as ff:
                ff.write(fm + body)

    def _generate_index(self):
        """Generate or update the master index catalog."""
        # Try to load existing index
        index_path = os.path.join(self.output_dir, "index.md")
        existing = ""
        if os.path.exists(index_path):
            with open(index_path) as f:
                existing = f.read()

        # Build new scan section
        scan_section = f"\n## Scan {self.scan_id} — {self.scan_date}\n\n"
        scan_section += f"**Target:** {self.target}\n"
        scan_section += f"**Findings:** {len(self.findings)}\n\n"

        by_severity = {}
        for f in self.findings:
            sev = f.get("severity", "Info")
            by_severity.setdefault(sev, []).append(f)

        for sev in ["Critical", "High", "Medium", "Low", "Info"]:
            if sev in by_severity:
                scan_section += f"### {self._severity_emoji(sev)} {sev}\n\n"
                for f in by_severity[sev]:
                    i = list(self.findings).index(f) + 1
                    fid = f"FIN-{i:03d}"
                    ftype = f.get("type", "?")
                    scan_section += f"- [[findings/{fid}|{fid}]] {ftype} — {f.get('agent','?')}\n"
                scan_section += "\n"

        # Prepend to existing or create new
        if existing:
            # Insert after header
            header_end = existing.find("\n## ")
            if header_end > 0:
                content = existing[:header_end] + scan_section + existing[header_end:]
            else:
                content = existing + scan_section
        else:
            content = f"""---
title: Briar Security Wiki
date: {self.scan_date}
tags: [security, pentest, briar]
---

# 🥀 Briar Security Wiki

> *Living knowledge base — updated with every scan.*

## Quick Stats
- **Targets monitored:** 1
- **Total findings:** {len(self.findings)}
- **Last scan:** {self.scan_time}
- **Tool:** [[Briar]]

{scan_section}
"""

        with open(index_path, "w") as f:
            f.write(content)

    def _generate_log(self):
        """Append a chronological entry to the log."""
        log_path = os.path.join(self.output_dir, "log.md")
        entry = f"""## [{self.scan_date}] Scan — {self.target}

**Time:** {self.scan_time}
**Scan ID:** {self.scan_id}
**Agents run:** {len(set(f.get('agent','?') for f in self.findings))}
**Findings:** {len(self.findings)}
**Critical:** {sum(1 for f in self.findings if f.get('severity')=='Critical')}
**High:** {sum(1 for f in self.findings if f.get('severity')=='High')}
**Medium:** {sum(1 for f in self.findings if f.get('severity')=='Medium')}
**Low:** {sum(1 for f in self.findings if f.get('severity')=='Low')}

"""

        if os.path.exists(log_path):
            with open(log_path) as f:
                existing = f.read()
            # Insert after the title/first line
            lines = existing.split("\n", 2)
            if len(lines) > 2:
                content = lines[0] + "\n" + lines[1] + "\n\n" + entry + lines[2]
            else:
                content = existing + "\n" + entry
        else:
            content = f"# 📜 Scan Log\n\n{entry}"

        with open(log_path, "w") as f:
            f.write(content)

    def _generate_overview(self):
        """Generate executive overview with visualization data."""
        critical = sum(1 for f in self.findings if f.get("severity") == "Critical")
        high = sum(1 for f in self.findings if f.get("severity") == "High")
        medium = sum(1 for f in self.findings if f.get("severity") == "Medium")
        low = sum(1 for f in self.findings if f.get("severity") == "Low")
        confirmed = sum(1 for f in self.findings if f.get("confirmed", False))
        total = len(self.findings)
        agents = set(f.get("agent", "?") for f in self.findings)
        types = set(f.get("type", "?") for f in self.findings)

        content = f"""---
title: Security Overview
date: {self.scan_date}
target: {self.target}
scan_id: {self.scan_id}
---

# 🥀 Security Overview — {self.target}

> Generated: {self.scan_time} | Scan: [[scans/{self.scan_id}-scan|{self.scan_id}]]

## Executive Summary

Briar performed an autonomous security assessment targeting **{self.target}**.

| Metric | Value |
|--------|-------|
| 🔴 Critical | {critical} |
| 🟠 High | {high} |
| 🟡 Medium | {medium} |
| 🟢 Low | {low} |
| 📊 **Total** | **{total}** |
| ✅ Confirmed | {confirmed} |
| 🤖 Agents | {len(agents)} |
| 🏷️ Vuln Types | {len(types)} |

## Vulnerability Types Discovered

"""
        for t in sorted(types):
            content += f"- [[../vulns/{t.lower().replace(' ','_')}|{t}]]\n"

        content += f"\n## Reconnaissance Summary\n\n"
        recon = next((f for f in self.findings if f.get("agent") == "Recon"), None)
        if recon:
            content += recon.get("analysis", "No recon data.")[:500]
        else:
            content += "No reconnaissance data available."

        content += f"\n\n---\n*[[index|← Back to Index]] | [[log|View Log]]*"

        path = os.path.join(self.output_dir, "scans", f"{self.scan_id}-scan.md")
        with open(path, "w") as f:
            f.write(content)

    def _generate_endpoints(self):
        """Create or update entity pages for each endpoint."""
        endpoints = {}
        for f in self.findings:
            url = f.get("url", self.target)
            if url not in endpoints:
                endpoints[url] = []
            endpoints[url].append(f)

        for url, findings in endpoints.items():
            slug = url.replace("://", "_").replace("/", "_")[:40]
            path = os.path.join(self.output_dir, "endpoints", f"{slug}.md")

            critical = sum(1 for f in findings if f.get("severity") == "Critical")
            high = sum(1 for f in findings if f.get("severity") == "High")

            content = f"""---
endpoint: {url}
total_findings: {len(findings)}
critical: {critical}
high: {high}
scan_date: {self.scan_date}
tags: [endpoint]
---

# 🔗 {url}

> {len(findings)} findings (🔴{critical} 🟠{high})

## Findings

"""
            for f in findings:
                i = list(self.findings).index(f) + 1
                fid = f"FIN-{i:03d}"
                sev = f.get("severity", "?")
                ftype = f.get("type", "?")
                content += f"- [[../findings/{fid}|{fid}]] {self._severity_emoji(sev)} {ftype}\n"

            content += f"\n---\n*[[../index|Index]] | [[../scans/{self.scan_id}-scan|Scan Report]]*"

            with open(path, "w") as f:
                f.write(content)

    def _generate_canvas(self):
        """Generate Obsidian canvas mindmap of findings."""
        nodes = [{
            "id": "main", "type": "text",
            "text": f"**🔍 Audit: {self.target[:30]}**\n{self.scan_date}\n{len(self.findings)} findings",
            "x": 0, "y": 0, "width": 300, "height": 120
        }]
        edges = []

        for i, f in enumerate(self.findings):
            fid = f"FIN-{i+1:03d}"
            sev = f.get("severity", "Info")
            ftype = f.get("type", "?")
            color = self._severity_color(sev)
            nodes.append({
                "id": f"f{i}", "type": "text",
                "text": f"**{fid}: {ftype}**\n{self._severity_emoji(sev)} {sev}\n{f.get('agent','?')}",
                "x": 350 + (i % 3) * 320,
                "y": -200 + (i // 3) * 200,
                "width": 280, "height": 120,
                "color": color
            })
            edges.append({"id": f"e{i}", "fromNode": "main", "toNode": f"f{i}"})

        # Add endpoint nodes
        endpoints_seen = set()
        ei = len(self.findings)
        for f in self.findings:
            url = f.get("url", "")
            if url and url not in endpoints_seen:
                endpoints_seen.add(url)
                nodes.append({
                    "id": f"ep{ei}", "type": "text",
                    "text": f"**Endpoint**\n{url[:40]}",
                    "x": -350, "y": -200 + (len(endpoints_seen) - 1) * 200,
                    "width": 250, "height": 80,
                    "color": "5"
                })
                edges.append({"id": f"ee{ei}", "fromNode": "main", "toNode": f"ep{ei}"})
                ei += 1

        canvas_path = os.path.join(self.output_dir, "canvas.canvas")
        with open(canvas_path, "w") as f:
            json.dump({"nodes": nodes, "edges": edges}, f, indent=2)

    def _generate_scan_report(self):
        """Generate a standalone scan report page."""
        # Already done in _generate_overview, but here we add the detailed findings
        pass
