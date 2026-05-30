#!/usr/bin/env python3
"""Briar CLI — Autonomous AI Pentester 🥀"""
import sys, os, click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def load_saved_config():
    """Load provider and API keys from ~/.briar/config. Returns dict or None."""
    config_file = os.path.expanduser("~/.briar/config")
    if not os.path.exists(config_file):
        return None
    config = {}
    with open(config_file) as f:
        for line in f:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                config[k] = v
                if k.endswith('_API_KEY') or k == 'OLLAMA_HOST' or k == 'OLLAMA_PORT' or k == 'OLLAMA_MODEL' or k == 'CUSTOM_ENDPOINT' or k == 'CUSTOM_MODEL':
                    os.environ[k] = v  # Load into env for providers
    return config


BANNER = """
[bold red]
  ██████╗ ██████╗ ██╗ █████╗ ██████╗ 
  ██╔══██╗██╔══██╗██║██╔══██╗██╔══██╗
  ██████╔╝██████╔╝██║███████║██████╔╝
  ██╔══██╗██╔══██╗██║██╔══██║██╔══██╗
  ██████╔╝██║  ██║██║██║  ██║██║  ██║
  ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝[/bold red]
[cyan]              Autonomous AI Pentester[/cyan]
[dim]         11 providers · 12 agents · AGPL-3.0[/dim]
"""

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

@click.group(invoke_without_command=True)
@click.version_option(version="0.3.0")
@click.pass_context
def cli(ctx):
    """Briar — Autonomous AI Pentester"""
    if ctx.invoked_subcommand is None:
        console.print(BANNER)
        console.print("\n[dim]Run [cyan]briar --help[/cyan] for commands[/dim]\n")

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
@click.option("-u", "--url", required=False, help="Target URL")
@click.option("-r", "--repo", help="Source code path")
@click.option("-p", "--provider", default=None, help="AI provider (overrides saved config)")
@click.option("-o", "--output", default="./reports", help="Output dir")
@click.option("-c", "--config", "config_path", help="YAML config file (auth, rules, target)")
@click.option("--quick", is_flag=True, help="Quick scan (4 agents)")
@click.option("--deep", is_flag=True, help="Deep scan (all 12 agents + browser)")
@click.option("--resume", "resume_ws", help="Resume a workspace by name")
def scan(url, repo, provider, output, config_path, quick, deep, resume_ws):
    """Run a pentest scan"""
    # Load saved config (mandatory if no -p flag)
    saved = load_saved_config()

    # Load config file if provided
    if config_path:
        from briar.config import load_config, build_login_flow
        config = load_config(config_path)
        url = url or config.get("target", {}).get("url", "")
        provider = config.get("provider", provider)
        output = config.get("output", output)
        mode = config.get("mode", "standard")
        auth_flow = build_login_flow(config)
        console.print(f"[dim]Config loaded: {len(config.get('rules',{}).get('avoid',[]))} avoid rules, auth={'yes' if auth_flow else 'no'}[/dim]")
    else:
        auth_flow = None

    # Resolve provider: -p flag > YAML config > saved config > ERROR
    if not provider:
        if saved:
            provider = saved.get('PROVIDER', '')
        if not provider:
            console.print(Panel.fit(
                "[bold red]No AI provider configured[/bold red]\n\n"
                "[dim]Run [cyan]briar setup[/cyan] to choose a provider.\n"
                "Or use [cyan]-p PROVIDER[/cyan] flag.[/dim]",
                title="Error"))
            sys.exit(1)

    # Show what we're using
    api_key_env = f"{provider.upper()}_API_KEY"
    has_key = os.environ.get(api_key_env) or (provider == 'ollama')
    key_status = "[green]key set[/green]" if has_key else "[red]no key[/red]"
    console.print(f"[dim]Provider: [cyan]{provider}[/cyan] ({key_status})[/dim]")

    if not has_key and provider != 'ollama':
        console.print(f"[yellow]Warning: {api_key_env} not set. Provider may fail.[/yellow]")

    if not url:
        console.print("[red]URL required (-u or config file)[/red]"); sys.exit(1)

    mode = "deep" if deep else "quick" if quick else "standard"
    agent_count = 12 if deep else 4 if quick else 8

    # Resume existing workspace
    from briar.core.workspace import Workspace
    if resume_ws:
        ws = Workspace.load(resume_ws)
        findings = ws.get_findings()
        all_agents = ["recon","injection","xss","ssrf","auth","authz","csrf","upload","traversal","rce","api","secrets"]
        agents_to_run = ws.get_remaining_agents(all_agents)
        console.print(Panel.fit(
            f"[bold red]Briar Resume[/bold red]\n"
            f"[cyan]{url}[/cyan] | [yellow]{provider}[/yellow] | [dim]{len(findings)} findings so far, {len(agents_to_run)} agents left[/dim]",
            title="Resume"))
    else:
        ws = Workspace(url, mode)
        findings = []
        all_agents = ["recon","injection","xss","ssrf","auth","authz","csrf","upload","traversal","rce","api","secrets"]
        agents_to_run = all_agents[:agent_count]

    console.print(Panel.fit(
        f"[bold red]Briar Scan[/bold red]\n"
        f"[cyan]{url}[/cyan] | [yellow]{provider}[/yellow] | [dim]{mode} ({agent_count} agents)[/dim]"
        + (f"\n[dim]Workspace: {ws.name}[/dim]" if ws else ""),
        title="Scan"))

    if provider == "ollama" and not check_ollama():
        console.print("[red]Start Ollama first[/red]"); sys.exit(1)

    # Authenticate if config provides credentials
    if auth_flow:
        from briar.core.http import HTTPClient
        http = HTTPClient(timeout=10)
        creds = auth_flow.get("credentials", {})
        login_url = url.rstrip("/") + auth_flow.get("login_url", "/login").lstrip("/")
        method = auth_flow.get("method", "form")
        try:
            if method == "json":
                resp = http.post(login_url, json=creds)
            else:
                resp = http.post(login_url, data=creds)
            console.print(f"[green]Auth: {resp.status_code} on {login_url}[/green]")
        except Exception as e:
            console.print(f"[yellow]Auth failed: {e}[/yellow]")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("[cyan]Scanning...", total=len(agents_to_run))
        from briar.agents import run_agent

        provider_errors = 0
        for agent_name in agents_to_run:
            progress.update(task, description=f"[yellow]{agent_name}...")
            try:
                result = run_agent(agent_name, provider, url=url, repo_path=repo)
                if result and "error" not in result:
                    findings.append(result)
                    ws.checkpoint_agent(agent_name, [result])
                    provider_errors = 0  # Reset on success
                elif result and "error" in result:
                    provider_errors += 1
                    if provider_errors >= 3:
                        progress.update(task, description=f"[red]Provider failing — aborting[/red]")
                        console.print(f"[red]Provider '{provider}' returned {provider_errors} errors. Check your API key.[/red]")
                        break
                    ws.checkpoint_agent(agent_name, [])
            except Exception as e:
                provider_errors += 1
                if provider_errors >= 3:
                    progress.update(task, description=f"[red]Provider failing — aborting[/red]")
                    console.print(f"[red]Provider '{provider}' crashed {provider_errors} times. Check configuration.[/red]")
                    break
            progress.advance(task)

        # Exploit validation — replay High/Critical findings
        progress.update(task, description="[yellow]Validating exploits...")
        from briar.core.validator import ExploitValidator
        validator = ExploitValidator()
        findings = validator.validate_all(findings, url)
        progress.update(task, description=f"[dim]{validator.summary()}[/dim]")
        
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
@click.argument("workspace_name", required=False)
def resume(workspace_name):
    """Resume an interrupted scan from a workspace"""
    from briar.core.workspace import Workspace
    if workspace_name:
        # Re-run scan with --resume flag
        import subprocess, sys
        ws_path = os.path.join(os.path.expanduser("~/.briar/workspaces"), workspace_name)
        if not os.path.exists(ws_path):
            workspaces = Workspace.list_workspaces()
            console.print(f"[red]Workspace not found: {workspace_name}[/red]")
            if workspaces:
                console.print("\n[dim]Available workspaces:[/dim]")
                for w in workspaces[:10]:
                    console.print(f"  {w}")
            sys.exit(1)
        console.print(f"[green]Resuming workspace: {workspace_name}[/green]")
        console.print("[dim]Run: briar scan --resume {workspace_name}[/dim]")
    else:
        workspaces = Workspace.list_workspaces()
        if not workspaces:
            console.print("[dim]No workspaces found.[/dim]")
            return
        console.print("[bold]Saved workspaces:[/bold]")
        for w in workspaces[:20]:
            console.print(f"  [cyan]{w}[/cyan]")

