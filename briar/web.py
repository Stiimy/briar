"""Briar Web Dashboard — FastAPI + Jinja2 + HTMX 🥀"""
from fastapi import FastAPI, BackgroundTasks, Request, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import uvicorn, os, json
from datetime import datetime
from pathlib import Path

app = FastAPI(title="Briar Dashboard", version="0.4.17")

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

SCANS_FILE = os.path.expanduser("~/.briar/scans.json")
WORKSPACES_DIR = os.path.expanduser("~/.briar/workspaces")
SEV_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}
SEV_CLASS = {"Critical": "b-crit", "High": "b-high", "Medium": "b-med", "Low": "b-low", "Info": "b-info"}
SEV_COLOR = {"Critical": "#cba6f7", "High": "#f38ba8", "Medium": "#fab387", "Low": "#f9e2af", "Info": "#89b4fa"}

def load_scans():
    try:
        with open(SCANS_FILE) as f:
            return json.load(f)
    except: return []

def load_workspace_findings(name):
    path = os.path.join(WORKSPACES_DIR, name, "findings.json")
    try:
        with open(path) as f:
            return json.load(f)
    except: return []

def get_saved_provider():
    config_file = os.path.expanduser("~/.briar/config")
    if not os.path.exists(config_file): return None
    try:
        with open(config_file) as f:
            for line in f:
                if line.startswith("PROVIDER="):
                    return line.strip().split("=", 1)[1]
    except: pass
    return None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    scans = load_scans()
    scans_sorted = sorted(scans, key=lambda s: s.get("date", ""), reverse=True)
    total_findings = sum(s.get("findings", 0) for s in scans)
    
    # Count by severity across all scans
    sev_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Info": 0}
    
    return templates.TemplateResponse("home.html", {
        "request": request,
        "scans": scans_sorted[:20],
        "total_scans": len(scans),
        "total_findings": total_findings,
        "saved_provider": get_saved_provider() or "ollama",
        "sev_counts": sev_counts,
    })

@app.get("/scan/{scan_id}", response_class=HTMLResponse)
async def scan_detail(request: Request, scan_id: str):
    workspaces = [d for d in os.listdir(WORKSPACES_DIR) if os.path.isdir(os.path.join(WORKSPACES_DIR, d))]
    ws_name = None
    for ws in workspaces:
        if scan_id in ws:
            ws_name = ws
            break
    
    findings = load_workspace_findings(ws_name) if ws_name else []
    findings_sorted = sorted(findings, key=lambda f: SEV_ORDER.get(f.get("severity", "Info"), 99))
    
    critical = sum(1 for f in findings_sorted if f.get("severity") == "Critical")
    high = sum(1 for f in findings_sorted if f.get("severity") == "High")
    medium = sum(1 for f in findings_sorted if f.get("severity") == "Medium")
    low = sum(1 for f in findings_sorted if f.get("severity") == "Low")
    confirmed = sum(1 for f in findings_sorted if f.get("confirmed"))
    
    return templates.TemplateResponse("scan_detail.html", {
        "request": request,
        "scan_id": scan_id,
        "findings": findings_sorted,
        "total": len(findings_sorted),
        "critical": critical, "high": high, "medium": medium, "low": low,
        "confirmed": confirmed,
        "sev_class": SEV_CLASS, "sev_color": SEV_COLOR,
    })

@app.get("/scan", response_class=HTMLResponse)
async def launch_scan(url: str, provider: str = None, mode: str = "standard", background_tasks: BackgroundTasks = None):
    if not provider:
        provider = get_saved_provider() or "ollama"
    
    scan_id = datetime.now().strftime("%Y%m%d%H%M%S")
    scan_record = {
        "scan_id": scan_id,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "target": url, "provider": provider, "mode": mode,
        "status": "running", "findings": 0
    }
    
    scans = load_scans()
    scans.append(scan_record)
    os.makedirs(os.path.dirname(SCANS_FILE), exist_ok=True)
    with open(SCANS_FILE, "w") as f:
        json.dump(scans, f, indent=2)

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
            if s.get("scan_id") == scan_id:
                s["status"] = "done"
                s["findings"] = findings_count
                break
        with open(SCANS_FILE, "w") as f:
            json.dump(scans, f, indent=2)

    if background_tasks:
        background_tasks.add_task(run_scan)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.4.17", "scans": len(load_scans())}

def main():
    print("Briar Dashboard -> http://localhost:8233")
    uvicorn.run(app, host="0.0.0.0", port=8233)

if __name__ == "__main__":
    main()
