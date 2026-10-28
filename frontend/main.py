#!/usr/bin/env python3
"""
Pygame Slot Simulator — Frontend Entry Point

This is the main executable. It initializes Pygame, the backend engine,
game state, and rendering systems, then runs the game loop.

Usage:
    python main.py [--seed SEED] [--volatility {low,medium,high}]

Example:
    python main.py --seed 42 --volatility high
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pygame


# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pygame_config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    TITLE,
    FPS,
    COLOR_BG,
    STARTING_BALANCE,
    DEFAULT_BET,
)
from game.state import GameState
from game.game_loop import GameLoop
from integration.engine_adapter import EngineAdapter
from rendering.renderer import Renderer
from rendering.audio_renderer import AudioRenderer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="slot_simulator",
        description="Interactive Pygame slot machine simulator.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible spins",
    )
    parser.add_argument(
        "--volatility",
        choices=["low", "medium", "high"],
        default="high",
        help="Volatility preset (default: high)",
    )
    parser.add_argument(
        "--balance",
        type=float,
        default=STARTING_BALANCE,
        help=f"Starting balance (default: {STARTING_BALANCE})",
    )
    parser.add_argument(
        "--bet",
        type=float,
        default=DEFAULT_BET,
        help=f"Initial bet (default: {DEFAULT_BET})",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Launch with debug overlay enabled",
    )
    return parser.parse_args()


def main() -> None:
    """Initialize and run the game."""
    args = parse_args()

    # ─────────────────────────────────────────────────────────────
    # Pygame setup
    # ─────────────────────────────────────────────────────────────
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(TITLE)

    # ─────────────────────────────────────────────────────────────
    # Initialize game components
    # ─────────────────────────────────────────────────────────────
    state = GameState(
        balance=args.balance,
        bet=args.bet,
    )
    state.debug_enabled = args.debug

    engine = EngineAdapter(seed=args.seed, volatility=args.volatility)
    renderer = Renderer(screen)
    audio = AudioRenderer(enabled=True, volume=0.7)

    # ─────────────────────────────────────────────────────────────
    # Run game loop
    # ─────────────────────────────────────────────────────────────
    print(f"[Game] Starting Slot Simulator")
    print(f"[Game] Volatility: {args.volatility}")
    print(f"[Game] Starting balance: ${state.balance:.2f}")
    print(f"[Game] Initial bet: ${state.bet:.2f}")
    print(f"[Game] Seed: {args.seed if args.seed else 'random'}")
    print()

    game_loop = GameLoop(state, engine, renderer, audio)
    try:
        game_loop.run()
    except KeyboardInterrupt:
        print("\n[Game] Interrupted by user")
    finally:
        pygame.quit()
        print("[Game] Goodbye!")


if __name__ == "__main__":
    main()
