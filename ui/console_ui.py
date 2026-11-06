"""
Mahjong Riichi - Console UI
Simple text-based UI for testing
"""

from typing import Optional, List
from core.tiles import Tile, sort_tiles
from core.shanten import ShantenCalculator
from engine.game_state import GameState
from ai import create_ai


class ConsoleUI:
    """
    Simple console-based UI for testing Mahjong game

    Features:
    - ASCII display of tiles
    - Command input
    - Game state visualization
    """

    def __init__(self):
        self.game_state: Optional[GameState] = None
        self.shanten_calc = ShantenCalculator()
        self.ai_players = {}

    def create_game(self, player_names: List[str] = None, ai_levels: List[int] = None):
        """Create a new game"""
        if player_names is None:
            player_names = ["Player 1", "Player 2", "Player 3", "Player 4"]

        if ai_levels is None:
            ai_levels = [0, 2, 2, 2]  # Player 1 is human, others AI level 2

        self.game_state = GameState(player_names=player_names)
        self.game_state.start_new_round()
        self.game_state.deal_initial_hands()

        # Setup AI players
        for i, level in enumerate(ai_levels):
            if level > 0:
                ai = create_ai(i, level)
                self.ai_players[i] = ai
                self.game_state.players[i].is_ai = True
                self.game_state.players[i].ai_level = level

        return self.game_state

    def display_game_state(self, player_index: int = 0):
        """Display current game state from player's perspective"""
        if not self.game_state:
            print("No game started!")
            return

        print("\n" + "=" * 60)
        print(f"Round {self.game_state.round_number}, Honba: {self.game_state.honba}")
        print(f"Turn: {self.game_state.turn_number}")
        print(f"Current Player: {self.game_state.players[self.game_state.current_turn].name}")
        print("-" * 60)

        # Dora indicators
        if self.game_state.dora_indicators:
            print(f"Dora: {' '.join(d.unicode for d in self.game_state.dora_indicators)}")

        # Display players (rotated view)
        player_names = []
        for i in range(4):
            idx = (player_index + i) % 4
            p = self.game_state.players[idx]

            wind_symbol = ["E", "S", "W", "N"][idx]
            dealer_mark = " [DEALER]" if p.is_dealer else ""
            riichi_mark = " [R]" if p.riichi_declared else ""
            tenpai_mark = " [T]" if p.is_tenpai else ""

            print(f"\n{p.name}[{wind_symbol}] Score: {p.score}{dealer_mark}{riichi_mark}{tenpai_mark}")

            if idx == player_index:
                # Current player's full hand
                hand = sort_tiles(p.hand.copy())
                print(f"  Hand: {' '.join(t.unicode for t in hand)}")

                # Show shanten
                shanten = self.shanten_calc.calculate_shanten(p.hand)
                if shanten == 0:
                    waits = self.shanten_calc.get_wait_tiles(p.hand)
                    print(f"  Shanten: TENPAI (waits: {len(waits)} tiles)")
                elif shanten == -1:
                    print(f"  Shanten: AGARI!")
                else:
                    print(f"  Shanten: {shanten}")
            else:
                # Other players - show discards only
                print(f"  Hand: {' '.join(['🀫'] * len(p.hand))}")
                if p.discards:
                    print(f"  Discards: {' '.join(t.unicode for t in p.discards)}")

        print("-" * 60)

        # Discard pile
        print(f"Discard Pile: {' '.join(t.unicode for t in self.game_state.discard_pile)}")

        print("=" * 60)

    def display_hand(self, player_index: int):
        """Display player's hand with tile selection"""
        player = self.game_state.players[player_index]
        hand = sort_tiles(player.hand.copy())

        print("\nYour Hand:")
        for i, tile in enumerate(hand):
            marker = " *" if tile.just_drawn else " "
            print(f"  [{i+1}] {tile.unicode}{marker} {tile.name}")

        return hand

    def get_player_input(self, player_index: int) -> Optional[Tile]:
        """Get tile selection from player"""
        player = self.game_state.players[player_index]
        hand = sort_tiles(player.hand.copy())

        while True:
            print("\nSelect tile to discard (1-{}): ".format(len(hand)), end="")
            try:
                choice = input().strip()
                if choice.lower() in ['q', 'quit', 'exit']:
                    return None

                idx = int(choice) - 1
                if 0 <= idx < len(hand):
                    tile = hand[idx]

                    # Can always discard just-drawn tile
                    if tile.just_drawn:
                        return tile

                    # Check if tile can be discarded
                    print(f"Discard {tile.name}? (y/n): ", end="")
                    confirm = input().strip().lower()
                    if confirm == 'y':
                        return tile
                else:
                    print("Invalid choice!")
            except ValueError:
                print("Please enter a number!")

    def process_turn(self):
        """Process one turn"""
        if not self.game_state:
            return

        current = self.game_state.current_turn
        player = self.game_state.players[current]

        # Draw tile
        drawn = self.game_state.draw_tile(current)
        if drawn is None:
            print("No tiles left! Draw game.")
            return

        print(f"\n{player.name} draws {drawn[0].unicode}")

        # Check for tsumo win
        win_result = self.game_state.check_win(current, drawn[0], is_tsumo=True)
        if win_result:
            print(f"\n*** {player.name} wins by TSUMO! ***")
            print(f"Score: {win_result.score}")
            print(f"Yaku: {', '.join(win_result.yaku_names)}")
            return True

        # Check for kan
        # For simplicity, skip kan for now

        # If AI, decide discard
        if player.is_ai and current in self.ai_players:
            ai = self.ai_players[current]
            tile = ai.decide_discard(self.game_state)

            # Check riichi
            if player.can_declare_riichi() and player.is_tenpai:
                if ai.decide_riichi(self.game_state, tile):
                    print(f"\n*** {player.name} declares RIICHI! ***")
                    player.declare_riichi(tile)
        else:
            # Human input
            self.display_hand(current)
            tile = self.get_player_input(current)
            if tile is None:
                return True  # Quit

        # Discard tile
        self.game_state.discard_tile(current, tile)
        print(f"{player.name} discards {tile.unicode}")

        # Check for calls (pon, chi, ron)
        # Simplified: just check for ron
        for pid, p in enumerate(self.game_state.players):
            if pid == current:
                continue

            # Check if player can ron
            # For simplicity, AI decides
            if p.is_ai and pid in self.ai_players:
                ai = self.ai_players[pid]
                if ai.decide_call(self.game_state, "ron", tile):
                    # Check if they actually win
                    win = self.game_state.check_win(pid, tile, is_tsumo=False)
                    if win:
                        print(f"\n*** {p.name} wins by RON! ***")
                        print(f"Score: {win.score}")
                        print(f"Yaku: {', '.join(win.yaku_names)}")
                        return True
            # Human: ask if they want to ron
            else:
                print(f"\n{p.name}, do you want to ron on {tile.unicode}? (y/n): ", end="")
                if input().strip().lower() == 'y':
                    win = self.game_state.check_win(pid, tile, is_tsumo=False)
                    if win:
                        print(f"\n*** {p.name} wins by RON! ***")
                        print(f"Score: {win.score}")
                        return True

        # Next turn
        self.game_state.next_turn()
        return False

    def run_game(self):
        """Run the game loop"""
        if not self.game_state:
            print("No game created!")
            return

        max_turns = 200  # Safety limit
        turn = 0

        while turn < max_turns:
            turn += 1

            # Display state
            self.display_game_state(player_index=0)

            # Check for exhaustion
            if self.game_state.deck.remaining <= 0:
                print("\n*** DRAW - No tiles remaining! ***")
                break

            # Process turn
            game_over = self.process_turn()
            if game_over:
                break

            input("\nPress Enter to continue...")

        if turn >= max_turns:
            print("\n*** Game ended by turn limit ***")

        # Final scores
        print("\n" + "=" * 60)
        print("FINAL SCORES")
        print("=" * 60)
        for p in sorted(self.game_state.players, key=lambda x: -x.score):
            print(f"{p.name}: {p.score}")
