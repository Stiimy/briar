"""Briar Web Dashboard — FastAPI"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import os

app = FastAPI(title="Briar Dashboard 🥀", version="0.1.0")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Briar Dashboard 🥀</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                background: #0a0514; color: #cdd6f4; 
                font-family: 'JetBrains Mono', monospace;
                display: flex; align-items: center; justify-content: center;
                min-height: 100vh;
            }
            .container { text-align: center; padding: 2rem; }
            h1 { font-size: 3rem; color: #B847F0; margin-bottom: 1rem; }
            .subtitle { color: #6c7086; margin-bottom: 2rem; }
            .status { 
                background: #1e1e2e; border: 1px solid #313244;
                border-radius: 12px; padding: 2rem; max-width: 500px; margin: 0 auto;
            }
            .badge {
                display: inline-block; padding: 0.5rem 1.5rem;
                border-radius: 999px; font-size: 0.9rem; margin: 0.5rem;
            }
            .badge-green { background: rgba(166,227,161,0.15); color: #a6e3a1; border: 1px solid #a6e3a1; }
            .badge-purple { background: rgba(184,71,240,0.15); color: #B847F0; border: 1px solid #B847F0; }
            a { color: #89b4fa; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🥀 Briar</h1>
            <p class="subtitle">Autonomous AI Pentester</p>
            <div class="status">
                <p><span class="badge badge-green">✅ v0.1.0</span></p>
                <p><span class="badge badge-purple">🔄 MVP — Full features coming soon</span></p>
                <br>
                <p>📊 <a href="/docs">API Docs</a></p>
                <p>⭐ <a href="https://github.com/Stiimy/briar">GitHub</a></p>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}

def main():
    uvicorn.run(app, host="0.0.0.0", port=8233)

if __name__ == "__main__":
    main()
