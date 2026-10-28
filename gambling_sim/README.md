# Gambling Simulator

A transparent Python slot-machine / gambling simulator that demonstrates RNG-based outcome generation, Return to Player (RTP), volatility, and cascading mechanics.  No fake wins, no misleading UX — every number shown is the real outcome.

---

## Project Structure

```
gambling_sim/
├── config/
│   └── game_config.py      # All tunable parameters (grid, symbols, paytable, volatility presets)
├── core/
│   ├── rng.py              # Seeded RNG wrapper (random + numpy)
│   ├── models.py           # CascadeStep, SpinResult, BonusState dataclasses
│   ├── payout.py           # BFS cluster detection + payout calculation
│   └── slot_machine.py     # Game engine: grid generation, cascades, bonus round
├── simulation/
│   ├── runner.py           # Monte Carlo loop (run_simulation)
│   └── statistics.py       # SimulationStats: win frequency, distribution, streaks
├── ui/
│   └── cli.py              # Rich-based terminal display
├── visualization/
│   └── charts.py           # matplotlib: win histogram + RTP convergence graph
└── main.py                 # Entry point (argparse)
```

---

## Requirements

Python 3.11+

```bash
pip install -r requirements.txt
```

`requirements.txt` installs `rich`, `matplotlib`, and `numpy`.

---

## Usage

### Interactive spin mode

Step through individual spins with cascade-by-cascade output.

```bash
python gambling_sim/main.py --mode spin
python gambling_sim/main.py --mode spin --seed 42 --bet 5.0 --volatility high
```

Type **Enter** to spin again, **q** + Enter to quit.

### Monte Carlo simulation

Run a large batch and see RTP, win distribution, and charts.

```bash
python gambling_sim/main.py --mode simulate --spins 100000
python gambling_sim/main.py --mode simulate --spins 50000 --volatility low
python gambling_sim/main.py --mode simulate --spins 50000 --volatility high --no-visual
```

---

## CLI Options

| Option | Default | Description |
|---|---|---|
| `--mode` | `simulate` | `spin` (interactive) or `simulate` (batch) |
| `--spins N` | `100000` | Number of spins for simulation mode |
| `--seed S` | None | Integer seed — same seed → identical output |
| `--bet AMOUNT` | `1.0` | Bet per spin; all wins scale linearly |
| `--volatility` | `medium` | `low` / `medium` / `high` |
| `--no-visual` | off | Suppress matplotlib charts |

---

## Game Mechanics

### Grid
6 columns × 5 rows.  Symbols are drawn from weighted probabilities each spin.

### Symbols & Weights (medium volatility)
| Symbol | Weight | Notes |
|--------|--------|-------|
| A | 30% | Most common; lowest pay |
| B | 25% | |
| C | 20% | |
| D | 15% | |
| E | 8% | Rare; highest pay |
| SCATTER | 2% | Triggers bonus round only |

### Cluster Pays
A win requires **5 or more** identical, orthogonally connected symbols.  Payout scales with cluster size (5–12+ cells).  Larger clusters pay more.

### Cascading
After a win, matched symbols are removed and surviving symbols fall downward (gravity).  New symbols fill from the top.  Each subsequent cascade applies an incrementing multiplier (base game: ×1 → ×2 → … → ×5 cap).

### Bonus Round
Landing **3+ SCATTER** symbols anywhere on the grid triggers **10 free spins**.  A persistent multiplier starts at ×1 and increments by the number of cascade steps each free spin, up to ×10.  The multiplier carries across free spins.  Re-triggering (another 3+ SCATTERs during free spins) awards 10 more free spins, up to a 50-spin safety cap.

### Volatility Presets
| Preset | Effect |
|--------|--------|
| `low` | Common symbols heavier → frequent small wins, lower variance |
| `medium` | Base configuration |
| `high` | Rare symbols heavier + 2× payout scale → infrequent but large wins |

---

## Understanding RTP

**RTP (Return to Player)** is the percentage of all wagers returned as winnings over a large number of spins.

- RTP = 96% means for every £100 wagered, £96 is returned *on average over many spins*.
- The remaining 4% is the **house edge**.
- Short sessions deviate wildly from the theoretical RTP; the simulation shows convergence.
- **No gambling system overcomes a negative-expectation game.**

The simulation shows the actual measured RTP, not a marketing figure.  The RTP convergence chart illustrates how individual session results vary before settling near the long-run value.

---

## Reproducibility

Pass `--seed N` to get identical grids and outcomes every run:

```bash
python main.py --mode spin --seed 42
# Every run with seed=42 produces the exact same sequence of spins.
```
