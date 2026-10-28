from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gambling_sim.core.models import SpinResult


class SimulationStats:
    """
    Accumulates statistics across many spins.

    Tracks win frequency, win distribution (bucketed by win multiplier),
    bonus trigger rate, cascade depth, and loss streaks.
    All statistics reflect *transparent* outcomes — no rounding or hiding.
    """

    # Win-multiplier buckets: (label, lower_inclusive, upper_exclusive)
    # "0x" is handled separately (exact zero win).
    BUCKETS: tuple[tuple[str, float, float], ...] = (
        ("0x-0.5x",   0.0,   0.5),
        ("0.5x-1x",   0.5,   1.0),
        ("1x-2x",     1.0,   2.0),
        ("2x-5x",     2.0,   5.0),
        ("5x-10x",    5.0,  10.0),
        ("10x-25x",  10.0,  25.0),
        ("25x-50x",  25.0,  50.0),
        ("50x-100x", 50.0, 100.0),
        ("100x+",   100.0,  float("inf")),
    )

    def __init__(self) -> None:
        self.total_spins: int = 0
        self.winning_spins: int = 0
        self.bonus_triggers: int = 0
        self.max_win: float = 0.0
        self.max_win_multiplier: float = 0.0
        self.total_cascade_steps: int = 0
        self.max_cascade_depth: int = 0
        self.max_consecutive_losses: int = 0
        self.win_buckets: dict[str, int] = {}

        self._current_loss_streak: int = 0

    # ------------------------------------------------------------------

    def record_spin(self, result: "SpinResult") -> None:
        self.total_spins += 1
        win_mult = result.win_multiplier

        # Win / loss tracking
        if result.total_win > 0:
            self.winning_spins += 1
            self._current_loss_streak = 0
        else:
            self._current_loss_streak += 1
            if self._current_loss_streak > self.max_consecutive_losses:
                self.max_consecutive_losses = self._current_loss_streak

        # Bonus
        if result.is_bonus:
            self.bonus_triggers += 1

        # Max win
        if result.total_win > self.max_win:
            self.max_win = result.total_win
        if win_mult > self.max_win_multiplier:
            self.max_win_multiplier = win_mult

        # Cascade depth
        depth = len(result.steps)
        self.total_cascade_steps += depth
        if depth > self.max_cascade_depth:
            self.max_cascade_depth = depth

        # Bucketing
        bucket = self._classify(win_mult)
        self.win_buckets[bucket] = self.win_buckets.get(bucket, 0) + 1

    # ------------------------------------------------------------------
    # Classification helpers
    # ------------------------------------------------------------------

    def _classify(self, win_mult: float) -> str:
        if win_mult == 0.0:
            return "0x"
        for label, lo, hi in self.BUCKETS:
            if lo <= win_mult < hi:
                return label
        return "100x+"

    # ------------------------------------------------------------------
    # Derived statistics
    # ------------------------------------------------------------------

    @property
    def win_frequency(self) -> float:
        return self.winning_spins / self.total_spins if self.total_spins > 0 else 0.0

    @property
    def average_cascade_depth(self) -> float:
        return (
            self.total_cascade_steps / self.winning_spins
            if self.winning_spins > 0
            else 0.0
        )

    def summary(self) -> dict:
        bonus = max(self.bonus_triggers, 1)
        return {
            "total_spins": self.total_spins,
            "win_frequency": f"{self.win_frequency:.2%}",
            "bonus_triggers": self.bonus_triggers,
            "bonus_trigger_rate": f"1 in {self.total_spins // bonus}",
            "max_win_multiplier": f"{self.max_win_multiplier:.1f}x",
            "max_consecutive_losses": self.max_consecutive_losses,
            "avg_cascade_depth": f"{self.average_cascade_depth:.2f}",
            "max_cascade_depth": self.max_cascade_depth,
            "win_distribution": self.win_buckets,
        }
