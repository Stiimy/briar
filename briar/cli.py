#!/usr/bin/env python3
"""Briar CLI — Autonomous AI Pentester 🥀"""
import sys, os, click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def check_ollama():
    from briar.providers import get_provider
    try:
        p = get_provider("ollama")
        if p.health_check():
            models = p.list_models()
            console.print(f"[green]Ollama ready — {len(models)} models[/green]")
            return p
    except: pass
    console.print("[yellow]Ollama not running[/yellow]")
    return None

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Briar — Autonomous AI Pentester"""
    pass

@cli.command()
def setup():
    """Configure Briar"""
    console.print(Panel.fit("[bold green]Briar Setup[/bold green]\nPick your AI provider:", title="Setup"))
    
    provider_list = [
        ("1", "Ollama", "Free, local, no API key"),
        ("2", "OpenAI", "GPT-4o, paid API"),
        ("3", "Anthropic", "Claude, paid API"),
        ("4", "DeepSeek", "V3/R1, cheap API"),
        ("5", "Groq", "Fast, free tier available"),
        ("6", "Mistral", "European, paid API"),
        ("7", "xAI", "Grok-3, paid API"),
        ("8", "Google", "Gemini 2.5, free tier"),
        ("9", "OpenRouter", "200+ models, paid"),
        ("10", "Together", "Open-source models"),
        ("11", "Custom", "OpenAI-compatible endpoint"),
    ]
    for num, name, desc in provider_list:
        console.print(f"  [cyan]{num}. {name}[/cyan] — [dim]{desc}[/dim]")
    
    choice = click.prompt("Choice", type=int, default=1)
    providers = {
        1:"ollama",2:"openai",3:"anthropic",4:"deepseek",5:"groq",6:"mistral",
        7:"xai",8:"google",9:"openrouter",10:"together",11:"custom"
    }
    provider = providers.get(choice, "ollama")
    
    os.makedirs(os.path.expanduser("~/.briar"), exist_ok=True)
    config = f"PROVIDER={provider}\n"
    if provider == "ollama":
        config += "OLLAMA_HOST=localhost\nOLLAMA_PORT=11434\nOLLAMA_MODEL=minimax-m2.5:latest\n"
    elif provider == "custom":
        config += f"CUSTOM_ENDPOINT={click.prompt('API Endpoint URL')}\n"
        config += f"CUSTOM_API_KEY={click.prompt('API Key', hide_input=True)}\n"
        config += f"CUSTOM_MODEL={click.prompt('Model name', default='gpt-4o')}\n"
    else:
        config += f"{provider.upper()}_API_KEY={click.prompt('API Key', hide_input=True)}\n"
    with open(os.path.expanduser("~/.briar/config"), "w") as f:
        f.write(config)
    console.print(f"\n[green]Provider: {provider}[/green]")

@cli.command()
@click.option("-u", "--url", required=True, help="Target URL")
@click.option("-r", "--repo", help="Source code path")
@click.option("-p", "--provider", default="ollama", help="AI provider")
@click.option("-o", "--output", default="./reports", help="Output dir")
@click.option("--quick", is_flag=True, help="Quick scan (4 agents)")
@click.option("--deep", is_flag=True, help="Deep scan (all 12 agents + browser)")
def scan(url, repo, provider, output, quick, deep):
    """Run a pentest scan"""
    mode = "deep" if deep else "quick" if quick else "standard"
    agent_count = 12 if deep else 4 if quick else 8
    
    console.print(Panel.fit(
        f"[bold red]Briar Scan[/bold red]\n"
        f"[cyan]{url}[/cyan] | [yellow]{provider}[/yellow] | [dim]{mode} ({agent_count} agents)[/dim]",
        title="Scan"))
    
    if provider == "ollama" and not check_ollama():
        console.print("[red]Start Ollama first[/red]"); sys.exit(1)
    
    findings = []
    all_agents = ["recon","injection","xss","ssrf","auth","authz","csrf","upload","traversal","rce","api","secrets"]
    agents_to_run = all_agents[:agent_count]
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("[cyan]Scanning...", total=len(agents_to_run))
        from briar.agents import run_agent
        
        for agent_name in agents_to_run:
            progress.update(task, description=f"[yellow]{agent_name}...")
            try:
                result = run_agent(agent_name, provider, url=url, repo_path=repo)
                if result and "error" not in result:
                    findings.append(result)
            except Exception as e:
                findings.append({"type": agent_name, "severity": "Error", "url": url, "analysis": str(e), "agent": agent_name})
            progress.advance(task)
        
        # Deep mode: active exploits
        if deep:
            from urllib.parse import urlparse, parse_qs
            
            # Extract params from recon findings
            params_list = []
            recon_result = next((f for f in findings if f.get("agent") == "Recon"), None)
            if recon_result and recon_result.get("urls_sample"):
                for u in recon_result["urls_sample"]:
                    try:
                        parsed = urlparse(u)
                        params = list(parse_qs(parsed.query).keys())
                        params_list.extend(params)
                    except: pass
            params_list = list(set(params_list)) or ["q", "id", "page"]
            
            # CLI exploits — SQL injection
            from briar.exploits.browser import CLIExploiter
            progress.update(task, description="[yellow]SQL injection exploits...")
            for param in params_list[:5]:
                try:
                    result = CLIExploiter.test_sql_injection(url, param)
                    anomalies = [t for t in result.get("tests", []) if t.get("status") != 200]
                    if anomalies:
                        findings.append({
                            "type": "SQL Injection (exploit)", "severity": "High",
                            "agent": "Exploiter", "url": url, "param": param,
                            "tests": len(anomalies),
                            "analysis": f"SQLi anomalies detected on param '{param}': {len(anomalies)}/{len(result['tests'])} payloads"
                        })
                except: pass
            
            # CLI exploits — SSRF
            progress.update(task, description="[yellow]SSRF exploits...")
            for param in ["url", "redirect", "callback", "next", "return"][:3]:
                try:
                    result = CLIExploiter.test_ssrf(url, param)
                    metadata_responses = [t for t in result.get("tests", [])
                        if "metadata" in str(t.get("payload","")).lower() and t.get("status", 0) == 200]
                    if metadata_responses:
                        findings.append({
                            "type": "SSRF (exploit)", "severity": "Critical",
                            "agent": "Exploiter", "url": url, "param": param,
                            "analysis": f"SSRF possible: cloud metadata endpoint accessible via '{param}'"
                        })
                except: pass
            
            # Browser exploits — screenshots + XSS
            progress.update(task, description="[yellow]Browser exploits...")
            try:
                from briar.exploits.browser import BrowserExploiter
                browser = BrowserExploiter(headless=True)
                try:
                    screenshot_path = browser.screenshot(url, f"{output}/screenshots")
                    findings.append({
                        "type": "Screenshot", "severity": "Info",
                        "agent": "Exploiter", "url": url,
                        "analysis": f"Page screenshot saved: {screenshot_path}"
                    })
                    
                    xss_payloads = [
                        "<script>alert(1)</script>",
                        "<img src=x onerror=alert(1)>",
                        "\"><script>alert('XSS')</script>",
                        "javascript:alert(1)",
                    ]
                    for payload in xss_payloads[:3]:
                        xss_result = browser.test_xss(url, payload, f"{output}/screenshots")
                        if xss_result["vulnerable"]:
                            findings.append({
                                "type": "XSS (exploit)", "severity": "High",
                                "agent": "Exploiter", "url": url, "payload": payload,
                                "screenshot": xss_result.get("screenshot"),
                                "analysis": f"XSS confirmed: alert() triggered with payload '{payload}'"
                            })
                            break
                finally:
                    browser.quit()
            except Exception as e:
                findings.append({
                    "type": "Browser Exploit", "severity": "Error",
                    "agent": "Exploiter", "url": url,
                    "analysis": f"Browser exploit failed: {e}"
                })
        
        # Charts
        progress.update(task, description="[green]Generating charts...")
        from briar.charts.generator import ChartGenerator
        cg = ChartGenerator(findings, f"{output}/charts")
        cg.severity_pie()
        cg.agent_bar()
        
        # Reports
        progress.update(task, description="[green]Generating reports...")
        from briar.reports.generator import ReportGenerator
        gen = ReportGenerator(url, findings, output)
        reports = gen.all_formats()
        
        # Obsidian
        from briar.reports.obsidian import ObsidianGenerator
        og = ObsidianGenerator(url, findings, f"{output}/obsidian")
        og.generate()
        
        # Slides
        from briar.slides.pptx_gen import SlideGenerator
        sg = SlideGenerator(url, findings, f"{output}/slides")
        try: sg.pptx()
        except: pass
        sg.html_slides()
        
        progress.advance(task)
    
    table = Table(title="Scan Complete")
    table.add_column("Metric", style="cyan"); table.add_column("Value", style="green")
    table.add_row("Target", url)
    table.add_row("Mode", f"{mode} ({len(agents_to_run)} agents)")
    table.add_row("Findings", str(len(findings)))
    for fmt, path in reports.items():
        table.add_row(f"Report ({fmt})", path)
    table.add_row("Charts", f"{output}/charts/")
    console.print(table)
    console.print("\n[dim]Open reports or launch dashboard: briar serve[/dim]")

@cli.command()
def serve():
    """Start web dashboard"""
    os.system("python -m briar.web")

if __name__ == "__main__":
    cli()
