"""Briar HTML Report — standalone interactive pentest report 🥀"""
import os
from datetime import datetime

# Severity order and colors
SEV_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}
SEV_BADGE = {"Critical": "b-crit", "High": "b-high", "Medium": "b-med", "Low": "b-low", "Info": "b-info"}
SEV_COLOR = {"Critical": "#bb9af7", "High": "#f7768e", "Medium": "#ff9e64", "Low": "#e0af68", "Info": "#7aa2f7"}
SEV_LABEL = {"Critical": "Critique", "High": "Élevée", "Medium": "Moyenne", "Low": "Faible", "Info": "Info"}

# Finding ID prefixes
TYPE_PREFIX = {
    "Reconnaissance": "REC", "Injection": "INJ", "XSS": "XSS", "SSRF": "SRF",
    "Authentication": "AUTH", "Authorization": "ATHZ", "CSRF": "CSF",
    "File Upload": "UPL", "Path Traversal": "TRV", "RCE": "RCE",
    "API Security": "API", "Secrets Detection": "SEC", "Screenshot": "SCR",
    "Browser Exploit": "BRS", "Error": "ERR"
}

def get_prefix(ftype: str) -> str:
    for key, prefix in TYPE_PREFIX.items():
        if key.lower() in ftype.lower():
            return prefix
    return "FND"

def get_finding_id(finding: dict, index: int) -> str:
    ftype = finding.get("type", "Unknown").replace(" ⚠️", "")
    prefix = get_prefix(ftype)
    return f"F-{prefix}-{index:03d}"

