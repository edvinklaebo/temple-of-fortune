from __future__ import annotations

import math
from functools import lru_cache

import pygame

from pygame_config import (
    BONUS_OVERLAY_FADE_MS,
    BONUS_OVERLAY_SLIDE_MS,
    COLOR_TEXT,
    COLOR_BUTTON_NORMAL,
    COLOR_BUTTON_HOVER,
    COLOR_BUTTON_PRESS,
    COLOR_LOSS,
    COLOR_WIN,
    FONT_SIZE_DEBUG,
    SPIN_BUTTON_X,
    SPIN_BUTTON_Y,
    SPIN_BUTTON_WIDTH,
    SPIN_BUTTON_HEIGHT,
    BET_MINUS_X,
    BET_MINUS_Y,
    BET_PLUS_X,
    BET_PLUS_Y,
    BET_BUTTON_WIDTH,
    BET_BUTTON_HEIGHT,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    GRID_X,
    GRID_Y,
    GRID_COLS,
    CELL_SIZE,
    FONT_NAME_UI,
    UI_PANEL_Y,
    UI_PANEL_HEIGHT,
    UI_LEFT_X,
    UI_CENTER_X,
    UI_RIGHT_X,
)
from game.state import GameState


@lru_cache(maxsize=32)
def _get_font(size: int, bold: bool = False) -> pygame.font.Font:
    return pygame.font.SysFont(FONT_NAME_UI, size, bold=bold)


