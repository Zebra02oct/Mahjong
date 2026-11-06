"""
Tests for AI players
"""

import pytest
from core.tiles import Tile
from core.deck import create_standard_deck
from engine.game_state import GameState, create_new_game
from ai.random_ai import RandomAI
from ai.basic_ai import BasicAI
from ai.advanced_ai import AdvancedAI
from ai import create_ai


class TestRandomAI:
    """Tests for RandomAI"""

    def test_ai_creation(self):
        """Test AI creation"""
        ai = RandomAI(player_id=0)
        assert ai.player_id == 0
        assert ai.difficulty == 1

    def test_decide_discard(self):
        """Test discard decision"""
        ai = RandomAI(player_id=0)
        game = create_new_game(seed=42)

        # Draw hand
        for i in range(4):
            for _ in range(13):
                tile = game.deck.draw(1)[0]
                game.players[i].hand.append(tile)

        # AI should return a tile
        tile = ai.decide_discard(game)
        assert tile is not None
        assert isinstance(tile, Tile)

    def test_decide_call_ron(self):
        """Test ron decision"""
        ai = RandomAI(player_id=1)
        game = create_new_game(seed=42)

        # Setup
        for i in range(4):
            for _ in range(13):
                tile = game.deck.draw(1)[0]
                game.players[i].hand.append(tile)

        # Should return True or False
        result = ai.decide_call(game, "ron", Tile(0))
        assert isinstance(result, bool)


class TestBasicAI:
    """Tests for BasicAI"""

    def test_ai_creation(self):
        """Test AI creation"""
        ai = BasicAI(player_id=0)
        assert ai.player_id == 0
        assert ai.difficulty == 2

    def test_decide_discard(self):
        """Test discard decision"""
        ai = BasicAI(player_id=0)
        game = create_new_game(seed=42)

        # Draw hand
        for i in range(4):
            for _ in range(13):
                tile = game.deck.draw(1)[0]
                game.players[i].hand.append(tile)

        # AI should return a tile
        tile = ai.decide_discard(game)
        assert tile is not None
        assert isinstance(tile, Tile)


class TestAdvancedAI:
    """Tests for AdvancedAI"""

    def test_ai_creation(self):
        """Test AI creation"""
        ai = AdvancedAI(player_id=0)
        assert ai.player_id == 0
        assert ai.difficulty == 3

    def test_decide_discard(self):
        """Test discard decision"""
        ai = AdvancedAI(player_id=0)
        game = create_new_game(seed=42)

        # Draw hand
        for i in range(4):
            for _ in range(13):
                tile = game.deck.draw(1)[0]
                game.players[i].hand.append(tile)

        # AI should return a tile
        tile = ai.decide_discard(game)
        assert tile is not None
        assert isinstance(tile, Tile)

    def test_defense_score(self):
        """Test defense scoring"""
        ai = AdvancedAI(player_id=0)
        game = create_new_game(seed=42)

        # Draw hand
        for i in range(4):
            for _ in range(13):
                tile = game.deck.draw(1)[0]
                game.players[i].hand.append(tile)

        # Add some discards
        game.players[1].discards.append(Tile(0))
        game.players[1].discards.append(Tile(0))

        # Honor tile should be safer
        honor_tile = Tile(27)  # East
        danger = ai.get_tile_danger(honor_tile, game)
        assert 0 <= danger <= 1


class TestCreateAI:
    """Tests for AI factory function"""

    def test_create_ai_level_1(self):
        """Test creating level 1 AI"""
        ai = create_ai(0, 1)
        assert isinstance(ai, RandomAI)

    def test_create_ai_level_2(self):
        """Test creating level 2 AI"""
        ai = create_ai(0, 2)
        assert isinstance(ai, BasicAI)

    def test_create_ai_level_3(self):
        """Test creating level 3 AI"""
        ai = create_ai(0, 3)
        assert isinstance(ai, AdvancedAI)

    def test_create_ai_default(self):
        """Test creating AI with invalid level defaults to RandomAI"""
        ai = create_ai(0, 0)
        assert isinstance(ai, RandomAI)


class TestAIIntegration:
    """Integration tests for AI in game"""

    def test_ai_game_simulation(self):
        """Test running a few turns with AI"""
        game = create_new_game(seed=42)

        # Setup AI players
        ai1 = BasicAI(0)
        ai2 = BasicAI(1)
        ai3 = BasicAI(2)
        ai4 = BasicAI(3)

        game.players[0].is_ai = True
        game.players[1].is_ai = True
        game.players[2].is_ai = True
        game.players[3].is_ai = True

        # Run a few turns
        for _ in range(16):  # 4 players × 4 turns
            current = game.current_turn
            player = game.players[current]

            # Draw
            tile = game.deck.draw(1)
            if not tile:
                break
            player.draw_tile(tile[0])

            # AI discard
            if current == 0:
                discard = ai1.decide_discard(game)
            elif current == 1:
                discard = ai2.decide_discard(game)
            elif current == 2:
                discard = ai3.decide_discard(game)
            else:
                discard = ai4.decide_discard(game)

            if discard:
                game.discard_tile(current, discard)

            # Next turn
            game.next_turn()

        # Game should still be running
        assert game.deck.remaining >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
