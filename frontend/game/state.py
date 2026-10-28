from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pygame_config import (
    BIG_WIN_CONFIRM_MULTIPLIER,
    BONUS_OVERLAY_DURATION_MS,
    LOSS_STREAK_ALERT_THRESHOLD,
    LOSS_STREAK_FLASH_MS,
)


@dataclass
class GameState:
    """
    Mutable game state — tracks balance, bet, spin status, and current result.
    Read-only from rendering layer (no side effects in draw calls).
    """

    balance: float = 1000.0
    bet: float = 1.0
    is_spinning: bool = False
    auto_spin_enabled: bool = False
    current_result: dict[str, Any] | None = None
    debug_enabled: bool = False
    speed_mode: str = "normal"  # "normal", "fast", "turbo"
    auto_spin_remaining: int | None = None
    session_spins: int = 0
    session_total_bet: float = 0.0
    session_total_win: float = 0.0
    last_win_amount: float = 0.0
    pending_last_win_amount: float = 0.0
    consecutive_losses: int = 0
    max_consecutive_losses: int = 0

    # Animation-layer visual state (Phase 2)
    anim_grid: list[list[str]] | None = None
    anim_highlight_positions: set[tuple[int, int]] = field(default_factory=set)
    anim_hidden_positions: set[tuple[int, int]] = field(default_factory=set)
    anim_new_positions: set[tuple[int, int]] = field(default_factory=set)
    anim_cell_offsets: dict[tuple[int, int], float] = field(default_factory=dict)
    anim_cell_scales: dict[tuple[int, int], float] = field(default_factory=dict)
    anim_multiplier_value: int | None = None
    anim_multiplier_progress: float = 0.0
    pending_sound_event: str | None = None

    # UI feedback state (Phase 3)
    balance_feedback_ms: float = 0.0
    balance_feedback_positive: bool = False
    balance_pulse_scale: float = 1.0
    bet_feedback_ms: float = 0.0
    pressed_button: str | None = None
    pressed_button_ms: float = 0.0
    bonus_overlay_ms: float = 0.0
    bonus_overlay_total_ms: float = BONUS_OVERLAY_DURATION_MS
    bonus_last_spins_played: int = 0
    bonus_last_final_multiplier: int = 1
    bonus_trigger_popup_ms: float = 0.0
    bonus_trigger_popup_total_ms: float = 1400.0
    bonus_spins_awarded: int = 0
    loss_streak_flash_ms: float = 0.0

    # Blocking confirmation modal for >=5x bet wins.
    big_win_confirm_required: bool = False
    big_win_confirm_amount: float = 0.0
    big_win_confirm_multiplier: float = 0.0

    # ──────────────────────────────────────────────────────────────
    # Public methods
    # ──────────────────────────────────────────────────────────────

    def deduct_bet(self) -> bool:
        """Deduct bet from balance. Return True if sufficient funds, False otherwise."""
        if self.balance >= self.bet:
            self.balance -= self.bet
            self.session_total_bet += self.bet
            return True
        return False

    def add_win(self, amount: float) -> None:
        """Add winnings to balance and track session stats."""
        self.balance += amount
        self.session_total_win += amount
        # Keep UI stable during spin animation and reveal this value once settled.
        self.pending_last_win_amount = amount
        self.trigger_balance_feedback(amount)

    def commit_last_win_amount(self) -> None:
        """Reveal the latest win amount in UI after spin animation completes."""
        self.last_win_amount = self.pending_last_win_amount

    def record_spin(self, result: dict[str, Any]) -> None:
        """Record spin result from backend."""
        self.session_spins += 1
        self.current_result = result
        total_win = result.get("total_win", 0.0)
        self.add_win(total_win)

        if total_win > 0:
            self.consecutive_losses = 0
            self.loss_streak_flash_ms = 0.0
        else:
            self.consecutive_losses += 1
            self.max_consecutive_losses = max(self.max_consecutive_losses, self.consecutive_losses)
            if self.consecutive_losses >= LOSS_STREAK_ALERT_THRESHOLD:
                self.loss_streak_flash_ms = LOSS_STREAK_FLASH_MS

        if result.get("is_bonus"):
            self.bonus_overlay_ms = BONUS_OVERLAY_DURATION_MS
            self.bonus_overlay_total_ms = BONUS_OVERLAY_DURATION_MS
            self.bonus_last_spins_played = int(result.get("bonus_spins_played", 0))
            self.bonus_last_final_multiplier = int(result.get("bonus_final_multiplier", 1))
            self.bonus_spins_awarded = int(result.get("bonus_spins_awarded", 10))
            self.bonus_trigger_popup_ms = self.bonus_trigger_popup_total_ms

    def reset_spin_state(self) -> None:
        """Mark spin as finished while keeping last result visible."""
        self.is_spinning = False

    def clear_animation_state(self) -> None:
        """Reset transient animation-only state."""
        self.anim_grid = None
        self.anim_highlight_positions = set()
        self.anim_hidden_positions = set()
        self.anim_new_positions = set()
        self.anim_cell_offsets = {}
        self.anim_cell_scales = {}
        self.anim_multiplier_value = None
        self.anim_multiplier_progress = 0.0
        self.pending_sound_event = None

    def update_feedback(self, dt_ms: float) -> None:
        """Advance short-lived UI feedback timers."""
        if self.balance_feedback_ms > 0:
            self.balance_feedback_ms = max(0.0, self.balance_feedback_ms - dt_ms)
            progress = self.balance_feedback_ms / 260.0
            self.balance_pulse_scale = 1.0 + 0.08 * progress
        else:
            self.balance_pulse_scale = 1.0

        if self.bet_feedback_ms > 0:
            self.bet_feedback_ms = max(0.0, self.bet_feedback_ms - dt_ms)

        if self.pressed_button_ms > 0:
            self.pressed_button_ms = max(0.0, self.pressed_button_ms - dt_ms)
            if self.pressed_button_ms == 0:
                self.pressed_button = None

        if self.bonus_overlay_ms > 0:
            self.bonus_overlay_ms = max(0.0, self.bonus_overlay_ms - dt_ms)

        if self.bonus_trigger_popup_ms > 0:
            self.bonus_trigger_popup_ms = max(0.0, self.bonus_trigger_popup_ms - dt_ms)

        if self.loss_streak_flash_ms > 0:
            self.loss_streak_flash_ms = max(0.0, self.loss_streak_flash_ms - dt_ms)

    def trigger_balance_feedback(self, win_amount: float) -> None:
        """Pulse balance display and color-flash based on win/loss direction."""
        self.balance_feedback_positive = win_amount >= 0
        self.balance_feedback_ms = 260.0

    def trigger_bet_feedback(self) -> None:
        """Flash bet display after adjustment."""
        self.bet_feedback_ms = 180.0

    def set_pressed_button(self, button_name: str) -> None:
        """Show a brief pressed state for clicked UI buttons."""
        self.pressed_button = button_name
        self.pressed_button_ms = 120.0

    def set_speed_mode(self, mode: str) -> None:
        """Set animation speed mode."""
        if mode in ("normal", "fast", "turbo"):
            self.speed_mode = mode

    def require_big_win_confirmation(self, total_win: float, bet: float) -> None:
        """Pause progression until player confirms a sufficiently large win."""
        if bet <= 0:
            return
        mult = total_win / bet
        if mult >= BIG_WIN_CONFIRM_MULTIPLIER:
            self.big_win_confirm_required = True
            self.big_win_confirm_amount = total_win
            self.big_win_confirm_multiplier = mult

    def clear_big_win_confirmation(self) -> None:
        """Dismiss big win confirmation modal and allow play to continue."""
        self.big_win_confirm_required = False
        self.big_win_confirm_amount = 0.0
        self.big_win_confirm_multiplier = 0.0

    @property
    def session_rtp(self) -> float:
        """Return session RTP as a percentage (e.g., 0.95 = 95%)."""
        if self.session_total_bet == 0:
            return 0.0
        return self.session_total_win / self.session_total_bet

    @property
    def session_profit(self) -> float:
        """Return session profit (negative = loss)."""
        return self.session_total_win - self.session_total_bet
