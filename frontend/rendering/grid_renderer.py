from __future__ import annotations

import math
from pathlib import Path

import pygame

from pygame_config import (
    CELL_SIZE,
    COLOR_CELL_BORDER,
    COLOR_CELL_BG,
    COLOR_GRID_BG,
    GRID_COLS,
    GRID_ROWS,
    GRID_X,
    GRID_Y,
    COLOR_WIN,
    COLOR_TEXT,
)


SYMBOL_COLORS = {
    "A": (220, 70, 70),      # Ruby red
    "B": (75, 170, 210),     # Cyan blue
    "C": (192, 150, 90),     # Clay gold
    "D": (245, 210, 70),     # Crown gold
    "E": (95, 200, 120),     # Coin green
    "SCATTER": (170, 110, 220),  # Crystal violet
}

SYMBOL_OUTLINE = (30, 22, 14)
SYMBOL_RARITY = {
    "A": "common",
    "B": "rare",
    "C": "common",
    "D": "rare",
    "E": "epic",
    "SCATTER": "epic",
}
_SPRITE_CACHE: dict[str, pygame.Surface | None] = {}


def _get_symbol_sprite(symbol: str) -> pygame.Surface | None:
    """Load and cache a sprite named after the symbol key (e.g., A.jpeg)."""
    if symbol in _SPRITE_CACHE:
        return _SPRITE_CACHE[symbol]

    sprites_dir = Path(__file__).resolve().parents[1] / "assets" / "sprites"
    candidates = [
        sprites_dir / f"{symbol}.png",
        sprites_dir / f"{symbol}.jpg",
        sprites_dir / f"{symbol}.jpeg",
        sprites_dir / f"{symbol}.webp",
    ]

    for candidate in candidates:
        if candidate.exists():
            try:
                surface = pygame.image.load(str(candidate)).convert_alpha()
            except pygame.error:
                surface = None
            _SPRITE_CACHE[symbol] = surface
            return surface

    _SPRITE_CACHE[symbol] = None
    return None


