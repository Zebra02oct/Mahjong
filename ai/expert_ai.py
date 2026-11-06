"""
Mahjong Riichi - Expert AI (Level 4)
Advanced AI with strategic play using all analyzers
Enhanced with comprehensive decision making
"""

from typing import List, Optional, Dict, Tuple
from core.tiles import Tile, tiles_to_counts
from core.shanten import ShantenCalculator
from engine.game_state import GameState
from ai.base_ai import BaseAI
from ai.ai_utils import TileAnalyzer, DefenseAnalyzer, StrategyPlanner


class ExpertAI(BaseAI):
    """
    Level 4 - Expert AI

    Features:
    - Tile value analysis with complexity scoring
    - Wait quality estimation with future potential
    - Defense with threat level integration
    - Strategic planning with score-aware play
    - Opponent modeling and prediction
    - Edge case handling (late game, dealer, desperation)
    """

    def __init__(self, player_id: int, difficulty: int = 4):
        super().__init__(player_id, difficulty)

        # Analyzers
        self.tile_analyzer = TileAnalyzer()
        self.defense_analyzer = DefenseAnalyzer()
        self.strategy_planner = StrategyPlanner()

        # Enhanced opponent models
        self.opponent_models = {
            i: {
                'tenpai_prob': 0.0,
                'estimated_shanten': 8,
                'discard_pattern': None,
                'hand_strength': 0.0,
                'threat_level': 'low',
                'likely_yaku': [],
                'suit_focus': None,
                'pattern_type': 'unknown'
            }
            for i in range(4) if i != player_id
        }

        # Track decision history for analysis
        self.decision_history = []

    def decide_discard(self, game_state: GameState) -> Tile:
        """
        Expert discard decision using all analyzers
        Integrates offense, defense, and strategic considerations
        """
        player = game_state.players[self.player_id]
        hand = player.hand

        # Filter available tiles
        available = [t for t in hand if not t.just_drawn]
        if not available:
            available = hand

        # Get strategy and tactical priority
        strategy = self.strategy_planner.adjust_strategy(player, game_state)
        tactical = self.strategy_planner.get_tactical_priority(game_state, player)

        # Get threat assessment for defense integration
        threat_assessment = self.defense_analyzer.calculate_defensive_threat(
            player, game_state
        )

        # Calculate score for each tile
        best_tile = None
        best_score = float('-inf')

        for tile in available:
            score = self._calculate_discard_score(
                tile, hand, game_state, strategy, tactical, threat_assessment
            )

            if score > best_score:
                best_score = score
                best_tile = tile

        # Record decision for analysis
        self._record_decision('discard', best_tile, best_score, game_state)

        return best_tile if best_tile else available[0]

    def _calculate_discard_score(self, tile: Tile, hand: List[Tile],
                                game_state: GameState,
                                strategy: Dict,
                                tactical: str,
                                threat_assessment: Dict) -> float:
        """
        Calculate comprehensive discard score with all factors
        """
        player = game_state.players[self.player_id]
        temp_hand = [t for t in hand if t != tile]

        # === OFFENSE SCORE ===
        offense_score = self._calculate_offense_score(
            tile, temp_hand, game_state
        )

        # === DEFENSE SCORE ===
        defense_score = self._calculate_defense_score(
            tile, player, game_state, threat_assessment
        )

        # === HAND COMPLEXITY FACTOR ===
        complexity_bonus = self._calculate_complexity_bonus(
            tile, hand, temp_hand
        )

        # === FUTURE WAIT QUALITY ===
        future_wait_score = self._calculate_future_wait_score(
            tile, temp_hand, game_state
        )

        # === STRATEGY WEIGHTS ===
        off_weight = strategy['offense_weight']
        def_weight = strategy['defense_weight']

        # Tactical adjustments
        if tactical == 'offense':
            off_weight += 0.2
            def_weight -= 0.2
        elif tactical == 'defense':
            off_weight -= 0.2
            def_weight += 0.2
        elif tactical == 'desperation':
            off_weight += 0.3
            def_weight -= 0.3

        # Phase adjustments
        phase = self.strategy_planner.analyze_game_phase(game_state)
        if phase == 'late':
            def_weight += 0.15
            off_weight -= 0.15
        elif phase == 'early':
            off_weight += 0.1
            def_weight -= 0.1

        # Threat level adjustment from opponent positions
        threat_level = threat_assessment.get('threat_level', 'low')
        if threat_level == 'critical':
            def_weight += 0.1
            off_weight -= 0.1
        elif threat_level == 'high':
            def_weight += 0.05
            off_weight -= 0.05

        # Position-based adjustments
        position, _ = self.strategy_planner.get_score_position(player, game_state)
        if position == 'last':
            off_weight += 0.1
            def_weight -= 0.1

        # Dealer adjustment
        if player.is_dealer:
            def_weight += 0.05
            off_weight -= 0.05

        # Riichi players prioritize defense
        if player.riichi_declared:
            off_weight = 0.1
            def_weight = 0.9

        # Normalize weights
        total_weight = off_weight + def_weight
        if total_weight > 0:
            off_weight /= total_weight
            def_weight /= total_weight

        # Calculate combined score
        total_score = (
            offense_score * off_weight +
            defense_score * def_weight +
            complexity_bonus +
            future_wait_score * 0.5
        )

        return total_score

    def _calculate_offense_score(self, tile: Tile, temp_hand: List[Tile],
                               game_state: GameState) -> float:
        """Calculate offensive component of discard score"""
        score = 0.0

        # === SHANTEN IMPROVEMENT ===
        shanten_improvement = self.tile_analyzer.calculate_shanten_improvement(
            tile, game_state.players[self.player_id].hand, game_state
        )
        score += shanten_improvement * 100

        # Current shanten
        current_shanten = self.shanten_calc.calculate_shanten(temp_hand)

        # === WAIT QUALITY ===
        if current_shanten == 0:
            waits = self.shanten_calc.get_wait_tiles(temp_hand)
            wait_quality = self.tile_analyzer.estimate_wait_quality(waits, game_state)
            score += wait_quality * 5
        elif current_shanten <= 1:
            # Close to tenpai - check potential
            wait_analysis = self.tile_analyzer.analyze_wait_patterns(temp_hand)
            score += wait_analysis.get('wait_diversity', 0) * 2

        # === TILE VALUE ===
        tile_value = self.tile_analyzer.calculate_tile_value(
            tile, temp_hand, game_state
        )
        score += tile_value

        # === MELD POTENTIAL ===
        meld_potential = self.tile_analyzer.evaluate_meld_potential(tile, temp_hand)
        score += meld_potential['overall_potential'] * 2

        # === DORA VALUE ===
        if self._is_dora_related(tile, game_state):
            score += 20

        # === FUTURE VALUE ===
        future_value = self.tile_analyzer.estimate_future_value(
            tile, temp_hand, game_state
        )
        score += future_value * 0.5

        # === HAND COMPLEXITY ===
        complexity = self.tile_analyzer.calculate_hand_complexity(temp_hand)
        score += complexity * 0.1

        # === PAIR PRESERVATION ===
        counts = tiles_to_counts(temp_hand)
        if counts[tile.type] == 2 and not tile.is_terminal:
            score -= 15  # Penalty for breaking a pair

        # === TERMINAL/HONOR HANDLING ===
        if tile.is_terminal and current_shanten > 2:
            score -= 10  # Terminals are harder to use
        if tile.is_honor and current_shanten > 3:
            score -= 5

        return score

    def _calculate_defense_score(self, tile: Tile, player,
                                game_state: GameState,
                                threat_assessment: Dict) -> float:
        """Calculate defensive component of discard score"""
        score = 100.0  # Base safe score

        # === TILE DANGER ===
        danger = self.defense_analyzer.calculate_tile_danger(tile, player, game_state)
        score -= danger * 100

        # === SAFE TILE ===
        safe_options = self.defense_analyzer.find_safe_discard_options(
            player.hand, game_state
        )
        for option in safe_options:
            if option['tile'] == tile:
                score += option['safety_score'] * 0.3
                break

        # === GENBUTSU ===
        if any(t.type == tile.type for t in player.discards):
            score += 40

        # === RIMOTENESS ===
        remaining = game_state.get_remaining_tile_count(tile.type)
        rimoteness = 1.0 - (remaining / 4)
        score += rimoteness * 20

        # === SUJI TRAP ===
        suji_danger = self.defense_analyzer.calculate_suji_trap_danger(
            tile, player, game_state
        )
        if suji_danger > 0.5:
            score -= 30

        # === OPPONENT THREATS ===
        total_tenpai_prob = sum(
            self.opponent_models[p.player_id]['tenpai_prob']
            for p in game_state.players
            if p.player_id != self.player_id
        )
        if total_tenpai_prob > 0.5:
            score += 20 * total_tenpai_prob
            if danger > 0.5:
                score -= 20

        # === POSITION THREAT INTEGRATION ===
        threat_level = threat_assessment.get('threat_level', 'low')
        if threat_level in ['high', 'critical']:
            if danger > 0.3:
                score -= 30

        # Primary threat position consideration
        for threat in threat_assessment.get('threat_details', []):
            if threat.get('position_threat', 0) > 0.8:
                # Left player (most dangerous) has high threat
                if danger > 0.2:
                    score -= 20

        # === PHASE ADJUSTMENT ===
        phase = self.strategy_planner.analyze_game_phase(game_state)
        if phase == 'late':
            if danger < 0.3:
                score += 20
            elif danger > 0.5:
                score -= 30

        # === HONOR/TERMINAL SAFETY ===
        if tile.is_honor:
            score += 15
        if tile.is_terminal and game_state.turn_number < 30:
            score -= 10

        return score

    def _calculate_complexity_bonus(self, tile: Tile, original_hand: List[Tile],
                                   temp_hand: List[Tile]) -> float:
        """
        Calculate how discarding this tile affects hand complexity/flexibility
        """
        original_complexity = self.tile_analyzer.calculate_hand_complexity(original_hand)
        after_complexity = self.tile_analyzer.calculate_hand_complexity(temp_hand)

        # Prefer keeping flexible hands (higher complexity)
        complexity_change = after_complexity - original_complexity

        # Bonus for maintaining flexibility
        if complexity_change > 5:
            return complexity_change * 2
        elif complexity_change < -10:
            return complexity_change * 3  # Penalize losing flexibility
        return 0

    def _calculate_future_wait_score(self, tile: Tile, temp_hand: List[Tile],
                                   game_state: GameState) -> float:
        """
        Consider future wait quality after discarding this tile
        """
        score = 0.0

        # If not at tenpai, consider future wait potential
        shanten = self.shanten_calc.calculate_shanten(temp_hand)

        if shanten > 0:
            counts = tiles_to_counts(temp_hand)

            # Check for good wait tiles in hand
            for wait_type in range(34):
                if counts[wait_type] >= 1:
                    remaining = game_state.get_remaining_tile_count(wait_type)
                    if remaining >= 3:
                        score += 2
                    elif remaining >= 2:
                        score += 1

        return score

    def decide_call(self, game_state: GameState, call_type: str,
                   tile: Tile) -> bool:
        """
        Expert call decisions with comprehensive evaluation
        """
        player = game_state.players[self.player_id]
        hand = player.hand

        # === RON ===
        if call_type == "ron":
            return self._should_ron(hand, tile, game_state)

        # === PON ===
        if call_type == "pon":
            return self._should_pon(hand, tile, game_state)

        # === CHI ===
        if call_type == "chi":
            return self._should_chi(hand, tile, game_state)

        # === KAN ===
        if call_type == "kan":
            return self._should_kan(hand, tile, game_state)

        return False

    def _should_ron(self, hand: List[Tile], tile: Tile,
                   game_state: GameState) -> bool:
        """
        Decide if to ron
        Considers: winning, furiten, hand value, opponent position
        """
        player = game_state.players[self.player_id]

        # Check if it wins
        temp_hand = hand + [tile]
        if not self.shanten_calc.is_agari(temp_hand):
            return False

        # Furiten check - NEVER ron when in furiten
        if player.furiten:
            return False

        # Calculate hand value
        hand_value = self._estimate_hand_value(temp_hand, game_state)

        # Get threat assessment
        threat = self.defense_analyzer.calculate_defensive_threat(player, game_state)
        threat_level = threat.get('threat_level', 'low')

        # Score position
        position, _ = self.strategy_planner.get_score_position(player, game_state)

        # High value hands: always ron
        if hand_value >= 5:
            return True

        # Low value but in danger: consider urgency
        if hand_value <= 2 and threat_level in ['high', 'critical']:
            riichi_count = threat.get('riichi_count', 0)
            if riichi_count > 0:
                return True  # Ron is urgent when someone is in riichi

        # Last place desperation: ron anything
        if position == 'last':
            return True

        # Default: ron if winning
        return True

    def _should_pon(self, hand: List[Tile], tile: Tile,
                   game_state: GameState) -> bool:
        """
        Decide if to pon
        Considers: pair breaking, terminal/honor value, shanten impact
        """
        player = game_state.players[self.player_id]

        # Can't pon after calling riichi
        if player.has_called_melds() or player.riichi_declared:
            return False

        # Check current shanten
        current_shanten = self.shanten_calc.calculate_shanten(hand)
        counts = tiles_to_counts(hand)

        # Pon of terminal/honor is usually good
        if tile.is_terminal or tile.is_honor:
            return current_shanten <= 4

        # Check if pon breaks a valuable pair
        if counts[tile.type] == 2:
            # Breaking a pair for pon - evaluate carefully
            remaining = game_state.get_remaining_tile_count(tile.type)
            if remaining >= 2:
                # Consider hand value
                if tile.is_terminal or tile.is_honor:
                    return True  # Terminal/honor pon is valuable
                # Consider shanten impact
                if current_shanten >= 2:
                    return True  # Far from tenpai, can afford to pon
                # Close to tenpai: be more conservative
                return False

        # Analyze hand shape
        hand_shape = self.tile_analyzer.analyze_hand_shape(hand)
        pairs = hand_shape['pairs']

        # Check opponent threat level
        threat = self.defense_analyzer.calculate_defensive_threat(
            player, game_state
        )
        if threat.get('threat_level') == 'critical':
            return False  # Don't open hand in critical danger

        # If far from tenpai, pon might be okay
        if current_shanten >= 2:
            return True

        return False

    def _should_chi(self, hand: List[Tile], tile: Tile,
                    game_state: GameState) -> bool:
        """
        Decide if to chi
        Considers: shanten, hand value, opening hand, position
        """
        player = game_state.players[self.player_id]

        # Chi opens hand - can't riichi
        if player.has_called_melds():
            return False

        current_shanten = self.shanten_calc.calculate_shanten(hand)

        # Check if chi helps with a good yaku
        if self._is_valuable_chi(hand, tile, game_state):
            return current_shanten >= 2

        # Position-based: last place, late game - take more chances
        position, _ = self.strategy_planner.get_score_position(player, game_state)
        phase = self.strategy_planner.analyze_game_phase(game_state)

        if position == 'last' and phase == 'late' and current_shanten >= 2:
            return True

        # Check if chi is for valuable tiles (terminals)
        if tile.is_terminal:
            return True

        # Only chi if very far from tenpai
        return current_shanten >= 3

    def _should_kan(self, hand: List[Tile], tile: Tile,
                   game_state: GameState) -> bool:
        """
        Decide if to kan
        Distinguishes between added kan and ankan
        """
        player = game_state.players[self.player_id]

        # Check if it wins immediately
        temp_hand = hand + [tile]
        if self.shanten_calc.is_agari(temp_hand):
            return True

        counts = tiles_to_counts(hand)

        # If we have 4 of a kind, this is an ankan opportunity
        if counts[tile.type] == 4:
            return self._should_ankaan(hand, tile, game_state)

        # For added kan (3 of a kind + tile), evaluate
        if counts[tile.type] == 3:
            return self._should_add_kan(hand, tile, game_state)

        return False

    def _should_add_kan(self, hand: List[Tile], tile: Tile,
                       game_state: GameState) -> bool:
        """
        Evaluate added kan (calling kan from 3 of a kind)
        """
        player = game_state.players[self.player_id]

        # Can't kan if already called riichi
        if player.riichi_declared:
            return False

        # Check if tile is dora related
        for indicator in game_state.dora_indicators:
            if self._is_next_tile(tile.type, indicator.type):
                return True  # Kan dora is valuable

        # Terminal/honor kan: good for yaku
        if tile.is_terminal or tile.is_honor:
            return True

        # Late game: avoid kan (reduces tsumo chance)
        phase = self.strategy_planner.analyze_game_phase(game_state)
        if phase == 'late':
            return False

        # Check shanten - don't kan if close to tenpai
        shanten = self.shanten_calc.calculate_shanten(hand)
        if shanten <= 1:
            return False

        return True

    def _should_ankaan(self, hand: List[Tile], tile: Tile,
                      game_state: GameState) -> bool:
        """
        Evaluate ankan (closed kan)
        """
        player = game_state.players[self.player_id]

        # Can't ankan after calling
        if player.has_called_melds():
            return False

        # Dora kan is almost always good
        for indicator in game_state.dora_indicators:
            if self._is_next_tile(tile.type, indicator.type):
                return True

        # Terminal/honor kan for yakuman potential
        if tile.is_terminal or tile.is_honor:
            return True

        # Late game: ankan is safe (closed hand)
        phase = self.strategy_planner.analyze_game_phase(game_state)
        if phase == 'late':
            return True

        # Consider if it helps with tenpai
        shanten = self.shanten_calc.calculate_shanten(hand)
        if shanten == 0:
            return False  # Don't disrupt tenpai

        return True

    def _is_valuable_chi(self, hand: List[Tile], tile: Tile,
                          game_state: GameState) -> bool:
        """Check if chi helps with valuable yaku"""
        counts = tiles_to_counts(hand)

        # Check if it helps with tanyao (all simples)
        if tile.is_simple:
            return True

        # Check if it helps with pinfu potential
        if not any(t.is_terminal or t.is_honor for t in hand):
            return True

        return False

    def _estimate_hand_value(self, hand: List[Tile],
                           game_state: GameState) -> int:
        """Estimate hand value in han"""
        value = 1
        counts = tiles_to_counts(hand)
        analysis = self.tile_analyzer.analyze_hand_shape(hand)

        # Hand shape value
        if analysis['shape_type'] == 'honitsu':
            value += 3
        elif analysis['shape_type'] == 'chinitsu':
            value += 6
        elif analysis['shape_type'] == 'toitoi':
            value += 4

        # Dora check
        for indicator in game_state.dora_indicators:
            if self._is_next_tile(indicator.type, counts):
                value += 1

        # Terminal/honor bonus
        terminals = sum(1 for i in range(34)
                      if i in [0, 8, 9, 17, 18, 26] and counts[i] > 0)
        honors = sum(1 for i in range(27, 34) if counts[i] > 0)
        if terminals >= 4:
            value += 2
        if honors >= 3:
            value += 1

        return max(1, value)

    def decide_riichi(self, game_state: GameState, tile: Tile) -> bool:
        """
        Expert riichi timing with score-aware decisions
        """
        player = game_state.players[self.player_id]

        # Basic checks
        if not player.can_declare_riichi():
            return False

        if not player.is_tenpai:
            return False

        # Use comprehensive riichi evaluation
        riichi_eval = self.strategy_planner.evaluate_riichi_timing(
            player.hand, game_state, player
        )

        # Get score position
        position, _ = self.strategy_planner.get_score_position(player, game_state)
        phase = self.strategy_planner.analyze_game_phase(game_state)

        # Score-aware decision
        if position == 'last' and phase == 'late':
            # Desperation mode: riichi even with lower quality
            if riichi_eval['expected_value'] > 0:
                return True
            return riichi_eval['wait_details']['total_tiles'] >= 6

        # Standard riichi decision based on timing evaluation
        if riichi_eval['recommendation'] in ['now', 'aggressive']:
            return True
        elif riichi_eval['recommendation'] == 'wait':
            # Consider waiting if hand value is high
            if riichi_eval['hand_value_estimate'] >= 4:
                return False
            return riichi_eval['wait_details']['total_tiles'] >= 8

        return False

    def update_opponent_model(self, game_state: GameState) -> None:
        """
        Update opponent models based on game state
        Tracks discard patterns, estimates shanten, predicts actions
        """
        for player in game_state.players:
            if player.player_id == self.player_id:
                continue

            model = self.opponent_models[player.player_id]

            # Update tenpai probability
            tenpai_prob = self.defense_analyzer.estimate_tenpai_probability(
                player, game_state
            )
            model['tenpai_prob'] = (
                model['tenpai_prob'] * 0.7 + tenpai_prob * 0.3
            )

            # Update hand strength analysis
            strength = self.defense_analyzer.estimate_opponent_hand_strength(
                player, game_state
            )
            model['estimated_shanten'] = strength['estimated_shanten']
            model['hand_strength'] = strength['hand_strength']
            model['threat_level'] = strength['threat_level']
            model['likely_yaku'] = strength['likely_yaku']
            model['suit_focus'] = strength.get('suit_focus')

            # Update discard pattern
            pattern = self.defense_analyzer.analyze_discard_pattern(player)
            model['discard_pattern'] = pattern
            model['pattern_type'] = pattern.get('pattern_type', 'unknown')

            # Riichi = definitely tenpai
            if player.riichi_declared:
                model['tenpai_prob'] = 1.0
                model['estimated_shanten'] = 0
                model['hand_strength'] = 1.0

    def get_opponent_threat(self, opponent_id: int) -> Dict:
        """
        Get threat information for a specific opponent
        """
        return self.opponent_models.get(opponent_id, {})

    def predict_opponent_discard(self, opponent_id: int) -> List[int]:
        """
        Predict likely discards for an opponent based on their pattern
        """
        model = self.opponent_models.get(opponent_id, {})
        pattern = model.get('discard_pattern')

        if not pattern:
            return []

        # Return tiles they're likely to discard (potential waits)
        return pattern.get('potential_waits', [])

    def _handle_late_game(self, player, game_state: GameState) -> Dict:
        """
        Special handling for late game decisions
        """
        remaining = game_state.deck.remaining
        phase = 'late' if remaining < 30 else 'mid'

        # Last tiles: prioritize tsumo over ron
        if remaining < 15:
            return {
                'priority': 'tsumo',
                'aggression': 0.8,
                'reason': 'Last tiles - prioritize tsumo'
            }

        # Riichi threats: be more defensive
        riichi_count = sum(
            1 for p in game_state.players
            if p.player_id != self.player_id and p.riichi_declared
        )
        if riichi_count > 0:
            return {
                'priority': 'defense',
                'aggression': 0.3,
                'reason': f'{riichi_count} riichi(s) active'
            }

        return {
            'priority': 'balance',
            'aggression': 0.5,
            'reason': 'Normal late game'
        }

    def _handle_dealer_tactics(self, player, game_state: GameState) -> Dict:
        """
        Special handling for dealer position
        """
        position, _ = self.strategy_planner.get_score_position(player, game_state)

        # Dealer should be more conservative
        base_aggression = 0.4 if player.is_dealer else 0.5

        # Adjust based on position
        if position in ['dominant', 'leading']:
            base_aggression = 0.3  # Protect lead as dealer
        elif position in ['behind', 'last']:
            base_aggression = 0.6  # Need to catch up

        return {
            'aggression': base_aggression,
            'dealer_bonus': 0.2,
            'defense_priority': player.is_dealer
        }

    def _handle_desperation_plays(self, player, game_state: GameState) -> Dict:
        """
        Handle last place desperation situations
        """
        scores = game_state.get_player_scores()
        sorted_scores = sorted(scores, reverse=True)
        player_score = player.score
        first_score = sorted_scores[0]

        gap = first_score - player_score
        position, _ = self.strategy_planner.get_score_position(player, game_state)
        phase = self.strategy_planner.analyze_game_phase(game_state)

        is_desperation = (
            position == 'last' and
            (phase == 'late' or gap > 15000)
        )

        if not is_desperation:
            return {
                'desperation': False,
                'aggression_modifier': 0
            }

        # Desperation adjustments
        aggression_mod = 0.3
        if gap > 30000:
            aggression_mod = 0.4
        elif gap > 20000:
            aggression_mod = 0.35

        return {
            'desperation': True,
            'aggression_modifier': aggression_mod,
            'gap': gap,
            'take_ron_chances': True,
            'push_for_yaku': True
        }

    def _record_decision(self, decision_type: str, tile: Optional[Tile],
                         score: float, game_state: GameState) -> None:
        """Record decision for analysis"""
        self.decision_history.append({
            'type': decision_type,
            'tile': tile,
            'score': score,
            'turn': game_state.turn_number,
            'shanten': self.shanten_calc.calculate_shanten(
                game_state.players[self.player_id].hand
            )
        })

        # Keep only last 50 decisions
        if len(self.decision_history) > 50:
            self.decision_history = self.decision_history[-50:]

    def get_strategy_info(self, game_state: GameState) -> Dict:
        """Get comprehensive strategy information for current state"""
        player = game_state.players[self.player_id]

        return self.strategy_planner.get_strategy_summary(game_state, player)

    def get_strategy_summary(self, game_state: GameState) -> Dict:
        """
        Get comprehensive strategy summary for debugging/logging
        """
        player = game_state.players[self.player_id]
        hand = player.hand

        # Get all analysis
        phase = self.strategy_planner.analyze_game_phase(game_state)
        position, lead = self.strategy_planner.get_score_position(player, game_state)
        strategy = self.strategy_planner.adjust_strategy(player, game_state)
        threat = self.defense_analyzer.calculate_defensive_threat(player, game_state)
        riichi_eval = self.strategy_planner.evaluate_riichi_timing(hand, game_state, player)
        yaku_plan = self.strategy_planner.plan_yaku_strategy(hand, game_state)

        # Special situation handlers
        late_game = self._handle_late_game(player, game_state)
        dealer_tactics = self._handle_dealer_tactics(player, game_state)
        desperation = self._handle_desperation_plays(player, game_state)

        return {
            'game_phase': phase,
            'score_position': position,
            'lead': lead,
            'strategy_weights': strategy,
            'threat_level': threat['threat_level'],
            'riichi_timing': riichi_eval,
            'yaku_plan': yaku_plan,
            'late_game': late_game,
            'dealer_tactics': dealer_tactics,
            'desperation': desperation,
            'opponent_models': {
                pid: {
                    'tenpai_prob': model['tenpai_prob'],
                    'shanten': model['estimated_shanten'],
                    'threat_level': model['threat_level']
                }
                for pid, model in self.opponent_models.items()
            }
        }

    def reset_history(self) -> None:
        """Reset decision history and opponent models"""
        self.decision_history = []
        for pid in self.opponent_models:
            self.opponent_models[pid] = {
                'tenpai_prob': 0.0,
                'estimated_shanten': 8,
                'discard_pattern': None,
                'hand_strength': 0.0,
                'threat_level': 'low',
                'likely_yaku': [],
                'suit_focus': None,
                'pattern_type': 'unknown'
            }

    def _is_dora_related(self, tile: Tile, game_state: GameState) -> bool:
        """Check if tile is related to dora"""
        for indicator in game_state.dora_indicators:
            if self._is_next_tile(tile.type, indicator.type):
                return True
        return False

    def _is_next_tile(self, tile_type: int, indicator_type: int) -> bool:
        """Check if tile is next after indicator"""
        if 0 <= indicator_type <= 8:
            return tile_type == (0 if indicator_type == 8 else indicator_type + 1)
        if 9 <= indicator_type <= 17:
            return tile_type == (9 if indicator_type == 17 else indicator_type + 1)
        if 18 <= indicator_type <= 26:
            return tile_type == (18 if indicator_type == 26 else indicator_type + 1)
        return False
