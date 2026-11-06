"""
Mahjong Riichi - Advanced AI (Level 3)
Full-featured AI with defense and offense balancing
"""

import random
from typing import List, Tuple, Dict
from core.tiles import Tile, tiles_to_counts
from core.shanten import ShantenCalculator
from core.constants import PIN_RANGE, SOU_RANGE, MAN_RANGE, TERMINALS, HONORS
from engine.game_state import GameState
from ai.base_ai import BaseAI


class AdvancedAI(BaseAI):
    """
    Level 3 AI - Full defense and offense

    Features:
    - Shanten optimization
    - Tile danger assessment
    - Suji trap detection
    - Rimoteness calculation
    - Defensive/offensive balance
    - Riichi timing
    - Dora exploitation
    """

    def __init__(self, player_id: int, difficulty: int = 3):
        super().__init__(player_id, difficulty)

    def decide_discard(self, game_state: GameState) -> Tile:
        """
        Advanced discard decision

        Combines:
        1. Offense score (shanten, wait quality)
        2. Defense score (tile danger)
        3. Game situation factors
        """
        player = game_state.players[self.player_id]
        hand = player.hand

        # Filter out just-drawn tile
        available = [t for t in hand if not t.just_drawn]
        if not available:
            available = hand

        # Calculate game situation
        player_score = player.score
        avg_score = sum(p.score for p in game_state.players) / 4
        is_behind = player_score < avg_score - 10000

        # Weight offense vs defense based on situation
        if is_behind:
            offense_weight = 0.7
            defense_weight = 0.3
        else:
            offense_weight = 0.4
            defense_weight = 0.6

        best_tile = None
        best_score = float('-inf')

        for tile in available:
            offense_score = self._calculate_offense_score(tile, hand, game_state)
            defense_score = self._calculate_defense_score(tile, game_state)

            total_score = (
                offense_score * offense_weight +
                defense_score * defense_weight
            )

            if total_score > best_score:
                best_score = total_score
                best_tile = tile

        return best_tile if best_tile else available[0]

    def _calculate_offense_score(self, tile: Tile, hand: List[Tile],
                                game_state: GameState) -> float:
        """Calculate offensive score for discarding a tile"""
        score = 0.0

        # Calculate shanten
        temp_hand = [t for t in hand if t != tile]
        shanten = self.shanten_calc.calculate_shanten(temp_hand)

        # Current shanten
        current_shanten = self.shanten_calc.calculate_shanten(hand)

        # Shanten improvement
        shanten_improvement = current_shanten - shanten
        score += shanten_improvement * 100

        # Wait quality
        if shanten == 0:
            wait_tiles = self.shanten_calc.get_wait_tiles(temp_hand)
            wait_quality = sum(
                game_state.get_remaining_tile_count(w)
                for w in wait_tiles
            )
            score += wait_quality * 5

        # Dora bonus
        if tile.is_dora or self._is_dora_related(tile, game_state):
            score += 20

        # Terminal/honor penalty
        if tile.is_terminal:
            score -= 10
        elif tile.is_honor:
            score -= 5

        # Pair tile penalty (don't break pairs early)
        counts = tiles_to_counts(hand)
        if counts[tile.type] == 2 and tile.type not in TERMINALS:
            score -= 5

        return score

    def _calculate_defense_score(self, tile: Tile, game_state: GameState) -> float:
        """Calculate defensive score for discarding a tile"""
        score = 100.0  # Base safe score

        # 1. Genbutsu - already discarded tiles
        if self._is_genbutsu(tile, game_state):
            score += 50

        # 2. Suji danger
        suji_danger = self._calculate_suji_danger(tile, game_state)
        score -= suji_danger * 80

        # 3. Rimoteness
        rimoteness = self._calculate_rimoteness(tile, game_state)
        score += rimoteness * 30

        # 4. Dora penalty
        if tile.is_dora or self._is_dora_related(tile, game_state):
            score -= 30

        # 5. Early game honor preference
        if game_state.turn_number < 15:
            if tile.is_honor:
                score += 40
            elif tile.is_terminal:
                score += 10

        # 6. Late game - be more aggressive
        if game_state.turn_number > 50:
            score *= 0.7

        return score

    def _is_genbutsu(self, tile: Tile, game_state: GameState) -> bool:
        """Check if tile is genbutsu (safe tile)"""
        player = game_state.players[self.player_id]
        return any(t.type == tile.type for t in player.discards)

    def _calculate_suji_danger(self, tile: Tile, game_state: GameState) -> float:
        """
        Calculate suji trap danger

        Suji: Numbers that share the same modulo 3
        1-4-7, 2-5-8, 3-6-9

        If someone discards 1, they might be waiting for 4 or 7
        """
        if not tile.is_suit:
            return 0.0

        danger = 0.0
        value = tile.value
        suit = tile.suit

        # Determine suji group
        suji_group = value % 3  # 0=1/4/7, 1=2/5/8, 2=3/6/9

        # Check discards from other players
        for player in game_state.players:
            if player.player_id == self.player_id:
                continue

            for discard in player.discards:
                if not discard.is_suit or discard.suit != suit:
                    continue

                discard_value = discard.value
                discard_group = discard_value % 3

                # Same suji group = potential trap
                if discard_group == suji_group:
                    diff = abs(discard_value - value)
                    if diff in [3, 6]:  # Adjacent suji
                        danger = max(danger, 0.6)
                    elif diff in [6]:
                        danger = max(danger, 0.3)

        return danger

    def _calculate_rimoteness(self, tile: Tile, game_state: GameState) -> float:
        """
        Calculate rimoteness (how far from potential danger)

        More tiles discarded = less chance of being waited
        """
        all_discards = game_state.get_all_discards()
        discard_count = sum(1 for t in all_discards if t.type == tile.type)

        # 0 discards = 0% rimoteness (could be waited)
        # 4 discards = 100% rimoteness (all in discard)
        rimoteness = min(1.0, discard_count / 4)

        return rimoteness

    def _is_dora_related(self, tile: Tile, game_state: GameState) -> bool:
        """Check if tile is related to a dora indicator"""
        for indicator in game_state.dora_indicators:
            if self._is_next_tile(tile.type, indicator.type):
                return True
        return False

    def _is_next_tile(self, tile_type: int, indicator_type: int) -> bool:
        """Check if tile is the next tile after indicator"""
        # Pin
        if 0 <= indicator_type <= 8:
            next_tile = 0 if indicator_type == 8 else indicator_type + 1
            return tile_type == next_tile
        # Sou
        if 9 <= indicator_type <= 17:
            next_tile = 9 if indicator_type == 17 else indicator_type + 1
            return tile_type == next_tile
        # Man
        if 18 <= indicator_type <= 26:
            next_tile = 18 if indicator_type == 26 else indicator_type + 1
            return tile_type == next_tile
        return False

    def decide_call(self, game_state: GameState, call_type: str, tile: Tile) -> bool:
        """
        Advanced call decisions

        Considers:
        - Current shanten
        - Defense implications
        - Dora potential
        """
        player = game_state.players[self.player_id]
        hand = player.hand

        # Ron: Always if winning
        if call_type == "ron":
            return self._check_win(hand, tile, game_state)

        # Can't chi after calling
        if call_type == "chi" and player.has_called_melds():
            return False

        # Chi only if next player
        if call_type == "chi":
            expected = (game_state.last_discarded_by + 1) % 4
            if self.player_id != expected:
                return False

        # Pon: Evaluate cost/benefit
        if call_type == "pon":
            return self._should_pon_advanced(hand, tile, game_state)

        # Chi: Evaluate
        if call_type == "chi":
            return self._should_chi_advanced(hand, tile, game_state)

        # Kan: Very rare
        if call_type == "kan":
            return self._should_kan_advanced(hand, tile, game_state)

        return False

    def _check_win(self, hand: List[Tile], tile: Tile,
                  game_state: GameState) -> bool:
        """Check if ron wins"""
        temp_hand = hand + [tile]
        return self.shanten_calc.is_agari(temp_hand)

    def _should_pon_advanced(self, hand: List[Tile], tile: Tile,
                            game_state: GameState) -> bool:
        """Advanced pon decision"""
        player = game_state.players[self.player_id]

        # Never pon if already called
        if player.has_called_melds():
            return False

        # Calculate current situation
        current_shanten = self.shanten_calc.calculate_shanten(hand)

        # Simulate pon
        temp_counts = tiles_to_counts(hand)
        temp_counts[tile.type] += 1

        # After pon, will need to discard
        # Pon is good if:
        # 1. Not sacrificing tenpai
        # 2. Terminal/honor pon has value
        # 3. Have good defense after

        if tile.is_terminal or tile.is_honor:
            # Pon of terminal/honor is usually good
            return current_shanten <= 3

        # Simple tile pon - be more conservative
        return current_shanten <= 1

    def _should_chi_advanced(self, hand: List[Tile], tile: Tile,
                             game_state: GameState) -> bool:
        """Advanced chi decision"""
        player = game_state.players[self.player_id]

        if player.has_called_melds():
            return False

        current_shanten = self.shanten_calc.calculate_shanten(hand)

        # Chi opens hand, usually bad for shanten
        # Only chi if far from tenpai
        return current_shanten >= 3

    def _should_kan_advanced(self, hand: List[Tile], tile: Tile,
                           game_state: GameState) -> bool:
        """Advanced kan decision"""
        # Kan is almost never worth it
        # Opens hand, gives info, rarely improves tenpai

        # Only kan if it would win immediately
        temp_hand = hand + [tile]
        return self.shanten_calc.is_agari(temp_hand)

    def decide_riichi(self, game_state: GameState, tile: Tile) -> bool:
        """
        Advanced riichi decision

        Consider:
        - Wait quality
        - Defense after riichi
        - Score position
        - Dora potential
        """
        player = game_state.players[self.player_id]

        if not player.can_declare_riichi():
            return False

        if not player.is_tenpai:
            return False

        # Wait quality check
        wait_tiles = self.shanten_calc.get_wait_tiles(player.hand)
        wait_quality = sum(
            game_state.get_remaining_tile_count(w)
            for w in wait_tiles
        )

        # Dora count
        dora_count = len(game_state.dora_indicators)

        # Score position
        if player.score < 10000:
            return False  # Can't afford to riichi

        # Decision based on quality
        if wait_quality >= 30:
            return True
        elif wait_quality >= 20 and dora_count >= 1:
            return True
        elif wait_quality >= 15:
            return random.random() < 0.8
        else:
            return random.random() < 0.4
