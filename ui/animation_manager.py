#!/usr/bin/env python3
"""
Mahjong Riichi - Animation Manager
Handles all animations for the game
"""

import pygame
import math
from typing import List, Optional, Callable, Tuple
from dataclasses import dataclass


@dataclass
class Animation:
    """Base animation class"""
    duration: float  # milliseconds
    elapsed: float = 0.0
    start_pos: Tuple[int, int] = (0, 0)
    end_pos: Tuple[int, int] = (0, 0)
    callback: Optional[Callable] = None
    active: bool = True

    def update(self, dt: float) -> bool:
        """Update animation, returns True if complete"""
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.active = False
            if self.callback:
                self.callback()
            return True
        return False

    def get_progress(self) -> float:
        """Get progress from 0.0 to 1.0"""
        if self.duration <= 0:
            return 1.0
        return min(1.0, self.elapsed / self.duration)

    def get_current_pos(self) -> Tuple[int, int]:
        """Get current position based on progress"""
        t = self._ease_function(self.get_progress())
        x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * t
        y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * t
        return (int(x), int(y))

    def _ease_function(self, t: float) -> float:
        """Ease function (can be overridden)"""
        return t  # Linear by default


class EaseOutQuad(Animation):
    """Ease out quadratic"""
    def _ease_function(self, t: float) -> float:
        return 1 - (1 - t) ** 2


class EaseInOutQuad(Animation):
    """Ease in-out quadratic"""
    def _ease_function(self, t: float) -> float:
        if t < 0.5:
            return 2 * t * t
        return 1 - ((-2 * t + 2) ** 2) / 2


class EaseOutBack(Animation):
    """Ease out with overshoot"""
    c1 = 1.70158
    c3 = c1 + 1

    def _ease_function(self, t: float) -> float:
        return 1 + self.c3 * ((t - 1) ** 3) + self.c1 * ((t - 1) ** 2)


class ArcAnimation(Animation):
    """Animation with arc trajectory"""
    arc_height: float = 50.0

    def get_current_pos(self) -> Tuple[int, int]:
        """Get position with arc"""
        t = self._ease_function(self.get_progress())
        x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * t
        base_y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * t
        # Add arc
        arc = math.sin(t * math.pi) * self.arc_height
        return (int(x), int(base_y - arc))


class FlipAnimation(Animation):
    """Tile flip animation"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rotation: float = 0.0

    def update(self, dt: float) -> bool:
        self.elapsed += dt
        self.rotation = self.get_progress() * 180
        if self.elapsed >= self.duration:
            self.active = False
            if self.callback:
                self.callback()
            return True
        return False


class PulseAnimation(Animation):
    """Pulse/glow animation"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scale: float = 1.0

    def update(self, dt: float) -> bool:
        self.elapsed += dt
        # Pulse between 1.0 and 1.2
        t = (math.sin(self.elapsed / 100) + 1) / 2
        self.scale = 1.0 + t * 0.2
        return False  # Repeating animation

    def is_complete(self) -> bool:
        return False


class ParticleAnimation:
    """Particle effect for celebrations"""
    def __init__(self, x: int, y: int, color: Tuple[int, int, int]):
        self.particles: List[dict] = []
        self.active = True
        self._spawn_particles(x, y, color)

    def _spawn_particles(self, x: int, y: int, color: Tuple[int, int, int]):
        for _ in range(20):
            angle = pygame.math.Vector2(1, 0).rotate(
                pygame.math.Vector2(0, 1).angle_to(pygame.math.Vector2(
                    x - x, y - y
                )) + pygame.time.get_ticks() % 360
            ).x * (2 * math.pi / 360) + random.random() * 2 * math.pi

            speed = 2 + random.random() * 4
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': 1.0,
                'color': color
            })

    def update(self, dt: float) -> bool:
        if not self.active:
            return True

        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.1  # gravity
            p['life'] -= 0.02

        self.particles = [p for p in self.particles if p['life'] > 0]

        if not self.particles:
            self.active = False
            return True
        return False

    def draw(self, screen: pygame.Surface):
        for p in self.particles:
            alpha = int(p['life'] * 255)
            size = int(4 * p['life'])
            if size > 0:
                pygame.draw.circle(
                    screen,
                    (*p['color'], alpha),
                    (int(p['x']), int(p['y'])),
                    size
                )


# Import random for particle effects
import random