@cli.command()
@click.argument("workspace_name", required=False)
def workspaces(workspace_name):
    """List all saved workspaces"""
    from briar.core.workspace import Workspace
    import json
    if workspace_name:
        try:
            ws = Workspace.load(workspace_name)
            console.print(f"[bold]Workspace: {ws.name}[/bold]")
            console.print(f"  Target: {ws._state.get('target','?')}")
            console.print(f"  Mode: {ws._state.get('mode','?')}")
            console.print(f"  Agents done: {len(ws._state.get('agents_completed',[]))}")
            console.print(f"  Findings: {ws._state.get('findings_count',0)}")
            console.print(f"  Resume: briar scan --resume {ws.name}")
        except Exception as e:
            console.print(f"[red]{e}[/red]")
    else:
        workspaces = Workspace.list_workspaces()
        if not workspaces:
            console.print("[dim]No workspaces yet. Run a scan first.[/dim]")
            return
        table = Table(title="Workspaces")
        table.add_column("Name", style="cyan")
        table.add_column("Target")
        table.add_column("Findings", style="green")
        table.add_column("Agents Done")
        for w_name in workspaces[:20]:
            try:
                ws = Workspace.load(w_name)
                table.add_row(
                    w_name[:40], 
                    str(ws._state.get("target", "?"))[:30],
                    str(ws._state.get("findings_count", 0)),
                    str(len(ws._state.get("agents_completed", [])))
                )
            except:
                table.add_row(w_name[:40], "?","?","?")
        console.print(table)

@cli.command()
def status():
    """Show current configuration"""
    saved = load_saved_config()
    if not saved:
        console.print("[yellow]No configuration found.[/yellow]")
        console.print("[dim]Run [cyan]briar setup[/cyan] to configure.[/dim]")
        return

    provider = saved.get('PROVIDER', 'unknown')
    details = '\n'.join(f'  [dim]{k}: {v[:30]}[/dim]' for k,v in saved.items() if k != 'PROVIDER')
    console.print(Panel.fit(
        f"[bold green]Briar Status[/bold green]\n"
        f"  Provider:  [cyan]{provider}[/cyan]\n\n"
        f"{details}\n\n"
        f"[dim]Run [cyan]briar setup[/cyan] to change provider.[/dim]",
        title="Config"
    ))

@cli.command()
def serve():
    """Start web dashboard"""
    os.system("python -m briar.web")

if __name__ == "__main__":
    cli()
