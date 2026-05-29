# 🥀 Briar — Autonomous AI Pentester

> *Find vulnerabilities before hackers do. 100% open source, 100% free.*

[![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-AGPL--3.0-green)](LICENSE)
[![Ollama](https://img.shields.io/badge/Ollama-Free-%23cba6f7)](https://ollama.ai)

Briar is an autonomous, white-box AI pentester that analyzes your source code, identifies attack vectors, and executes real exploits — all powered by local AI via Ollama.

**🇫🇷 Made in France | Rapports bilingues FR/EN**

## Quick Start

```bash
# Install
pip install briar

# Configure (one-time)
briar setup

# Scan
briar scan -u https://target.com -r /path/to/source

# Web Dashboard
briar serve  # → http://localhost:8233
```

## Features

- 🧠 **12 OWASP agents** — Injection, XSS, SSRF, Auth, CSRF, RCE...
- 🤖 **13 AI providers** — Ollama (free), OpenAI, Claude, Groq, Mistral...
- 📄 **5 report formats** — MD, Word, Excel, Obsidian, PPTX
- 🖼️ **Auto screenshots** — Selenium-powered exploit captures
- 📊 **Charts & stats** — Camemberts, barres, tendances
- 🌐 **Web Dashboard** — Port 8233
- 🐳 **Docker ready** — `docker-compose up`

## Why Briar?

| | Shannon (upstream) | Briar |
|---|-------------------|-------|
| Price | $$$ (Anthropic API) | Free (Ollama) |
| Providers | 1 | 13 |
| Reports | 1 format | 5 formats |
| Language | EN only | FR/EN bilingual |
| Docker | Mandatory | Optional |

## License

AGPL-3.0 — Free forever.
