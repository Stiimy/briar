# 🥀 Briar — Autonomous AI Pentester

> *Find vulnerabilities before hackers do. Free. Open Source. No Docker required.*

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-AGPL--3.0-green)](LICENSE)
[![Ollama](https://img.shields.io/badge/Ollama-Free-%23cba6f7)](https://ollama.ai)
[![Version](https://img.shields.io/badge/version-0.3.0-purple)](https://github.com/Stiimy/briar/releases)

Briar is an autonomous AI pentester. It scans web applications, injects real payloads, validates exploits, and generates professional security reports — powered by **11 AI providers** including a completely free local mode via Ollama.

---

## Quick Start

```bash
pip install briar
briar setup              # Pick your AI provider (Ollama = free)
briar scan -u https://target.com --quick
briar serve              # Web dashboard → http://localhost:8233
```

---

## Features

| Category | Details |
|----------|---------|
| 🤖 **11 AI Providers** | Ollama (free, local), OpenAI, Claude, DeepSeek, Groq, Mistral, xAI/Grok, Google/Gemini, OpenRouter, Together, Custom |
| 🛡️ **10 OWASP Agents** | Recon, Injection, XSS, SSRF, Auth, AuthZ, CSRF, Upload, Traversal, RCE, API, Secrets |
| 🎯 **No Exploit, No Report** | Every High/Critical finding is replayed and confirmed before reporting |
| 🔌 **Blackbox + Whitebox** | Works with just a URL. Add `-r /path/to/source` for code-aware analysis |
| 📡 **Port Scanning** | 24 common ports scanned during recon phase |
| 📄 **Reports** | Markdown, Word (.docx), Excel (.xlsx), Obsidian vault + canvas mindmap |
| 🎨 **Slides** | PowerPoint (.pptx) + HTML presentation |
| 📊 **Charts** | Severity pie chart, agent bar chart |
| 🌐 **Dashboard** | Web UI on port 8233 (FastAPI) with scan launcher |
| 💾 **Workspaces** | Resume interrupted scans, checkpoint after every agent |
| ⚙️ **YAML Config** | Authenticated scanning, login flows, custom rules (avoid/focus paths) |
| 🐳 **No Docker Required** | Native Python. pip install and go. Docker optional for server mode. |

---

## Usage

```bash
# Quick scan (4 agents)
briar scan -u https://target.com --quick

# Standard scan (8 agents)  
briar scan -u https://target.com

# Deep scan (all 12 agents + browser exploits)
briar scan -u https://target.com --deep

# With source code (whitebox mode)
briar scan -u https://target.com -r /path/to/repo

# With DeepSeek provider (set env var first)
export DEEPSEEK_API_KEY=sk-xxx
briar scan -u https://target.com -p deepseek

# With config file (authenticated scanning)
briar scan -c juice-shop.yaml

# Resume an interrupted scan
briar scan --resume workspace-name

# List saved workspaces
briar workspaces
```

---

## Config File (YAML)

```yaml
# juice-shop.yaml — example for OWASP Juice Shop
target:
  url: http://localhost:3000

provider: deepseek
mode: deep
output: ./reports/juice-shop

authentication:
  login_url: /rest/user/login
  method: json
  credentials:
    email: test@test.com
    password: test123
  success_condition: "status=200"

rules:
  avoid:
    - path: /logout
    - path: /score-board
  focus:
    - path: /api
    - path: /rest
```

---

## Architecture

```
briar/
├── agents/          12 security agents (recon, injection, xss, ssrf,
│                    auth, authz, csrf, upload, traversal, rce, api, secrets)
├── providers/       11 AI backends (Ollama, OpenAI, Claude, DeepSeek, ...)
├── core/            HTTP client, exploit validator, workspace manager
├── exploits/        Selenium browser exploits + CLI payload injector
├── reports/         Markdown, Word, Excel, Obsidian generators
├── charts/          Pie chart + bar chart (matplotlib)
├── slides/          PowerPoint + HTML slide decks
├── cli.py           Main CLI (click + rich)
├── web.py           FastAPI dashboard (port 8233)
├── worker.py        Background job queue worker
└── config.py        YAML config loader
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

> *"No exploit, no report."* — Briar validates every High/Critical finding before you see it.

**License:** AGPL-3.0 — Free. Forever.
