#!/usr/bin/env python3
"""
Mahjong Riichi - Tile Renderer
Renders Mahjong tiles using Pygame with programmatic generation
"""

import pygame
from typing import Optional, Tuple

# =============================================================================
# TILE DIMENSIONS
# =============================================================================
TILE_WIDTH = 44
TILE_HEIGHT = 60
TILE_RADIUS = 6

# Colors for each suit
PIN_COLOR = (46, 125, 201)       # Blue
SOU_COLOR = (76, 175, 80)        # Green
MAN_COLOR = (198, 40, 40)        # Red
WIND_COLOR = (33, 33, 33)       # Dark gray
DRAGON_COLORS = {
    31: (255, 255, 255),       # White dragon - white
    32: (76, 175, 80),         # Green dragon - green
    33: (198, 40, 40),         # Red dragon - red
}

# Background colors
TILE_FACE_COLOR = (255, 255, 255)
TILE_BACK_COLOR = (70, 130, 180)
TILE_BORDER_COLOR = (50, 50, 50)
SELECTED_COLOR = (255, 215, 0)  # Gold
HIGHLIGHT_COLOR = (100, 200, 100)  # Light green


class TileRenderer:
    """Renders Mahjong tiles as Pygame surfaces"""

    def __init__(self, tile_width: int = TILE_WIDTH, tile_height: int = TILE_HEIGHT):
        self.tile_width = tile_width
        self.tile_height = tile_height
        self._tile_cache = {}
        self._back_cache = None
        self._selected_cache = {}
        self.font = None
        self._init_fonts()

    def _init_fonts(self):
        """Initialize fonts for tile text"""
        try:
            # Try to use a nice font, fall back to default
            self.font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 16)
            self.large_font = pygame.font.Font(None, 36)
        except:
            self.font = pygame.font.SysFont('arial', 20)
            self.small_font = pygame.font.SysFont('arial', 14)
            self.large_font = pygame.font.SysFont('arial', 28)

    def _get_tile_color(self, tile_type: int) -> Tuple[int, int, int]:
        """Get the color for a tile based on its type"""
        if 0 <= tile_type <= 8:
            return PIN_COLOR
        elif 9 <= tile_type <= 17:
            return SOU_COLOR
        elif 18 <= tile_type <= 26:
            return MAN_COLOR
        elif 27 <= tile_type <= 30:
            return WIND_COLOR
        else:
            return DRAGON_COLORS.get(tile_type, (255, 255, 255))

    def _get_tile_symbol(self, tile_type: int) -> str:
        """Get the symbol/number for a tile"""
        if 0 <= tile_type <= 8:
            return str(tile_type + 1)
        elif 9 <= tile_type <= 17:
            return str(tile_type - 8)
        elif 18 <= tile_type <= 26:
            return str(tile_type - 17)
        elif tile_type == 27:
            return "東"
        elif tile_type == 28:
            return "南"
        elif tile_type == 29:
            return "西"
        elif tile_type == 30:
            return "北"
        elif tile_type == 31:
            return "白"
        elif tile_type == 32:
            return "發"
        elif tile_type == 33:
            return "中"
        return "?"

    def _get_tile_name(self, tile_type: int) -> str:
        """Get the full name for a tile"""
        if 0 <= tile_type <= 8:
            return f"{tile_type + 1}筒"
        elif 9 <= tile_type <= 17:
            return f"{tile_type - 8}索"
        elif 18 <= tile_type <= 26:
            return f"{tile_type - 17}萬"
        elif tile_type == 27:
            return "東"
        elif tile_type == 28:
            return "南"
        elif tile_type == 29:
            return "西"
        elif tile_type == 30:
            return "北"
        elif tile_type == 31:
            return "白"
        elif tile_type == 32:
            return "發"
        elif tile_type == 33:
            return "中"
        return "?"

    def render_tile(self, tile_type: int, highlighted: bool = False) -> pygame.Surface:
        """Render a single tile"""
        cache_key = (tile_type, highlighted)
        if cache_key in self._tile_cache:
            return self._tile_cache[cache_key]

        # Create surface with alpha for transparency
        surface = pygame.Surface((self.tile_width, self.tile_height), pygame.SRCALPHA)

        # Draw tile background
        rect = pygame.Rect(0, 0, self.tile_width, self.tile_height)
        pygame.draw.rect(surface, TILE_FACE_COLOR, rect, border_radius=TILE_RADIUS)

        # Draw border
        border_color = HIGHLIGHT_COLOR if highlighted else TILE_BORDER_COLOR
        pygame.draw.rect(surface, border_color, rect, width=2, border_radius=TILE_RADIUS)

        # Get tile properties
        color = self._get_tile_color(tile_type)
        symbol = self._get_tile_symbol(tile_type)
        name = self._get_tile_name(tile_type)

        # Draw suit indicator (small circle)
        center_x = self.tile_width // 2
        center_y = self.tile_height // 2

        if tile_type <= 26:  # Numbered suits
            # Draw colored circle
            circle_radius = 12
            pygame.draw.circle(surface, color, (center_x, center_y - 4), circle_radius)

            # Draw number on circle
            text_color = (255, 255, 255)
            text_surf = self.large_font.render(symbol, True, text_color)
            text_rect = text_surf.get_rect(center=(center_x, center_y - 4))
            surface.blit(text_surf, text_rect)

            # Draw suit name at bottom
            text_surf = self.small_font.render(name, True, TILE_BORDER_COLOR)
            text_rect = text_surf.get_rect(center=(center_x, self.tile_height - 12))
            surface.blit(text_surf, text_rect)
        else:  # Honors (winds and dragons)
            # Draw larger area for wind/dragon
            rect_inner = pygame.Rect(4, 4, self.tile_width - 8, self.tile_height - 8)
            pygame.draw.rect(surface, (*color, 40) if color != (255, 255, 255) else (240, 240, 240),
                           rect_inner, border_radius=4)

            # Draw character
            text_color = color if color != (255, 255, 255) else TILE_BORDER_COLOR
            text_surf = self.large_font.render(symbol, True, text_color)
            text_rect = text_surf.get_rect(center=(center_x, center_y))
            surface.blit(text_surf, text_rect)

            # Draw name at bottom
            text_surf = self.small_font.render(name, True, TILE_BORDER_COLOR)
            text_rect = text_surf.get_rect(center=(center_x, self.tile_height - 12))
            surface.blit(text_surf, text_rect)

        self._tile_cache[cache_key] = surface
        return surface

    def render_back(self) -> pygame.Surface:
        """Render the back of a tile"""
        if self._back_cache is not None:
            return self._back_cache

        surface = pygame.Surface((self.tile_width, self.tile_height), pygame.SRCALPHA)

        # Draw tile background
        rect = pygame.Rect(0, 0, self.tile_width, self.tile_height)
        pygame.draw.rect(surface, TILE_BACK_COLOR, rect, border_radius=TILE_RADIUS)

        # Draw border
        pygame.draw.rect(surface, TILE_BORDER_COLOR, rect, width=2, border_radius=TILE_RADIUS)

        # Draw pattern on back
        center_x = self.tile_width // 2
        center_y = self.tile_height // 2

        # Draw inner rectangle pattern
        inner_rect = pygame.Rect(6, 6, self.tile_width - 12, self.tile_height - 12)
        pygame.draw.rect(surface, (100, 160, 210), inner_rect, width=2, border_radius=4)

        # Draw diagonal lines
        pygame.draw.line(surface, (120, 170, 220), (10, 10), (self.tile_width - 10, self.tile_height - 10), 2)
        pygame.draw.line(surface, (120, 170, 220), (self.tile_width - 10, 10), (10, self.tile_height - 10), 2)

        self._back_cache = surface
        return surface

    def render_selected(self, tile_type: int) -> pygame.Surface:
        """Render a tile with selection highlight"""
        if tile_type in self._selected_cache:
            return self._selected_cache[tile_type]

        surface = self.render_tile(tile_type)

        # Create a new surface slightly taller for the highlight bar
        new_height = self.tile_height + 8
        new_surface = pygame.Surface((self.tile_width, new_height), pygame.SRCALPHA)

        # Draw selection bar at bottom
        bar_rect = pygame.Rect(0, new_height - 8, self.tile_width, 8)
        pygame.draw.rect(new_surface, SELECTED_COLOR, bar_rect, border_radius=4)

        # Blit the tile
        new_surface.blit(surface, (0, 0))

        self._selected_cache[tile_type] = new_surface
        return new_surface

    def render_danger(self, tile_type: int) -> pygame.Surface:
        """Render a tile with danger highlight (red border)"""
        surface = self.render_tile(tile_type, highlighted=True)

        # Add red overlay
        overlay = pygame.Surface((self.tile_width, self.tile_height), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (255, 0, 0, 50), overlay.get_rect(), border_radius=TILE_RADIUS)
        surface.blit(overlay, (0, 0))

        return surface

    def get_tile_rect(self, x: int, y: int, selected: bool = False) -> pygame.Rect:
        """Get the rect for a tile at position"""
        width = self.tile_width
        height = self.tile_height + (8 if selected else 0)
        return pygame.Rect(x, y, width, height)


def test_tile_renderer():
    """Test the tile renderer"""
    pygame.init()

    # Create a small window to test
    screen = pygame.display.set_mode((800, 400))
    pygame.display.set_caption("Tile Renderer Test")

    renderer = TileRenderer()

    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        screen.fill((40, 44, 52))

        # Draw all 34 tiles
        x_offset = 10
        y_offset = 10

        for i in range(34):
            tile = renderer.render_tile(i)
            screen.blit(tile, (x_offset, y_offset))

            x_offset += renderer.tile_width + 4

            if x_offset + renderer.tile_width > 780:
                x_offset = 10
                y_offset += renderer.tile_height + 20

        # Draw back tiles
        y_offset += renderer.tile_height + 30
        for i in range(5):
            back = renderer.render_back()
            screen.blit(back, (x_offset, y_offset))
            x_offset += renderer.tile_width + 4

        # Draw selected tiles
        y_offset += renderer.tile_height + 30
        for i in range(5):
            selected = renderer.render_selected(i)
            screen.blit(selected, (x_offset, y_offset))
            x_offset += renderer.tile_width + 4

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    test_tile_renderer()
