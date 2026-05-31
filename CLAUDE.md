# Briar — Agent Instructions

## Project
Briar is an autonomous AI pentester. Python 3.10+, AGPL-3.0. Published on PyPI as `briar-pentest`.

## Architecture
```
briar/
├── agents/        12 security agents (analyzer.py = LLM brain, rest = attack agents)
├── providers/     11 AI backends (Ollama free, OpenAI, Claude, DeepSeek...)
├── core/          http.py (shared HTTP client), params.py (attack params), 
│                  validator.py (replay exploits), workspace.py (checkpoint/resume)
├── exploits/      browser.py (Selenium) and CLI injector
├── reports/       generator.py (Markdown/Word/Excel), obsidian.py (LLM-Wiki)
├── charts/        generator.py (donut, heatmap, bar charts)
├── slides/        pptx_gen.py (PPTX + HTML slides)
├── cli.py         Main CLI (click + rich), entry point
├── web.py         FastAPI dashboard (:8233)
├── worker.py      Background job queue
└── config.py      YAML config loader
```

## Commit style
- Short, no emojis, no periods
- French or English ok
- Anime/gaming references encouraged
- Only bump 3rd version digit (0.4.x → 0.4.x+1)

## Key principles
- Agents do real HTTP work first, then use LLM for analysis
- "No exploit, no report" — High/Critical findings replayed before reporting
- No hardcoded defaults — user must configure provider via `briar setup`
- Reports are tech-specific — remediation targets actual detected stack
- Workspaces persist — scans can resume after crash

## Dependencies
Core: requests, click, rich, fastapi, uvicorn
Optional: python-docx, openpyxl, python-pptx, matplotlib, selenium, openai, anthropic

## Testing
- `python -m briar` — banner + help
- `python -m briar status` — show config
- `python -m briar scan -u https://httpbin.org --quick` — safe test
- Use DeepSeek for tests: set `DEEPSEEK_API_KEY` env var
