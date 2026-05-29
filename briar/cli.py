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
    for i, (n, d) in enumerate({"1":"Ollama (free, local)","2":"OpenAI","3":"Anthropic","4":"DeepSeek","5":"Groq","6":"Mistral"}.items()):
        console.print(f"  {i}. {d}")
    choice = click.prompt("Choice", type=int, default=1)
    providers = {1:"ollama",2:"openai",3:"anthropic",4:"deepseek",5:"groq",6:"mistral"}
    provider = providers.get(choice, "ollama")
    os.makedirs(os.path.expanduser("~/.briar"), exist_ok=True)
    config = f"PROVIDER={provider}\n"
    if provider == "ollama":
        config += "OLLAMA_HOST=localhost\nOLLAMA_PORT=11434\nOLLAMA_MODEL=minimax-m2.5:latest\n"
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
