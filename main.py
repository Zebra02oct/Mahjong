#!/usr/bin/env python3
"""
Mahjong Riichi - Main Entry Point
Japanese Riichi Mahjong Game - Phase 2
"""

import sys
import argparse
from ui.console_ui import ConsoleUI
from engine.game_state import GameState
from core.deck import create_standard_deck
from core.tiles import Tile


def print_banner():
    """Print game banner"""
    banner = """
    +==========================================================+
    |                                                          |
    |          M A H J O N G   R I I C H I                    |
    |                                                          |
    |          Japanese Traditional Tile Game                    |
    |                                                          |
    +==========================================================+
    """
    print(banner)


def demo_game():
    """Run a simple demonstration of the game logic"""
    print_banner()
    print("\n=== Mahjong Riichi Demo ===\n")

    # Create deck
    deck = create_standard_deck(seed=42)
    print(f"Created deck with {len(deck.tiles)} tiles")
    print(f"First 5 tiles: {[t.name for t in deck.tiles[:5]]}")

    # Draw a hand
    hand = deck.draw_player_hand()
    print(f"\nDrew 13 tiles: {len(hand)} tiles")
    print(f"Tiles: {' '.join(t.name for t in hand)}")

    # Test shanten calculation
    from core.shanten import ShantenCalculator
    calc = ShantenCalculator()

    shanten = calc.calculate_shanten(hand)
    print(f"\nShanten: {shanten}")

    # Test wait tiles
    if shanten == 0:
        waits = calc.get_wait_tiles(hand)
        print(f"Wait tiles: {[Tile(t).name for t in waits]}")

    # Test yaku detection
    from core.yaku import YakuDetector, YakuContext
    detector = YakuDetector()
    context = YakuContext(is_menzen=True, is_tsumo=True)

    yaku = detector.detect(hand, context)
    print(f"\nYaku detected: {[y.name for y in yaku]}")

    print("\n" + "=" * 50)


def run_console_game():
    """Run the console-based game"""
    print_banner()
    print("\nStarting Console Game...\n")

    ui = ConsoleUI()

    # Setup game with 1 human player and 3 AI
    ui.create_game(
        player_names=["You", "CPU-2", "CPU-3", "CPU-4"],
        ai_levels=[0, 2, 2, 2]
    )

    print("\nGame created! Starting...")
    print("Press Enter after each turn to continue.")
    input()

    ui.run_game()


