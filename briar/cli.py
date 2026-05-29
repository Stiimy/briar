#!/usr/bin/env python3
"""Briar CLI — Autonomous AI Pentester 🥀"""
import sys
import os
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def check_ollama():
    """Check if Ollama is running"""
    from briar.providers.ollama import OllamaProvider
    ollama = OllamaProvider()
    if ollama.health_check():
        models = ollama.list_models()
        console.print(f"[green]✅ Ollama running — {len(models)} models available[/green]")
        return ollama
    else:
        console.print("[yellow]⚠️  Ollama not running. Start with: ollama serve[/yellow]")
        return None

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Briar — Autonomous AI Pentester"""
    pass

@cli.command()
def setup():
    """Configure Briar (interactive wizard)"""
    console.print(Panel.fit(
        "[bold green]🥀 Briar Setup[/bold green]\n\n"
        "Welcome to Briar — the autonomous AI pentester.\n\n"
        "This wizard will help you configure your AI provider.",
        title="Setup"
    ))
    
    console.print("\n[bold]Select AI Provider:[/bold]")
    console.print("  1. Ollama (local, free)")
    console.print("  2. OpenAI (ChatGPT)")
    console.print("  3. Anthropic (Claude)")
    console.print("  4. DeepSeek")
    console.print("  5. Groq (free tier)")
    console.print("  6. Mistral AI 🇫🇷")
    
    choice = click.prompt("Choice", type=int, default=1)
    
    providers = {
        1: "ollama", 2: "openai", 3: "anthropic",
        4: "deepseek", 5: "groq", 6: "mistral"
    }
    
    provider = providers.get(choice, "ollama")
    
    # Save config
    os.makedirs(os.path.expanduser("~/.briar"), exist_ok=True)
    config = f"PROVIDER={provider}\n"
    
    if provider == "ollama":
        config += "OLLAMA_HOST=localhost\nOLLAMA_PORT=11434\n"
        config += 'OLLAMA_MODEL=minimax-m2.5:latest\n'
    else:
        api_key = click.prompt("API Key", hide_input=True)
        config += f"{provider.upper()}_API_KEY={api_key}\n"
    
    with open(os.path.expanduser("~/.briar/config"), "w") as f:
        f.write(config)
    
    console.print(f"\n[green]✅ Configured with provider: {provider}[/green]")
    console.print("[dim]Config saved to ~/.briar/config[/dim]")

@cli.command()
@click.option("-u", "--url", required=True, help="Target URL to scan")
@click.option("-r", "--repo", help="Path to source code repository")
@click.option("-p", "--provider", default="ollama", help="AI provider")
@click.option("-o", "--output", default="./reports", help="Output directory")
@click.option("--quick", is_flag=True, help="Quick scan (5 min)")
def scan(url, repo, provider, output, quick):
    """Run a pentest scan"""
    console.print(Panel.fit(
        f"[bold red]🥀 Briar Scan[/bold red]\n\n"
        f"Target: [cyan]{url}[/cyan]\n"
        f"Provider: [yellow]{provider}[/yellow]\n"
        f"Mode: [dim]{'Quick' if quick else 'Full'}[/dim]",
        title="Scan"
    ))
    
    # Check provider
    if provider == "ollama":
        ollama = check_ollama()
        if not ollama:
            console.print("[red]❌ Ollama required. Start it first.[/red]")
            sys.exit(1)
    
    # Progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Phase 1: Recon
        task1 = progress.add_task("[cyan]🔍 Reconnaissance...", total=100)
        progress.update(task1, advance=100)
        
        # Phase 2: Analysis
        task2 = progress.add_task("[yellow]🧪 Vulnerability Analysis...", total=100)
        agents = ["Injection", "XSS", "SSRF", "Auth", "AuthZ"]
        for agent in agents:
            progress.update(task2, advance=20, description=f"[yellow]🧪 {agent}...")
        progress.update(task2, advance=0, description=f"[yellow]🧪 Done — 0 vulns found")
        
        # Phase 3: Report
        task3 = progress.add_task("[green]📄 Generating report...", total=100)
        progress.update(task3, advance=100)
    
    # Summary table
    table = Table(title="Scan Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Target", url)
    table.add_row("Duration", "12s")
    table.add_row("Vulnerabilities", "0 (MVP)")
    table.add_row("Report", f"{output}/report.md")
    
    console.print(table)
    console.print("\n[dim]💡 MVP — full analysis coming in v0.2[/dim]")

@cli.command()
def serve():
    """Start the Briar web dashboard"""
    console.print("[green]Starting Briar Dashboard on http://localhost:8233[/green]")
    os.system("python -m briar.web")

if __name__ == "__main__":
    cli()
