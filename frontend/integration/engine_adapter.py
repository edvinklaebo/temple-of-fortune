from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Add parent directory to path so we can import gambling_sim
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from gambling_sim.config.game_config import GAME_CONFIG, VOLATILITY_PRESETS
from gambling_sim.core.rng import RNG
from gambling_sim.core.slot_machine import SlotMachine

if TYPE_CHECKING:
    from gambling_sim.core.models import SpinResult


class EngineAdapter:
    """
    Wraps the SlotMachine backend and exposes a frontend-friendly interface.

    Converts SpinResult objects into dicts suitable for rendering.
    Enforces the principle: **Frontend never calculates wins.
    It only renders backend results.**
    """

    def __init__(self, seed: int | None = None, volatility: str = "medium"):
        """
        Initialize the game engine.

        Parameters
        ----------
        seed : int or None
            Random seed for reproducible spins.
        volatility : str
            One of "low", "medium", "high".
        """
        self.volatility = volatility
        self.rng = RNG(seed=seed)

        # Build config with volatility adjustments
        cfg = self._build_config(volatility)
        self.slot_machine = SlotMachine(cfg, self.rng)

    # ──────────────────────────────────────────────────────────────

    def spin(self, bet: float = 1.0) -> dict[str, Any]:
        """
        Spin the slot machine and return a frontend-friendly result dict.

        All win calculations are done by the backend.
        This method only translates SpinResult → frontend format.

        Parameters
        ----------
        bet : float
            Bet amount for this spin.

        Returns
        -------
        dict
            {
                "total_win": float,
                "is_bonus": bool,
                "bonus_spins_played": int,
                "bonus_final_multiplier": int,
                "final_grid": list[list[str]],
                "steps": [
                    {
                        "grid": list[list[str]],
                        "win_amount": float,
                        "multiplier": int,
                        "removed_positions": set[(row, col)],
                    },
                    ...
                ],
            }
        """
        result: SpinResult = self.slot_machine.spin(bet=bet)

        # Convert backend SpinResult to frontend dict
        return {
            "total_win": result.total_win,
            "is_bonus": result.is_bonus,
            "bonus_spins_awarded": self.slot_machine.config.get("bonus", {}).get("free_spins", 10),
            "bonus_spins_played": result.bonus_spins_played,
            "bonus_final_multiplier": result.bonus_final_multiplier,
            "final_grid": result.final_grid,
            "steps": [
                {
                    "grid": step.grid,
                    "win_amount": step.win_amount,
                    "multiplier": step.multiplier,
                    "removed_positions": step.removed_positions,
                }
                for step in result.steps
            ],
        }

    # ──────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────

    def _build_config(self, volatility: str) -> dict:
        """Merge GAME_CONFIG with volatility preset."""
        import copy

        cfg = copy.deepcopy(GAME_CONFIG)
        preset = VOLATILITY_PRESETS.get(volatility, VOLATILITY_PRESETS["medium"])

        if preset["symbol_weights"]:
            cfg["symbol_weights"] = preset["symbol_weights"]

        scale = preset["payout_multiplier"]
        if scale != 1.0:
            cfg["paytable"] = {
                sym: {size: val * scale for size, val in tbl.items()}
                for sym, tbl in cfg["paytable"].items()
            }

        return cfg
