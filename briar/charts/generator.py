"""Briar Chart Generator — clean, professional security charts 📊"""
import os
import matplotlib
matplotlib.use('Agg')

BG = "#0d0d1a"
FG = "#cdd6f4"
RED = "#cc0000"
ORANGE = "#ff6600"
YELLOW = "#ffcc00"
GREEN = "#00cc44"
GREY = "#555577"
VIOLET = "#B847F0"

SEV_COLORS = {"Critical": RED, "High": ORANGE, "Medium": YELLOW, "Low": GREEN, "Info": GREY, "Error": GREY}

class ChartGenerator:
    def __init__(self, findings: list, output_dir: str = "./reports/charts"):
        self.findings = findings
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def severity_donut(self) -> str:
        """Donut chart — severity distribution with count labels."""
        import matplotlib.pyplot as plt
        severities = {}
        for f in self.findings:
            s = f.get("severity", "Info")
            severities[s] = severities.get(s, 0) + 1

        if len(severities) < 2:
            return "⚠️ All findings same severity — donut skipped"

        order = ["Critical", "High", "Medium", "Low", "Info", "Error"]
        labels = [k for k in order if k in severities]
        values = [severities[k] for k in labels]
        colors = [SEV_COLORS.get(k, GREY) for k in labels]

        fig, ax = plt.subplots(figsize=(8, 6), facecolor=BG)
        ax.set_facecolor(BG)
        wedges, texts = ax.pie(values, labels=None, colors=colors,
                                startangle=90, wedgeprops=dict(width=0.4, edgecolor=BG, linewidth=2))

        # Legend with counts
        legend_labels = [f"{l} ({v})" for l, v in zip(labels, values)]
        legend = ax.legend(wedges, legend_labels, loc="center left",
                           bbox_to_anchor=(1, 0.5), frameon=False,
                           prop={'color': FG, 'size': 11})
        ax.set_title("Severity Distribution", color=FG, fontsize=16, fontweight='bold', pad=20)

        path = os.path.join(self.output_dir, "severity_donut.png")
        plt.savefig(path, dpi=150, bbox_inches='tight', facecolor=BG)
        plt.close()
        return path

    def severity_pie(self) -> str:
        """Legacy — delegates to donut."""
        return self.severity_donut()

    def endpoint_heatmap(self) -> str:
        """Heatmap: severity × endpoint. Shows where the pain is."""
        import matplotlib.pyplot as plt
        import numpy as np

        # Gather data
        endpoints = {}
        sev_order = ["Critical", "High", "Medium", "Low", "Info"]
        for f in self.findings:
            url = f.get("url", "?")
            short = url.replace("https://", "").replace("http://", "")[:35]
            sev = f.get("severity", "Info")
            if short not in endpoints:
                endpoints[short] = {s: 0 for s in sev_order}
            if sev in sev_order:
                endpoints[short][sev] += 1

        if len(endpoints) < 2:
            return "⚠️ Single endpoint — heatmap skipped"

        # Build matrix
        rows = list(endpoints.keys())[:10]
        data = [[endpoints[r][s] for s in sev_order] for r in rows]
        data = np.array(data)

        fig, ax = plt.subplots(figsize=(max(8, len(rows)*0.6), max(4, len(rows)*0.4)), facecolor=BG)
        ax.set_facecolor(BG)

        # Custom colormap: dark bg -> green -> yellow -> red
        from matplotlib.colors import LinearSegmentedColormap
        cmap = LinearSegmentedColormap.from_list("briar", [BG, GREEN, YELLOW, RED], N=10)

        im = ax.imshow(data, cmap=cmap, aspect='auto')

        # Labels
        ax.set_xticks(range(len(sev_order)))
        ax.set_xticklabels(sev_order, color=FG, fontsize=9)
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels(rows, color=FG, fontsize=9)
        ax.set_title("Vulnerabilities: Severity × Endpoint", color=FG, fontsize=14, fontweight='bold', pad=15)

        # Annotate cells
        for i in range(len(rows)):
            for j in range(len(sev_order)):
                val = data[i, j]
                color = "white" if val > 0 and sev_order[j] in ("Critical", "High") else FG
                ax.text(j, i, str(val) if val > 0 else "", ha='center', va='center',
                        color=color, fontsize=9, fontweight='bold')

        for spine in ax.spines.values():
            spine.set_visible(False)

        path = os.path.join(self.output_dir, "endpoint_heatmap.png")
        plt.savefig(path, dpi=150, bbox_inches='tight', facecolor=BG)
        plt.close()
        return path

    def type_bar(self) -> str:
        """Horizontal bar chart — findings by vulnerability type."""
        import matplotlib.pyplot as plt
        types = {}
        for f in self.findings:
            t = f.get("type", "Unknown").replace(" ⚠️", "")
            types[t] = types.get(t, 0) + 1

        if not types:
            return "⚠️ No findings to chart"

        type_sev = {}
        for f in self.findings:
            t = f.get("type", "Unknown").replace(" ⚠️", "")
            sev = f.get("severity", "Info")
            if t not in type_sev or sev in ("Critical", "High"):
                type_sev[t] = sev

        sorted_types = sorted(types.items(), key=lambda x: x[1], reverse=True)
        labels = [t[0] for t in sorted_types]
        values = [t[1] for t in sorted_types]
        colors = [SEV_COLORS.get(type_sev.get(l, "Info"), GREY) for l in labels]

        fig, ax = plt.subplots(figsize=(10, max(4, len(labels)*0.5)), facecolor=BG)
        ax.set_facecolor(BG)
        bars = ax.barh(labels, values, color=colors, height=0.6, edgecolor=BG, linewidth=1)
        ax.invert_yaxis()

        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height()/2,
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
        """Horizontal bar chart — findings by agent."""
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

        fig, ax = plt.subplots(figsize=(8, max(3, len(labels)*0.4)), facecolor=BG)
        ax.set_facecolor(BG)
        bars = ax.barh(labels, values, color=VIOLET, height=0.5, edgecolor=BG, linewidth=1)
        ax.invert_yaxis()

        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height()/2,
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
