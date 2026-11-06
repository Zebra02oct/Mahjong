#!/usr/bin/env python3
"""
Mahjong Riichi - Board Renderer
Renders the game board layout with all players
"""

import pygame
from typing import List, Optional, Tuple, Dict
from core.tiles import Tile
from engine.player import Player
from core.constants import TILE_UNICODE, SEAT_WIND_NAMES


# Colors
BG_COLOR = (45, 50, 60)
TABLE_COLOR = (35, 100, 70)
TABLE_BORDER = (25, 80, 55)
INFO_BG = (30, 35, 45)
INFO_BORDER = (60, 70, 80)
TEXT_COLOR = (220, 220, 220)
ACCENT_COLOR = (255, 200, 50)
DANGER_COLOR = (200, 50, 50)
SAFE_COLOR = (50, 200, 100)

# Dimensions
TILE_W = 44
TILE_H = 60
TILE_GAP = 4
DISCARD_COLS = 6


class BoardRenderer:
    """
    Renders the Mahjong game board
    """

    def __init__(self, screen: pygame.Surface, tile_renderer):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.tile_renderer = tile_renderer

        # Calculate layout
        self._calculate_layout()

        # Cached surfaces
        self._info_panel_cache = {}

    def _calculate_layout(self):
        """Calculate positions for all UI elements"""
        center_x = self.width // 2
        center_y = self.height // 2

        # Main hand (bottom player) position
        self.own_hand_x = center_x - (14 * (TILE_W + TILE_GAP)) // 2
        self.own_hand_y = self.height - TILE_H - 80

        # Other players' hand positions
        hand_offset = TILE_W + 10

        # Left player (vertical)
        self.left_hand_x = 60
        self.left_hand_y = center_y - (7 * (TILE_H + 6)) // 2

        # Right player (vertical)
        self.right_hand_x = self.width - 60 - TILE_H
        self.right_hand_y = center_y - (7 * (TILE_H + 6)) // 2

        # Top player (horizontal, showing fewer tiles)
        self.top_hand_x = center_x - (13 * (TILE_W + TILE_GAP)) // 2
        self.top_hand_y = 60

        # Discard pile positions
        discard_area_size = 180
        self.own_discard_x = self.own_hand_x
        self.own_discard_y = self.own_hand_y - 140

        self.left_discard_x = self.left_hand_x + 60
        self.left_discard_y = center_y - discard_area_size // 2

        self.right_discard_x = self.right_hand_x - 60
        self.right_discard_y = center_y - discard_area_size // 2

        self.top_discard_x = center_x - discard_area_size // 2
        self.top_discard_y = self.top_hand_y + TILE_H + 30

        # Dora indicator position (center)
        self.dora_x = center_x - 60
        self.dora_y = center_y - 30

        # Info panel position
        self.info_panel_x = self.width - 200
        self.info_panel_y = 20
        self.info_panel_w = 180
        self.info_panel_h = 200

    def draw_board(self, game_state, selected_tile: Optional[int] = None,
                   valid_discards: Optional[List[int]] = None,
                   highlighted_tile: Optional[int] = None):
        """Draw the complete game board"""
        # Draw background
        self.screen.fill(BG_COLOR)

        # Draw table
        table_rect = pygame.Rect(40, 40, self.width - 80, self.height - 80)
        pygame.draw.rect(self.screen, TABLE_COLOR, table_rect, border_radius=20)
        pygame.draw.rect(self.screen, TABLE_BORDER, table_rect, width=4, border_radius=20)

        # Draw player areas
        self._draw_player_areas(game_state)

        # Draw dora indicators
        self._draw_dora(game_state)

        # Draw discard piles
        self._draw_discards(game_state)

        # Draw info panel
        self._draw_info_panel(game_state)

        # Draw call window if active
        if game_state.call_window_active:
            self._draw_call_window(game_state)

        # Draw turn indicator
        self._draw_turn_indicator(game_state)

    def _draw_player_areas(self, game_state):
        """Draw all player hands"""
        players = game_state.players
        current = game_state.current_turn

        for i, player in enumerate(players):
            if i == current:
                self._draw_current_turn_indicator(player)
            self._draw_player_label(player, i)

        # Own hand (player 0 - bottom)
        own_hand = players[0].hand
        self._draw_own_hand(own_hand, selected_tile)

        # Left player (player 1)
        self._draw_other_hand(players[1].hand, 'left')

        # Top player (player 2)
        self._draw_other_hand(players[2].hand, 'top')

        # Right player (player 3)
        self._draw_other_hand(players[3].hand, 'right')

    def _draw_own_hand(self, tiles: List[Tile], selected_idx: Optional[int] = None):
        """Draw the player's own hand (interactive)"""
        for i, tile in enumerate(tiles):
            x = self.own_hand_x + i * (TILE_W + TILE_GAP)
            y = self.own_hand_y

            # Check if selected
            if selected_idx == i:
                surf = self.tile_renderer.render_selected(tile.type)
                y -= 15  # Lift up
            else:
                surf = self.tile_renderer.render_tile(tile.type)

            self.screen.blit(surf, (x, y))

    def _draw_other_hand(self, tiles: List[Tile], position: str):
        """Draw another player's hand (face down)"""
        count = len(tiles)

        if position == 'left':
            for i in range(count):
                x = self.left_hand_x
                y = self.left_hand_y + i * (TILE_H + 6)
                surf = self.tile_renderer.render_back()
                rotated = pygame.transform.rotate(surf, 90)
                self.screen.blit(rotated, (x, y))

        elif position == 'top':
            x_start = self.top_hand_x
            y = self.top_hand_y
            for i in range(count):
                x = x_start + i * (TILE_W + TILE_GAP)
                surf = self.tile_renderer.render_back()
                self.screen.blit(surf, (x, y))

        elif position == 'right':
            for i in range(count):
                x = self.right_hand_x
                y = self.right_hand_y + i * (TILE_H + 6)
                surf = self.tile_renderer.render_back()
                rotated = pygame.transform.rotate(surf, -90)
                self.screen.blit(rotated, (x, y))

    def _draw_discards(self, game_state):
        """Draw all discard piles"""
        for i, player in enumerate(game_state.players):
            discards = player.discards
            position = ['own', 'left', 'top', 'right'][i]
            self._draw_discard_pile(discards, position)

    def _draw_discard_pile(self, discards: List[Tile], position: str):
        """Draw a single discard pile"""
        if not discards:
            return

        if position == 'own':
            x = self.own_discard_x
            y = self.own_discard_y
            cols = DISCARD_COLS
            dx = TILE_W + 2
            dy = TILE_H + 2

        elif position == 'left':
            x = self.left_discard_x
            y = self.left_discard_y
            cols = 2
            dx = TILE_W + 2
            dy = TILE_H + 2

        elif position == 'top':
            x = self.top_discard_x
            y = self.top_discard_y
            cols = DISCARD_COLS
            dx = TILE_W + 2
            dy = TILE_H + 2

        elif position == 'right':
            x = self.right_discard_x
            y = self.right_discard_y
            cols = 2
            dx = TILE_W + 2
            dy = TILE_H + 2

        for i, tile in enumerate(discards):
            col = i % cols
            row = i // cols

            tx = x + col * dx
            ty = y + row * dy

            surf = self.tile_renderer.render_tile(tile.type, highlighted=False)
            self.screen.blit(surf, (tx, ty))

    def _draw_dora(self, game_state):
        """Draw dora indicators"""
        dora = game_state.dora_indicators
        x = self.dora_x
        y = self.dora_y

        # Draw label
        font = pygame.font.Font(None, 20)
        label = font.render("DORA", True, TEXT_COLOR)
        self.screen.blit(label, (x, y - 20))

        for i, indicator in enumerate(dora):
            tx = x + i * (TILE_W + 5)
            surf = self.tile_renderer.render_tile(indicator.type, highlighted=True)
            self.screen.blit(surf, (tx, y))

    def _draw_info_panel(self, game_state):
        """Draw player scores and game info"""
        panel_rect = pygame.Rect(
            self.info_panel_x, self.info_panel_y,
            self.info_panel_w, self.info_panel_h
        )
        pygame.draw.rect(self.screen, INFO_BG, panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, INFO_BORDER, panel_rect, width=2, border_radius=10)

        font = pygame.font.Font(None, 22)
        small_font = pygame.font.Font(None, 18)

        y = self.info_panel_y + 15
        x = self.info_panel_x + 10

        # Round info
        round_text = f"Round {game_state.round_number}"
        text = font.render(round_text, True, TEXT_COLOR)
        self.screen.blit(text, (x, y))
        y += 25

        honba_text = f"Honba: {game_state.honba}"
        text = small_font.render(honba_text, True, ACCENT_COLOR)
        self.screen.blit(text, (x, y))
        y += 20

        riichi_text = f"Riichi: {game_state.riichi_sticks}"
        text = small_font.render(riichi_text, True, ACCENT_COLOR)
        self.screen.blit(text, (x, y))
        y += 30

        # Separator
        pygame.draw.line(self.screen, INFO_BORDER, (x, y), (x + self.info_panel_w - 20, y), 1)
        y += 15

        # Player scores
        for i, player in enumerate(game_state.players):
            wind = ["E", "S", "W", "N"][i]
            is_current = i == game_state.current_turn

            color = ACCENT_COLOR if is_current else TEXT_COLOR
            name_text = f"{wind} {player.name[:8]}"
            text = small_font.render(name_text, True, color)
            self.screen.blit(text, (x, y))
            y += 18

            score_text = f"   {player.score:,}"
            text = small_font.render(score_text, True, color)
            self.screen.blit(text, (x, y))

            # Riichi marker
            if player.riichi_declared:
                marker = font.render("R", True, DANGER_COLOR)
                self.screen.blit(marker, (x + self.info_panel_w - 30, y - 2))

            y += 22

        # Deck count
        y += 10
        remaining = game_state.deck.remaining
        deck_text = f"Deck: {remaining}"
        text = small_font.render(deck_text, True, TEXT_COLOR)
        self.screen.blit(text, (x, y))

    def _draw_player_label(self, player: Player, position: int):
        """Draw player name label"""
        font = pygame.font.Font(None, 24)

        names = {
            0: (self.width // 2, self.height - 25),  # Bottom
            1: (25, self.height // 2),  # Left
            2: (self.width // 2, 35),  # Top
            3: (self.width - 25, self.height // 2),  # Right
        }

        x, y = names[position]
        wind = ["E", "S", "W", "N"][position]

        label = f"{wind} {player.name[:6]}"
        text = font.render(label, True, TEXT_COLOR)

        if position in [0, 2]:
            rect = text.get_rect(centerx=x, centery=y)
        else:
            rect = text.get_rect(centerx=x, centery=y)

        # Background
        bg_rect = rect.inflate(10, 6)
        pygame.draw.rect(self.screen, INFO_BG, bg_rect, border_radius=5)
        self.screen.blit(text, rect)

    def _draw_current_turn_indicator(self, player: Player):
        """Draw indicator showing whose turn it is"""
        # Arrow indicator pointing to current player
        pass  # Could add animated indicator

    def _draw_turn_indicator(self, game_state):
        """Draw arrow pointing to current player"""
        current = game_state.current_turn

        arrow_positions = {
            0: (self.width // 2, self.height - TILE_H - 105),  # Below own hand
            1: (30, self.height // 2 - 50),  # Left of left hand
            2: (self.width // 2, TILE_H + 80),  # Above top hand
            3: (self.width - 30, self.height // 2 - 50),  # Right of right hand
        }

        x, y = arrow_positions[current]

        # Draw pulsing indicator
        import math
        pulse = (math.sin(pygame.time.get_ticks() / 200) + 1) / 2
        size = int(10 + pulse * 5)

        color = (255, 200, 50, int(150 + pulse * 105))
        pygame.draw.circle(self.screen, ACCENT_COLOR, (x, y), size)

    def _draw_call_window(self, game_state):
        """Draw popup for pon/chi/kan/ron calls"""
        if not game_state.call_window_active:
            return

        tile = game_state.call_tile
        if tile is None:
            return

        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))

        # Call window box
        window_w = 300
        window_h = 200
        window_x = self.width // 2 - window_w // 2
        window_y = self.height // 2 - window_h // 2

        box_rect = pygame.Rect(window_x, window_y, window_w, window_h)
        pygame.draw.rect(self.screen, INFO_BG, box_rect, border_radius=15)
        pygame.draw.rect(self.screen, ACCENT_COLOR, box_rect, width=3, border_radius=15)

        # Title
        font = pygame.font.Font(None, 32)
        title = font.render("CALL AVAILABLE", True, ACCENT_COLOR)
        title_rect = title.get_rect(centerx=window_x + window_w // 2, top=window_y + 15)
        self.screen.blit(title, title_rect)

        # Draw the tile
        tile_surf = self.tile_renderer.render_tile(tile.type)
        tile_rect = tile_surf.get_rect(centerx=window_x + window_w // 2, centery=window_y + 80)
        self.screen.blit(tile_surf, tile_rect)

        # Buttons
        font = pygame.font.Font(None, 24)
        button_y = window_y + 130

        # Get available calls
        player = game_state.players[game_state.current_turn]
        calls = player.get_callable_actions(tile)

        buttons = []
        if "ron" in calls:
            buttons.append(("RON", DANGER_COLOR))
        if "pon" in calls:
            buttons.append(("PON", SAFE_COLOR))
        if "chi" in calls:
            buttons.append(("CHI", SAFE_COLOR))
        if "kan" in calls:
            buttons.append(("KAN", SAFE_COLOR))
        buttons.append(("PASS", (100, 100, 100)))

        # Draw buttons
        btn_w = 60
        btn_h = 35
        total_btn_w = len(buttons) * (btn_w + 10) - 10
        start_x = window_x + window_w // 2 - total_btn_w // 2

        for i, (label, color) in enumerate(buttons):
            bx = start_x + i * (btn_w + 10)
            btn_rect = pygame.Rect(bx, button_y, btn_w, btn_h)
            pygame.draw.rect(self.screen, color, btn_rect, border_radius=8)

            text = font.render(label, True, (255, 255, 255))
            text_rect = text.get_rect(center=btn_rect.center)
            self.screen.blit(text, text_rect)

    def get_tile_at_pos(self, x: int, y: int, tiles: List[Tile]) -> Optional[int]:
        """Get tile index at screen position"""
        # Check own hand
        for i, tile in enumerate(tiles):
            tx = self.own_hand_x + i * (TILE_W + TILE_GAP)
            ty = self.own_hand_y

            if tx <= x <= tx + TILE_W and ty <= y <= ty + TILE_H:
                return i

        return None

    def get_button_at_pos(self, x: int, y: int, game_state) -> Optional[str]:
        """Check if click is on a call button"""
        if not game_state.call_window_active:
            return None

        window_w = 300
        window_h = 200
        window_x = self.width // 2 - window_w // 2
        window_y = self.height // 2 - window_h // 2

        button_y = window_y + 130
        btn_w = 60
        btn_h = 35
        total_btn_w = 5 * (btn_w + 10) - 10  # Max 5 buttons
        start_x = window_x + window_w // 2 - total_btn_w // 2

        player = game_state.players[game_state.current_turn]
        calls = player.get_callable_actions(game_state.call_tile)

        buttons = []
        if "ron" in calls:
            buttons.append("ron")
        if "pon" in calls:
            buttons.append("pon")
        if "chi" in calls:
            buttons.append("chi")
        if "kan" in calls:
            buttons.append("kan")
        buttons.append("pass")

        for i, action in enumerate(buttons):
            bx = start_x + i * (btn_w + 10)

            if bx <= x <= bx + btn_w and button_y <= y <= button_y + btn_h:
                return action

        return None
