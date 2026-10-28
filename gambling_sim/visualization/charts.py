from __future__ import annotations

import sys
from typing import TYPE_CHECKING

try:
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker

    _MPL_AVAILABLE = True
except ImportError:
    _MPL_AVAILABLE = False

if TYPE_CHECKING:
    from gambling_sim.simulation.statistics import SimulationStats


def _check_available() -> bool:
    if not _MPL_AVAILABLE:
        print(
            "matplotlib is not installed.  Run:  pip install matplotlib",
            file=sys.stderr,
        )
        return False
    return True


def _bucket_sort_key(label: str) -> float:
    if label == "0x":
        return -1.0
    try:
        return float(label.split("x")[0].split("-")[0].replace("+", ""))
    except (ValueError, IndexError):
        return 999.0


# ─────────────────────────────────────────────
# Win-size histogram
# ─────────────────────────────────────────────


def plot_win_histogram(
    stats: "SimulationStats",
    title: str = "Win Distribution (frequency per bucket)",
) -> None:
    """
    Bar chart of win counts per multiplier bucket.
    Frequency axis is log-scale to make rare big wins visible.
    Zero-win spins ("0x") are coloured red; all other buckets are blue.
    """
    if not _check_available():
        return

    buckets = stats.win_buckets
    if not buckets:
        print("No win data to plot.")
        return

    sorted_items = sorted(buckets.items(), key=lambda kv: _bucket_sort_key(kv[0]))
    labels = [k for k, _ in sorted_items]
    counts = [v for _, v in sorted_items]
    colors = ["#e74c3c" if lb == "0x" else "#3498db" for lb in labels]

    fig, ax = plt.subplots(figsize=(11, 5))
    bars = ax.bar(labels, counts, color=colors, edgecolor="white", linewidth=0.6)

    ax.set_yscale("log")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Win Range (× bet)", fontsize=11)
    ax.set_ylabel("Frequency (log scale)", fontsize=11)
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"{int(x):,}")
    )
    ax.tick_params(axis="x", rotation=35)

    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() * 1.15,
            f"{count:,}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    fig.tight_layout()
    plt.show()


# ─────────────────────────────────────────────
# RTP convergence graph
# ─────────────────────────────────────────────


def plot_rtp_convergence(
    rtp_series: list[float],
    target_rtp: float | None = None,
    title: str = "RTP Convergence",
) -> None:
    """
    Line chart of running RTP after each spin.
    Shows how the measured RTP converges toward its long-run value.
    An optional red dashed line marks the theoretical target RTP.
    """
    if not _check_available():
        return

    if not rtp_series:
        print("No RTP data to plot.")
        return

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(
        rtp_series,
        color="#2ecc71",
        linewidth=0.7,
        alpha=0.9,
        label="Measured RTP",
    )

    if target_rtp is not None:
        ax.axhline(
            y=target_rtp,
            color="#e74c3c",
            linestyle="--",
            linewidth=1.3,
            label=f"Target RTP ({target_rtp:.1%})",
        )

    final_rtp = rtp_series[-1]
    ax.axhline(
        y=final_rtp,
        color="#3498db",
        linestyle=":",
        linewidth=1.1,
        label=f"Final measured RTP ({final_rtp:.2%})",
    )

    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Spin number", fontsize=11)
    ax.set_ylabel("Return to Player", fontsize=11)
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"{x:.1%}")
    )
    ax.legend(fontsize=10)

    fig.tight_layout()
    plt.show()
