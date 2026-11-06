"""
Mahjong Riichi - Constants and Definitions
34 unique tile types numbered 0-33
"""

from typing import Dict, List

# =============================================================================
# TILE TYPE INDICES (0-33)
# =============================================================================
# Pin (Circles)  : 0-8   (1-9)
# Sou (Bamboo)   : 9-17  (1-9)
# Man (Characters): 18-26 (1-9)
# Winds          : 27-30 (East, South, West, North)
# Dragons        : 31-33 (White, Green, Red)

PIN_RANGE = list(range(0, 9))      # 0-8
SOU_RANGE = list(range(9, 18))     # 9-17
MAN_RANGE = list(range(18, 27))    # 18-26
WIND_RANGE = list(range(27, 31))   # 27-30
DRAGON_RANGE = list(range(31, 34)) # 31-33

ALL_TILE_TYPES = list(range(34))   # 0-33

# =============================================================================
# TILE NAMES FOR DISPLAY
# =============================================================================
TILE_NAMES: Dict[int, str] = {
    **{i: f"{i+1}-pin" for i in range(9)},           # 0-8: 1-pin to 9-pin
    **{i: f"{i-8}-sou" for i in range(9, 18)},      # 9-17: 1-sou to 9-sou
    **{i: f"{i-17}-man" for i in range(18, 27)},    # 18-26: 1-man to 9-man
    27: "east", 28: "south", 29: "west", 30: "north",
    31: "white-dragon", 32: "green-dragon", 33: "red-dragon"
}

# Tile Unicode characters (for console display)
TILE_UNICODE: Dict[int, str] = {
    0: "🀙", 1: "🀚", 2: "🀛", 3: "🀜", 4: "🀝", 5: "🀞", 6: "🀟", 7: "🀠", 8: "🀡",  # Pin 1-9
    9: "🀐", 10: "🀑", 11: "🀒", 12: "🀓", 13: "🀔", 14: "🀕", 15: "🀖", 16: "🀗", 17: "🀘",  # Sou 1-9
    18: "🀆", 19: "🀇", 20: "🀈", 21: "🀉", 22: "🀊", 23: "🀋", 24: "🀌", 25: "🀍", 26: "🀎",  # Man 1-9
    27: "🀀", 28: "🀁", 29: "🀂", 30: "🀃",  # East, South, West, North
    31: "🀄", 32: "🀅", 33: "🀆"             # White, Green, Red
}

# =============================================================================
# TILE PROPERTIES
# =============================================================================
TERMINALS = {0, 8, 9, 17, 18, 26}  # 1 and 9 of each suit
HONORS = set(WIND_RANGE + DRAGON_RANGE)  # Winds and Dragons
SIMPLES = [i for i in ALL_TILE_TYPES if i not in TERMINALS and i not in HONORS]

# Suits
def get_suit(tile_type: int) -> str:
    """Get suit name from tile type"""
    if tile_type in PIN_RANGE:
        return "pin"
    elif tile_type in SOU_RANGE:
        return "sou"
    elif tile_type in MAN_RANGE:
        return "man"
    elif tile_type in WIND_RANGE:
        return "wind"
    else:
        return "dragon"

def get_value(tile_type: int) -> int:
    """Get numeric value from tile type (1-9 for suits, 0 for honors)"""
    if tile_type in PIN_RANGE:
        return tile_type + 1
    elif tile_type in SOU_RANGE:
        return tile_type - 8
    elif tile_type in MAN_RANGE:
        return tile_type - 17
    else:
        return 0  # Honors don't have numeric value

# =============================================================================
# DECK CONSTANTS
# =============================================================================
TILES_PER_TYPE = 4  # 4 copies of each tile
TOTAL_TILES = 34 * TILES_PER_TYPE  # 136 tiles

# Dead wall position (where kan tiles come from)
DEAD_WALL_INDEX = 136 - 14  # Last 14 tiles form dead wall

