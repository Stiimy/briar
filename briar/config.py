"""Briar Config Loader — YAML config for authenticated scans 📋"""
import os, yaml

DEFAULT_CONFIG = {
    "target": {"url": ""},
    "mode": "standard",
    "provider": "ollama",
    "output": "./reports",
    "authentication": None,
    "rules": {"avoid": [], "focus": []},
}

def load_config(path: str) -> dict:
    """Load a YAML configuration file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path) as f:
        config = yaml.safe_load(f) or {}
    # Merge with defaults
    merged = {**DEFAULT_CONFIG, **config}
    merged["rules"] = {**DEFAULT_CONFIG["rules"], **config.get("rules", {})}
    return merged

def build_login_flow(config: dict) -> dict:
    """Extract authentication details from config."""
    auth = config.get("authentication")
    if not auth:
        return None
    return {
        "login_url": auth.get("login_url", "/login"),
        "method": auth.get("method", "form"),
        "credentials": auth.get("credentials", {}),
        "success_condition": auth.get("success_condition", "status=200"),
        "login_flow": auth.get("login_flow", []),
    }
