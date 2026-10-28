from __future__ import annotations


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def ease_out_cubic(t: float) -> float:
    """Smooth deceleration curve in [0, 1]."""
    x = _clamp01(t)
    return 1.0 - (1.0 - x) ** 3


def ease_in_quad(t: float) -> float:
    """Acceleration curve in [0, 1]."""
    x = _clamp01(t)
    return x * x


def ease_out_bounce(t: float) -> float:
    """Simple bounce-like curve in [0, 1]."""
    x = _clamp01(t)
    n1 = 7.5625
    d1 = 2.75

    if x < 1 / d1:
        return n1 * x * x
    if x < 2 / d1:
        x -= 1.5 / d1
        return n1 * x * x + 0.75
    if x < 2.5 / d1:
        x -= 2.25 / d1
        return n1 * x * x + 0.9375
    x -= 2.625 / d1
    return n1 * x * x + 0.984375
