from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from gambling_sim.core.models import BonusState, CascadeStep, SpinResult
from gambling_sim.core.payout import calculate_cluster_win, find_clusters

if TYPE_CHECKING:
    from gambling_sim.core.rng import RNG


class SlotMachine:
    """
    6×5 cluster-pays slot engine with cascading wins and a free-spin bonus.

    Grid coordinates: row 0 = top of display, row (rows-1) = bottom.
    Gravity direction: symbols fall *down* (toward higher row indices).
    New symbols refill from the top after each cascade.
    """

    def __init__(self, config: dict, rng: "RNG") -> None:
        self.config = config
        self.rng = rng

        self._symbols: list[str] = config["symbols"] + config.get("special_symbols", [])
        self._weights: list[float] = [
            config["symbol_weights"][s] for s in self._symbols
        ]
        self._paytable: dict[str, dict[int, float]] = config["paytable"]
        self._min_cluster: int = config.get("min_cluster", 5)
        self._scatter_count: int = config.get("scatter_trigger_count", 3)
        self._base_max_mult: int = config.get("max_cascade_multiplier", 5)

        bonus_cfg = config.get("bonus", {})
        self._bonus_free_spins: int = bonus_cfg.get("free_spins", 10)
        self._bonus_max_mult: int = bonus_cfg.get("max_multiplier", 10)
        self._bonus_max_total: int = bonus_cfg.get("max_total_spins", 50)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def spin(self, bet: float = 1.0) -> SpinResult:
        """
        Play one base spin.  If the scatter bonus triggers it is resolved
        immediately and its results are appended to the returned SpinResult.
        """
        grid = self._generate_grid()
        base_steps, base_raw_win, base_final_grid = self._resolve_cascades(
            grid, multiplier_cap=self._base_max_mult
        )

        total_win = base_raw_win * bet
        bonus_spins_played = 0
        bonus_final_multiplier = 1
        is_bonus = self._is_bonus_triggered(grid)
        final_grid = base_final_grid

        if is_bonus:
            (
                bonus_win,
                bonus_spins_played,
                bonus_steps,
                bonus_final_grid,
                bonus_final_multiplier,
            ) = self._play_bonus(bet)
            total_win += bonus_win
            base_steps.extend(bonus_steps)
            final_grid = bonus_final_grid

        return SpinResult(
            total_win=total_win,
            steps=base_steps,
            final_grid=final_grid,
            is_bonus=is_bonus,
            bonus_spins_played=bonus_spins_played,
            bonus_final_multiplier=bonus_final_multiplier,
            bet=bet,
        )

    # ------------------------------------------------------------------
    # Grid generation
    # ------------------------------------------------------------------

    def _generate_grid(self) -> list[list[str]]:
        rows = self.config["grid_rows"]
        cols = self.config["grid_cols"]
        flat = self.rng.weighted_choices(self._symbols, self._weights, n=rows * cols)
        return [flat[r * cols : (r + 1) * cols] for r in range(rows)]

    # ------------------------------------------------------------------
    # Cascade resolution
    # ------------------------------------------------------------------

    def _resolve_cascades(
        self,
        grid: list[list[str]],
        multiplier_cap: int,
    ) -> tuple[list[CascadeStep], float, list[list[str]]]:
        """
        Iteratively detect winning clusters, record each step, apply gravity,
        and refill until no more clusters form.

        Returns (steps, total_raw_win, final_grid).
        Raw win is before bet scaling so callers can apply their own multipliers.
        """
        grid = copy.deepcopy(grid)
        steps: list[CascadeStep] = []
        total_win = 0.0
        multiplier = 1

        while True:
            clusters = find_clusters(grid, min_size=self._min_cluster)
            if not clusters:
                break

            raw_win = calculate_cluster_win(clusters, self._paytable)
            step_win = raw_win * multiplier
            total_win += step_win

            removed: set[tuple[int, int]] = {
                pos for _, positions in clusters for pos in positions
            }

            steps.append(
                CascadeStep(
                    grid=copy.deepcopy(grid),
                    win_amount=step_win,
                    multiplier=multiplier,
                    removed_positions=removed,
                )
            )

            grid = self._apply_gravity(grid, removed)
            multiplier = min(multiplier + 1, multiplier_cap)

        return steps, total_win, grid

    def _apply_gravity(
        self,
        grid: list[list[str]],
        removed: set[tuple[int, int]],
    ) -> list[list[str]]:
        """
        Remove winning positions then let surviving symbols fall downward.
        Empty cells at the top are filled with newly generated symbols.

        Layout: row 0 = top, row (rows-1) = bottom.
        After gravity the column looks like: [new_symbols..., survivors...]
        so that survivors are at the bottom and refills appear at the top.
        """
        rows = self.config["grid_rows"]
        cols = self.config["grid_cols"]
        result: list[list[str]] = [["" for _ in range(cols)] for _ in range(rows)]

        for c in range(cols):
            # Collect surviving symbols in top-to-bottom order
            surviving = [
                grid[r][c]
                for r in range(rows)
                if (r, c) not in removed and grid[r][c] not in ("EMPTY", "")
            ]
            needed = rows - len(surviving)
            new_symbols = self.rng.weighted_choices(
                self._symbols, self._weights, n=needed
            )
            # New symbols fill from the top; survivors settle at the bottom
            column = new_symbols + surviving
            for r in range(rows):
                result[r][c] = column[r]

        return result

    # ------------------------------------------------------------------
    # Bonus / free spins
    # ------------------------------------------------------------------

    def _is_bonus_triggered(self, grid: list[list[str]]) -> bool:
        count = sum(
            1 for row in grid for cell in row if cell == "SCATTER"
        )
        return count >= self._scatter_count

    def _play_bonus(
        self, bet: float
    ) -> tuple[float, int, list[CascadeStep], list[list[str]], int]:
        """
        Play a free-spin bonus round.

        Rules:
        - Starts with `free_spins` free spins.
        - A persistent multiplier begins at 1 and increases by the number
          of cascade steps recorded in that free spin (capped at max_multiplier).
          The persistent multiplier carries over between free spins.
        - Landing 3+ SCATTERs during a free spin awards another `free_spins`
          free spins (re-trigger), capped by max_total_spins overall.
        - The cascade multiplier within each free spin is separate; the
          persistent multiplier is applied on top of the total raw win.

        Returns (total_bonus_win, spins_played, all_cascade_steps, final_grid, final_multiplier).
        """
        state = BonusState(
            free_spins_remaining=self._bonus_free_spins,
            persistent_multiplier=1,
            active=True,
        )
        total_win = 0.0
        all_steps: list[CascadeStep] = []
        spins_played = 0
        final_grid: list[list[str]] = []

        while state.free_spins_remaining > 0 and spins_played < self._bonus_max_total:
            state.free_spins_remaining -= 1
            spins_played += 1

            grid = self._generate_grid()
            steps, raw_win, spin_final_grid = self._resolve_cascades(
                grid, multiplier_cap=self._bonus_max_mult
            )
            final_grid = spin_final_grid

            # Apply persistent multiplier on top of the accumulated cascade win
            bonus_win = raw_win * state.persistent_multiplier * bet
            total_win += bonus_win

            # Increment persistent multiplier by the cascade depth of this spin
            if steps:
                state.persistent_multiplier = min(
                    state.persistent_multiplier + len(steps),
                    self._bonus_max_mult,
                )

            # Re-trigger check
            if self._is_bonus_triggered(grid):
                state.free_spins_remaining += self._bonus_free_spins

            all_steps.extend(steps)

        return total_win, spins_played, all_steps, final_grid, state.persistent_multiplier
