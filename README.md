# 🥀 Briar — Autonomous AI Pentester

> *Find vulnerabilities before hackers do. Free. Open Source. No Docker.*

[![PyPI](https://img.shields.io/pypi/v/briar-pentest?color=cc0000)](https://pypi.org/project/briar-pentest/)
[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-AGPL--3.0-green)](LICENSE)
[![Stars](https://img.shields.io/github/stars/Stiimy/briar?color=yellow)](https://github.com/Stiimy/briar)

Briar is an autonomous AI pentester. It scans web applications, injects **real payloads**, validates exploits, and generates professional security reports — powered by **11 AI providers** including a completely free local mode via Ollama.

```
pip install briar-pentest && briar setup && briar scan -u https://target.com --deep
```

---

## What Briar Found — Real Example

Against a file server on port 666 (ransomware-like deployment):

| # | Vulnerability | Severity | CVSS |
|---|--------------|----------|------|
| 1 | Path Traversal | 🔴 Critical | 9.1 |
| 2 | IDOR — File Enumeration | 🟠 High | 7.5 |
| 3 | Unauthenticated File Access | 🔴 Critical | 9.1 |
| 4 | Arbitrary File Upload (RCE) | 🔴 Critical | 9.8 |
| 5 | Directory Listing | 🟠 High | 6.5 |
| 6 | HTTP Verb Tampering | 🟡 Medium | 5.0 |
| 7 | Missing Security Headers | 🟢 Low | 3.1 |
| 8 | SSRF via URL param | 🟠 High | 8.6 |
| 9 | Reflected XSS | 🟠 High | 7.2 |
| 10 | Sensitive File Exposure | 🟡 Medium | 5.3 |

**Each finding includes**: copy-paste curl PoC, CVSS score, tech-specific remediation (nginx/Apache/Flask/Express code).

---

## Features

| Category | Details |
|----------|---------|
| 🤖 **11 AI Providers** | Ollama (free, local), OpenAI, Claude, DeepSeek, Groq, Mistral, xAI/Grok, Google/Gemini, OpenRouter, Together, Custom |
| 🛡️ **12 Security Agents** | Recon, Injection, XSS, SSRF, Auth, AuthZ, CSRF, Upload, Traversal, RCE, API, Secrets |
| 🎯 **No Exploit, No Report** | Every High/Critical finding replayed and confirmed before reporting |
| 🔌 **Blackbox + Whitebox** | Works with just a URL. Add `-r /path/to/source` for code-aware analysis |
| 📡 **Port Scanning** | 24 common ports scanned during recon |
| 📓 **LLM-Wiki (Obsidian)** | Interlinked vault, frontmatter YAML, index, log, canvas mindmap — Karpathy pattern |
| 📄 **Reports** | Markdown, Word (.docx), Excel (.xlsx), HTML slides |
| 📊 **Charts** | Donut severity, heatmap severity×endpoint, bar charts (type + agent) |
| 🌐 **Dashboard** | Web UI on port 8233 (FastAPI) with live scan launcher |
| 💾 **Workspaces** | Resume interrupted scans, checkpoint after every agent |
| ⚙️ **YAML Config** | Authenticated scanning, login flows, custom rules (avoid/focus paths) |
| 🐳 **No Docker Required** | Native Python. pip install and go. Docker optional. |

---

## Briar vs Shannon

| Feature | Briar | Shannon |
|---------|:-----:|:-------:|
| AI Providers | **11** (Ollama free) | 1 (Claude paid) |
| OWASP Categories | **10** | 5 |
| Blackbox (no source) | ✅ | ❌ Whitebox only |
| Port Scanning | ✅ | ❌ |
| Docker Required | ❌ Native Python | ✅ |
| Dashboard | ✅ Free | 💰 Pro only |
| Obsidian LLM-Wiki | ✅ | ❌ |
| Config YAML | ✅ | ✅ |
| Auth Support | Form login | 2FA/SSO/Magic links |
| Benchmark | Not yet | 96% XBOW |

---

## Quick Start

```bash
# Install
pip install briar-pentest

# Configure (pick Ollama for free local AI)
briar setup

# Quick scan
briar scan -u https://target.com --quick

# Deep scan with browser exploits
briar scan -u https://target.com --deep

# With config file (authenticated)
briar scan -c config.yaml

# Resume interrupted scan
briar scan --resume workspace-name

# Web dashboard
briar serve  # → http://localhost:8233
```

---

## Config File (YAML)

```yaml
target:
  url: http://localhost:3000
provider: deepseek
mode: deep

authentication:
  login_url: /rest/user/login
  method: json
  credentials:
    email: admin@test.com
    password: admin123

rules:
  avoid:
    - path: /logout
  focus:
    - path: /api
    - path: /rest
```

---

## Commands

```
briar             Show banner + version
briar status      Show configured provider + API key
briar setup       Pick AI provider (interactive)
briar scan        Run pentest (-u URL, --quick, --deep, -c config.yaml)
briar serve       Start web dashboard (:8233)
briar workspaces  List saved workspaces
briar resume      Resume an interrupted scan
```

---

## Install from Source

```bash
git clone https://github.com/Stiimy/briar
cd briar
pip install -e .
briar setup
```

---

**License:** AGPL-3.0 — Free. Forever.

*"No exploit, no report."*
