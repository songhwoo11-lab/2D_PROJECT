"""Lobby scene shown when the game starts and after every battle."""

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
        self.reset_player_position()

    def reset_player_position(self):
        """Put the lobby player back to the lobby entrance."""
        if self.player is None:
            return
        self.player.x = LOBBY_PLAYER_START_X
        self.player.y = LOBBY_PLAYER_START_Y

    def update(self, delta_time):
        """Advance the lobby by one frame."""
        self._clamp_player_to_bounds()

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
