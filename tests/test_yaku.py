"""
Tests for Yaku Detection
"""

import pytest
from core.tiles import Tile
from core.yaku import YakuDetector, YakuContext, detect_yaku
from core.meld import Meld


class TestYakuDetector:
    """Tests for YakuDetector"""

    def setup_method(self):
        """Setup for each test"""
        self.detector = YakuDetector()

    def test_tanyao(self):
        """Test Tanyao (All Simples)"""
        # Hand with only simples (2-8)
        tiles = [
            Tile(1), Tile(2), Tile(3),  # Chi 2-3-4 pin
            Tile(4), Tile(5), Tile(6),  # Chi 5-6-7 pin
            Tile(7), Tile(8), Tile(9),  # Chi 8-9-10 (10=sou 1)
            Tile(10), Tile(10), Tile(10),  # Pon sou 2
            Tile(11), Tile(11),            # Pair sou 3
        ]

        context = YakuContext(is_menzen=True)
        yaku = self.detector.detect(tiles, context)

        yaku_names = [y.name for y in yaku]
        assert "tanyao" in yaku_names

    def test_tanyao_with_terminal(self):
        """Test Tanyao fails with terminals"""
        tiles = [
            Tile(0), Tile(1), Tile(2),  # Chi with terminal 1
            Tile(4), Tile(5), Tile(6),
            Tile(7), Tile(8), Tile(9),
            Tile(10), Tile(10), Tile(10),
            Tile(11), Tile(11),
        ]

        context = YakuContext(is_menzen=True)
        yaku = self.detector.detect(tiles, context)

        yaku_names = [y.name for y in yaku]
        assert "tanyao" not in yaku_names

    def test_honitsu(self):
        """Test Half Flush (Honitsu)"""
        # Pin suit + honor tiles
        tiles = [
            Tile(0), Tile(1), Tile(2),  # Pin 1-2-3
            Tile(3), Tile(4), Tile(5),  # Pin 4-5-6
            Tile(6), Tile(7), Tile(8),  # Pin 7-8-9
            Tile(27), Tile(27), Tile(27),  # Pon East
            Tile(31), Tile(31),            # Pair White Dragon
        ]

        context = YakuContext(is_menzen=True)
        yaku = self.detector.detect(tiles, context)

        yaku_names = [y.name for y in yaku]
        assert "honitsu" in yaku_names

    def test_chinitsu(self):
        """Test Full Flush (Chinitsu)"""
        # All one suit
        tiles = [
            Tile(0), Tile(0), Tile(0),  # Pon 1
            Tile(1), Tile(2), Tile(3),  # Chi 1-2-3
            Tile(4), Tile(5), Tile(6),  # Chi 4-5-6
            Tile(7), Tile(8), Tile(8),  # Chi 7-8-9
            Tile(9), Tile(9),            # Pair 1
        ]

        context = YakuContext(is_menzen=True)
        yaku = self.detector.detect(tiles, context)

        yaku_names = [y.name for y in yaku]
        assert "chinitsu" in yaku_names

    def test_toitoi(self):
        """Test Toitoi (All Pons)"""
        tiles = [
            Tile(0), Tile(0), Tile(0),  # Pon 1
            Tile(1), Tile(1), Tile(1),  # Pon 2
            Tile(2), Tile(2), Tile(2),  # Pon 3
            Tile(3), Tile(3), Tile(3),  # Pon 4
            Tile(4), Tile(4),            # Pair 5
        ]

        context = YakuContext(is_menzen=True)
        yaku = self.detector.detect(tiles, context)

        yaku_names = [y.name for y in yaku]
        assert "toitoi" in yaku_names

    def test_menzen_tsumo(self):
        """Test Menzen Tsumo"""
        # Complete hand, won by tsumo
        tiles = [
            Tile(0), Tile(0), Tile(0),
            Tile(1), Tile(2), Tile(3),
            Tile(4), Tile(5), Tile(6),
            Tile(7), Tile(8), Tile(8),
            Tile(9), Tile(9),
        ]

        context = YakuContext(is_menzen=True, is_tsumo=True)
        yaku = self.detector.detect(tiles, context)

        yaku_names = [y.name for y in yaku]
        assert "menzen_tsumo" in yaku_names

    def test_riichi(self):
        """Test Riichi"""
        tiles = [
            Tile(0), Tile(0), Tile(0),
            Tile(1), Tile(2), Tile(3),
            Tile(4), Tile(5), Tile(6),
            Tile(7), Tile(8), Tile(8),
            Tile(9), Tile(9),
        ]

        context = YakuContext(is_riichi=True)
        yaku = self.detector.detect(tiles, context)

        yaku_names = [y.name for y in yaku]
        assert "reach" in yaku_names

    def test_tsuuiso(self):
        """Test Tsuuiso (All Honors)"""
        tiles = [
            Tile(27), Tile(27), Tile(27),  # Pon East
            Tile(28), Tile(28), Tile(28),  # Pon South
            Tile(29), Tile(29), Tile(29),  # Pon West
            Tile(30), Tile(30), Tile(30),  # Pon North
            Tile(31), Tile(31),            # Pair White
        ]

        context = YakuContext(is_menzen=True)
        yaku = self.detector.detect(tiles, context)

        yaku_names = [y.name for y in yaku]
        assert "tsuuiso" in yaku_names

    def test_ryuuiisou(self):
        """Test Ryuuiisou (All Green)"""
        # Green tiles: sou 2,3,4,6,8 and green dragon
        tiles = [
            Tile(10), Tile(10), Tile(10),  # Pon sou 2
            Tile(11), Tile(11), Tile(11),  # Pon sou 3
            Tile(12), Tile(12), Tile(12),  # Pon sou 4
            Tile(14), Tile(14), Tile(14),  # Pon sou 6
            Tile(16), Tile(16),            # Pair sou 8
        ]

        context = YakuContext(is_menzen=True)
        yaku = self.detector.detect(tiles, context)

        yaku_names = [y.name for y in yaku]
        assert "ryuuiisou" in yaku_names


class TestDetectYaku:
    """Tests for detect_yaku function"""

    def test_detect_yaku_function(self):
        """Test standalone detect_yaku function"""
        tiles = [
            Tile(0), Tile(0), Tile(0),
            Tile(1), Tile(2), Tile(3),
            Tile(4), Tile(5), Tile(6),
            Tile(7), Tile(8), Tile(8),
            Tile(9), Tile(9),
        ]

        context = YakuContext(is_riichi=True, is_tsumo=True)
        yaku = detect_yaku(tiles, context)

        assert len(yaku) > 0
        yaku_names = [y.name for y in yaku]
        assert "reach" in yaku_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