def draw_ui(
    screen: pygame.Surface,
    state: GameState,
    font_ui: pygame.font.Font,
    mouse_pos: tuple[int, int],
) -> None:
    """
    Draw the UI layer: balance, bet, last win, buttons, and status.

    Parameters
    ----------
    screen : pygame.Surface
        The display surface.
    state : GameState
        Current game state.
    font_ui : pygame.font.Font
        Font for UI text.
    mouse_pos : tuple[int, int]
        Current mouse position (for button hover detection).
    """
    ticks = pygame.time.get_ticks()
    panel_y = UI_PANEL_Y

    font_big = _get_font(34, bold=True)
    font_mid = _get_font(22, bold=True)
    font_small = _get_font(FONT_SIZE_DEBUG + 2)
    font_spin = _get_font(30, bold=True)

    # Top strip dedicated to wins only.
    top_w = 540
    top_x = (WINDOW_WIDTH - top_w) // 2
    top_y = 42
    top_panel = pygame.Surface((top_w, 52), pygame.SRCALPHA)
    top_panel.fill((16, 10, 6, 182))
    screen.blit(top_panel, (top_x, top_y))
    pygame.draw.rect(screen, COLOR_TEXT, (top_x, top_y, top_w, 52), width=1)

    win_color = COLOR_WIN if state.last_win_amount > 0 else COLOR_TEXT
    win_scale = 1.0 + 0.15 * (0.5 + 0.5 * math.sin(ticks * 0.012)) if state.last_win_amount > 0 else 1.0
    win_text = font_big.render(f"LAST WIN  ${state.last_win_amount:.2f}", True, win_color)
    if win_scale != 1.0:
        ww = max(1, int(win_text.get_width() * win_scale))
        wh = max(1, int(win_text.get_height() * win_scale))
        win_text = pygame.transform.smoothscale(win_text, (ww, wh))
    win_rect = win_text.get_rect(center=(top_x + top_w // 2, top_y + 26))
    screen.blit(win_text, win_rect)

    # Bottom dock keeps session information and controls on a shared baseline.
    panel_h = UI_PANEL_HEIGHT
    dock_rect = pygame.Rect(12, panel_y, WINDOW_WIDTH - 24, panel_h)
    pygame.draw.rect(screen, (7, 4, 3), dock_rect.move(0, 5), border_radius=18)
    pygame.draw.rect(screen, (18, 12, 8), dock_rect, border_radius=18)
    pygame.draw.rect(screen, (145, 108, 54), dock_rect, width=2, border_radius=18)
    pygame.draw.line(
        screen,
        (238, 195, 101),
        (dock_rect.x + 18, dock_rect.y + 2),
        (dock_rect.right - 18, dock_rect.y + 2),
        2,
    )

    left_box = pygame.Rect(UI_LEFT_X, panel_y + 10, 260, panel_h - 20)
    center_box = pygame.Rect(UI_CENTER_X - 210, panel_y + 10, 420, panel_h - 20)
    right_box = pygame.Rect(UI_RIGHT_X, panel_y + 10, 260, panel_h - 20)
    for box, fill in (
        (left_box, (35, 24, 16)),
        (center_box, (29, 19, 12)),
        (right_box, (35, 24, 16)),
    ):
        pygame.draw.rect(screen, fill, box, border_radius=12)
        pygame.draw.rect(screen, (112, 82, 43), box, width=1, border_radius=12)

    if state.balance_feedback_ms > 0:
        balance_color = COLOR_WIN if state.balance_feedback_positive else COLOR_LOSS
    else:
        balance_color = COLOR_WIN if state.balance > 0 else COLOR_LOSS

    balance_label = font_small.render("YOUR BALANCE", True, (194, 164, 112))
    screen.blit(balance_label, (left_box.x + 14, left_box.y + 9))

    balance_text = font_big.render(f"${state.balance:.2f}", True, balance_color)
    if state.balance_pulse_scale != 1.0:
        bw = max(1, int(balance_text.get_width() * state.balance_pulse_scale))
        bh = max(1, int(balance_text.get_height() * state.balance_pulse_scale))
        balance_text = pygame.transform.smoothscale(balance_text, (bw, bh))
    screen.blit(balance_text, (left_box.x + 14, left_box.y + 26))

    bet_color = COLOR_WIN if state.bet_feedback_ms > 0 else COLOR_TEXT
    session_net = state.session_profit
    net_color = COLOR_WIN if session_net >= 0 else COLOR_LOSS
    net_sign = "+" if session_net >= 0 else "-"
    net_text = font_small.render(
        f"NET  {net_sign}${abs(session_net):.2f}",
        True,
        net_color,
    )
    screen.blit(net_text, (left_box.x + 14, left_box.y + 76))

    if state.session_spins:
        session_text = font_small.render(
            f"{state.session_spins:,} SPINS   ·   RTP {state.session_rtp:.1%}",
            True,
            (194, 164, 112),
        )
    else:
        session_text = font_small.render("SESSION   ·   0 SPINS", True, (194, 164, 112))
    screen.blit(session_text, (left_box.x + 14, left_box.y + 98))

    chip_font = _get_font(13, bold=True)
    chips = (
        (f"{state.speed_mode.upper()} SPEED", (74, 51, 24), (234, 195, 113)),
        (
            f"AUTO {'ON' if state.auto_spin_enabled else 'OFF'}",
            (39, 43, 29) if state.auto_spin_enabled else (48, 34, 23),
            (204, 219, 148) if state.auto_spin_enabled else (191, 157, 105),
        ),
    )
    chip_gap = 10
    chip_widths = [chip_font.size(label)[0] + 24 for label, _, _ in chips]
    chip_x = center_box.centerx - (sum(chip_widths) + chip_gap) // 2
    for (label, fill, text_color), chip_width in zip(chips, chip_widths):
        chip_rect = pygame.Rect(chip_x, panel_y + 18, chip_width, 24)
        pygame.draw.rect(screen, fill, chip_rect, border_radius=12)
        pygame.draw.rect(screen, (119, 89, 49), chip_rect, width=1, border_radius=12)
        chip_text = chip_font.render(label, True, text_color)
        screen.blit(chip_text, chip_text.get_rect(center=chip_rect.center))
        chip_x = chip_rect.right + chip_gap

    # Bonus badge during long bonus-resolution sequences
    is_bonus_active = bool(
        state.is_spinning
        and state.current_result
        and state.current_result.get("is_bonus")
    )
    if is_bonus_active:
        badge_w, badge_h = 210, 40
        bx = GRID_X + GRID_COLS * CELL_SIZE - badge_w
        by = GRID_Y - 48

        badge = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
        pulse = 0.85 + 0.15 * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.013))
        badge.fill((50, 34, 12, int(210 * pulse)))
        screen.blit(badge, (bx, by))
        pygame.draw.rect(screen, COLOR_WIN, (bx, by, badge_w, badge_h), width=2)

        badge_text = font_ui.render("BONUS ACTIVE", True, COLOR_WIN)
        screen.blit(badge_text, (bx + 18, by + 10))

    bet_label = font_small.render("BET PER SPIN", True, (194, 164, 112))
    screen.blit(bet_label, bet_label.get_rect(center=(right_box.centerx, right_box.y + 17)))
    bet_text = font_mid.render(f"${state.bet:.2f}", True, bet_color)
    screen.blit(bet_text, bet_text.get_rect(center=(right_box.centerx, right_box.y + 48)))

    # ── Spin Button ──────────────────────────────────────────────
    draw_button(
        screen,
        SPIN_BUTTON_X,
        SPIN_BUTTON_Y,
        SPIN_BUTTON_WIDTH,
        SPIN_BUTTON_HEIGHT,
        "SPIN",
        font_spin,
        mouse_pos,
        is_disabled=state.is_spinning or state.balance < state.bet,
        is_pressed=state.pressed_button == "spin",
    )

    # ── Bet Adjustment Buttons ───────────────────────────────────
    draw_button(
        screen,
        BET_MINUS_X,
        BET_MINUS_Y,
        BET_BUTTON_WIDTH,
        BET_BUTTON_HEIGHT,
        "−",
        font_ui,
        mouse_pos,
        is_disabled=state.is_spinning,
        is_pressed=state.pressed_button == "bet_minus",
    )

    draw_button(
        screen,
        BET_PLUS_X,
        BET_PLUS_Y,
        BET_BUTTON_WIDTH,
        BET_BUTTON_HEIGHT,
        "+",
        font_ui,
        mouse_pos,
        is_disabled=state.is_spinning,
        is_pressed=state.pressed_button == "bet_plus",
    )

    increment_hint = _get_font(12).render("ADJUST BY $0.10", True, (161, 133, 92))
    screen.blit(
        increment_hint,
        increment_hint.get_rect(center=(right_box.centerx, right_box.bottom - 10)),
    )

    spin_hint = _get_font(12).render("SPACE TO SPIN", True, (161, 133, 92))
    screen.blit(
        spin_hint,
        spin_hint.get_rect(center=(center_box.centerx, center_box.bottom - 10)),
    )


