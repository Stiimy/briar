"""Briar Web Dashboard — FastAPI + stats + scan launcher 🥀"""
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn, os, json
from datetime import datetime

app = FastAPI(title="Briar Dashboard", version="0.1.0")

SCANS_FILE = os.path.expanduser("~/.briar/scans.json")

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

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    scans = load_scans()
    scans_html = ""
    for s in scans[-10:]:
        scans_html += f"""
        <tr>
            <td>{s['date']}</td>
            <td style="color:#89b4fa">{s['target']}</td>
            <td>{s['findings']}</td>
            <td><span class="badge badge-{'green' if s['status']=='done' else 'yellow'}">{s['status']}</span></td>
        </tr>"""
    
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Briar Dashboard</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a0514;color:#cdd6f4;font-family:'JetBrains Mono',monospace;padding:2rem}}
h1{{color:#B847F0;font-size:2.5rem;margin-bottom:.5rem}}
h2{{color:#B847F0;margin:2rem 0 1rem}}
.subtitle{{color:#6c7086;margin-bottom:2rem}}
.card{{background:#1e1e2e;border:1px solid #313244;border-radius:12px;padding:1.5rem;margin:1rem 0;max-width:800px}}
.stats{{display:flex;gap:1rem;margin:1rem 0;flex-wrap:wrap}}
.stat{{background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:1rem;text-align:center;min-width:120px}}
.stat-value{{font-size:2rem;font-weight:bold;color:#B847F0}}
.stat-label{{color:#6c7086;font-size:.8rem}}
.btn{{background:rgba(184,71,240,.2);color:#B847F0;border:1px solid #B847F0;border-radius:8px;padding:.7rem 1.5rem;font-size:1rem;cursor:pointer;text-decoration:none;display:inline-block;margin:.5rem}}
.btn:hover{{background:rgba(184,71,240,.4)}}
table{{width:100%;border-collapse:collapse;margin:1rem 0}}
th,td{{text-align:left;padding:.7rem;border-bottom:1px solid #313244}}
th{{color:#6c7086;font-size:.8rem;text-transform:uppercase}}
.badge{{padding:.2rem .8rem;border-radius:999px;font-size:.8rem}}
.badge-green{{background:rgba(166,227,161,.15);color:#a6e3a1}}
.badge-yellow{{background:rgba(249,226,175,.15);color:#f9e2af}}
a{{color:#89b4fa;text-decoration:none}}
form{{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center}}
input{{background:#0a0514;border:1px solid #313244;border-radius:6px;padding:.7rem;color:#cdd6f4;font-family:inherit;font-size:.9rem}}
input:focus{{outline:none;border-color:#B847F0}}
</style></head><body>
<h1>Briar Dashboard</h1>
<p class="subtitle">Autonomous AI Pentester — v0.1.0</p>

<div class="stats">
    <div class="stat"><div class="stat-value">{len(scans)}</div><div class="stat-label">Total Scans</div></div>
    <div class="stat"><div class="stat-value">{sum(s['findings'] for s in scans)}</div><div class="stat-label">Findings</div></div>
    <div class="stat"><div class="stat-value">12</div><div class="stat-label">Agents</div></div>
    <div class="stat"><div class="stat-value">9</div><div class="stat-label">Providers</div></div>
</div>

<div class="card">
    <h2>New Scan</h2>
    <form action="/scan" method="get">
        <input type="url" name="url" placeholder="https://target.com" required style="flex:1;min-width:250px">
        <input type="text" name="provider" placeholder="ollama" value="ollama" style="width:120px">
        <button type="submit" class="btn">Scan</button>
    </form>
</div>

<div class="card">
    <h2>Recent Scans</h2>
    <table>
        <tr><th>Date</th><th>Target</th><th>Findings</th><th>Status</th></tr>
        {scans_html if scans_html else '<tr><td colspan="4" style="color:#6c7086">No scans yet. Run your first scan!</td></tr>'}
    </table>
</div>

<p style="color:#6c7086;margin-top:3rem;text-align:center">
    <a href="/docs">API Docs</a> | <a href="https://github.com/Stiimy/briar">GitHub</a> | v0.1.0
</p>
</body></html>"""

@app.get("/scan")
async def scan(url: str, provider: str = "ollama", background_tasks: BackgroundTasks = None):
    """Launch a new scan"""
    scan_record = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "target": url,
        "provider": provider,
        "status": "running",
        "findings": 0
    }
    save_scan(scan_record)
    
    # Background scan
    def run_scan():
        from briar.agents import run_agent
        findings = 0
        for agent_name in ["injection","xss","ssrf","auth"]:
            try:
                result = run_agent(agent_name, provider, url=url)
                if result and "error" not in result:
                    findings += 1
            except: pass
        scan_record["status"] = "done"
        scan_record["findings"] = findings
        save_scan(scan_record)
    
    if background_tasks:
        background_tasks.add_task(run_scan)
    
    return {"message": "Scan started", "url": url, "provider": provider}

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0", "scans": len(load_scans())}

def main():
    print("🥀 Briar Dashboard → http://localhost:8233")
    uvicorn.run(app, host="0.0.0.0", port=8233)

if __name__ == "__main__":
    main()
