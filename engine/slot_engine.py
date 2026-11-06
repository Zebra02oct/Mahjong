#!/usr/bin/env python3
"""
Mahjong Riichi - Slot Game Engine
Multi-game slot machine engine with various game modes
"""

import random
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum


class GameMode(Enum):
    """Available slot game modes"""
    SWEET_BONANZA = "sweet_bonanza"
    WOLF_GOLD = "wolf_gold"
    BIG_BASS = "big_bass"
    STARLIGHT = "starlight"
    GATES_OF_OLYMPUS = "gates_of_olympus"


@dataclass
class SlotSymbol:
    """Represents a slot symbol"""
    id: str
    name: str
    emoji: str
    value: int  # Payout multiplier for 8+ matching
    is_scatter: bool = False
    is_wild: bool = False
    is_jackpot: bool = False
    is_special: bool = False  # For candy bombs, fish, etc


@dataclass
class SpinResult:
    """Result of a single spin"""
    reels: List[List[str]]  # The grid after spin
    symbols: List[List[SlotSymbol]]  # Symbol objects
    winning_lines: List[Dict]  # Details of winning combinations
    total_payout: int  # Total payout from this spin
    is_free_spin: bool = False
    bonus_triggered: bool = False
    bonus_type: str = None
    multipliers: List[int] = field(default_factory=list)  # Active multipliers
    cascade_count: int = 0  # Number of cascades after initial spin


@dataclass
class BonusGame:
    """Bonus game state (free spins, respins, etc.)"""
    bonus_type: str  # 'free_spins', 'respin', 'jackpot'
    spins_remaining: int
    total_win: int = 0
    multiplier: float = 1.0
    state: Dict = field(default_factory=dict)  # Game-specific state


class SlotEngine:
    """Base slot machine engine"""

    def __init__(self, game_mode: GameMode, bet: int = 100):
        self.game_mode = game_mode
        self.bet = bet
        self.symbols = self._init_symbols()
        self.reels = 6
        self.rows = 5

    def _init_symbols(self) -> Dict[str, SlotSymbol]:
        """Initialize symbols based on game mode - override in subclasses"""
        return {}

    def get_random_row(self) -> List[str]:
        """Get a random row of symbols"""
        weights = [self.symbols[s].value for s in self.symbols if not self.symbols[s].is_special]
        total = sum(weights)
        probs = [w / total for w in weights]
        return random.choices(list(self.symbols.keys()), weights=probs, k=self.reels)

    def spin(self) -> SpinResult:
        """Perform a single spin"""
        # Generate initial reels
        reels = [self.get_random_row() for _ in range(self.rows)]

        # Convert to symbol objects
        symbols = [[self.symbols[r[c]] for c in range(len(r))] for r in reels]

        # Find winning combinations
        winning_lines, total_payout = self._check_wins(symbols)

        # Check for bonus triggers
        bonus_triggered, bonus_type = self._check_bonus(symbols)

        return SpinResult(
            reels=reels,
            symbols=symbols,
            winning_lines=winning_lines,
            total_payout=total_payout,
            bonus_triggered=bonus_triggered,
            bonus_type=bonus_type
        )

    def _check_wins(self, symbols: List[List[SlotSymbol]]) -> Tuple[List[Dict], int]:
        """Check for winning combinations - implement per game"""
        return [], 0

    def _check_bonus(self, symbols: List[List[SlotSymbol]]) -> Tuple[bool, Optional[str]]:
        """Check if bonus feature is triggered"""
        return False, None

    def calculate_payout(self, matches: List[Tuple], multiplier: float = 1.0) -> int:
        """Calculate payout for matching symbols"""
        total = 0
        for match in matches:
            symbol, count = match
            # Base payout increases with more symbols
            if count >= 4:
                base_payout = self.symbols[symbol].value * (count - 3)
            else:
                base_payout = 0
            total += int(base_payout * self.bet * multiplier)
        return total


