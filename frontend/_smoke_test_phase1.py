#!/usr/bin/env python3
"""Smoke test for Phase 1 frontend integration."""

from pathlib import Path
import sys
import traceback

sys.path.insert(0, str(Path(__file__).parent.parent))


def main() -> int:
    print("Testing Phase 1 backend integration...")
    print()

    try:
        print("Testing pygame import...")
        import pygame

        print(f"OK pygame {pygame.__version__}")

        print()
        print("Testing pygame_config...")
        from pygame_config import STARTING_BALANCE, WINDOW_HEIGHT, WINDOW_WIDTH

        assert WINDOW_WIDTH > 0 and WINDOW_HEIGHT > 0
        assert STARTING_BALANCE > 0
        print(f"OK config window={WINDOW_WIDTH}x{WINDOW_HEIGHT}")

        print()
        print("Testing GameState...")
        from game.state import GameState

        state = GameState(balance=1000, bet=10)
        assert state.balance == 1000
        assert state.deduct_bet() is True
        assert state.balance == 990
        state.add_win(25)
        assert state.balance == 1015
        assert state.session_rtp == 25 / 10
        print("OK GameState logic")

        print()
        print("Testing EngineAdapter...")
        from integration.engine_adapter import EngineAdapter

        adapter = EngineAdapter(seed=42, volatility="medium")
        result = adapter.spin(bet=1.0)

        assert isinstance(result, dict)
        assert "total_win" in result
        assert "steps" in result
        assert "is_bonus" in result
        assert "bonus_spins_played" in result
        assert "bonus_final_multiplier" in result
        assert "final_grid" in result
        assert result["total_win"] >= 0
        assert isinstance(result["steps"], list)
        assert isinstance(result["final_grid"], list)

        if result["steps"]:
            step = result["steps"][0]
            assert "grid" in step
            assert "win_amount" in step
            assert "multiplier" in step
            assert "removed_positions" in step

        print(
            "OK EngineAdapter spin=%.2f steps=%d bonus=%s"
            % (result["total_win"], len(result["steps"]), result["is_bonus"])
        )

        print()
        print("Testing state + adapter integration...")
        state = GameState(balance=1000, bet=5)
        initial_balance = state.balance
        state.deduct_bet()
        adapter_result = adapter.spin(bet=5)
        state.record_spin(adapter_result)

        expected_balance = initial_balance - 5 + adapter_result["total_win"]
        assert state.balance == expected_balance
        print("OK Integration balance=%.2f last_win=%.2f" % (state.balance, state.last_win_amount))

        print()
        print("Testing 100-spin session stats...")
        state = GameState(balance=1000, bet=1)
        for _ in range(100):
            if state.balance < state.bet:
                break
            state.deduct_bet()
            spin_result = adapter.spin(bet=state.bet)
            state.record_spin(spin_result)

        assert state.session_spins == 100
        assert state.session_total_bet == 100
        print(
            "OK Session spins=%d RTP=%.2f%% profit=%.2f"
            % (state.session_spins, state.session_rtp * 100, state.session_profit)
        )

        print()
        print("=" * 60)
        print("PHASE 1 INTEGRATION TEST PASSED")
        print("=" * 60)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
