from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Protocol


class Animation(Protocol):
    duration_ms: float
    elapsed_ms: float

    def on_start(self, state) -> None:
        ...

    def on_update(self, state, t: float) -> None:
        ...

    def on_finish(self, state) -> None:
        ...


@dataclass
class _QueuedAnimation:
    animation: Animation
    started: bool = False


class Animator:
    """FIFO animation queue that advances one effect at a time."""

    def __init__(self) -> None:
        self._queue: deque[_QueuedAnimation] = deque()

    def clear(self) -> None:
        self._queue.clear()

    def enqueue(self, animation: Animation) -> None:
        self._queue.append(_QueuedAnimation(animation=animation))

    @property
    def is_busy(self) -> bool:
        return bool(self._queue)

    def update(self, state, dt_ms: float) -> None:
        if not self._queue:
            return

        current = self._queue[0]
        animation = current.animation

        if not current.started:
            current.started = True
            animation.elapsed_ms = 0.0
            animation.on_start(state)

        duration = max(1.0, animation.duration_ms)
        animation.elapsed_ms += max(0.0, dt_ms)
        t = min(1.0, animation.elapsed_ms / duration)
        animation.on_update(state, t)

        if animation.elapsed_ms >= duration:
            animation.on_finish(state)
            self._queue.popleft()