class SweetBonanzaEngine(SlotEngine):
    """
    Sweet Bonanza slot machine with Hybrid Multiplier System

    Features:
    - 6x5 grid with "pay anywhere" (8+ matching symbols)
    - Tumble mechanic (cascading wins)
    - Hybrid Multiplier System:
      - Candy Bombs appear on reels
      - Global Accumulator builds across tumble chain
      - Conservative range: 2x-25x
    - Free Spins with enhanced multipliers
    """

    def __init__(self, bet: int = 100, is_free_spins: bool = False):
        super().__init__(GameMode.SWEET_BONANZA, bet)
        self.reels = 6
        self.rows = 5
        self.is_free_spins = is_free_spins

        # Import multiplier system
        from engine.multiplier_system import SweetBonanzaMultiplierSystem
        self.multiplier_system = SweetBonanzaMultiplierSystem(is_free_spins=is_free_spins)

    def _init_symbols(self) -> Dict[str, SlotSymbol]:
        """Sweet Bonanza candy symbols"""
        return {
            # Low value (4-6 pay more)
            'lollipop': SlotSymbol('lollipop', 'Lollipop', '🍭', 2),
            'candy': SlotSymbol('candy', 'Candy', '🍬', 3),
            'cupcake': SlotSymbol('cupcake', 'Cupcake', '🧁', 4),
            'donut': SlotSymbol('donut', 'Donut', '🍩', 5),

            # High value
            'apple': SlotSymbol('apple', 'Apple', '🍎', 8),
            'grape': SlotSymbol('grape', 'Grape', '🍇', 10),
            'banana': SlotSymbol('banana', 'Banana', '🍌', 15),

            # Special
            'scatter': SlotSymbol('scatter', 'Lollipop Scatter', '⭐', 0, is_scatter=True),
        }

    def _generate_grid_with_clusters(self) -> List[List[str]]:
        """
        Generate a grid for Sweet Bonanza.
        Sweet Bonanza needs clusters of 8+ adjacent matching symbols.
        Hit rate should be around 35-45%.
        """
        # Initialize empty grid
        grid = [[None for _ in range(self.reels)] for _ in range(self.rows)]

        # Symbol list (excluding scatter)
        symbols_list = ['lollipop', 'candy', 'cupcake', 'donut', 'apple', 'grape', 'banana']

        # Define cluster shapes with 8+ symbols
        cluster_shapes = [
            # Small L (8)
            [(0, 0), (0, 1), (1, 0), (2, 0), (3, 0), (3, 1), (4, 0), (4, 1)],
            # Big L (8)
            [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2), (3, 3), (3, 4)],
            # Square (9)
            [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)],
            # Wide rectangle (10)
            [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1)],
            # T shape (8)
            [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)],
            # Line (10)
            [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4)],
        ]

        # 35% chance of placing a winning cluster
        should_win = random.random() < 0.35

        placed_clusters = []

        if should_win:
            # Place 1-2 clusters
            num_clusters = random.choice([1, 1, 1, 2])  # 75% single, 25% double

            for _ in range(num_clusters):
                # Pick random symbol for this cluster (bias toward high value)
                if random.random() < 0.4:
                    sym = random.choice(['banana', 'grape', 'apple'])  # High value
                else:
                    sym = random.choice(symbols_list)

                # Pick random shape
                shape = random.choice(cluster_shapes)

                # Try to place cluster (avoid going out of bounds)
                max_attempts = 20
                for _ in range(max_attempts):
                    start_row = random.randint(0, self.rows - 3)
                    start_col = random.randint(0, self.reels - 5)

                    # Check if positions are valid and empty
                    valid = True
                    positions = []
                    for dr, dc in shape:
                        r, c = start_row + dr, start_col + dc
                        if r >= self.rows or c >= self.reels:
                            valid = False
                            break
                        if grid[r][c] is not None:
                            valid = False
                            break
                        positions.append((r, c))

                    if valid:
                        for r, c in positions:
                            grid[r][c] = sym
                        placed_clusters.append((sym, len(positions)))
                        break

        # Fill remaining empty spots
        all_symbols = ['lollipop', 'lollipop', 'lollipop',  # Weighted
                      'candy', 'candy', 'candy',
                      'cupcake', 'cupcake',
                      'donut',
                      'apple', 'apple',
                      'grape',
                      'banana']

        # Determine how many scatters to place (0-2)
        num_scatters = 0
        if random.random() < 0.15:
            num_scatters = random.randint(1, 2)

        scatter_placed = 0

        for r in range(self.rows):
            for c in range(self.reels):
                if grid[r][c] is None:
                    if scatter_placed < num_scatters and random.random() < 0.1:
                        grid[r][c] = 'scatter'
                        scatter_placed += 1
                    else:
                        grid[r][c] = random.choice(all_symbols)

        return grid

    def spin(self) -> SpinResult:
        """Perform Sweet Bonanza spin with hybrid multiplier system"""
        from engine.multiplier_system import calculate_cluster_payout

        # Reset multiplier system
        self.multiplier_system.reset()

        # Generate grid with clusters
        reels_raw = self._generate_grid_with_clusters()

        # Convert to SlotSymbol objects for processing
        symbols = [[self.symbols[reels_raw[r][c]] for c in range(self.reels)] for r in range(self.rows)]

        # Generate bombs on grid
        bombs = self.multiplier_system.generate_bombs_for_grid(self.rows, self.reels)

        # Track bombs triggered in each tumble step
        bombs_triggered_per_step = []

        # Process tumbles
        cascade_count = 0
        total_payout = 0
        all_winning_lines = []
        all_multipliers = []

        while True:
            # Find wins (cluster of 8+ matching symbols)
            matches = self._find_clusters(symbols)

            if not matches:
                break

            # Track bombs for this step
            step_bombs = {}

            # Calculate payout with multiplier system
            for match_symbol, positions in matches:
                if self.symbols[match_symbol].is_scatter:
                    continue

                count = len(positions)

                # Use official payout table
                base_win = calculate_cluster_payout(match_symbol, count, self.bet)

                # Find adjacent bombs and trigger them
                bombs_in_win = self.multiplier_system._find_adjacent_bombs(
                    positions, bombs
                )

                for bomb_pos in bombs_in_win:
                    mult = self.multiplier_system.trigger_bomb(bomb_pos)
                    all_multipliers.append(mult)
                    step_bombs[bomb_pos] = mult

                # Get accumulated multiplier
                accumulated = self.multiplier_system.get_accumulated_multiplier()

                # Calculate final payout for this cluster
                if accumulated > 0:
                    cluster_payout = base_win * accumulated
                else:
                    cluster_payout = base_win

                all_winning_lines.append({
                    'symbol': match_symbol,
                    'count': count,
                    'positions': positions,
                    'base_win': base_win,
                    'multiplier': accumulated,
                    'payout': cluster_payout,
                    'bombs_triggered': len(bombs_in_win)
                })
                total_payout += cluster_payout

            cascade_count += 1
            bombs_triggered_per_step.append(step_bombs)

            # Remove winning symbols and tumble
            symbols, bombs = self._tumble_with_bombs(symbols, matches, bombs)

            # Add new symbols at top with new bombs (convert to SlotSymbol objects)
            new_row_raw = self.get_random_row()
            symbols = [[self.symbols[new_row_raw[c]] if i == 0 else symbols[i-1][c]
                       for c in range(self.reels)] for i in range(self.rows)]

            # Generate new bombs for new symbols
            new_bombs = self.multiplier_system.generate_bombs_for_grid(self.rows, self.reels)
            bombs.update(new_bombs)

        # Check for scatter trigger (4+ scatters = free spins)
        scatter_count = sum(1 for row in symbols for s in row if s and s.is_scatter)
        bonus_triggered = scatter_count >= 4
        bonus_type = 'free_spins' if scatter_count >= 4 else None

        # Get multiplier stats
        mult_stats = self.multiplier_system.get_stats()

        return SpinResult(
            reels=reels_raw,
            symbols=symbols,
            winning_lines=all_winning_lines,
            total_payout=total_payout,
            bonus_triggered=bonus_triggered,
            bonus_type=bonus_type,
            multipliers=all_multipliers,
            cascade_count=cascade_count
        )

    def _find_clusters(self, symbols: List[List[SlotSymbol]]) -> List[Tuple[str, List[Tuple]]]:
        """Find all clusters of 8+ matching symbols"""
        clusters = []
        matched = set()

        for row in range(self.rows):
            for col in range(self.reels):
                if (row, col) in matched:
                    continue

                symbol = symbols[row][col]
                if symbol is None:
                    continue
                if symbol.is_scatter or symbol.is_special:
                    continue

                # Flood fill to find cluster
                cluster = []
                queue = [(row, col)]
                while queue:
                    r, c = queue.pop(0)
                    if (r, c) in matched:
                        continue
                    if r < 0 or r >= self.rows or c < 0 or c >= self.reels:
                        continue
                    if symbols[r][c] is None:
                        continue
                    if symbols[r][c].id != symbol.id:
                        continue

                    matched.add((r, c))
                    cluster.append((r, c))

                    # Check adjacent
                    queue.extend([(r+1, c), (r-1, c), (r, c+1), (r, c-1)])

                if len(cluster) >= 8:
                    clusters.append((symbol.id, cluster))

        return clusters

    def _tumble_with_bombs(self, symbols: List[List[SlotSymbol]],
                          matches: List[Tuple],
                          bombs: Dict[Tuple, int]) -> Tuple[List[List[SlotSymbol]], Dict[Tuple, int]]:
        """Remove matched symbols and tumble, keeping track of bombs"""
        matched_positions = set()
        for _, positions in matches:
            matched_positions.update(positions)

        # Track which bombs to remove
        bombs_to_remove = [pos for pos in bombs.keys() if pos in matched_positions]

        # Create new grid
        new_symbols = [[None for _ in range(self.reels)] for _ in range(self.rows)]
        new_bombs = {}

        # For each column, shift non-matched symbols down
        for col in range(self.reels):
            # Collect surviving symbols in this column
            surviving = []
            surviving_bombs = {}

            for row in range(self.rows):
                if (row, col) not in matched_positions:
                    surviving.append(symbols[row][col])
                    if (row, col) in bombs:
                        surviving_bombs[row] = bombs[(row, col)]

            # Fill from bottom with surviving symbols
            for i, sym in enumerate(surviving):
                new_row = self.rows - 1 - i
                new_symbols[new_row][col] = sym
                if i in surviving_bombs:
                    new_bombs[(new_row, col)] = surviving_bombs[i]

        # Remove triggered bombs
        for pos in bombs_to_remove:
            if pos in bombs:
                del bombs[pos]

        return new_symbols, new_bombs


