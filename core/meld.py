"""
Mahjong Riichi - Meld Detection
Handles detection of melds (pon, chi, kan) in a hand
"""

from dataclasses import dataclass
from typing import List, Optional, Set
from core.tiles import Tile, tiles_to_counts
from core.constants import (
    MELD_PON, MELD_CHI, MELD_KAN,
    PIN_RANGE, SOU_RANGE, MAN_RANGE
)


@dataclass
class Meld:
    """
    Represents a meld (set of 3 or 4 tiles)

    Types:
    - pon: 3 identical tiles (e.g., 🀙🀙🀙)
    - chi: 3 consecutive tiles of same suit (e.g., 1-2-3 pin)
    - kan: 4 identical tiles (e.g., 🀙🀙🀙🀙)
    """
    type: str  # "pon", "chi", "kan"
    tiles: List[Tile]
    from_discards: bool = False  # True if called from discards (open meld)
    called_tile: Optional[Tile] = None  # The tile that was called
    caller_seat: Optional[int] = None  # Seat that called this meld

    @property
    def is_concealed(self) -> bool:
        """Check if this is a concealed meld (not called from discards)"""
        return not self.from_discards

    @property
    def is_menzen(self) -> bool:
        """Alias for is_concealed"""
        return self.is_concealed

    @property
    def is_open(self) -> bool:
        """Check if this is an open meld"""
        return self.from_discards

    def __repr__(self) -> str:
        tile_strs = [t.unicode for t in self.tiles]
        source = "open" if self.from_discards else "closed"
        return f"Meld({self.type}, {tile_strs}, {source})"


def detect_melds(tiles: List[Tile], include_kans: bool = True) -> List[List[Tile]]:
    """
    Detect all possible melds in a hand

    Args:
        tiles: List of tiles to check
        include_kans: Whether to include kans (4-tile melds)

    Returns:
        List of possible melds (each is a list of 3 or 4 tiles)
    """
    counts = tiles_to_counts(tiles)
    melds = []

    # Detect Pons (3 identical)
    for tile_type in range(34):
        if counts[tile_type] >= 3:
            pon_tiles = [Tile(tile_type) for _ in range(3)]
            melds.append(pon_tiles)

    # Detect Chis (3 consecutive, same suit)
    for suit_ranges in [PIN_RANGE, SOU_RANGE, MAN_RANGE]:
        for i in range(7):  # 0-6 for 1-7 start points
            for offset in range(3):
                idx = suit_ranges[i + offset]
                if counts[idx] < 1:
                    break
            else:
                # All three tiles exist
                chi_tiles = [Tile(suit_ranges[i]),
                            Tile(suit_ranges[i + 1]),
                            Tile(suit_ranges[i + 2])]
                melds.append(chi_tiles)

    # Detect Kans (4 identical)
    if include_kans:
        for tile_type in range(34):
            if counts[tile_type] >= 4:
                kan_tiles = [Tile(tile_type) for _ in range(4)]
                melds.append(kan_tiles)

    return melds


def detect_pon(tile_type: int, counts: List[int]) -> Optional[List[Tile]]:
    """
    Detect if a pon can be formed from tile counts

    Args:
        tile_type: The tile type to check
        counts: Tile count array (34 elements)

    Returns:
        List of 3 tiles forming a pon, or None
    """
    if counts[tile_type] >= 3:
        return [Tile(tile_type) for _ in range(3)]
    return None


def detect_chi(tile_type: int, counts: List[int]) -> List[List[Tile]]:
    """
    Detect all possible chis that include the given tile

    Args:
        tile_type: The tile type to check
        counts: Tile count array (34 elements)

    Returns:
        List of possible chi combinations (each is list of 3 tiles)
    """
    chis = []

    # Determine suit and value
    if 0 <= tile_type <= 8:  # Pin
        suit_range = PIN_RANGE
    elif 9 <= tile_type <= 17:  # Sou
        suit_range = SOU_RANGE
    elif 18 <= tile_type <= 26:  # Man
        suit_range = MAN_RANGE
    else:
        return []  # Honors can't form chi

    value = tile_type - suit_range[0]  # 0-8 index

    # Check three possible chi patterns:
    # 1. If tile is the lowest (0): can form 0-1-2
    if value >= 2:
        low = suit_range[value - 2]
        mid = suit_range[value - 1]
        high = tile_type
        if counts[low] >= 1 and counts[mid] >= 1:
            chis.append([Tile(low), Tile(mid), Tile(high)])

    # 2. If tile is middle: can form -1,0,+1
    if value >= 1 and value <= 7:
        low = tile_type
        mid = suit_range[value + 1]
        high = suit_range[value + 2]
        if counts[mid] >= 1 and counts[high] >= 1:
            chis.append([Tile(low), Tile(mid), Tile(high)])

    # 3. If tile is highest (8): can form -2,-1,0
    if value <= 6:
        low = tile_type
        mid = suit_range[value + 1]
        high = suit_range[value + 2]
        if counts[mid] >= 1 and counts[high] >= 1:
            chis.append([Tile(low), Tile(mid), Tile(high)])

    return chis


