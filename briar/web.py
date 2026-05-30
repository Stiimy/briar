"""Briar Web Dashboard — FastAPI + live stats + scan launcher 🥀"""
from fastapi import FastAPI, BackgroundTasks, Query
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
import uvicorn, os, json
from datetime import datetime

app = FastAPI(title="Briar Dashboard", version="0.3.0")

SCANS_FILE = os.path.expanduser("~/.briar/scans.json")
WORKSPACES_DIR = os.path.expanduser("~/.briar/workspaces")

def load_scans():
    try:
        with open(SCANS_FILE) as f:
            return json.load(f)
    except:
        return []

def save_scan(scan):
    scans = load_scans()
    scans.append(scan)
    os.makedirs(os.path.dirname(SCANS_FILE), exist_ok=True)
    with open(SCANS_FILE, "w") as f:
        json.dump(scans, f, indent=2)

def load_workspaces():
    if not os.path.exists(WORKSPACES_DIR):
        return []
    return sorted([d for d in os.listdir(WORKSPACES_DIR) 
                   if os.path.isdir(os.path.join(WORKSPACES_DIR, d))], reverse=True)

def load_workspace_findings(name):
    path = os.path.join(WORKSPACES_DIR, name, "findings.json")
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return []

PROVIDERS = ["ollama","openai","anthropic","deepseek","groq","mistral","xai","google","openrouter","together","custom"]

