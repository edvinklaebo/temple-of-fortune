#!/usr/bin/env python3
"""
Gambling Simulator — entry point.

Usage examples
--------------
Interactive single-spin mode (deterministic with --seed):
    python main.py --mode spin --seed 42 --bet 1.0

Monte Carlo simulation (100 k spins, medium volatility):
    python main.py --mode simulate --spins 100000 --volatility medium

High-volatility simulation without charts:
    python main.py --mode simulate --spins 50000 --volatility high --no-visual

Compare volatility presets:
    python main.py --mode simulate --spins 50000 --volatility low
    python main.py --mode simulate --spins 50000 --volatility high
"""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def build_config(volatility: str) -> dict:
    """Return a GAME_CONFIG dict merged with the requested volatility preset."""
    from gambling_sim.config.game_config import GAME_CONFIG, VOLATILITY_PRESETS

    cfg = copy.deepcopy(GAME_CONFIG)
    preset = VOLATILITY_PRESETS.get(volatility, VOLATILITY_PRESETS["medium"])

    if preset["symbol_weights"] is not None:
        cfg["symbol_weights"] = preset["symbol_weights"]

    scale = preset["payout_multiplier"]
    if scale != 1.0:
        cfg["paytable"] = {
            sym: {size: val * scale for size, val in tbl.items()}
            for sym, tbl in cfg["paytable"].items()
        }

    return cfg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="gambling_sim",
        description=(
            "RNG slot simulator — demonstrates RTP, volatility, and "
            "cascading mechanics.\n"
            "All profit/loss figures are shown transparently."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["spin", "simulate"],
        default="simulate",
        help="spin = interactive step-by-step mode; simulate = Monte Carlo batch (default: simulate)",
    )
    parser.add_argument(
        "--spins",
        type=int,
        default=100_000,
        metavar="N",
        help="Number of spins to simulate (simulate mode only, default: 100000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        metavar="S",
        help="Integer seed for reproducible RNG (e.g. --seed 42)",
    )
    parser.add_argument(
        "--bet",
        type=float,
        default=1.0,
        metavar="AMOUNT",
        help="Bet amount per spin — all wins scale linearly (default: 1.0)",
    )
    parser.add_argument(
        "--volatility",
        choices=["low", "medium", "high"],
        default="medium",
        help="Volatility preset: adjusts symbol weights and payout scale (default: medium)",
    )
    parser.add_argument(
        "--no-visual",
        action="store_true",
        help="Suppress matplotlib charts (useful in headless environments)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = build_config(args.volatility)

    from gambling_sim.core.rng import RNG
    from gambling_sim.core.slot_machine import SlotMachine

    rng = RNG(seed=args.seed)
    slot = SlotMachine(cfg, rng)

    # ── Interactive spin mode ────────────────────────────────────────
    if args.mode == "spin":
        from gambling_sim.ui.cli import console, play_once

        console.print(
            f"[bold]Slot Simulator[/bold]"
            f" | volatility=[cyan]{args.volatility}[/cyan]"
            f" | bet=[yellow]{args.bet}[/yellow]"
            f" | seed=[dim]{args.seed}[/dim]"
        )
        console.print("[dim]Press Enter to spin · type  q  then Enter to quit[/dim]\n")

        while True:
            play_once(slot, bet=args.bet)
            try:
                ans = console.input("\n[dim]➜ [/dim]")
            except (EOFError, KeyboardInterrupt):
                break
            if ans.strip().lower() == "q":
                break

    # ── Simulation mode ──────────────────────────────────────────────
    elif args.mode == "simulate":
        from gambling_sim.ui.cli import console, run_simulation_with_progress

        console.print(
            f"[bold]Slot Simulator[/bold]"
            f" | mode=simulate"
            f" | spins=[yellow]{args.spins:,}[/yellow]"
            f" | bet=[yellow]{args.bet}[/yellow]"
            f" | volatility=[cyan]{args.volatility}[/cyan]"
            f" | seed=[dim]{args.seed}[/dim]"
        )

        result = run_simulation_with_progress(slot, spins=args.spins, bet=args.bet)

        if not args.no_visual:
            from gambling_sim.visualization.charts import plot_rtp_convergence, plot_win_histogram

            plot_win_histogram(result["stats"])
            plot_rtp_convergence(result["rtp_series"], target_rtp=0.96)


if __name__ == "__main__":
    main()
