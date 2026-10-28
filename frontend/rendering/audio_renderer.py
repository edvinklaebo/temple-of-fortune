from __future__ import annotations

from pathlib import Path

import pygame

from pygame_config import SOUND_FILES

# ─────────────────────────────────────────────────────────────────
# Audio Renderer (Phase 1: stubs, Phase 5: real audio)
# ─────────────────────────────────────────────────────────────────

class AudioRenderer:
    """
    Manages sound playback.

    Phase 1: Print stubs only.
    Phase 5: Load actual WAV files and play them.
    """

    def __init__(self, enabled: bool = True, volume: float = 0.7):
        self.enabled = enabled
        self.volume = volume
        self.mixer_init = False
        self._sound_cache: dict[str, pygame.mixer.Sound] = {}
        self._missing_sounds: set[str] = set()
        self._sound_volume_scale: dict[str, float] = {
            "ui_click": 0.38,
            "spin_start": 0.78,
            "cascade_pop": 0.72,
            "win_chime": 0.82,
            "bonus_trigger": 1.0,
            "big_win": 1.0,
        }

        base_dir = Path(__file__).resolve().parent.parent
        self._sound_paths = {
            name: base_dir / rel_path for name, rel_path in SOUND_FILES.items()
        }

        if enabled:
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                self.mixer_init = True
            except Exception as e:
                print(f"[Audio] Mixer init failed: {e}")

    def play_sound(self, sound_name: str) -> None:
        """
        Play a named sound effect.

        Parameters
        ----------
        sound_name : str
            Sound identifier: "spin_start", "cascade_pop", "win_chime", "big_win"
        """
        if not self.enabled or not self.mixer_init:
            return

        if sound_name.startswith("win_chime_x"):
            self._play_multiplier_chime(sound_name)
            return

        if sound_name == "bonus_trigger":
            # Prefer dedicated bonus trigger sound; fallback to layered celebratory stack.
            if not self._play_loaded_sound("bonus_trigger", extra_scale=1.0):
                self._play_loaded_sound("big_win", extra_scale=0.9)
                self._play_loaded_sound("win_chime", extra_scale=0.75)
            return

        self._play_loaded_sound(sound_name)

    def _play_multiplier_chime(self, sound_name: str) -> None:
        """Play progressively stronger win cue as cascade multiplier increases."""
        try:
            multiplier = int(sound_name.split("_x", 1)[1])
        except (ValueError, IndexError):
            multiplier = 1

        base_boost = min(1.35, 0.9 + 0.12 * max(0, multiplier - 1))
        self._play_loaded_sound("win_chime", extra_scale=base_boost)

        if multiplier >= 3:
            low_layer = min(0.95, 0.28 + 0.12 * (multiplier - 3))
            self._play_loaded_sound("cascade_pop", extra_scale=low_layer)

    def _play_loaded_sound(self, sound_name: str, extra_scale: float = 1.0) -> bool:
        """Load and play one sound; returns True if successfully played."""
        sound = self._load_sound(sound_name)
        if sound is None:
            return False

        sound_scale = self._sound_volume_scale.get(sound_name, 1.0) * extra_scale
        sound.set_volume(max(0.0, min(1.0, self.volume * sound_scale)))
        sound.play()
        return True

    def _load_sound(self, sound_name: str) -> pygame.mixer.Sound | None:
        """Load and cache WAV sound effects on first use."""
        cached = self._sound_cache.get(sound_name)
        if cached is not None:
            return cached

        sound_path = self._sound_paths.get(sound_name)
        if sound_path is None:
            return None

        if not sound_path.exists():
            if sound_name not in self._missing_sounds:
                self._missing_sounds.add(sound_name)
                print(f"[Audio] Missing sound file: {sound_path}")
            return None

        try:
            sound = pygame.mixer.Sound(str(sound_path))
            self._sound_cache[sound_name] = sound
            return sound
        except Exception as exc:
            if sound_name not in self._missing_sounds:
                self._missing_sounds.add(sound_name)
                print(f"[Audio] Failed to load sound '{sound_name}': {exc}")
            return None

    def set_volume(self, volume: float) -> None:
        """Set master volume (0.0–1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        if self.mixer_init:
            try:
                pygame.mixer.music.set_volume(self.volume)
            except Exception:
                pass