class WolfGoldEngine(SlotEngine):
    """Wolf Gold slot machine with Money Respin"""

    def __init__(self, bet: int = 100):
        super().__init__(GameMode.WOLF_GOLD, bet)
        self.reels = 5
        self.rows = 3

    def _init_symbols(self) -> Dict[str, SlotSymbol]:
        """Wolf Gold symbols"""
        return {
            # Regular symbols
            'A': SlotSymbol('A', 'Ace', 'A', 10),
            'K': SlotSymbol('K', 'King', 'K', 8),
            'Q': SlotSymbol('Q', 'Queen', 'Q', 6),
            'J': SlotSymbol('J', 'Jack', 'J', 5),
            '10': SlotSymbol('10', 'Ten', '10', 4),
            '9': SlotSymbol('9', 'Nine', '9', 3),

            # High value
            'buffalo': SlotSymbol('buffalo', 'Buffalo', '🦬', 20),
            'eagle': SlotSymbol('eagle', 'Eagle', '🦅', 15),
            'wolf': SlotSymbol('wolf', 'Wolf', '🐺', 12),
            'deer': SlotSymbol('deer', 'Deer', '🦌', 10),

            # Special
            'wild': SlotSymbol('wild', 'Wild', '🃏', 0, is_wild=True),
            'scatter': SlotSymbol('scatter', 'G', '🌟', 0, is_scatter=True),
            'money': SlotSymbol('money', 'Money', '💰', 0, is_special=True),
            'jackpot_mini': SlotSymbol('jackpot_mini', 'Mini', '🌕', 0, is_jackpot=True),
            'jackpot_major': SlotSymbol('jackpot_major', 'Major', '🌟', 0, is_jackpot=True),
            'jackpot_grand': SlotSymbol('jackpot_grand', 'Grand', '👑', 0, is_jackpot=True),
        }

    def get_random_row(self) -> List[str]:
        """Get weighted random row"""
        # Money symbols (10%)
        if random.random() < 0.10:
            return ['money', 'money', 'money', 'money', 'money']

        # Jackpot symbols (2% each)
        if random.random() < 0.02:
            return ['jackpot_mini', 'A', 'K', 'Q', 'J']
        if random.random() < 0.015:
            return ['jackpot_major', 'A', 'K', 'Q', 'J']
        if random.random() < 0.01:
            return ['jackpot_grand', 'A', 'K', 'Q', 'J']

        # Regular symbols with weights
        regulars = ['A', 'A', 'K', 'K', 'K', 'Q', 'Q', 'J', 'J', '10',
                   'buffalo', 'buffalo', 'eagle', 'eagle', 'wolf', 'wolf', 'deer']

        return random.sample(regulars, 5)

    def _check_wins(self, symbols: List[List[SlotSymbol]]) -> Tuple[List[Dict], int]:
        """Check for line wins in Wolf Gold"""
        winning_lines = []
        total_payout = 0

        # Paylines (5 paylines for 5-reel game)
        paylines = [
            [0, 0, 0, 0, 0],  # Top
            [1, 1, 1, 1, 1],  # Middle
            [2, 2, 2, 2, 2],  # Bottom
            [0, 1, 2, 1, 0],  # V shape
            [2, 1, 0, 1, 2],  # Inverted V
        ]

        for line_idx, payline in enumerate(paylines):
            first_symbol = symbols[payline[0]][0]
            if first_symbol.is_scatter or first_symbol.is_special or first_symbol.is_jackpot:
                continue

            # Count matching symbols from left
            count = 1
            for i in range(1, 5):
                current = symbols[payline[i]][i]
                prev = symbols[payline[i-1]][i-1]

                # Wild matches anything
                if current.is_wild or current.id == prev.id:
                    count += 1
                else:
                    break

            if count >= 3:
                payout = int(first_symbol.value * count * self.bet * 0.2)
                winning_lines.append({
                    'line': line_idx,
                    'symbol': first_symbol.id,
                    'count': count,
                    'positions': [(payline[i], i) for i in range(count)],
                    'payout': payout
                })
                total_payout += payout

        return winning_lines, total_payout

    def _check_bonus(self, symbols: List[List[SlotSymbol]]) -> Tuple[bool, Optional[str]]:
        """Check for Money Respin trigger"""
        scatter_count = sum(1 for row in symbols for s in row if s and s.is_scatter)
        if scatter_count >= 3:
            return True, 'respin'

        money_count = sum(1 for row in symbols for s in row if s.is_special)
        if money_count >= 3:
            return True, 'respin'

        return False, None


