#!/usr/bin/env python3
"""
Mahjong Riichi - Sound Manager
Handles all sound effects for the game
"""

import os
import pygame
from typing import Optional


class SoundManager:
    """
    Manages sound effects for Mahjong game
    """

    def __init__(self, volume: float = 0.7, enabled: bool = True):
        self.volume = volume
        self.enabled = enabled
        self.sounds: dict = {}
        self.music_volume = 0.3
        self._initialized = False

        # Try to initialize pygame mixer
        self._init_sound()

    def _init_sound(self) -> bool:
        """Initialize sound system"""
        try:
            if not pygame.get_init():
                pygame.init()
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self._initialized = True
            return True
        except Exception as e:
            print(f"Sound initialization failed: {e}")
            self._initialized = False
            return False

    def _get_sound_path(self, sound_name: str) -> str:
        """Get path to sound file"""
        # Try multiple locations
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        possible_paths = [
            os.path.join(base_dir, 'assets', 'sounds', f'{sound_name}.wav'),
            os.path.join(base_dir, 'assets', 'sounds', f'{sound_name}.mp3'),
            os.path.join(base_dir, 'sounds', f'{sound_name}.wav'),
            os.path.join(base_dir, 'sounds', f'{sound_name}.mp3'),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path
        return possible_paths[0]  # Return first path for error message

    def load_sound(self, name: str) -> Optional[pygame.mixer.Sound]:
        """Load a sound file"""
        if not self._initialized:
            return None

        if name in self.sounds:
            return self.sounds[name]

        path = self._get_sound_path(name)
        try:
            sound = pygame.mixer.Sound(path)
            sound.set_volume(self.volume)
            self.sounds[name] = sound
            return sound
        except Exception as e:
            # Sound file not found, but don't error
            return None

    def play(self, sound_name: str) -> None:
        """Play a sound by name"""
        if not self.enabled or not self._initialized:
            return

        sound = self.load_sound(sound_name)
        if sound:
            try:
                sound.play()
            except Exception:
                pass

    def play_tile_draw(self) -> None:
        """Play tile draw sound"""
        self.play('tile_draw')

    def play_discard(self) -> None:
        """Play tile discard sound"""
        self.play('tile_discard')

    def play_pon(self) -> None:
        """Play pon call sound"""
        self.play('pon')

    def play_chi(self) -> None:
        """Play chi call sound"""
        self.play('chi')

    def play_kan(self) -> None:
        """Play kan call sound"""
        self.play('kan')

    def play_ron(self) -> None:
        """Play ron win sound"""
        self.play('ron')

    def play_tsumo(self) -> None:
        """Play tsumo win sound"""
        self.play('tsumo')

    def play_riichi(self) -> None:
        """Play riichi declaration sound"""
        self.play('riichi')

    def play_dora(self) -> None:
        """Play dora reveal sound"""
        self.play('dora')

    def play_button_click(self) -> None:
        """Play button click sound"""
        self.play('click')

    def play_call(self, call_type: str) -> None:
        """Play call sound (pon/chi/kan)"""
        if call_type == 'pon':
            self.play_pon()
        elif call_type == 'chi':
            self.play_chi()
        elif call_type == 'kan':
            self.play_kan()

    def play_win(self, is_tsumo: bool) -> None:
        """Play win sound"""
        if is_tsumo:
            self.play_tsumo()
        else:
            self.play_ron()

    def set_volume(self, volume: float) -> None:
        """Set master volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.volume)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable sounds"""
        self.enabled = enabled

    def is_enabled(self) -> bool:
        """Check if sounds are enabled"""
        return self.enabled

    def toggle(self) -> bool:
        """Toggle sound on/off, returns new state"""
        self.enabled = not self.enabled
        return self.enabled

    def generate_beep(self, freq: int = 440, duration: int = 100) -> None:
        """Generate a simple beep sound programmatically"""
        if not self._initialized:
            return

        try:
            import numpy as np

            # Generate beep using numpy
            sample_rate = 22050
            samples = int(sample_rate * duration / 1000)

            # Generate sine wave
            t = np.linspace(0, duration / 1000, samples, False)
            wave = np.sin(2 * np.pi * freq * t)

            # Apply envelope
            envelope = np.ones(samples)
            attack = int(samples * 0.01)
            release = int(samples * 0.1)
            envelope[:attack] = np.linspace(0, 1, attack)
            envelope[-release:] = np.linspace(1, 0, release)
            wave *= envelope

            # Convert to 16-bit integers
            wave = (wave * 32767 * 0.3).astype(np.int16)

            # Create stereo
            stereo = np.column_stack((wave, wave))

            # Create sound and play
            sound = pygame.mixer.Sound(stereo)
            sound.set_volume(self.volume * 0.5)
            sound.play()
        except ImportError:
            # NumPy not available, use simple click sound
            pass


def create_default_sounds(base_dir: str) -> None:
    """
    Create placeholder directories for sounds
    Call this during first setup
    """
    sound_dir = os.path.join(base_dir, 'assets', 'sounds')
    os.makedirs(sound_dir, exist_ok=True)

    # Create a README explaining sound requirements
    readme = """# Mahjong Sound Effects

Place sound files here (.wav or .mp3 format).

Required sound files:
- tile_draw.wav - Drawing a tile from the wall
- tile_discard.wav - Discarding a tile
- pon.wav - Pon call
- chi.wav - Chi call
- kan.wav - Kan call
- ron.wav - Ron win
- tsumo.wav - Tsumo win
- riichi.wav - Riichi declaration
- dora.wav - Dora reveal
- click.wav - Button click

Sounds are optional - game works without them.
"""
    readme_path = os.path.join(sound_dir, 'README.txt')
    if not os.path.exists(readme_path):
        with open(readme_path, 'w') as f:
            f.write(readme)


# Demo function
if __name__ == "__main__":
    print("Sound Manager Demo")
    print("-" * 40)

    sm = SoundManager(volume=0.7)

    if sm._initialized:
        print("Sound system initialized successfully")
        print("Available methods:")
        print("  - play_tile_draw()")
        print("  - play_discard()")
        print("  - play_pon() / play_chi() / play_kan()")
        print("  - play_ron() / play_tsumo()")
        print("  - play_riichi()")
        print("  - play_dora()")
        print("  - set_volume(0.0-1.0)")
        print("  - toggle()")
    else:
        print("Sound system not available (pygame.mixer failed to initialize)")
        print("Game will run without sounds.")

    # Create default sound directories
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    create_default_sounds(base_dir)
    print(f"\nSound directory created at: {os.path.join(base_dir, 'assets', 'sounds')}")
