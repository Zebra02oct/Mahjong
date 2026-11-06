#!/usr/bin/env python3
"""
Sweet Bonanza Multiplier System - Hybrid Implementation

Features:
1. Candy Bomb multipliers (appear on reels)
2. Global Accumulator (builds across tumble chain)
3. Conservative range: 2x-25x
4. Enhanced Free Spins with boosted multipliers
"""

import random
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field
from enum import Enum


class MultiplierSource(Enum):
    """Where the multiplier comes from"""
    CANDY_BOMB = "candy_bomb"      # Random bomb on reels
    ACCUMULATED = "accumulated"     # Built up from tumble chain


@dataclass
class MultiplierResult:
    """Result of multiplier calculation"""
    value: int
    source: MultiplierSource
    is_new: bool = False  # First time this multiplier appeared


@dataclass
class TumbleStep:
    """One step in the tumble chain"""
    step_number: int
    base_win: int
    active_multipliers: List[int]  # List of active multipliers this step
    accumulated_multiplier: int     # Running total
    step_payout: int              # Payout for this step
    symbols_removed: List[Tuple]   # Which symbols were removed
    bombs_triggered: int           # How many bombs exploded


class SweetBonanzaMultiplierSystem:
    """
    Hybrid Multiplier System for Sweet Bonanza

    How it works:

    1. CANDY BOMBS (on reels):
       - Appear randomly on 5-15% of spins
       - When a cluster wins AND bomb is adjacent to cluster:
         → Bomb explodes and adds its multiplier to global accumulator

    2. GLOBAL ACCUMULATOR:
       - Multiplier starts at 0
       - Each bomb explosion ADDS to accumulator
       - Accumulator persists across tumble chain
       - Resets at end of spin

    3. FREE SPINS MODE:
       - Multiplier starts at 0 (same as base game)
       - BUT bombs are more frequent (2x chance)
       - AND higher value bombs more likely
       - Multiplier doesn't reset between free spins

    Example tumble chain:
    Step 1: 8 🍬 = $100, no bombs → Payout: $100 × 1 = $100
    Step 2: 💥5x + 6 🍬 = $80   → Accumulator: 5  → Payout: $80 × 5 = $400
    Step 3: 💥3x + 7 🍇 = $120  → Accumulator: 8  → Payout: $120 × 8 = $960
    Step 4: 💥10x + 5 🍌 = $150  → Accumulator: 18 → Payout: $150 × 18 = $2700

    TOTAL WIN = $100 + $400 + $960 + $2700 = $4,160
    """

    # ============================================================
    # MULTIPLIER POOL CONFIGURATION
    # ============================================================

    # VERY CONSERVATIVE RANGE: 2x - 10x
    BASE_GAME_MULTIPLIERS = {
        # Very Common (80%)
        2: 40,   # 40% chance
        3: 25,   # 25% chance
        5: 15,   # 15% chance
        # Rare (20%)
        8: 12,   # 12% chance
        10: 8,   # 8% chance
    }

    # FREE SPINS MODE - More generous but still capped
    FREE_SPINS_MULTIPLIERS = {
        # Common (70%)
        2: 35,
        3: 25,
        5: 18,
        # Less common (30%)
        8: 10,
        10: 7,
        15: 5,
    }

    # ============================================================
    # BOMB SPAWN CONFIGURATION
    # ============================================================

    # Chance of bomb appearing in a reel
    BASE_GAME_BOMB_CHANCE = 0.03       # 3% (very rare)
    FREE_SPINS_BOMB_CHANCE = 0.08      # 8% (still rare)

    # How many symbols can have bombs per row
    MAX_BOMBS_PER_ROW = 2

    def __init__(self, is_free_spins: bool = False):
        self.is_free_spins = is_free_spins
        self.accumulated_multiplier = 0
        self.multiplier_history: List[MultiplierResult] = []
        self.total_bombs_triggered = 0

    def reset(self):
        """Reset for new spin"""
        self.accumulated_multiplier = 0
        self.multiplier_history.clear()
        self.total_bombs_triggered = 0

    # ============================================================
    # MULTIPLIER GENERATION
    # ============================================================

    def get_multiplier_pool(self) -> Dict[int, int]:
        """Get the multiplier pool based on mode"""
        return (self.FREE_SPINS_MULTIPLIERS if self.is_free_spins
                else self.BASE_GAME_MULTIPLIERS)

    def get_bomb_chance(self) -> float:
        """Get bomb spawn chance"""
        return (self.FREE_SPINS_BOMB_CHANCE if self.is_free_spins
                else self.BASE_GAME_BOMB_CHANCE)

    def generate_random_multiplier(self) -> int:
        """
        Generate a random multiplier based on probability distribution
        Uses weighted random selection
        """
        pool = self.get_multiplier_pool()
        weights = []
        values = []

        for mult, weight in pool.items():
            weights.append(weight)
            values.append(mult)

        # Weighted random selection
        total_weight = sum(weights)
        rand = random.randint(1, total_weight)

        cumulative = 0
        for weight, value in zip(weights, values):
            cumulative += weight
            if rand <= cumulative:
                return value

        return values[-1]  # Fallback to lowest

    # ============================================================
    # BOMB PLACEMENT
    # ============================================================

    def should_spawn_bomb(self) -> bool:
        """Determine if a bomb should spawn"""
        return random.random() < self.get_bomb_chance()

    def generate_bomb_position(self, rows: int, cols: int,
                               existing_bombs: set) -> Optional[Tuple[int, int]]:
        """
        Generate a random bomb position
        Returns (row, col) or None if no bomb
        """
        if not self.should_spawn_bomb():
            return None

        # Find available positions
        available = []
        for r in range(rows):
            for c in range(cols):
                if (r, c) not in existing_bombs:
                    available.append((r, c))

        if not available:
            return None

        return random.choice(available)

    def generate_bombs_for_reel(self, rows: int, cols: int,
                                existing_bombs: set = None) -> Dict[Tuple[int, int], int]:
        """
        Generate bombs for a single reel
        Returns dict of {(row, col): multiplier_value}
        """
        if existing_bombs is None:
            existing_bombs = set()

        bombs = {}
        bombs_per_reel = random.randint(0, self.MAX_BOMBS_PER_ROW)

        for _ in range(bombs_per_reel):
            pos = self.generate_bomb_position(rows, cols, existing_bombs | set(bombs.keys()))
            if pos:
                bombs[pos] = self.generate_random_multiplier()

        return bombs

    def generate_bombs_for_grid(self, rows: int, cols: int) -> Dict[Tuple[int, int], int]:
        """
        Generate bombs for entire grid
        Each reel has independent bomb chance
        """
        all_bombs = {}

        for c in range(cols):
            reel_bombs = self.generate_bomb_position(rows, cols, set(all_bombs.keys()))
            if reel_bombs:
                all_bombs[reel_bombs] = self.generate_random_multiplier()

        return all_bombs

    # ============================================================
    # MULTIPLIER APPLICATION
    # ============================================================

    def trigger_bomb(self, position: Tuple[int, int]) -> int:
        """
        Trigger a bomb at position and add to accumulator
        Returns the multiplier value
        """
        multiplier = self.generate_random_multiplier()

        # Add to accumulated multiplier
        self.accumulated_multiplier += multiplier

        # Record history
        self.multiplier_history.append(MultiplierResult(
            value=multiplier,
            source=MultiplierSource.CANDY_BOMB,
            is_new=True
        ))

        self.total_bombs_triggered += 1

        return multiplier

    def get_accumulated_multiplier(self) -> int:
        """Get current accumulated multiplier"""
        return self.accumulated_multiplier

    def calculate_step_payout(self, base_win: int,
                              bombs_in_cluster: List[Tuple[int, int]]) -> Tuple[int, List[int]]:
        """
        Calculate payout for one tumble step

        Returns: (final_payout, new_multipliers_triggered)
        """
        new_multipliers = []

        # Trigger bombs that are adjacent to winning cluster
        for pos in bombs_in_cluster:
            mult = self.trigger_bomb(pos)
            new_multipliers.append(mult)

        # Calculate final payout
        if self.accumulated_multiplier > 0:
            final_payout = base_win * self.accumulated_multiplier
        else:
            final_payout = base_win

        return final_payout, new_multipliers

    # ============================================================
    # TUMBLE CHAIN PROCESSING
    # ============================================================

    def process_tumble_chain(self, tumble_results: List[Dict],
                           bombs_per_step: List[Dict[Tuple[int, int], int]]) -> List[TumbleStep]:
        """
        Process complete tumble chain with multipliers

        Args:
            tumble_results: List of {positions, base_win} for each step
            bombs_per_step: Bombs that were on the grid for each step

        Returns:
            List of TumbleStep with full multiplier info
        """
        self.reset()
        steps = []

        for step_num, (result, bombs) in enumerate(zip(tumble_results, bombs_per_step)):
            base_win = result.get('base_win', 0)
            positions = result.get('positions', [])

            # Find bombs adjacent to winning positions
            bombs_in_win = self._find_adjacent_bombs(positions, bombs)

            # Trigger bombs and get multipliers
            new_mults = []
            for bomb_pos in bombs_in_win:
                mult = self.trigger_bomb(bomb_pos)
                new_mults.append(mult)

            # Calculate step payout
            if self.accumulated_multiplier > 0:
                step_payout = base_win * self.accumulated_multiplier
            else:
                step_payout = base_win

            steps.append(TumbleStep(
                step_number=step_num + 1,
                base_win=base_win,
                active_multipliers=list(self.multiplier_history[-len(new_mults):]),
                accumulated_multiplier=self.accumulated_multiplier,
                step_payout=step_payout,
                symbols_removed=positions,
                bombs_triggered=len(new_mults)
            ))

        return steps

    def _find_adjacent_bombs(self, winning_positions: List[Tuple],
                            available_bombs: Dict[Tuple[int, int], int]) -> List[Tuple[int, int]]:
        """
        Find bombs that are adjacent to winning cluster
        A bomb counts if it's adjacent (up/down/left/right) to any winning symbol
        """
        adjacent_bombs = []

        for win_pos in winning_positions:
            win_r, win_c = win_pos

            # Check all 4 adjacent positions
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                bomb_pos = (win_r + dr, win_c + dc)
                if bomb_pos in available_bombs:
                    adjacent_bombs.append(bomb_pos)

        return adjacent_bombs

    # ============================================================
    # STATISTICS
    # ============================================================

    def get_stats(self) -> Dict:
        """Get multiplier statistics for current spin"""
        return {
            'total_accumulated': self.accumulated_multiplier,
            'bombs_triggered': self.total_bombs_triggered,
            'multiplier_history': [
                {'value': m.value, 'source': m.source.value}
                for m in self.multiplier_history
            ],
            'max_single_mult': max([m.value for m in self.multiplier_history], default=0),
            'is_free_spins': self.is_free_spins
        }


