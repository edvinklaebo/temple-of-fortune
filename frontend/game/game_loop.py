from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pygame

from animation.animator import Animator
from input_handler import InputHandler
from pygame_config import ANIM_FALL, ANIM_REFILL, ANIM_REMOVAL, ANIM_STEP_DELAY, ANIM_WIN_HIGHLIGHT, FPS, SPEED_MODES
from rendering.effects import DelayEffect, FallEffect, RefillEffect, RemovalEffect, WinHighlightEffect

from pygame_config import (
    MIN_BET,
    MAX_BET,
    BET_INCREMENT,
)
from game.state import GameState

if TYPE_CHECKING:
    pass


class GameLoop:
    """
    Main game loop: handle input, update state, render.

    Runs at 60 FPS and orchestrates all game logic.
    """

    def __init__(self, state: GameState, engine, renderer, audio):
        """
        Parameters
        ----------
        state : GameState
            Mutable game state.
        engine : EngineAdapter
            Backend slot machine interface.
        renderer : Renderer
            Rendering pipeline.
        audio : AudioRenderer
            Audio system.
        """
        self.state = state
        self.engine = engine
        self.renderer = renderer
        self.audio = audio

        self.running = True
        self.clock = pygame.time.Clock()
        self.animator = Animator()
        self.input_handler = InputHandler()

    def handle_events(self) -> bool:
        """
        Process events (input, quit, etc.).

        Returns False if quit requested, True otherwise.
        """
        actions = self.input_handler.gather()
        if actions.quit_requested:
            return False

        if self.state.big_win_confirm_required:
            if actions.spin or actions.click_any:
                self.audio.play_sound("ui_click")
                self.state.clear_big_win_confirmation()
            return True

        if actions.spin:
            self._do_spin()

        if actions.toggle_auto_spin:
            self.state.auto_spin_enabled = not self.state.auto_spin_enabled
            self.state.auto_spin_remaining = None

        if actions.bet_down:
            self._adjust_bet(-BET_INCREMENT)

        if actions.bet_up:
            self._adjust_bet(BET_INCREMENT)

        if actions.toggle_debug:
            self.state.debug_enabled = not self.state.debug_enabled

        if actions.speed_mode:
            self.state.set_speed_mode(actions.speed_mode)

        if actions.toggle_mute:
            self.audio.enabled = not self.audio.enabled

        if actions.click_spin:
            self.state.set_pressed_button("spin")
            self.audio.play_sound("ui_click")
            self._do_spin()

        if actions.click_bet_minus:
            self.state.set_pressed_button("bet_minus")
            self.audio.play_sound("ui_click")
            self._adjust_bet(-BET_INCREMENT)

        if actions.click_bet_plus:
            self.state.set_pressed_button("bet_plus")
            self.audio.play_sound("ui_click")
            self._adjust_bet(BET_INCREMENT)

        return True

    def update(self) -> None:
        """Update game state each frame."""
        dt_ms = self.clock.get_time()
        self.state.update_feedback(dt_ms)
        self.animator.update(self.state, dt_ms)

        if self.state.pending_sound_event:
            self.audio.play_sound(self.state.pending_sound_event)
            self.state.pending_sound_event = None

        if self.state.is_spinning and not self.animator.is_busy:
            completed_result = self.state.current_result
            self.state.reset_spin_state()
            self.state.clear_animation_state()
            self.state.commit_last_win_amount()
            if completed_result is not None:
                self._arm_big_win_confirmation(completed_result)

        # If auto-spin is enabled and not currently spinning, trigger spin
        if self.state.auto_spin_enabled and not self.state.is_spinning and not self.state.big_win_confirm_required:
            self._do_spin()

    def render(self) -> None:
        """Render the current frame."""
        mouse_pos = pygame.mouse.get_pos()
        self.renderer.render(self.state, mouse_pos)

    def run(self) -> None:
        """Main game loop."""
        while self.running:
            self.clock.tick(FPS)
            self.running = self.handle_events()
            self.update()
            self.render()

    # ──────────────────────────────────────────────────────────────
    # Private handlers
    # ──────────────────────────────────────────────────────────────

    def _do_spin(self) -> None:
        """Execute a spin."""
        if self.state.is_spinning or self.state.big_win_confirm_required:
            return  # Already spinning

        if self.state.balance < self.state.bet:
            print("[Game] Insufficient balance!")
            return  # Not enough money

        # Deduct bet
        self.state.deduct_bet()

        # Request spin from backend
        self.state.is_spinning = True
        result = self.engine.spin(bet=self.state.bet)

        # Record result
        self.state.record_spin(result)
        self.state.clear_animation_state()

        # Play sound
        self.audio.play_sound("spin_start")
        if result.get("is_bonus"):
            self.audio.play_sound("bonus_trigger")
        if result.get("total_win", 0.0) >= self.state.bet * 20:
            self.audio.play_sound("big_win")

        self._queue_cascade_animations(result)

        # No wins: end immediately and show final settled grid.
        if not result["steps"]:
            self.state.reset_spin_state()
            self.state.commit_last_win_amount()
            self._arm_big_win_confirmation(result)

    def _arm_big_win_confirmation(self, result: dict) -> None:
        """Require confirmation after large wins before allowing next spin."""
        total_win = float(result.get("total_win", 0.0))
        self.state.require_big_win_confirmation(total_win=total_win, bet=self.state.bet)

    def _queue_cascade_animations(self, result: dict) -> None:
        """Build the per-cascade animation sequence for one spin result."""
        self.animator.clear()

        steps = result.get("steps", [])
        final_grid = result.get("final_grid")
        speed = self._speed_multiplier()

        for index, step in enumerate(steps):
            step_grid = step["grid"]
            removed_positions = set(step["removed_positions"])

            if index < len(steps) - 1:
                next_grid = steps[index + 1]["grid"]
            else:
                next_grid = final_grid or step_grid

            self.animator.enqueue(
                WinHighlightEffect(
                    duration_ms=ANIM_WIN_HIGHLIGHT * speed,
                    step_grid=step_grid,
                    removed_positions=removed_positions,
                    multiplier=step["multiplier"],
                    win_amount=step["win_amount"],
                )
            )
            self.animator.enqueue(
                RemovalEffect(
                    duration_ms=ANIM_REMOVAL * speed,
                    step_grid=step_grid,
                    removed_positions=removed_positions,
                )
            )

            fall_effect = FallEffect(
                duration_ms=ANIM_FALL * speed,
                step_grid=step_grid,
                next_grid=next_grid,
                removed_positions=removed_positions,
            )
            self.animator.enqueue(fall_effect)

            # Recompute new positions with the same logic used by FallEffect.
            new_positions = self._find_new_symbol_positions(step_grid, next_grid, removed_positions)
            self.animator.enqueue(
                RefillEffect(
                    duration_ms=ANIM_REFILL * speed,
                    next_grid=next_grid,
                    new_positions=new_positions,
                )
            )
            self.animator.enqueue(DelayEffect(duration_ms=ANIM_STEP_DELAY * speed))

    def _find_new_symbol_positions(
        self,
        step_grid: list[list[str]],
        next_grid: list[list[str]],
        removed_positions: set[tuple[int, int]],
    ) -> set[tuple[int, int]]:
        """Infer newly inserted cells by column from removal depth."""
        from pygame_config import GRID_COLS, GRID_ROWS

        new_positions: set[tuple[int, int]] = set()
        for col in range(GRID_COLS):
            survivors = [
                (row, step_grid[row][col])
                for row in range(GRID_ROWS)
                if (row, col) not in removed_positions
            ]
            needed = GRID_ROWS - len(survivors)
            for row in range(needed):
                new_positions.add((row, col))
        return new_positions

    def _speed_multiplier(self) -> float:
        """Return animation duration multiplier for current speed mode."""
        return SPEED_MODES.get(self.state.speed_mode, 1.0)

    def _adjust_bet(self, delta: float) -> None:
        """Adjust the bet amount."""
        if self.state.is_spinning:
            return

        new_bet = self.state.bet + delta
        new_bet = max(MIN_BET, min(MAX_BET, new_bet))
        self.state.bet = round(new_bet, 2)
        self.state.trigger_bet_feedback()
