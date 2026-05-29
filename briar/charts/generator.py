"""Briar Chart Generator — camemberts, barres, courbes 📊"""
import os
import matplotlib
matplotlib.use('Agg')  # headless — pas de GUI

class ChartGenerator:
    def __init__(self, findings: list, output_dir: str = "./reports/charts"):
        self.findings = findings
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def severity_pie(self) -> str:
        """Camembert de sévérité"""
        try:
            import matplotlib.pyplot as plt
            severities = {}
            for f in self.findings:
                s = f.get("severity", "Unknown")
                severities[s] = severities.get(s, 0) + 1
            
            colors = {"Critical":"#ff0000","High":"#ff6600","Medium":"#ffcc00","Low":"#00cc00"}
            fig, ax = plt.subplots(figsize=(8,8))
            ax.pie(severities.values(), labels=severities.keys(), 
                   colors=[colors.get(k,"#999") for k in severities.keys()],
                   autopct='%1.1f%%', startangle=90)
            ax.set_title("Vulnerabilities by Severity")
            
            path = os.path.join(self.output_dir, "severity_pie.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            return path
        except ImportError:
            return "⚠️ matplotlib not installed"
    
    def agent_bar(self) -> str:
        """Barres par agent"""
        try:
            import matplotlib.pyplot as plt
            agents = {}
            for f in self.findings:
                a = f.get("agent", "Unknown")
                agents[a] = agents.get(a, 0) + 1
            
            fig, ax = plt.subplots(figsize=(10,5))
            ax.bar(agents.keys(), agents.values(), color='#B847F0', edgecolor='white')
            ax.set_title("Findings by Agent")
            ax.set_ylabel("Count")
            plt.xticks(rotation=45)
            
            path = os.path.join(self.output_dir, "agent_bar.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            return path
        except ImportError:
            return "⚠️ matplotlib not installed"