def draw_button(
    screen: pygame.Surface,
    x: int,
    y: int,
    width: int,
    height: int,
    label: str,
    font: pygame.font.Font,
    mouse_pos: tuple[int, int],
    is_disabled: bool = False,
    is_pressed: bool = False,
) -> pygame.Rect:
    """
    Draw a simple button with hover effect.

    Returns the button rect for click detection.
    """
    rect = pygame.Rect(x, y, width, height)
    is_hovered = rect.collidepoint(mouse_pos)

    # Button color
    if is_disabled:
        color = (0x50, 0x50, 0x50)
    elif is_pressed:
        color = COLOR_BUTTON_PRESS
    elif is_hovered:
        color = COLOR_BUTTON_HOVER
    else:
        color = COLOR_BUTTON_NORMAL

    # Visual scale for interactivity while keeping click area stable.
    scale = 1.0
    if not is_disabled and is_hovered:
        scale = 1.03
    if is_pressed:
        scale = 0.97
    draw_w = max(1, int(width * scale))
    draw_h = max(1, int(height * scale))
    draw_rect = pygame.Rect(0, 0, draw_w, draw_h)
    draw_rect.center = rect.center

    if label == "SPIN" and not is_disabled:
        glow = pygame.Surface((draw_w + 26, draw_h + 26), pygame.SRCALPHA)
        glow_alpha = 80 if is_hovered else 58
        pygame.draw.rect(glow, (255, 215, 72, glow_alpha), (0, 0, draw_w + 26, draw_h + 26), border_radius=20)
        screen.blit(glow, (draw_rect.x - 13, draw_rect.y - 13))

    if label == "SPIN":
        top = (91, 61, 28) if is_disabled else (231, 183, 87)
        bottom = (55, 37, 21) if is_disabled else (137, 91, 36)
        gradient = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
        for i in range(draw_rect.height):
            t = i / max(1, draw_rect.height - 1)
            row_color = tuple(
                int(top[channel] * (1 - t) + bottom[channel] * t)
                for channel in range(3)
            )
            pygame.draw.line(gradient, row_color, (0, i), (draw_rect.width - 1, i))
        mask = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=14)
        gradient.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(gradient, draw_rect)
        border_color = (130, 102, 61) if is_disabled else (255, 220, 133)
        pygame.draw.rect(screen, border_color, draw_rect, width=2, border_radius=14)
    else:
        button_color = (61, 45, 28) if is_disabled else color
        border_color = (112, 88, 55) if is_disabled else (224, 185, 107)
        pygame.draw.rect(screen, button_color, draw_rect, border_radius=12)
        pygame.draw.rect(screen, border_color, draw_rect, width=2, border_radius=12)

    # Label text
    label_color = (168, 146, 111) if is_disabled else (255, 232, 179)
    text_surface = font.render(label, True, label_color)
    text_rect = text_surface.get_rect(center=draw_rect.center)
    screen.blit(text_surface, text_rect)

    return rect


