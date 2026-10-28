from __future__ import annotations

from dataclasses import dataclass, field

from animation.easing import ease_in_quad, ease_out_bounce, ease_out_cubic
from pygame_config import CELL_SIZE, GRID_COLS, GRID_ROWS


def _copy_grid(grid: list[list[str]]) -> list[list[str]]:
    return [row[:] for row in grid]


def _compute_fall_offsets(
    from_grid: list[list[str]],
    to_grid: list[list[str]],
    removed_positions: set[tuple[int, int]],
) -> tuple[dict[tuple[int, int], float], set[tuple[int, int]]]:
    """Map each symbol in the target grid to a starting Y offset in pixels."""
    offsets: dict[tuple[int, int], float] = {}
    new_positions: set[tuple[int, int]] = set()

    for col in range(GRID_COLS):
        survivors = [
            (row, from_grid[row][col])
            for row in range(GRID_ROWS)
            if (row, col) not in removed_positions
        ]
        needed = GRID_ROWS - len(survivors)

        for idx, (old_row, _) in enumerate(survivors):
            new_row = needed + idx
            offsets[(new_row, col)] = float((old_row - new_row) * CELL_SIZE)

        for new_row in range(needed):
            offsets[(new_row, col)] = float(-needed * CELL_SIZE)
            new_positions.add((new_row, col))

        for row in range(GRID_ROWS):
            offsets.setdefault((row, col), 0.0)

    return offsets, new_positions


@dataclass
class Effect:
    duration_ms: float
    elapsed_ms: float = 0.0

    def on_start(self, state) -> None:
        pass

    def on_update(self, state, t: float) -> None:
        pass

    def on_finish(self, state) -> None:
        pass


@dataclass
class WinHighlightEffect(Effect):
    step_grid: list[list[str]] = field(default_factory=list)
    removed_positions: set[tuple[int, int]] = field(default_factory=set)
    multiplier: int = 1
    win_amount: float = 0.0

    def on_start(self, state) -> None:
        state.anim_grid = _copy_grid(self.step_grid)
        state.anim_highlight_positions = set(self.removed_positions)
        state.anim_hidden_positions = set()
        state.anim_cell_offsets = {}
        state.anim_cell_scales = {}
        state.anim_new_positions = set()
        state.anim_multiplier_value = self.multiplier if self.multiplier > 1 else None
        state.anim_multiplier_progress = 0.0
        if self.win_amount > 0:
            state.pending_sound_event = f"win_chime_x{max(1, self.multiplier)}"

    def on_update(self, state, t: float) -> None:
        state.anim_multiplier_progress = ease_out_bounce(t)


@dataclass
class RemovalEffect(Effect):
    step_grid: list[list[str]] = field(default_factory=list)
    removed_positions: set[tuple[int, int]] = field(default_factory=set)

    def on_start(self, state) -> None:
        state.anim_grid = _copy_grid(self.step_grid)
        state.anim_highlight_positions = set(self.removed_positions)
        state.anim_hidden_positions = set()
        state.anim_cell_offsets = {}
        state.anim_new_positions = set()

    def on_update(self, state, t: float) -> None:
        shrink = 1.0 - 0.8 * ease_in_quad(t)
        state.anim_cell_scales = {
            pos: shrink for pos in self.removed_positions
        }

    def on_finish(self, state) -> None:
        state.anim_hidden_positions = set(self.removed_positions)
        state.anim_highlight_positions = set()
        state.anim_cell_scales = {}


@dataclass
class FallEffect(Effect):
    step_grid: list[list[str]] = field(default_factory=list)
    next_grid: list[list[str]] = field(default_factory=list)
    removed_positions: set[tuple[int, int]] = field(default_factory=set)
    _start_offsets: dict[tuple[int, int], float] = field(default_factory=dict)

    def on_start(self, state) -> None:
        offsets, new_positions = _compute_fall_offsets(
            self.step_grid,
            self.next_grid,
            self.removed_positions,
        )
        state.anim_grid = _copy_grid(self.next_grid)
        state.anim_hidden_positions = set()
        state.anim_highlight_positions = set()
        state.anim_new_positions = set(new_positions)
        state.anim_cell_scales = {}
        state.anim_cell_offsets = offsets
        self._start_offsets = offsets
        state.pending_sound_event = "cascade_pop"

    def on_update(self, state, t: float) -> None:
        eased = ease_out_cubic(t)
        state.anim_cell_offsets = {
            pos: start_offset * (1.0 - eased)
            for pos, start_offset in self._start_offsets.items()
        }

    def on_finish(self, state) -> None:
        state.anim_cell_offsets = {}


@dataclass
class RefillEffect(Effect):
    next_grid: list[list[str]] = field(default_factory=list)
    new_positions: set[tuple[int, int]] = field(default_factory=set)

    def on_start(self, state) -> None:
        state.anim_grid = _copy_grid(self.next_grid)
        state.anim_highlight_positions = set()
        state.anim_hidden_positions = set()
        state.anim_cell_offsets = {}
        state.anim_new_positions = set(self.new_positions)

    def on_update(self, state, t: float) -> None:
        bounce = ease_out_bounce(t)
        scale = 0.75 + 0.25 * bounce
        state.anim_cell_scales = {pos: scale for pos in self.new_positions}

    def on_finish(self, state) -> None:
        state.anim_cell_scales = {}
        state.anim_new_positions = set()


@dataclass
class DelayEffect(Effect):
    def on_start(self, state) -> None:
        pass