# =============================================================================
# SEAT WINDS
# =============================================================================
EAST = 0
SOUTH = 1
WEST = 2
NORTH = 3

SEAT_WIND_NAMES = ["East", "South", "West", "North"]
SEAT_WIND_TILES = [27, 28, 29, 30]  # East, South, West, North tiles

# =============================================================================
# DORA CONFIGURATION
# =============================================================================
DORA_INDICATOR_COUNT = 1  # Base dora indicator
MAX_URADORAS = 4  # Max uradora (hidden dora)

# =============================================================================
# YAKU DEFINITIONS
# =============================================================================
YAKU_LIST: Dict[str, int] = {
    # 1 Han yaku
    "menzen_tsumo": 1,    # Closed hand tsumo
    "reach": 1,            # Riichi
    "ippatsu": 1,          # One shot after riichi
    "pinfu": 1,            # No point yaku, all sequences, open pair
    "tanyao": 1,           # All simples (2-8)
    "haitei": 1,           # Last tile from wall
    "houtei": 1,           # Last discard
    "rinshan": 1,          # After kan draw

    # 2 Han yaku
    "danyao": 2,           # All terminals and honors
    "toitoi": 2,           # All pons
    "sanankou": 2,         # Three concealed pons
    "sanshoku": 2,         # Same sequence in all suits
    "sankantsu": 2,        # Three kans
    "honitsu": 2,          # Half flush
    "chanta": 2,           # Outside hand
    "ittsu": 2,            # Three consecutive sequences
    "sanhou": 2,           # Three melds + pair
    "honroku": 2,          # Three terminals/honors

    # 3 Han yaku
    "junsei_chanta": 3,    # Pure outside hand
    "junchan": 3,          # Pure terminals
    "ryanpeiko": 3,        # Two sequences twice

    # 6 Han yaku
    "chinitsu": 6,         # Full flush (one suit only)
    "junsei": 6,           # Pure straight

    # Yakuman (13 Han)
    "kokushi_musou": 13,   # Thirteen orphans
    "chuuren_poto": 13,    # Nine gates
    "suuankou": 13,        # Four concealed pons
    "suukantsu": 13,       # Four kans
    "tsuuiso": 13,         # All honors
    "ryuuiisou": 13,       # All green tiles
    "chinrouku": 13,       # All terminals
    "daisuushii": 13,      # Four big winds
    "shosuushii": 13,      # Four small winds
    "tenhou": 13,          # Heaven win (dealer round 1)
    "chihou": 13,          # Earth win (non-dealer round 1)
    "renhou": 13,          # Hand of man
}

# Yakuman list for special handling
YAKUMAN_LIST = {
    "kokushi_musou", "chuuren_poto", "suuankou", "suukantsu",
    "tsuuiso", "ryuuiisou", "chinrouku", "daisuushii",
    "shosuushii", "tenhou", "chihou", "renhou"
}

# =============================================================================
# SCORE CONSTANTS
# =============================================================================
# Mangan fixed scores (han >= 5)
MANGAN_SCORES = {
    5: 8000,
    6: 12000,
    7: 18000,
    8: 24000,
    9: 36000,
    10: 48000,
    11: 72000,
    12: 96000,
}

# Starting score
STARTING_SCORE = 25000

# =============================================================================
# MELD TYPES
# =============================================================================
MELD_PON = "pon"
MELD_CHI = "chi"
MELD_KAN = "kan"
MELD_KOUKAN = "koukan"  # Added kan (from pon)
MELD_CHAKAN = "chakan"  # Added kan (from hand)

# =============================================================================
# ACTION TYPES
# =============================================================================
ACTION_DISCARD = "discard"
ACTION_TSUMO = "tsumo"
ACTION_RON = "ron"
ACTION_PON = "pon"
ACTION_CHI = "chi"
ACTION_KAN = "kan"
ACTION_RICHI = "riichi"
ACTION_NONE = "none"