def draw_debug_overlay(
    screen: pygame.Surface,
    state: GameState,
    font_debug: pygame.font.Font,
) -> None:
    """
    Draw debug information overlay (if enabled).

    Shows win amounts, multipliers, and step information.
    """
    if not state.debug_enabled:
        return

    lines = [
        "=== DEBUG MODE ===",
        f"Is spinning: {state.is_spinning}",
        f"Speed mode: {state.speed_mode}",
    ]

    if state.current_result:
        result = state.current_result
        lines.append(f"Total win: ${result['total_win']:.2f}")
        lines.append(f"Is bonus: {result['is_bonus']}")
        lines.append(f"Bonus spins: {result['bonus_spins_played']}")
        lines.append(f"Cascade steps: {len(result['steps'])}")

        if result['steps']:
            first_step = result['steps'][0]
            lines.append(f"First step win: ${first_step['win_amount']:.2f}")
            lines.append(f"First step multiplier: ×{first_step['multiplier']}")

    lines.extend([
        f"Session spins: {state.session_spins}",
        f"Session RTP: {state.session_rtp:.1%}",
        f"Loss streak: {state.consecutive_losses}",
    ])

    y_offset = 108
    for i, line in enumerate(lines):
        text = font_debug.render(line, True, COLOR_WIN)
        screen.blit(text, (WINDOW_WIDTH - 260, y_offset + i * 16))


