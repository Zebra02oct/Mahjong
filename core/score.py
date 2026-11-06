"""
Mahjong Riichi - Score Calculator
Calculates final score based on han and fu
"""

from dataclasses import dataclass
from typing import List, Optional
from core.tiles import Tile
from core.yaku import Yaku, YakuContext
from core.constants import MANGAN_SCORES, YAKUMAN_LIST


@dataclass
class ScoreResult:
    """Result of score calculation"""
    base_score: int          # Base score before modifiers
    fu: int                 # Fu (minimum points)
    han: int                # Total han
    total_score: int        # Final score
    is_mangan: bool         # Is mangan or higher
    is_yakuman: bool        # Is yakuman
    yaku_list: List[str]    # List of yaku names
    dora_count: int          # Number of dora

    def __str__(self) -> str:
        return f"Score: {self.total_score} (Han: {self.han}, Fu: {self.fu})"


class ScoreCalculator:
    """
    Calculator for Mahjong scores

    Score formula:
    - Han < 5: base = fu * 2^(han+2)
    - Han >= 5: mangan table
    - Yakuman: fixed 8000/12000/16000/24000 depending on han
    """

    # Yakuman base scores (for dealer)
    YAKUMAN_DEALER = 48000  # 32000 * 1.5
    YAKUMAN_NON_DEALER = 32000

    def calculate(self, yaku_list: List[Yaku], fu: int, is_dealer: bool,
                  is_tsumo: bool = False) -> ScoreResult:
        """
        Calculate score from yaku and fu

        Args:
            yaku_list: List of detected yaku
            fu: Fu (minimum points)
            is_dealer: Is the player the dealer
            is_tsumo: Is this a tsumo win

        Returns:
            ScoreResult with final score
        """
        # Calculate total han
        total_han = sum(y.han for y in yaku_list)
        is_yakuman = any(y.is_yakuman for y in yaku_list)

        # Count dora
        dora_count = sum(1 for y in yaku_list if y.name == "dora")

        # Calculate base score
        if is_yakuman:
            base_score = self._calculate_yakuman_score(total_han, is_dealer)
        elif total_han >= 5:
            base_score = self._calculate_mangan_score(total_han, fu)
        else:
            base_score = fu * (2 ** (total_han + 2))

        # Apply dealer multiplier
        if is_dealer:
            base_score *= 2

        # Calculate total (with limit)
        total_score = min(base_score, 80000)  # Cap at 80000 for mangan

        return ScoreResult(
            base_score=base_score,
            fu=fu,
            han=total_han,
            total_score=total_score,
            is_mangan=total_han >= 5 or base_score >= 2000,
            is_yakuman=is_yakuman,
            yaku_list=[y.name for y in yaku_list],
            dora_count=dora_count
        )

    def _calculate_yakuman_score(self, total_han: int, is_dealer: bool) -> int:
        """
        Calculate yakuman score

        Multiple yakuman can stack
        """
        if is_dealer:
            base = self.YAKUMAN_DEALER
        else:
            base = self.YAKUMAN_NON_DEALER

        # If multiple yakuman, multiply
        yakuman_count = total_han // 13
        if yakuman_count == 0:
            yakuman_count = 1

        return base * yakuman_count

    def _calculate_mangan_score(self, han: int, fu: int) -> int:
        """
        Calculate mangan or higher score

        For han >= 5, use mangan table
        """
        if han in MANGAN_SCORES:
            return MANGAN_SCORES[han]
        elif han > 12:
            # Beyond table, calculate yakuman equivalent
            return self.YAKUMAN_DEALER * (han // 13)
        else:
            # Use highest available
            return MANGAN_SCORES[max(MANGAN_SCORES.keys())]

    def calculate_fu(self, hand_tiles: List[Tile], yaku_list: List[Yaku],
                     context: YakuContext, has_pair_wait: bool = False) -> int:
        """
        Calculate fu (minimum points)

        Base fu:
        - Menzen: 30
        - Open: 20

        Additions:
        - Pon of terminals/honors: +4 (menzen) / +2 (open)
        - Kan of terminals/honors: +8 (menzen) / +4 (open)
        - Tsumo: +2
        - Pair of dealer/wind/dragons: +2
        - Pinfu wait (ryanmen): +2
        """
        # Base fu
        fu = 30 if context.is_menzen else 20

        # Add for pair
        pair_tile = self._get_pair_tile(hand_tiles)
        if pair_tile:
            # Dealer pair
            if pair_tile.type == context.round_wind:
                fu += 2
            # Dragon pair
            if pair_tile.type in [31, 32, 33]:  # Dragons
                fu += 2

        # Add for pons/kan
        for tile in hand_tiles:
            count = sum(1 for t in hand_tiles if t.type == tile.type)
            if count >= 3:
                is_menzen = context.is_menzen
                is_terminal_or_honor = tile.is_terminal or tile.is_honor

                if count >= 4:
                    # Kan (adds fu for each kan)
                    fu += 8 if is_menzen else 4
                else:
                    # Pon
                    if is_terminal_or_honor:
                        fu += 4 if is_menzen else 2

        # Tsumo bonus
        if context.is_tsumo:
            fu += 2

        # Pinfu wait bonus
        if any(y.name == "pinfu" for y in yaku_list) and has_pair_wait:
            fu += 2

        # Round up to 10
        fu = ((fu + 9) // 10) * 10

        # Cap at 110
        return min(fu, 110)

    def _get_pair_tile(self, tiles: List[Tile]) -> Optional[Tile]:
        """Find the pair tile in hand"""
        from core.tiles import tiles_to_counts

        counts = tiles_to_counts(tiles)
        for tile_type in range(34):
            if counts[tile_type] >= 2:
                return Tile(tile_type)
        return None

    def calculate_payment(self, result: ScoreResult, is_tsumo: bool,
                        is_dealer: bool, num_players: int = 4) -> dict:
        """
        Calculate how score is paid (for tsumo)

        Args:
            result: ScoreResult
            is_tsumo: Is tsumo win
            is_dealer: Is winner the dealer
            num_players: Number of players

        Returns:
            Payment breakdown
        """
        if not is_tsumo:
            # Ron - loser pays all
            return {
                "winner": result.total_score,
                "from_other": result.total_score
            }

        # Tsumo payment
        if is_dealer:
            # Dealer pays full amount
            per_person = result.total_score
            return {
                "winner": result.total_score * 3,  # Gets 3x
                "from_dealer": per_person,
                "from_others": per_person * 2
            }
        else:
            # Non-dealer: dealer pays more
            dealer_pays = (result.total_score // 4) * 2  # 50% from dealer
            others_pay = result.total_score // 4  # 25% each

            return {
                "winner": result.total_score,
                "from_dealer": dealer_pays,
                "from_others": others_pay
            }

    def format_score(self, result: ScoreResult) -> str:
        """Format score result for display"""
        lines = []
        lines.append("=" * 40)
        lines.append("SCORE RESULT")
        lines.append("=" * 40)
        lines.append(f"Han: {result.han}")
        lines.append(f"Fu: {result.fu}")

        if result.is_yakuman:
            lines.append("YAKUMAN!")
        elif result.is_mangan:
            lines.append("MANGAN or higher")

        lines.append(f"Total: {result.total_score}")
        lines.append("-" * 40)
        lines.append("Yaku:")
        for yaku in result.yaku_list:
            lines.append(f"  - {yaku}")

        if result.dora_count > 0:
            lines.append(f"Dora: {result.dora_count}")

        lines.append("=" * 40)
        return "\n".join(lines)


def calculate_score(yaku_list: List[Yaku], fu: int, is_dealer: bool,
                   is_tsumo: bool = False) -> ScoreResult:
    """Quick function to calculate score"""
    calc = ScoreCalculator()
    return calc.calculate(yaku_list, fu, is_dealer, is_tsumo)
