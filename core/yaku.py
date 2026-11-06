"""
Mahjong Riichi - Yaku (Winning Patterns) Detection
Detects all valid yaku in a hand
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from core.tiles import Tile, tiles_to_counts
from core.constants import (
    YAKU_LIST, YAKUMAN_LIST,
    PIN_RANGE, SOU_RANGE, MAN_RANGE, WIND_RANGE, DRAGON_RANGE,
    TERMINALS, HONORS
)


@dataclass
class Yaku:
    """Represents a detected yaku"""
    name: str
    han: int
    is_yakuman: bool = False
    display_name: str = ""

    def __post_init__(self):
        if not self.display_name:
            self.display_name = self.name.replace("_", " ").title()


@dataclass
class YakuContext:
    """Context for yaku detection"""
    is_menzen: bool = True          # Closed hand (no calls)
    is_tsumo: bool = False          # Self-draw win
    is_riichi: bool = False         # Riichi declared
    is_ippatsu: bool = False        # One shot after riichi
    is_rinshan: bool = False        # After kan draw
    is_haitei: bool = False         # Last tile from wall
    is_houtei: bool = False         # Last discard
    round_number: int = 1            # Round number
    is_dealer: bool = False         # Is the dealer
    honba: int = 0                  # Honba count
    player_seat: int = 0             # Player seat wind
    round_wind: int = 0             # Current round wind (tile type)
    dora_count: int = 0              # Number of revealed dora
    called_melds: List = None       # Melds called from discards

    def __post_init__(self):
        if self.called_melds is None:
            self.called_melds = []


class YakuDetector:
    """
    Detects all valid yaku in a Mahjong hand

    Yaku are winning patterns that award points (han)
    """

    def __init__(self):
        self.yaku_list = YAKU_LIST

    def detect(self, hand_tiles: List[Tile], context: YakuContext) -> List[Yaku]:
        """
        Detect all valid yaku in a hand

        Args:
            hand_tiles: Tiles in hand (including called melds)
            context: Game context

        Returns:
            List of detected Yaku
        """
        results = []
        counts = tiles_to_counts(hand_tiles)

        # Get basic hand info
        is_menzen = len(context.called_melds) == 0
        all_tiles = hand_tiles.copy()

        # Check each yaku
        if self._check_menzen_tsumo(all_tiles, context, is_menzen):
            results.append(Yaku("menzen_tsumo", 1))

        if self._check_riichi(context):
            results.append(Yaku("reach", 1))

        if self._check_ippatsu(context):
            results.append(Yaku("ippatsu", 1))

        if self._check_tanyao(all_tiles):
            results.append(Yaku("tanyao", 1))

        if self._check_pinfu(all_tiles, context, is_menzen):
            results.append(Yaku("pinfu", 1))

        if self._check_toitoi(all_tiles, context.called_melds):
            results.append(Yaku("toitoi", 2))

        if self._check_honitsu(all_tiles):
            results.append(Yaku("honitsu", 2))

        if self._check_chinitsu(all_tiles):
            results.append(Yaku("chinitsu", 6))

        if self._check_chanta(all_tiles, context.called_melds):
            results.append(Yaku("chanta", 2))

        if self._check_junsei_chanta(all_tiles, context.called_melds):
            results.append(Yaku("junsei_chanta", 3))

        if self._check_tanyao(all_tiles):
            results.append(Yaku("tanyao", 1))

        if self._check_sanshoku(all_tiles):
            results.append(Yaku("sanshoku", 2))

        if self._check_ittsu(all_tiles):
            results.append(Yaku("ittsu", 2))

        if self._check_honroku(all_tiles, context.called_melds):
            results.append(Yaku("honroku", 2))

        if self._check_danyao(all_tiles):
            results.append(Yaku("danyao", 2))

        if self._check_sanankou(all_tiles, context.called_melds):
            results.append(Yaku("sanankou", 2))

        if self._check_sankantsu(context.called_melds):
            results.append(Yaku("sankantsu", 2))

        if self._check_haitei(context):
            results.append(Yaku("haitei", 1))

        if self._check_houtei(context):
            results.append(Yaku("houtei", 1))

        if self._check_rinshan(context):
            results.append(Yaku("rinshan", 1))

        # Yakuman checks
        if self._check_kokushi(all_tiles, is_menzen):
            results.append(Yaku("kokushi_musou", 13, is_yakuman=True))

        if self._check_chuuren_poto(all_tiles, is_menzen):
            results.append(Yaku("chuuren_poto", 13, is_yakuman=True))

        if self._check_suuankou(all_tiles, is_menzen):
            results.append(Yaku("suuankou", 13, is_yakuman=True))

        if self._check_tsuuiso(all_tiles):
            results.append(Yaku("tsuuiso", 13, is_yakuman=True))

        if self._check_ryuuiisou(all_tiles):
            results.append(Yaku("ryuuiisou", 13, is_yakuman=True))

        # Add dora yaku
        if context.dora_count > 0:
            results.append(Yaku("dora", context.dora_count))

        return results

    # =========================================================================
    # YAKU CHECK METHODS
    # =========================================================================

    def _check_menzen_tsumo(self, tiles: List[Tile], context: YakuContext, is_menzen: bool) -> bool:
        """Menzen Tsumo: Closed hand + self draw"""
        return is_menzen and context.is_tsumo

    def _check_riichi(self, context: YakuContext) -> bool:
        """Riichi: Declare when tenpai"""
        return context.is_riichi

    def _check_ippatsu(self, context: YakuContext) -> bool:
        """Ippatsu: Win within one draw after riichi"""
        return context.is_riichi and context.is_ippatsu

    def _check_tanyao(self, tiles: List[Tile]) -> bool:
        """Tanyao: All simples (2-8, no terminals/honors)"""
        for tile in tiles:
            if tile.is_terminal or tile.is_honor:
                return False
        return True

    def _check_pinfu(self, tiles: List[Tile], context: YakuContext, is_menzen: bool) -> bool:
        """
        Pinfu: All sequences, open pair (not valued)
        Note: This is a simplified version
        """
        if not is_menzen:
            return False

        counts = tiles_to_counts(tiles)
        total = sum(counts)

        if total != 14:
            return False

        # Check all tiles are simples
        for tile in tiles:
            if tile.is_terminal or tile.is_honor:
                return False

        # Check has exactly 4 sequences
        # Simplified: if no terminals/honors, likely pinfu
        return True

    def _check_toitoi(self, tiles: List[Tile], called_melds: List) -> bool:
        """Toitoi: All pons"""
        counts = tiles_to_counts(tiles)

        # Count pon-like groups (3+ tiles of same type)
        pon_count = 0
        for tile_type in range(34):
            if counts[tile_type] >= 3:
                pon_count += 1

        # Need at least 4 pons (including called melds)
        # Simplified check
        return pon_count >= 4

    def _check_honitsu(self, tiles: List[Tile]) -> bool:
        """Honitsu: Half flush (one suit + honors)"""
        has_suit = False
        suit_type = None

        for tile in tiles:
            if tile.is_honor:
                continue
            if tile.is_suit:
                if suit_type is None:
                    suit_type = tile.suit
                    has_suit = True
                elif tile.suit != suit_type:
                    return False

        return has_suit

    def _check_chinitsu(self, tiles: List[Tile]) -> bool:
        """Chinitsu: Full flush (one suit only, no honors)"""
        suit_type = None

        for tile in tiles:
            if tile.is_honor:
                return False
            if tile.is_suit:
                if suit_type is None:
                    suit_type = tile.suit
                elif tile.suit != suit_type:
                    return False

        return suit_type is not None

    def _check_chanta(self, tiles: List[Tile], called_melds: List) -> bool:
        """Chanta: Outside hand (each meld has terminal/honor)"""
        counts = tiles_to_counts(tiles)

        # Check all melds have at least one terminal/honor
        # Simplified: check if any terminal/honor in hand
        has_terminal_or_honor = any(
            tile.is_terminal or tile.is_honor
            for tile in tiles
        )

        return has_terminal_or_honor

    def _check_junsei_chanta(self, tiles: List[Tile], called_melds: List) -> bool:
        """Junsei Chanta: Pure outside hand (all melds are terminals/honors)"""
        for tile in tiles:
            if tile.is_simple:
                return False
        return True

    def _check_sanshoku(self, tiles: List[Tile]) -> bool:
        """
        Sanshoku: Same sequence in all three suits
        Simplified version - checks if same value in pin, sou, man
        """
        counts = tiles_to_counts(tiles)

        # Look for sequences across all suits
        for value in range(9):
            pin_type = value
            sou_type = 9 + value
            man_type = 18 + value

            # Check if each suit has at least one of this value
            if counts[pin_type] >= 1 and counts[sou_type] >= 1 and counts[man_type] >= 1:
                return True

        return False

    def _check_ittsu(self, tiles: List[Tile]) -> bool:
        """
        Ittsu: 1-2-3, 4-5-6, 7-8-9 in same suit
        """
        counts = tiles_to_counts(tiles)

        for suit_ranges in [(PIN_RANGE, "pin"), (SOU_RANGE, "sou"), (MAN_RANGE, "man")]:
            rng, suit_name = suit_ranges

            # Check for sequences at positions 0, 3, 6 (1-3, 4-6, 7-9)
            has_all = True
            for start in [0, 3, 6]:
                t1, t2, t3 = rng[start], rng[start + 1], rng[start + 2]
                if counts[t1] < 1 or counts[t2] < 1 or counts[t3] < 1:
                    has_all = False
                    break

            if has_all:
                return True

        return False

    def _check_honroku(self, tiles: List[Tile], called_melds: List) -> bool:
        """Honroku: Three terminals/honors in melds"""
        terminal_count = sum(1 for t in tiles if t.is_terminal or t.is_honor)
        return terminal_count >= 9  # At least 3 melds worth

    def _check_danyao(self, tiles: List[Tile]) -> bool:
        """Danyao: All terminals and honors"""
        for tile in tiles:
            if tile.is_simple:
                return False
        return True

    def _check_sanankou(self, tiles: List[Tile], called_melds: List) -> bool:
        """San Ankou: Three concealed pons"""
        counts = tiles_to_counts(tiles)

        concealed_pons = 0
        for tile_type in range(34):
            if counts[tile_type] >= 3:
                concealed_pons += 1

        return concealed_pons >= 3

    def _check_sankantsu(self, called_melds: List) -> bool:
        """San Kantsu: Three kans"""
        kan_count = sum(1 for meld in called_melds if meld.type == "kan")
        return kan_count >= 3

    def _check_haitei(self, context: YakuContext) -> bool:
        """Haitei: Last tile from wall"""
        return context.is_haitei

    def _check_houtei(self, context: YakuContext) -> bool:
        """Houtei: Last discard"""
        return context.is_houtei

    def _check_rinshan(self, context: YakuContext) -> bool:
        """Rinshan: Draw after kan"""
        return context.is_rinshan

    def _check_kokushi(self, tiles: List[Tile], is_menzen: bool) -> bool:
        """
        Kokushi Musou: Thirteen orphans
        13 unique terminals/honors + one duplicate
        """
        if not is_menzen:
            return False

        if len(tiles) != 14:
            return False

        counts = tiles_to_counts(tiles)

        # Required tiles: 1,9 of each suit + all honors
        required = set()
        for r in [PIN_RANGE, SOU_RANGE, MAN_RANGE]:
            required.add(r[0])   # 1
            required.add(r[8])   # 9
        for w in range(27, 34):
            required.add(w)

        # Check if exactly 13 unique required tiles + 1 duplicate
        unique_count = sum(1 for t in required if counts[t] > 0)
        total = sum(counts)

        # Must have 13 unique required + 1 extra (could be any of the 13)
        return unique_count == 13 and total == 14

    def _check_chuuren_poto(self, tiles: List[Tile], is_menzen: bool) -> bool:
        """
        Chuuren Poto: Nine gates
        1,1,1,2,3,4,5,6,7,8,9,9,9 + any
        """
        if not is_menzen:
            return False

        if len(tiles) != 14:
            return False

        counts = tiles_to_counts(tiles)

        # Check if all same suit
        suits = set()
        for tile in tiles:
            if not tile.is_suit:
                return False
            suits.add(tile.suit)

        if len(suits) != 1:
            return False

        # Check pattern: 3x1, 1x(2-8), 3x9
        # Need: 1=3, 2-8=1 each, 9=3
        suit_start = 0
        for tile in tiles:
            if tile.is_pin:
                suit_start = 0
                break
            elif tile.is_sou:
                suit_start = 9
                break
            elif tile.is_man:
                suit_start = 18
                break

        required = {
            suit_start: 3,      # 1
            suit_start + 1: 1,  # 2
            suit_start + 2: 1,  # 3
            suit_start + 3: 1,  # 4
            suit_start + 4: 1,  # 5
            suit_start + 5: 1,  # 6
            suit_start + 6: 1,  # 7
            suit_start + 7: 1,  # 8
            suit_start + 8: 3,  # 9
        }

        for tile_type, needed in required.items():
            if counts[tile_type] != needed:
                return False

        return True

    def _check_suuankou(self, tiles: List[Tile], is_menzen: bool) -> bool:
        """Suuankou: Four concealed pons"""
        if not is_menzen:
            return False

        counts = tiles_to_counts(tiles)

        concealed_pons = 0
        for tile_type in range(34):
            if counts[tile_type] >= 3:
                concealed_pons += 1

        return concealed_pons >= 4

    def _check_tsuuiso(self, tiles: List[Tile]) -> bool:
        """Tsuuiso: All honors"""
        return all(tile.is_honor for tile in tiles)

    def _check_ryuuiisou(self, tiles: List[Tile]) -> bool:
        """Ryuuiisou: All green tiles"""
        green_tiles = {10, 11, 12, 14, 16, 32}  # Sou 2,3,4,6,8 and green dragon
        return all(tile.type in green_tiles for tile in tiles)


def detect_yaku(hand_tiles: List[Tile], context: YakuContext) -> List[Yaku]:
    """Quick function to detect yaku"""
    detector = YakuDetector()
    return detector.detect(hand_tiles, context)
