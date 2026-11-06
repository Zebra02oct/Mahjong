"""
Mahjong Riichi - Core Module
Core game logic components
"""

from core.tiles import Tile, create_tile, tiles_to_counts, counts_to_tiles, sort_tiles
from core.deck import Deck, create_standard_deck
from core.meld import Meld, MeldDetector, detect_melds, can_ron
from core.shanten import ShantenCalculator, calculate_shanten, is_tenpai, is_agari
from core.yaku import Yaku, YakuContext, YakuDetector, detect_yaku
from core.score import ScoreCalculator, ScoreResult, calculate_score
from core.constants import (
    TILE_NAMES, TILE_UNICODE,
    PIN_RANGE, SOU_RANGE, MAN_RANGE, WIND_RANGE, DRAGON_RANGE,
    YAKU_LIST, YAKUMAN_LIST,
    STARTING_SCORE, MANGAN_SCORES,
    MELD_PON, MELD_CHI, MELD_KAN,
    EAST, SOUTH, WEST, NORTH, SEAT_WIND_NAMES,
    TERMINALS, HONORS, SIMPLES
)

__all__ = [
    # Tiles
    'Tile', 'create_tile', 'tiles_to_counts', 'counts_to_tiles', 'sort_tiles',
    # Deck
    'Deck', 'create_standard_deck',
    # Meld
    'Meld', 'MeldDetector', 'detect_melds', 'can_ron',
    # Shanten
    'ShantenCalculator', 'calculate_shanten', 'is_tenpai', 'is_agari',
    # Yaku
    'Yaku', 'YakuContext', 'YakuDetector', 'detect_yaku',
    # Score
    'ScoreCalculator', 'ScoreResult', 'calculate_score',
    # Constants
    'TILE_NAMES', 'TILE_UNICODE',
    'PIN_RANGE', 'SOU_RANGE', 'MAN_RANGE', 'WIND_RANGE', 'DRAGON_RANGE',
    'YAKU_LIST', 'YAKUMAN_LIST',
    'STARTING_SCORE', 'MANGAN_SCORES',
    'MELD_PON', 'MELD_CHI', 'MELD_KAN',
    'EAST', 'SOUTH', 'WEST', 'NORTH', 'SEAT_WIND_NAMES',
    'TERMINALS', 'HONORS', 'SIMPLES',
]
