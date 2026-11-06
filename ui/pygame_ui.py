#!/usr/bin/env python3
"""
Mahjong Riichi - Pygame UI
Main game interface using Pygame
"""

import pygame
import sys
from typing import List, Optional, Dict
from engine.game_state import GameState
from engine.player import Player
from core.tiles import Tile
from ai.base_ai import BaseAI
from ai.advanced_ai import AdvancedAI  # Fallback
from ui.tile_renderer import TileRenderer
from ui.board_renderer import BoardRenderer
from ui.animation_manager import AnimationManager
from ui.sound_manager import SoundManager


# Colors
BG_COLOR = (45, 50, 60)
TEXT_COLOR = (220, 220, 220)
ACCENT_COLOR = (255, 200, 50)


class PygameUI:
    """
    Main Pygame UI for Mahjong game
    """

    def __init__(self, screen_width: int = 1200, screen_height: int = 800):
        # Initialize pygame
        pygame.init()

        # Screen setup
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Mahjong Riichi - Japanese Tile Game")
        self.width = screen_width
        self.height = screen_height

        # Components
        self.tile_renderer = TileRenderer()
        self.board_renderer = BoardRenderer(self.screen, self.tile_renderer)
        self.animation_manager = AnimationManager()
        self.sound_manager = SoundManager(volume=0.7)

        # Game state
        self.game_state: Optional[GameState] = None
        self.ai_players: Dict[int, BaseAI] = {}
        self.human_player_id: int = 0

        # UI state
        self.selected_tile_idx: Optional[int] = None
        self.waiting_for_input: bool = False
        self.game_over: bool = False
        self.winner: Optional[int] = None

        # Timing
        self.clock = pygame.time.Clock()
        self.ai_thinking_time: int = 500  # ms to show AI thinking
        self.last_action_time: int = 0

        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.large_font = pygame.font.Font(None, 48)
        self.medium_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)

    def create_game(self, player_names: List[str] = None,
                   ai_levels: List[int] = None) -> None:
        """Create a new game"""
        if player_names is None:
            player_names = ["You", "CPU-2", "CPU-3", "CPU-4"]
        if ai_levels is None:
            ai_levels = [0, 2, 2, 2]  # Human + 3 AI

        # Create game state
        self.game_state = GameState(player_names=player_names, seed=None)
        self.game_state.start_new_round()
        self.game_state.deal_initial_hands()

        # Create AI players
        self.ai_players = {}
        for i, level in enumerate(ai_levels):
            if i != self.human_player_id and level > 0:
                ai = self._create_ai(i, level)
                if ai:
                    self.ai_players[i] = ai

        self.selected_tile_idx = None
        self.game_over = False
        self.winner = None

    def _create_ai(self, player_id: int, level: int) -> Optional[BaseAI]:
        """Create AI player"""
        try:
            if level == 1:
                from ai.random_ai import RandomAI
                return RandomAI(player_id, level)
            elif level == 2:
                from ai.basic_ai import BasicAI
                return BasicAI(player_id, level)
            elif level >= 3:
                from ai.advanced_ai import AdvancedAI
                return AdvancedAI(player_id, level)
            else:
                return None
        except ImportError:
            # Fallback to advanced AI
            return AdvancedAI(player_id, level)

    def run(self) -> None:
        """Main game loop"""
        if self.game_state is None:
            self.create_game()

        running = True
        while running:
            dt = self.clock.tick(60)  # 60 FPS

            # Handle events
            running = self.handle_events()

            # Update game
            self.update(dt)

            # Render
            self.render()

            pygame.display.flip()

        pygame.quit()

    def handle_events(self) -> bool:
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE:
                    # Skip animation
                    self.animation_manager.clear()
                elif event.key == pygame.K_m:
                    # Toggle sound
                    self.sound_manager.toggle()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_click(event.pos)

        return True

    def handle_click(self, pos: tuple) -> None:
        """Handle mouse click"""
        x, y = pos

        # Check for call window buttons
        if self.game_state and self.game_state.call_window_active:
            button = self.board_renderer.get_button_at_pos(x, y, self.game_state)
            if button:
                self.handle_call_response(button)
                return

        # Check for tile click (only on own turn)
        if self.game_state and self.game_state.current_turn == self.human_player_id:
            player = self.game_state.players[self.human_player_id]
            idx = self.board_renderer.get_tile_at_pos(x, y, player.hand)

            if idx is not None:
                self.handle_tile_click(idx, player.hand)

    def handle_tile_click(self, idx: int, hand: List[Tile]) -> None:
        """Handle clicking on a tile in hand"""
        tile = hand[idx]

        # Can't discard just-drawn tile
        if tile.just_drawn:
            # Toggle selection
            if self.selected_tile_idx == idx:
                self.selected_tile_idx = None
            else:
                self.selected_tile_idx = idx
            return

        # If tile is selected, discard it
        if self.selected_tile_idx == idx:
            self.discard_selected_tile()
        else:
            # Select tile
            self.selected_tile_idx = idx

    def discard_selected_tile(self) -> None:
        """Discard the selected tile"""
        if self.selected_tile_idx is None:
            return

        player = self.game_state.players[self.human_player_id]
        tile = player.hand[self.selected_tile_idx]

        # Check for riichi
        if player.can_declare_riichi() and player.is_tenpai:
            # Show riichi dialog (simplified: auto riichi)
            self.game_state.declare_riichi(self.human_player_id, tile)
            self.sound_manager.play_riichi()

        # Discard
        self.game_state.discard_tile(self.human_player_id, tile)
        self.sound_manager.play_discard()
        self.selected_tile_idx = None

        # Check for calls from other players
        self.process_other_player_calls(tile)

        # Next turn
        self.game_state.next_turn()

    def handle_call_response(self, action: str) -> None:
        """Handle player's response to a call window"""
        if action == "pass":
            self.game_state._clear_call_window()
            return

        # Process the call
        meld = self.game_state.process_call(self.human_player_id, action)
        if meld:
            self.sound_manager.play_call(action)
            self.game_state.next_turn()

    def process_other_player_calls(self, tile: Tile) -> None:
        """Check and process calls from other players"""
        from_player = self.human_player_id

        # Check for pon/chi/kan
        calls = self.game_state.can_call_discard(tile, from_player)

        # For AI players, let them decide
        for player_id, available_calls in calls.items():
            ai = self.ai_players.get(player_id)
            if ai:
                for call_type in available_calls:
                    if ai.decide_call(self.game_state, call_type, tile):
                        # AI calls
                        meld = self.game_state.process_call(player_id, call_type)
                        if meld:
                            self.sound_manager.play_call(call_type)
                        return

        # Check for ron
        ron_candidates = self.game_state.check_ron_candidates(tile, from_player)
        for player_id in ron_candidates:
            ai = self.ai_players.get(player_id)
            if ai:
                if ai.decide_call(self.game_state, "ron", tile):
                    win = self.game_state.check_win(player_id, tile, is_tsumo=False)
                    if win:
                        self.handle_win(win)
                        return

    def update(self, dt: int) -> None:
        """Update game state"""
        # Update animations
        self.animation_manager.update(dt)

        if self.game_over:
            return

        if self.game_state is None:
            return

        # Check for AI turn
        current = self.game_state.current_turn
        if current != self.human_player_id:
            # AI turn
            ai = self.ai_players.get(current)
            if ai and not self.animation_manager.is_animating():
                self.process_ai_turn(ai, current)

    def process_ai_turn(self, ai: BaseAI, player_id: int) -> None:
        """Process AI player's turn"""
        player = self.game_state.players[player_id]

        # Check for ankan
        ankan_options = self.game_state.check_ankan_available(player_id)
        if ankan_options:
            # Simple ankan decision
            if ai.decide_call(self.game_state, "kan", ankan_options[0]):
                tile_type = ankan_options[0].type
                self.game_state.declare_ankan(player_id, tile_type)
                self.sound_manager.play_kan()
                return

        # Draw tile
        drawn = self.game_state.draw_tile(player_id)
        if not drawn:
            self.handle_exhaustion()
            return

        self.sound_manager.play_tile_draw()

        # Check for tsumo
        win = self.game_state.check_win(player_id, drawn, is_tsumo=True)
        if win:
            self.handle_win(win)
            return

        # Decide discard
        tile = ai.decide_discard(self.game_state)

        # Check for riichi
        if player.can_declare_riichi() and player.is_tenpai:
            if ai.decide_riichi(self.game_state, tile):
                self.game_state.declare_riichi(player_id, tile)
                self.sound_manager.play_riichi()

        # Discard
        self.game_state.discard_tile(player_id, tile)
        self.sound_manager.play_discard()

        # Check for calls from other players
        self.check_calls_for_ai(player_id, tile)

        # Next turn
        self.game_state.next_turn()

    def check_calls_for_ai(self, from_player: int, tile: Tile) -> None:
        """Check for calls from other players on AI's discard"""
        # Check pon/chi/kan
        calls = self.game_state.can_call_discard(tile, from_player)
        for player_id, available_calls in calls.items():
            ai = self.ai_players.get(player_id)
            if ai:
                for call_type in available_calls:
                    if ai.decide_call(self.game_state, call_type, tile):
                        meld = self.game_state.process_call(player_id, call_type)
                        if meld:
                            self.sound_manager.play_call(call_type)
                            return

        # Check for ron
        ron_candidates = self.game_state.check_ron_candidates(tile, from_player)
        for player_id in ron_candidates:
            ai = self.ai_players.get(player_id)
            if ai:
                if ai.decide_call(self.game_state, "ron", tile):
                    win = self.game_state.check_win(player_id, tile, is_tsumo=False)
                    if win:
                        self.handle_win(win)
                        return

    def handle_win(self, win_result) -> None:
        """Handle a win"""
        self.game_state.handle_win(win_result)
        self.sound_manager.play_win(win_result.is_tsumo)
        self.game_over = True
        self.winner = win_result.winner_id
        self.animation_manager.animate_win(
            win_result.is_tsumo,
            (self.width // 2, self.height // 2)
        )

    def handle_exhaustion(self) -> None:
        """Handle tile exhaustion (draw)"""
        self.game_state.handle_exhaustion()
        self.game_over = True
        self.winner = None

    def render(self) -> None:
        """Render the game"""
        if self.game_state:
            self.board_renderer.draw_board(
                self.game_state,
                selected_tile=self.selected_tile_idx
            )

            # Draw animations
            self.animation_manager.draw(self.screen)

            # Draw game over screen
            if self.game_over:
                self.render_game_over()

            # Draw help text
            self.render_help_text()
        else:
            self.render_start_screen()

    def render_start_screen(self) -> None:
        """Render start screen"""
        self.screen.fill(BG_COLOR)

        # Title
        title = self.title_font.render("MAHJONG RIICHI", True, ACCENT_COLOR)
        title_rect = title.get_rect(center=(self.width // 2, 200))
        self.screen.blit(title, title_rect)

        # Subtitle
        subtitle = self.medium_font.render("Japanese Traditional Tile Game", True, TEXT_COLOR)
        subtitle_rect = subtitle.get_rect(center=(self.width // 2, 260))
        self.screen.blit(subtitle, subtitle_rect)

        # Instructions
        instructions = [
            "Click on a tile to select it",
            "Click again to discard",
            "Press SPACE to skip animations",
            "Press M to toggle sound",
            "Press ESC to quit"
        ]

        y = 350
        for line in instructions:
            text = self.small_font.render(line, True, TEXT_COLOR)
            text_rect = text.get_rect(center=(self.width // 2, y))
            self.screen.blit(text, text_rect)
            y += 30

        # Start message
        start_text = self.large_font.render("Starting game...", True, ACCENT_COLOR)
        start_rect = start_text.get_rect(center=(self.width // 2, 550))
        self.screen.blit(start_text, start_rect)

    def render_game_over(self) -> None:
        """Render game over screen"""
        # Overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        # Box
        box_w, box_h = 500, 400
        box_x = self.width // 2 - box_w // 2
        box_y = self.height // 2 - box_h // 2

        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (30, 35, 45), box_rect, border_radius=20)
        pygame.draw.rect(self.screen, ACCENT_COLOR, box_rect, width=3, border_radius=20)

        # Title
        title = "GAME OVER"
        if self.winner is not None:
            winner = self.game_state.players[self.winner]
            title = f"{winner.name} WINS!"

        title_surf = self.large_font.render(title, True, ACCENT_COLOR)
        title_rect = title_surf.get_rect(center=(self.width // 2, box_y + 50))
        self.screen.blit(title_surf, title_rect)

        # Final scores
        y = box_y + 120
        sorted_players = sorted(self.game_state.players, key=lambda p: -p.score)

        for i, player in enumerate(sorted_players):
            wind = ["E", "S", "W", "N"][player.seat_wind]
            color = ACCENT_COLOR if player.player_id == self.winner else TEXT_COLOR
            text = self.medium_font.render(
                f"{wind} {player.name}: {player.score:,}",
                True, color
            )
            text_rect = text.get_rect(center=(self.width // 2, y))
            self.screen.blit(text, text_rect)
            y += 40

        # Restart instruction
        restart = self.small_font.render("Press SPACE to play again", True, TEXT_COLOR)
        restart_rect = restart.get_rect(center=(self.width // 2, box_y + box_h - 40))
        self.screen.blit(restart, restart_rect)

    def render_help_text(self) -> None:
        """Render help text at bottom of screen"""
        text = self.small_font.render(
            "ESC: Quit | SPACE: Skip Animation | M: Toggle Sound",
            True, (150, 150, 150)
        )
        self.screen.blit(text, (10, self.height - 25))


def main():
    """Main entry point"""
    ui = PygameUI()
    ui.create_game()
    ui.run()


if __name__ == "__main__":
    main()
