"""
Mahjong Riichi - Random AI (Level 1)
Simple AI that makes random valid decisions
"""

import random
from typing import List
from core.tiles import Tile
from core.constants import STARTING_SCORE
from engine.game_state import GameState
from ai.base_ai import BaseAI


class RandomAI(BaseAI):
    """
    Level 1 AI - Random decisions

    Behavior:
    - Discard random tile (except just-drawn)
    - Random call decisions
    - Sometimes declares riichi randomly
    """

    def __init__(self, player_id: int, difficulty: int = 1):
        super().__init__(player_id, difficulty)

    def decide_discard(self, game_state: GameState) -> Tile:
        """
        Discard a random tile

        Strategy: Pick any tile that's not just drawn
        """
        player = game_state.players[self.player_id]
        hand = player.hand

        # Filter out just-drawn tile
        available = [t for t in hand if not t.just_drawn]

        if not available:
            available = hand

        return random.choice(available)

    def decide_call(self, game_state: GameState, call_type: str, tile: Tile) -> bool:
        """
        Random call decision

        Probabilities:
        - Ron: 80%
        - Pon: 50%
        - Chi: 40%
        - Kan: 30%
        """
        player = game_state.players[self.player_id]

        # Can't call if not menzen (except kan)
        if call_type == "chi" and player.has_called_melds():
            return False

        # Can't chi if not next player
        if call_type == "chi":
            expected_player = (game_state.last_discarded_by + 1) % 4
            if self.player_id != expected_player:
                return False

        # Random decision based on call type
        probabilities = {
            'ron': 0.80,
            'pon': 0.50,
            'chi': 0.40,
            'kan': 0.30,
        }

        return random.random() < probabilities.get(call_type, 0.0)

    def decide_riichi(self, game_state: GameState, tile: Tile) -> bool:
        """
        Random riichi decision

        Only declares riichi 30% of the time when in tenpai
        """
        player = game_state.players[self.player_id]

        if not player.can_declare_riichi():
            return False

        if not player.is_tenpai:
            return False

        return random.random() < 0.30
