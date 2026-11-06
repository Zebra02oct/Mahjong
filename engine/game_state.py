"""
Mahjong Riichi - Game State Manager
Manages the complete game state with full Phase 2 features
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from core.tiles import Tile, tiles_to_counts
from core.deck import Deck, create_standard_deck
from core.meld import Meld
from core.shanten import ShantenCalculator
from core.yaku import YakuContext, YakuDetector
from core.score import ScoreCalculator
from core.constants import (
    STARTING_SCORE, EAST, SOUTH, WEST, NORTH,
    DEAD_WALL_INDEX, DORA_INDICATOR_COUNT
)
from engine.player import Player


@dataclass
class GameAction:
    """Represents a game action"""
    player_id: int
    action_type: str  # "discard", "pon", "chi", "kan", "ron", "tsumo", "ankan"
    tile: Optional[Tile] = None
    target_tile: Optional[Tile] = None


@dataclass
class WinResult:
    """Result of a winning hand"""
    winner_id: int
    winning_tile: Tile
    is_tsumo: bool
    score: int
    yaku_names: List[str]
    han: int
    fu: int
    is_yakuman: bool
    is_double_riichi: bool = False
    is_ippatsu: bool = False


class GameState:
    """
    Manages the complete Mahjong game state

    Phase 2 Features:
    - Complete turn system with cycle tracking
    - Pon/Chi/Kan call system
    - Ron detection with priority
    - Ankan (concealed kan) support
    - Riichi with Ippatsu tracking
    - Double Riichi detection
    - Round/Honba management
    - Draw/Exhaustion handling
    """

    def __init__(self, player_names: List[str] = None, seed: int = None):
        # Create players
        if player_names is None:
            player_names = ["East", "South", "West", "North"]

        self.players: List[Player] = [
            Player(player_id=i, name=name, seat_wind=i)
            for i, name in enumerate(player_names)
        ]

        # First player is dealer
        self.players[0].is_dealer = True

        # Create deck
        self.deck = create_standard_deck(seed=seed)

        # Turn management
        self.current_turn: int = 0
        self.dealer_seat: int = 0
        self.turn_number: int = 0
        self.cycle_number: int = 0  # Number of times we've gone around

        # Round info
        self.round_number: int = 1  # East 1, East 2, etc.
        self.honba: int = 0  # Consecutive rounds without win
        self.riichi_sticks: int = 0  # Riichi bets

        # Discard pile
        self.discard_pile: List[Tile] = []
        self.last_discarded_tile: Optional[Tile] = None
        self.last_discarded_by: Optional[int] = None

        # Dora
        self.dora_indicators: List[Tile] = []
        self.uradora_indicators: List[Tile] = []  # Hidden dora (after riichi)

        # Riichi state
        self.riichi_declared: Set[int] = set()
        self.ippatsu_active: bool = False  # Ippatsu is valid this turn
        self.cycle_started: bool = False  # Track if kan happened this cycle

        # Game status
        self.game_over: bool = False
        self.winner: Optional[int] = None
        self.draw_reason: Optional[str] = None

        # Call state
        self.pending_calls: Dict[str, any] = {}
        self.call_window_active: bool = False
        self.call_tile: Optional[Tile] = None
        self.call_from_player: Optional[int] = None

        # Ankan state
        self.ankan_available: bool = False
        self.ankan_tile: Optional[Tile] = None

        # Shanten calculator
        self.shanten_calc = ShantenCalculator()
        self.yaku_detector = YakuDetector()
        self.score_calc = ScoreCalculator()

    # =========================================================================
    # GAME SETUP
    # =========================================================================

    def start_new_round(self) -> None:
        """Start a new round"""
        # Reset deck
        self.deck.reset()

        # Reset player hands
        for player in self.players:
            player.hand = []
            player.called_melds = []
            player.discards = []
            player.riichi_declared = False
            player.riichi_tile = None
            player.is_tenpai = False
            player.furiten = False
            player.last_drawn_tile = None

        # Clear discard pile
        self.discard_pile = []
        self.last_discarded_tile = None
        self.last_discarded_by = None

        # Reveal initial dora
        self.dora_indicators = []
        self.uradora_indicators = []
        self._reveal_dora()

        # Reset round state
        self.riichi_declared = set()
        self.ippatsu_active = False
        self.cycle_started = False
        self.call_window_active = False
        self.call_tile = None
        self.call_from_player = None
        self.ankan_available = False
        self.ankan_tile = None

        # First turn is dealer
        self.current_turn = self.dealer_seat
        self.turn_number = 0
        self.cycle_number = 0

    def deal_initial_hands(self) -> None:
        """Deal 13 tiles to each player"""
        for i in range(4):
            player = self.players[i]
            for _ in range(13):
                tiles = self.deck.draw(1)
                if tiles:
                    player.hand.extend(tiles)

        # Sort all hands
        for player in self.players:
            player.sort_hand()

        # Check for tenpai on initial hand (rare but possible)
        for player in self.players:
            player.check_tenpai()

    # =========================================================================
    # TURN MANAGEMENT
    # =========================================================================

    def get_current_player(self) -> Player:
        """Get the current player"""
        return self.players[self.current_turn]

    def is_first_turn(self) -> bool:
        """Check if this is the first turn of the round"""
        # First turn is when current_turn == dealer_seat AND turn_number == 0
        return self.current_turn == self.dealer_seat and self.turn_number == 0

    def next_turn(self) -> None:
        """Move to next player's turn"""
        self.current_turn = (self.current_turn + 1) % 4
        self.turn_number += 1

        # Track cycle (complete round)
        if self.current_turn == self.dealer_seat:
            self.cycle_number += 1

        # Reveal dora every cycle (after first)
        if self.cycle_number > 0:
            self._reveal_dora()

        # Reset ippatsu at start of new cycle
        if self.current_turn == self.dealer_seat:
            self.ippatsu_active = False
            self.cycle_started = False

    def draw_tile(self, player_id: int) -> Optional[Tile]:
        """Draw a tile for a player"""
        player = self.players[player_id]
        tiles = self.deck.draw(1)

        if tiles:
            tile = tiles[0]
            player.draw_tile(tile)
            return tile

        return None

    def discard_tile(self, player_id: int, tile: Tile) -> None:
        """Player discards a tile"""
        player = self.players[player_id]
        player.discard_tile(tile)

        # Update discard pile
        self.discard_pile.append(tile)
        self.last_discarded_tile = tile
        self.last_discarded_by = player_id

        # Invalidate ippatsu on any discard (unless declared riichi this turn)
        if not player.riichi_declared:
            self.ippatsu_active = False

        # Check for tenpai
        if len(player.hand) == 13:
            player.check_tenpai()

        # Mark ippatsu as active if riichi was just declared
        if player.riichi_declared:
            self.ippatsu_active = True

    # =========================================================================
    # ANKAN (CONCEALED KAN)
    # =========================================================================

    def check_ankan_available(self, player_id: int) -> List[Tile]:
        """Check if player has any ankan available"""
        player = self.players[player_id]
        counts = tiles_to_counts(player.hand)

        available = []
        for tile_type in range(34):
            if counts[tile_type] >= 4:
                # Check if it's a valid ankan (not in melds)
                in_meld = False
                for meld in player.called_melds:
                    if tile_type in [t.type for t in meld.tiles]:
                        in_meld = True
                        break
                if not in_meld:
                    available.append(Tile(tile_type))

        return available

    def declare_ankan(self, player_id: int, tile_type: int) -> Optional[Meld]:
        """Declare ankan (concealed kan from hand)"""
        player = self.players[player_id]

        # Remove 4 tiles from hand
        tiles_removed = []
        for tile in player.hand[:]:
            if tile.type == tile_type and len(tiles_removed) < 4:
                tiles_removed.append(tile)
                player.hand.remove(tile)

        if len(tiles_removed) == 4:
            meld = Meld(
                type="kan",
                tiles=tiles_removed,
                from_discards=False,
                caller_seat=player_id
            )
            player.add_meld(meld)

            # Draw replacement
            replacement = self.deck.draw_kandora()
            if replacement:
                player.draw_tile(replacement)

            # Reveal dora
            self._reveal_dora()

            # Ankan breaks ippatsu
            self.ippatsu_active = False
            self.cycle_started = True

            return meld

        return None

    # =========================================================================
    # CALLS (PON, CHI, KAN)
    # =========================================================================

    def can_call_discard(self, tile: Tile, from_player: int) -> Dict[int, List[str]]:
        """Check which players can call on a discarded tile"""
        calls = {}

        for player in self.players:
            if player.player_id == from_player:
                continue

            # Can't call after riichi
            if player.riichi_declared:
                continue

            available = player.get_callable_actions(tile)
            if available:
                calls[player.player_id] = available

        return calls

    def check_ron_candidates(self, tile: Tile, from_player: int) -> List[int]:
        """Check which players can ron on this tile"""
        candidates = []

        for player in self.players:
            if player.player_id == from_player:
                continue

            # Can't ron if in furiten
            if player.furiten:
                continue

            # Can't ron if already riichi (they'll declare themselves)
            # Actually, riichi players CAN ron

            # Check if this would complete their hand
            temp_hand = player.get_all_tiles() + [tile]
            counts = tiles_to_counts(temp_hand)
            if self.shanten_calc._check_agari(counts):
                candidates.append(player.player_id)

        return candidates

    def process_call(self, player_id: int, call_type: str) -> Optional[Meld]:
        """Process a call (pon, chi, kan)"""
        player = self.players[player_id]
        tile = self.call_tile

        if tile is None:
            return None

        if call_type == "pon":
            return self._process_pon(player, tile, player_id)
        elif call_type == "chi":
            return self._process_chi(player, tile, player_id)
        elif call_type == "kan":
            return self._process_daimin_kan(player, tile, player_id)

        return None

    def _process_pon(self, player: Player, tile: Tile, player_id: int) -> Optional[Meld]:
        """Process pon call"""
        tiles = [tile]
        for t in player.hand[:]:
            if t.type == tile.type and len(tiles) < 3:
                tiles.append(t)
                player.hand.remove(t)

        if len(tiles) == 3:
            meld = Meld(
                type="pon",
                tiles=tiles,
                from_discards=True,
                called_tile=tile,
                caller_seat=player_id
            )
            player.add_meld(meld)
            self._clear_call_window()
            return meld
        return None

    def _process_chi(self, player: Player, tile: Tile, player_id: int) -> Optional[Meld]:
        """Process chi call"""
        # Only next player can chi
        expected_player = (self.call_from_player + 1) % 4
        if player_id != expected_player:
            return None

        tiles = [tile]
        counts = tiles_to_counts(player.hand)
        tile_type = tile.type

        # Determine suit
        if 0 <= tile_type <= 8:
            suit_range = list(range(0, 9))
        elif 9 <= tile_type <= 17:
            suit_range = list(range(9, 18))
        elif 18 <= tile_type <= 26:
            suit_range = list(range(18, 27))
        else:
            return None  # Honors can't chi

        value = tile_type - suit_range[0]

        # Find valid chi pattern
        for low_val, mid_val in [
            (value - 2, value - 1),
            (value - 1, value + 1),
            (value + 1, value + 2),
        ]:
            if 0 <= low_val <= 8 and 0 <= mid_val <= 8:
                low_type = suit_range[low_val]
                mid_type = suit_range[mid_val]

                if counts[low_type] >= 1 and counts[mid_type] >= 1:
                    tiles = [tile, Tile(low_type), Tile(mid_type)]

                    # Remove from hand
                    removed = 0
                    for t in player.hand[:]:
                        if removed < 2:
                            if t.type == low_type or t.type == mid_type:
                                if removed == 0 and t.type == low_type:
                                    player.hand.remove(t)
                                    removed += 1
                                elif removed == 1 and t.type == mid_type:
                                    player.hand.remove(t)
                                    removed += 1

                    if removed == 2:
                        meld = Meld(
                            type="chi",
                            tiles=tiles,
                            from_discards=True,
                            called_tile=tile,
                            caller_seat=player_id
                        )
                        player.add_meld(meld)
                        self._clear_call_window()
                        return meld

        return None

    def _process_daimin_kan(self, player: Player, tile: Tile, player_id: int) -> Optional[Meld]:
        """Process daimin kan (added kan from pon)"""
        tiles = [tile]
        for t in player.hand[:]:
            if t.type == tile.type and len(tiles) < 4:
                tiles.append(t)
                player.hand.remove(t)

        if len(tiles) == 4:
            meld = Meld(
                type="kan",
                tiles=tiles,
                from_discards=True,
                called_tile=tile,
                caller_seat=player_id
            )
            player.add_meld(meld)

            # Draw replacement
            replacement = self.deck.draw_kandora()
            if replacement:
                player.draw_tile(replacement)

            self._reveal_dora()
            self._clear_call_window()

            # Kan breaks ippatsu
            self.ippatsu_active = False
            self.cycle_started = True

            return meld

        return None

    def _reveal_dora(self) -> None:
        """Reveal a dora indicator"""
        if len(self.dora_indicators) < 5:
            indicators = self.deck.get_dora_indicators(count=len(self.dora_indicators) + 1)
            if len(indicators) > len(self.dora_indicators):
                self.dora_indicators = indicators

    def _clear_call_window(self) -> None:
        """Clear the call window"""
        self.call_window_active = False
        self.call_tile = None
        self.call_from_player = None

    # =========================================================================
    # WIN DETECTION
    # =========================================================================

    def check_win(self, player_id: int, tile: Tile, is_tsumo: bool = False) -> Optional[WinResult]:
        """Check if a player has won"""
        player = self.players[player_id]

        # Get all tiles
        all_tiles = player.get_all_tiles()

        # For tsumo, add the drawn tile
        if is_tsumo:
            all_tiles.append(tile)

        # Check if winning
        counts = tiles_to_counts(all_tiles)
        if not self.shanten_calc._check_agari(counts):
            return None

        # Create yaku context
        is_double_riichi = self.is_first_turn() and player.riichi_declared
        is_ippatsu = player.riichi_declared and self.ippatsu_active

        context = YakuContext(
            is_menzen=player.is_menzen(),
            is_tsumo=is_tsumo,
            is_riichi=player.riichi_declared,
            is_ippatsu=is_ippatsu,
            is_dealer=player.is_dealer,
            dora_count=len(self.dora_indicators),
            called_melds=player.called_melds
        )

        # Detect yaku
        yaku_list = self.yaku_detector.detect(all_tiles, context)

        if not yaku_list:
            return None

        # Calculate fu
        fu = self.score_calc.calculate_fu(all_tiles, yaku_list, context)

        # Calculate score
        score_result = self.score_calc.calculate(yaku_list, fu, player.is_dealer, is_tsumo)

        return WinResult(
            winner_id=player_id,
            winning_tile=tile,
            is_tsumo=is_tsumo,
            score=score_result.total_score,
            yaku_names=[y.name for y in yaku_list],
            han=score_result.han,
            fu=score_result.fu,
            is_yakuman=score_result.is_yakuman,
            is_double_riichi=is_double_riichi,
            is_ippatsu=is_ippatsu
        )

    # =========================================================================
    # RICHI MANAGEMENT
    # =========================================================================

    def declare_riichi(self, player_id: int, tile: Tile) -> bool:
        """Declare riichi"""
        player = self.players[player_id]

        if not player.can_declare_riichi():
            return False

        if not player.is_tenpai:
            return False

        if player.score < 1000:
            return False

        player.declare_riichi(tile)
        self.riichi_declared.add(player_id)
        self.riichi_sticks += 1

        return True

    def is_double_riichi(self, player_id: int) -> bool:
        """Check if this is a double riichi"""
        return self.is_first_turn() and self.players[player_id].riichi_declared

    # =========================================================================
    # ROUND MANAGEMENT
    # =========================================================================

    def handle_win(self, win_result: WinResult) -> None:
        """Handle end of round after a win"""
        winner = self.players[win_result.winner_id]

        # Pay winner - subtract from each payer first, then add to winner
        if win_result.is_tsumo:
            # Tsumo: all players pay their share
            for p in self.players:
                if p.player_id != win_result.winner_id:
                    payment = self._calculate_tsumo_payment(win_result, p.is_dealer)
                    p.score -= payment
        else:
            # Ron: only the discarder pays
            loser_id = self.last_discarded_by
            self.players[loser_id].score -= win_result.score

        # Winner receives the total
        winner.score += win_result.score

        # Add riichi bets back to winner
        winner.score += self.riichi_sticks * 1000

        # Update honba
        if winner.is_dealer:
            self.honba += 1
        else:
            self.honba = 0

        self.game_over = True
        self.winner = win_result.winner_id

    def _calculate_tsumo_payment(self, win_result: WinResult, is_dealer: bool) -> int:
        """Calculate tsumo payment"""
        # Simplified: just divide by 3 (or 2 for dealer)
        if is_dealer:
            return win_result.score // 2
        else:
            return win_result.score // 4

    def next_round(self) -> bool:
        """
        Advance to next round
        Returns True if game continues, False if game ends
        """
        # Rotate dealer
        self.dealer_seat = (self.dealer_seat + 1) % 4
        self.players[self.dealer_seat].is_dealer = True

        # Update round number
        self.round_number += 1
        if self.round_number > 4:
            # Game ends after East round
            self.game_over = True
            return False

        # Reset for new round
        self.start_new_round()
        self.deal_initial_hands()

        return True

    def handle_exhaustion(self) -> None:
        """Handle draw by tile exhaustion"""
        self.game_over = True
        self.draw_reason = "Tile exhaustion - draw game"

        # No one wins, honba increases
        self.honba += 1

    # =========================================================================
    # DORA
    # =========================================================================

    def count_dora(self, tile: Tile) -> int:
        """Count dora for a tile"""
        count = 0
        for indicator in self.dora_indicators:
            if self._is_dora(tile.type, indicator.type):
                count += 1
        return count

    def _is_dora(self, tile_type: int, indicator_type: int) -> bool:
        """Check if a tile is dora"""
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

    # =========================================================================
    # GAME INFO
    # =========================================================================

    def get_player_scores(self) -> List[int]:
        """Get all player scores"""
        return [p.score for p in self.players]

    def get_player_discards(self, player_id: int) -> List[Tile]:
        """Get discards of a specific player"""
        return self.players[player_id].discards

    def get_all_discards(self) -> List[Tile]:
        """Get all discards"""
        return self.discard_pile

    def get_remaining_tile_count(self, tile_type: int) -> int:
        """Get remaining count of a tile type"""
        return self.deck.get_remaining_count(tile_type)

    def get_hand_counts(self, player_id: int) -> List[int]:
        """Get tile counts for a player's hand"""
        return self.players[player_id].get_hand_counts()

    def get_state_summary(self) -> str:
        """Get a summary of the current game state"""
        lines = []
        lines.append("=" * 50)
        lines.append(f"Round {self.round_number}, Honba {self.honba}")
        lines.append(f"Turn {self.turn_number}, Cycle {self.cycle_number}")
        lines.append(f"Current: Player {self.current_turn}")
        lines.append(f"Dora: {[d.name for d in self.dora_indicators]}")
        lines.append("-" * 50)

        for player in self.players:
            wind_symbol = ["E", "S", "W", "N"][player.seat_wind]
            dealer_mark = " [DEALER]" if player.is_dealer else ""
            riichi_mark = " [R]" if player.riichi_declared else ""
            tenpai_mark = " [T]" if player.is_tenpai else ""
            lines.append(f"{player.name}[{wind_symbol}] Score: {player.score}{dealer_mark}{riichi_mark}{tenpai_mark}")

        lines.append("=" * 50)
        return "\n".join(lines)


def create_new_game(player_names: List[str] = None, seed: int = None) -> GameState:
    """Factory function to create a new game"""
    game = GameState(player_names=player_names, seed=seed)
    game.start_new_round()
    game.deal_initial_hands()
    return game
