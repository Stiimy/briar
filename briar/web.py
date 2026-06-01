"""Briar Web Dashboard v2 — FastAPI, zero deps 🥀"""
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
import uvicorn, os, json, time
from datetime import datetime
from pathlib import Path

app = FastAPI(title="Briar Dashboard")

SCANS_FILE = os.path.expanduser("~/.briar/scans.json")
WORKSPACES_DIR = os.path.expanduser("~/.briar/workspaces")
SEV_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}
SEV_CLASS = {"Critical": "b-crit", "High": "b-high", "Medium": "b-med", "Low": "b-low", "Info": "b-info"}
SEV_COLOR = {"Critical": "#cba6f7", "High": "#f38ba8", "Medium": "#fab387", "Low": "#f9e2af", "Info": "#89b4fa"}

CSS = """<style>
:root{--bg:#0d0d1a;--card:#13132b;--muted:#6c7086;--fg:#cdd6f4;--accent:#89b4fa;--ok:#a6e3a1;--low:#f9e2af;--med:#fab387;--high:#f38ba8;--crit:#cba6f7;--border:#252545;--red:#cc0000;--redbg:rgba(204,0,0,.1)}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--fg);font-family:-apple-system,Segoe UI,Roboto,sans-serif;line-height:1.6;min-height:100vh}
.header{background:linear-gradient(135deg,#1a0a0a,#13132b);border-bottom:2px solid var(--red);padding:16px 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
.header h1{font-size:18px;color:var(--red)}.header .sub{color:var(--muted);font-size:11px}
.nav-links{display:flex;gap:16px;flex-wrap:wrap}
.nav-links a{color:var(--muted);text-decoration:none;font-size:13px;padding:4px 0;border-bottom:2px solid transparent}
.nav-links a:hover,.nav-links a.active{color:var(--red);border-bottom-color:var(--red)}
.container{max-width:1200px;margin:0 auto;padding:20px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:10px;margin-bottom:20px}
.stat{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px;text-align:center}
.stat .n{font-size:24px;font-weight:700}.stat .l{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-top:2px}
.card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:18px;margin-bottom:14px}
.card h2{font-size:15px;color:var(--red);margin-bottom:14px}
.btn{background:var(--redbg);color:var(--red);border:1px solid var(--red);border-radius:6px;padding:7px 16px;font-size:12px;cursor:pointer;text-decoration:none;display:inline-block;font-weight:600;transition:all .2s}
.btn:hover{background:rgba(204,0,0,.25)}.btn-sm{padding:4px 10px;font-size:10px}
.btn-green{background:rgba(166,227,161,.1);color:var(--ok);border-color:var(--ok)}.btn-green:hover{background:rgba(166,227,161,.2)}
.btn-amber{background:rgba(249,226,175,.1);color:var(--low);border-color:var(--low)}
table{width:100%;border-collapse:collapse}
th,td{padding:10px 12px;text-align:left;border-bottom:1px solid var(--border);font-size:12px}
th{color:var(--muted);text-transform:uppercase;font-size:10px;letter-spacing:1px;font-weight:600}
tr:hover{background:rgba(255,255,255,.02)}
.badge{display:inline-block;padding:2px 7px;border-radius:10px;font-size:10px;font-weight:700;text-transform:uppercase}
.b-crit{background:#2a1840;color:var(--crit)}.b-high{background:#2a1828;color:var(--high)}.b-med{background:#2a2018;color:var(--med)}.b-low{background:#2a2618;color:var(--low)}.b-info{background:#182030;color:var(--accent)}.b-ok{background:#182a18;color:var(--ok)}
form{display:flex;gap:8px;flex-wrap:wrap;align-items:end}
input,select{background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:9px 12px;color:var(--fg);font-size:12px;outline:none;font-family:inherit}
input:focus,select:focus{border-color:var(--red)}
.empty{text-align:center;padding:40px;color:var(--muted)}.empty h3{font-size:16px;margin-bottom:6px}
.finding-row{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border);font-size:12px;cursor:pointer}
.finding-row:hover{background:rgba(255,255,255,.01)}
.finding-detail{display:none;padding:12px;background:rgba(0,0,0,.2);border-radius:8px;margin-top:6px;font-size:11px;max-height:350px;overflow-y:auto;white-space:pre-wrap;line-height:1.5}
.finding-detail.open{display:block}
.sev-dot{width:8px;height:8px;border-radius:50%;display:inline-block;flex-shrink:0}
.sev-bar{display:flex;height:6px;border-radius:3px;overflow:hidden;gap:1px;margin:4px 0}
.sev-bar span{height:100%}
code{background:#1a1a35;padding:1px 4px;border-radius:3px;font-size:11px}
pre{background:rgba(0,0,0,.3);border:1px solid var(--border);border-radius:6px;padding:10px;overflow-x:auto;color:var(--fg);font-size:11px;line-height:1.3;margin:6px 0}
a{color:var(--accent);text-decoration:none}a:hover{color:var(--red)}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.live-dot{width:8px;height:8px;background:var(--red);border-radius:50%;display:inline-block;animation:pulse 1.5s infinite;margin-right:6px}
.progress-bar{background:var(--border);border-radius:8px;height:5px;margin:6px 0;overflow:hidden}
.progress-fill{background:var(--red);height:100%;border-radius:8px;transition:width .5s}
@media(max-width:768px){.grid-2{grid-template-columns:1fr}.header{flex-direction:column}}
</style>"""

