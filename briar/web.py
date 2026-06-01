"""Briar Web Dashboard — FastAPI, zero external dependencies 🥀"""
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn, os, json
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
.header{background:linear-gradient(135deg,#1a0a0a,#13132b);border-bottom:2px solid var(--red);padding:20px 32px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
.header h1{font-size:20px;color:var(--red)}.header .sub{color:var(--muted);font-size:12px}
.container{max-width:1100px;margin:0 auto;padding:24px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px;margin-bottom:24px}
.stat{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px;text-align:center}
.stat .n{font-size:26px;font-weight:700}.stat .l{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-top:4px}
.card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:20px;margin-bottom:16px}
.card h2{font-size:16px;color:var(--red);margin-bottom:16px}
.btn{background:var(--redbg);color:var(--red);border:1px solid var(--red);border-radius:6px;padding:8px 18px;font-size:13px;cursor:pointer;text-decoration:none;display:inline-block;font-weight:600}
.btn:hover{background:rgba(204,0,0,.25)}.btn-sm{padding:4px 12px;font-size:11px}
.btn-green{background:rgba(166,227,161,.1);color:var(--ok);border-color:var(--ok)}.btn-green:hover{background:rgba(166,227,161,.2)}
table{width:100%;border-collapse:collapse}
th,td{padding:10px 14px;text-align:left;border-bottom:1px solid var(--border);font-size:13px}
th{color:var(--muted);text-transform:uppercase;font-size:11px;letter-spacing:1px;font-weight:600}
tr:hover{background:rgba(255,255,255,.02)}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.5px}
.b-crit{background:#2a1840;color:var(--crit)}.b-high{background:#2a1828;color:var(--high)}.b-med{background:#2a2018;color:var(--med)}.b-low{background:#2a2618;color:var(--low)}.b-info{background:#182030;color:var(--accent)}.b-ok{background:#182a18;color:var(--ok)}
form{display:flex;gap:8px;flex-wrap:wrap;align-items:end}
input,select{background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:10px 14px;color:var(--fg);font-size:13px;outline:none;font-family:inherit}
input:focus,select:focus{border-color:var(--red)}
.empty{text-align:center;padding:48px;color:var(--muted)}.empty h3{font-size:18px;margin-bottom:8px}
.finding-row{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--border);font-size:13px;cursor:pointer}
.finding-row:hover{background:rgba(255,255,255,.01)}
.finding-detail{display:none;padding:14px;background:rgba(0,0,0,.2);border-radius:8px;margin-top:8px;font-size:12px;max-height:400px;overflow-y:auto;white-space:pre-wrap;line-height:1.5}
.finding-detail.open{display:block}
.sev-dot{width:10px;height:10px;border-radius:50%;display:inline-block;flex-shrink:0}
code{background:#1a1a35;padding:1px 5px;border-radius:3px;font-size:12px}
pre{background:rgba(0,0,0,.3);border:1px solid var(--border);border-radius:6px;padding:12px;overflow-x:auto;color:var(--fg);font-size:11px;line-height:1.4;margin:8px 0}
a{color:var(--accent);text-decoration:none}a:hover{color:var(--red)}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.live-dot{width:8px;height:8px;background:var(--red);border-radius:50%;display:inline-block;animation:pulse 1.5s infinite;margin-right:6px}
</style>"""

JS_ACCORDION = """<script>
document.querySelectorAll('.finding-detail').forEach(el=>el.addEventListener('click',e=>e.stopPropagation()));
document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll('.finding-detail.open').forEach(el=>el.classList.remove('open'))});
</script>"""

def load_scans():
    try:
        with open(SCANS_FILE) as f: return json.load(f)
    except: return []

def load_workspace_findings(name):
    path = os.path.join(WORKSPACES_DIR, name, "findings.json")
    try:
        with open(path) as f: return json.load(f)
    except: return []

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

@app.get("/", response_class=HTMLResponse)
async def home():
    scans = load_scans()
    scans_sorted = sorted(scans, key=lambda s: s.get("date", ""), reverse=True)
    total_findings = sum(s.get("findings", 0) for s in scans)
    saved = get_saved_provider()

    prov_opts = "".join(f'<option value="{p}" {"selected" if p==saved else ""}>{p}</option>' for p in PROVIDERS)

    scans_html = ""
    for s in scans_sorted[:20]:
        sid = s.get("scan_id", s.get("date", ""))
        s_status = s.get("status", "?")
        s_target = s.get("target", "?")
        if s_status == "done":
            badge = '<span class="badge b-info">Done</span>'
        elif s_status == "running":
            badge = '<span class="badge b-high"><span class="live-dot"></span>Running</span>'
        else:
            badge = f'<span class="badge b-low">{s_status}</span>'
        scans_html += f"""<tr>
            <td style="color:var(--muted);font-size:12px">{s.get('date','?')}</td>
            <td style="max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{s_target}</td>
            <td>{s.get('findings',0)}</td>
            <td>{badge}</td>
            <td><a href="/scan/{sid}" class="btn btn-sm btn-green">View</a></td>
        </tr>"""

    if not scans_sorted:
        scans_html = '<tr><td colspan="5"><div class="empty"><h3>No scans yet</h3><p>Launch your first scan above.</p></div></td></tr>'

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Briar Dashboard</title>{CSS}<meta http-equiv="refresh" content="15"></head><body>
<div class="header"><div><h1>Briar Dashboard</h1><p class="sub">Autonomous AI Pentester</p></div></div>
<div class="container">
<div class="stats">
<div class="stat"><div class="n">{len(scans)}</div><div class="l">Scans</div></div>
<div class="stat"><div class="n">{total_findings}</div><div class="l">Findings</div></div>
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
<div class="card"><h2>Recent Scans</h2><table><tr><th>Date</th><th>Target</th><th>Findings</th><th>Status</th><th></th></tr>{scans_html}</table></div>
</div></body></html>""")