def _draw_symbol_icon(
    screen: pygame.Surface,
    symbol: str,
    center: tuple[int, int],
    radius: int,
    is_highlighted: bool = False,
    is_new: bool = False,
) -> None:
    """Draw symbol sprite if available, otherwise fallback to shape-based icon."""
    cx, cy = center
    color = SYMBOL_COLORS.get(symbol, COLOR_TEXT)
    rarity = SYMBOL_RARITY.get(symbol, "common")
    ticks = pygame.time.get_ticks()

    if rarity in ("rare", "epic"):
        pulse = 0.5 + 0.5 * math.sin(ticks * (0.009 if rarity == "rare" else 0.015))
        aura = radius + (10 if rarity == "rare" else 14)
        aura += int((4 if rarity == "rare" else 7) * pulse)
        aura_surface = pygame.Surface((aura * 2, aura * 2), pygame.SRCALPHA)
        aura_center = (aura, aura)
        alpha = 36 + int((28 if rarity == "rare" else 56) * pulse)
        aura_color = (106, 180, 255, alpha) if rarity == "rare" else (255, 220, 120, alpha)
        pygame.draw.circle(aura_surface, aura_color, aura_center, aura)
        screen.blit(aura_surface, (cx - aura, cy - aura))

    if symbol == "SCATTER":
        # Stronger animated aura to make free-spin triggers stand out.
        pulse = 0.5 + 0.5 * math.sin(ticks * 0.018)
        aura_scale = 1.0 + 0.16 * pulse
        aura_radius = int((radius + 16) * aura_scale)
        if is_highlighted or is_new:
            aura_radius += 8

        glow_surface = pygame.Surface((aura_radius * 2, aura_radius * 2), pygame.SRCALPHA)
        glow_center = (aura_radius, aura_radius)
        outer_alpha = 48 + int(54 * pulse)
        inner_alpha = 86 + int(74 * pulse)
        pygame.draw.circle(glow_surface, (180, 120, 255, outer_alpha), glow_center, aura_radius)
        pygame.draw.circle(glow_surface, (235, 220, 255, inner_alpha), glow_center, max(1, aura_radius - 8))
        screen.blit(glow_surface, (cx - aura_radius, cy - aura_radius))

        # Soft orbit ring for extra motion/readability.
        ring_color = (245, 232, 255, 150 + int(70 * pulse))
        pygame.draw.circle(screen, ring_color, (cx, cy), radius + 11, width=2)

    sprite = _get_symbol_sprite(symbol)
    if sprite is not None:
        sprite_size = max(24, radius * 2)
        if symbol == "SCATTER":
            sprite_size = int(sprite_size * (1.18 if (is_highlighted or is_new) else 1.10))

        scaled = pygame.transform.smoothscale(sprite, (sprite_size, sprite_size))
        rect = scaled.get_rect(center=(cx, cy))
        screen.blit(scaled, rect)
        return

    # Base medallion to make icon readable against both normal and highlighted cells.
    pygame.draw.circle(screen, (46, 32, 20), (cx, cy), radius + 8)
    pygame.draw.circle(screen, color, (cx, cy), radius + 4)
    pygame.draw.circle(screen, SYMBOL_OUTLINE, (cx, cy), radius + 4, width=2)

    if symbol == "A":
        # Diamond
        pts = [(cx, cy - radius), (cx + radius, cy), (cx, cy + radius), (cx - radius, cy)]
        pygame.draw.polygon(screen, (255, 240, 240), pts)
        pygame.draw.polygon(screen, SYMBOL_OUTLINE, pts, width=2)
    elif symbol == "B":
        # Eye + pupil
        eye_rect = pygame.Rect(cx - radius, cy - radius // 2, radius * 2, radius)
        pygame.draw.ellipse(screen, (235, 245, 255), eye_rect)
        pygame.draw.ellipse(screen, SYMBOL_OUTLINE, eye_rect, width=2)
        pygame.draw.circle(screen, (25, 45, 90), (cx, cy), radius // 3)
    elif symbol == "C":
        # Urn silhouette
        body = [
            (cx - radius // 2, cy - radius // 2),
            (cx + radius // 2, cy - radius // 2),
            (cx + radius - 2, cy + radius // 2),
            (cx - radius + 2, cy + radius // 2),
        ]
        pygame.draw.polygon(screen, (236, 216, 186), body)
        pygame.draw.polygon(screen, SYMBOL_OUTLINE, body, width=2)
        pygame.draw.rect(screen, (236, 216, 186), (cx - radius // 3, cy - radius, 2 * radius // 3, radius // 3))
        pygame.draw.rect(screen, SYMBOL_OUTLINE, (cx - radius // 3, cy - radius, 2 * radius // 3, radius // 3), width=2)
    elif symbol == "D":
        # Crown
        base_rect = pygame.Rect(cx - radius, cy + radius // 4, radius * 2, radius // 2)
        pygame.draw.rect(screen, (255, 242, 178), base_rect)
        pygame.draw.rect(screen, SYMBOL_OUTLINE, base_rect, width=2)
        crown_pts = [
            (cx - radius, cy + radius // 4),
            (cx - radius // 2, cy - radius),
            (cx, cy - radius // 3),
            (cx + radius // 2, cy - radius),
            (cx + radius, cy + radius // 4),
        ]
        pygame.draw.polygon(screen, (255, 242, 178), crown_pts)
        pygame.draw.polygon(screen, SYMBOL_OUTLINE, crown_pts, width=2)
    elif symbol == "E":
        # Coin with center dot
        pygame.draw.circle(screen, (250, 238, 150), (cx, cy), radius)
        pygame.draw.circle(screen, SYMBOL_OUTLINE, (cx, cy), radius, width=2)
        pygame.draw.circle(screen, (220, 180, 60), (cx, cy), max(3, radius // 4))
    elif symbol == "SCATTER":
        # Crystal
        sparkle = 0.82 + 0.18 * (0.5 + 0.5 * math.sin(ticks * 0.024))
        crystal_color = (
            min(255, int(237 * sparkle + 28)),
            min(255, int(227 * sparkle + 32)),
            255,
        )
        pts = [
            (cx, cy - radius),
            (cx + radius // 2, cy - radius // 3),
            (cx + radius // 3, cy + radius),
            (cx - radius // 3, cy + radius),
            (cx - radius // 2, cy - radius // 3),
        ]
        pygame.draw.polygon(screen, crystal_color, pts)
        pygame.draw.polygon(screen, SYMBOL_OUTLINE, pts, width=2)
        pygame.draw.circle(screen, (255, 250, 255), (cx, cy - radius // 3), max(2, radius // 5))
    else:
        pygame.draw.circle(screen, (245, 235, 210), (cx, cy), radius)
        pygame.draw.circle(screen, SYMBOL_OUTLINE, (cx, cy), radius, width=2)


def draw_grid(
    screen: pygame.Surface,
    grid: list[list[str]],
    font_emoji: pygame.font.Font,
    highlight_positions: set[tuple[int, int]] | None = None,
    hidden_positions: set[tuple[int, int]] | None = None,
    cell_offsets: dict[tuple[int, int], float] | None = None,
    cell_scales: dict[tuple[int, int], float] | None = None,
    new_positions: set[tuple[int, int]] | None = None,
) -> None:
    """
    Draw the 6×5 grid with symbols.

    Winning positions are highlighted with a bright border.

    Parameters
    ----------
    screen : pygame.Surface
        The display surface.
    grid : list[list[str]]
        The game grid (e.g., 5 rows × 6 columns).
    font_emoji : pygame.font.Font
        Font for rendering emoji symbols.
    highlight_positions : set[tuple[int, int]] or None
        Positions to highlight (row, col). Used for win visualization.
    """
    if highlight_positions is None:
        highlight_positions = set()
    if hidden_positions is None:
        hidden_positions = set()
    if cell_offsets is None:
        cell_offsets = {}
    if cell_scales is None:
        cell_scales = {}
    if new_positions is None:
        new_positions = set()

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x = GRID_X + col * CELL_SIZE
            y = GRID_Y + row * CELL_SIZE
            y_offset = int(cell_offsets.get((row, col), 0.0))

            # Cell background
            is_highlighted = (row, col) in highlight_positions
            is_new = (row, col) in new_positions
            bg_color = (90, 66, 28) if is_highlighted else COLOR_CELL_BG
            border_color = COLOR_WIN if is_highlighted or is_new else COLOR_CELL_BORDER

            if is_highlighted:
                glow = pygame.Surface((CELL_SIZE + 20, CELL_SIZE + 20), pygame.SRCALPHA)
                pygame.draw.rect(glow, (255, 215, 0, 84), (0, 0, CELL_SIZE + 20, CELL_SIZE + 20), border_radius=14)
                screen.blit(glow, (x - 10, y - 10 + y_offset))

            pygame.draw.rect(
                screen,
                bg_color,
                (x + 4, y + 4 + y_offset, CELL_SIZE - 8, CELL_SIZE - 8),
            )

            # Subtle bevel and inset shadow to avoid flat grid look.
            pygame.draw.line(
                screen,
                (176, 140, 86),
                (x + 6, y + 6 + y_offset),
                (x + CELL_SIZE - 8, y + 6 + y_offset),
                1,
            )
            pygame.draw.line(
                screen,
                (176, 140, 86),
                (x + 6, y + 6 + y_offset),
                (x + 6, y + CELL_SIZE - 8 + y_offset),
                1,
            )
            pygame.draw.line(
                screen,
                (26, 16, 10),
                (x + 6, y + CELL_SIZE - 8 + y_offset),
                (x + CELL_SIZE - 8, y + CELL_SIZE - 8 + y_offset),
                1,
            )
            pygame.draw.line(
                screen,
                (26, 16, 10),
                (x + CELL_SIZE - 8, y + 6 + y_offset),
                (x + CELL_SIZE - 8, y + CELL_SIZE - 8 + y_offset),
                1,
            )

            shadow = pygame.Surface((CELL_SIZE - 12, CELL_SIZE - 12), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 34))
            screen.blit(shadow, (x + 7, y + 8 + y_offset))

            pygame.draw.rect(
                screen,
                border_color,
                (x + 4, y + 4 + y_offset, CELL_SIZE - 8, CELL_SIZE - 8),
                width=3 if is_highlighted or is_new else 1,
            )

            if (row, col) in hidden_positions:
                continue

            # Symbol icon + short label for guaranteed readability.
            symbol = grid[row][col]
            center = (x + CELL_SIZE // 2, y + CELL_SIZE // 2 + y_offset)
            icon_radius = (CELL_SIZE - 8) // 2
            if symbol == "SCATTER":
                # Make free-spin symbol feel more important than regular pieces.
                icon_radius += 4 if (is_highlighted or is_new) else 2
            _draw_symbol_icon(
                screen,
                symbol,
                center,
                radius=icon_radius,
                is_highlighted=is_highlighted,
                is_new=is_new,
            )


def draw_grid_outline(screen: pygame.Surface) -> None:
    """Draw a decorative border around the entire grid."""
    x = GRID_X
    y = GRID_Y
    w = CELL_SIZE * GRID_COLS
    h = CELL_SIZE * GRID_ROWS

    frame_outer = pygame.Rect(x - 10, y - 10, w + 20, h + 20)
    frame_inner = pygame.Rect(x - 4, y - 4, w + 8, h + 8)

    pygame.draw.rect(screen, COLOR_GRID_BG, frame_outer)
    pygame.draw.rect(screen, (150, 116, 68), frame_outer, width=3)
    pygame.draw.rect(screen, (58, 36, 18), frame_inner, width=2)
    pygame.draw.rect(screen, COLOR_CELL_BORDER, (x - 2, y - 2, w + 4, h + 4), width=3)
