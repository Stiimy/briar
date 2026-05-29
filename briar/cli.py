#!/usr/bin/env python3
"""Briar CLI — Autonomous AI Pentester 🥀"""
import sys, os, click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def check_ollama():
    from briar.providers.ollama import OllamaProvider
    ollama = OllamaProvider()
    if ollama.health_check():
        models = ollama.list_models()
        console.print(f"[green]✅ Ollama — {len(models)} modèles prêts[/green]")
        return ollama
    else:
        console.print("[yellow]⚠️  Ollama not running[/yellow]")
        return None

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Briar — Autonomous AI Pentester"""
    pass

@cli.command()
def setup():
    """Configure Briar"""
    console.print(Panel.fit("[bold green]🥀 Briar Setup[/bold green]\n\nPick your AI provider:", title="Setup"))
    console.print("  1. Ollama (free, local)\n  2. OpenAI\n  3. Anthropic\n  4. DeepSeek\n  5. Groq\n  6. Mistral 🇫🇷")
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
    console.print(f"\n[green]✅ Provider: {provider}[/green]")

@cli.command()
@click.option("-u", "--url", required=True, help="Target URL")
@click.option("-r", "--repo", help="Source code path")
@click.option("-p", "--provider", default="ollama", help="AI provider")
@click.option("-o", "--output", default="./reports", help="Output dir")
@click.option("--quick", is_flag=True, help="Quick scan")
def scan(url, repo, provider, output, quick):
    """Run a pentest scan 🥀"""
    console.print(Panel.fit(f"[bold red]🥀 Briar Scan[/bold red]\n\n🎯 [cyan]{url}[/cyan]\n🤖 [yellow]{provider}[/yellow]", title="Scan"))
    
    if provider == "ollama" and not check_ollama():
        console.print("[red]❌ Start Ollama first[/red]"); sys.exit(1)
    
    findings = []
    agents_to_run = ["injection", "xss", "ssrf", "auth"][:2 if quick else 4]
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("[cyan]🔍 Scanning...", total=len(agents_to_run))
        
        from briar.agents import run_agent
        for agent_name in agents_to_run:
            progress.update(task, description=f"[yellow]🧪 {agent_name}...")
            try:
                result = run_agent(agent_name, provider, url=url)
                if result and "error" not in result:
                    findings.append(result)
            except Exception as e:
                findings.append({"type": agent_name, "severity": "Error", "url": url, "analysis": str(e), "agent": agent_name})
            progress.advance(task)
    
    # Generate reports
    progress2 = progress.add_task("[green]📄 Reports...", total=1)
    from briar.reports.generator import ReportGenerator
    gen = ReportGenerator(url, findings, output)
    reports = gen.all_formats()
    progress.advance(progress2)
    
    # Summary
    table = Table(title="🥀 Scan Complete")
    table.add_column("Metric", style="cyan"); table.add_column("Value", style="green")
    table.add_row("Target", url)
    table.add_row("Findings", str(len(findings)))
    table.add_row("Report (MD)", reports.get("markdown","N/A"))
    table.add_row("Report (Word)", reports.get("word","N/A"))
    table.add_row("Report (Excel)", reports.get("excel","N/A"))
    console.print(table)

@cli.command()
def serve():
    """Start web dashboard"""
    console.print("[green]🥀 Dashboard → http://localhost:8233[/green]")
    os.system("python -m briar.web")

if __name__ == "__main__":
    cli()
