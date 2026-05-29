"""Briar Workspace — checkpoint and resume scans 💾"""
import os, json, time
from pathlib import Path

WORKSPACES_DIR = os.path.expanduser("~/.briar/workspaces")

class Workspace:
    """Saves scan progress so crashed/deep scans can resume."""

    def __init__(self, target: str, mode: str = "standard"):
        safe_target = target.replace("://", "_").replace("/", "_").replace(":", "_")[:60]
        self.name = f"{safe_target}_{int(time.time())}"
        self.dir = os.path.join(WORKSPACES_DIR, self.name)
        self.state_file = os.path.join(self.dir, "state.json")
        self.findings_file = os.path.join(self.dir, "findings.json")
        self._state = {"target": target, "mode": mode, "agents_completed": [], "findings_count": 0}
        self._findings = []
        os.makedirs(self.dir, exist_ok=True)

    def save(self):
        """Persist current state to disk."""
        with open(self.state_file, "w") as f:
            json.dump(self._state, f, indent=2)
        with open(self.findings_file, "w") as f:
            json.dump(self._findings, f, indent=2)

    def checkpoint_agent(self, agent_name: str, findings: list):
        """Record that an agent completed."""
        self._state["agents_completed"].append(agent_name)
        self._state["findings_count"] += len(findings)
        self._findings.extend(findings)
        self.save()

    def get_remaining_agents(self, all_agents: list) -> list:
        """Return agents that haven't run yet."""
        return [a for a in all_agents if a not in self._state["agents_completed"]]

    def get_findings(self) -> list:
        return self._findings

    @staticmethod
    def load(workspace_name: str) -> "Workspace":
        """Load an existing workspace to resume."""
        dir_path = os.path.join(WORKSPACES_DIR, workspace_name)
        if not os.path.exists(dir_path):
            raise FileNotFoundError(f"Workspace not found: {workspace_name}")

        ws = Workspace.__new__(Workspace)
        ws.dir = dir_path
        ws.state_file = os.path.join(dir_path, "state.json")
        ws.findings_file = os.path.join(dir_path, "findings.json")

        with open(ws.state_file) as f:
            ws._state = json.load(f)
        try:
            with open(ws.findings_file) as f:
                ws._findings = json.load(f)
        except FileNotFoundError:
            ws._findings = []

        ws.name = workspace_name
        return ws

    @staticmethod
    def list_workspaces() -> list:
        """List all saved workspaces."""
        if not os.path.exists(WORKSPACES_DIR):
            return []
        return sorted([
            d for d in os.listdir(WORKSPACES_DIR)
            if os.path.isdir(os.path.join(WORKSPACES_DIR, d))
        ], reverse=True)
