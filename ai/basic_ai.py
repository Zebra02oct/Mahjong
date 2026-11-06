"""
Mahjong Riichi - Basic AI (Level 2)
Shanten-aware AI that optimizes for hand improvement
"""

import random
from typing import List, Tuple
from core.tiles import Tile, tiles_to_counts
from core.shanten import ShantenCalculator
from engine.game_state import GameState
from ai.base_ai import BaseAI


class BasicAI(BaseAI):
    """
    Level 2 AI - Shanten-aware decision making

    Behavior:
    - Discards based on shanten optimization
    - Considers wait quality
    - Better call decisions
    - Smarter riichi timing
    """

    def __init__(self, player_id: int, difficulty: int = 2):
        super().__init__(player_id, difficulty)

    def decide_discard(self, game_state: GameState) -> Tile:
        """
        Discard tile that optimizes shanten

        Strategy:
        1. Calculate shanten for each possible discard
        2. Choose tile that maintains lowest shanten
        3. Break ties with wait quality
        """
        player = game_state.players[self.player_id]
        hand = player.hand

        # Filter out just-drawn tile
        available = [t for t in hand if not t.just_drawn]
        if not available:
            available = hand

        best_tile = None
        best_shanten = float('inf')
        best_wait_quality = -1

        for tile in available:
            # Simulate discarding this tile
            temp_hand = [t for t in hand if t != tile]
            shanten = self.shanten_calc.calculate_shanten(temp_hand)

            # Calculate wait quality if this would be tenpai
            wait_quality = 0
            if shanten == 0:
                wait_tiles = self.shanten_calc.get_wait_tiles(temp_hand)
                wait_quality = self._estimate_wait_quality(temp_hand, wait_tiles, game_state)

            # Score: lower shanten is better, higher wait quality is better
            score = shanten * 100 - wait_quality

            if score < best_shanten or (score == best_shanten and wait_quality > best_wait_quality):
                best_shanten = shanten
                best_wait_quality = wait_quality
                best_tile = tile

        return best_tile if best_tile else available[0]

    def decide_call(self, game_state: GameState, call_type: str, tile: Tile) -> bool:
        """
        Better call decisions based on hand improvement

        Strategy:
        - Ron: Always if it wins
        - Pon: If improves shanten
        - Chi: If improves shanten and not sacrificing good wait
        - Kan: Rarely (opens hand)
        """
        player = game_state.players[self.player_id]
        hand = player.hand

        # Ron: Always if it wins
        if call_type == "ron":
            return self._check_win(hand, tile, game_state)

        # Can't chi after calling
        if call_type == "chi" and player.has_called_melds():
            return False

        # Can't chi if not next player
        if call_type == "chi":
            expected_player = (game_state.last_discarded_by + 1) % 4
            if self.player_id != expected_player:
                return False

        # Pon: Consider if it helps
        if call_type == "pon":
            return self._should_pon(hand, tile, game_state)

        # Chi: Consider if it helps
        if call_type == "chi":
            return self._should_chi(hand, tile, game_state)

        # Kan: Rarely (usually bad for shanten)
        if call_type == "kan":
            return self._should_kan(hand, tile, game_state)

        return False

    def _check_win(self, hand: List[Tile], tile: Tile, game_state: GameState) -> bool:
        """Check if calling ron would result in a win"""
        temp_hand = hand + [tile]
        return self.shanten_calc.is_agari(temp_hand)

    def _should_pon(self, hand: List[Tile], tile: Tile, game_state: GameState) -> bool:
        """Decide if pon is beneficial"""
        player = game_state.players[self.player_id]

        # Already called? Pon reduces hand quality
        if player.has_called_melds():
            return False

        # Check current shanten
        current_shanten = self.shanten_calc.calculate_shanten(hand)

        # Simulate pon
        temp_counts = tiles_to_counts(hand)
        temp_counts[tile.type] += 1

        # After pon, would need to discard
        # Check if hand is still viable
        temp_shanten = self.shanten_calc.calculate_shanten_from_counts(temp_counts)

        # Pon is good if it doesn't increase shanten much
        return temp_shanten <= current_shanten + 1

    def _should_chi(self, hand: List[Tile], tile: Tile, game_state: GameState) -> bool:
        """Decide if chi is beneficial"""
        player = game_state.players[self.player_id]

        # Can't chi after calling
        if player.has_called_melds():
            return False

        # Chi opens the hand (reduces menzen bonus)
        current_shanten = self.shanten_calc.calculate_shanten(hand)

        # Chi is more acceptable if already far from tenpai
        return current_shanten > 2

    def _should_kan(self, hand: List[Tile], tile: Tile, game_state: GameState) -> bool:
        """Decide if kan is beneficial"""
        # Kan is rarely beneficial for AI
        # Opens hand, gives away information
        return random.random() < 0.1  # 10% chance

    def _estimate_wait_quality(self, hand: List[Tile], wait_tiles: List[int],
                               game_state: GameState) -> int:
        """
        Estimate quality of wait tiles

        Higher quality = more tiles available
        """
        if not wait_tiles:
            return 0

        quality = 0
        for wait_type in wait_tiles:
            # Count remaining tiles
            remaining = game_state.get_remaining_tile_count(wait_type)
            quality += remaining

        return quality

    def decide_riichi(self, game_state: GameState, tile: Tile) -> bool:
        """
        Smarter riichi timing

        Declare riichi if:
        - In tenpai
        - Has decent wait quality
        - Not too risky (score allows it)
        """
        player = game_state.players[self.player_id]

        if not player.can_declare_riichi():
            return False

        if not player.is_tenpai:
            return False

        # Check wait quality
        wait_tiles = self.shanten_calc.get_wait_tiles(player.hand)
        wait_quality = self._estimate_wait_quality(player.hand, wait_tiles, game_state)

        # Higher wait quality = more likely to riichi
        if wait_quality >= 20:
            return True
        elif wait_quality >= 10:
            return random.random() < 0.7
        else:
            return random.random() < 0.3