@app.get("/scan/{scan_id}", response_class=HTMLResponse)
async def scan_detail(scan_id: str):
    workspaces = sorted([d for d in os.listdir(WORKSPACES_DIR) if os.path.isdir(os.path.join(WORKSPACES_DIR, d))], reverse=True)
    
    # Find target URL from scan record
    scans = load_scans()
    target_url = None
    for s in scans:
        if s.get("scan_id") == scan_id:
            target_url = s.get("target", "")
            break
    
    # Match workspace by target URL (pick most recent)
    ws_name = None
    if target_url:
        safe = target_url.replace("://", "_").replace("/", "_").replace(":", "_")[:50]
        for ws in workspaces:
            if safe in ws:
                ws_name = ws
                break

    findings = load_workspace_findings(ws_name) if ws_name else []
    findings_sorted = sorted(findings, key=lambda f: SEV_ORDER.get(f.get("severity", "Info"), 99))

    total = len(findings_sorted)
    critical = sum(1 for f in findings_sorted if f.get("severity") == "Critical")
    high = sum(1 for f in findings_sorted if f.get("severity") == "High")
    medium = sum(1 for f in findings_sorted if f.get("severity") == "Medium")
    low = sum(1 for f in findings_sorted if f.get("severity") == "Low")
    confirmed = sum(1 for f in findings_sorted if f.get("confirmed"))

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
<span style="flex:1">{ftype}</span>
<span style="color:var(--muted);font-size:11px">{agent}</span>
<span style="color:var(--muted)">&#9662;</span></div>
<div class="finding-detail">
<p><strong>Endpoint:</strong> <code>{url}</code></p>
{f'<p><strong>Param:</strong> <code>{param}</code></p>' if param else ''}
{f'<p><strong>Payload:</strong> <code>{payload}</code></p>' if payload else ''}
{f'<p><span class="badge b-ok">Confirmed</span></p>' if is_confirmed else '<p><span class="badge b-low">Unconfirmed</span></p>'}
{f'<p><strong>PoC:</strong></p><pre>{poc}</pre>' if poc else ''}
<hr style="border-color:var(--border);margin:10px 0">
<div style="max-height:250px;overflow-y:auto">{analysis}</div></div>"""

    if not findings_sorted:
        findings_html = '<div class="empty"><h3>No findings</h3><p>This scan produced no results.</p></div>'

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Scan {scan_id} - Briar</title>{CSS}</head><body>
<div class="header"><div><h1><a href="/" style="color:var(--red)">Briar</a> / Scan {scan_id}</h1>
<p class="sub">{total} findings</p></div><a href="/" class="btn">Back</a></div>
<div class="container">
<div class="stats">
<div class="stat"><div class="n">{total}</div><div class="l">Total</div></div>
<div class="stat"><div class="n" style="color:var(--crit)">{critical}</div><div class="l">Critical</div></div>
<div class="stat"><div class="n" style="color:var(--high)">{high}</div><div class="l">High</div></div>
<div class="stat"><div class="n" style="color:var(--med)">{medium}</div><div class="l">Medium</div></div>
<div class="stat"><div class="n" style="color:var(--low)">{low}</div><div class="l">Low</div></div>
<div class="stat"><div class="n" style="color:var(--ok)">{confirmed}</div><div class="l">Confirmed</div></div>
</div>
<div class="card"><h2>Findings</h2>{findings_html}</div>
</div>{JS_ACCORDION}</body></html>""")

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
    return {"status":"ok","version":"0.4.19","scans":len(load_scans())}

def main():
    print("Briar Dashboard -> http://localhost:8233")
    uvicorn.run(app, host="0.0.0.0", port=8233)

if __name__ == "__main__":
    main()
