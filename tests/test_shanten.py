"""
Tests for Shanten Calculator
"""

import pytest
from core.tiles import Tile, tiles_to_counts
from core.shanten import ShantenCalculator, calculate_shanten, is_tenpai, is_agari


class TestShantenCalculator:
    """Tests for ShantenCalculator"""

    def setup_method(self):
        """Setup for each test"""
        self.calc = ShantenCalculator()

    def test_empty_hand(self):
        """Test empty hand"""
        shanten = self.calc.calculate_shanten([])
        assert shanten == 4  # Need 4 melds + 1 pair

    def test_one_tile(self):
        """Test hand with 1 tile"""
        tiles = [Tile(0)]
        shanten = self.calc.calculate_shanten(tiles)
        assert shanten >= 3  # Far from tenpai

    def test_basic_agari(self):
        """Test already winning hand (14 tiles, complete)"""
        # This should be a winning hand
        # 4 melds + 1 pair = 14 tiles
        tiles = [
            Tile(0), Tile(0), Tile(0),  # Pon pin 1
            Tile(1), Tile(2), Tile(3),  # Chi pin 1-2-3
            Tile(4), Tile(5), Tile(6),  # Chi pin 4-5-6
            Tile(7), Tile(8), Tile(8),  # Chi pin 7-8-9
            Tile(9), Tile(9),            # Pair sou 1
        ]
        shanten = self.calc.calculate_shanten(tiles)
        assert shanten == -1  # Already winning

    def test_tenpai(self):
        """Test tenpai hand (one tile away)"""
        # 13 tiles, needs one more to win
        tiles = [
            Tile(0), Tile(0), Tile(0),  # Pon pin 1
            Tile(1), Tile(2), Tile(3),  # Chi pin 1-2-3
            Tile(4), Tile(5), Tile(6),  # Chi pin 4-5-6
            Tile(7), Tile(8), Tile(8),  # Chi pin 7-8-9
            Tile(9),                     # Waiting for tile 9
        ]
        shanten = self.calc.calculate_shanten(tiles)
        assert shanten == 0  # Tenpai

    def test_wait_tiles(self):
        """Test wait tile detection"""
        # Tenpai hand
        tiles = [
            Tile(0), Tile(0), Tile(0),  # Pon pin 1
            Tile(1), Tile(2), Tile(3),  # Chi pin 1-2-3
            Tile(4), Tile(5), Tile(6),  # Chi pin 4-5-6
            Tile(7), Tile(8), Tile(8),  # Chi pin 7-8-9
            Tile(9),                     # Waiting
        ]

        waits = self.calc.get_wait_tiles(tiles)
        assert 9 in waits  # Waiting for sou 1

    def test_is_tenpai(self):
        """Test tenpai check"""
        # Tenpai hand
        tenpai_tiles = [
            Tile(0), Tile(0), Tile(0),
            Tile(1), Tile(2), Tile(3),
            Tile(4), Tile(5), Tile(6),
            Tile(7), Tile(8), Tile(8),
            Tile(9),
        ]
        assert self.calc.is_tenpai(tenpai_tiles)

        # Not tenpai
        far_tiles = [Tile(0) for _ in range(13)]
        assert not self.calc.is_tenpai(far_tiles)

    def test_is_agari(self):
        """Test agari check"""
        # Winning hand
        winning_tiles = [
            Tile(0), Tile(0), Tile(0),
            Tile(1), Tile(2), Tile(3),
            Tile(4), Tile(5), Tile(6),
            Tile(7), Tile(8), Tile(8),
            Tile(9), Tile(9),
        ]
        assert self.calc.is_agari(winning_tiles)

        # Not winning
        losing_tiles = [Tile(0) for _ in range(13)]
        assert not self.calc.is_agari(losing_tiles)

    def test_multiple_wait(self):
        """Test hand with multiple wait tiles"""
        # Tenpai with ryanmen wait (waiting for 2 tiles)
        tiles = [
            Tile(0), Tile(1),            # Waiting for 2 or 3
            Tile(1), Tile(2),            # Partial chi
            Tile(3), Tile(3), Tile(3),  # Pon
            Tile(4), Tile(4), Tile(4),  # Pon
            Tile(5), Tile(5),            # Pair
        ]
        shanten = self.calc.calculate_shanten(tiles)
        assert shanten == 0  # Tenpai

        waits = self.calc.get_wait_tiles(tiles)
        # Should be waiting for 0 or 2
        assert len(waits) >= 1

    def test_shanten_function(self):
        """Test standalone function"""
        tiles = [Tile(0) for _ in range(13)]
        shanten = calculate_shanten(tiles)
        assert shanten >= 0

    def test_is_tenpai_function(self):
        """Test standalone tenpai function"""
        tiles = [Tile(0) for _ in range(13)]
        assert not is_tenpai(tiles)

    def test_is_agari_function(self):
        """Test standalone agari function"""
        tiles = [Tile(0) for _ in range(13)]
        assert not is_agari(tiles)


class TestShantenEdgeCases:
    """Edge case tests for shanten"""

    def setup_method(self):
        self.calc = ShantenCalculator()

    def test_full_hand(self):
        """Test 14 tile hand"""
        tiles = [Tile(i % 34) for i in range(14)]
        shanten = self.calc.calculate_shanten(tiles)
        assert shanten >= -1

    def test_same_tiles(self):
        """Test hand with same tiles"""
        tiles = [Tile(0) for _ in range(13)]
        shanten = self.calc.calculate_shanten(tiles)
        # Should be far from tenpai
        assert shanten > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