JS_ACCORDION = """<script>
document.querySelectorAll('.finding-detail').forEach(el=>el.addEventListener('click',e=>e.stopPropagation()));
document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll('.finding-detail.open').forEach(el=>el.classList.remove('open'))});
</script>"""

REFRESH_5S = '<meta http-equiv="refresh" content="5">'

def load_scans():
    try:
        with open(SCANS_FILE) as f: return json.load(f)
    except: return []

def load_workspace_findings(name):
    path = os.path.join(WORKSPACES_DIR, name, "findings.json")
    try:
        with open(path) as f: return json.load(f)
    except: return []

def load_workspace_state(name):
    path = os.path.join(WORKSPACES_DIR, name, "state.json")
    try:
        with open(path) as f: return json.load(f)
    except: return {}

def get_saved_provider():
    config_file = os.path.expanduser("~/.briar/config")
    if not os.path.exists(config_file): return "ollama"
    try:
        with open(config_file) as f:
            for line in f:
                if line.startswith("PROVIDER="):
                    return line.strip().split("=", 1)[1]
    except: pass
    return "ollama"

PROVIDERS = ["ollama","openai","anthropic","deepseek","groq","mistral","xai","google","openrouter","together","custom"]

def find_workspace(scan_id: str) -> str:
    """Find workspace by scan_id or target URL."""
    scans = load_scans()
    target_url = None
    for s in scans:
        if s.get("scan_id") == scan_id:
            target_url = s.get("target", "")
            break
    if not target_url:
        return None
    workspaces = sorted([d for d in os.listdir(WORKSPACES_DIR) if os.path.isdir(os.path.join(WORKSPACES_DIR, d))], reverse=True)
    safe = target_url.replace("://", "_").replace("/", "_").replace(":", "_")[:50]
    for ws in workspaces:
        if safe in ws:
            return ws
    return None

def find_workspace_latest(target_url: str) -> str:
    """Find latest workspace for a target."""
    workspaces = sorted([d for d in os.listdir(WORKSPACES_DIR) if os.path.isdir(os.path.join(WORKSPACES_DIR, d))], reverse=True)
    safe = target_url.replace("://", "_").replace("/", "_").replace(":", "_")[:50]
    for ws in workspaces:
        if safe in ws:
            return ws
    return None