class BigBassEngine(SlotEngine):
    """Big Bass Bonanza fishing slot"""

    def __init__(self, bet: int = 100):
        super().__init__(GameMode.BIG_BASS, bet)
        self.reels = 5
        self.rows = 3

    def _init_symbols(self) -> Dict[str, SlotSymbol]:
        """Big Bass symbols"""
        return {
            # Low value
            'A': SlotSymbol('A', 'Ace', 'A', 10),
            'K': SlotSymbol('K', 'King', 'K', 8),
            'Q': SlotSymbol('Q', 'Queen', 'Q', 6),
            'J': SlotSymbol('J', 'Jack', 'J', 5),
            '10': SlotSymbol('10', 'Ten', '10', 4),

            # High value
            'fishing_rod': SlotSymbol('fishing_rod', 'Fishing Rod', '🎣', 15),
            'dragonfly': SlotSymbol('dragonfly', 'Dragonfly', '🪰', 12),
            'hook': SlotSymbol('hook', 'Hook', '🪝', 10),
            'boot': SlotSymbol('boot', 'Boot', '👢', 8),

            # Special
            'wild': SlotSymbol('wild', 'Fisherman', '🧑‍🦱', 0, is_wild=True),
            'scatter': SlotSymbol('scatter', 'Bass', '🐟', 0, is_scatter=True),
            'fish': SlotSymbol('fish', 'Fish Money', '🐠', 0, is_special=True),
        }

    def get_random_row(self) -> List[str]:
        """Get weighted random row"""
        # Fish symbols (8%)
        if random.random() < 0.08:
            return ['fish', 'A', 'K', 'Q', 'J']

        # Scatter (10%)
        if random.random() < 0.10:
            return ['scatter', 'A', 'K', 'Q', 'J']

        # Regular symbols
        regulars = ['A', 'A', 'K', 'K', 'K', 'Q', 'Q', 'J', 'J', '10',
                   'fishing_rod', 'fishing_rod', 'dragonfly', 'dragonfly',
                   'hook', 'hook', 'boot', 'boot', 'wild']

        return random.sample(regulars, 5)

    def _check_wins(self, symbols: List[List[SlotSymbol]]) -> Tuple[List[Dict], int]:
        """Check for line wins"""
        winning_lines = []
        total_payout = 0

        paylines = [
            [0, 0, 0, 0, 0],
            [1, 1, 1, 1, 1],
            [2, 2, 2, 2, 2],
        ]

        for line_idx, payline in enumerate(paylines):
            first_symbol = symbols[payline[0]][0]
            if first_symbol.is_scatter or first_symbol.is_special:
                continue

            count = 1
            for i in range(1, 5):
                current = symbols[payline[i]][i]
                prev = symbols[payline[i-1]][i-1]
                if current.is_wild or current.id == prev.id:
                    count += 1
                else:
                    break

            if count >= 3:
                payout = int(first_symbol.value * count * self.bet * 0.2)
                winning_lines.append({
                    'line': line_idx,
                    'symbol': first_symbol.id,
                    'count': count,
                    'payout': payout
                })
                total_payout += payout

        return winning_lines, total_payout


