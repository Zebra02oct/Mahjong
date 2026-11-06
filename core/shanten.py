"""
Mahjong Riichi - Shanten Calculator
Core algorithm to determine how many tiles away from tenpai (ready)

Shanten number:
- -1 = Already winning (agari)
- 0 = Tenpai (one tile away from winning)
- 1+ = Number of tiles needed to reach tenpai
"""

from functools import lru_cache
from typing import List, Set, Tuple, Optional
from core.tiles import Tile, tiles_to_counts, counts_to_tiles
from core.constants import (
    PIN_RANGE, SOU_RANGE, MAN_RANGE,
    TERMINALS, HONORS
)


class ShantenCalculator:
    """
    Shanten Calculator using dynamic programming with memoization

    Key algorithm:
    1. For a 14-tile hand, try all possible combinations of 4 melds + 1 pair
    2. Calculate how many tiles are "wasted" (not part of complete hand)
    3. Shanten = number of tiles needed to complete the hand
    """

    def __init__(self):
        self.memo = {}

    def calculate_shanten(self, tiles: List[Tile]) -> int:
        """
        Calculate shanten number for a hand

        Args:
            tiles: List of tiles (usually 14 tiles, but can be any number)

        Returns:
            Shanten number (-1 to 8+)
            -1 = already winning
            0 = tenpai (ready)
        """
        if not tiles:
            return 4  # Need 4 melds + 1 pair = 14 tiles

        counts = tiles_to_counts(tiles)

        # Handle special case: 13 orphans (cannot win)
        if self._is_13_orphans(counts):
            return 13

        return self._calculate_shanten(counts)

    def calculate_shanten_from_counts(self, counts: List[int]) -> int:
        """
        Calculate shanten from a count array

        Args:
            counts: List of 34 integers representing tile counts

        Returns:
            Shanten number
        """
        total = sum(counts)

        # If less than 14 tiles, calculate tiles needed
        if total < 14:
            return 4 - (total // 3)  # Approximate

        return self._calculate_shanten(counts)

    def _calculate_shanten(self, counts: List[int]) -> int:
        """
        Internal shanten calculation

        Uses dynamic programming to find minimum shanten
        """
        total = sum(counts)

        # Quick check: if 14 tiles, check for agari first
        if total == 14:
            if self._check_agari(counts):
                return -1  # Already winning

        # If less than 14 tiles, calculate based on tile count
        if total < 14:
            # Can form at most total // 3 melds
            # Need 4 melds + 1 pair = 14 tiles
            max_mentsu = total // 3
            tiles_needed = 14 - total

            # Shanten = tiles_needed + (max(0, 4 - max_mentsu - 1))
            # Simplified: need 4 melds and 1 pair
            return max(0, (14 - total) // 3 + 1)

        # For 14+ tiles, use full algorithm
        return self._find_min_shanten(counts)

    def _find_min_shanten(self, counts: List[int]) -> int:
        """
        Find minimum shanten by trying all possible hand configurations

        Strategy:
        1. Try using each tile type as a potential pair
        2. Calculate max melds from remaining tiles
        3. Shanten = 4 - (mentsu_count + (has_pair ? 1 : 0))
        """
        min_shanten = 8  # Start with high value

        # Try each tile as pair (if count >= 2)
        for pair_type in range(34):
            if counts[pair_type] >= 2:
                # Use this pair
                temp_counts = counts.copy()
                temp_counts[pair_type] -= 2

                # Count max melds
                melds = self._count_max_melds(temp_counts)

                # Calculate shanten
                # Need: 4 melds + 1 pair = shanten 0
                # Have: melds melds + 1 pair
                # Shanten = max(0, 4 - melds) + (melds < 4 ? 0 : 0)
                # Simplified: shanten = max(0, 4 - melds)
                shanten = max(0, 4 - melds)

                min_shanten = min(min_shanten, shanten)

        # Also try without any pair (just melds)
        melds = self._count_max_melds(counts)
        shanten = max(0, 5 - melds)  # Need 4 melds + 1 pair = 5 units
        min_shanten = min(min_shanten, shanten)

        return min_shanten

    def _count_max_melds(self, counts: List[int]) -> int:
        """
        Count maximum number of melds that can be formed

        Uses greedy algorithm with some optimization
        """
        # Create a mutable copy
        c = counts.copy()

        meld_count = 0

        # Count pons first (they use 3 tiles)
        for tile_type in range(34):
            while c[tile_type] >= 3:
                c[tile_type] -= 3
                meld_count += 1

        # Then count chis
        # Process each suit
        for suit_range in [PIN_RANGE, SOU_RANGE, MAN_RANGE]:
            # Count chis using greedy
            for start in range(7):
                while True:
                    t1 = suit_range[start]
                    t2 = suit_range[start + 1]
                    t3 = suit_range[start + 2]

                    if c[t1] >= 1 and c[t2] >= 1 and c[t3] >= 1:
                        c[t1] -= 1
                        c[t2] -= 1
                        c[t3] -= 1
                        meld_count += 1
                    else:
                        break

        return meld_count

    def _check_agari(self, counts: List[int]) -> bool:
        """
        Check if hand is already winning (agari)

        A winning hand has exactly 4 melds + 1 pair
        """
        # Try each tile as pair
        for pair_type in range(34):
            if counts[pair_type] >= 2:
                temp = counts.copy()
                temp[pair_type] -= 2

                melds = self._count_max_melds(temp)
                if melds == 4:
                    return True

        return False

    def is_tenpai(self, tiles: List[Tile]) -> bool:
        """Check if hand is tenpai (shanten = 0)"""
        return self.calculate_shanten(tiles) == 0

    def is_agari(self, tiles: List[Tile]) -> bool:
        """Check if hand is already winning"""
        return self.calculate_shanten(tiles) == -1

    def get_wait_tiles(self, tiles: List[Tile]) -> List[int]:
        """
        Get all tiles that would make this hand tenpai (agarimen)

        Args:
            tiles: Current hand (usually 13 tiles)

        Returns:
            List of tile types (0-33) that complete the hand
        """
        if len(tiles) != 13:
            return []

        counts = tiles_to_counts(tiles)
        waits = []

        for tile_type in range(34):
            if counts[tile_type] < 4:  # Can only draw if not already 4
                temp_counts = counts.copy()
                temp_counts[tile_type] += 1

                if self._calculate_shanten(temp_counts) == 0:
                    waits.append(tile_type)

        return waits

    def get_wait_tiles_detailed(self, tiles: List[Tile]) -> List[Tuple[int, List[str]]]:
        """
        Get wait tiles with their wait types

        Returns:
            List of (tile_type, wait_type) tuples
            wait_type: "tanki" (single), "ryanmen" (double-sided),
                      "kanchan" (edge), "penchan" (edge)
        """
        if len(tiles) != 13:
            return []

        counts = tiles_to_counts(tiles)
        waits = []

        for tile_type in range(34):
            if counts[tile_type] < 4:
                temp_counts = counts.copy()
                temp_counts[tile_type] += 1

                if self._calculate_shanten(temp_counts) == 0:
                    wait_type = self._classify_wait(counts, tile_type)
                    waits.append((tile_type, wait_type))

        return waits

    def _classify_wait(self, counts: List[int], new_tile: int) -> str:
        """
        Classify the wait type for a specific tile

        Wait types:
        - tanki: Single tile wait
        - ryanmen: Double-sided (e.g., waiting for 3 or 7)
        - kanchan: Center (e.g., waiting for 5 when have 4-6)
        - penchan: Edge (e.g., waiting for 1 when have 2-3)
        """
        # Determine suit of new tile
        if 0 <= new_tile <= 8:
            suit_range = PIN_RANGE
        elif 9 <= new_tile <= 17:
            suit_range = SOU_RANGE
        elif 18 <= new_tile <= 26:
            suit_range = MAN_RANGE
        else:
            return "tanki"  # Honors are always tanki

        value = new_tile - suit_range[0]  # 0-8

        # Count tiles needed to form melds
        # Simple heuristic based on tile position
        if value == 0 or value == 8:
            return "penchan"  # Waiting for 1 or 9
        elif value == 4:
            return "kanchan"  # Waiting for 5 in 4-5-6
        else:
            return "ryanmen"  # Middle tiles = better wait

    def _is_13_orphans(self, counts: List[int]) -> bool:
        """
        Check if hand is 13 orphans (cannot win)

        13 orphans: one of each terminal/honor + one duplicate
        """
        # Required tiles for 13 orphans
        required = set()
        for r in [PIN_RANGE, SOU_RANGE, MAN_RANGE]:
            required.add(r[0])   # 1
            required.add(r[8])   # 9
        for w in range(27, 34):
            required.add(w)

        # Count tiles that are in the required set
        orphan_count = sum(counts[t] for t in required)

        # 13 orphans = 13 tiles from required set + 1 extra
        total = sum(counts)

        if total == 14 and orphan_count == 14:
            # Check it's actually 13 unique + 1 duplicate
            unique_orphans = sum(1 for t in required if counts[t] > 0)
            return unique_orphans == 13

        return False

    def estimate_shanten_fast(self, tiles: List[Tile]) -> int:
        """
        Fast shanten estimation (not 100% accurate but quick)

        Use for AI when speed is more important than precision
        """
        counts = tiles_to_counts(tiles)
        total = sum(counts)

        # Quick formula based on tile count
        if total < 13:
            return max(0, (14 - total) // 3 + 1)

        if total == 13:
            # Check for tenpai
            for t in range(34):
                if counts[t] < 4:
                    temp = counts.copy()
                    temp[t] += 1
                    if self._check_agari(temp):
                        return 0
            return 1

        return self._find_min_shanten(counts)


# =============================================================================
# STANDALONE FUNCTIONS
# =============================================================================

def calculate_shanten(tiles: List[Tile]) -> int:
    """Quick function to calculate shanten"""
    calc = ShantenCalculator()
    return calc.calculate_shanten(tiles)


def get_wait_tiles(tiles: List[Tile]) -> List[int]:
    """Quick function to get wait tiles"""
    calc = ShantenCalculator()
    return calc.get_wait_tiles(tiles)


def is_tenpai(tiles: List[Tile]) -> bool:
    """Quick function to check tenpai"""
    calc = ShantenCalculator()
    return calc.is_tenpai(tiles)


def is_agari(tiles: List[Tile]) -> bool:
    """Quick function to check agari"""
    calc = ShantenCalculator()
    return calc.is_agari(tiles)
