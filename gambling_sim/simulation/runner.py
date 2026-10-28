from __future__ import annotations

from typing import TYPE_CHECKING

from gambling_sim.simulation.statistics import SimulationStats

if TYPE_CHECKING:
    from gambling_sim.core.slot_machine import SlotMachine


def run_simulation(
    slot_machine: "SlotMachine",
    spins: int,
    bet: float = 1.0,
) -> dict:
    """
    Monte Carlo simulation: spin *spins* times and aggregate results.

    Returns
    -------
    dict with keys:
        spins          — number of spins run
        total_bet      — total amount wagered
        total_return   — total amount won
        rtp            — total_return / total_bet  (e.g. 0.9612 = 96.12 %)
        profit         — total_return - total_bet  (negative = house edge)
        rtp_series     — list[float] — running RTP after each spin (for convergence plot)
        stats          — SimulationStats instance with full distribution data
    """
    stats = SimulationStats()
    total_bet = 0.0
    total_return = 0.0
    rtp_series: list[float] = []

    for _ in range(spins):
        result = slot_machine.spin(bet=bet)
        total_bet += bet
        total_return += result.total_win
        stats.record_spin(result)
        rtp_series.append(total_return / total_bet)

    rtp = total_return / total_bet if total_bet > 0 else 0.0

    return {
        "spins": spins,
        "total_bet": total_bet,
        "total_return": round(total_return, 2),
        "rtp": rtp,
        "profit": round(total_return - total_bet, 2),
        "rtp_series": rtp_series,
        "stats": stats,
    }