# ================================================================
# PAYOUT TABLE (Sweet Bonanza Real Game Approximation)
# Based on Sweet Bonanza by Pragmatic Play
# RTP: 96.48%
# ================================================================

SWEET_BONANZA_PAYOUT = {
    # Target RTP ~96%
    'lollipop': {8: 0.25, 9: 0.45, 10: 0.65, 12: 1.00, 15: 1.60, 20: 2.00},
    'candy': {8: 0.25, 9: 0.45, 10: 0.65, 12: 1.00, 15: 1.60, 20: 2.00},
    'cupcake': {8: 0.35, 9: 0.55, 10: 0.85, 12: 1.30, 15: 2.00, 20: 2.60},

    # Medium Value Symbols
    'donut': {8: 0.50, 9: 0.90, 10: 1.30, 12: 1.95, 15: 3.90, 20: 5.20},
    'apple': {8: 0.50, 9: 0.90, 10: 1.30, 12: 1.95, 15: 3.90, 20: 5.20},

    # High Value Symbols
    'grape': {8: 1.00, 9: 1.55, 10: 2.25, 12: 3.25, 15: 7.15, 20: 9.75},

    # Highest Value Symbols
    'banana': {8: 1.55, 9: 2.25, 10: 3.25, 12: 5.20, 15: 10.40, 20: 15.60},
}


