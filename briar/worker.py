"""Briar Worker — background scan executor with file-based job queue"""
import json, os, time, sys
from pathlib import Path

JOBS_FILE = os.path.expanduser("~/.briar/jobs.json")

def load_jobs():
    try:
        with open(JOBS_FILE) as f:
            return json.load(f)
    except:
        return []

def save_jobs(jobs):
    os.makedirs(os.path.dirname(JOBS_FILE), exist_ok=True)
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2)

def process_job(job):
    """Execute a single scan job"""
    from briar.agents import run_agent
    url = job["url"]
    provider = job.get("provider", "ollama")
    mode = job.get("mode", "standard")
    agent_count = 12 if mode == "deep" else 4 if mode == "quick" else 8

    all_agents = ["recon","injection","xss","ssrf","auth","authz","csrf","upload","traversal","rce","api","secrets"]
    agents = all_agents[:agent_count]
    findings = 0
    errors = 0

    for agent_name in agents:
        try:
            result = run_agent(agent_name, provider, url=url)
            if result and "error" not in result:
                findings += 1
        except:
            errors += 1

    return {"url": url, "findings": findings, "errors": errors, "agents_ran": len(agents)}

def main():
    print("🥀 Briar Worker v0.1.0 — waiting for jobs...")
    while True:
        jobs = load_jobs()
        pending = [j for j in jobs if j.get("status") == "pending"]

        for job in pending:
            print(f"[Worker] Processing: {job['url']} ({job.get('provider','ollama')})")
            job["status"] = "running"
            save_jobs(jobs)

            try:
                result = process_job(job)
                job["status"] = "done"
                job["result"] = result
                job["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                print(f"[Worker] Done: {job['url']} — {result['findings']} findings")
            except Exception as e:
                job["status"] = "failed"
                job["error"] = str(e)
                print(f"[Worker] Failed: {job['url']} — {e}")

            save_jobs(jobs)

        time.sleep(5)

if __name__ == "__main__":
    main()
