"""
CLI dashboard — Rich-based live view for resilience experiments.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich.text import Text


class BattleDashboard:
    """Rich-based dashboard for resilience-run visualization and export."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def _build_layout(self, battle_state: Dict[str, Any]) -> Layout:
        """Build layout from current battle state for Live updates."""
        layout = Layout()

        header = Panel(
            f"[bold cyan]RESILIENCE EXPERIMENT DASHBOARD[/bold cyan]\n"
            f"Image: {battle_state.get('image_path', 'Unknown')}\n"
            f"Round: {battle_state.get('round', 0)}/{battle_state.get('max_rounds', 50)}",
            title="[bold]RUN STATUS[/bold]",
            border_style="cyan",
        )

        confidence = battle_state.get("confidence", 0)
        confidence_color = (
            "green" if confidence > 0.8 else "yellow" if confidence > 0.5 else "red"
        )

        metrics_text = f"""
[bold]Confidence:[/bold] [{confidence_color}]{confidence:.1%}[/{confidence_color}]
[bold]Signals flagged:[/bold] {len(battle_state.get('waste_detected', {}))} types
[bold]Adaptive recovery:[/bold] {'Yes' if battle_state.get('self_healing_detected') else 'No'}
[bold]Active modifiers:[/bold] {len(battle_state.get('active_cleaning', []))} methods
"""
        metrics_panel = Panel(
            metrics_text,
            title="[bold]METRICS[/bold]",
            border_style="blue",
        )

        waste = battle_state.get("waste_detected", {})
        if waste:
            waste_table = Table(title="Flagged signals")
            waste_table.add_column("Type", style="cyan")
            waste_table.add_column("Confidence", style="yellow")
            waste_table.add_column("Status", style="green")
            active = battle_state.get("active_cleaning", [])
            for waste_type, conf in waste.items():
                status = "Targeted" if active else "Detected"
                waste_table.add_row(
                    waste_type.replace("_", " ").title(),
                    f"{conf:.1%}",
                    status,
                )
            waste_panel = Panel(
                waste_table,
                title="[bold red]SIGNAL DETAILS[/bold red]",
                border_style="red",
            )
        else:
            waste_panel = Panel(
                "[green]No flagged signals[/green]",
                title="[bold green]CLEAR STATUS[/bold green]",
                border_style="green",
            )

        log_lines = battle_state.get("battle_log", [])[-10:]
        log_text = "\n".join(log_lines) if log_lines else "Run log will appear here..."
        log_panel = Panel(
            log_text,
            title="[bold yellow]RUN LOG[/bold yellow]",
            border_style="yellow",
            height=8,
        )

        active_cleaning = battle_state.get("active_cleaning", [])
        if active_cleaning:
            cleaning_table = Table(title="Active modifiers")
            cleaning_table.add_column("Method", style="magenta")
            cleaning_table.add_column("Progress", style="cyan")
            cleaning_table.add_column("Center", style="blue")
            for c in active_cleaning:
                progress = c.get("progress", 0.0)
                center = c.get("center", ("N/A", "N/A"))
                cleaning_table.add_row(
                    c.get("method", "?"),
                    f"{progress:.0%}",
                    f"({center[0]}, {center[1]})",
                )
            cleaning_panel = Panel(
                cleaning_table,
                title="[bold cyan]ACTIVE MODIFIERS[/bold cyan]",
                border_style="cyan",
            )
        else:
            cleaning_panel = Panel(
                "[dim]No active modifier operations.[/dim]",
                title="[bold cyan]MODIFIER STATUS[/bold cyan]",
                border_style="cyan",
            )

        layout.split_column(
            Layout(header, size=4),
            Layout(metrics_panel, size=6),
            Layout(waste_panel, size=10),
            Layout(log_panel, size=8),
            Layout(cleaning_panel, size=8),
        )
        return layout

    def display_battle_status(self, battle_state: Dict[str, Any]) -> None:
        """Display current battle status (single render)."""
        layout = self._build_layout(battle_state)
        self.console.print(layout)

    def live_display(
        self,
        get_state: Callable[[], Dict[str, Any]],
        refresh_per_second: float = 2,
        transient: bool = False,
    ) -> Live:
        """
        Return a Live context for real-time updates.
        Caller should update state and live.refresh() in a loop.

        Example:
            with dashboard.live_display(lambda: battle_state) as live:
                for _ in range(10):
                    # update battle_state
                    live.update(dashboard._build_layout(battle_state))
                    time.sleep(0.5)
        """
        return Live(
            self._build_layout(get_state()),
            refresh_per_second=refresh_per_second,
            screen=True,
            transient=transient,
        )

    def display_battle_summary(self, battle_state: Dict[str, Any]) -> None:
        """Display final battle summary."""
        self.console.clear()

        if battle_state.get("confidence", 0) >= 0.95:
            status = "[bold green]THRESHOLD MET[/bold green]"
            status_color = "green"
        elif battle_state.get("round", 0) >= battle_state.get("max_rounds", 50):
            status = "[bold yellow]MAX ROUNDS REACHED[/bold yellow]"
            status_color = "yellow"
        else:
            status = "[bold red]RUN IN PROGRESS[/bold red]"
            status_color = "red"

        summary_panel = Panel(
            f"""
{status}

[bold]Final statistics:[/bold]
• Total rounds: {battle_state.get('round', 0)}
• Final confidence: {battle_state.get('confidence', 0):.1%}
• Signal types flagged: {len(battle_state.get('waste_detected', {}))}
• Adaptive recovery observed: {'Yes' if battle_state.get('self_healing_detected') else 'No'}

[bold]Outcome:[/bold] {'Detector confidence below threshold' if battle_state.get('confidence', 0) >= 0.95 else 'Residual signals may remain (review logs)'}
            """,
            title="[bold]RUN SUMMARY[/bold]",
            border_style=status_color,
        )

        self.console.print(summary_panel)

        if battle_state.get("battle_log"):
            self.console.print("\n[bold]Recent run log:[/bold]")
            for entry in battle_state["battle_log"][-5:]:
                self.console.print(f"  {entry}")

    def export_report(
        self,
        battle_state: Dict[str, Any],
        output_path: str,
        format: str = "json",
    ) -> str:
        """
        Export resilience run report to file.

        Args:
            battle_state: Current run state payload.
            output_path: Output file path.
            format: 'json' or 'txt'.

        Returns:
            Path to exported file.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Sanitize for JSON (remove non-serializable)
        export_state = {k: v for k, v in battle_state.items() if not k.startswith("_")}
        for key in list(export_state.keys()):
            if isinstance(export_state[key], (set, bytes)):
                export_state[key] = str(export_state[key])

        if format.lower() == "json":
            with open(path, "w") as f:
                json.dump(export_state, f, indent=2)
        else:
            lines = [
                "STEGANOGRAPHY RESILIENCE REPORT",
                "=" * 40,
                f"Image: {battle_state.get('image_path', 'Unknown')}",
                f"Rounds: {battle_state.get('round', 0)}/{battle_state.get('max_rounds', 50)}",
                f"Final Confidence: {battle_state.get('confidence', 0):.1%}",
                f"Adaptive recovery: {'Yes' if battle_state.get('self_healing_detected') else 'No'}",
                "",
                "Run log:",
            ]
            for entry in battle_state.get("battle_log", []):
                lines.append(f"  {entry}")
            path.write_text("\n".join(lines), encoding="utf-8")

        return str(path)

    def create_progress_display(self, battle_state: Dict[str, Any]) -> Progress:
        """Create a progress display for the run."""
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )

        progress.add_task(
            "Run progress",
            total=100,
            completed=int(battle_state.get("confidence", 0) * 100),
        )

        for waste_type, confidence in battle_state.get("waste_detected", {}).items():
            progress.add_task(
                f"Removing {waste_type}",
                total=100,
                completed=int((1 - confidence) * 100),
            )

        return progress
