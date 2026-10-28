from __future__ import annotations

import math

import pygame
from typing import TYPE_CHECKING

from pygame_config import (
    COLOR_BG,
    COLOR_TEXT,
    COLOR_WIN,
    FONT_NAME_DEBUG,
    FONT_NAME_TITLE,
    FONT_NAME_UI,
    FONT_SIZE_DEBUG,
    FONT_SIZE_UI,
    GRID_X,
    GRID_Y,
    GRID_COLS,
    GRID_ROWS,
    CELL_SIZE,
)
from rendering.grid_renderer import draw_grid, draw_grid_outline
from rendering.ui_renderer import (
    draw_big_win_confirm_overlay,
    draw_bonus_overlay,
    draw_bonus_trigger_overlay,
    draw_debug_overlay,
    draw_ui,
)

if TYPE_CHECKING:
    from game.state import GameState


class Renderer:
    """
    Main rendering pipeline.

    Orchestrates all draw calls: grid, UI, overlays, effects.
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_ui = pygame.font.SysFont(FONT_NAME_UI, FONT_SIZE_UI, bold=True)
        self.font_debug = pygame.font.SysFont(FONT_NAME_DEBUG, FONT_SIZE_DEBUG)
        self.font_emoji = pygame.font.Font(None, 56)  # Large size for emoji
        self.font_multiplier = pygame.font.SysFont(FONT_NAME_TITLE, 72, bold=True)
        self.font_title = pygame.font.SysFont(FONT_NAME_TITLE, 32, bold=True)

    def _draw_atmosphere(self) -> None:
        """Draw layered background for a stronger Egyptian-casino mood."""
        # Vertical gradient backdrop.
        for y in range(0, GRID_Y + GRID_ROWS * CELL_SIZE + 160, 4):
            t = min(1.0, y / float(GRID_Y + GRID_ROWS * CELL_SIZE + 160))
            r = int(22 + 18 * t)
            g = int(12 + 7 * (1.0 - t))
            b = int(8 + 5 * (1.0 - t))
            pygame.draw.rect(self.screen, (r, g, b), (0, y, GRID_X * 2 + GRID_COLS * CELL_SIZE, 4))

        # Side vignette to lift contrast around the reel well.
        for i in range(140):
            alpha = max(0, 160 - i)
            shade = pygame.Surface((1, self.screen.get_height()), pygame.SRCALPHA)
            shade.fill((8, 5, 3, alpha))
            self.screen.blit(shade, (i, 0))
            self.screen.blit(shade, (self.screen.get_width() - 1 - i, 0))

        # Subtle moving glints.
        ticks = pygame.time.get_ticks() * 0.001
        for i in range(8):
            x = int(80 + i * 120 + 18 * math.sin(ticks * 0.7 + i))
            y = int(70 + 25 * math.sin(ticks * 1.3 + i * 0.8))
            alpha = int(70 + 45 * (0.5 + 0.5 * math.sin(ticks * 2.1 + i)))
            dot = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(dot, (255, 225, 130, alpha), (4, 4), 3)
            self.screen.blit(dot, (x, y))

        # Temple cap above the grid (kept high to preserve title breathing room).
        frame_x = GRID_X - 8
        frame_y = GRID_Y - 10
        frame_w = GRID_COLS * CELL_SIZE + 16
        cap_y = 2
        cap_h = 40
        pygame.draw.rect(self.screen, (72, 46, 24), (frame_x, cap_y, frame_w, cap_h))
        pygame.draw.rect(self.screen, (194, 151, 74), (frame_x, cap_y, frame_w, cap_h), width=2)
        pygame.draw.line(self.screen, (232, 193, 104), (frame_x + 4, cap_y + 4), (frame_x + frame_w - 5, cap_y + 4), 1)
        pygame.draw.line(self.screen, (32, 20, 12), (frame_x + 4, cap_y + cap_h - 4), (frame_x + frame_w - 5, cap_y + cap_h - 4), 1)

        title = self.font_title.render("TEMPLE OF FORTUNE", True, (235, 196, 98))
        title_rect = title.get_rect(center=(GRID_X + (GRID_COLS * CELL_SIZE) // 2, 22))
        self.screen.blit(title, title_rect)

    def render(self, state: "GameState", mouse_pos: tuple[int, int]) -> None:
        """
        Draw a complete frame.

        Parameters
        ----------
        state : GameState
            Current game state.
        mouse_pos : tuple[int, int]
            Current mouse position (for button hover effects).
        """
        # Clear screen
        self.screen.fill(COLOR_BG)
        self._draw_atmosphere()

        # Draw grid from animation layer if active, else from last spin result.
        if state.anim_grid is not None:
            final_grid = state.anim_grid
            highlight_pos = state.anim_highlight_positions
            hidden_positions = state.anim_hidden_positions
            cell_offsets = state.anim_cell_offsets
            cell_scales = state.anim_cell_scales
            new_positions = state.anim_new_positions
        elif state.current_result and state.current_result["steps"]:
            final_grid = state.current_result.get("final_grid") or state.current_result["steps"][-1]["grid"]
            highlight_pos = set()
            hidden_positions = set()
            cell_offsets = {}
            cell_scales = {}
            new_positions = set()
        elif state.current_result and state.current_result.get("final_grid"):
            final_grid = state.current_result["final_grid"]
            highlight_pos = set()
            hidden_positions = set()
            cell_offsets = {}
            cell_scales = {}
            new_positions = set()
        else:
            # Placeholder empty grid(not used in Phase 1, just for reference)
            final_grid = [["E"] * 6 for _ in range(5)]
            highlight_pos = set()
            hidden_positions = set()
            cell_offsets = {}
            cell_scales = {}
            new_positions = set()

        draw_grid_outline(self.screen)
        draw_grid(
            self.screen,
            final_grid,
            self.font_emoji,
            highlight_positions=highlight_pos,
            hidden_positions=hidden_positions,
            cell_offsets=cell_offsets,
            cell_scales=cell_scales,
            new_positions=new_positions,
        )

        # Multiplier popup during cascade steps
        if state.anim_multiplier_value and state.anim_multiplier_progress > 0.0:
            text = f"x{state.anim_multiplier_value}"
            surf = self.font_multiplier.render(text, True, COLOR_WIN)
            scale = 1.4 - 0.4 * state.anim_multiplier_progress
            w = max(1, int(surf.get_width() * scale))
            h = max(1, int(surf.get_height() * scale))
            surf = pygame.transform.smoothscale(surf, (w, h))

            center_x = GRID_X + (GRID_COLS * CELL_SIZE) // 2
            center_y = GRID_Y + (GRID_ROWS * CELL_SIZE) // 2
            panel = pygame.Surface((max(220, w + 56), max(120, h + 34)), pygame.SRCALPHA)
            panel.fill((14, 10, 6, 186))
            panel_rect = panel.get_rect(center=(center_x, center_y))
            self.screen.blit(panel, panel_rect)
            pygame.draw.rect(self.screen, COLOR_TEXT, panel_rect, width=2)

            shadow = surf.copy()
            shadow.fill((20, 12, 5), special_flags=pygame.BLEND_RGB_MULT)
            shadow_rect = shadow.get_rect(center=(center_x + 3, center_y + 3))
            self.screen.blit(shadow, shadow_rect)

            rect = surf.get_rect(center=(center_x, center_y))
            self.screen.blit(surf, rect)

        # Draw UI
        draw_ui(self.screen, state, self.font_ui, mouse_pos)
        draw_bonus_trigger_overlay(self.screen, state)
        draw_bonus_overlay(self.screen, state, self.font_ui)
        draw_big_win_confirm_overlay(self.screen, state)

        # Draw debug overlay (if enabled)
        draw_debug_overlay(self.screen, state, self.font_debug)

        # Flip display
        pygame.display.flip()
