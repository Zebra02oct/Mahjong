"""
Mahjong Riichi - AI Tournament System
Test and compare AI levels against each other
"""

import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict

from engine.game_state import GameState, create_new_game
from ai.random_ai import RandomAI
from ai.basic_ai import BasicAI
from ai.advanced_ai import AdvancedAI
from ai.expert_ai import ExpertAI


@dataclass
class MatchResult:
    """Result of a single match"""
    winner_id: int
    final_scores: List[int]
    rounds_played: int
    game_ended: str  # 'win', 'exhaustion', 'suspended'


@dataclass
class TournamentResult:
    """Result of tournament between AI levels"""
    matchups: List[Dict] = field(default_factory=list)
    total_games: int = 0
    avg_rounds_per_game: float = 0.0


@dataclass
class AIStats:
    """Statistics for an AI level"""
    wins: int = 0
    total_score: int = 0
    avg_score: float = 0.0
    games_played: int = 0
    placement_counts: Dict[int, int] = field(default_factory=dict)  # rank -> count


class Tournament:
    """
    AI Tournament System

    Run matches between different AI levels and track statistics
    """

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.results: Dict[Tuple[int, int, int], TournamentResult] = {}
        self.global_stats: Dict[int, AIStats] = {}

    def get_ai_instance(self, level: int, player_id: int):
        """Create AI instance based on level"""
        ai_map = {
            1: RandomAI,
            2: BasicAI,
            3: AdvancedAI,
            4: ExpertAI
        }
        ai_class = ai_map.get(level, RandomAI)
        return ai_class(player_id=player_id, difficulty=level)

    def run_match(self, ai_levels: List[int], max_rounds: int = 500,
                  seed: Optional[int] = None) -> MatchResult:
        """
        Run a single match between AI players

        Args:
            ai_levels: List of 4 AI levels (one per player)
            max_rounds: Maximum rounds before draw
            seed: Random seed for this match

        Returns:
            MatchResult with winner and scores
        """
        # Create game
        game = create_new_game(seed=seed)

        # Create AIs
        ais = {}
        for i, level in enumerate(ai_levels):
            ais[i] = self.get_ai_instance(level, i)

        # Update AI references in game
        game.ai_players = ais

        rounds_played = 0

        while rounds_played < max_rounds:
            rounds_played += 1

            current = game.current_turn
            player = game.players[current]
            ai = ais.get(current)

            if ai is None:
                game.next_turn()
                continue

            # Check for ankan
            ankan_options = game.check_ankan_available(current)
            if ankan_options:
                # AI considers ankan (simplified logic)
                if self.rng.random() < 0.1:
                    tile_type = ankan_options[0].type
                    game.declare_ankan(current, tile_type)

            # Draw tile
            drawn = game.draw_tile(current)
            if not drawn:
                break

            # Check tsumo
            win_result = game.check_win(current, drawn, is_tsumo=True)
            if win_result:
                game.handle_win(win_result)
                return MatchResult(
                    winner_id=win_result.winner_id,
                    final_scores=game.get_player_scores(),
                    rounds_played=rounds_played,
                    game_ended='win'
                )

            # AI decide discard
            tile = ai.decide_discard(game)

            # Riichi check
            if player.can_declare_riichi() and player.is_tenpai:
                if ai.decide_riichi(game, tile):
                    game.declare_riichi(current, tile)

            game.discard_tile(current, tile)

            # Check for ron
            for pid, other_player in enumerate(game.players):
                if pid == current:
                    continue
                if other_player.furiten:
                    continue

                other_ai = ais.get(pid)
                if other_ai:
                    if other_ai.decide_call(game, "ron", tile):
                        win = game.check_win(pid, tile, is_tsumo=False)
                        if win:
                            game.handle_win(win)
                            return MatchResult(
                                winner_id=pid,
                                final_scores=game.get_player_scores(),
                                rounds_played=rounds_played,
                                game_ended='win'
                            )

            # Update opponent models
            for ai_instance in ais.values():
                if hasattr(ai_instance, 'update_opponent_model'):
                    ai_instance.update_opponent_model(game)

            game.next_turn()

        # Exhaustion - no winner
        return MatchResult(
            winner_id=-1,
            final_scores=game.get_player_scores(),
            rounds_played=rounds_played,
            game_ended='exhaustion'
        )

    def run_matchup(self, level_a: int, level_b: int,
                    games: int = 10, seed_base: int = 42) -> TournamentResult:
        """
        Run multiple games between two AI levels

        Args:
            level_a: First AI level
            level_b: Second AI level
            games: Number of games to play
            seed_base: Base seed for reproducibility

        Returns:
            TournamentResult with statistics
        """
        results = []

        for i in range(games):
            # Alternate positions for fairness
            ai_levels = [level_a, level_b, level_b, level_a]
            self.rng.shuffle(ai_levels)

            # Try to balance positions
            seed = seed_base + i

            result = self.run_match(ai_levels, seed=seed)
            results.append(result)

        # Calculate statistics
        total_rounds = sum(r.rounds_played for r in results)
        wins_a = sum(1 for r in results if r.winner_id in [0, 3])
        wins_b = sum(1 for r in results if r.winner_id in [1, 2])

        # Calculate placements
        placements_a = []
        placements_b = []

        for result in results:
            scores = result.final_scores
            sorted_indices = sorted(range(len(scores)), key=lambda i: -scores[i])
            for rank, player_id in enumerate(sorted_indices, 1):
                if player_id in [0, 3]:
                    placements_a.append(rank)
                else:
                    placements_b.append(rank)

        avg_rank_a = sum(placements_a) / len(placements_a) if placements_a else 0
        avg_rank_b = sum(placements_b) / len(placements_b) if placements_b else 0

        return TournamentResult(
            matchups=[{
                'level_a': level_a,
                'level_b': level_b,
                'games': games,
                'wins_a': wins_a,
                'wins_b': wins_b,
                'avg_rank_a': avg_rank_a,
                'avg_rank_b': avg_rank_b,
                'avg_rounds': total_rounds / games
            }],
            total_games=games,
            avg_rounds_per_game=total_rounds / games
        )

    def run_full_tournament(self, ai_levels: List[int] = None,
                          games_per_matchup: int = 10,
                          seed: int = 42) -> Dict:
        """
        Run full tournament with all specified AI levels

        Args:
            ai_levels: List of AI levels to test (default: [1, 2, 3, 4])
            games_per_matchup: Games per matchup
            seed: Base seed

        Returns:
            Dictionary with all tournament results
        """
        if ai_levels is None:
            ai_levels = [1, 2, 3, 4]

        # Initialize stats
        stats = {level: AIStats() for level in ai_levels}

        # Run each matchup
        all_results = []

        for i, level_a in enumerate(ai_levels):
            for level_b in ai_levels[i+1:]:
                result = self.run_matchup(
                    level_a, level_b,
                    games=games_per_matchup,
                    seed_base=seed + i * 100 + level_b
                )
                all_results.extend(result.matchups)

                # Update stats
                self._update_stats(stats, result, level_a, level_b)

        # Calculate overall rankings
        rankings = self._calculate_rankings(stats)

        return {
            'matchups': all_results,
            'stats': {
                level: {
                    'wins': s.wins,
                    'avg_score': s.avg_score,
                    'games_played': s.games_played,
                    'placement_distribution': s.placement_counts
                }
                for level, s in stats.items()
            },
            'rankings': rankings
        }

    def _update_stats(self, stats: Dict[int, AIStats],
                     result: TournamentResult,
                     level_a: int, level_b: int) -> None:
        """Update statistics for a matchup"""
        matchup = result.matchups[0]

        # Update level A stats
        stats[level_a].wins += matchup['wins_a']
        stats[level_a].games_played += matchup['games']

        # Update level B stats
        stats[level_b].wins += matchup['wins_b']
        stats[level_b].games_played += matchup['games']

    def _calculate_rankings(self, stats: Dict[int, AIStats]) -> List[Tuple[int, float]]:
        """Calculate rankings based on win rate"""
        rankings = []

        for level, s in stats.items():
            if s.games_played > 0:
                win_rate = s.wins / s.games_played
            else:
                win_rate = 0.0
            rankings.append((level, win_rate))

        rankings.sort(key=lambda x: -x[1])
        return rankings

    def run_level_vs_all(self, level: int, other_levels: List[int] = None,
                        games: int = 10, seed: int = 42) -> Dict:
        """
        Test one AI level against all others

        Args:
            level: The AI level to test
            other_levels: Other levels to test against (default: all)
            games: Games per matchup
            seed: Base seed

        Returns:
            Results dictionary
        """
        if other_levels is None:
            other_levels = [1, 2, 3, 4]

        other_levels = [l for l in other_levels if l != level]

        total_wins = 0
        total_games = 0
        matchup_results = []

        for other_level in other_levels:
            result = self.run_matchup(level, other_level, games=games, seed_base=seed)
            matchup = result.matchups[0]

            total_wins += matchup['wins_a']
            total_games += games

            matchup_results.append({
                'opponent': other_level,
                'wins': matchup['wins_a'],
                'total': games,
                'win_rate': matchup['wins_a'] / games
            })

        return {
            'level': level,
            'total_wins': total_wins,
            'total_games': total_games,
            'overall_win_rate': total_wins / total_games if total_games > 0 else 0,
            'matchups': matchup_results
        }


