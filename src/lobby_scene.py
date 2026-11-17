"""Lobby scene shown when the game starts and after every battle."""

import pico2d

from battle_record import result_record_text
from game_config import (
    LOBBY_WORLD_HEIGHT,
    LOBBY_WORLD_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TOTAL_WAVES,
)
from hud import draw_centered_text, draw_text_at_center
from lobby_map import (
    LOCATION_ACTIONS,
    LOBBY_LOCATIONS,
    LOBBY_MOVES,
    LOBBY_NODE_BY_KEY,
    LOBBY_START_KEY,
)
from weapon import weapon_display_name


class LobbyScene:
    """Lifecycle of the lobby: initialisation, update, and rendering."""

    def __init__(
        self,
        player,
        background=None,
        hud_font=None,
        state=None,
        node_key=None,
    ):
        self.player = player
        self.background = background
        self.hud_font = hud_font
        self.state = state
        self.keys = set()
        self.mouse_screen_x = SCREEN_WIDTH / 2
        self.mouse_screen_y = SCREEN_HEIGHT / 2
        self.exit_requested = False
        self.pending_action = None
        self.locations = tuple(LOBBY_LOCATIONS)
        self.current_node = (
            node_key if node_key in LOBBY_NODE_BY_KEY else LOBBY_START_KEY
        )
        self.nearby_location = None
        self.panel = None
        self.gun_selection_index = 0
        self._place_player_at_current_node()

    def reset_player_position(self):
        """Put the lobby player back at the central node."""
        self.current_node = LOBBY_START_KEY
        self._place_player_at_current_node()

    def _place_player_at_current_node(self):
        self.nearby_location = LOBBY_NODE_BY_KEY.get(self.current_node)
        if self.player is None:
            return
        node = LOBBY_NODE_BY_KEY[self.current_node]
        self.player.x = node.zone_x
        self.player.y = node.zone_y

    def update(self, delta_time):
        """Keep the fixed lobby position in sync with the current node."""
        self._update_nearby_location()

    def _update_nearby_location(self):
        """Remember the fixed location the player is standing at."""
        self.nearby_location = LOBBY_NODE_BY_KEY.get(self.current_node)

    def location_at(self, x, y):
        """Return the location whose interaction area covers the position."""
        for location in self.locations:
            if location.contains(x, y):
                return location
        return None

    def _move_to_adjacent_node(self, key):
        """Move directly to the node connected by the pressed wasd key."""
        next_key = LOBBY_MOVES.get((self.current_node, key))
        if next_key is None:
            return
        node = LOBBY_NODE_BY_KEY[next_key]
        self.current_node = next_key
        if self.player is not None:
            self.player.x = node.zone_x
            self.player.y = node.zone_y
        self._update_nearby_location()

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
        self._draw_direction_arrows()
        if self.hud_font is not None:
            self.hud_font.draw(
                40,
                SCREEN_HEIGHT - 60,
                "LOBBY",
                (255, 255, 255),
            )
        self._draw_location_labels()
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
            "W/S : SELECT    SPACE : CONFIRM    Q : CANCEL",
            (170, 190, 220),
        )

    def _draw_direction_arrows(self):
        """Show the movement directions available from the current node."""
        if self.player is None:
            return
        available = {
            direction
            for (node, direction) in LOBBY_MOVES
            if node == self.current_node
        }
        size = 12.0
        # Small isosceles triangles pointing toward the available node.
        triangles = {
            "w": (
                (0.0, size * 1.5),
                (-size, -size * 0.5),
                (size, -size * 0.5),
            ),
            "a": (
                (-size * 1.5, 0.0),
                (size * 0.5, size),
                (size * 0.5, -size),
            ),
            "s": (
                (0.0, -size * 1.5),
                (-size, size * 0.5),
                (size, size * 0.5),
            ),
            "d": (
                (size * 1.5, 0.0),
                (-size * 0.5, size),
                (-size * 0.5, -size),
            ),
        }
        color = (170, 190, 220, 255)
        for direction in ("w", "a", "s", "d"):
            if direction not in available:
                continue
            base_x = self.player.x
            base_y = self.player.y
            offset = 70.0
            if direction == "w":
                base_y += offset
            elif direction == "s":
                base_y -= offset
            elif direction == "a":
                base_x -= offset
            elif direction == "d":
                base_x += offset
            points = [
                (base_x + dx, base_y + dy) for dx, dy in triangles[direction]
            ]
            # Fill the triangle with horizontal scanlines.
            min_y = min(point[1] for point in points)
            max_y = max(point[1] for point in points)
            for scan_y in range(int(min_y), int(max_y) + 1):
                intersections = []
                for index in range(3):
                    start = points[index]
                    end = points[(index + 1) % 3]
                    y1, y2 = start[1], end[1]
                    if (y1 <= scan_y <= y2) or (y2 <= scan_y <= y1):
                        if abs(y2 - y1) < 0.0001:
                            intersections.append(start[0])
                            intersections.append(end[0])
                        else:
                            ratio = (scan_y - y1) / (y2 - y1)
                            intersections.append(start[0] + (end[0] - start[0]) * ratio)
                if len(intersections) < 2:
                    continue
                left = int(min(intersections))
                right = int(max(intersections))
                try:
                    pico2d.draw_line(
                        left,
                        scan_y,
                        right,
                        scan_y,
                        *color[:3],
                        color[3],
                    )
                except Exception:
                    pass

    def _draw_location_labels(self):
        """Draw only the current location name."""
        if self.hud_font is None or self.nearby_location is None:
            return
        location = self.nearby_location
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
            elif key in ("space", "q"):
                self.close_panel()
            return
        if key in ("w", "a", "s", "d"):
            self._move_to_adjacent_node(key)
            return
        if key == "space" and self.nearby_location is not None:
            self._activate_location(self.nearby_location)

    def _activate_location(self, location):
        """Run the action bound to the fixed location the player stands at."""
        action = LOCATION_ACTIONS.get(location.key)
        if action is None:
            return
        if action == "exit_game":
            self.exit_requested = True
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
        elif key == "space":
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
