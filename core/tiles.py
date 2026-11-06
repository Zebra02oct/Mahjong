"""
Mahjong Riichi - Tile Class
Represents a single tile with properties
"""

from dataclasses import dataclass, field
from typing import Optional
from core.constants import (
    TILE_NAMES, TILE_UNICODE, get_suit, get_value,
    PIN_RANGE, SOU_RANGE, MAN_RANGE, WIND_RANGE, DRAGON_RANGE,
    TERMINALS, HONORS, SIMPLES
)


@dataclass
class Tile:
    """
    Represents a single Mahjong tile (0-33)

    Tile types:
    - 0-8:   Pin (Circles) 1-9
    - 9-17:  Sou (Bamboo) 1-9
    - 18-26: Man (Characters) 1-9
    - 27-30: Winds (East, South, West, North)
    - 31-33: Dragons (White, Green, Red)
    """
    type: int  # 0-33

    # State flags
    is_guarded: bool = False  # Tile is safe (can't be ronned)
    is_dora: bool = False      # This is a dora tile
    just_drawn: bool = False   # Just drawn this turn (can't discard)

    def __post_init__(self):
        if not 0 <= self.type <= 33:
            raise ValueError(f"Invalid tile type: {self.type}")

    @property
    def suit(self) -> str:
        """Get the suit of this tile"""
        return get_suit(self.type)

    @property
    def value(self) -> int:
        """Get the numeric value (1-9 for suits, 0 for honors)"""
        return get_value(self.type)

    @property
    def is_terminal(self) -> bool:
        """Check if tile is terminal (1 or 9 of any suit)"""
        return self.type in TERMINALS

    @property
    def is_honor(self) -> bool:
        """Check if tile is honor (wind or dragon)"""
        return self.type in HONORS

    @property
    def is_simple(self) -> bool:
        """Check if tile is simple (2-8 of any suit)"""
        return self.type in SIMPLES

    @property
    def is_suit(self) -> bool:
        """Check if tile is a suit tile (pin, sou, man)"""
        return self.suit in ("pin", "sou", "man")

    @property
    def is_pin(self) -> bool:
        """Check if tile is pin (circles)"""
        return self.type in PIN_RANGE

    @property
    def is_sou(self) -> bool:
        """Check if tile is sou (bamboo)"""
        return self.type in SOU_RANGE

    @property
    def is_man(self) -> bool:
        """Check if tile is man (characters)"""
        return self.type in MAN_RANGE

    @property
    def is_wind(self) -> bool:
        """Check if tile is wind"""
        return self.type in WIND_RANGE

    @property
    def is_dragon(self) -> bool:
        """Check if tile is dragon"""
        return self.type in DRAGON_RANGE

    @property
    def is_green(self) -> bool:
        """Check if tile is green (sou 2,3,4,6,8 and green dragon)"""
        green_tiles = {10, 11, 12, 14, 16, 32}  # Sou 2,3,4,6,8 and green dragon
        return self.type in green_tiles

    @property
    def name(self) -> str:
        """Get display name"""
        return TILE_NAMES[self.type]

    @property
    def unicode(self) -> str:
        """Get Unicode character for display"""
        return TILE_UNICODE[self.type]

    @property
    def index(self) -> int:
        """Get index within suit (0-8 for suits, 0 for honors)"""
        if self.is_suit:
            return self.value - 1
        return 0

    def __str__(self) -> str:
        return self.unicode

    def __repr__(self) -> str:
        return f"Tile({self.type}, {self.name})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Tile):
            return False
        return self.type == other.type

    def __hash__(self) -> int:
        return hash(self.type)


def create_tile(type_id: int) -> Tile:
    """Factory function to create a tile"""
    return Tile(type=type_id)


def tiles_to_counts(tiles: list) -> list:
    """
    Convert a list of tiles to a count array (34 elements)

    Args:
        tiles: List of Tile objects

    Returns:
        List of 34 integers representing count of each tile type
    """
    counts = [0] * 34
    for tile in tiles:
        counts[tile.type] += 1
    return counts


def counts_to_tiles(counts: list) -> list:
    """
    Convert a count array back to a list of tiles

    Args:
        counts: List of 34 integers

    Returns:
        List of Tile objects
    """
    tiles = []
    for tile_type, count in enumerate(counts):
        for _ in range(count):
            tiles.append(Tile(type=tile_type))
    return tiles


def sort_tiles(tiles: list, by: str = "type") -> list:
    """
    Sort tiles for display

    Args:
        by: "type" (by tile number) or "suit" (by suit then value)
    """
    if by == "type":
        return sorted(tiles, key=lambda t: t.type)
    elif by == "suit":
        # Sort by suit order: pin, sou, man, wind, dragon
        suit_order = {"pin": 0, "sou": 1, "man": 2, "wind": 3, "dragon": 4}
        return sorted(tiles, key=lambda t: (suit_order[t.suit], t.value))
    return tiles
