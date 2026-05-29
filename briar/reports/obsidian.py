"""Briar Obsidian Report Generator — .md + canvas mindmap 📓"""
import os
from datetime import datetime

class ObsidianGenerator:
    def __init__(self, target: str, findings: list, output_dir: str = "./reports/obsidian"):
        self.target = target
        self.findings = findings
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate(self) -> str:
        """Generate Obsidian vault with linked notes and canvas"""
        # Main report
        main = f"""---
title: "Security Audit — {self.target}"
date: {datetime.now().strftime('%Y-%m-%d')}
tags: [security, pentest, briar]
---

# Security Audit — {self.target}

## Summary
- **Target:** {self.target}
- **Findings:** {len(self.findings)}
- **Tool:** [[Briar]]

## Findings

"""
        for i, f in enumerate(self.findings):
            sev = f.get("severity", "Unknown")
            fname = f"finding_{i+1}"
            main += f"- [[{fname}]] — {f.get('type','?')} ({sev})\n"
            
            # Individual finding note
            fnote = f"""---
severity: {sev}
type: {f.get('type','?')}
agent: {f.get('agent','?')}
url: {f.get('url', self.target)}
---
# Finding {i+1}: {f.get('type','Vulnerability')}

**Severity:** {sev}

{f.get('analysis', f.get('raw','No details'))}

## Related
- [[Security Audit — {self.target}]]
- [[Briar]]
"""
            with open(os.path.join(self.output_dir, f"{fname}.md"), "w") as ff:
                ff.write(fnote)
        
        # Canvas mindmap
        canvas = {"nodes": [], "edges": []}
        canvas["nodes"].append({
            "id": "main", "type": "text", "text": f"**Audit: {self.target}**",
            "x": 0, "y": 0, "width": 300, "height": 100
        })
        
        for i, f in enumerate(self.findings):
            sev = f.get("severity", "Unknown")
            color = {"Critical":"1","High":"2","Medium":"3","Low":"4"}.get(sev,"0")
            node_id = f"f{i}"
            canvas["nodes"].append({
                "id": node_id, "type": "text",
                "text": f"**{f.get('type','?')}**\n{sev}",
                "x": 350 + (i % 3) * 300, "y": -200 + (i // 3) * 200,
                "width": 250, "height": 100, "color": color
            })
            canvas["edges"].append({
                "id": f"e{i}", "fromNode": "main", "toNode": node_id
            })
        
        with open(os.path.join(self.output_dir, "canvas.canvas"), "w") as f:
            import json
            json.dump(canvas, f, indent=2)
        
        main += f"\n## Mindmap\n![[canvas.canvas]]\n"
        
        safe_target = self.target.replace("://", "_").replace("/", "_").replace(":", "_")
        path = os.path.join(self.output_dir, f"Security Audit — {safe_target}.md")
        with open(path, "w") as f:
            f.write(main)
        
        return self.output_dir
