from __future__ import annotations

import random
from typing import Any, Sequence

import numpy as np


class RNG:
    """
    Seeded random number generator.

    Wraps random.Random for simple draws (reproducible with seed) and
    numpy's default_rng for fast weighted sampling over large arrays.
    Both internal generators are seeded from the same seed value.
    """

    def __init__(self, seed: int | None = None):
        self._seed = seed
        self._rng = random.Random(seed)
        self._np_rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # Core primitives
    # ------------------------------------------------------------------

    def roll(self) -> float:
        """Return a float in [0.0, 1.0)."""
        return self._rng.random()

    def choice(self, items: Sequence[Any]) -> Any:
        """Uniform random choice from a sequence."""
        return self._rng.choice(items)

    # ------------------------------------------------------------------
    # Weighted sampling (uses numpy for speed)
    # ------------------------------------------------------------------

    def weighted_choice(self, items: Sequence[Any], weights: Sequence[float]) -> Any:
        """Return one item drawn proportionally to weights."""
        weights_arr = np.array(weights, dtype=float)
        weights_arr /= weights_arr.sum()
        idx: int = int(self._np_rng.choice(len(items), p=weights_arr))
        return items[idx]

    def weighted_choices(
        self,
        items: Sequence[Any],
        weights: Sequence[float],
        n: int,
    ) -> list[Any]:
        """Return n items drawn with replacement proportionally to weights."""
        weights_arr = np.array(weights, dtype=float)
        weights_arr /= weights_arr.sum()
        indices: np.ndarray = self._np_rng.choice(len(items), size=n, p=weights_arr)
        return [items[int(i)] for i in indices]

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @property
    def seed(self) -> int | None:
        return self._seed
