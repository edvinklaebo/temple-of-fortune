# Temple of Fortune

Temple of Fortune is a Python slot-machine simulator with a Pygame frontend and
a terminal simulation mode. It is an entertainment/demo project that uses
virtual credits only; it does not accept or pay real money.

## Requirements

Python 3.11 or newer is recommended.

Install the dependencies from the repository root:

```powershell
python -m pip install -r requirements.txt
python -m pip install -r frontend/requirements.txt
```

## Play the game

Launch the Pygame game from the repository root:

```powershell
python frontend/main.py
```

Controls: **Space** spins, **A** toggles auto-spin, **Up/Down** adjusts the bet,
**1–3** changes animation speed, **M** toggles audio, and **Esc** quits.

## Run the terminal simulator

Interactive spins:

```powershell
python gambling_sim/main.py --mode spin
```

Monte Carlo simulation:

```powershell
python gambling_sim/main.py --mode simulate --spins 100000
```

Add `--no-visual` to suppress charts. Use `--seed 42` for reproducible results.

## Rules

- The game uses a 6-column × 5-row grid and weighted symbols.
- Clusters of at least five identical, orthogonally connected symbols win.
- Wins are removed; remaining symbols fall and new symbols refill from above.
- Cascade multipliers increase up to ×5 in the base game.
- Three or more scatter symbols on the initial grid trigger ten free spins.
- During free spins, a persistent multiplier increases with cascade depth up to
  ×10. Scatters can retrigger free spins, subject to a 50-spin cap.
- Low, medium, and high volatility presets are available.

See `gambling_sim/config/game_config.py` for symbol weights, payout tables, and
the complete configuration.