def report_exists(scan_id: str) -> dict:
    """Check what reports exist for a scan."""
    scans = load_scans()
    target_url = None
    for s in scans:
        if s.get("scan_id") == scan_id:
            target_url = s.get("target", "")
            break
    if not target_url:
        return {}
    from urllib.parse import urlparse
    host = urlparse(target_url).hostname or "unknown"
    host_slug = host.replace(".", "-")[:40]
    result = {}
    cwd = os.getcwd()
    reports_dir = os.path.join(cwd, "reports")
    # Check latest dated report
    import glob
    pattern = os.path.join(reports_dir, f"{host_slug}_*.md")
    md_files = sorted(glob.glob(pattern), reverse=True)
    if md_files:
        result["markdown"] = os.path.basename(md_files[0])
    html_path = os.path.join(reports_dir, "rapport.html")
    if os.path.exists(html_path):
        result["html"] = "rapport.html"
    obsidian_dir = os.path.join(reports_dir, "obsidian")
    if os.path.exists(obsidian_dir):
        result["obsidian"] = "obsidian/"
    return result

@app.get("/", response_class=HTMLResponse)
async def home():
    scans = load_scans()
    scans_sorted = sorted(scans, key=lambda s: s.get("date", ""), reverse=True)
    total_findings = sum(s.get("findings", 0) for s in scans)
    saved = get_saved_provider()
    running = sum(1 for s in scans if s.get("status") == "running")

    prov_opts = "".join(f'<option value="{p}" {"selected" if p==saved else ""}>{p}</option>' for p in PROVIDERS)

    scans_html = ""
    for s in scans_sorted[:30]:
        sid = s.get("scan_id", s.get("date", ""))
        s_status = s.get("status", "?")
        s_target = s.get("target", "?")
        s_mode = s.get("mode", "?")
        s_findings = s.get("findings", 0)
        if s_status == "done":
            badge = '<span class="badge b-info">Done</span>'
        elif s_status == "running":
            badge = '<span class="badge b-high"><span class="live-dot"></span>Running</span>'
        else:
            badge = f'<span class="badge b-low">{s_status}</span>'

        scans_html += f"""<tr>
            <td style="color:var(--muted);font-size:11px;white-space:nowrap">{s.get('date','?')}</td>
            <td style="max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="{s_target}">{s_target}</td>
            <td><span class="badge b-info">{s_mode}</span></td>
            <td>{s_findings}</td>
            <td>{badge}</td>
            <td style="white-space:nowrap">
                <a href="/scan/{sid}" class="btn btn-sm btn-green">Detail</a>
                <a href="/scan/{sid}/live" class="btn btn-sm btn-amber">Live</a>
            </td>
        </tr>"""

    if not scans_sorted:
        scans_html = '<tr><td colspan="6"><div class="empty"><h3>No scans yet</h3><p>Launch your first scan.</p></div></td></tr>'

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Briar Dashboard</title>{CSS}{REFRESH_5S if running else ''}</head><body>
<div class="header"><div><h1>Briar Dashboard</h1><p class="sub">Autonomous AI Pentester</p></div>
<div class="nav-links"><a href="/" class="active">Scans</a><a href="/reports">Reports</a><a href="/health">API</a></div></div>
<div class="container">
<div class="stats">
<div class="stat"><div class="n">{len(scans)}</div><div class="l">Scans</div></div>
<div class="stat"><div class="n">{total_findings}</div><div class="l">Findings</div></div>
<div class="stat"><div class="n" style="color:var(--high)">{running}</div><div class="l">Running</div></div>
<div class="stat"><div class="n">12</div><div class="l">Agents</div></div>
<div class="stat"><div class="n">11</div><div class="l">Providers</div></div>
</div>
<div class="card"><h2>New Scan</h2>
<form action="/scan" method="get">
<input type="url" name="url" placeholder="https://target.com" required style="flex:1;min-width:200px">
<select name="provider">{prov_opts}</select>
<select name="mode"><option value="quick">Quick (4)</option><option value="standard" selected>Standard (8)</option><option value="deep">Deep (12)</option></select>
<button type="submit" class="btn">Launch</button>
</form></div>
<div class="card"><h2>Scan History</h2><table><tr><th>Date</th><th>Target</th><th>Mode</th><th>Findings</th><th>Status</th><th></th></tr>{scans_html}</table></div>
</div></body></html>""")

@app.get("/scan/{scan_id}", response_class=HTMLResponse)
async def scan_detail(scan_id: str):
    ws_name = find_workspace(scan_id)
    findings = load_workspace_findings(ws_name) if ws_name else []
    state = load_workspace_state(ws_name) if ws_name else {}
    findings_sorted = sorted(findings, key=lambda f: SEV_ORDER.get(f.get("severity", "Info"), 99))

    total = len(findings_sorted)
    critical = sum(1 for f in findings_sorted if f.get("severity") == "Critical")
    high = sum(1 for f in findings_sorted if f.get("severity") == "High")
    medium = sum(1 for f in findings_sorted if f.get("severity") == "Medium")
    low = sum(1 for f in findings_sorted if f.get("severity") == "Low")
    confirmed = sum(1 for f in findings_sorted if f.get("confirmed"))
    agents_done = state.get("agents_completed", [])

    # Find target URL
    scans = load_scans()
    target_url = ""
    for s in scans:
        if s.get("scan_id") == scan_id:
            target_url = s.get("target", "")
            break

    # Severity bar
    sev_bar = ""
    for sev, color, count in [("Critical", "#cba6f7", critical), ("High", "#f38ba8", high),
                                ("Medium", "#fab387", medium), ("Low", "#f9e2af", low)]:
        if total > 0:
            pct = count / total * 100
            if pct > 0:
                sev_bar += f'<span style="width:{pct}%;background:{color}" title="{sev}: {count}"></span>'

    # Reports available
    reports = report_exists(scan_id)
    report_links = ""
    if reports.get("html"):
        report_links += f'<a href="/report/{scan_id}" class="btn btn-sm">View HTML Report</a> '
    if reports.get("obsidian"):
        report_links += f'<span class="btn btn-sm" style="opacity:.5">Obsidian vault: {reports["obsidian"]}</span> '
    if not report_links:
        report_links = '<span style="color:var(--muted);font-size:11px">No reports found</span>'

    findings_html = ""
    for f in findings_sorted:
        sev = f.get("severity", "Info")
        ftype = f.get("type", "?")
        agent = f.get("agent", "?")
        url = f.get("url", "?")
        param = f.get("param", "")
        payload = f.get("payload", "")
        poc = f.get("poc", "")
        is_confirmed = f.get("confirmed", False)
        analysis = f.get("analysis", f.get("raw", "No details"))

        findings_html += f"""<div class="finding-row" onclick="this.nextElementSibling.classList.toggle('open')">
