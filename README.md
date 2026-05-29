# 🥀 Briar — Autonomous AI Pentester

> *Find vulnerabilities before hackers do. Free. Open Source. Ollama-powered.*
[![Version](https://img.shields.io/badge/version-0.1.0-purple)](https://github.com/Stiimy/briar/releases)

[![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-AGPL--3.0-green)](LICENSE)
[![Ollama](https://img.shields.io/badge/Ollama-Free-%23cba6f7)](https://ollama.ai)
[![Version](https://img.shields.io/badge/version-0.1.0-purple)](https://github.com/Stiimy/briar/releases)
[![Stars](https://img.shields.io/badge/dynamic/json?color=yellow&label=Stars&query=stargazers_count&url=https://api.github.com/repos/Stiimy/briar)](https://github.com/Stiimy/briar)

Briar is an autonomous, white-box AI pentester. It analyzes source code, identifies attack vectors, and generates professional security reports — powered by **13 AI providers** including free local Ollama.
[![Version](https://img.shields.io/badge/version-0.1.0-purple)](https://github.com/Stiimy/briar/releases)

## Quick Start

```bash
pip install briar
briar setup
briar scan -u https://target.com -r /path/to/source
briar serve  # Web dashboard → http://localhost:8233
```

## Features

| Category | Details |
|----------|---------|
| 🤖 **AI Providers** | Ollama (free), OpenAI, Claude, DeepSeek, Groq, Mistral + 7 more |
| 🛡️ **Security Agents** | Injection, XSS, SSRF, Auth, AuthZ, CSRF, Upload, Traversal, RCE, API, Secrets |
| 📄 **Reports** | Markdown, Word (.docx), Excel (.xlsx), Obsidian (mindmap + linked notes) |
| 🎨 **Slides** | PowerPoint (.pptx), HTML/Canva-style |
| 📊 **Charts** | Camemberts, bar charts, severity distribution |
| 🌐 **Dashboard** | Web UI on port 8233 (FastAPI) |
| 🇫🇷 **Language** | Bilingual FR/EN reports |

## Architecture

```
briar/
├── agents/          # 11 OWASP security agents
├── providers/       # 6 AI providers (13 planned)
├── reports/         # 5 report formats
├── slides/          # PPTX + HTML slide decks
├── charts/          # Matplotlib chart generation
├── exploits/        # Selenium + CLI exploit engine
├── cli.py           # Main CLI
└── web.py           # FastAPI dashboard
```

---

## License

AGPL-3.0 — age of stars.