class AnimationManager:
    """
    Manages all animations in the game
    """

    def __init__(self):
        self.animations: List[Animation] = []
        self.particles: List[ParticleAnimation] = []
        self.delayed_actions: List[Tuple[float, Callable]] = []
        self.screen_shake: Tuple[float, float] = (0, 0)
        self.screen_shake_duration: float = 0
        self.screen_shake_intensity: float = 0

    def add_animation(self, anim: Animation) -> None:
        """Add an animation to the queue"""
        anim.active = True
        self.animations.append(anim)

    def animate_tile_draw(self, start_pos: Tuple[int, int],
                         end_pos: Tuple[int, int],
                         duration_ms: int = 200,
                         callback: Optional[Callable] = None,
                         arc: bool = True) -> None:
        """Animate a tile being drawn from deck"""
        if arc:
            anim = ArcAnimation(
                duration=duration_ms,
                start_pos=start_pos,
                end_pos=end_pos,
                callback=callback,
                arc_height=30
            )
        else:
            anim = EaseOutQuad(
                duration=duration_ms,
                start_pos=start_pos,
                end_pos=end_pos,
                callback=callback
            )
        self.add_animation(anim)

    def animate_discard(self, start_pos: Tuple[int, int],
                        end_pos: Tuple[int, int],
                        duration_ms: int = 150,
                        callback: Optional[Callable] = None) -> None:
        """Animate a tile being discarded"""
        anim = EaseOutBack(
            duration=duration_ms,
            start_pos=start_pos,
            end_pos=end_pos,
            callback=callback,
            arc_height=40
        )
        self.add_animation(anim)

    def animate_call(self, meld_type: str,
                    tiles: List[Tuple[int, int]],
                    duration_ms: int = 300,
                    callback: Optional[Callable] = None) -> None:
        """Animate meld call (pon/chi/kan)"""
        # Animate tiles moving together
        if len(tiles) >= 2:
            target = tiles[0]
            for i, pos in enumerate(tiles[1:], 1):
                delay = i * 50
                def make_callback(pos=pos, target=target):
                    def cb():
                        pass  # Will be updated when integrating with board
                    return cb
                anim = EaseOutQuad(
                    duration=duration_ms,
                    start_pos=pos,
                    end_pos=target,
                    callback=callback if i == len(tiles) - 1 else None
                )
                # Delay start slightly
                anim.elapsed = -delay
                self.add_animation(anim)

    def animate_dora_reveal(self, pos: Tuple[int, int],
                            duration_ms: int = 400,
                            callback: Optional[Callable] = None) -> None:
        """Animate dora indicator reveal with flip"""
        anim = FlipAnimation(
            duration=duration_ms,
            start_pos=pos,
            end_pos=pos,
            callback=callback
        )
        self.add_animation(anim)

    def animate_win(self, is_tsumo: bool,
                   pos: Tuple[int, int],
                   duration_ms: int = 1000,
                   callback: Optional[Callable] = None) -> None:
        """Animate winning hand"""
        # Pulse animation for win
        anim = PulseAnimation(
            duration=duration_ms,
            start_pos=pos,
            end_pos=pos,
            callback=callback
        )
        self.add_animation(anim)

        # Add celebration particles
        colors = [(255, 215, 0), (255, 100, 100), (100, 255, 100)]
        for color in colors:
            particle = ParticleAnimation(pos[0], pos[1], color)
            self.particles.append(particle)

    def animate_screen_shake(self, intensity: float = 10,
                           duration_ms: int = 200) -> None:
        """Trigger screen shake effect"""
        self.screen_shake_intensity = intensity
        self.screen_shake_duration = duration_ms

    def update(self, dt: float) -> None:
        """Update all animations"""
        # Update animations
        for anim in self.animations[:]:
            if anim.active:
                anim.update(dt)
            if not anim.active:
                self.animations.remove(anim)

        # Update particles
        for particle in self.particles[:]:
            if particle.update(dt):
                self.particles.remove(particle)

        # Update screen shake
        if self.screen_shake_duration > 0:
            self.screen_shake_duration -= dt
            if self.screen_shake_duration <= 0:
                self.screen_shake = (0, 0)
            else:
                import random
                self.screen_shake = (
                    random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity),
                    random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity)
                )

        # Process delayed actions
        for delay, action in self.delayed_actions[:]:
            if delay <= 0:
                action()
                self.delayed_actions.remove((delay, action))
            else:
                self.delayed_actions[self.delayed_actions.index((delay, action))] = (delay - dt, action)

    def delay_action(self, delay_ms: int, action: Callable) -> None:
        """Schedule an action to run after delay"""
        self.delayed_actions.append((delay_ms, action))

    def get_animation_at_pos(self, pos: Tuple[int, int]) -> Optional[Animation]:
        """Get active animation at a position"""
        for anim in self.animations:
            if anim.active:
                anim_pos = anim.get_current_pos()
                if abs(anim_pos[0] - pos[0]) < 50 and abs(anim_pos[1] - pos[1]) < 50:
                    return anim
        return None

    def draw(self, screen: pygame.Surface) -> None:
        """Draw particle effects"""
        for particle in self.particles:
            particle.draw(screen)

    def is_animating(self) -> bool:
        """Check if any animations are active"""
        return any(a.active for a in self.animations) or len(self.particles) > 0

    def clear(self) -> None:
        """Clear all animations"""
        self.animations.clear()
        self.particles.clear()
        self.delayed_actions.clear()
