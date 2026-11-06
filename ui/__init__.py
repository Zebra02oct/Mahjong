"""
Mahjong Riichi - UI Module
User interface implementations
"""

from ui.console_ui import ConsoleUI

# Pygame UI (optional, requires pygame)
try:
    from ui.pygame_ui import PygameUI
    from ui.tile_renderer import TileRenderer
    from ui.board_renderer import BoardRenderer
    from ui.animation_manager import AnimationManager
    from ui.sound_manager import SoundManager
    _PYGAME_AVAILABLE = True
except ImportError:
    _PYGAME_AVAILABLE = False

__all__ = [
    'ConsoleUI',
    'PygameUI' if _PYGAME_AVAILABLE else None,
    'TileRenderer' if _PYGAME_AVAILABLE else None,
    'BoardRenderer' if _PYGAME_AVAILABLE else None,
    'AnimationManager' if _PYGAME_AVAILABLE else None,
    'SoundManager' if _PYGAME_AVAILABLE else None,
]

# Filter out None values
__all__ = [x for x in __all__ if x is not None]