def run_ai_vs_ai():
    """Run a game with AI vs AI (enhanced Phase 2)"""
    print_banner()
    print("\nRunning AI vs AI Game (Level 3 - Phase 2)...\n")

    from ui.console_ui import ConsoleUI
    ui = ConsoleUI()

    # All AI players
    ui.create_game(
        player_names=["AI-1", "AI-2", "AI-3", "AI-4"],
        ai_levels=[3, 3, 3, 3]
    )

    if not ui.game_state:
        print("Failed to create game!")
        return

    # Run enhanced game loop
    max_turns = 500
    turn = 0

    while turn < max_turns:
        turn += 1

        # Show progress every 8 turns
        if turn % 8 == 0:
            print(f"\n--- Turn {turn} ---")
            for p in ui.game_state.players:
                wind = ["E", "S", "W", "N"][p.seat_wind]
                riichi = " [R]" if p.riichi_declared else ""
                tenpai = " [T]" if p.is_tenpai else ""
                print(f"  {p.name}[{wind}]: Score={p.score}, Hand={len(p.hand)}{riichi}{tenpai}")

            print(f"  Dora: {[d.name for d in ui.game_state.dora_indicators]}")
            print(f"  Deck remaining: {ui.game_state.deck.remaining}")

        # Check for exhaustion
        if ui.game_state.deck.remaining <= 0:
            print("\n*** DRAW - No tiles remaining! ***")
            # Check tenpai
            tenpai_players = [p for p in ui.game_state.players if p.is_tenpai]
            if tenpai_players:
                print(f"Tenpai: {[p.name for p in tenpai_players]}")
            break

        # Process turn
        current = ui.game_state.current_turn
        player = ui.game_state.players[current]

        # Check for ankan
        ankan_options = ui.game_state.check_ankan_available(current)
        if ankan_options:
            ai = ui.ai_players.get(current)
            if ai:
                # AI considers ankan (simplified: 10% chance)
                import random
                if random.random() < 0.1:
                    tile_type = ankan_options[0].type
                    ui.game_state.declare_ankan(current, tile_type)
                    print(f"  {player.name} declares ANKAN!")
                    continue  # Skip normal draw

        # Draw tile
        drawn = ui.game_state.draw_tile(current)
        if not drawn:
            break

        # Check tsumo
        win_result = ui.game_state.check_win(current, drawn, is_tsumo=True)
        if win_result:
            print(f"\n*** {player.name} wins by TSUMO! ***")
            print(f"  Score: {win_result.score}")
            print(f"  Han: {win_result.han}, Fu: {win_result.fu}")
            print(f"  Yaku: {', '.join(win_result.yaku_names)}")
            if win_result.is_double_riichi:
                print(f"  DOUBLE RICHI!")
            if win_result.is_ippatsu:
                print(f"  IPPAATSU!")

            ui.game_state.handle_win(win_result)
            break

        # AI decide discard
        ai = ui.ai_players.get(current)
        if ai:
            tile = ai.decide_discard(ui.game_state)

            # Riichi check
            if player.can_declare_riichi() and player.is_tenpai:
                if ai.decide_riichi(ui.game_state, tile):
                    ui.game_state.declare_riichi(current, tile)
                    print(f"  *** {player.name} declares RICHI! ***")

            ui.game_state.discard_tile(current, tile)

            # Check for ron (from ALL other players)
            ron_happened = False
            for pid, p in enumerate(ui.game_state.players):
                if pid == current:
                    continue

                # Check if player can ron
                if p.furiten:
                    continue

                ai_opp = ui.ai_players.get(pid)
                if ai_opp:
                    if ai_opp.decide_call(ui.game_state, "ron", tile):
                        win = ui.game_state.check_win(pid, tile, is_tsumo=False)
                        if win:
                            print(f"\n*** {p.name} wins by RON! ***")
                            print(f"  From: {player.name} discarded {tile.name}")
                            print(f"  Score: {win.score}")
                            print(f"  Yaku: {', '.join(win.yaku_names)}")

                            ui.game_state.handle_win(win)
                            ron_happened = True
                            break

            if ron_happened:
                break

        # Next turn
        ui.game_state.next_turn()

    # Final scores
    print("\n" + "=" * 50)
    print("FINAL SCORES")
    print("=" * 50)
    for p in sorted(ui.game_state.players, key=lambda x: -x.score):
        wind = ["E", "S", "W", "N"][p.seat_wind]
        print(f"{p.name}[{wind}]: {p.score}")

    if ui.game_state.winner is not None:
        winner = ui.game_state.players[ui.game_state.winner]
        print(f"\nWinner: {winner.name}!")


def run_tournament():
    """Run AI tournament"""
    from ai.tournament import run_quick_benchmark, compare_two_ais, Tournament
    import argparse

    parser = argparse.ArgumentParser(description="AI Tournament Options")
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

    t_args = parser.parse_args()

    if t_args.benchmark:
        run_quick_benchmark()
    elif t_args.full:
        tournament = Tournament(seed=t_args.seed)
        results = tournament.run_full_tournament(seed=t_args.seed)
        from ai.tournament import print_tournament_results
        print_tournament_results(results)
    else:
        compare_two_ais(t_args.level_a, t_args.level_b, t_args.games)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Mahjong Riichi")
    parser.add_argument(
        '--mode',
        choices=['demo', 'console', 'ai', 'tournament', 'pygame'],
        default='demo',
        help='Game mode: demo, console, ai, tournament, pygame'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--ai-level',
        type=int,
        default=3,
        help='AI difficulty level (1-4) for single player mode'
    )

    args = parser.parse_args()

    if args.mode == 'demo':
        demo_game()
    elif args.mode == 'console':
        run_console_game()
    elif args.mode == 'ai':
        run_ai_vs_ai()
    elif args.mode == 'tournament':
        run_tournament()
    elif args.mode == 'pygame':
        from ui.pygame_ui import PygameUI
        ui = PygameUI()
        ui.create_game(
            player_names=["You", "CPU-2", "CPU-3", "CPU-4"],
            ai_levels=[0, 2, 2, 2]
        )
        ui.run()


if __name__ == '__main__':
    main()
