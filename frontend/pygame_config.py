# pygame_config.py
# Configuration for visual settings, input mappings, and theme.

import pygame

# ─────────────────────────────────────────────────────────────────
# Window & Display
# ─────────────────────────────────────────────────────────────────

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
FPS = 60
TITLE = "Slot Simulator • Pygame"

# ─────────────────────────────────────────────────────────────────
# Grid Layout
# ─────────────────────────────────────────────────────────────────

GRID_ROWS = 5
GRID_COLS = 6
CELL_SIZE = 95  # pixels (includes padding)
SYMBOL_SIZE = 64  # emoji display size within cell

# Calculate grid position (centered)
GRID_WIDTH = GRID_COLS * CELL_SIZE
GRID_HEIGHT = GRID_ROWS * CELL_SIZE
GRID_X = (WINDOW_WIDTH - GRID_WIDTH) // 2
GRID_Y = 108  # top margin

# ─────────────────────────────────────────────────────────────────
# Colors (Dark gold + sand palette)
# ─────────────────────────────────────────────────────────────────

COLOR_BG = (0x1B, 0x10, 0x0A)  # Deep brown-black
COLOR_GRID_BG = (0x10, 0x08, 0x05)  # Near-black slot well
COLOR_CELL_BG = (0x2A, 0x1C, 0x11)  # Dark bronze tile base
COLOR_CELL_BORDER = (0xB5, 0x94, 0x5E)  # Warm gold-taupe
COLOR_TEXT = (0xD4, 0xAF, 0x37)  # Sand/gold
COLOR_WIN = (0xFF, 0xD7, 0x00)  # Bright gold
COLOR_LOSS = (0xCC, 0x4C, 0x4C)  # Muted red
COLOR_BUTTON_NORMAL = (0x55, 0x44, 0x33)  # Brown
COLOR_BUTTON_HOVER = (0x77, 0x66, 0x55)  # Lighter brown
COLOR_BUTTON_PRESS = (0x33, 0x22, 0x11)  # Darker brown

# ─────────────────────────────────────────────────────────────────
# Buttons
# ─────────────────────────────────────────────────────────────────

SPIN_BUTTON_WIDTH = 220
SPIN_BUTTON_HEIGHT = 56
SPIN_BUTTON_X = (WINDOW_WIDTH - SPIN_BUTTON_WIDTH) // 2
SPIN_BUTTON_Y = GRID_Y + GRID_HEIGHT + 66

BET_BUTTON_WIDTH = 46
BET_BUTTON_HEIGHT = 42
BET_MINUS_X = WINDOW_WIDTH - 210
BET_MINUS_Y = GRID_Y + GRID_HEIGHT + 90
BET_PLUS_X = BET_MINUS_X + BET_BUTTON_WIDTH + 16
BET_PLUS_Y = BET_MINUS_Y

# Bottom UI layout anchors
UI_PANEL_Y = GRID_Y + GRID_HEIGHT + 12
UI_PANEL_HEIGHT = 150
UI_LEFT_X = 26
UI_CENTER_X = WINDOW_WIDTH // 2
UI_RIGHT_X = WINDOW_WIDTH - 286

# ─────────────────────────────────────────────────────────────────
# Fonts
# ─────────────────────────────────────────────────────────────────

FONT_SIZE_TITLE = 32
FONT_SIZE_UI = 20
FONT_SIZE_DEBUG = 13
FONT_NAME_UI = "cambria"
FONT_NAME_DEBUG = "consolas"
FONT_NAME_TITLE = "timesnewroman"

# ─────────────────────────────────────────────────────────────────
# Symbol Emoji Mapping (Egyptian theme)
# ─────────────────────────────────────────────────────────────────

SYMBOL_EMOJI = {
    "A": "💍",  # Ruby
    "B": "🪬",  # Diamond
    "C": "⚱️",  # Amethyst
    "D": "👑",  # Emerald
    "E": "💰",  # Gold Coin
    "SCATTER": "🔮",  # Crystal
}

# ─────────────────────────────────────────────────────────────────
# Input Mappings
# ─────────────────────────────────────────────────────────────────

KEY_SPIN = pygame.K_SPACE
KEY_AUTO_SPIN = pygame.K_a
KEY_BET_UP = pygame.K_UP
KEY_BET_DOWN = pygame.K_DOWN
KEY_DEBUG_TOGGLE = pygame.K_d
KEY_SPEED_NORMAL = pygame.K_1
KEY_SPEED_FAST = pygame.K_2
KEY_SPEED_TURBO = pygame.K_3
KEY_MUTE = pygame.K_m
KEY_QUIT = pygame.K_ESCAPE

# ─────────────────────────────────────────────────────────────────
# Animation Timing (milliseconds, then scaled by speed modes)
# ─────────────────────────────────────────────────────────────────

ANIM_WIN_HIGHLIGHT = 300
ANIM_REMOVAL = 200
ANIM_FALL = 400
ANIM_REFILL = 300
ANIM_STEP_DELAY = 100

# Speed mode multipliers
SPEED_MODES = {
    "normal": 1.0,
    "fast": 0.6,
    "turbo": 0.3,
}

# ─────────────────────────────────────────────────────────────────
# Game Settings
# ─────────────────────────────────────────────────────────────────

STARTING_BALANCE = 1000.0
MIN_BET = 0.10
MAX_BET = 100.0
DEFAULT_BET = 1.0
BET_INCREMENT = 0.10

# ─────────────────────────────────────────────────────────────────
# Sound (stubs for Phase 1)
# ─────────────────────────────────────────────────────────────────

SOUNDS_ENABLED = True
SOUND_VOLUME = 0.7

# Sound files (placeholders—will be created in Phase 5)
SOUND_FILES = {
    "spin_start": "assets/sounds/spin_start.wav",
    "cascade_pop": "assets/sounds/cascade_pop.wav",
    "win_chime": "assets/sounds/win_chime.wav",
    "bonus_trigger": "assets/sounds/bonus_trigger.wav",
    "big_win": "assets/sounds/big_win.wav",
    "ui_click": "assets/sounds/ui_click.wav",
}

# ─────────────────────────────────────────────────────────────────
# Phase 4 UI polish constants
# ─────────────────────────────────────────────────────────────────

BONUS_OVERLAY_DURATION_MS = 2200.0
BONUS_OVERLAY_SLIDE_MS = 240.0
BONUS_OVERLAY_FADE_MS = 420.0
LOSS_STREAK_ALERT_THRESHOLD = 5
LOSS_STREAK_FLASH_MS = 700.0

# Require user confirmation before proceeding on wins at or above this multiple.
BIG_WIN_CONFIRM_MULTIPLIER = 5.0
