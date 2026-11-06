"""
Tests for Score Calculator
"""

import pytest
from core.tiles import Tile
from core.yaku import Yaku, YakuContext
from core.score import ScoreCalculator, ScoreResult, calculate_score


class TestScoreCalculator:
    """Tests for ScoreCalculator"""

    def setup_method(self):
        """Setup for each test"""
        self.calc = ScoreCalculator()

    def test_basic_score(self):
        """Test basic score calculation"""
        # Simple hand with tanyao (1 han) and menzen tsumo (1 han)
        yaku_list = [
            Yaku("tanyao", 1),
            Yaku("menzen_tsumo", 1),
        ]

        result = self.calc.calculate(yaku_list, 30, is_dealer=False, is_tsumo=True)

        assert result.han == 2
        assert result.fu == 30
        assert result.total_score > 0

    def test_menzen_tsumo(self):
        """Test menzen tsumo score"""
        yaku_list = [
            Yaku("menzen_tsumo", 1),
            Yaku("pinfu", 1),
        ]

        result = self.calc.calculate(yaku_list, 30, is_dealer=False, is_tsumo=True)

        assert result.han == 2
        assert result.total_score > 0

    def test_dealer_multiplier(self):
        """Test dealer multiplier"""
        yaku_list = [Yaku("tanyao", 1)]

        result_dealer = self.calc.calculate(yaku_list, 30, is_dealer=True)
        result_non_dealer = self.calc.calculate(yaku_list, 30, is_dealer=False)

        # Dealer should get more points
        assert result_dealer.total_score >= result_non_dealer.total_score

    def test_mangan_score(self):
        """Test mangan score"""
        # 5 han should be mangan
        yaku_list = [
            Yaku("tanyao", 1),
            Yaku("pinfu", 1),
            Yaku("honitsu", 2),
        ]

        result = self.calc.calculate(yaku_list, 30, is_dealer=False)

        assert result.is_mangan
        assert result.han >= 5

    def test_yakuman(self):
        """Test yakuman score"""
        yaku_list = [
            Yaku("kokushi_musou", 13, is_yakuman=True),
        ]

        result_dealer = self.calc.calculate(yaku_list, 0, is_dealer=True)
        result_non = self.calc.calculate(yaku_list, 0, is_dealer=False)

        assert result_dealer.is_yakuman
        assert result_non.is_yakuman
        assert result_dealer.total_score > result_non.total_score

    def test_dora_in_score(self):
        """Test dora in score"""
        yaku_list = [
            Yaku("tanyao", 1),
            Yaku("dora", 2),  # 2 dora
        ]

        result = self.calc.calculate(yaku_list, 30, is_dealer=False)

        assert result.dora_count == 2

    def test_calculate_fu(self):
        """Test fu calculation"""
        tiles = [
            Tile(0), Tile(0), Tile(0),  # Pon
            Tile(1), Tile(2), Tile(3),
            Tile(4), Tile(5), Tile(6),
            Tile(7), Tile(8), Tile(8),
            Tile(9), Tile(9),
        ]

        yaku_list = [Yaku("tanyao", 1)]
        context = YakuContext(is_menzen=True, is_tsumo=True)

        fu = self.calc.calculate_fu(tiles, yaku_list, context)

        assert fu >= 30  # Base menzen fu
        assert fu <= 110  # Max fu

    def test_format_score(self):
        """Test score formatting"""
        result = ScoreResult(
            base_score=2000,
            fu=30,
            han=2,
            total_score=4000,
            is_mangan=False,
            is_yakuman=False,
            yaku_list=["tanyao", "pinfu"],
            dora_count=0
        )

        formatted = self.calc.format_score(result)

        assert "SCORE RESULT" in formatted
        assert "Han: 2" in formatted
        assert "Fu: 30" in formatted
        assert "Total: 4000" in formatted


class TestCalculateScore:
    """Tests for standalone calculate_score function"""

    def test_calculate_score_function(self):
        """Test standalone function"""
        yaku_list = [Yaku("tanyao", 1)]
        result = calculate_score(yaku_list, 30, is_dealer=False)

        assert isinstance(result, ScoreResult)
        assert result.total_score > 0


class TestScoreEdgeCases:
    """Edge case tests for scoring"""

    def setup_method(self):
        self.calc = ScoreCalculator()

    def test_no_yaku(self):
        """Test with no yaku (invalid win)"""
        yaku_list = []
        result = self.calc.calculate(yaku_list, 30, is_dealer=False)

        # Should still calculate but han is 0
        assert result.han == 0

    def test_multiple_yakuman(self):
        """Test multiple yakuman"""
        yaku_list = [
            Yaku("suuankou", 13, is_yakuman=True),
            Yaku("tenhou", 13, is_yakuman=True),
        ]

        result = self.calc.calculate(yaku_list, 0, is_dealer=True)

        assert result.is_yakuman
        assert result.han >= 26


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
