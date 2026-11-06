"""
Mahjong Riichi - AI Module
AI player implementations
"""

from ai.base_ai import BaseAI
from ai.random_ai import RandomAI
from ai.basic_ai import BasicAI
from ai.advanced_ai import AdvancedAI
from ai.expert_ai import ExpertAI


def create_ai(player_id: int, difficulty: int) -> BaseAI:
    """
    Factory function to create AI by difficulty level

    Args:
        player_id: Player ID
        difficulty: 1-4 (Random, Basic, Advanced, Expert)

    Returns:
        AI instance
    """
    if difficulty == 1:
        return RandomAI(player_id, difficulty)
    elif difficulty == 2:
        return BasicAI(player_id, difficulty)
    elif difficulty == 3:
        return AdvancedAI(player_id, difficulty)
    elif difficulty >= 4:
        return ExpertAI(player_id, difficulty)
    else:
        return RandomAI(player_id, 1)


__all__ = [
    'BaseAI',
    'RandomAI',
    'BasicAI',
    'AdvancedAI',
    'ExpertAI',
    'create_ai',
]
