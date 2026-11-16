"""Lobby scene shown when the game starts and after every battle."""

import math
import os

from game_config import (
    LOBBY_BOUNDS_BOTTOM,
    LOBBY_BOUNDS_LEFT,
    LOBBY_BOUNDS_RIGHT,
    LOBBY_BOUNDS_TOP,
    LOBBY_PLAYER_START_X,
    LOBBY_PLAYER_START_Y,
    LOBBY_WORLD_HEIGHT,
    LOBBY_WORLD_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from lobby_map import LOBBY_WALLS


class LobbyScene:
    """Lifecycle of the lobby: initialisation, update, and rendering."""

    def __init__(self, player, background=None, hud_font=None, state=None):
        self.player = player
        self.background = background
        self.hud_font = hud_font
        self.state = state
        self.keys = set()
        self.mouse_screen_x = SCREEN_WIDTH / 2
        self.mouse_screen_y = SCREEN_HEIGHT / 2
        self.exit_requested = False
        self.pending_action = None
        self.walls = tuple(LOBBY_WALLS)
        self.reset_player_position()

    def reset_player_position(self):
        """Put the lobby player back to the lobby entrance."""
        if self.player is None:
            return
        self.player.x = LOBBY_PLAYER_START_X
        self.player.y = LOBBY_PLAYER_START_Y

    def update(self, delta_time):
        """Advance the lobby by one frame."""
        self._update_player(delta_time)
        self._clamp_player_to_bounds()

    def _movement_input(self):
        """Return the requested movement direction from the pressed keys."""
        move_x = 0.0
        move_y = 0.0
        if "a" in self.keys:
            move_x -= 1.0
        if "d" in self.keys:
            move_x += 1.0
        if "s" in self.keys:
            move_y -= 1.0
        if "w" in self.keys:
            move_y += 1.0
        return move_x, move_y

    def _update_player(self, delta_time):
        """Move the lobby player with the shared player speed."""
        if self.player is None:
            return
        move_x, move_y = self._movement_input()
        direction_length = math.hypot(move_x, move_y)
        if direction_length > 1:
            move_x /= direction_length
            move_y /= direction_length
        step = self.player.speed * delta_time
        new_x = self.player.x + move_x * step
        if not self._collides_with_wall(new_x, self.player.y):
            self.player.x = new_x
        new_y = self.player.y + move_y * step
        if not self._collides_with_wall(self.player.x, new_y):
            self.player.y = new_y

    def _collides_with_wall(self, x, y):
        """Check whether the player circle touches a lobby obstacle."""
        if self.player is None:
            return False
        radius = self.player.radius
        for wall in self.walls:
            closest_x = min(max(x, wall.left), wall.right)
            closest_y = min(max(y, wall.bottom), wall.top)
            if math.hypot(x - closest_x, y - closest_y) < radius:
                return True
        return False

    def _clamp_player_to_bounds(self):
        """Keep the lobby player inside the walkable lobby area."""
        if self.player is None:
            return
        radius = self.player.radius
        self.player.x = min(
            max(self.player.x, LOBBY_BOUNDS_LEFT + radius),
            LOBBY_BOUNDS_RIGHT - radius,
        )
        self.player.y = min(
            max(self.player.y, LOBBY_BOUNDS_BOTTOM + radius),
            LOBBY_BOUNDS_TOP - radius,
        )

    def draw(self, draw_rectangle):
        """Render the lobby on the canvas."""
        if self.background is not None:
            self.background.draw(
                LOBBY_WORLD_WIDTH / 2,
                LOBBY_WORLD_HEIGHT / 2,
                LOBBY_WORLD_WIDTH,
                LOBBY_WORLD_HEIGHT,
            )
        if self.player is not None and self.player.image is not None:
            self.player.draw()
        if self.hud_font is not None:
            self.hud_font.draw(
                40,
                SCREEN_HEIGHT - 60,
                "LOBBY",
                (255, 255, 255),
            )
        self._draw_debug_overlay(draw_rectangle)

    def _draw_debug_overlay(self, draw_rectangle):
        """Overlay the lobby obstacles to check the layout alignment."""
        if not os.environ.get("CHALLENGING_GUNNER_LOBBY_DEBUG"):
            return
        for wall in self.walls:
            draw_rectangle(
                wall.left,
                wall.bottom,
                wall.right,
                wall.top,
                255,
                60,
                60,
                120,
                True,
            )
        draw_rectangle(
            120,
            240,
            1680,
            760,
            60,
            255,
            60,
            160,
            False,
        )

    def key_down(self, key):
        self.keys.add(key.lower())

    def key_up(self, key):
        self.keys.discard(key.lower())

    def mouse_move(self, screen_x, screen_y):
        self.mouse_screen_x = screen_x
        self.mouse_screen_y = screen_y

    def mouse_down(self, button, screen_x=None, screen_y=None):
        return None

    def mouse_up(self, button):
        return None

    def close(self):
        return None