def print_tournament_results(results: Dict) -> None:
    """Print tournament results in readable format"""
    print("\n" + "=" * 60)
    print("            MAHJONG RICHI AI TOURNAMENT RESULTS")
    print("=" * 60)

    # Print rankings
    print("\n📊 OVERALL RANKINGS (by win rate):")
    print("-" * 40)
    for rank, (level, win_rate) in enumerate(results['rankings'], 1):
        stats = results['stats'][level]
        emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        print(f"  {emoji} Level {level}: {win_rate*100:.1f}% win rate "
              f"({stats['wins']} wins in {stats['games_played']} games)")

    # Print matchup details
    print("\n📈 HEAD-TO-HEAD RESULTS:")
    print("-" * 40)

    for matchup in results['matchups']:
        la, lb = matchup['level_a'], matchup['level_b']
        wa, wb = matchup['wins_a'], matchup['wins_b']
        print(f"  Level {la} vs Level {lb}: {wa}-{wb} "
              f"(Avg rounds: {matchup['avg_rounds']:.1f})")

    print("\n" + "=" * 60)


def print_matchup_results(results: Dict) -> None:
    """Print single matchup results"""
    print("\n" + "=" * 50)
    print(f"   LEVEL {results['level']} VS ALL OTHERS")
    print("=" * 50)

    print(f"\n🎯 Overall Win Rate: {results['overall_win_rate']*100:.1f}%")
    print(f"   Total: {results['total_wins']} wins / {results['total_games']} games\n")

    print("📊 Matchup Details:")
    print("-" * 40)
    for m in results['matchups']:
        bar = "█" * int(m['win_rate'] * 20) + "░" * (20 - int(m['win_rate'] * 20))
        print(f"  vs Level {m['opponent']}: {m['wins']}/{m['total']} {bar} {m['win_rate']*100:.0f}%")

    print()