def get_saved_provider():
    """Read provider from ~/.briar/config. Returns 'ollama' if not found."""
    config_file = os.path.expanduser("~/.briar/config")
    if not os.path.exists(config_file):
        return None
    try:
        with open(config_file) as f:
            for line in f:
                if line.startswith("PROVIDER="):
                    return line.strip().split("=", 1)[1]
    except:
        pass
    return None

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    scans = load_scans()
    workspaces = load_workspaces()
    total_findings = sum(s['findings'] for s in scans)
    critical = sum(s.get('critical', 0) for s in scans)

    # Recent findings from latest workspace
    recent_findings = []
    if workspaces:
        findings = load_workspace_findings(workspaces[0])
        recent_findings = findings[-8:]

    findings_html = ""
    for f in recent_findings[::-1]:
        sev = f.get("severity", "Info")
        color = {"Critical":"#ff4444","High":"#ff6600","Medium":"#ffcc00","Low":"#00cc00"}.get(sev,"#666")
        icon = "🔴" if sev == "Critical" else "🟠" if sev == "High" else "🟡" if sev == "Medium" else "🟢"
        findings_html += f"""
        <div class="finding-row">
            <span style="color:{color}">{icon} {sev}</span>
            <span style="color:#cdd6f4">{f.get('type','?')}</span>
            <span style="color:#6c7086;font-size:.8rem">{f.get('agent','?')}</span>
        </div>"""

    scans_html = ""
    for s in scans[-8:]:
        status_color = "#a6e3a1" if s['status'] == 'done' else "#f9e2af"
        scans_html += f"""
        <tr>
            <td style="color:#6c7086">{s['date']}</td>
            <td style="color:#89b4fa;max-width:200px;overflow:hidden;text-overflow:ellipsis">{s['target']}</td>
            <td>{s['findings']}</td>
            <td><span style="background:rgba(166,227,161,.15);color:{status_color};padding:.2rem .6rem;border-radius:999px;font-size:.75rem">{s['status']}</span></td>
        </tr>"""

    workspaces_html = ""
    for ws in workspaces[:5]:
        state_path = os.path.join(WORKSPACES_DIR, ws, "state.json")
        try:
            with open(state_path) as f:
                state = json.load(f)
            target = state.get("target","?")[:25]
            agents = len(state.get("agents_completed",[]))
            findings = state.get("findings_count",0)
            workspaces_html += f"""<tr>
                <td style="color:#89b4fa">{ws[:30]}</td>
                <td style="color:#cdd6f4">{target}</td>
                <td style="color:#a6e3a1">{findings}</td>
                <td style="color:#6c7086">{agents}</td>
            </tr>"""
        except:
            workspaces_html += f"""<tr><td style="color:#89b4fa">{ws[:30]}</td><td colspan="3" style="color:#6c7086">corrupted</td></tr>"""

    saved_provider = get_saved_provider()
    provider_options = "".join(f'<option value="{p}" {"selected" if p==saved_provider else ""}>{p}</option>' for p in PROVIDERS)
    if not saved_provider:
        provider_options += '<option value="" disabled selected>Run briar setup first</option>'

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Briar Dashboard</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0d0d1a;color:#cdd6f4;font-family:'JetBrains Mono','Fira Code',monospace;min-height:100vh}}
.header{{background:linear-gradient(135deg,#1a0a0a,#1e1e2e);border-bottom:2px solid #cc0000;padding:1.5rem 2rem;display:flex;align-items:center;gap:1.5rem}}
.header h1{{color:#cc0000;font-size:1.8rem;letter-spacing:-1px}}
.header .sub{{color:#6c7086;font-size:.8rem}}
.layout{{display:flex;padding:1.5rem;gap:1.5rem;flex-wrap:wrap}}
.main{{flex:2;min-width:500px}}
.sidebar{{flex:1;min-width:280px}}
.card{{background:#13132b;border:1px solid #252545;border-radius:10px;padding:1.2rem;margin-bottom:1rem}}
.card h2{{color:#cc0000;font-size:1rem;margin-bottom:1rem;text-transform:uppercase;letter-spacing:1px}}
.stats{{display:flex;gap:.8rem;flex-wrap:wrap;margin-bottom:1rem}}
.stat{{background:#1a1a35;border:1px solid #252545;border-radius:8px;padding:1rem;text-align:center;min-width:100px;flex:1}}
.stat-value{{font-size:1.8rem;font-weight:bold;color:#cc0000}}
.stat-label{{color:#6c7086;font-size:.7rem;text-transform:uppercase;margin-top:.3rem}}
.btn{{background:rgba(204,0,0,.15);color:#cc0000;border:1px solid #cc0000;border-radius:6px;padding:.6rem 1.2rem;font-size:.85rem;cursor:pointer;text-decoration:none;font-family:inherit}}
.btn:hover{{background:rgba(204,0,0,.3)}}
.btn-sm{{padding:.3rem .8rem;font-size:.75rem}}
table{{width:100%;border-collapse:collapse}}
th,td{{text-align:left;padding:.6rem;border-bottom:1px solid #1e1e35;font-size:.8rem}}
th{{color:#6c7086;text-transform:uppercase;font-size:.7rem;letter-spacing:1px}}
form{{display:flex;gap:.5rem;flex-wrap:wrap}}
input,select{{background:#0d0d1a;border:1px solid #252545;border-radius:6px;padding:.6rem;color:#cdd6f4;font-family:inherit;font-size:.8rem;outline:none}}
input:focus,select:focus{{border-color:#cc0000}}
.finding-row{{display:flex;align-items:center;gap:1rem;padding:.4rem 0;border-bottom:1px solid #1e1e2e;font-size:.8rem}}
.finding-row span:first-child{{min-width:100px}}
.finding-row span:last-child{{margin-left:auto}}
.badge{{padding:.2rem .6rem;border-radius:999px;font-size:.7rem}}
.empty{{color:#6c7086;text-align:center;padding:2rem;font-size:.85rem}}
.footer{{text-align:center;padding:2rem;color:#4a4a6a;font-size:.7rem}}
.footer a{{color:#cc0000}}
@media(max-width:800px){{.layout{{flex-direction:column}}.main,.sidebar{{min-width:100%}}}}
</style>
<meta http-equiv="refresh" content="15">
</head><body>
<div class="header">
    <div>
        <h1>🥀 Briar Dashboard</h1>
        <p class="sub">Autonomous AI Pentester v0.3.0</p>
    </div>
</div>

<div class="layout">
<div class="main">
    <div class="stats">
        <div class="stat"><div class="stat-value">{len(scans)}</div><div class="stat-label">Scans</div></div>
        <div class="stat"><div class="stat-value">{total_findings}</div><div class="stat-label">Findings</div></div>
        <div class="stat"><div class="stat-value">12</div><div class="stat-label">Agents</div></div>
        <div class="stat"><div class="stat-value">11</div><div class="stat-label">Providers</div></div>
    </div>

    <div class="card">
        <h2>⚡ New Scan</h2>
        <form action="/scan" method="get" style="align-items:end">
            <div style="flex:2;min-width:200px"><input type="url" name="url" placeholder="https://target.com" required style="width:100%"></div>
            <div style="width:120px"><select name="provider">{provider_options}</select></div>
            <div style="width:110px"><select name="mode">
                <option value="quick">Quick (4)</option>
                <option value="standard" selected>Standard (8)</option>
                <option value="deep">Deep (12)</option>
            </select></div>
            <button type="submit" class="btn">Scan →</button>
        </form>
    </div>

    <div class="card">
        <h2>📋 Recent Scans</h2>
        {'<table><tr><th>Date</th><th>Target</th><th>Findings</th><th>Status</th></tr>'+scans_html+'</table>' if scans_html else '<p class="empty">No scans yet. Launch your first scan above.</p>'}
    </div>
</div>

<div class="sidebar">
    <div class="card">
        <h2>🔍 Latest Findings</h2>
        {findings_html if findings_html else '<p class="empty">No findings yet.</p>'}
    </div>

    <div class="card">
        <h2>💾 Workspaces</h2>
        {'<table><tr><th>Name</th><th>Target</th><th>F</th><th>A</th></tr>'+workspaces_html+'</table>' if workspaces_html else '<p class="empty">No workspaces yet.</p>'}
    </div>
</div>
</div>

<div class="footer">
    <a href="/docs">API Docs</a> · <a href="https://github.com/Stiimy/briar">GitHub</a> · <a href="/health">Health</a>
</div>
</body></html>"""

@app.get("/scan")
async def scan(url: str, provider: str = None, mode: str = "standard", background_tasks: BackgroundTasks = None):
    if not provider:
        provider = get_saved_provider() or "ollama"
    scan_record = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),"target": url,
        "provider": provider,"mode": mode,"status": "running","findings": 0
    }
    save_scan(scan_record)

    def run_scan():
        from briar.agents import run_agent
        all_agents = ["recon","injection","xss","ssrf","auth","authz","csrf","upload","traversal","rce","api","secrets"]
        agent_count = 12 if mode == "deep" else 4 if mode == "quick" else 8
        agents = all_agents[:agent_count]
        findings_count = 0
        for agent_name in agents:
            try:
                result = run_agent(agent_name, provider, url=url)
                if result and "error" not in result:
                    findings_count += 1
            except: pass
        scans = load_scans()
        for s in scans:
            if s["target"] == url and s.get("status") == "running":
                s["status"] = "done"
                s["findings"] = findings_count
                break
        os.makedirs(os.path.dirname(SCANS_FILE), exist_ok=True)
        with open(SCANS_FILE, "w") as f:
            json.dump(scans, f, indent=2)

    if background_tasks:
        background_tasks.add_task(run_scan)
    return {"message": "Scan started", "url": url, "provider": provider, "mode": mode}

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.3.0", "scans": len(load_scans())}

def main():
    print("🥀 Briar Dashboard → http://localhost:8233")
    uvicorn.run(app, host="0.0.0.0", port=8233)

if __name__ == "__main__":
    main()
