"""Lobby scene shown when the game starts and after every battle."""

import math

from battle_record import result_record_text
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
    TOTAL_WAVES,
)
from hud import draw_centered_text, draw_text_at_center
from lobby_map import LOCATION_ACTIONS, LOBBY_LOCATIONS, LOBBY_WALLS
from weapon import weapon_display_name


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
        self.locations = tuple(LOBBY_LOCATIONS)
        self.nearby_location = None
        self.panel = None
        self.gun_selection_index = 0
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
        self._update_nearby_location()

    def _update_nearby_location(self):
        """Remember the location the player currently stands next to."""
        if self.player is None:
            self.nearby_location = None
            return
        self.nearby_location = self.location_at(self.player.x, self.player.y)

    def location_at(self, x, y):
        """Return the location whose interaction area covers the position."""
        for location in self.locations:
            if location.contains(x, y):
                return location
        return None

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
        self._draw_location_labels()
        self._draw_nearby_location_marker(draw_rectangle)
        if self.panel == "records":
            self._draw_records_panel(draw_rectangle)
        elif self.panel == "gun_select":
            self._draw_gun_selection_panel(draw_rectangle)

    def _draw_gun_selection_panel(self, draw_rectangle):
        """Draw the gun list that is shown before the battle starts."""
        draw_rectangle(
            0,
            0,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            10,
            10,
            20,
            210,
            True,
        )
        if self.hud_font is None:
            return
        draw_centered_text(
            self.hud_font,
            SCREEN_HEIGHT - 180,
            "SELECT GUN",
            (255, 220, 100),
        )
        owned_guns = self.state.owned_guns if self.state is not None else []
        for index, gun_id in enumerate(owned_guns):
            color = (
                (255, 220, 100)
                if index == self.gun_selection_index
                else (255, 255, 255)
            )
            draw_centered_text(
                self.hud_font,
                SCREEN_HEIGHT - 280 - index * 60,
                weapon_display_name(gun_id),
                color,
            )
        draw_centered_text(
            self.hud_font,
            120,
            "W/S : SELECT    ENTER : CONFIRM    Q : CANCEL",
            (170, 190, 220),
        )

    def _draw_location_labels(self):
        """Draw the name of every place and the access guide of the nearby one."""
        if self.hud_font is None:
            return
        for location in self.locations:
            label_y = min(
                location.zone_y + location.zone_radius + 40.0,
                SCREEN_HEIGHT - 120.0,
            )
            draw_text_at_center(
                self.hud_font,
                location.zone_x,
                label_y,
                location.label,
                (170, 190, 220),
            )
        if self.nearby_location is None or self.panel is not None:
            return
        draw_centered_text(
            self.hud_font,
            SCREEN_HEIGHT - 200.0,
            "PRESS ENTER : {}".format(self.nearby_location.label),
            (255, 220, 100),
        )

    def _draw_nearby_location_marker(self, draw_rectangle):
        """Mark the interaction area the player is standing next to."""
        location = self.nearby_location
        if location is None or self.panel is not None:
            return
        draw_rectangle(
            location.zone_x - location.zone_radius,
            location.zone_y - location.zone_radius,
            location.zone_x + location.zone_radius,
            location.zone_y + location.zone_radius,
            255,
            220,
            60,
            220,
            False,
        )

    def _draw_records_panel(self, draw_rectangle):
        """Draw the battle record list over the lobby."""
        draw_rectangle(
            0,
            0,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            10,
            10,
            20,
            210,
            True,
        )
        if self.hud_font is None:
            return
        draw_centered_text(
            self.hud_font,
            SCREEN_HEIGHT - 180,
            "BATTLE RECORDS",
            (255, 220, 100),
        )
        records = self.state.records if self.state is not None else []
        if not records:
            draw_centered_text(
                self.hud_font,
                SCREEN_HEIGHT - 280,
                "NO RECORDS YET",
            )
            return
        for index, record in enumerate(records):
            text = result_record_text(
                record.result,
                record.reached_wave,
                TOTAL_WAVES,
                record.elapsed_time,
                record.clear_time,
            )
            draw_centered_text(
                self.hud_font,
                SCREEN_HEIGHT - 280 - index * 60,
                text,
            )

    def key_down(self, key):
        key = key.lower()
        if key in self.keys:
            return
        self.keys.add(key)
        if self.panel is not None:
            if self.panel == "gun_select":
                self._handle_gun_selection_key(key)
            elif key in ("return", "enter", "q"):
                self.close_panel()
            return
        if key in ("return", "enter") and self.nearby_location is not None:
            self._activate_location(self.nearby_location)

    def _activate_location(self, location):
        """Run the action bound to the location the player stands at."""
        action = LOCATION_ACTIONS.get(location.key)
        if action is None:
            return
        if action == "show_records":
            self.open_records()
            return
        if action == "enter_portal":
            self._start_battle_entry()
            return
        self.pending_action = action

    def _start_battle_entry(self):
        """Start the battle entry flow and check the gun selection first."""
        if self.state is not None and self.state.needs_gun_selection():
            self.open_gun_selection()
            return
        self.pending_action = "start_battle"

    def open_gun_selection(self):
        """Show the gun selection screen before the battle starts."""
        self.panel = "gun_select"
        self.gun_selection_index = 0
        if self.state is None:
            return
        if self.state.selected_gun in self.state.owned_guns:
            self.gun_selection_index = self.state.owned_guns.index(
                self.state.selected_gun
            )

    def _handle_gun_selection_key(self, key):
        """Move the selection and confirm or cancel the chosen gun."""
        owned_guns = self.state.owned_guns if self.state is not None else []
        if not owned_guns:
            return
        if key in ("w", "up"):
            self.gun_selection_index = (self.gun_selection_index - 1) % len(owned_guns)
        elif key in ("s", "down"):
            self.gun_selection_index = (self.gun_selection_index + 1) % len(owned_guns)
        elif key in ("return", "enter"):
            self._confirm_gun_selection()
        elif key == "q":
            self.close_panel()

    def _confirm_gun_selection(self):
        """Store the chosen gun and ask the app to start the battle."""
        if self.state is None:
            self.close_panel()
            return
        gun_id = self.state.owned_guns[self.gun_selection_index]
        self.state.select_gun(gun_id)
        self.close_panel()
        self.pending_action = "start_battle"

    def open_records(self):
        """Show the battle record panel."""
        self.panel = "records"

    def close_panel(self):
        """Close the panel that is currently open."""
        self.panel = None

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