<span class="sev-dot" style="background:{SEV_COLOR.get(sev,'#666')}"></span>
<span class="badge {SEV_CLASS.get(sev,'b-info')}">{sev}</span>
<span style="flex:1;font-weight:500">{ftype}</span>
<span style="color:var(--muted);font-size:10px">{agent}</span>
<span style="color:var(--muted);font-size:14px">&#9662;</span></div>
<div class="finding-detail">
<p><strong>Endpoint:</strong> <code>{url}</code></p>
{f'<p><strong>Param:</strong> <code>{param}</code></p>' if param else ''}
{f'<p><strong>Payload:</strong> <code>{payload}</code></p>' if payload else ''}
{f'<p><span class="badge b-ok">Confirmed</span></p>' if is_confirmed else '<p><span class="badge b-low">Unconfirmed</span></p>'}
{f'<p><strong>PoC:</strong></p><pre>{poc}</pre>' if poc else ''}
<hr style="border-color:var(--border);margin:8px 0">
<div style="max-height:220px;overflow-y:auto;font-size:11px">{analysis}</div></div>"""

    if not findings_sorted:
        findings_html = '<div class="empty"><h3>No findings</h3><p>This scan produced no results.</p></div>'

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Scan {scan_id} - Briar</title>{CSS}</head><body>
<div class="header"><div><h1><a href="/" style="color:var(--red)">Briar</a> / Scan</h1>
<p class="sub">{target_url}</p></div><div style="display:flex;gap:8px">{report_links}<a href="/" class="btn btn-sm">Back</a></div></div>
<div class="container">
<div class="stats">
<div class="stat"><div class="n">{total}</div><div class="l">Total</div></div>
<div class="stat"><div class="n" style="color:var(--crit)">{critical}</div><div class="l">Critical</div></div>
<div class="stat"><div class="n" style="color:var(--high)">{high}</div><div class="l">High</div></div>
<div class="stat"><div class="n" style="color:var(--med)">{medium}</div><div class="l">Medium</div></div>
<div class="stat"><div class="n" style="color:var(--low)">{low}</div><div class="l">Low</div></div>
<div class="stat"><div class="n" style="color:var(--ok)">{confirmed}</div><div class="l">Confirmed</div></div>
</div>
{f'<div class="sev-bar">{sev_bar}</div>' if total > 0 else ''}
<div class="card"><h2>Findings ({total})</h2>{findings_html}</div>
</div>{JS_ACCORDION}</body></html>""")

