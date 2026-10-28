from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from gambling_sim.core.models import SpinResult
    from gambling_sim.core.slot_machine import SlotMachine
    from gambling_sim.simulation.statistics import SimulationStats

console = Console()

# Symbol → rich style mapping
SYMBOL_STYLES: dict[str, str] = {
    "A":       "bold yellow",
    "B":       "bold cyan",
    "C":       "bold green",
    "D":       "bold magenta",
    "E":       "bold red",
    "SCATTER": "bold white on blue",
    "EMPTY":   "dim white",
}

# ─────────────────────────────────────────────
# Grid rendering
# ─────────────────────────────────────────────


def render_grid(
    grid: list[list[str]],
    highlight: set[tuple[int, int]] | None = None,
    title: str = "Grid",
) -> None:
    """Print the grid as a rich Table. Winning positions are highlighted (reversed)."""
    cols = len(grid[0]) if grid else 0

    table = Table(
        title=title,
        box=box.SQUARE,
        show_header=False,
        padding=(0, 1),
        title_style="bold white",
    )
    for _ in range(cols):
        table.add_column(justify="center", min_width=9)

    for r, row in enumerate(grid):
        cells: list[Text] = []
        for c, sym in enumerate(row):
            style = SYMBOL_STYLES.get(sym, "white")
            if highlight and (r, c) in highlight:
                t = Text(f"[{sym}]", style=style + " reverse")
            else:
                t = Text(f"  {sym}  ", style=style)
            cells.append(t)
        table.add_row(*cells)

    console.print(table)


# ─────────────────────────────────────────────
# Single-spin interactive mode
# ─────────────────────────────────────────────


def play_once(slot: "SlotMachine", bet: float = 1.0) -> "SpinResult":
    """Spin once, print every cascade step, then print the summary."""
    console.rule("[bold]New Spin")
    result = slot.spin(bet=bet)

    if not result.steps:
        console.print(Panel("[dim]No winning clusters — no win this spin.[/dim]", style="red"))
    else:
        for i, step in enumerate(result.steps, start=1):
            title = (
                f"Cascade Step {i}"
                f"  ×{step.multiplier} cascade multiplier"
                f"  ➜  Win: {step.win_amount:.2f}"
            )
            render_grid(step.grid, highlight=step.removed_positions, title=title)
            console.print()

    _print_spin_summary(result)
    return result


def _print_spin_summary(result: "SpinResult") -> None:
    color = "green" if result.total_win > 0 else "red"

    t = Table(box=box.MINIMAL, show_header=False, padding=(0, 1))
    t.add_column("Key", style="bold white")
    t.add_column("Value", style=color)

    t.add_row("Bet",             f"{result.bet:.2f}")
    t.add_row("Total Win",       f"{result.total_win:.2f}")
    t.add_row("Win Multiplier",  f"{result.win_multiplier:.2f}×")
    t.add_row("Cascade Steps",   str(len(result.steps)))
    t.add_row("Bonus Triggered", "Yes ✓" if result.is_bonus else "No")
    if result.is_bonus:
        t.add_row("Bonus Spins Played", str(result.bonus_spins_played))

    console.print(Panel(t, title="[bold]Spin Result", border_style=color))


# ─────────────────────────────────────────────
# Simulation mode (with progress bar)
# ─────────────────────────────────────────────


def run_simulation_with_progress(
    slot: "SlotMachine",
    spins: int,
    bet: float = 1.0,
) -> dict:
    """Run the Monte Carlo loop with a live Rich progress bar."""
    from gambling_sim.simulation.statistics import SimulationStats  # avoid top-level circular import

    stats = SimulationStats()
    total_bet = 0.0
    total_return = 0.0
    rtp_series: list[float] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(f"Simulating {spins:,} spins…", total=spins)

        for _ in range(spins):
            result = slot.spin(bet=bet)
            total_bet += bet
            total_return += result.total_win
            stats.record_spin(result)
            rtp_series.append(total_return / total_bet)
            progress.advance(task)

    rtp = total_return / total_bet if total_bet > 0 else 0.0
    sim_result = {
        "spins": spins,
        "total_bet": total_bet,
        "total_return": round(total_return, 2),
        "rtp": rtp,
        "profit": round(total_return - total_bet, 2),
        "rtp_series": rtp_series,
        "stats": stats,
    }

    print_simulation_results(sim_result)
    return sim_result


def print_simulation_results(result: dict) -> None:
    """Render the simulation outcome as rich tables."""
    stats: "SimulationStats" = result["stats"]
    summary = stats.summary()

    profit_color = "green" if result["profit"] >= 0 else "red"
    profit_str = f"{result['profit']:+.2f}"

    # ── Main statistics ──────────────────────────────────────────────
    main_table = Table(
        title="Simulation Results",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold white",
    )
    main_table.add_column("Metric", style="bold")
    main_table.add_column("Value", justify="right")

    main_table.add_row("Spins",                f"{result['spins']:,}")
    main_table.add_row("Total Bet",            f"{result['total_bet']:,.2f}")
    main_table.add_row("Total Return",         f"{result['total_return']:,.2f}")
    main_table.add_row("RTP",                  f"[bold]{result['rtp']:.2%}[/bold]")
    main_table.add_row(
        "Profit / Loss",
        f"[{profit_color}]{profit_str}[/{profit_color}]",
    )
    main_table.add_row("Win Frequency",        summary["win_frequency"])
    main_table.add_row(
        "Bonus Triggers",
        f"{summary['bonus_triggers']:,}  ({summary['bonus_trigger_rate']})",
    )
    main_table.add_row("Max Win Multiplier",   summary["max_win_multiplier"])
    main_table.add_row("Max Loss Streak",      str(summary["max_consecutive_losses"]))
    main_table.add_row("Avg Cascade Depth",    summary["avg_cascade_depth"])
    main_table.add_row("Max Cascade Depth",    str(summary["max_cascade_depth"]))

    console.print(main_table)

    # ── Win distribution ─────────────────────────────────────────────
    dist_table = Table(
        title="Win Distribution",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold white",
    )
    dist_table.add_column("Win Range (× bet)", style="bold")
    dist_table.add_column("Count", justify="right")
    dist_table.add_column("% of Spins", justify="right")

    total_spins = result["spins"]
    for bucket, count in sorted(
        summary["win_distribution"].items(),
        key=lambda kv: _bucket_sort_key(kv[0]),
    ):
        pct = count / total_spins * 100
        dist_table.add_row(bucket, f"{count:,}", f"{pct:.2f}%")

    console.print(dist_table)

    # ── Transparency note ────────────────────────────────────────────
    console.print(
        Panel(
            "[bold yellow]Transparency:[/bold yellow] All figures above are "
            "actual simulated outcomes.\n"
            "RTP < 100% means the house has an edge. "
            "Profit/Loss shows your net position at these bet levels.",
            style="dim",
        )
    )


# ─────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────


def _bucket_sort_key(label: str) -> float:
    """Sort win-bucket labels by their lower numeric bound."""
    if label == "0x":
        return -1.0
    try:
        return float(label.split("x")[0].split("-")[0].replace("+", ""))
    except (ValueError, IndexError):
        return 999.0
