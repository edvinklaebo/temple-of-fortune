from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CascadeStep:
    """Snapshot of one cascade iteration: the grid *before* removal, the win, and which
    positions were removed to trigger the next fall."""

    grid: list[list[str]]
    win_amount: float
    multiplier: int
    removed_positions: set[tuple[int, int]]


@dataclass
class BonusState:
    """Mutable state carried through a bonus (free-spin) round."""

    free_spins_remaining: int = 0
    persistent_multiplier: int = 1
    active: bool = False


@dataclass
class SpinResult:
    """Complete result of a single spin, including any bonus round played within it."""

    total_win: float
    steps: list[CascadeStep]
    final_grid: list[list[str]] = field(default_factory=list)
    is_bonus: bool = False
    bonus_spins_played: int = 0
    bonus_final_multiplier: int = 1
    bet: float = 1.0

    @property
    def win_multiplier(self) -> float:
        """Total win expressed as a multiple of the bet (e.g. 3.5 = 3.5× bet)."""
        return self.total_win / self.bet if self.bet > 0 else 0.0