def calculate_cluster_payout(symbol_id: str, count: int, bet: int) -> int:
    """
    Calculate payout for a cluster of matching symbols

    Args:
        symbol_id: The symbol type (e.g., 'candy', 'banana')
        count: Number of matching symbols
        bet: The player's bet amount

    Returns:
        Payout in credits
    """
    if symbol_id not in SWEET_BONANZA_PAYOUT:
        return 0

    payout_table = SWEET_BONANZA_PAYOUT[symbol_id]

    # Find the right payout bracket (sorted from high to low)
    brackets = sorted(payout_table.keys(), reverse=True)
    for bracket in brackets:
        if count >= bracket:
            return int(bet * payout_table[bracket])

    # Minimum 8 symbols
    return int(bet * payout_table.get(8, 0))


# ================================================================
# DEMO / TESTING
# ================================================================

if __name__ == "__main__":
    print("=== Sweet Bonanza Multiplier System Demo ===\n")

    # Test normal game
    print("--- Base Game Multipliers ---")
    mult_sys = SweetBonanzaMultiplierSystem(is_free_spins=False)

    print(f"Bomb chance: {mult_sys.get_bomb_chance() * 100}%")
    print("Sample multipliers:")
    for _ in range(10):
        print(f"  {mult_sys.generate_random_multiplier()}x", end=" ")
    print("\n")

    # Test free spins
    print("--- Free Spins Multipliers ---")
    mult_sys_fs = SweetBonanzaMultiplierSystem(is_free_spins=True)

    print(f"Bomb chance: {mult_sys_fs.get_bomb_chance() * 100}%")
    print("Sample multipliers:")
    for _ in range(10):
        print(f"  {mult_sys_fs.generate_random_multiplier()}x", end=" ")
    print("\n")

    # Simulate a tumble chain
    print("--- Simulated Tumble Chain ---")
    mult = SweetBonanzaMultiplierSystem()

    tumble_steps = [
        {'positions': [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1)], 'base_win': 100},
        {'positions': [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)], 'base_win': 80},
        {'positions': [(0, 0), (0, 1), (0, 2), (1, 0)], 'base_win': 60},
    ]

    bombs = [
        {},  # No bombs
        {(1, 0): 5},  # Bomb at position
        {(0, 1): 10},  # Another bomb
    ]

    steps = mult.process_tumble_chain(tumble_steps, bombs)

    total_win = 0
    for step in steps:
        total_win += step.step_payout
        print(f"Step {step.step_number}: Base ${step.base_win} × {step.accumulated_multiplier}x = ${step.step_payout}")
        if step.bombs_triggered:
            print(f"  💥 {step.bombs_triggered} bomb(s) triggered!")

    print(f"\nTotal Win: ${total_win}")

    # Test payout table
    print("\n--- Payout Table Examples ---")
    print(f"8 bananas: ${calculate_cluster_payout('banana', 8, 100)}")
    print(f"12 bananas: ${calculate_cluster_payout('banana', 12, 100)}")
    print(f"20 bananas: ${calculate_cluster_payout('banana', 20, 100)}")
    print(f"8 lollipops: ${calculate_cluster_payout('lollipop', 8, 100)}")
