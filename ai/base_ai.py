"""
Mahjong Riichi - AI Base Interface
Abstract base class for AI players
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from core.tiles import Tile, tiles_to_counts
from core.shanten import ShantenCalculator
from engine.game_state import GameState


class BaseAI(ABC):
    """
    Abstract base class for Mahjong AI

    AI subclasses must implement:
    - decide_discard(): Choose which tile to discard
    - decide_call(): Choose whether to call (pon/chi/kan/ron)
    - decide_riichi(): Choose whether to declare riichi
    """

    def __init__(self, player_id: int, difficulty: int = 1):
        """
        Initialize AI

        Args:
            player_id: Player ID
            difficulty: AI difficulty level (1=easy, 2=medium, 3=hard)
        """
        self.player_id = player_id
        self.difficulty = difficulty
        self.shanten_calc = ShantenCalculator()

    @abstractmethod
    def decide_discard(self, game_state: GameState) -> Tile:
        """
        Decide which tile to discard

        Args:
            game_state: Current game state

        Returns:
            Tile to discard
        """
        pass

    @abstractmethod
    def decide_call(self, game_state: GameState, call_type: str,
                   tile: Tile) -> bool:
        """
        Decide whether to call (pon/chi/kan/ron)

        Args:
            game_state: Current game state
            call_type: Type of call ("pon", "chi", "kan", "ron")
            tile: The tile to call

        Returns:
            True to call, False to skip
        """
        pass

    def decide_riichi(self, game_state: GameState, tile: Tile) -> bool:
        """
        Decide whether to declare riichi

        Default implementation checks basic requirements

        Args:
            game_state: Current game state
            tile: Tile to be discarded

        Returns:
            True to declare riichi
        """
        player = game_state.players[self.player_id]

        # Basic requirements
        if player.riichi_declared:
            return False
        if player.has_called_melds():
            return False
        if player.score < 1000:
            return False
        if not player.is_tenpai:
            return False

        # Higher difficulty = more likely to riichi
        if self.difficulty >= 2:
            return True

        # Low difficulty: only riichi with good wait
        waits = self.shanten_calc.get_wait_tiles(player.hand)
        if len(waits) >= 2:
            return True

        return False

    def get_hand_info(self, game_state: GameState) -> dict:
        """
        Get information about current hand

        Returns:
            Dict with hand statistics
        """
        player = game_state.players[self.player_id]
        hand = player.hand

        counts = tiles_to_counts(hand)

        # Calculate shanten
        shanten = self.shanten_calc.calculate_shanten(hand)

        # Get wait tiles if tenpai
        wait_tiles = []
        wait_quality = 0
        if shanten == 0:
            wait_tiles = self.shanten_calc.get_wait_tiles(hand)
            wait_quality = len(wait_tiles)

        return {
            'hand_size': len(hand),
            'shanten': shanten,
            'is_tenpai': shanten == 0,
            'wait_tiles': wait_tiles,
            'wait_quality': wait_quality,
            'has_called': player.has_called_melds(),
            'is_menzen': player.is_menzen(),
            'riichi_declared': player.riichi_declared,
        }

    def get_tile_danger(self, tile: Tile, game_state: GameState) -> float:
        """
        Calculate danger level of a tile (0.0 = safe, 1.0 = dangerous)

        Used for defensive play

        Args:
            tile: Tile to assess
            game_state: Current game state

        Returns:
            Danger level (0.0 to 1.0)
        """
        danger = 0.0

        # Count how many of this tile have been discarded
        all_discards = game_state.get_all_discards()
        discarded_count = sum(1 for t in all_discards if t.type == tile.type)

        # More discards = safer
        if discarded_count >= 4:
            danger = 0.0
        elif discarded_count >= 2:
            danger = 0.3
        elif discarded_count >= 1:
            danger = 0.6
        else:
            danger = 0.9

        # Honor tiles are slightly safer early game
        if tile.is_honor and game_state.turn_number < 20:
            danger *= 0.7

        # Terminal tiles are more dangerous
        if tile.is_terminal:
            danger *= 1.2

        return min(1.0, max(0.0, danger))