class StarlightPrincessEngine(SlotEngine):
    """Starlight Princess - anime fantasy theme"""

    def __init__(self, bet: int = 100):
        super().__init__(GameMode.STARLIGHT, bet)
        self.reels = 6
        self.rows = 5

    def _init_symbols(self) -> Dict[str, SlotSymbol]:
        """Starlight Princess symbols"""
        return {
            # Regular symbols (heart, star, moon, etc.)
            'pink_heart': SlotSymbol('pink_heart', 'Pink Heart', '💖', 8),
            'green_gem': SlotSymbol('green_gem', 'Green Gem', '💚', 10),
            'blue_diamond': SlotSymbol('blue_diamond', 'Blue Diamond', '💎', 12),
            'yellow_star': SlotSymbol('yellow_star', 'Yellow Star', '⭐', 15),
            'purple_gem': SlotSymbol('purple_gem', 'Purple Gem', '💜', 20),

            # Special
            'scatter': SlotSymbol('scatter', 'Princess', '👸', 0, is_scatter=True),
            'multiplier': SlotSymbol('multiplier', 'Multiplier', '⚡', 0, is_special=True),
            'wild': SlotSymbol('wild', 'Wild', '🌟', 0, is_wild=True),
        }

    def get_random_row(self) -> List[str]:
        """Get weighted random row"""
        # Multiplier (5%)
        if random.random() < 0.05:
            return ['multiplier'] + ['pink_heart', 'green_gem', 'blue_diamond', 'yellow_star', 'purple_gem']

        # Scatter (10%)
        if random.random() < 0.10:
            return ['scatter'] + ['pink_heart', 'green_gem', 'blue_diamond', 'yellow_star', 'purple_gem']

        # Regular
        regulars = ['pink_heart', 'pink_heart', 'green_gem', 'green_gem',
                   'blue_diamond', 'yellow_star', 'purple_gem', 'wild']
        return random.sample(regulars, 6)

    def spin(self) -> SpinResult:
        """Starlight spin with multiplier mechanics"""
        reels = [[self.get_random_row()[c] for c in range(6)] for _ in range(5)]
        symbols = [[self.symbols[r[c]] for c in range(6)] for r in reels]

        # Process cascades
        cascade_count = 0
        total_payout = 0
        all_winning_lines = []
        active_multipliers = []

        while True:
            matches = self._find_clusters(symbols)
            if not matches:
                break

            # Collect multipliers first
            for row in range(5):
                for col in range(6):
                    if symbols[row][col].is_special:
                        # Random multiplier 2-100
                        mult = random.choice([2, 2, 3, 3, 5, 10, 25, 50, 100])
                        active_multipliers.append(mult)

            for match_symbol, positions in matches:
                if self.symbols[match_symbol].is_scatter:
                    continue

                count = len(positions)
                base_value = self.symbols[match_symbol].value
                payout = int(base_value * count * self.bet * 0.1)

                # Apply highest multiplier
                if active_multipliers:
                    payout *= max(active_multipliers)

                all_winning_lines.append({
                    'symbol': match_symbol,
                    'count': count,
                    'payout': payout
                })
                total_payout += payout

            cascade_count += 1
            symbols = self._tumble(symbols, matches)

            # Add new row
            new_row = [self.get_random_row()[c] for c in range(6)]
            symbols = [[new_row[c] if i == 0 else symbols[i-1][c]
                       for c in range(6)] for i in range(5)]

        scatter_count = sum(1 for r in symbols for s in r if s.is_scatter)
        bonus_triggered = scatter_count >= 4

        return SpinResult(
            reels=[[r[c] for c in range(6)] for r in symbols],
            symbols=symbols,
            winning_lines=all_winning_lines,
            total_payout=total_payout,
            bonus_triggered=bonus_triggered,
            bonus_type='free_spins' if scatter_count >= 4 else None,
            multipliers=active_multipliers,
            cascade_count=cascade_count
        )

    def _find_clusters(self, symbols: List[List[SlotSymbol]]) -> List[Tuple[str, List[Tuple]]]:
        """Find clusters of 8+ matching symbols"""
        clusters = []
        matched = set()

        for row in range(5):
            for col in range(6):
                if (row, col) in matched:
                    continue

                symbol = symbols[row][col]
                if symbol.is_scatter or symbol.is_special or symbol.is_wild:
                    continue

                cluster = []
                queue = [(row, col)]
                while queue:
                    r, c = queue.pop(0)
                    if (r, c) in matched:
                        continue
                    if r < 0 or r >= 5 or c < 0 or c >= 6:
                        continue
                    if symbols[r][c].id != symbol.id:
                        continue

                    matched.add((r, c))
                    cluster.append((r, c))
                    queue.extend([(r+1, c), (r-1, c), (r, c+1), (r, c-1)])

                if len(cluster) >= 8:
                    clusters.append((symbol.id, cluster))

        return clusters

    def _tumble(self, symbols: List[List[SlotSymbol]], matches: List[Tuple]) -> List[List[SlotSymbol]]:
        """Remove matched symbols"""
        matched_positions = set()
        for _, positions in matches:
            matched_positions.update(positions)

        new_symbols = [[None for _ in range(6)] for _ in range(5)]

        for col in range(6):
            column = []
            for row in range(5):
                if (row, col) not in matched_positions:
                    column.append(symbols[row][col])

            for i, sym in enumerate(reversed(column)):
                new_symbols[4-i][col] = sym

        return new_symbols


