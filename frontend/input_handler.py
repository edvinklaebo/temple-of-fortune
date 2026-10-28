from __future__ import annotations

from dataclasses import dataclass

import pygame

from pygame_config import (
    BET_BUTTON_HEIGHT,
    BET_BUTTON_WIDTH,
    BET_MINUS_X,
    BET_MINUS_Y,
    BET_PLUS_X,
    BET_PLUS_Y,
    KEY_AUTO_SPIN,
    KEY_BET_DOWN,
    KEY_BET_UP,
    KEY_DEBUG_TOGGLE,
    KEY_MUTE,
    KEY_QUIT,
    KEY_SPEED_FAST,
    KEY_SPEED_NORMAL,
    KEY_SPEED_TURBO,
    KEY_SPIN,
    SPIN_BUTTON_HEIGHT,
    SPIN_BUTTON_WIDTH,
    SPIN_BUTTON_X,
    SPIN_BUTTON_Y,
)


@dataclass
class InputActions:
    quit_requested: bool = False
    spin: bool = False
    toggle_auto_spin: bool = False
    bet_up: bool = False
    bet_down: bool = False
    toggle_debug: bool = False
    speed_mode: str | None = None
    toggle_mute: bool = False
    click_spin: bool = False
    click_bet_minus: bool = False
    click_bet_plus: bool = False
    click_any: bool = False


class InputHandler:
    """Maps pygame events to normalized game actions."""

    def __init__(self) -> None:
        self.spin_button_rect = pygame.Rect(
            SPIN_BUTTON_X, SPIN_BUTTON_Y, SPIN_BUTTON_WIDTH, SPIN_BUTTON_HEIGHT
        )
        self.bet_minus_rect = pygame.Rect(
            BET_MINUS_X, BET_MINUS_Y, BET_BUTTON_WIDTH, BET_BUTTON_HEIGHT
        )
        self.bet_plus_rect = pygame.Rect(
            BET_PLUS_X, BET_PLUS_Y, BET_BUTTON_WIDTH, BET_BUTTON_HEIGHT
        )

    def gather(self) -> InputActions:
        actions = InputActions()
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                actions.quit_requested = True
                continue

            if event.type == pygame.KEYDOWN:
                key = event.key
                if key == KEY_QUIT:
                    actions.quit_requested = True
                elif key == KEY_SPIN:
                    actions.spin = True
                elif key == KEY_AUTO_SPIN:
                    actions.toggle_auto_spin = True
                elif key == KEY_BET_UP:
                    actions.bet_up = True
                elif key == KEY_BET_DOWN:
                    actions.bet_down = True
                elif key == KEY_DEBUG_TOGGLE:
                    actions.toggle_debug = True
                elif key == KEY_SPEED_NORMAL:
                    actions.speed_mode = "normal"
                elif key == KEY_SPEED_FAST:
                    actions.speed_mode = "fast"
                elif key == KEY_SPEED_TURBO:
                    actions.speed_mode = "turbo"
                elif key == KEY_MUTE:
                    actions.toggle_mute = True

            if event.type == pygame.MOUSEBUTTONDOWN:
                actions.click_any = True
                if self.spin_button_rect.collidepoint(mouse_pos):
                    actions.click_spin = True
                elif self.bet_minus_rect.collidepoint(mouse_pos):
                    actions.click_bet_minus = True
                elif self.bet_plus_rect.collidepoint(mouse_pos):
                    actions.click_bet_plus = True

        return actions
