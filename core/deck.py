"""
Mahjong Riichi - Deck Management
Handles deck creation, shuffling, and drawing
"""

import random
from typing import List, Optional, Tuple
from core.tiles import Tile, create_tile
from core.constants import TOTAL_TILES, DEAD_WALL_INDEX, DORA_INDICATOR_COUNT


class Deck:
    """
    Represents the Mahjong deck (136 tiles)

    Structure:
    - 136 tiles total
    - 34 unique types × 4 copies each
    - Last 14 tiles form the "dead wall"
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize deck

        Args:
            seed: Random seed for reproducibility (optional)
        """
        if seed is not None:
            random.seed(seed)

        self.tiles: List[Tile] = []
        self._build()

        # Dead wall (end of deck, 14 tiles)
        # Dora indicators are at the front of dead wall
        self._dead_wall_index = DEAD_WALL_INDEX

        # Dora count (how many dora indicators revealed)
        self._dora_count = 0

    def _build(self):
        """Build the deck with 4 copies of each tile type"""
        self.tiles = []
        for tile_type in range(34):
            for _ in range(4):
                self.tiles.append(create_tile(tile_type))

    def shuffle(self):
        """Shuffle the deck"""
        random.shuffle(self.tiles)

    def reset(self, seed: Optional[int] = None):
        """Reset and optionally reshuffle the deck"""
        if seed is not None:
            random.seed(seed)
        self._build()
        self._dora_count = 0

    # =========================================================================
    # DRAWING TILES
    # =========================================================================

    def draw(self, count: int = 1) -> List[Tile]:
        """
        Draw tiles from the top of the wall

        Args:
            count: Number of tiles to draw

        Returns:
            List of drawn tiles
        """
        if count <= 0:
            return []

        drawn = []
        for _ in range(count):
            if self.remaining < 1:
                break
            drawn.append(self.tiles.pop())

        return drawn

    def draw_from_wall(self, position: int) -> Optional[Tile]:
        """
        Draw a specific tile from the wall by position

        Args:
            position: Position in the wall (0 = top/front)

        Returns:
            Tile at that position or None if out of bounds
        """
        if 0 <= position < len(self.tiles):
            return self.tiles.pop(position)
        return None

    def draw_player_hand(self) -> List[Tile]:
        """
        Draw initial 13 tiles for a player hand

        Returns:
            List of 13 tiles
        """
        return self.draw(13)

    def draw_kandora(self) -> Optional[Tile]:
        """
        Draw kan dora (when someone calls kan)

        Returns:
            Tile to replace the dora indicator, or None if dead wall reached
        """
        if self.remaining > DEAD_WALL_INDEX + 1:
            # Draw replacement from after dora indicators
            return self.tiles.pop(DEAD_WALL_INDEX + self._dora_count)
        return None

    # =========================================================================
    # DORA MANAGEMENT
    # =========================================================================

    def get_dora_indicators(self, count: int = None) -> List[Tile]:
        """
        Get revealed dora indicators

        Args:
            count: Specific number of indicators (default: revealed count)

        Returns:
            List of dora indicator tiles
        """
        if count is None:
            count = self._dora_count

        start = DEAD_WALL_INDEX
        end = start + count

        if end > len(self.tiles):
            end = len(self.tiles)

        return self.tiles[start:end]

    def reveal_dora(self) -> Tile:
        """
        Reveal the next dora indicator

        Returns:
            The newly revealed dora tile
        """
        if self._dora_count < 5:  # Max 5 dora
            self._dora_count += 1
            return self.tiles[DEAD_WALL_INDEX + self._dora_count - 1]
        return self.tiles[DEAD_WALL_INDEX]  # Return last indicator

    def get_revealed_dora_count(self) -> int:
        """Get number of revealed dora indicators"""
        return self._dora_count

    def count_dora(self, tile: Tile) -> int:
        """
        Count how many dora this tile represents

        Args:
            tile: Tile to check

        Returns:
            Number of dora
        """
        dora_indicators = self.get_dora_indicators()
        count = 0

        for indicator in dora_indicators:
            if self._is_dora(tile.type, indicator.type):
                count += 1

        return count

    def _is_dora(self, tile_type: int, dora_type: int) -> bool:
        """
        Check if a tile is a dora of the given indicator

        Dora indicator shows the NEXT tile in sequence
        Pin: 1->2->3->...->9->1 (wraps)
        Sou/Man: Same
        Honor: 27(E)->28(S)->29(W)->30(N)->27(E)
        Dragon: 31(W)->32(G)->33(R)->31(W)
        """
        # Pin: 0-8, wrap 8->0
        if 0 <= dora_type <= 8:
            next_tile = 0 if dora_type == 8 else dora_type + 1
            return tile_type == next_tile

        # Sou: 9-17
        if 9 <= dora_type <= 17:
            next_tile = 9 if dora_type == 17 else dora_type + 1
            return tile_type == next_tile

        # Man: 18-26
        if 18 <= dora_type <= 26:
            next_tile = 18 if dora_type == 26 else dora_type + 1
            return tile_type == next_tile

        # Wind: 27-30 (E->S->W->N->E)
        if 27 <= dora_type <= 30:
            next_tile = 27 if dora_type == 30 else dora_type + 1
            return tile_type == next_tile

        # Dragon: 31-33 (W->G->R->W)
        if 31 <= dora_type <= 33:
            next_tile = 31 if dora_type == 33 else dora_type + 1
            return tile_type == next_tile

        return False

    # =========================================================================
    # PROPERTIES
    # =========================================================================

    @property
    def remaining(self) -> int:
        """Number of tiles remaining in the wall"""
        return len(self.tiles)

    @property
    def dead_wall_remaining(self) -> int:
        """Number of tiles in the dead wall"""
        return max(0, len(self.tiles) - DEAD_WALL_INDEX)

    @property
    def is_exhausted(self) -> bool:
        """Check if the deck is exhausted (no more draws)"""
        return self.remaining <= self.dead_wall_remaining

    # =========================================================================
    # DEBUG / INFO
    # =========================================================================

    def get_remaining_count(self, tile_type: int) -> int:
        """Get remaining count of a specific tile type in the wall"""
        return sum(1 for tile in self.tiles if tile.type == tile_type)

    def get_distribution(self) -> dict:
        """Get distribution of remaining tiles"""
        dist = {}
        for i in range(34):
            count = self.get_remaining_count(i)
            if count > 0:
                dist[i] = count
        return dist

    def __str__(self) -> str:
        return f"Deck(remaining={self.remaining}, dora={self._dora_count})"

    def __repr__(self) -> str:
        return self.__str__()


def create_standard_deck(seed: Optional[int] = None) -> Deck:
    """
    Factory function to create a standard shuffled deck

    Args:
        seed: Random seed for reproducibility

    Returns:
        Shuffled Deck object
    """
    deck = Deck(seed=seed)
    deck.shuffle()
    return deck