def get_engine(game_mode: str, bet: int = 100) -> SlotEngine:
    """Factory function to get the appropriate engine"""
    modes = {
        'sweet_bonanza': SweetBonanzaEngine,
        'wolf_gold': WolfGoldEngine,
        'big_bass': BigBassEngine,
        'starlight': StarlightPrincessEngine,
        'gates_of_olympus': SweetBonanzaEngine,  # Reuse Sweet Bonanza mechanics
    }
    engine_class = modes.get(game_mode.lower(), SweetBonanzaEngine)
    return engine_class(bet)


# Demo function
if __name__ == "__main__":
    print("=== Sweet Bonanza Demo ===")
    engine = get_engine('sweet_bonanza', 100)
    for i in range(3):
        result = engine.spin()
        print(f"Spin {i+1}:")
        for row in result.reels:
            print(f"  {row}")
        print(f"  Payout: {result.total_payout}, Cascades: {result.cascade_count}")
        if result.bonus_triggered:
            print(f"  BONUS TRIGGERED: {result.bonus_type}!")

    print("\n=== Wolf Gold Demo ===")
    engine = get_engine('wolf_gold', 100)
    for i in range(3):
        result = engine.spin()
        print(f"Spin {i+1}:")
        for row in result.reels:
            print(f"  {row}")
        print(f"  Payout: {result.total_payout}")