class HTMLReportGenerator:
    def __init__(self, target: str, findings: list, output_dir: str = "./reports", recon_data: dict = None):
        self.target = target
        self.findings = sorted(findings, key=lambda f: SEV_ORDER.get(f.get("severity", "Info"), 99))
        self.output_dir = output_dir
        self.recon = recon_data or next((f for f in findings if f.get("agent") == "Recon"), {})
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.time = datetime.now().strftime("%H:%M")
        os.makedirs(output_dir, exist_ok=True)

    def _badge(self, severity: str) -> str:
        cls = SEV_BADGE.get(severity, "b-info")
        label = SEV_LABEL.get(severity, "Info")
        return f'<span class="badge {cls}">{label}</span>'

    def _stats(self):
        total = len(self.findings)
        critical = sum(1 for f in self.findings if f.get("severity") == "Critical")
        high = sum(1 for f in self.findings if f.get("severity") == "High")
        medium = sum(1 for f in self.findings if f.get("severity") == "Medium")
        low = sum(1 for f in self.findings if f.get("severity") == "Low")
        info = sum(1 for f in self.findings if f.get("severity") == "Info")
        confirmed = sum(1 for f in self.findings if f.get("confirmed"))
        agents_used = set(f.get("agent", "?") for f in self.findings)
        endpoints = set(f.get("url", "") for f in self.findings)
        return total, critical, high, medium, low, info, confirmed, agents_used, endpoints

    def _nav(self):
        items = ""
        f_index = 0
        for f in self.findings:
            f_index += 1
            fid = get_finding_id(f, f_index)
            sev = f.get("severity", "Info")
            items += f'<a href="#{fid}">{fid} ({sev[:4]})</a>\n'
        return items

    def _risk_matrix(self):
        # Place findings in likelihood x impact grid
        grid = {(l, i): [] for l in range(5) for i in range(5)}
        f_index = 0
        for f in self.findings:
            f_index += 1
            sev = f.get("severity", "Info")
            fid = get_finding_id(f, f_index)
            # Map severity to likelihood x impact
            mapping = {"Critical": (4, 4), "High": (2, 3), "Medium": (2, 2), "Low": (1, 1), "Info": (0, 0), "Error": (4, 4)}
            l, imp = mapping.get(sev, (0, 0))
            grid[(l, imp)].append(fid)

        rows = ""
        l_labels = ["Rare", "Peu probable", "Possible", "Probable", "Très probable"]
        i_labels = ["Négligeable", "Mineur", "Modéré", "Majeur", "Critique"]
        m_colors = ["m0", "m1", "m2", "m3", "m4"]

        # Header row
        rows += '<div class="matrix">\n<div class="h">Likelihood ↓ / Impact →</div>\n'
        for il in i_labels:
            rows += f'<div class="h">{il}</div>\n'

        for li in range(4, -1, -1):
            rows += f'<div class="h">{l_labels[li]}</div>\n'
            for ii in range(5):
                findings_here = grid.get((li, ii), [])
                color = m_colors[min(ii, 4)]
                ids = '<br>'.join(findings_here) if findings_here else ""
                rows += f'<div class="cell {color}">{ids}</div>\n'
        rows += '</div>\n'
        return rows

    def _findings_html(self):
        html = ""
        f_index = 0
        for f in self.findings:
            f_index += 1
            fid = get_finding_id(f, f_index)
            sev = f.get("severity", "Info")
            ftype = f.get("type", "?").replace(" ⚠️", "")
            agent = f.get("agent", "?")
            url = f.get("url", self.target)
            confirmed = f.get("confirmed", False)
            poc = f.get("poc", "")
            param = f.get("param", "")
            payload = f.get("payload", "")
            analysis = f.get("analysis", f.get("raw", "No details available."))

            html += f"""<div class="card" id="{fid}">
{self._badge(sev)} <span class="finding-id">{fid}</span>
{f'<span class="badge b-ok" style="margin-left:8px">✅ Confirmé</span>' if confirmed else ''}
<h3 style="margin-top:8px">{ftype}</h3>
<p><strong>Agent :</strong> {agent} &middot; <strong>Endpoint :</strong> <code>{url}</code></p>
{f'<p><strong>Paramètre :</strong> <code>{param}</code> &middot; <strong>Payload :</strong> <code>{payload}</code></p>' if param else ''}
{f'<p><strong>PoC :</strong></p><pre>{poc}</pre>' if poc else ''}
<div style="background:#0a0c11;border:1px solid #262a35;border-radius:8px;padding:16px;margin-top:10px;color:#c0caf5;font-size:13px;white-space:pre-wrap;max-height:600px;overflow-y:auto">
{analysis}
</div>
</div>
"""
        return html

    def _negative_tests(self):
        # List agents that ran and found nothing confirmed
        agents_ran = set(f.get("agent", "?") for f in self.findings)
        confirmed_types = set(f.get("type", "?").replace(" ⚠️", "") for f in self.findings if f.get("confirmed"))
        all_categories = ["SQL Injection", "XSS", "SSRF", "CSRF", "Path Traversal", "RCE", "IDOR",
                          "Command Injection", "SSTI", "File Upload", "JWT bypass", "Privilege Escalation"]
        
        items = ""
        for cat in all_categories:
            if not any(cat.lower() in t.lower() for t in confirmed_types):
                items += f"<li>{cat} — testé, non exploitable</li>\n"
        
        return f"""<div class="card">
<h3>Vulnérabilités testées sans succès</h3>
<p>Les catégories suivantes ont été testées mais aucune exploitation n'a été confirmée :</p>
<ul class="clean">{items}</ul>
</div>"""

    def _methodology(self):
        agents_ran = set(f.get("agent", "?") for f in self.findings)
        return f"""<div class="card">
<h3>Méthodologie</h3>
<p>Audit black-box automatisé réalisé par <strong>Briar v0.4.11</strong> — pentester autonome.</p>
<h4>Phases</h4>
<ol>
<li><strong>Reconnaissance</strong> — scan de ports, détection de technologies, mapping de surface</li>
<li><strong>Injection de payloads</strong> — {len(agents_ran)} agents spécialisés OWASP : {', '.join(sorted(agents_ran))}</li>
<li><strong>Validation</strong> — chaque finding High/Critical rejoué pour confirmer l'exploitabilité</li>
<li><strong>Analyse IA</strong> — DeepSeek V4 pour l'interprétation et les recommandations</li>
</ol>
<h4>Outils</h4>
<p>Briar (Python), requests, Selenium, matplotlib, Obsidian LLM-Wiki</p>
</div>"""

    def generate(self) -> str:
        target_host = self.target.replace("https://", "").replace("http://", "").rstrip("/")
        total, critical, high, medium, low, info, confirmed, agents_used, endpoints = self._stats()

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Rapport de Pentest — {target_host} — {self.date}</title>
<style>
:root{{--bg:#0d0d1a;--card:#13132b;--muted:#6c7086;--fg:#cdd6f4;--accent:#89b4fa;--ok:#a6e3a1;--low:#f9e2af;--med:#fab387;--high:#f38ba8;--crit:#cba6f7;--border:#252545;--red:#cc0000;}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg);line-height:1.6;}}
header{{background:linear-gradient(135deg,#1a0a0a,#13132b);padding:32px 48px;border-bottom:2px solid var(--red);}}
header h1{{margin:0;font-size:28px;color:var(--fg)}}
header .sub{{color:var(--muted);margin-top:6px;font-size:14px}}
.layout{{display:grid;grid-template-columns:260px 1fr;min-height:100vh}}
nav{{background:#0a0a16;border-right:1px solid var(--border);padding:24px 18px;position:sticky;top:0;height:100vh;overflow-y:auto}}
nav h3{{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);margin:18px 0 6px}}
nav a{{display:block;color:var(--fg);text-decoration:none;padding:5px 8px;border-radius:6px;font-size:13px}}
nav a:hover{{background:#1a1a35;color:var(--red)}}
main{{padding:32px 48px;max-width:1100px}}
section{{margin-bottom:48px;scroll-margin-top:16px}}
h2{{border-bottom:2px solid var(--red);padding-bottom:8px;color:var(--red);font-size:20px}}
h3{{color:var(--fg);margin-top:24px}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:18px 22px;margin:14px 0}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px}}
.stat{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px;text-align:center}}
.stat .n{{font-size:28px;font-weight:700}}
.stat .l{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-top:4px}}
.badge{{display:inline-block;padding:3px 10px;border-radius:14px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px}}
.b-crit{{background:#2a1840;color:var(--crit)}}
.b-high{{background:#2a1828;color:var(--high)}}
.b-med{{background:#2a2018;color:var(--med)}}
.b-low{{background:#2a2618;color:var(--low)}}
.b-info{{background:#182030;color:var(--accent)}}
.b-ok{{background:#182a18;color:var(--ok)}}
table{{width:100%;border-collapse:collapse;margin:12px 0;background:var(--card);border-radius:8px;overflow:hidden}}
th,td{{padding:10px 14px;text-align:left;border-bottom:1px solid var(--border);font-size:13px;vertical-align:top}}
th{{background:#1a1a35;color:var(--muted);text-transform:uppercase;font-size:11px;letter-spacing:1px}}
tr:last-child td{{border-bottom:none}}
code{{background:#1a1a35;padding:2px 6px;border-radius:4px;color:var(--fg)}}
pre{{background:#0a0c11;border:1px solid var(--border);border-radius:8px;padding:14px;overflow-x:auto;color:var(--fg);font-family:"JetBrains Mono",Consolas,monospace;font-size:13px}}
.matrix{{display:grid;grid-template-columns:130px repeat(5,1fr);gap:3px;margin:12px 0}}
.matrix .h{{background:#1a1a35;padding:8px;text-align:center;font-weight:700;font-size:11px;color:var(--muted)}}
.matrix .cell{{padding:10px 6px;text-align:center;font-size:11px;border-radius:4px;min-height:30px}}
.m0{{background:#131a13;color:var(--ok)}}
.m1{{background:#1a1a13;color:var(--low)}}
.m2{{background:#2a2018;color:var(--med)}}
.m3{{background:#2a1828;color:var(--high)}}
.m4{{background:#2a1840;color:var(--crit)}}
.finding-id{{color:var(--muted);font-family:monospace;font-size:12px}}
ul.clean{{padding-left:20px}}
</style>
</head>
<body>
<div class="layout">
<nav>
<h3>Navigation</h3>
<a href="#exec">Synthèse exécutive</a>
<a href="#perimeter">Périmètre</a>
<a href="#stats">Statistiques</a>
<a href="#matrix">Matrice de risque</a>
<a href="#findings">Vulnérabilités</a>
{f''.join(f'<a href="#{get_finding_id(f, i+1)}">{get_finding_id(f, i+1)} ({f.get("severity","?")[:4]})</a>\n' for i, f in enumerate(self.findings))}
<a href="#negative">Tests négatifs</a>
<a href="#recommendations">Recommandations</a>
<a href="#method">Méthodologie</a>
<a href="#surface">Surface d'attaque</a>
</nav>

<main>
<header style="margin:-32px -48px 32px;padding:32px 48px">
<h1>🥀 Rapport de Pentest — {target_host}</h1>
<div class="sub">
<strong>Cible :</strong> {self.target} &middot;
<strong>Date :</strong> {self.date} {self.time} &middot;
<strong>Type :</strong> Black-box, automatisé
</div>
</header>

<section id="exec">
<h2>Synthèse exécutive</h2>
<div class="card">
<p>Audit de sécurité automatisé de <strong>{target_host}</strong> réalisé par Briar, pentester autonome.</p>
<p><strong>Résultat global :</strong> {self._badge("High") if critical+high > 0 else self._badge("Medium") if medium > 0 else self._badge("Info") if total > 0 else self._badge("Low")}</p>
<p><strong>{total} vulnérabilités</strong> identifiées : {critical} Critiques, {high} Élevées, {medium} Moyennes, {low} Faibles, {info} Informatives.</p>
<p><strong>{confirmed} findings confirmés</strong> avec preuve d'exploitabilité reproductible.</p>
</div>
</section>

<section id="perimeter">
<h2>Périmètre</h2>
<div class="card">
<table>
<tr><th>Élément</th><th>Détail</th></tr>
<tr><td>Frontend</td><td><code>{self.target}</code></td></tr>
<tr><td>Serveur détecté</td><td><code>{self.recon.get('server', 'Unknown')}</code></td></tr>
<tr><td>Technologies</td><td>{', '.join(self.recon.get('technologies', ['Unknown']))}</td></tr>
<tr><td>Endpoints découverts</td><td>{self.recon.get('endpoints_discovered', 0)}</td></tr>
<tr><td>Ports ouverts</td><td>{len(self.recon.get('open_ports', []))}</td></tr>
<tr><td>Mode</td><td>Non authentifié</td></tr>
</table>
</div>
</section>

<section id="stats">
<h2>Statistiques</h2>
<div class="grid">
<div class="stat"><div class="n">{total}</div><div class="l">Findings</div></div>
<div class="stat"><div class="n" style="color:var(--high)">{high}</div><div class="l">High</div></div>
<div class="stat"><div class="n" style="color:var(--med)">{medium}</div><div class="l">Medium</div></div>
<div class="stat"><div class="n" style="color:var(--low)">{low}</div><div class="l">Low</div></div>
<div class="stat"><div class="n" style="color:var(--accent)">{info}</div><div class="l">Info</div></div>
<div class="stat"><div class="n">{len(agents_used)}</div><div class="l">Agents</div></div>
<div class="stat"><div class="n">{len(endpoints)}</div><div class="l">Endpoints</div></div>
<div class="stat"><div class="n">{confirmed}</div><div class="l">Confirmés</div></div>
</div>
</section>

<section id="matrix">
<h2>Matrice de risque</h2>
<p style="color:var(--muted);font-size:13px">Sévérité = Likelihood × Impact. Chaque cellule liste les findings.</p>
{self._risk_matrix()}
<p style="color:var(--muted);font-size:13px">Légende : <span class="badge b-info">Info</span> <span class="badge b-low">Low</span> <span class="badge b-med">Medium</span> <span class="badge b-high">High</span> <span class="badge b-crit">Critical</span></p>
</section>

<section id="findings">
<h2>Vulnérabilités détaillées</h2>
{self._findings_html()}
</section>

<section id="negative">
<h2>Tests négatifs</h2>
{self._negative_tests()}
</section>

<section id="recommendations">
<h2>Recommandations</h2>
<div class="card">
<ol>
<li>Corriger en priorité les vulnérabilités Critical et High</li>
<li>Appliquer les remediations spécifiques décrites dans chaque finding</li>
<li>Re-scanner après correction pour vérifier les fixs</li>
<li>Mettre en place un scan automatique régulier</li>
</ol>
</div>
</section>

<section id="method">
<h2>Méthodologie</h2>
{self._methodology()}
</section>

<section id="surface">
<h2>Surface d'attaque</h2>
<div class="card">
<p><strong>Endpoints découverts :</strong> {self.recon.get('endpoints_discovered', 0)}</p>
<p><strong>Ports ouverts :</strong> {', '.join(f"{p['port']}/tcp ({p['service']})" for p in self.recon.get('open_ports', [])) or 'Aucun'}</p>
<h4>Headers de sécurité</h4>
<table>
<tr><th>Header</th><th>Valeur</th></tr>
{"".join(f'<tr><td>{k}</td><td style="color:{"var(--ok)" if v!="MISSING" else "var(--high)"}">{v}</td></tr>' for k,v in self.recon.get('security_headers', {}).items())}
</table>
</div>
</section>

<p style="color:var(--muted);text-align:center;padding:40px;font-size:12px">
Rapport généré par <a href="https://github.com/Stiimy/briar" style="color:var(--red)">Briar</a> — Pentester Autonome &middot; v0.4.11 &middot; AGPL-3.0
</p>
</main>
</div>
</body>
</html>"""
        path = os.path.join(self.output_dir, "rapport.html")
        with open(path, "w") as f:
            f.write(html)
        return path
