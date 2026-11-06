"""
Mahjong Riichi - AI Utilities
Utility classes for enhanced AI decision making
"""

from typing import List, Dict, Tuple, Optional
from core.tiles import Tile, tiles_to_counts
from core.shanten import ShantenCalculator
from core.constants import (
    PIN_RANGE, SOU_RANGE, MAN_RANGE, WIND_RANGE, DRAGON_RANGE,
    TERMINALS, HONORS, SIMPLES
)


class TileAnalyzer:
    """
    Analyzes tiles and hand patterns
    """

    def __init__(self):
        self.shanten_calc = ShantenCalculator()

    def calculate_tile_value(self, tile: Tile, hand: List[Tile],
                           game_state) -> float:
        """
        Calculate the value of a tile for discarding

        Returns value from -100 (very bad) to +100 (very good)
        """
        value = 0.0

        # Terminal tiles are harder to use
        if tile.is_terminal:
            value -= 15

        # Honor tiles are situational
        if tile.is_honor:
            value -= 5

        # Check if tile is part of potential melds
        hand_counts = tiles_to_counts(hand)

        # Pair potential
        if hand_counts[tile.type] == 2:
            value += 20  # Keep pairs

        # Pong potential
        if hand_counts[tile.type] == 1:
            # Check if another of same tile exists
            remaining = game_state.get_remaining_tile_count(tile.type)
            if remaining >= 2:
                value += 10

        # Chow potential (for suit tiles)
        if tile.is_suit:
            value += self._calculate_chow_value(tile, hand_counts)

        # Dora bonus
        for indicator in game_state.dora_indicators:
            if self._is_next_tile(tile.type, indicator.type):
                value += 25

        return value

    def _calculate_chow_value(self, tile: Tile, hand_counts: List[int]) -> float:
        """Calculate how valuable a tile is for forming chows"""
        if not tile.is_suit:
            return 0.0

        value = 0.0
        suit_start = self._get_suit_start(tile.type)
        idx = tile.type - suit_start  # 0-8

        # Check adjacent tiles
        adjacent_count = 0
        if idx > 0:
            adjacent_count += hand_counts[suit_start + idx - 1]
        if idx < 8:
            adjacent_count += hand_counts[suit_start + idx + 1]

        # More adjacent = more valuable
        value += adjacent_count * 5

        # Middle tiles (3-7) are more flexible
        if 2 <= idx <= 6:
            value += 10

        return value

    def _get_suit_start(self, tile_type: int) -> int:
        """Get the start index of a suit"""
        if 0 <= tile_type <= 8:
            return 0
        elif 9 <= tile_type <= 17:
            return 9
        elif 18 <= tile_type <= 26:
            return 18
        return 0

    def _is_next_tile(self, tile_type: int, indicator_type: int) -> bool:
        """Check if tile is next after indicator"""
        if 0 <= indicator_type <= 8:
            next_tile = 0 if indicator_type == 8 else indicator_type + 1
            return tile_type == next_tile
        if 9 <= indicator_type <= 17:
            next_tile = 9 if indicator_type == 17 else indicator_type + 1
            return tile_type == next_tile
        if 18 <= indicator_type <= 26:
            next_tile = 18 if indicator_type == 26 else indicator_type + 1
            return tile_type == next_tile
        return False

    def estimate_wait_quality(self, waits: List[int], game_state) -> float:
        """
        Estimate the quality of wait tiles

        Returns quality score based on:
        - Number of remaining tiles
        - Wait type (ryanmen > kanchan > penchan > tanki)
        - Suit diversity
        """
        if not waits:
            return 0.0

        quality = 0.0

        # Count remaining tiles
        total_remaining = sum(
            game_state.get_remaining_tile_count(w) for w in waits
        )
        quality += total_remaining * 2

        # Suit diversity bonus
        suits = set(w // 9 for w in waits)
        quality += len(suits) * 10

        # Wait type analysis
        wait_types = [self._classify_wait(w) for w in waits]
        for wt in wait_types:
            if wt == 'ryanmen':
                quality += 30
            elif wt == 'kanchan':
                quality += 15
            elif wt == 'penchan':
                quality += 5
            # tanki gets no bonus

        return quality

    def _classify_wait(self, tile_type: int) -> str:
        """Classify a wait tile type"""
        if 0 <= tile_type <= 8:
            suit_range = PIN_RANGE
        elif 9 <= tile_type <= 17:
            suit_range = SOU_RANGE
        elif 18 <= tile_type <= 26:
            suit_range = MAN_RANGE
        else:
            return 'tanki'

        idx = tile_type - suit_range[0]

        if idx in [1, 2, 3, 4, 5, 6]:  # Not edge
            return 'ryanmen'
        elif idx in [0, 8]:  # Edge
            return 'penchan'
        else:
            return 'tanki'

    def analyze_hand_shape(self, hand: List[Tile]) -> Dict:
        """
        Analyze the shape of a hand

        Returns analysis with:
        - tenpai_ready: bool
        - shape_type: str (toitoi, chanta, etc.)
        - development_potential: float
        """
        counts = tiles_to_counts(hand)

        # Count groups
        pairs = sum(1 for c in counts if c >= 2)
        pons = sum(c // 3 for c in counts)
        singles = sum(1 for c in counts if c == 1)
        doubles = sum(1 for c in counts if c == 2)

        # Determine shape
        shape_type = "normal"
        if pons >= 3:
            shape_type = "toitoi"
        elif self._is_honitsu(counts):
            shape_type = "honitsu"
        elif self._is_chinitsu(counts):
            shape_type = "chinitsu"

        # Calculate development potential
        potential = self._calculate_potential(counts)

        return {
            'shape_type': shape_type,
            'pairs': pairs,
            'pons': pons,
            'singles': singles,
            'doubles': doubles,
            'development_potential': potential
        }

    def _is_honitsu(self, counts: List[int]) -> bool:
        """Check if hand is half flush"""
        has_suit = False
        suit_type = None

        for i in range(34):
            if counts[i] == 0:
                continue
            if i in TERMINALS or i in HONORS:
                continue
            tile_suit = i // 9
            if suit_type is None:
                suit_type = tile_suit
                has_suit = True
            elif tile_suit != suit_type:
                return False

        return has_suit

    def _is_chinitsu(self, counts: List[int]) -> bool:
        """Check if hand is full flush"""
        suit_type = None
        for i in range(34):
            if counts[i] == 0:
                continue
            if i in HONORS:
                return False
            tile_suit = i // 9
            if suit_type is None:
                suit_type = tile_suit
            elif tile_suit != suit_type:
                return False
        return suit_type is not None

    def _calculate_potential(self, counts: List[int]) -> float:
        """Calculate hand development potential"""
        potential = 0.0

        # Singles are potential for pairs
        singles = sum(1 for c in counts if c == 1)
        potential += singles * 5

        # Doubles are closer to pairs
        doubles = sum(1 for c in counts if c == 2)
        potential += doubles * 10

        # Suits with 2-3 tiles are promising
        for i in range(27):  # Only suits
            suit_tiles = sum(counts[i:i+9])
            if 2 <= suit_tiles <= 4:
                potential += 5

        return potential

    def calculate_shanten_improvement(self, tile: Tile, hand: List[Tile],
                                     game_state) -> float:
        """
        Calculate how discarding this tile affects shanten

        Args:
            tile: The tile being considered for discard
            hand: Current hand (usually 14 tiles)
            game_state: Current game state for context

        Returns:
            Improvement score: negative means worse, positive means better
            - Higher positive = better discard for shanten improvement
            - 0 = neutral
            - Negative = discard worsens shanten
        """
        counts = tiles_to_counts(hand)
        current_shanten = self.shanten_calc.calculate_shanten(hand)

        # If already at shanten 0 (tenpai), no improvement possible
        if current_shanten < 0:
            return 0.0

        # Simulate removing this tile
        if counts[tile.type] <= 0:
            return 0.0

        temp_counts = counts.copy()
        temp_counts[tile.type] -= 1

        # Calculate shanten with tile removed
        new_shanten = self.shanten_calc.calculate_shanten_from_counts(temp_counts)

        # Calculate raw improvement
        improvement = current_shanten - new_shanten

        # Bonus for reaching tenpai
        if new_shanten == 0 and current_shanten > 0:
            improvement += 2.0

        # Bonus for getting closer to winning (shanten -1)
        if new_shanten == -1:
            improvement += 3.0

        return improvement

    def analyze_wait_patterns(self, hand: List[Tile], game_state=None) -> Dict:
        """
        Identify all possible tenpai patterns and classify wait types

        Args:
            hand: Current hand (usually 13 tiles for tenpai analysis)
            game_state: Optional game state for remaining tile count

        Returns:
            Dictionary containing:
            - tenpai_patterns: List of possible winning tiles with details
            - wait_types: Classification of waits (ryanmen, kanchan, penchan, tanki)
            - wait_diversity: Score 0-100 for variety of wait options
            - best_wait: Best tile to wait for
        """
        if len(hand) != 13:
            return {
                'tenpai_patterns': [],
                'wait_types': [],
                'wait_diversity': 0.0,
                'best_wait': None
            }

        counts = tiles_to_counts(hand)
        current_shanten = self.shanten_calc.calculate_shanten(hand)

        # Find all tiles that would complete the hand
        tenpai_patterns = []
        wait_type_counts = {'ryanmen': 0, 'kanchan': 0, 'penchan': 0, 'tanki': 0}

        for tile_type in range(34):
            if counts[tile_type] >= 4:
                continue  # Already have 4, can't draw

            temp_counts = counts.copy()
            temp_counts[tile_type] += 1

            if self.shanten_calc.calculate_shanten_from_counts(temp_counts) == 0:
                # This tile completes the hand
                wait_type = self._classify_wait_tile(tile_type)
                remaining = game_state.get_remaining_tile_count(tile_type) if game_state else 4 - counts[tile_type]

                tenpai_patterns.append({
                    'tile_type': tile_type,
                    'wait_type': wait_type,
                    'remaining': remaining,
                    'tile_name': self._get_tile_name(tile_type)
                })
                wait_type_counts[wait_type] += 1

        # Calculate wait diversity (0-100)
        diversity = 0.0
        if tenpai_patterns:
            # More unique wait types = higher diversity
            unique_types = sum(1 for v in wait_type_counts.values() if v > 0)
            diversity += unique_types * 20

            # More total waits = higher diversity
            diversity += min(len(tenpai_patterns) * 5, 30)

            # Ryanmen preference
            diversity += wait_type_counts['ryanmen'] * 10

        # Find best wait
        best_wait = None
        if tenpai_patterns:
            # Prefer ryanmen, then remaining count
            sorted_patterns = sorted(
                tenpai_patterns,
                key=lambda p: (
                    {'ryanmen': 0, 'kanchan': 1, 'penchan': 2, 'tanki': 3}[p['wait_type']],
                    -p['remaining']
                )
            )
            best_wait = sorted_patterns[0]['tile_type']

        return {
            'tenpai_patterns': tenpai_patterns,
            'wait_types': wait_type_counts,
            'wait_diversity': min(diversity, 100.0),
            'best_wait': best_wait,
            'current_shanten': current_shanten
        }

    def _classify_wait_tile(self, tile_type: int) -> str:
        """
        Classify the wait type for a specific tile

        Args:
            tile_type: Tile type (0-33)

        Returns:
            Wait type: 'ryanmen', 'kanchan', 'penchan', or 'tanki'
        """
        if 0 <= tile_type <= 8:
            suit_range = PIN_RANGE
        elif 9 <= tile_type <= 17:
            suit_range = SOU_RANGE
        elif 18 <= tile_type <= 26:
            suit_range = MAN_RANGE
        else:
            return 'tanki'  # Honors are always tanki

        idx = tile_type - suit_range[0]  # 0-8

        if idx == 0 or idx == 8:
            return 'penchan'  # Waiting for 1 or 9 (edge)
        elif idx == 4:
            return 'kanchan'  # Waiting for 5 in 4-5-6
        elif 1 <= idx <= 7:
            return 'ryanmen'  # Middle tiles have better waits
        else:
            return 'tanki'

    def _get_tile_name(self, tile_type: int) -> str:
        """Get display name for tile type"""
        if 0 <= tile_type <= 8:
            return f"{tile_type + 1}-pin"
        elif 9 <= tile_type <= 17:
            return f"{tile_type - 8}-sou"
        elif 18 <= tile_type <= 26:
            return f"{tile_type - 17}-man"
        elif tile_type == 27:
            return "east"
        elif tile_type == 28:
            return "south"
        elif tile_type == 29:
            return "west"
        elif tile_type == 30:
            return "north"
        elif tile_type == 31:
            return "white-dragon"
        elif tile_type == 32:
            return "green-dragon"
        else:
            return "red-dragon"

    def calculate_hand_complexity(self, hand: List[Tile]) -> float:
        """
        Calculate the complexity/flexibility of a hand

        Args:
            hand: List of tiles to analyze

        Returns:
            Complexity score from 0-100:
            - 0-30: Simple, rigid hand (few options)
            - 31-60: Moderate complexity
            - 61-100: Complex, flexible hand (many options)
        """
        counts = tiles_to_counts(hand)

        # Count distinct tile types present
        distinct_tiles = sum(1 for c in counts if c > 0)
        distinct_score = min(distinct_tiles * 3, 30)  # Max 30 points

        # Assess flexibility based on tile distribution
        singles = sum(1 for c in counts if c == 1)
        doubles = sum(1 for c in counts if c == 2)
        triples_plus = sum(1 for c in counts if c >= 3)

        # Singles and doubles give flexibility
        flexibility_score = min(singles * 2 + doubles * 3 + triples_plus * 1, 40)

        # Assess suit balance
        suit_balance = self._calculate_suit_balance(counts)
        balance_score = suit_balance * 30  # Max 30 points

        # Total complexity score
        complexity = distinct_score + flexibility_score + balance_score
        return min(complexity, 100.0)

    def _calculate_suit_balance(self, counts: List[int]) -> float:
        """
        Calculate suit balance score

        Returns:
            0.0-1.0 representing how balanced the suits are
        """
        pin_count = sum(counts[0:9])
        sou_count = sum(counts[9:18])
        man_count = sum(counts[18:27])
        honor_count = sum(counts[27:34])

        total = pin_count + sou_count + man_count + honor_count
        if total == 0:
            return 0.0

        # Calculate entropy-like balance
        # Perfect balance = 1.0
        suit_counts = [pin_count, sou_count, man_count]
        non_zero = sum(1 for c in suit_counts if c > 0)

        if non_zero <= 1:
            return 0.3  # Single suit

        # Calculate how evenly distributed
        avg = sum(suit_counts) / non_zero
        if avg == 0:
            return 0.0

        variance = sum((c - avg) ** 2 for c in suit_counts if c > 0) / non_zero
        max_variance = avg ** 2 * (non_zero - 1) / non_zero

        if max_variance == 0:
            return 1.0

        balance = 1.0 - (variance / max_variance)
        return max(0.0, min(1.0, balance))

    def evaluate_meld_potential(self, tile: Tile, hand: List[Tile]) -> Dict:
        """
        Check if tile completes or extends a meld

        Args:
            tile: The tile to evaluate
            hand: Current hand

        Returns:
            Dictionary containing:
            - completes_pon: True if tile completes a pong
            - extends_pon: Score for extending toward a pong (0-10)
            - completes_chow: True if tile completes a sequence
            - extends_chow: Score for extending toward a sequence (0-10)
            - overall_potential: Combined potential score (0-20)
        """
        counts = tiles_to_counts(hand)
        result = {
            'completes_pon': False,
            'extends_pon': 0.0,
            'completes_chow': False,
            'extends_chow': 0.0,
            'overall_potential': 0.0
        }

        # Check pong potential
        current_count = counts[tile.type]
        if current_count == 3:
            result['completes_pon'] = True
            result['extends_pon'] = 10.0
        elif current_count == 2:
            result['extends_pon'] = 8.0  # One away from pon
        elif current_count == 1:
            result['extends_pon'] = 3.0  # Two away from pon

        # Check chow potential (only for suit tiles)
        if tile.is_suit:
            suit_start = self._get_suit_start(tile.type)
            idx = tile.type - suit_start  # 0-8

            # Check for chi possibilities
            # Chi patterns: (n-2, n-1, n), (n-1, n, n+1), (n, n+1, n+2)
            chi_candidates = []

            # Pattern: waiting in the middle (n-1, n, n+1)
            if idx >= 1 and idx <= 7:
                left = suit_start + idx - 1
                right = suit_start + idx + 1
                if counts[left] >= 1 and counts[right] >= 1:
                    result['completes_chow'] = True
                    result['extends_chow'] = 10.0

            # Pattern: waiting at left edge (n, n+1, n+2)
            if idx >= 2:
                left = suit_start + idx - 2
                middle = suit_start + idx - 1
                if counts[left] >= 1 and counts[middle] >= 1:
                    result['completes_chow'] = True
                    result['extends_chow'] = 10.0
                    chi_candidates.append((left, middle))

            # Pattern: waiting at right edge (n-2, n-1, n)
            if idx <= 6:
                middle = suit_start + idx + 1
                right = suit_start + idx + 2
                if counts[middle] >= 1 and counts[right] >= 1:
                    result['completes_chow'] = True
                    result['extends_chow'] = 10.0
                    chi_candidates.append((middle, right))

            # Extend potential (adjacent tiles present)
            adjacent_count = 0
            if idx > 0:
                adjacent_count += counts[suit_start + idx - 1]
            if idx < 8:
                adjacent_count += counts[suit_start + idx + 1]

            if not result['completes_chow']:
                if adjacent_count >= 2:
                    result['extends_chow'] = 7.0
                elif adjacent_count == 1:
                    result['extends_chow'] = 4.0

        # Calculate overall potential
        result['overall_potential'] = max(result['extends_pon'], result['extends_chow'])
        return result

    def estimate_future_value(self, tile: Tile, hand: List[Tile],
                             game_state) -> float:
        """
        Estimate the future potential value of a tile

        Args:
            tile: The tile to evaluate
            hand: Current hand
            game_state: Current game state for context

        Returns:
            Future value score 0-100:
            - Dora-related potential
            - Suit balance contribution
            - Terminal/honor flexibility
        """
        score = 0.0

        # Dora indicator relationship
        if game_state and hasattr(game_state, 'dora_indicators'):
            for indicator in game_state.dora_indicators:
                if self._is_next_tile(tile.type, indicator.type):
                    score += 25  # Could become dora
                elif abs(tile.type - indicator.type) <= 2:
                    score += 5  # Close to dora

        # Suit balance contribution
        counts = tiles_to_counts(hand)
        current_suit_tiles = self._count_suit_tiles(counts)

        if tile.is_suit:
            # Adding to an existing suit helps balance
            if current_suit_tiles > 0:
                score += 10
            # Simpler tiles (2-8) have more future flexibility
            if tile.is_simple:
                score += 15
            # Terminals are rigid but high value if honored
            elif tile.is_terminal:
                score += 8

        # Honor tiles
        if tile.is_honor:
            # Check if matching honor already in hand
            if counts[tile.type] > 0:
                score += 12  # Could form a pair/pon
            else:
                score += 5  # Standalone honor

        # Green tile bonus (if pursuing green dragon yaku)
        if tile.is_green:
            score += 10

        # Check remaining tiles in game (future drawing probability)
        if game_state and hasattr(game_state, 'get_remaining_tile_count'):
            remaining = game_state.get_remaining_tile_count(tile.type)
            if remaining >= 3:
                score += 10
            elif remaining >= 2:
                score += 5

        return min(score, 100.0)

    def _count_suit_tiles(self, counts: List[int]) -> int:
        """Count total suit tiles in counts array"""
        return sum(counts[0:27])


class DefenseAnalyzer:
    """
    Analyzes defensive options
    """

    def __init__(self):
        self.tile_analyzer = TileAnalyzer()

    def estimate_tenpai_probability(self, player, game_state) -> float:
        """
        Estimate probability that an opponent is in tenpai

        Based on:
        - Turn number (more turns = higher chance)
        - Discard pattern
        - Riichi declarations
        """
        # Riichi = definitely tenpai
        if player.riichi_declared:
            return 1.0

        turn = game_state.turn_number
        probability = 0.0

        # Base probability increases with turns
        if turn >= 50:
            probability = 0.8
        elif turn >= 40:
            probability = 0.6
        elif turn >= 30:
            probability = 0.4
        elif turn >= 20:
            probability = 0.2
        elif turn >= 10:
            probability = 0.1

        # Adjust based on discards
        discards = player.discards

        # Analyze discard pattern
        terminals_in_discards = sum(1 for t in discards if t.is_terminal)
        honors_in_discards = sum(1 for t in discards if t.is_honor)

        # If many terminals/honors discarded, likely tenpai is waiting
        if terminals_in_discards + honors_in_discards >= 5:
            probability += 0.2

        # Late game discount
        if game_state.deck.remaining < 30:
            probability = min(1.0, probability + 0.1)

        return min(1.0, probability)

    def calculate_tile_danger(self, tile: Tile, player, game_state) -> float:
        """
        Calculate how dangerous a tile is to discard

        Returns danger level 0.0 (safe) to 1.0 (very dangerous)
        """
        danger = 0.0

        # Genbutsu - tile already discarded by this player
        if any(t.type == tile.type for t in player.discards):
            return 0.0

        # Count discards
        all_discards = game_state.get_all_discards()
        discard_count = sum(1 for t in all_discards if t.type == tile.type)

        # More discards = safer
        if discard_count >= 4:
            danger = 0.0
        elif discard_count >= 2:
            danger = 0.2
        elif discard_count >= 1:
            danger = 0.5
        else:
            danger = 0.8

        # Suji danger
        if tile.is_suit:
            suji_danger = self._calculate_suji_danger(tile, player, game_state)
            danger = max(danger, suji_danger)

        # Terminal/honor penalty
        if tile.is_terminal:
            danger += 0.1
        if tile.is_honor:
            danger -= 0.1  # Honors are safer

        # Dora tiles are dangerous
        for indicator in game_state.dora_indicators:
            if self._is_next_tile(tile.type, indicator.type):
                danger += 0.2

        return min(1.0, max(0.0, danger))

    def _calculate_suji_danger(self, tile: Tile, player,
                             game_state) -> float:
        """Calculate suji trap danger"""
        if not tile.is_suit:
            return 0.0

        value = tile.value
        suit = tile.type // 9
        suji_group = value % 3

        danger = 0.0

        # Check other players' discards for suji
        for other_player in game_state.players:
            if other_player.player_id == player.player_id:
                continue

            for discard in other_player.discards:
                if not discard.is_suit or discard.type // 9 != suit:
                    continue

                discard_value = discard.value
                discard_group = discard_value % 3

                # Same suji group
                if discard_group == suji_group:
                    diff = abs(discard_value - value)
                    if diff == 3 or diff == 6:
                        danger = max(danger, 0.6)

        return danger

    def _is_next_tile(self, tile_type: int, indicator_type: int) -> bool:
        """Check if tile is next after indicator"""
        if 0 <= indicator_type <= 8:
            return tile_type == (0 if indicator_type == 8 else indicator_type + 1)
        if 9 <= indicator_type <= 17:
            return tile_type == (9 if indicator_type == 17 else indicator_type + 1)
        if 18 <= indicator_type <= 26:
            return tile_type == (18 if indicator_type == 26 else indicator_type + 1)
        return False

    def find_safe_tiles(self, hand: List[Tile], game_state) -> List[Tile]:
        """
        Find all safe tiles to discard from hand
        """
        player = game_state.players[game_state.current_turn]
        safe_tiles = []

        for tile in hand:
            if tile.just_drawn:
                continue  # Can always discard just-drawn

            danger = self.calculate_tile_danger(tile, player, game_state)
            if danger < 0.3:
                safe_tiles.append(tile)

        return safe_tiles

    def analyze_discard_pattern(self, player) -> Dict:
        """
        Analyze the discard pattern of an opponent player

        Returns dictionary with:
        - avoided_suits: List of suits player is avoiding
        - discard_rate: Average tiles discarded per turn
        - pattern_type: 'aggressive', 'normal', 'defensive'
        - terminal_honor_ratio: Ratio of terminals/honors discarded
        - suit_distribution: Distribution across suits
        - early_terminals: Number of terminals discarded in first 5 turns
        - potential_waits: Estimated wait tiles they might have
        """
        discards = player.discards

        if not discards:
            return {
                'avoided_suits': [],
                'discard_rate': 0.0,
                'pattern_type': 'unknown',
                'terminal_honor_ratio': 0.0,
                'suit_distribution': {},
                'early_terminals': 0,
                'potential_waits': [],
                'honor_discard_count': 0,
                'suji_discards': {}
            }

        # Count by suit
        pin_count = sum(1 for t in discards if 0 <= t.type <= 8)
        sou_count = sum(1 for t in discards if 9 <= t.type <= 17)
        man_count = sum(1 for t in discards if 18 <= t.type <= 26)
        honor_count = sum(1 for t in discards if t.is_honor)

        suit_distribution = {
            'pin': pin_count,
            'sou': sou_count,
            'man': man_count,
            'honor': honor_count
        }

        # Find avoided suits (significant difference)
        total_suit_tiles = sum(suit_distribution.values())
        if total_suit_tiles > 0:
            avg_suit = (pin_count + sou_count + man_count) / 3
            avoided = []
            if pin_count > 0 and pin_count < avg_suit * 0.5:
                avoided.append('pin')
            if sou_count > 0 and sou_count < avg_suit * 0.5:
                avoided.append('sou')
            if man_count > 0 and man_count < avg_suit * 0.5:
                avoided.append('man')
        else:
            avoided = []

        # Calculate terminal/honor ratio
        terminals = sum(1 for t in discards if t.is_terminal)
        terminal_honor_ratio = (terminals + honor_count) / len(discards) if discards else 0.0

        # Count early terminals (first 5 discards)
        early_terminals = sum(1 for t in discards[:5] if t.is_terminal or t.is_honor)

        # Analyze suji patterns
        suji_discards = self._analyze_suji_discards(discards)

        # Determine pattern type
        if early_terminals >= 3 or terminal_honor_ratio > 0.6:
            pattern_type = 'aggressive'  # Discarding valuable tiles, likely tenpai
        elif avoided and len(avoided) >= 2:
            pattern_type = 'defensive'  # Focusing on one suit, building
        else:
            pattern_type = 'normal'

        # Estimate potential waits based on what they've kept
        potential_waits = self._estimate_potential_waits(discards)

        return {
            'avoided_suits': avoided,
            'discard_rate': len(discards) / max(1, getattr(player, 'turn', 1)),
            'pattern_type': pattern_type,
            'terminal_honor_ratio': terminal_honor_ratio,
            'suit_distribution': suit_distribution,
            'early_terminals': early_terminals,
            'potential_waits': potential_waits,
            'honor_discard_count': honor_count,
            'suji_discards': suji_discards,
            'total_discards': len(discards)
        }

    def _analyze_suji_discards(self, discards: List[Tile]) -> Dict:
        """
        Analyze suji (1-4-7, 2-5-8, 3-6-9) patterns in discards

        Returns dict mapping suji groups to discarded tiles
        """
        suji_groups = {
            0: [],  # 1-4-7
            1: [],  # 2-5-8
            2: []   # 3-6-9
        }

        for tile in discards:
            if not tile.is_suit:
                continue
            suji_group = (tile.value - 1) % 3
            suji_groups[suji_group].append(tile.type)

        return suji_groups

    def _estimate_potential_waits(self, discards: List[Tile]) -> List[int]:
        """
        Estimate what wait tiles an opponent might have based on discards

        Returns list of potential wait tile types
        """
        potential_waits = []

        # Build counts of what was discarded
        discarded_counts = [0] * 34
        for tile in discards:
            discarded_counts[tile.type] += 1

        # For each suit, analyze what would make a valid wait
        for suit_idx, suit_start in enumerate([0, 9, 18]):
            # Analyze sequences in discards
            # If they discarded 2-3, they might wait for 1 or 4
            suit_discarded = [discarded_counts[suit_start + i] > 0 for i in range(9)]

            for i in range(9):
                if not suit_discarded[i]:
                    # Tile not discarded - could be a wait
                    potential_waits.append(suit_start + i)

        return potential_waits

    def calculate_suji_trap_danger(self, tile: Tile, player, game_state) -> float:
        """
        Calculate the danger of a suji trap for a specific tile

        Enhanced with:
        - Basic suji detection (1-4-7, 2-5-8, 3-6-9)
        - Reverse suji (opposite side of sequence)
        - Trap likelihood based on opponent patterns

        Args:
            tile: The tile to check
            player: The player who would discard this tile
            game_state: Current game state

        Returns:
            Danger score 0.0 (safe) to 1.0 (very dangerous)
        """
        if not tile.is_suit:
            return 0.0

        danger = 0.0
        suit_start = (tile.type // 9) * 9
        tile_idx = tile.type % 9
        tile_value = tile_idx + 1  # 1-9

        # Check opponent players for suji patterns
        for other_player in game_state.players:
            if other_player.player_id == player.player_id:
                continue

            # Analyze their discards for suji patterns
            pattern = self.analyze_discard_pattern(other_player)

            # Basic suji check
            suji_group = (tile_value - 1) % 3

            # Check if they discarded a tile in the same suji group
            if suji_group in pattern['suji_discards']:
                # Found a suji discard - check distance
                for discarded_type in pattern['suji_discards'][suji_group]:
                    if discarded_type // 9 != tile.type // 9:
                        continue
                    discarded_value = (discarded_type % 9) + 1
                    distance = abs(discarded_value - tile_value)
                    if distance in [3, 6]:
                        danger = max(danger, 0.5)

            # Reverse suji check (opposite end of sequence)
            # If they discarded 7-8-9, they might be waiting for 6 (reverse suji of 3)
            reverse_suji = self._check_reverse_suji(tile, other_player)
            danger = max(danger, reverse_suji)

            # Kanchan/penchan trap detection
            kanchan_danger = self._check_kanchan_trap(tile, other_player)
            danger = max(danger, kanchan_danger)

            # Check if they're in defensive pattern
            if pattern['pattern_type'] == 'aggressive':
                danger *= 1.3  # Increase danger if they're discarding lots of terminals

        # Dead suji check - if all 4 tiles in suji are discarded
        dead_suji = self._is_dead_suji(tile, game_state)
        if dead_suji:
            danger *= 0.3  # Reduce danger if suji is "dead"

        return min(1.0, max(0.0, danger))

    def _check_reverse_suji(self, tile: Tile, player) -> float:
        """
        Check for reverse suji trap (opposite side of sequence)

        Example: Discarded 7-8, waiting for 9 (reverse of 3-6-9 suji)
        """
        if not tile.is_suit:
            return 0.0

        tile_value = (tile.type % 9) + 1
        suit_discards = [t for t in player.discards if t.type // 9 == tile.type // 9]
        discard_values = [(t.type % 9) + 1 for t in suit_discards]

        # Check for consecutive discards on edges
        # If they discarded 7-8, they might wait for 9 (reverse suji of 9-7-4)
        if 7 in discard_values and 8 in discard_values and tile_value == 9:
            return 0.4
        if 7 in discard_values and 8 in discard_values and tile_value == 6:
            return 0.5  # Waiting for 6 (middle of 4-6)
        if 2 in discard_values and 3 in discard_values and tile_value == 1:
            return 0.4
        if 2 in discard_values and 3 in discard_values and tile_value == 4:
            return 0.5

        # Check for edge patterns
        # If discarded 1-2, might wait for 3 (reverse suji)
        if 1 in discard_values and 2 in discard_values and tile_value == 3:
            return 0.3

        # If discarded 8-9, might wait for 7
        if 8 in discard_values and 9 in discard_values and tile_value == 7:
            return 0.3

        return 0.0

    def _check_kanchan_trap(self, tile: Tile, player) -> float:
        """
        Check for kanchan trap (single gap wait)

        Example: Discarded 2-4, waiting for 3 (kanchan wait)
        """
        if not tile.is_suit:
            return 0.0

        tile_value = (tile.type % 9) + 1
        suit_discards = [t for t in player.discards if t.type // 9 == tile.type // 9]
        discard_values = set((t.type % 9) + 1 for t in suit_discards)

        # Kanchan patterns: (n-2, n, n+1) waiting for n+1
        # Or (n-1, n, n+2) waiting for n
        # We check if they discarded tiles that form a kanchan pattern with our tile

        # Check if tile would complete a kanchan
        if tile_value in discard_values:
            # Check adjacent
            left = tile_value - 1
            right = tile_value + 1
            if left >= 1 and left in discard_values and right <= 9 and right in discard_values:
                return 0.6  # They have left-tile and right-tile, waiting for middle

            # Check if they have tile-2 and tile+1 (waiting for tile+2)
            if tile_value - 2 >= 1 and tile_value - 2 in discard_values and tile_value + 1 <= 9 and tile_value + 1 in discard_values:
                return 0.5

            # Check if they have tile-1 and tile+2 (waiting for tile)
            if tile_value - 1 >= 1 and tile_value - 1 in discard_values and tile_value + 2 <= 9 and tile_value + 2 in discard_values:
                return 0.5

        return 0.0

    def _is_dead_suji(self, tile: Tile, game_state) -> bool:
        """
        Check if a suji is "dead" (all tiles discarded or dead)

        Returns True if all tiles in the suji group are either:
        - All 4 copies discarded
        - Cannot be drawn (dead wall depleted)
        """
        if not tile.is_suit:
            return False

        tile_value = (tile.type % 9) + 1
        suji_group = (tile_value - 1) % 3

        # Get all tiles in this suji group
        suit_start = (tile.type // 9) * 9
        suji_tiles = []
        for i in range(9):
            if (i + 1) % 3 == suji_group % 3 or (i + 1) % 3 == (suji_group + 1) % 3:
                continue
            # Standard suji: 1-4-7, 2-5-8, 3-6-9
            actual_value = i + 1
            if actual_value % 3 == (suji_group + 1) % 3:
                suji_tiles.append(suit_start + i)

        # Check if all are dead
        all_dead = True
        for tile_type in suji_tiles:
            remaining = game_state.get_remaining_tile_count(tile_type)
            if remaining > 0:
                all_dead = False
                break

        return all_dead

    def estimate_opponent_hand_strength(self, player, game_state) -> Dict:
        """
        Estimate the strength of an opponent's hand

        Based on:
        - Discard patterns
        - Calls/pon declarations
        - Shanten estimate
        - Hand development stage

        Returns:
            Dictionary with:
            - estimated_shanten: Estimated shanten (0-8)
            - hand_strength: 0.0 to 1.0 scale
            - phase: 'early', 'building', 'tenpai', 'tenpai_waiting'
            - likely_yaku: List of possible yaku
            - threat_level: 'low', 'medium', 'high'
            - confidence: How confident we are in this estimate (0-1)
        """
        discards = player.discards
        turn = getattr(player, 'turn', game_state.turn_number)

        # Count recent discards
        recent_discards = discards[-5:] if len(discards) > 5 else discards

        # Analyze discard pattern
        pattern = self.analyze_discard_pattern(player)

        # Check for pon/call declarations
        calls = getattr(player, 'called_tiles', [])
        pons = [c for c in calls if c.get('type') == 'pon']

        # Calculate base shanten estimate
        base_shanten = 8  # Start with worst case

        # Adjust based on discards
        if len(discards) >= 10:
            base_shanten -= 3  # They've been playing for a while
        elif len(discards) >= 6:
            base_shanten -= 2
        elif len(discards) >= 3:
            base_shanten -= 1

        # Adjust based on what they discarded
        if pattern['terminal_honor_ratio'] > 0.5:
            base_shanten -= 1  # Discarding valuable tiles suggests building
        if pattern['early_terminals'] >= 3:
            base_shanten -= 2  # Strongly suggests tenpai

        # Adjust based on calls
        base_shanten -= len(pons) * 2  # Each pon reduces shanten

        # Check riichi
        if player.riichi_declared:
            estimated_shanten = 0
            phase = 'tenpai_waiting'
            hand_strength = 1.0
        else:
            estimated_shanten = max(0, min(8, base_shanten))
            phase = self._determine_phase(estimated_shanten, turn, pattern)
            hand_strength = self._calculate_hand_strength(estimated_shanten, pons, pattern)

        # Determine likely yaku
        likely_yaku = self._estimate_likely_yaku(player, pattern, pons)

        # Determine threat level
        threat_level = self._calculate_threat_level(
            estimated_shanten, hand_strength, player, game_state
        )

        # Calculate confidence
        confidence = self._calculate_confidence(pattern, turn, len(pons))

        return {
            'estimated_shanten': estimated_shanten,
            'hand_strength': hand_strength,
            'phase': phase,
            'likely_yaku': likely_yaku,
            'threat_level': threat_level,
            'confidence': confidence,
            'pon_count': len(pons),
            'suit_focus': self._identify_suit_focus(pattern)
        }

    def _determine_phase(self, shanten: int, turn: int, pattern: Dict) -> str:
        """Determine the development phase of opponent's hand"""
        if shanten == 0:
            return 'tenpai_waiting'
        elif shanten <= 2:
            return 'tenpai'
        elif turn >= 15 and pattern['terminal_honor_ratio'] > 0.4:
            return 'building'
        else:
            return 'early'

    def _calculate_hand_strength(self, shanten: int, pons: List,
                                  pattern: Dict) -> float:
        """Calculate hand strength score"""
        strength = 1.0 - (shanten / 8.0)  # Normalize to 0-1

        # Bonus for completed melds
        strength += len(pons) * 0.1

        # Bonus for defensive pattern (avoiding suits suggests good hand)
        if pattern['pattern_type'] == 'defensive':
            strength += 0.1

        return min(1.0, max(0.0, strength))

    def _estimate_likely_yaku(self, player, pattern: Dict,
                               pons: List) -> List[str]:
        """Estimate likely yaku based on discards and calls"""
        likely = []

        # Toitoi
        if len(pons) >= 3:
            likely.append('toitoi')
            likely.append('sananko')

        # Honitsu/Chinitsu
        if pattern['avoided_suits']:
            if len(pattern['avoided_suits']) >= 2:
                likely.append('honitsu')
            if pattern['terminal_honor_ratio'] < 0.2:
                likely.append('chinitsu')

        # Tanyao (all simples)
        if pattern['terminal_honor_ratio'] < 0.1:
            likely.append('tanyao')

        # Pinfu (if discarding honors/terminals but keeping simples)
        if pattern['honor_discard_count'] >= 2 and pattern['terminal_honor_ratio'] < 0.2:
            likely.append('pinfu')

        # Iipeiko
        if len(pons) >= 1:
            likely.append('iipeiko')

        return likely

    def _calculate_threat_level(self, shanten: int, strength: float,
                                 player, game_state) -> str:
        """Calculate threat level from opponent"""
        # High threat
        if shanten == 0 or strength > 0.8:
            return 'high'
        # Medium threat
        if shanten <= 2 or strength > 0.5:
            # Check position
            player_pos = self._get_player_position(player, game_state)
            if player_pos in ['dealer', 'first']:
                return 'high'
            return 'medium'
        # Low threat
        return 'low'

    def _get_player_position(self, player, game_state) -> str:
        """Get player position relative to dealer"""
        dealer_id = getattr(game_state, 'dealer_seat', 0)
        player_id = player.player_id

        if player_id == dealer_id:
            return 'dealer'

        # Calculate position (clockwise)
        distance = (player_id - dealer_id) % 4
        positions = {1: 'first', 2: 'second', 3: 'third'}
        return positions.get(distance, 'unknown')

    def _calculate_confidence(self, pattern: Dict, turn: int,
                              pon_count: int) -> float:
        """Calculate confidence in the estimate"""
        confidence = 0.3  # Base confidence

        # More discards = more confidence
        if pattern['total_discards'] >= 10:
            confidence += 0.3
        elif pattern['total_discards'] >= 5:
            confidence += 0.2

        # Calls give more confidence
        confidence += pon_count * 0.15

        # Clear pattern gives more confidence
        if pattern['pattern_type'] != 'unknown':
            confidence += 0.1

        # Late game more predictable
        if turn >= 15:
            confidence += 0.1

        return min(1.0, confidence)

    def _identify_suit_focus(self, pattern: Dict) -> Optional[str]:
        """Identify which suit the player is focusing on"""
        dist = pattern['suit_distribution']

        # Find suit with most discards
        max_suit = max(dist.items(), key=lambda x: x[1] if x[0] != 'honor' else 0)
        if max_suit[1] >= 3:
            return max_suit[0]

        return None

    def find_safe_discard_options(self, hand: List[Tile],
                                   game_state) -> List[Dict]:
        """
        Find and rank safe discard options from hand

        Returns list of tiles with safety information:
        - tile: The tile
        - safety_score: 0-100 (higher = safer)
        - danger_percentage: 0-100 (lower = safer)
        - safety_factors: List of factors contributing to safety
        - genbutsu: Boolean if tile is genbutsu
        - suji_safe: Boolean if suji is dead/safe
        - rimoteness: 0-8 distance from edge (higher = safer)
        """
        player = game_state.players[game_state.current_turn]
        options = []

        for tile in hand:
            if tile.just_drawn:
                # Just drawn tiles are always safe to discard
                options.append({
                    'tile': tile,
                    'safety_score': 100.0,
                    'danger_percentage': 0.0,
                    'safety_factors': ['just_drawn'],
                    'genbutsu': False,
                    'suji_safe': False,
                    'rimoteness': 0,
                    'recommendation': 'safe'
                })
                continue

            safety_score = 100.0
            safety_factors = []
            genbutsu = False
            suji_safe = False

            # Check genbutsu
            if any(t.type == tile.type for t in player.discards):
                genbutsu = True
                safety_score = 100.0
                safety_factors.append('genbutsu')

            # Calculate danger from each opponent
            max_danger = 0.0
            for other in game_state.players:
                if other.player_id == player.player_id:
                    continue

                # Base tile danger
                tile_danger = self.calculate_tile_danger(tile, other, game_state)

                # Suji trap danger
                suji_danger = self.calculate_suji_trap_danger(tile, other, game_state)

                # Get opponent threat level
                threat = self.estimate_opponent_hand_strength(other, game_state)

                # Combine dangers (weighted by threat)
                threat_multiplier = {
                    'high': 1.3,
                    'medium': 1.0,
                    'low': 0.7
                }.get(threat['threat_level'], 1.0)

                combined_danger = max(tile_danger, suji_danger) * threat_multiplier
                max_danger = max(max_danger, combined_danger)

                if combined_danger > 0.5:
                    safety_factors.append(f'threatening_opponent_{other.player_id}')

            if not genbutsu:
                safety_score = max(0.0, 100.0 - (max_danger * 100))

            # Check suji safety
            if tile.is_suit:
                dead_suji = self._is_dead_suji(tile, game_state)
                if dead_suji:
                    suji_safe = True
                    safety_factors.append('dead_suji')
                    safety_score = min(100.0, safety_score + 20)

            # Rimoteness (distance from edge)
            rimoteness = 0
            if tile.is_suit:
                idx = tile.type % 9
                rimoteness = min(idx, 8 - idx)  # 0-4, higher is safer (middle)

                # Bonus for rimote tiles
                if rimoteness >= 3:
                    safety_factors.append('rimote')
                    safety_score = min(100.0, safety_score + 10)
                elif rimoteness <= 1:
                    safety_factors.append('edge_tile')

            # Honor tiles bonus
            if tile.is_honor:
                safety_factors.append('honor_tile')
                if not genbutsu:
                    safety_score = min(100.0, safety_score + 15)

            # Generate recommendation
            if safety_score >= 80:
                recommendation = 'safe'
            elif safety_score >= 50:
                recommendation = 'caution'
            elif safety_score >= 20:
                recommendation = 'risky'
            else:
                recommendation = 'dangerous'

            options.append({
                'tile': tile,
                'safety_score': safety_score,
                'danger_percentage': 100.0 - safety_score,
                'safety_factors': safety_factors,
                'genbutsu': genbutsu,
                'suji_safe': suji_safe,
                'rimoteness': rimoteness,
                'recommendation': recommendation
            })

        # Sort by safety score (highest first)
        options.sort(key=lambda x: -x['safety_score'])

        return options

    def calculate_defensive_threat(self, player, game_state) -> Dict:
        """
        Calculate overall defensive threat from opponents

        Factors in:
        - Number of threatening opponents
        - Their positions relative to player
        - Their estimated hand strength
        - Score implications of their positions

        Returns:
            Dictionary with:
            - overall_threat_score: 0-100
            - threat_level: 'low', 'medium', 'high', 'critical'
            - primary_threats: List of player IDs sorted by threat
            - positional_danger: Dict of position -> danger level
            - recommended_defense: Suggested defense level
        """
        current_player_id = player.player_id
        threats = []

        for other in game_state.players:
            if other.player_id == current_player_id:
                continue

            # Estimate their hand strength
            strength = self.estimate_opponent_hand_strength(other, game_state)

            # Calculate positional threat
            position_threat = self._calculate_positional_threat(
                player, other, game_state
            )

            # Calculate score threat
            score_threat = self._calculate_score_threat(
                other, game_state
            )

            # Combine threats
            combined_threat = (
                strength['hand_strength'] * 40 +
                position_threat * 30 +
                score_threat * 30
            )

            threats.append({
                'player_id': other.player_id,
                'hand_strength': strength,
                'position_threat': position_threat,
                'score_threat': score_threat,
                'combined_threat': combined_threat,
                'is_riichi': other.riichi_declared,
                'is_dealer': other.is_dealer
            })

        # Sort by threat level
        threats.sort(key=lambda x: -x['combined_threat'])

        # Calculate overall threat
        if threats:
            overall_threat = max(t['combined_threat'] for t in threats)
            # Reduce if multiple players are threats (spread danger)
            threat_count = sum(1 for t in threats if t['combined_threat'] > 30)
            if threat_count >= 2:
                overall_threat *= 0.9  # Spread danger reduces individual threat
        else:
            overall_threat = 0.0

        # Determine threat level
        if overall_threat >= 80 or any(t['is_riichi'] for t in threats):
            threat_level = 'critical'
        elif overall_threat >= 60:
            threat_level = 'high'
        elif overall_threat >= 40:
            threat_level = 'medium'
        else:
            threat_level = 'low'

        # Calculate positional danger
        positional_danger = {}
        for i, threat in enumerate(threats[:4]):
            player_id = threat['player_id']
            distance = (player_id - current_player_id) % 4
            positional_danger[f'position_{distance}'] = threat['position_threat']

        # Determine recommended defense level
        recommended_defense = self._determine_defense_level(
            threat_level, threats, player, game_state
        )

        return {
            'overall_threat_score': overall_threat,
            'threat_level': threat_level,
            'primary_threats': [t['player_id'] for t in threats[:3]],
            'positional_danger': positional_danger,
            'recommended_defense': recommended_defense,
            'threat_details': threats,
            'riichi_count': sum(1 for t in threats if t['is_riichi']),
            'dealer_threat': any(t['is_dealer'] for t in threats)
        }

    def _calculate_positional_threat(self, player, other, game_state) -> float:
        """
        Calculate threat based on position relative to player

        Left (1 away) is most dangerous for defense
        """
        player_id = player.player_id
        other_id = other.player_id

        # Distance in clockwise direction
        distance = (other_id - player_id) % 4

        # Base threat by position
        position_threat = {
            1: 1.0,   # Left - most dangerous
            2: 0.7,   # Across
            3: 0.4    # Right - least dangerous
        }.get(distance, 0.5)

        # Adjust for riichi
        if other.riichi_declared:
            position_threat *= 1.5

        # Adjust for dealer position
        if other.is_dealer:
            position_threat *= 1.3

        return min(1.0, position_threat)

    def _calculate_score_threat(self, player, game_state) -> float:
        """Calculate threat based on score implications"""
        scores = game_state.get_player_scores()
        player_score = player.score

        # Calculate relative position
        sorted_scores = sorted(scores, reverse=True)
        rank = sorted_scores.index(player_score) + 1

        if player_score >= sorted_scores[0]:
            return 1.0  # Top scorer - threatening position
        elif rank == 2:
            return 0.7
        elif rank == 3:
            return 0.4
        else:
            return 0.3

    def _determine_defense_level(self, threat_level: str, threats: List,
                                 player, game_state) -> str:
        """Determine recommended defense level"""
        # Critical threat - maximum defense
        if threat_level == 'critical':
            return 'passive'

        # Check for riichi
        riichi_threats = [t for t in threats if t['is_riichi']]
        if riichi_threats:
            return 'passive'

        # Check for dealer threat
        dealer_threats = [t for t in threats if t['is_dealer']]
        if dealer_threats and dealer_threats[0]['combined_threat'] > 50:
            return 'passive'

        # High threat
        if threat_level == 'high':
            return 'moderate'

        # Medium threat
        if threat_level == 'medium':
            # Consider player position
            if player.score < 10000:
                return 'passive'  # Need to protect
            return 'moderate'

        # Low threat - can be aggressive
        return 'aggressive'

    def recommend_defensive_action(self, game_state) -> Dict:
        """
        Recommend the best defensive action based on game state

        Returns:
            Dictionary with:
            - action: 'aggressive', 'moderate', or 'passive'
            - reasoning: List of factors influencing decision
            - priority_tiles: Tiles to prioritize discarding
            - avoid_tiles: Tiles to avoid discarding
            - estimated_risk: Overall risk percentage
        """
        current_player = game_state.players[game_state.current_turn]

        # Calculate threat assessment
        threat = self.calculate_defensive_threat(current_player, game_state)

        # Analyze hand
        hand = current_player.hand
        safe_options = self.find_safe_discard_options(hand, game_state)

        # Calculate hand strength
        shanten = self.tile_analyzer.shanten_calc.calculate_shanten(hand)
        hand_strength = 1.0 - (shanten / 8.0) if shanten >= 0 else 1.0

        # Score position
        scores = game_state.get_player_scores()
        player_score = current_player.score
        last_place = player_score == min(scores)

        # Combine factors
        reasoning = []
        defense_score = 0.0

        # Factor 1: Threat level
        threat_weight = {
            'critical': 40,
            'high': 30,
            'medium': 20,
            'low': 10
        }
        defense_score += threat_weight.get(threat['threat_level'], 20)
        reasoning.append(f"Opponent threat: {threat['threat_level']}")

        # Factor 2: Hand strength
        if hand_strength < 0.3:
            defense_score += 20
            reasoning.append("Weak hand - prioritize defense")
        elif hand_strength > 0.7:
            defense_score -= 10
            reasoning.append("Strong hand - can be more aggressive")
        reasoning.append(f"Hand strength: {hand_strength:.0%}")

        # Factor 3: Score position
        if last_place:
            defense_score -= 15  # Need to win, can't play too safe
            reasoning.append("Last place - need to take risks")
        elif player_score > 30000:
            defense_score += 15
            reasoning.append("Comfortable score - play safe")
        reasoning.append(f"Player score: {player_score}")

        # Factor 4: Game phase
        remaining = game_state.deck.remaining
        if remaining < 20:
            defense_score += 10
            reasoning.append("Late game - play defensively")
        elif remaining > 100:
            reasoning.append("Early game - more options available")

        # Factor 5: Riichi declarations
        if threat['riichi_count'] > 0:
            defense_score += 20
            reasoning.append(f"{threat['riichi_count']} riichi(s) declared")

        # Factor 6: Safe tiles available
        safe_count = sum(1 for o in safe_options if o['recommendation'] == 'safe')
        if safe_count >= 3:
            reasoning.append(f"{safe_count} safe tiles available")
        elif safe_count == 0:
            defense_score += 10
            reasoning.append("No safe tiles - must accept some risk")

        # Determine action
        if defense_score >= 60:
            action = 'passive'
        elif defense_score >= 40:
            action = 'moderate'
        else:
            action = 'aggressive'

        # Calculate estimated risk
        if safe_options:
            avg_safety = sum(o['danger_percentage'] for o in safe_options) / len(safe_options)
            estimated_risk = min(100, avg_safety)
        else:
            estimated_risk = 50.0

        # Get priority and avoid tiles
        priority_tiles = [o['tile'] for o in safe_options[:3]]
        avoid_tiles = [o['tile'] for o in safe_options if o['danger_percentage'] > 60]

        return {
            'action': action,
            'reasoning': reasoning,
            'priority_tiles': priority_tiles,
            'avoid_tiles': avoid_tiles,
            'estimated_risk': estimated_risk,
            'defense_score': defense_score,
            'safe_discard_options': safe_options[:5],
            'threat_assessment': threat
        }


class StrategyPlanner:
    """
    Strategic decision making
    """

    def __init__(self):
        self.tile_analyzer = TileAnalyzer()
        self.defense_analyzer = DefenseAnalyzer()

    def analyze_game_phase(self, game_state) -> str:
        """
        Determine current game phase

        Returns: 'early', 'mid', or 'late'
        """
        turn = game_state.turn_number
        remaining = game_state.deck.remaining

        if remaining < 30 or turn > 60:
            return 'late'
        elif remaining < 70 or turn > 40:
            return 'mid'
        else:
            return 'early'

    def get_score_position(self, player, game_state) -> Tuple[str, float]:
        """
        Analyze player's score position

        Returns: (position, lead_amount)
        """
        scores = game_state.get_player_scores()
        player_score = player.score

        sorted_scores = sorted(scores, reverse=True)
        rank = sorted_scores.index(player_score) + 1

        avg_score = sum(scores) / len(scores)
        lead = player_score - avg_score

        if rank == 1 and lead > 10000:
            position = "dominant"
        elif rank == 1:
            position = "leading"
        elif rank == 2:
            position = "chasing"
        elif rank == 3:
            position = "behind"
        else:
            position = "last"

        return position, lead

    def adjust_strategy(self, player, game_state) -> Dict:
        """
        Determine strategic adjustments based on game state

        Returns dict with strategy weights
        """
        phase = self.analyze_game_phase(game_state)
        position, lead = self.get_score_position(player, game_state)

        strategy = {
            'offense_weight': 0.5,
            'defense_weight': 0.5,
            'aggression': 0.5,  # 0=passive, 1=aggressive
            'riichi_threshold': 0.6
        }

        # Adjust based on phase
        if phase == 'early':
            strategy['offense_weight'] = 0.7
            strategy['aggression'] = 0.4
        elif phase == 'mid':
            strategy['offense_weight'] = 0.5
            strategy['aggression'] = 0.5
        elif phase == 'late':
            strategy['offense_weight'] = 0.3
            strategy['aggression'] = 0.7

        # Adjust based on position
        if position == "dominant":
            strategy['defense_weight'] = 0.8
            strategy['aggression'] = 0.3
        elif position in ["chasing", "behind", "last"]:
            strategy['offense_weight'] = 0.7
            strategy['aggression'] = 0.7
            strategy['riichi_threshold'] = 0.4

        # Dealer adjustment
        if player.is_dealer:
            strategy['defense_weight'] *= 1.2

        return strategy

    def plan_hand_development(self, hand: List[Tile], game_state) -> Dict:
        """
        Plan hand development strategy

        Returns target yaku and development path
        """
        counts = tiles_to_counts(hand)
        analysis = self.tile_analyzer.analyze_hand_shape(hand)

        plan = {
            'target_yaku': [],
            'development_priority': 'balance',
            'riichi_viable': False
        }

        # Determine target yaku based on hand
        if analysis['shape_type'] == 'toitoi':
            plan['target_yaku'] = ['toitoi', 'honroku']
            plan['development_priority'] = 'pon'
        elif analysis['shape_type'] == 'honitsu':
            plan['target_yaku'] = ['honitsu']
        elif analysis['shape_type'] == 'chinitsu':
            plan['target_yaku'] = ['chinitsu']
        else:
            plan['target_yaku'] = ['tanyao', 'pinfu']

        # Check if riichi is viable
        shanten = self.shanten_calc.calculate_shanten(hand)
        if shanten == 0:
            waits = self.shanten_calc.get_wait_tiles(hand)
            quality = self.tile_analyzer.estimate_wait_quality(waits, game_state)
            plan['riichi_viable'] = quality >= 30

        return plan

    def calculate_target_score(self, game_state, player) -> int:
        """
        Determine what score is needed to achieve objectives

        Factors in:
        - Current score position and lead/distance to next player
        - Dealer position (oya) bonus
        - Game phase (early/mid/late)
        - Number of honba
        - Last place necessity

        Returns target score as integer
        """
        scores = game_state.get_player_scores()
        player_score = player.score
        sorted_scores = sorted(scores, reverse=True)
        player_rank = sorted_scores.index(player_score) + 1
        total_players = len(scores)

        # Base targets by position
        base_targets = {
            1: 30000,   # Top: maintain lead
            2: 35000,   # Second: catch up to first
            3: 25000,   # Third: secure position
            4: 30000    # Fourth (last): comeback target
        }

        # Starting point
        target = base_targets.get(player_rank, 30000)

        # Calculate distance to next position
        if player_rank == 1:
            # Leading: need to stay ahead by comfortable margin
            if sorted_scores[0] - sorted_scores[1] < 10000:
                target = max(target, sorted_scores[1] + 15000)
        elif player_rank == total_players:
            # Last place: need significant comeback
            first_score = sorted_scores[0]
            target = max(target, first_score - 10000)
        else:
            # Middle positions: target next position
            next_position_score = sorted_scores[player_rank - 2]  # player_rank is 1-indexed
            target = max(target, next_position_score + 5000)

        # Dealer bonus (oya can win smaller hands for more effective score)
        if player.is_dealer:
            target = int(target * 0.85)  # Dealer needs ~15% less raw points

        # Late game adjustment
        phase = self.analyze_game_phase(game_state)
        if phase == 'late':
            # Late game: smaller hands still matter, don't need huge targets
            target = int(target * 0.8)
        elif phase == 'early':
            # Early game: can aim higher since more time to achieve
            target = int(target * 1.1)

        # Honba bonus: stakes are raised
        honba = getattr(game_state, 'honba', 0)
        if honba > 0:
            target += honba * 1500 * (total_players - player_rank)

        # Ensure minimum viable target
        return max(8000, int(target))

    def analyze_opponent_positions(self, game_state, player_id: int) -> Dict:
        """
        Map all players' score positions and identify threats

        Returns dict with:
        - all_positions: List of {player_id, score, rank, position_type}
        - threats: Players to prioritize defending against
        - opportunities: Players who are vulnerable
        - threat_priority: Sorted list of player_ids by threat level
        """
        scores = game_state.get_player_scores()
        sorted_scores = sorted(scores, reverse=True)
        current_player_score = None

        # Find current player's score
        for p in game_state.players:
            if p.player_id == player_id:
                current_player_score = p.score
                break

        all_positions = []
        threats = []
        opportunities = []

        for p in game_state.players:
            if p.player_id == player_id:
                continue

            score = p.score
            rank = sorted_scores.index(score) + 1
            rank_score = score - sorted_scores[0]  # Distance from first

            # Determine position type
            if rank == 1:
                position_type = 'leader'
            elif rank == len(scores):
                position_type = 'last'
            elif rank_score > 5000:
                position_type = 'contender'
            else:
                position_type = 'close'

            player_info = {
                'player_id': p.player_id,
                'score': score,
                'rank': rank,
                'position_type': position_type,
                'is_dealer': p.is_dealer,
                'distance_from_first': -rank_score,
                'riichi_declared': p.riichi_declared
            }
            all_positions.append(player_info)

            # Classify as threat or opportunity
            if rank <= 2 and score > current_player_score:
                threats.append({
                    'player_id': p.player_id,
                    'reason': 'score_lead' if rank == 1 else 'close_contention',
                    'urgency': 1 if rank == 1 else 2
                })
            elif p.is_dealer and rank <= 2:
                threats.append({
                    'player_id': p.player_id,
                    'reason': 'dealer_threat',
                    'urgency': 1
                })
            elif rank >= 3 and score < current_player_score - 10000:
                opportunities.append({
                    'player_id': p.player_id,
                    'reason': 'vulnerable',
                    'potential': rank  # Lower rank = more vulnerable
                })

        # Sort threat priority: highest urgency first, then by score
        threat_priority = sorted(
            threats,
            key=lambda x: (x['urgency'], -next(
                (p['score'] for p in all_positions if p['player_id'] == x['player_id']
            ), 0))
        )
        threat_priority = [t['player_id'] for t in threat_priority]

        return {
            'all_positions': all_positions,
            'threats': threats,
            'opportunities': opportunities,
            'threat_priority': threat_priority,
            'player_count': len(scores),
            'score_spread': sorted_scores[0] - sorted_scores[-1]
        }

    def evaluate_riichi_timing(self, hand: List[Tile], game_state,
                                player) -> Dict:
        """
        Evaluate optimal timing for declaring riichi

        Considers:
        - Wait quality (number of tiles, wait type)
        - Opponent danger levels
        - Score position and stakes
        - Hand value (han/han)
        - Dead tile count

        Returns dict with:
        - recommendation: 'now', 'wait', 'never', 'aggressive'
        - confidence: 0.0 to 1.0
        - reasoning: List of factors
        - expected_value: Estimated point gain
        - wait_details: Information about current waits
        """
        # Check if already tenpai
        shanten = self.tile_analyzer.shanten_calc.calculate_shanten(hand)
        if shanten != 0:
            return {
                'recommendation': 'wait',
                'confidence': 0.0,
                'reasoning': ['Not yet tenpai'],
                'expected_value': 0,
                'wait_details': None
            }

        # Get wait information
        wait_analysis = self.tile_analyzer.analyze_wait_patterns(hand)
        waits = wait_analysis.get('tenpai_patterns', [])

        if not waits:
            return {
                'recommendation': 'never',
                'confidence': 1.0,
                'reasoning': ['No valid waits found'],
                'expected_value': 0,
                'wait_details': None
            }

        # Calculate wait quality score
        wait_quality = wait_analysis.get('wait_diversity', 0)
        wait_quality += self.tile_analyzer.estimate_wait_quality(
            [w['tile_type'] for w in waits],
            game_state
        )

        # Count remaining tiles in waits
        total_wait_tiles = sum(w['remaining'] for w in waits)
        avg_wait_tiles = total_wait_tiles / len(waits) if waits else 0

        # Calculate hand value estimate
        hand_value = self._estimate_hand_value(hand, game_state)

        # Calculate danger from opponents
        defense_analysis = self.defense_analyzer.calculate_defensive_threat(
            player, game_state
        )
        threat_level = defense_analysis['threat_level']

        # Calculate expected value
        base_points = hand_value * 1000
        win_probability = min(0.9, avg_wait_tiles / 10)

        # Adjust for danger
        if threat_level == 'critical':
            win_probability *= 0.5
        elif threat_level == 'high':
            win_probability *= 0.7
        elif threat_level == 'low':
            win_probability *= 0.9

        expected_value = base_points * win_probability

        # Determine recommendation
        reasoning = []
        score = 0

        # Factor 1: Wait quality (40% weight)
        if wait_quality >= 80:
            score += 40
            reasoning.append(f"Excellent wait quality ({wait_quality:.0f})")
        elif wait_quality >= 50:
            score += 25
            reasoning.append(f"Good wait quality ({wait_quality:.0f})")
        elif wait_quality >= 30:
            score += 10
            reasoning.append(f"Moderate wait quality ({wait_quality:.0f})")
        else:
            reasoning.append(f"Weak wait quality ({wait_quality:.0f})")

        # Factor 2: Hand value (30% weight)
        if hand_value >= 5:
            score += 30
            reasoning.append(f"High value hand ({hand_value} han)")
        elif hand_value >= 3:
            score += 20
            reasoning.append(f"Medium value hand ({hand_value} han)")
        elif hand_value >= 1:
            score += 10
            reasoning.append(f"Low value hand ({hand_value} han)")
        else:
            reasoning.append("Hand has minimal value")

        # Factor 3: Threat level (30% weight)
        if threat_level == 'low':
            score += 30
            reasoning.append("Low opponent threat")
        elif threat_level == 'medium':
            score += 15
            reasoning.append("Moderate opponent threat")
        elif threat_level == 'high':
            score += 5
            reasoning.append("High opponent threat")
        else:
            reasoning.append("Critical threat - riichi dangerous")

        # Make recommendation
        if score >= 70:
            recommendation = 'now'
            confidence = 0.8
        elif score >= 50:
            recommendation = 'now'
            confidence = 0.6
        elif score >= 30:
            recommendation = 'wait'
            confidence = 0.5
        elif threat_level == 'critical' or wait_quality < 20:
            recommendation = 'never'
            confidence = 0.7
        else:
            recommendation = 'wait'
            confidence = 0.4

        # Special case: desperation mode (last place, late game)
        position, _ = self.get_score_position(player, game_state)
        if position == 'last':
            phase = self.analyze_game_phase(game_state)
            if phase == 'late':
                if hand_value >= 2 or avg_wait_tiles >= 6:
                    recommendation = 'aggressive'
                    confidence = 0.7
                    reasoning.append("Desperation mode: must take riichi chance")

        return {
            'recommendation': recommendation,
            'confidence': confidence,
            'reasoning': reasoning,
            'expected_value': int(expected_value),
            'wait_details': {
                'wait_count': len(waits),
                'total_tiles': total_wait_tiles,
                'avg_tiles_per_wait': avg_wait_tiles,
                'wait_quality_score': wait_quality,
                'wait_types': wait_analysis.get('wait_types', {})
            },
            'hand_value_estimate': hand_value,
            'threat_level': threat_level,
            'timing_score': score
        }

    def _estimate_hand_value(self, hand: List[Tile], game_state) -> int:
        """Estimate hand value in han"""
        value = 0

        # Base yaku count
        counts = tiles_to_counts(hand)
        analysis = self.tile_analyzer.analyze_hand_shape(hand)

        # Count potential yaku
        if analysis['shape_type'] == 'honitsu':
            value += 3
        elif analysis['shape_type'] == 'chinitsu':
            value += 6
        elif analysis['shape_type'] == 'toitoi':
            value += 4

        # Dora check
        if hasattr(game_state, 'dora_indicators'):
            for indicator in game_state.dora_indicators:
                if self._is_next_tile_for_value(indicator.type, counts):
                    value += 1

        # Terminal/honor bonus
        terminals = sum(1 for i in TERMINALS if counts[i] > 0)
        honors = sum(1 for i in HONORS if counts[i] > 0)
        if terminals >= 4:
            value += 2
        if honors >= 3:
            value += 1

        # Pinfu potential
        if analysis['shape_type'] == 'normal' and terminals == 0 and honors == 0:
            value += 1

        return max(1, value)

    def _is_next_tile_for_value(self, indicator_type: int, counts: List[int]) -> bool:
        """Check if tile is dora (next after indicator)"""
        if 0 <= indicator_type <= 7:
            return counts[indicator_type + 1] > 0
        if indicator_type == 8:
            return counts[0] > 0
        if 9 <= indicator_type <= 16:
            return counts[indicator_type + 1] > 0
        if indicator_type == 17:
            return counts[9] > 0
        if 18 <= indicator_type <= 25:
            return counts[indicator_type + 1] > 0
        if indicator_type == 26:
            return counts[18] > 0
        return False

    def plan_yaku_strategy(self, hand: List[Tile], game_state) -> Dict:
        """
        Identify achievable yaku and plan hand development

        Returns dict with:
        - achievable_yaku: List of yaku that can be pursued
        - priority_order: Yaku sorted by value/difficulty ratio
        - dead_ends: Yaku to avoid (no good path)
        - recommended_path: Best strategy
        """
        counts = tiles_to_counts(hand)
        analysis = self.tile_analyzer.analyze_hand_shape(hand)

        achievable = []
        dead_ends = []

        # Check each potential yaku
        yaku_checks = [
            ('tanyao', self._check_tanyao_possible(counts)),
            ('pinfu', self._check_pinfu_possible(counts, hand)),
            ('chinitsu', self._check_chinitsu_possible(counts)),
            ('honitsu', self._check_honitsu_possible(counts)),
            ('toitoi', self._check_toitoi_possible(counts)),
            ('sananko', self._check_sananko_possible(counts)),
            ('ittsu', self._check_ittsu_possible(counts)),
            ('sanshoku', self._check_sanshoku_possible(counts))
        ]

        for yaku_name, result in yaku_checks:
            if result['possible']:
                achievable.append({
                    'yaku': yaku_name,
                    'han': result.get('han', 1),
                    'difficulty': result.get('difficulty', 5),
                    'value_ratio': result.get('han', 1) / max(result.get('difficulty', 5), 1),
                    'current_progress': result.get('progress', 0),
                    'requirements': result.get('requirements', [])
                })
            elif result.get('blocked', False):
                dead_ends.append({
                    'yaku': yaku_name,
                    'reason': result.get('reason', 'Unknown')
                })

        # Sort by value ratio (higher is better)
        achievable.sort(key=lambda x: -x['value_ratio'])

        # Determine recommended path
        if not achievable:
            recommended_path = {
                'strategy': 'flexible',
                'fallback': 'tanyao',
                'description': 'Keep hand flexible, aim for simple yaku'
            }
        else:
            top_yaku = achievable[0]
            if top_yaku['difficulty'] <= 2:
                recommended_path = {
                    'strategy': 'pursue',
                    'target': top_yaku['yaku'],
                    'description': f"Focus on {top_yaku['yaku']} ({top_yaku['han']} han)"
                }
            elif top_yaku['difficulty'] <= 4:
                recommended_path = {
                    'strategy': 'consider',
                    'target': top_yaku['yaku'],
                    'alternative': achievable[1]['yaku'] if len(achievable) > 1 else None,
                    'description': f"Work toward {top_yaku['yaku']} but stay flexible"
                }
            else:
                recommended_path = {
                    'strategy': 'flexible',
                    'fallback': achievable[0]['yaku'],
                    'description': 'Keep options open, build toward best available'
                }

        return {
            'achievable_yaku': achievable,
            'priority_order': [y['yaku'] for y in achievable],
            'dead_ends': dead_ends,
            'recommended_path': recommended_path,
            'hand_shape': analysis['shape_type']
        }

    def _check_tanyao_possible(self, counts: List[int]) -> Dict:
        """Check if tanyao is still achievable"""
        terminals = sum(counts[i] for i in TERMINALS)
        honors = sum(counts[i] for i in HONORS)
        if terminals > 0 or honors > 0:
            return {'possible': False, 'blocked': True, 'reason': 'Has terminals or honors'}
        return {'possible': True, 'han': 1, 'difficulty': 1, 'progress': 0.8}

    def _check_pinfu_possible(self, counts: List[int], hand: List[Tile]) -> Dict:
        """Check if pinfu is achievable"""
        terminals = sum(counts[i] for i in TERMINALS)
        honors = sum(counts[i] for i in HONORS)
        if terminals > 0 or honors > 0:
            return {'possible': False, 'blocked': True, 'reason': 'Needs simples only'}
        # Check for pair
        pairs = sum(1 for c in counts if c >= 2)
        if pairs != 1:
            return {'possible': False, 'blocked': False, 'reason': 'Needs exactly one pair'}
        return {'possible': True, 'han': 1, 'difficulty': 3, 'progress': 0.3}

    def _check_chinitsu_possible(self, counts: List[int]) -> Dict:
        """Check if chinitsu is achievable"""
        pin_count = sum(counts[0:9])
        sou_count = sum(counts[9:18])
        man_count = sum(counts[18:27])
        honor_count = sum(counts[27:34])

        if honor_count > 0:
            return {'possible': False, 'blocked': True, 'reason': 'Has honors'}
        active_suits = sum(1 for c in [pin_count, sou_count, man_count] if c > 0)
        if active_suits > 1:
            return {'possible': False, 'blocked': False, 'reason': 'Multiple suits active'}
        if active_suits == 1:
            main_suit = max(pin_count, sou_count, man_count)
            return {'possible': True, 'han': 6, 'difficulty': 7, 'progress': main_suit / 14}
        return {'possible': False, 'blocked': False, 'reason': 'No suit focus'}

    def _check_honitsu_possible(self, counts: List[int]) -> Dict:
        """Check if honitsu is achievable"""
        pin_count = sum(counts[0:9])
        sou_count = sum(counts[9:18])
        man_count = sum(counts[18:27])
        honor_count = sum(counts[27:34])

        if honor_count == 0:
            return {'possible': False, 'blocked': True, 'reason': 'Needs honors'}
        active_suits = sum(1 for c in [pin_count, sou_count, man_count] if c > 0)
        if active_suits > 1:
            return {'possible': False, 'blocked': False, 'reason': 'Multiple suits'}
        return {'possible': True, 'han': 3, 'difficulty': 4, 'progress': 0.5}

    def _check_toitoi_possible(self, counts: List[int]) -> Dict:
        """Check if toitoi is achievable"""
        pons = sum(c // 3 for c in counts)
        if pons >= 3:
            return {'possible': True, 'han': 4, 'difficulty': 5, 'progress': pons / 4}
        elif pons >= 2:
            return {'possible': True, 'han': 4, 'difficulty': 6, 'progress': pons / 4}
        return {'possible': False, 'blocked': False, 'reason': f'Only {pons} pons'}

    def _check_sananko_possible(self, counts: List[int]) -> Dict:
        """Check if sananko (three closed pons) is achievable"""
        pons = sum(c // 3 for c in counts)
        if pons >= 3:
            return {'possible': True, 'han': 2, 'difficulty': 7, 'progress': pons / 4}
        return {'possible': False, 'blocked': False, 'reason': f'Only {pons} closed pons'}

    def _check_ittsu_possible(self, counts: List[int]) -> Dict:
        """Check if itsu (pure straight) is achievable"""
        # Simplified check - look for sequence potential
        for suit_start in [0, 9, 18]:
            suit_counts = counts[suit_start:suit_start + 9]
            for i in range(7):
                seq_count = sum(suit_counts[i:i + 3])
                if seq_count >= 2:
                    return {'possible': True, 'han': 2, 'difficulty': 4, 'progress': 0.4}
        return {'possible': False, 'blocked': False, 'reason': 'No straight potential'}

    def _check_sanshoku_possible(self, counts: List[int]) -> Dict:
        """Check if sanshoku (mixed straight) is achievable"""
        # Check if we have tiles in all three suits that could form sequences
        for value in range(7):
            suits_with_tiles = 0
            for suit_start in [0, 9, 18]:
                if sum(counts[suit_start + value:suit_start + value + 3]) > 0:
                    suits_with_tiles += 1
            if suits_with_tiles >= 2:
                return {'possible': True, 'han': 2, 'difficulty': 5, 'progress': 0.3}
        return {'possible': False, 'blocked': False, 'reason': 'No mixed sequence potential'}

    def calculate_risk_tolerance(self, player, game_state) -> float:
        """
        Calculate risk tolerance based on game situation

        Returns risk level from 0.0 (very conservative) to 1.0 (very aggressive)

        Factors:
        - Score position (leading = conservative, behind = aggressive)
        - Game phase (early = moderate, late = polarized)
        - Dealer position (dealer more conservative)
        - Honba count (more honba = more conservative)
        - Last place desperation
        """
        phase = self.analyze_game_phase(game_state)
        position, lead = self.get_score_position(player, game_state)

        risk = 0.5  # Start neutral

        # Position adjustment
        if position == 'dominant':
            risk -= 0.3
        elif position == 'leading':
            risk -= 0.15
        elif position == 'chasing':
            risk += 0.1
        elif position == 'behind':
            risk += 0.2
        elif position == 'last':
            risk += 0.35
            # Last place desperation bonus
            scores = game_state.get_player_scores()
            sorted_scores = sorted(scores, reverse=True)
            first_score = sorted_scores[0]
            gap = first_score - player.score
            if gap > 20000:
                risk += 0.15  # Massive gap requires more risk

        # Phase adjustment
        if phase == 'early':
            risk += 0.05  # Early game allows some risk
        elif phase == 'mid':
            pass  # Neutral
        elif phase == 'late':
            # Late game polarizes risk
            if risk > 0.5:
                risk += 0.15  # Aggressive players get more aggressive
            else:
                risk -= 0.1   # Conservative players become more conservative

        # Dealer adjustment (dealer more conservative)
        if player.is_dealer:
            risk -= 0.1

        # Honba adjustment (high stakes = conservative)
        honba = getattr(game_state, 'honba', 0)
        if honba >= 3:
            risk -= 0.15
        elif honba >= 1:
            risk -= 0.05

        # Tsumo/ron consideration
        # If player tends toward tsumo, can be slightly more conservative
        recent_wins = getattr(player, 'recent_tsumo_ratio', 0.5)
        if recent_wins > 0.6:
            risk -= 0.05  # Can afford to wait for tsumo

        # Clamp to valid range
        return max(0.0, min(1.0, risk))

    def get_tactical_priority(self, game_state, player) -> str:
        """
        Determine tactical priority for current situation

        Returns one of:
        - 'offense': Maximize winning, push for hands
        - 'defense': Minimize losses, play safe
        - 'balance': Middle ground between offense and defense
        - 'desperation': High risk for comeback (last place, late game)
        """
        phase = self.analyze_game_phase(game_state)
        position, lead = self.get_score_position(player, game_state)
        risk_tolerance = self.calculate_risk_tolerance(player, game_state)

        # Check threat level
        threat = self.defense_analyzer.calculate_defensive_threat(player, game_state)
        threat_level = threat['threat_level']

        # Calculate hand strength
        hand = player.hand
        shanten = self.tile_analyzer.shanten_calc.calculate_shanten(hand)
        hand_strength = 1.0 - (shanten / 8.0) if shanten >= 0 else 1.0

        # Score tracking
        scores = game_state.get_player_scores()
        sorted_scores = sorted(scores, reverse=True)
        player_score = player.score
        player_rank = sorted_scores.index(player_score) + 1

        # Check for desperation (last place, large gap, late game)
        is_desperation = (
            position == 'last' and
            phase == 'late' and
            sorted_scores[0] - player_score > 15000
        )

        # Scoring logic
        offense_score = 0
        defense_score = 0

        # Factor 1: Position
        if position in ['behind', 'last']:
            offense_score += 3
        elif position in ['leading', 'dominant']:
            defense_score += 3

        # Factor 2: Hand strength
        if hand_strength > 0.7:
            offense_score += 2
        elif hand_strength < 0.3:
            defense_score += 2

        # Factor 3: Threat level
        if threat_level in ['high', 'critical']:
            defense_score += 3
        elif threat_level == 'low':
            offense_score += 2

        # Factor 4: Phase
        if phase == 'late':
            # Late game: position matters more
            if player_rank >= 3:
                offense_score += 2
            else:
                defense_score += 2
        elif phase == 'early':
            offense_score += 1  # Early game: build hands

        # Factor 5: Risk tolerance
        if risk_tolerance > 0.6:
            offense_score += 2
        elif risk_tolerance < 0.4:
            defense_score += 2

        # Factor 6: Honba
        honba = getattr(game_state, 'honba', 0)
        if honba >= 2:
            defense_score += 2

        # Desperation override
        if is_desperation:
            return 'desperation'

        # Determine priority
        if offense_score > defense_score + 2:
            return 'offense'
        elif defense_score > offense_score + 2:
            return 'defense'
        else:
            return 'balance'

    def get_strategy_summary(self, game_state, player) -> Dict:
        """
        Get comprehensive strategy summary for current game state

        Returns dict with all strategic information
        """
        phase = self.analyze_game_phase(game_state)
        position, lead = self.get_score_position(player, game_state)
        risk_tolerance = self.calculate_risk_tolerance(player, game_state)
        tactical_priority = self.get_tactical_priority(game_state, player)
        adjusted_strategy = self.adjust_strategy(player, game_state)
        target_score = self.calculate_target_score(game_state, player)
        opponent_analysis = self.analyze_opponent_positions(game_state, player.player_id)

        # Get riichi timing if hand is ready
        hand = player.hand
        riichi_eval = self.evaluate_riichi_timing(hand, game_state, player)
        yaku_plan = self.plan_yaku_strategy(hand, game_state)

        return {
            'game_phase': phase,
            'score_position': {
                'position': position,
                'lead': lead,
                'score': player.score
            },
            'risk_tolerance': risk_tolerance,
            'tactical_priority': tactical_priority,
            'strategy_weights': adjusted_strategy,
            'target_score': target_score,
            'opponent_analysis': opponent_analysis,
            'riichi_evaluation': riichi_eval,
            'yaku_plan': yaku_plan,
            'recommendations': self._generate_recommendations(
                phase, position, risk_tolerance, tactical_priority,
                adjusted_strategy, riichi_eval
            )
        }

    def _generate_recommendations(self, phase: str, position: str,
                                   risk_tolerance: float,
                                   tactical_priority: str,
                                   strategy: Dict,
                                   riichi_eval: Dict) -> List[str]:
        """Generate human-readable recommendations"""
        recommendations = []

        # Phase recommendation
        if phase == 'early':
            recommendations.append("Early game: Focus on building a strong hand")
        elif phase == 'mid':
            recommendations.append("Mid game: Evaluate position and adjust strategy")
        else:
            recommendations.append("Late game: Position matters more than hand value")

        # Position recommendation
        if position in ['leading', 'dominant']:
            recommendations.append("Play conservatively to maintain lead")
        elif position == 'last':
            recommendations.append("Take calculated risks to catch up")

        # Tactical priority
        priority_messages = {
            'offense': "Prioritize winning hands over safety",
            'defense': "Play defensively, prioritize safe discards",
            'balance': "Balance offense and defense based on situation",
            'desperation': "High risk needed - push for wins"
        }
        recommendations.append(priority_messages.get(tactical_priority, ''))

        # Risk tolerance
        if risk_tolerance > 0.6:
            recommendations.append("High risk tolerance - can pursue aggressive strategies")
        elif risk_tolerance < 0.4:
            recommendations.append("Low risk tolerance - prioritize safety")

        # Riichi recommendation
        if riichi_eval['recommendation'] == 'now':
            recommendations.append("RIICHI NOW: Strong timing for riichi declaration")
        elif riichi_eval['recommendation'] == 'wait':
            recommendations.append("Wait for better riichi timing")
        elif riichi_eval['recommendation'] == 'aggressive':
            recommendations.append("Consider riichi despite risks (desperation mode)")

        return recommendations
