"""Briar Scan Diff — compare two scans to find new/resolved findings 🔍"""
import json, os
from pathlib import Path

WORKSPACES_DIR = os.path.expanduser("~/.briar/workspaces")

def load_workspace(ws_name: str) -> tuple:
    """Load findings and state from a workspace."""
    findings_path = os.path.join(WORKSPACES_DIR, ws_name, "findings.json")
    state_path = os.path.join(WORKSPACES_DIR, ws_name, "state.json")
    findings = []
    state = {}
    try:
        with open(findings_path) as f:
            findings = json.load(f)
    except: pass
    try:
        with open(state_path) as f:
            state = json.load(f)
    except: pass
    return findings, state

def finding_key(f: dict) -> str:
    """Generate a stable key for comparing findings."""
    ftype = f.get("type", "?").replace(" ⚠️", "").strip()
    endpoint = f.get("url", "?")
    param = f.get("param", "")
    agent = f.get("agent", "?")
    return f"{ftype}|{endpoint}|{param}|{agent}"

def diff_workspaces(ws1: str, ws2: str) -> dict:
    """Compare two workspaces. Returns new, fixed, and unchanged findings."""
    f1, s1 = load_workspace(ws1)
    f2, s2 = load_workspace(ws2)

    keys1 = {finding_key(f): f for f in f1}
    keys2 = {finding_key(f): f for f in f2}

    new_findings = []
    fixed_findings = []
    unchanged = []
    changed_severity = []

    # Findings in ws2 but not in ws1 = new
    for key, f in keys2.items():
        if key not in keys1:
            new_findings.append({**f, "diff_status": "new"})
        else:
            old = keys1[key]
            if old.get("severity") != f.get("severity"):
                changed_severity.append({**f, "diff_status": "changed",
                    "old_severity": old.get("severity", "?")})
            else:
                unchanged.append({**f, "diff_status": "unchanged"})

    # Findings in ws1 but not in ws2 = fixed
    for key, f in keys1.items():
        if key not in keys2:
            fixed_findings.append({**f, "diff_status": "fixed"})

    return {
        "ws1": ws1, "ws2": ws2,
        "new": new_findings,
        "fixed": fixed_findings,
        "changed": changed_severity,
        "unchanged": unchanged,
        "summary": {
            "total_old": len(f1),
            "total_new": len(f2),
            "new_findings": len(new_findings),
            "fixed_findings": len(fixed_findings),
            "changed_severity": len(changed_severity),
            "unchanged": len(unchanged),
        }
    }