def run_quick_benchmark() -> None:
    """Run quick benchmark comparing all AI levels"""
    print("\n🚀 Running Quick Benchmark...")

    tournament = Tournament(seed=42)

    # Test Level 4 (Expert) against all
    print("\n🔍 Testing Expert AI (Level 4) against all levels...")
    expert_results = tournament.run_level_vs_all(level=4, games=10)

    print_matchup_results(expert_results)

    # Full tournament
    print("\n🎮 Running Full Tournament...")
    results = tournament.run_full_tournament(
        ai_levels=[1, 2, 3, 4],
        games_per_matchup=5,
        seed=42
    )

    print_tournament_results(results)


def compare_two_ais(level_a: int, level_b: int, games: int = 20) -> None:
    """Compare two specific AI levels"""
    print(f"\n⚔️  Comparing Level {level_a} vs Level {level_b}")
    print(f"   Playing {games} games...\n")

    tournament = Tournament(seed=42)
    result = tournament.run_matchup(level_a, level_b, games=games)

    matchup = result.matchups[0]

    print(f"📊 Results:")
    print(f"   Level {level_a}: {matchup['wins_a']} wins ({matchup['wins_a']/games*100:.1f}%)")
    print(f"   Level {level_b}: {matchup['wins_b']} wins ({matchup['wins_b']/games*100:.1f}%)")
    print(f"   Draws: {games - matchup['wins_a'] - matchup['wins_b']}")
    print(f"   Average rounds per game: {matchup['avg_rounds']:.1f}")

    # Win probability
    if matchup['wins_a'] > matchup['wins_b']:
        winner = level_a
        diff = matchup['wins_a'] - matchup['wins_b']
    elif matchup['wins_b'] > matchup['wins_a']:
        winner = level_b
        diff = matchup['wins_b'] - matchup['wins_a']
    else:
        winner = "TIE"
        diff = 0

    if winner != "TIE":
        print(f"\n🏆 Level {winner} wins! (+{diff} games advantage)")
    else:
        print(f"\n⚖️  It's a tie!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mahjong Riichi AI Tournament")
    parser.add_argument('--level-a', type=int, default=3,
                       help='First AI level (1-4)')
    parser.add_argument('--level-b', type=int, default=4,
                       help='Second AI level (1-4)')
    parser.add_argument('--games', type=int, default=10,
                       help='Number of games per matchup')
    parser.add_argument('--full', action='store_true',
                       help='Run full tournament')
    parser.add_argument('--benchmark', action='store_true',
                       help='Run quick benchmark')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed')

    args = parser.parse_args()

    if args.benchmark:
        run_quick_benchmark()
    elif args.full:
        tournament = Tournament(seed=args.seed)
        results = tournament.run_full_tournament(seed=args.seed)
        print_tournament_results(results)
    else:
        compare_two_ais(args.level_a, args.level_b, args.games)
