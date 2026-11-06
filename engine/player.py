"""
Mahjong Riichi - Player Class
Represents a player in the game
"""

from dataclasses import dataclass, field
from typing import List, Optional
from core.tiles import Tile, tiles_to_counts, sort_tiles
from core.meld import Meld, MELD_PON, MELD_CHI, MELD_KAN
from core.constants import STARTING_SCORE, EAST, SOUTH, WEST, NORTH


@dataclass
class Player:
    """
    Represents a Mahjong player

    Attributes:
        player_id: Unique identifier
        name: Display name
        seat_wind: Seat wind (0=East, 1=South, 2=West, 3=North)
        hand: Tiles in hand
        score: Current game score
        is_ai: Whether this is an AI player
        ai_level: AI difficulty (1-3)
        called_melds: Melds called from discards
        discards: Tiles discarded
        riichi_declared: Whether riichi has been declared
        is_tenpai: Whether hand is in tenpai state
        furiten: Whether player is in furiten (can't ron on known tiles)
    """
    player_id: int
    name: str
    seat_wind: int = EAST

    # Game state
    hand: List[Tile] = field(default_factory=list)
    score: int = STARTING_SCORE
    is_ai: bool = False
    ai_level: int = 1
    ai_class: Optional[object] = None  # Reference to AI class

    # Meld state
    called_melds: List[Meld] = field(default_factory=list)

    # Discard state
    discards: List[Tile] = field(default_factory=list)
    riichi_declared: bool = False
    riichi_tile: Optional[Tile] = None

    # Status
    is_tenpai: bool = False
    furiten: bool = False
    is_dealer: bool = False

    # Turn state
    can_pon: bool = False
    can_chi: bool = False
    can_kan: bool = False
    can_ron: bool = False
    last_drawn_tile: Optional[Tile] = None

    def __post_init__(self):
        if self.name is None:
            self.name = f"Player {self.player_id}"

    # =========================================================================
    # HAND MANAGEMENT
    # =========================================================================

    def draw_tile(self, tile: Tile) -> None:
        """Add a drawn tile to hand"""
        tile.just_drawn = True
        self.hand.append(tile)
        self.last_drawn_tile = tile

    def discard_tile(self, tile: Tile) -> None:
        """
        Remove a tile from hand and add to discards

        Args:
            tile: Tile to discard

        Raises:
            ValueError: If tile not in hand or is just drawn
        """
        if tile.just_drawn:
            # Can always discard just-drawn tile
            pass

        if tile not in self.hand:
            raise ValueError(f"Tile {tile} not in hand")

        self.hand.remove(tile)
        tile.just_drawn = False
        tile.is_guarded = True  # Can't ron on this immediately
        self.discards.append(tile)
        self.last_drawn_tile = None

    def add_meld(self, meld: Meld) -> None:
        """Add a called meld"""
        self.called_melds.append(meld)

    def get_all_tiles(self) -> List[Tile]:
        """Get all tiles including called melds"""
        tiles = self.hand.copy()
        for meld in self.called_melds:
            tiles.extend(meld.tiles)
        return tiles

    def get_hand_counts(self) -> List[int]:
        """Get tile count array for hand"""
        return tiles_to_counts(self.get_all_tiles())

    def sort_hand(self) -> None:
        """Sort hand tiles for display"""
        self.hand = sort_tiles(self.hand, by="suit")

    # =========================================================================
    # STATUS CHECKS
    # =========================================================================

    def has_called_melds(self) -> bool:
        """Check if player has called any melds"""
        return len(self.called_melds) > 0

    def is_menzen(self) -> bool:
        """Check if hand is menzen (no calls)"""
        return len(self.called_melds) == 0

    def can_call_pon(self, tile: Tile) -> bool:
        """Check if can call pon on this tile"""
        counts = tiles_to_counts(self.hand)
        tile_type = tile.type

        # Need 2 of the same tile in hand
        return counts[tile_type] >= 2

    def can_call_chi(self, tile: Tile) -> bool:
        """Check if can call chi on this tile"""
        if self.has_called_melds():
            return False  # Can't chi after calling

        # Check if tile allows chi
        if not tile.is_suit:
            return False

        counts = tiles_to_counts(self.hand)
        tile_type = tile.type

        # Determine suit and check for sequences
        if 0 <= tile_type <= 8:  # Pin
            suit_range = list(range(0, 9))
        elif 9 <= tile_type <= 17:  # Sou
            suit_range = list(range(9, 18))
        else:  # Man
            suit_range = list(range(18, 27))

        value = tile_type - suit_range[0]  # 0-8

        # Check three possible chi patterns
        can_chi = False

        # Low tile: can form (value-2, value-1, value) if value >= 2
        if value >= 2:
            low = suit_range[value - 2]
            mid = suit_range[value - 1]
            if counts[low] >= 1 and counts[mid] >= 1:
                can_chi = True

        # Middle tile: can form (value-1, value, value+1) if 1 <= value <= 7
        if 1 <= value <= 7:
            mid = tile_type
            high = suit_range[value + 1]
            low = suit_range[value - 1]
            if counts[low] >= 1 and counts[high] >= 1:
                can_chi = True

        # High tile: can form (value, value+1, value+2) if value <= 6
        if value <= 6:
            low = tile_type
            mid = suit_range[value + 1]
            high = suit_range[value + 2]
            if counts[mid] >= 1 and counts[high] >= 1:
                can_chi = True

        return can_chi

    def can_call_kan(self, tile: Tile) -> bool:
        """Check if can call kan (added kan) on this tile"""
        counts = tiles_to_counts(self.hand)
        tile_type = tile.type

        # Need 3 of the same tile in hand
        return counts[tile_type] >= 3

    def can_call_kan_from_hand(self, tile_type: int) -> bool:
        """Check if can call kan from hand (concealed kan)"""
        counts = tiles_to_counts(self.hand)
        return counts[tile_type] >= 4

    def get_callable_actions(self, tile: Tile, is_just_drawn: bool = False) -> List[str]:
        """
        Get list of callable actions for a tile

        Args:
            tile: The tile to check
            is_just_drawn: Whether this is the just-drawn tile

        Returns:
            List of action names: ["pon"], ["chi"], ["ron"], etc.
        """
        actions = []

        # Can't call on own discard
        if is_just_drawn:
            return actions

        # Check ron (unless in furiten)
        if not self.furiten:
            actions.append("ron")

        # Check pon
        if self.can_call_pon(tile):
            actions.append("pon")

        # Check chi
        if self.can_call_chi(tile):
            actions.append("chi")

        # Check kan (added kan)
        if self.can_call_kan(tile):
            actions.append("kan")

        return actions

    # =========================================================================
    # RICHI / TENPAI
    # =========================================================================

    def can_declare_riichi(self) -> bool:
        """Check if player can declare riichi"""
        if self.riichi_declared:
            return False
        if self.has_called_melds():
            return False
        if self.score < 1000:
            return False
        if self.is_tenpai:
            return True
        return False

    def declare_riichi(self, tile: Tile) -> None:
        """Declare riichi"""
        self.riichi_declared = True
        self.riichi_tile = tile
        self.score -= 1000  # Bet

    def check_tenpai(self) -> bool:
        """Check if hand is in tenpai state"""
        from core.shanten import ShantenCalculator

        if len(self.hand) != 13:
            return False

        calc = ShantenCalculator()
        self.is_tenpai = calc.is_tenpai(self.hand)
        return self.is_tenpai

    def update_furiten(self, discards: List[Tile]) -> None:
        """
        Update furiten status based on discards

        Furiten: Can't ron on tiles you have discarded
        """
        if self.is_tenpai:
            for discard in self.discards:
                for tile in discards:
                    if tile.type == discard.type:
                        self.furiten = True
                        break

    # =========================================================================
    # DISPLAY
    # =========================================================================

    def get_display_name(self) -> str:
        """Get display name with seat wind"""
        winds = ["E", "S", "W", "N"]
        return f"{self.name}[{winds[self.seat_wind]}]"

    def get_hand_string(self) -> str:
        """Get string representation of hand"""
        tiles = sort_tiles(self.hand.copy(), by="suit")
        return " ".join(t.unicode for t in tiles)

    def get_discard_string(self) -> str:
        """Get string representation of discards"""
        return " ".join(t.unicode for t in self.discards)

    def __str__(self) -> str:
        return f"{self.get_display_name()} Score: {self.score}"

    def __repr__(self) -> str:
        return f"Player({self.player_id}, {self.name}, wind={self.seat_wind}, score={self.score})"