def draw_bonus_overlay(
    screen: pygame.Surface,
    state: GameState,
    font_ui: pygame.font.Font,
) -> None:
    """Draw temporary bonus round banner after a bonus spin resolves."""
    if state.bonus_overlay_ms <= 0:
        return

    total = max(1.0, state.bonus_overlay_total_ms)
    elapsed = total - state.bonus_overlay_ms

    # Entrance slide (top -> resting position)
    enter_t = min(1.0, elapsed / max(1.0, BONUS_OVERLAY_SLIDE_MS))
    start_y = -60
    end_y = 54
    center_y = int(start_y + (end_y - start_y) * enter_t)

    # Fade-out near the end
    alpha = 220
    if state.bonus_overlay_ms < BONUS_OVERLAY_FADE_MS:
        alpha = int(220 * (state.bonus_overlay_ms / BONUS_OVERLAY_FADE_MS))

    panel = pygame.Surface((520, 90), pygame.SRCALPHA)
    panel.fill((10, 10, 10, max(0, alpha - 45)))
    rect = panel.get_rect(center=(WINDOW_WIDTH // 2, center_y))
    screen.blit(panel, rect)
    border_color = (*COLOR_WIN, alpha)
    pygame.draw.rect(screen, border_color, rect, width=2)

    line1 = font_ui.render(
        f"FREE SPINS PLAYED: {state.bonus_last_spins_played}",
        True,
        COLOR_WIN,
    )
    line2 = font_ui.render(
        f"BONUS MULTIPLIER ENDED AT x{state.bonus_last_final_multiplier}",
        True,
        COLOR_TEXT,
    )
    line1.set_alpha(alpha)
    line2.set_alpha(alpha)
    screen.blit(line1, (rect.x + 18, rect.y + 14))
    screen.blit(line2, (rect.x + 18, rect.y + 48))


def draw_bonus_trigger_overlay(
    screen: pygame.Surface,
    state: GameState,
) -> None:
    """Draw a short celebratory popup when bonus free spins are awarded."""
    if state.bonus_trigger_popup_ms <= 0:
        return

    total = max(1.0, state.bonus_trigger_popup_total_ms)
    progress = 1.0 - (state.bonus_trigger_popup_ms / total)
    ticks = pygame.time.get_ticks()

    # Fast punch-in then settle, with soft fade at end.
    pop = min(1.0, progress / 0.22)
    scale = 0.82 + 0.28 * pop
    if state.bonus_trigger_popup_ms < 340.0:
        scale *= 0.95 + 0.05 * (state.bonus_trigger_popup_ms / 340.0)

    alpha = 230
    if state.bonus_trigger_popup_ms < 420.0:
        alpha = int(230 * (state.bonus_trigger_popup_ms / 420.0))

    pulse = 0.5 + 0.5 * math.sin(ticks * 0.02)
    glow_r = int(112 + 36 * pulse)
    glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
    center = (glow_r, glow_r)
    pygame.draw.circle(glow, (255, 212, 78, min(140, alpha)), center, glow_r)
    pygame.draw.circle(glow, (255, 246, 182, min(120, alpha)), center, max(1, glow_r - 24))
    screen.blit(glow, (WINDOW_WIDTH // 2 - glow_r, 154 - glow_r))

    panel_w, panel_h = 640, 124
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((22, 12, 5, max(0, alpha - 38)))
    panel_rect = panel.get_rect(center=(WINDOW_WIDTH // 2, 156))
    screen.blit(panel, panel_rect)
    pygame.draw.rect(screen, (255, 221, 98, alpha), panel_rect, width=3)

    title_font = _get_font(42, bold=True)
    sub_font = _get_font(24, bold=True)

    title = title_font.render("10 BONUS SPINS ACQUIRED!", True, COLOR_WIN)
    tw = max(1, int(title.get_width() * scale))
    th = max(1, int(title.get_height() * scale))
    title = pygame.transform.smoothscale(title, (tw, th))
    title.set_alpha(alpha)
    title_rect = title.get_rect(center=(panel_rect.centerx, panel_rect.y + 48))
    screen.blit(title, title_rect)

    subtitle = sub_font.render("FREE SPINS MODE ACTIVATED", True, COLOR_TEXT)
    subtitle.set_alpha(alpha)
    subtitle_rect = subtitle.get_rect(center=(panel_rect.centerx, panel_rect.y + 92))
    screen.blit(subtitle, subtitle_rect)


def draw_big_win_confirm_overlay(
    screen: pygame.Surface,
    state: GameState,
) -> None:
    """Blocking modal shown for >=5x wins until player confirms."""
    if not state.big_win_confirm_required:
        return

    veil = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    veil.fill((8, 6, 4, 170))
    screen.blit(veil, (0, 0))

    panel_w = 560
    panel_h = 180
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((20, 12, 7, 238))
    rect = panel.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
    screen.blit(panel, rect)
    pygame.draw.rect(screen, COLOR_WIN, rect, width=3)

    title_font = _get_font(48, bold=True)
    body_font = _get_font(24, bold=True)

    pulse = 1.0 + 0.06 * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.015))
    title = title_font.render("BIG WIN!", True, COLOR_WIN)
    tw = max(1, int(title.get_width() * pulse))
    th = max(1, int(title.get_height() * pulse))
    title = pygame.transform.smoothscale(title, (tw, th))
    trect = title.get_rect(center=(rect.centerx, rect.y + 52))
    screen.blit(title, trect)

    amount = body_font.render(
        f"${state.big_win_confirm_amount:.2f}  ({state.big_win_confirm_multiplier:.2f}x)",
        True,
        COLOR_TEXT,
    )
    arect = amount.get_rect(center=(rect.centerx, rect.y + 102))
    screen.blit(amount, arect)

    prompt = body_font.render("Click or press SPACE to confirm", True, COLOR_TEXT)
    prect = prompt.get_rect(center=(rect.centerx, rect.y + 145))
    screen.blit(prompt, prect)
