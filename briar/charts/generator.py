"""Briar Chart Generator — clean, readable security charts 📊"""
import os
import matplotlib
matplotlib.use('Agg')

# Briar dark theme
BG = "#0d0d1a"
FG = "#cdd6f4"
RED = "#cc0000"
ORANGE = "#ff6600"
YELLOW = "#ffcc00"
GREEN = "#00cc44"
GREY = "#666688"
VIOLET = "#B847F0"

SEV_COLORS = {"Critical": RED, "High": ORANGE, "Medium": YELLOW, "Low": GREEN, "Info": GREY, "Error": GREY}

class ChartGenerator:
    def __init__(self, findings: list, output_dir: str = "./reports/charts"):
        self.findings = findings
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def severity_pie(self) -> str:
        """Camembert de sévérité — only if at least 2 different severities."""
        import matplotlib.pyplot as plt
        severities = {}
        for f in self.findings:
            s = f.get("severity", "Info")
            severities[s] = severities.get(s, 0) + 1

        # Skip pie if all findings are the same severity
        if len(severities) < 2:
            return "⚠️ All findings same severity — pie chart skipped"

        labels = list(severities.keys())
        values = list(severities.values())
        colors = [SEV_COLORS.get(k, GREY) for k in labels]

        fig, ax = plt.subplots(figsize=(7, 7), facecolor=BG)
        ax.set_facecolor(BG)
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, colors=colors,
            autopct='%1.0f%%', startangle=90,
            textprops={'color': FG, 'fontsize': 11}
        )
        for at in autotexts:
            at.set_fontsize(13)
            at.set_fontweight('bold')
        ax.set_title("Findings by Severity", color=FG, fontsize=14, fontweight='bold', pad=20)

        path = os.path.join(self.output_dir, "severity_pie.png")
        plt.savefig(path, dpi=150, bbox_inches='tight', facecolor=BG)
        plt.close()
        return path

    def type_bar(self) -> str:
        """Barres horizontales par type de vulnérabilité."""
        import matplotlib.pyplot as plt
        types = {}
        for f in self.findings:
            t = f.get("type", "Unknown").replace(" ⚠️", "")
            types[t] = types.get(t, 0) + 1

        if not types:
            return "⚠️ No findings to chart"

        # Get severity for coloring
        type_sev = {}
        for f in self.findings:
            t = f.get("type", "Unknown").replace(" ⚠️", "")
            sev = f.get("severity", "Info")
            if t not in type_sev or sev == "Critical":
                type_sev[t] = sev

        sorted_types = sorted(types.items(), key=lambda x: x[1], reverse=True)
        labels = [t[0] for t in sorted_types]
        values = [t[1] for t in sorted_types]
        colors = [SEV_COLORS.get(type_sev.get(l, "Info"), GREY) for l in labels]

        fig, ax = plt.subplots(figsize=(10, max(4, len(labels) * 0.5)), facecolor=BG)
        ax.set_facecolor(BG)
        bars = ax.barh(labels, values, color=colors, height=0.6)
        ax.invert_yaxis()

        # Add count labels
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                    str(val), va='center', color=FG, fontsize=10, fontweight='bold')

        ax.set_xlabel("Count", color=FG, fontsize=10)
        ax.set_title("Findings by Type", color=FG, fontsize=14, fontweight='bold', pad=15)
        ax.tick_params(colors=FG, labelsize=9)
        for spine in ax.spines.values():
            spine.set_color('#252545')
        ax.xaxis.label.set_color(FG)

        path = os.path.join(self.output_dir, "type_bar.png")
        plt.savefig(path, dpi=150, bbox_inches='tight', facecolor=BG)
        plt.close()
        return path

    def agent_bar(self) -> str:
        """Barres horizontales par agent."""
        import matplotlib.pyplot as plt
        agents = {}
        for f in self.findings:
            a = f.get("agent", "Unknown")
            agents[a] = agents.get(a, 0) + 1

        if not agents:
            return "⚠️ No findings to chart"

        sorted_agents = sorted(agents.items(), key=lambda x: x[1], reverse=True)
        labels = [a[0] for a in sorted_agents]
        values = [a[1] for a in sorted_agents]

        fig, ax = plt.subplots(figsize=(8, max(3, len(labels) * 0.4)), facecolor=BG)
        ax.set_facecolor(BG)
        bars = ax.barh(labels, values, color=VIOLET, height=0.5)
        ax.invert_yaxis()

        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                    str(val), va='center', color=FG, fontsize=10, fontweight='bold')

        ax.set_xlabel("Count", color=FG, fontsize=10)
        ax.set_title("Findings by Agent", color=FG, fontsize=14, fontweight='bold', pad=15)
        ax.tick_params(colors=FG, labelsize=9)
        for spine in ax.spines.values():
            spine.set_color('#252545')
        ax.xaxis.label.set_color(FG)

        path = os.path.join(self.output_dir, "agent_bar.png")
        plt.savefig(path, dpi=150, bbox_inches='tight', facecolor=BG)
        plt.close()
        return path
