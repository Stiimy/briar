"""Briar Animation — Sylph running & slaying vulnerabilities 💀"""
import time, sys, random
from threading import Thread

SYLPH_FRAMES = [
    r"  ᕕ(ò_ó)ᕗ",
    r"  ᕕ(ò_Ó)ᕗ",
    r"  ᕕ(◉_◉)ᕗ",
    r"  ᕕ(Ò_Ó)ᕗ",
]
SYLPH_ATTACK = r"  (╯ò_ó)╯彡💥"
SYLPH_IDLE = r"  (◕‿◕) ✧"

ENEMIES = ["🐛", "💉SQL", "❌XSS", "🌐SRF", "🔓AUTH", "📁TRV", "💣RCE", "🔑JWT"]

class SylphAnimation:
    """Animated Sylph running during scans."""

    def __init__(self, total_agents: int = 16):
        self.total = total_agents
        self.done = 0
        self.current_agent = ""
        self.messages = []
        self.running = False
        self._thread = None
        self._frame = 0

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def update(self, done: int, agent_name: str = "", message: str = ""):
        self.done = done
        self.current_agent = agent_name
        if message:
            self.messages.append(message)
            if len(self.messages) > 5:
                self.messages.pop(0)

    def render(self) -> str:
        pct = min(100, int(self.done / max(1, self.total) * 100))
        bar_width = 30
        filled = int(bar_width * self.done / max(1, self.total))
        bar = "█" * filled + "░" * (bar_width - filled)

        # Sylph state
        if self.done >= self.total:
            sylph = SYLPH_IDLE
        elif self.current_agent:
            self._frame = (self._frame + 1) % len(SYLPH_FRAMES)
            sylph = SYLPH_FRAMES[self._frame]
        else:
            sylph = SYLPH_IDLE

        # Choose random enemy for current agent
        enemy_idx = min(len(ENEMIES) - 1, self.done)
        enemy = ENEMIES[enemy_idx] if self.done < len(ENEMIES) else "💀"

        lines = []
        lines.append(f"  {sylph}   [bold red]▸ {self.current_agent or 'Starting...'}[/bold red]")
        lines.append(f"  [{bar}] {pct}%  ({self.done}/{self.total})")
        lines.append(f"  [dim]target: {enemy}[/dim]")

        # Last messages
        for msg in self.messages[-2:]:
            lines.append(f"  [yellow]  {msg}[/yellow]")

        return "\n".join(lines)