@app.get("/scan/{scan_id}/live", response_class=HTMLResponse)
async def scan_live(scan_id: str):
    ws_name = find_workspace(scan_id)
    findings = load_workspace_findings(ws_name) if ws_name else []
    state = load_workspace_state(ws_name) if ws_name else {}
    agents_done = state.get("agents_completed", [])
    total_agents = 12 if state.get("mode") == "deep" else 4 if state.get("mode") == "quick" else 8
    findings_count = state.get("findings_count", 0)
    target = state.get("target", "?")

    # Check if still running
    scans = load_scans()
    is_running = False
    for s in scans:
        if s.get("scan_id") == scan_id and s.get("status") == "running":
            is_running = True
            break

    pct = min(100, len(agents_done) / max(1, total_agents) * 100)

    agents_html = ""
    all_agents = ["recon","injection","xss","ssrf","auth","authz","csrf","upload","traversal","rce","api","secrets"]
    for a in all_agents[:total_agents]:
        done = a in agents_done
        agents_html += f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;font-size:12px;{"opacity:.4" if not done else ""}">{ "&#10003;" if done else "&#9679;" } {a}</div>'

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Live - Briar</title>{CSS}{'' if not is_running else REFRESH_5S}</head><body>
<div class="header"><div><h1><a href="/" style="color:var(--red)">Briar</a> / Live</h1>
<p class="sub">{target} {f'<span class="live-dot" style="margin-left:8px"></span>Running' if is_running else '- Done'}</p></div>
<a href="/scan/{scan_id}" class="btn btn-sm">Detail</a></div>
<div class="container">
<div class="stats">
<div class="stat"><div class="n">{findings_count}</div><div class="l">Findings</div></div>
<div class="stat"><div class="n">{len(agents_done)}/{total_agents}</div><div class="l">Agents</div></div>
<div class="stat"><div class="n">{int(pct)}%</div><div class="l">Progress</div></div>
</div>
<div class="progress-bar"><div class="progress-fill" style="width:{pct}%"></div></div>
<div class="grid-2">
<div class="card"><h2>Agents</h2>{agents_html}</div>
<div class="card"><h2>Latest Findings ({findings_count})</h2>
{"".join(f'<div class="finding-row"><span class="sev-dot" style="background:{SEV_COLOR.get(f.get("severity","Info"),"#666")}"></span><span class="badge {SEV_CLASS.get(f.get("severity","Info"),"b-info")}">{f.get("severity","?")}</span><span style="flex:1;font-size:12px">{f.get("type","?")}</span></div>' for f in findings[-6:]) if findings else '<div class="empty" style="padding:20px"><p>Waiting for findings...</p></div>'}
</div></div>
</div></body></html>""")

@app.get("/reports", response_class=HTMLResponse)
async def reports():
    scans = load_scans()
    scans_sorted = sorted(scans, key=lambda s: s.get("date", ""), reverse=True)

    reports_html = ""
    for s in scans_sorted[:30]:
        if s.get("status") != "done":
            continue
        sid = s.get("scan_id", "")
        s_target = s.get("target", "?")
        s_date = s.get("date", "?")
        s_findings = s.get("findings", 0)
        reports_avail = report_exists(sid)

        reports_html += f"""<tr>
            <td style="color:var(--muted);font-size:11px">{s_date}</td>
            <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{s_target}</td>
            <td>{s_findings}</td>
            <td style="white-space:nowrap">
                {'<a href="/report/'+ sid +'" class="btn btn-sm btn-green">HTML</a>' if reports_avail.get('html') else '<span style="color:var(--muted);font-size:10px">--</span>'}
                <a href="/scan/{sid}" class="btn btn-sm">Detail</a>
            </td>
        </tr>"""

    if not reports_html:
        reports_html = '<tr><td colspan="4"><div class="empty"><h3>No reports</h3><p>Completed scans will appear here.</p></div></td></tr>'

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Reports - Briar</title>{CSS}</head><body>
<div class="header"><div><h1><a href="/" style="color:var(--red)">Briar</a> / Reports</h1></div>
<div class="nav-links"><a href="/">Scans</a><a href="/reports" class="active">Reports</a></div></div>
<div class="container">
<div class="card"><h2>Completed Scans</h2><table><tr><th>Date</th><th>Target</th><th>Findings</th><th>Reports</th></tr>{reports_html}</table></div>
</div></body></html>""")