def can_form_pon(tile_type: int, counts: List[int]) -> bool:
    """Check if a pon can be formed"""
    return counts[tile_type] >= 3


def can_form_chi(tile_type: int, counts: List[int]) -> bool:
    """Check if any chi can be formed with this tile"""
    return len(detect_chi(tile_type, counts)) > 0


def can_form_kan(tile_type: int, counts: List[int]) -> bool:
    """Check if a kan can be formed"""
    return counts[tile_type] >= 4


def can_call(tile_type: int, counts: List[int], call_type: str = "any") -> bool:
    """
    Check what calls are available for a given tile

    Args:
        tile_type: The tile type to check
        counts: Current tile counts
        call_type: "pon", "chi", "kan", or "any"

    Returns:
        True if the call is possible
    """
    if call_type == "pon" or call_type == "any":
        if can_form_pon(tile_type, counts):
            return True

    if call_type == "chi" or call_type == "any":
        if can_form_chi(tile_type, counts):
            return True

    if call_type == "kan" or call_type == "any":
        if can_form_kan(tile_type, counts):
            return True

    return False


def get_available_calls(tile_type: int, counts: List[int]) -> List[str]:
    """
    Get all available call types for a tile

    Args:
        tile_type: The tile type to check
        counts: Current tile counts

    Returns:
        List of available call types: ["pon"], ["chi"], ["pon", "chi"], etc.
    """
    calls = []

    if can_form_pon(tile_type, counts):
        calls.append("pon")

    if can_form_chi(tile_type, counts):
        calls.append("chi")

    if can_form_kan(tile_type, counts):
        calls.append("kan")

    return calls


def can_ron(tile_type: int, hand_counts: List[int]) -> bool:
    """
    Check if a tile can complete a winning hand (ron)

    Args:
        tile_type: The discarded tile
        hand_counts: Current hand tile counts

    Returns:
        True if adding this tile would complete the hand
    """
    # Temporarily add the tile
    temp_counts = hand_counts.copy()
    temp_counts[tile_type] += 1

    # Check if hand can form 4 melds + 1 pair
    # This is a simplified check - proper check uses shanten calculator
    from core.shanten import ShantenCalculator
    calc = ShantenCalculator()
    return calc.is_agari(temp_counts)


class MeldDetector:
    """
    Advanced meld detection utility
    """

    def __init__(self):
        self.shanten_calc = None  # Lazy loaded

    def find_all_melds(self, tiles: List[Tile]) -> List[Meld]:
        """
        Find all valid melds in a hand

        Returns:
            List of Meld objects
        """
        melds = []
        counts = tiles_to_counts(tiles)

        # Pons
        for tile_type in range(34):
            if counts[tile_type] >= 3:
                meld = Meld(
                    type=MELD_PON,
                    tiles=[Tile(tile_type) for _ in range(3)],
                    from_discards=False
                )
                melds.append(meld)

        # Chis
        for suit_range in [PIN_RANGE, SOU_RANGE, MAN_RANGE]:
            for i in range(7):
                t1, t2, t3 = suit_range[i], suit_range[i + 1], suit_range[i + 2]
                if counts[t1] >= 1 and counts[t2] >= 1 and counts[t3] >= 1:
                    meld = Meld(
                        type=MELD_CHI,
                        tiles=[Tile(t1), Tile(t2), Tile(t3)],
                        from_discards=False
                    )
                    melds.append(meld)

        return melds

    def find_best_melds(self, tiles: List[Tile], max_melds: int = 4) -> List[Meld]:
        """
        Find the best combination of melds for a hand
        (for AI purposes)

        Returns:
            List of optimal melds
        """
        # This is a simplified version
        # Full implementation would use more sophisticated algorithms
        return self.find_all_melds(tiles)[:max_melds]
