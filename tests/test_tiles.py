"""
Tests for Tile and Deck functionality
"""

import pytest
from core.tiles import Tile, tiles_to_counts, counts_to_tiles, sort_tiles
from core.deck import Deck, create_standard_deck


class TestTile:
    """Tests for Tile class"""

    def test_tile_creation(self):
        """Test basic tile creation"""
        tile = Tile(0)  # 1-pin
        assert tile.type == 0
        assert tile.suit == "pin"
        assert tile.value == 1

    def test_tile_properties(self):
        """Test tile properties"""
        # Terminal
        tile = Tile(0)  # 1-pin
        assert tile.is_terminal
        assert not tile.is_simple

        tile = Tile(8)  # 9-pin
        assert tile.is_terminal

        # Simple
        tile = Tile(1)  # 2-pin
        assert tile.is_simple
        assert not tile.is_terminal

        # Honor
        tile = Tile(27)  # East
        assert tile.is_honor
        assert tile.is_wind

        tile = Tile(31)  # White dragon
        assert tile.is_honor
        assert tile.is_dragon

    def test_tile_suit(self):
        """Test suit identification"""
        # Pin
        for i in range(9):
            tile = Tile(i)
            assert tile.suit == "pin"

        # Sou
        for i in range(9, 18):
            tile = Tile(i)
            assert tile.suit == "sou"

        # Man
        for i in range(18, 27):
            tile = Tile(i)
            assert tile.suit == "man"

    def test_tile_invalid(self):
        """Test invalid tile type"""
        with pytest.raises(ValueError):
            Tile(34)  # Invalid

        with pytest.raises(ValueError):
            Tile(-1)  # Invalid


class TestDeck:
    """Tests for Deck class"""

    def test_deck_creation(self):
        """Test deck creation"""
        deck = Deck()
        assert len(deck.tiles) == 136

    def test_deck_shuffle(self):
        """Test deck shuffling"""
        deck1 = Deck(seed=42)
        deck2 = Deck(seed=42)
        deck1.shuffle()
        deck2.shuffle()

        # Same seed should produce same order after shuffle
        assert len(deck1.tiles) == len(deck2.tiles)

    def test_deck_draw(self):
        """Test drawing tiles"""
        deck = Deck()
        initial_count = len(deck.tiles)

        tile = deck.draw(1)
        assert len(tile) == 1
        assert len(deck.tiles) == initial_count - 1

        tiles = deck.draw(5)
        assert len(tiles) == 5
        assert len(deck.tiles) == initial_count - 6

    def test_deck_player_hand(self):
        """Test drawing player hand"""
        deck = Deck()
        hand = deck.draw_player_hand()
        assert len(hand) == 13

    def test_deck_remaining(self):
        """Test remaining tile count"""
        deck = Deck()
        assert deck.remaining == 136

        deck.draw(13)
        assert deck.remaining == 123

    def test_create_standard_deck(self):
        """Test factory function"""
        deck = create_standard_deck(seed=123)
        assert len(deck.tiles) == 136


class TestTilesConversion:
    """Tests for tile conversion functions"""

    def test_tiles_to_counts(self):
        """Test converting tiles to counts"""
        tiles = [Tile(0), Tile(0), Tile(1), Tile(8), Tile(9)]
        counts = tiles_to_counts(tiles)

        assert counts[0] == 2
        assert counts[1] == 1
        assert counts[8] == 1
        assert counts[9] == 1

    def test_counts_to_tiles(self):
        """Test converting counts to tiles"""
        counts = [0] * 34
        counts[0] = 2
        counts[1] = 1

        tiles = counts_to_tiles(counts)
        assert len(tiles) == 3

    def test_sort_tiles(self):
        """Test sorting tiles"""
        tiles = [Tile(8), Tile(0), Tile(1), Tile(9)]
        sorted_tiles = sort_tiles(tiles, by="type")

        assert sorted_tiles[0].type == 0
        assert sorted_tiles[1].type == 1
        assert sorted_tiles[2].type == 8
        assert sorted_tiles[3].type == 9