@app.get("/report/{scan_id}", response_class=HTMLResponse)
async def view_report(scan_id: str):
    scans = load_scans()
    target_url = ""
    for s in scans:
        if s.get("scan_id") == scan_id:
            target_url = s.get("target", "")
            break
    if not target_url:
        return HTMLResponse("<h2>Scan not found</h2>")

    from urllib.parse import urlparse
    host = urlparse(target_url).hostname or "unknown"
    host_slug = host.replace(".", "-")[:40]
    import glob
    reports_dir = os.path.join(os.getcwd(), "reports")
    html_files = sorted(glob.glob(os.path.join(reports_dir, "rapport*.html")), reverse=True)
    if html_files:
        with open(html_files[0]) as f:
            return HTMLResponse(f.read())
    return HTMLResponse(f"<body style='background:#0d0d1a;color:#cdd6f4;font-family:sans-serif;padding:40px'><h2>No HTML report found</h2><p>Run a scan first.</p></body>")

@app.get("/scan")
async def launch_scan(url: str, provider: str = None, mode: str = "standard", background_tasks: BackgroundTasks = None):
    if not provider:
        provider = get_saved_provider()
    scan_id = datetime.now().strftime("%Y%m%d%H%M%S")
    scan_record = {"scan_id": scan_id, "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                   "target": url, "provider": provider, "mode": mode, "status": "running", "findings": 0}
    scans = load_scans()
    scans.append(scan_record)
    os.makedirs(os.path.dirname(SCANS_FILE), exist_ok=True)
    with open(SCANS_FILE, "w") as f: json.dump(scans, f, indent=2)

    def run_scan():
        from briar.agents import run_agent
        all_agents = ["recon","injection","xss","ssrf","auth","authz","csrf","upload","traversal","rce","api","secrets"]
        agent_count = 12 if mode == "deep" else 4 if mode == "quick" else 8
        agents = all_agents[:agent_count]
        findings_count = 0
        for agent_name in agents:
            try:
                result = run_agent(agent_name, provider, url=url)
                if result and "error" not in result: findings_count += 1
            except: pass
        scans = load_scans()
        for s in scans:
            if s.get("scan_id") == scan_id:
                s["status"] = "done"; s["findings"] = findings_count; break
        with open(SCANS_FILE, "w") as f: json.dump(scans, f, indent=2)

    if background_tasks: background_tasks.add_task(run_scan)
    return RedirectResponse(url="/", status_code=303)

@app.get("/health")
async def health():
    return {"status":"ok","version":"0.4.20","scans":len(load_scans())}

def main():
    print("Briar Dashboard -> http://localhost:8233")
    uvicorn.run(app, host="0.0.0.0", port=8233)

if __name__ == "__main__":
    main()
