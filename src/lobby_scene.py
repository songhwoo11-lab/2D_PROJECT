"""Lobby scene shown when the game starts and after every battle."""

import math

import pico2d

from audio import (
    LOBBY_MUSIC_FILE,
    LOBBY_PORTAL_ENTRY_SOUND_FILE,
    RECORDS_MUSIC_FILE,
)
from battle_record import result_record_text, training_record_text
from game_config import (
    DIFFICULTIES,
    DIFFICULTY_EASY,
    DIFFICULTY_HARD,
    DIFFICULTY_NORMAL,
    DEFAULT_DIFFICULTY,
    LOBBY_WORLD_HEIGHT,
    LOBBY_WORLD_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TOTAL_WAVES,
    normalize_difficulty,
)
from hud import draw_centered_text, draw_text_at_center
from lobby_map import (
    LOCATION_ACTIONS,
    LOBBY_LOCATIONS,
    LOBBY_MOVES,
    LOBBY_NODE_BY_KEY,
    LOBBY_START_KEY,
)
from shop import GUN_SHOP_ORDER
from weapon import RIFLE_GUN_ID, weapon_display_name, weapon_stats_at_level


PORTAL_ENTRY_SECONDS = 3.0
PORTAL_ENTRY_TOTAL_ROTATIONS = 3.0
PORTAL_ENTRY_MOVE_DEPTH = 120.0
PORTAL_ENTRY_SPEED_GROWTH_RATE = 3.0

GUN_SELECT_TITLE_Y = SCREEN_HEIGHT - 120
# 총칸은 상점에서 사용하는 것과 같은 이미지를 같은 크기로 출력한다.
GUN_SELECT_SELECTED_SLOT_SIZE = (472, 508)
GUN_SELECT_UNSELECTED_SLOT_SIZE = (464, 509)
GUN_SELECT_CARD_WIDTH = max(
    GUN_SELECT_SELECTED_SLOT_SIZE[0], GUN_SELECT_UNSELECTED_SLOT_SIZE[0]
)
GUN_SELECT_CARD_HEIGHT = max(
    GUN_SELECT_SELECTED_SLOT_SIZE[1], GUN_SELECT_UNSELECTED_SLOT_SIZE[1]
)
GUN_SELECT_CARD_GAP = 60
GUN_SELECT_CARD_LEFT = (
    SCREEN_WIDTH
    - (len(GUN_SHOP_ORDER) * GUN_SELECT_CARD_WIDTH + (len(GUN_SHOP_ORDER) - 1) * GUN_SELECT_CARD_GAP)
) // 2
GUN_SELECT_CARD_BOTTOM = 320
GUN_SELECT_CARD_TOP = GUN_SELECT_CARD_BOTTOM + GUN_SELECT_CARD_HEIGHT
GUN_SELECT_NAME_Y = GUN_SELECT_CARD_TOP - 48
GUN_SELECT_IMAGE_Y = 710
GUN_SELECT_STATE_FIRST_ROW_OFFSET = 70
GUN_SELECT_STATE_ROW_GAP = 40
GUN_SELECT_STATE_TEXT_COLOR = (255, 255, 255)
GUN_SELECT_LOCKED_OPACITY = 0.5
GUN_SELECT_LOCK_COLOR = (85, 85, 90, 255)
GUN_SELECT_LOCK_KEYHOLE_COLOR = (40, 40, 45, 255)
GUN_SELECT_EXIT_BUTTON_WIDTH = 220
GUN_SELECT_EXIT_BUTTON_HEIGHT = 100
GUN_SELECT_EXIT_BUTTON_RIGHT = SCREEN_WIDTH - 60
GUN_SELECT_EXIT_BUTTON_BOTTOM = 60
GUN_SELECT_EXIT_BUTTON_COLOR = (130, 60, 55)
GUN_SELECT_EXIT_BUTTON_HOVER_COLOR = (190, 80, 70)

# 총기 선택 화면 좌측 하단의 난이도 버튼.
GUN_SELECT_DIFFICULTY_BUTTON_WIDTH = 150
GUN_SELECT_DIFFICULTY_BUTTON_HEIGHT = 90
GUN_SELECT_DIFFICULTY_BUTTON_GAP = 20
GUN_SELECT_DIFFICULTY_BUTTON_LEFT = 60
GUN_SELECT_DIFFICULTY_BUTTON_BOTTOM = 60
GUN_SELECT_DIFFICULTY_LABEL_Y = (
    GUN_SELECT_DIFFICULTY_BUTTON_BOTTOM
    + GUN_SELECT_DIFFICULTY_BUTTON_HEIGHT
    + 45
)
GUN_SELECT_DIFFICULTY_SELECTED_COLOR = (180, 180, 180, 255)
GUN_SELECT_DIFFICULTY_UNSELECTED_COLOR = (55, 65, 80, 255)
# NORMAL은 기존 색을 유지하고 EASY/HARD는 각 버튼과 표시 문구에 사용한다.
GUN_SELECT_DIFFICULTY_LABEL_COLOR = (255, 220, 100)
GUN_SELECT_DIFFICULTY_TEXT_COLORS = {
    DIFFICULTY_EASY: (80, 220, 120),
    DIFFICULTY_NORMAL: GUN_SELECT_DIFFICULTY_LABEL_COLOR,
    DIFFICULTY_HARD: (240, 90, 90),
}

# 기록 확인 화면: table 배경 위에 book 이미지를 출력한다.
RECORDS_BOOK_WIDTH = 1402
RECORDS_BOOK_HEIGHT = 1122
# book.png에서 종이(밝은 페이지) 영역의 이미지 좌표(위쪽 기준).
RECORDS_BOOK_PAPER_TOP_IMAGE_Y = 31
RECORDS_BOOK_PAPER_BOTTOM_IMAGE_Y = 950
RECORDS_TITLE_Y_OFFSET = 60
RECORDS_FIRST_ROW_Y_OFFSET = 150
RECORDS_ROW_GAP = 70
RECORDS_LEFT_PAGE_CENTER_X = 585
RECORDS_RIGHT_PAGE_CENTER_X = 1215
GUN_SELECT_HOVER_OUTLINE_COLOR = (120, 170, 230, 255)

GUN_SELECT_IMAGE_SIZES = {
    "pistol": (220, 125),
    "rifle": (280, 112),
    "machine_gun": (320, 78),
}

def gun_select_card_rect(index):
    left = GUN_SELECT_CARD_LEFT + index * (
        GUN_SELECT_CARD_WIDTH + GUN_SELECT_CARD_GAP
    )
    return left, GUN_SELECT_CARD_BOTTOM, left + GUN_SELECT_CARD_WIDTH, GUN_SELECT_CARD_TOP


def gun_select_exit_button_rect():
    return (
        GUN_SELECT_EXIT_BUTTON_RIGHT - GUN_SELECT_EXIT_BUTTON_WIDTH,
        GUN_SELECT_EXIT_BUTTON_BOTTOM,
        GUN_SELECT_EXIT_BUTTON_RIGHT,
        GUN_SELECT_EXIT_BUTTON_BOTTOM + GUN_SELECT_EXIT_BUTTON_HEIGHT,
    )


def gun_select_difficulty_button_rect(index):
    left = GUN_SELECT_DIFFICULTY_BUTTON_LEFT + index * (
        GUN_SELECT_DIFFICULTY_BUTTON_WIDTH
        + GUN_SELECT_DIFFICULTY_BUTTON_GAP
    )
    return (
        left,
        GUN_SELECT_DIFFICULTY_BUTTON_BOTTOM,
        left + GUN_SELECT_DIFFICULTY_BUTTON_WIDTH,
        GUN_SELECT_DIFFICULTY_BUTTON_BOTTOM
        + GUN_SELECT_DIFFICULTY_BUTTON_HEIGHT,
    )


def records_exit_button_rect():
    return gun_select_exit_button_rect()


def rect_contains(rect, x, y):
    if x is None or y is None:
        return False
    left, bottom, right, top = rect
    return left <= x <= right and bottom <= y <= top


def gun_select_stat_rows(gun_id, level):
    spec = weapon_stats_at_level(gun_id, level)
    return (
        ("LEVEL", str(level)),
        ("DAMAGE", str(spec.damage)),
        ("FIRE INTERVAL", "{:.3f}s".format(spec.fire_interval_seconds)),
        ("RELOAD TIME", "{:.1f}s".format(spec.reload_seconds)),
        ("MAX TEMP", "{:.1f}".format(spec.temperature_limit)),
        ("MAGAZINE SIZE", str(spec.magazine_size)),
    )


def gun_select_stat_row_y(row_index):
    reference_height = GUN_SELECT_IMAGE_SIZES[RIFLE_GUN_ID][1]
    return (
        GUN_SELECT_IMAGE_Y
        - reference_height / 2
        - GUN_SELECT_STATE_FIRST_ROW_OFFSET
        - row_index * GUN_SELECT_STATE_ROW_GAP
    )


class LobbyScene:
    """Lifecycle of the lobby: initialisation, update, and rendering."""

    def __init__(
        self,
        player,
        background=None,
        hud_font=None,
        state=None,
        node_key=None,
        gun_images=None,
        gun_select_background=None,
        selected_slot_image=None,
        unselected_slot_image=None,
        records_background=None,
        records_book_image=None,
        notice=None,
        audio=None,
    ):
        self.player = player
        self.background = background
        self.hud_font = hud_font
        self.state = state
        self.gun_images = gun_images or {}
        self.gun_select_background = gun_select_background
        self.selected_slot_image = selected_slot_image
        self.unselected_slot_image = unselected_slot_image
        self.records_background = records_background
        self.records_book_image = records_book_image
        self.notice = notice or ""
        self.audio = audio
        self.keys = set()
        self.mouse_screen_x = SCREEN_WIDTH / 2
        self.mouse_screen_y = SCREEN_HEIGHT / 2
        self.exit_requested = False
        self.pending_action = None
        self.portal_entry_active = False
        self.portal_entry_elapsed = 0.0
        self.portal_entry_start = (0.0, 0.0)
        self.portal_entry_target = (0.0, 0.0)
        self.portal_entry_angle = 0.0
        self.portal_entry_opacity = 1.0
        self.portal_entry_scale = 1.0
        self.locations = tuple(LOBBY_LOCATIONS)
        self.current_node = (
            node_key if node_key in LOBBY_NODE_BY_KEY else LOBBY_START_KEY
        )
        self.nearby_location = None
        self.panel = None
        self.gun_selection_index = 0
        self.gun_select_pending_gun_id = None
        self.gun_select_hover_target = None
        self.gun_select_hover_index = None
        self.gun_select_difficulty = DEFAULT_DIFFICULTY
        self.gun_select_difficulty_hover_index = None
        self.records_hover_exit = False
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
        if self.portal_entry_active:
            self._update_portal_entry(delta_time)

    def _update_portal_entry(self, delta_time):
        self.portal_entry_elapsed = min(
            PORTAL_ENTRY_SECONDS, self.portal_entry_elapsed + max(0.0, delta_time)
        )
        linear_progress = self.portal_entry_elapsed / PORTAL_ENTRY_SECONDS
        growth = math.exp(PORTAL_ENTRY_SPEED_GROWTH_RATE)
        progress = (math.exp(PORTAL_ENTRY_SPEED_GROWTH_RATE * linear_progress) - 1.0) / (
            growth - 1.0
        )
        start_x, start_y = self.portal_entry_start
        target_x, target_y = self.portal_entry_target
        if self.player is not None:
            self.player.x = start_x + (target_x - start_x) * progress
            self.player.y = start_y + (target_y - start_y) * progress
        self.portal_entry_angle = (
            math.tau * PORTAL_ENTRY_TOTAL_ROTATIONS * progress
        )
        self.portal_entry_opacity = 1.0 - progress
        self.portal_entry_scale = 1.0 - progress
        if self.portal_entry_elapsed >= PORTAL_ENTRY_SECONDS:
            self.portal_entry_active = False
            self.portal_entry_opacity = 0.0
            self.portal_entry_scale = 0.0
            self.pending_action = "battle_entry_loading"

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
            if self.portal_entry_active:
                self.player.draw(
                    angle=self.portal_entry_angle,
                    opacity=self.portal_entry_opacity,
                    scale=self.portal_entry_scale,
                )
            else:
                self.player.draw()
        if not self.portal_entry_active:
            self._draw_direction_arrows()
        if self.hud_font is not None:
            self.hud_font.draw(
                40,
                SCREEN_HEIGHT - 60,
                "LOBBY",
                (255, 255, 255),
            )
            if self.notice:
                draw_text_at_center(
                    self.hud_font,
                    SCREEN_WIDTH / 2,
                    SCREEN_HEIGHT - 110,
                    self.notice,
                    (255, 190, 90),
                )
        self._draw_location_labels()
        if self.panel == "records":
            self._draw_records_panel(draw_rectangle)
        elif self.panel == "gun_select":
            self._draw_gun_selection_panel(draw_rectangle)

    def _draw_gun_selection_panel(self, draw_rectangle):
        """Draw the three gun cards that are shown before the battle starts."""
        if self.gun_select_background is not None:
            self.gun_select_background.draw(
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 2,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            )
        else:
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
            GUN_SELECT_TITLE_Y,
            "SELECT GUN",
            (255, 220, 100),
        )
        selected_gun_id = self._selected_gun_id()
        for index, gun_id in enumerate(GUN_SHOP_ORDER):
            self._draw_gun_select_card(
                draw_rectangle, index, gun_id, selected_gun_id
            )
        self._draw_gun_select_difficulty_buttons(draw_rectangle)
        self._draw_gun_select_exit_button(draw_rectangle)

    def _draw_gun_select_difficulty_buttons(self, draw_rectangle):
        """Draw the three difficulty buttons in the lower-left corner."""
        first_rect = gun_select_difficulty_button_rect(0)
        last_rect = gun_select_difficulty_button_rect(len(DIFFICULTIES) - 1)
        draw_text_at_center(
            self.hud_font,
            (first_rect[0] + last_rect[2]) / 2,
            GUN_SELECT_DIFFICULTY_LABEL_Y,
            "DIFFICULTY: {}".format(self.gun_select_difficulty),
            GUN_SELECT_DIFFICULTY_TEXT_COLORS[self.gun_select_difficulty],
        )
        for index, difficulty in enumerate(DIFFICULTIES):
            left, bottom, right, top = gun_select_difficulty_button_rect(index)
            selected = difficulty == self.gun_select_difficulty
            color = (
                GUN_SELECT_DIFFICULTY_SELECTED_COLOR
                if selected
                else GUN_SELECT_DIFFICULTY_UNSELECTED_COLOR
            )
            draw_rectangle(left, bottom, right, top, *color, True)
            if index == self.gun_select_difficulty_hover_index:
                draw_rectangle(
                    left,
                    bottom,
                    right,
                    top,
                    *GUN_SELECT_HOVER_OUTLINE_COLOR,
                    False,
                )
            draw_text_at_center(
                self.hud_font,
                (left + right) / 2,
                (bottom + top) / 2,
                difficulty,
                GUN_SELECT_DIFFICULTY_TEXT_COLORS[difficulty],
            )

    def _selected_gun_id(self):
        if self.gun_select_pending_gun_id is not None:
            return self.gun_select_pending_gun_id
        if self.state is None:
            return None
        owned_guns = self.state.owned_guns
        if not 0 <= self.gun_selection_index < len(owned_guns):
            return None
        return owned_guns[self.gun_selection_index]

    def _draw_gun_select_card(self, draw_rectangle, index, gun_id, selected_gun_id):
        left, bottom, right, top = gun_select_card_rect(index)
        center_x = (left + right) / 2
        center_y = (bottom + top) / 2
        owned = self.state is not None and self.state.owns_gun(gun_id)
        selected = owned and gun_id == selected_gun_id

        slot_image = (
            self.selected_slot_image if selected else self.unselected_slot_image
        )
        if slot_image is not None:
            slot_size = (
                GUN_SELECT_SELECTED_SLOT_SIZE
                if selected
                else GUN_SELECT_UNSELECTED_SLOT_SIZE
            )
            slot_image.draw(center_x, center_y, *slot_size)
        else:
            draw_rectangle(left, bottom, right, top, 38, 40, 52, 255, True)
            if selected:
                draw_rectangle(left, bottom, right, top, 255, 220, 100, 255, False)
        if index == self.gun_select_hover_index:
            draw_rectangle(
                left,
                bottom,
                right,
                top,
                *GUN_SELECT_HOVER_OUTLINE_COLOR,
                False,
            )

        name_color = (255, 220, 100) if owned else (150, 155, 170)
        draw_text_at_center(
            self.hud_font, center_x, GUN_SELECT_NAME_Y, weapon_display_name(gun_id), name_color
        )
        self._draw_gun_select_image(draw_rectangle, gun_id, center_x, owned)
        self._draw_gun_select_stats(gun_id, center_x, owned)

    def _draw_gun_select_image(self, draw_rectangle, gun_id, center_x, owned):
        image = self.gun_images.get(gun_id)
        if image is None:
            draw_text_at_center(
                self.hud_font,
                center_x,
                GUN_SELECT_IMAGE_Y,
                "[{}]".format(weapon_display_name(gun_id)),
                (170, 190, 220),
            )
        else:
            width, height = GUN_SELECT_IMAGE_SIZES[gun_id]
            opacify = getattr(image, "opacify", None)
            if owned or opacify is None:
                image.draw(center_x, GUN_SELECT_IMAGE_Y, width, height)
            else:
                opacify(GUN_SELECT_LOCKED_OPACITY)
                try:
                    image.draw(center_x, GUN_SELECT_IMAGE_Y, width, height)
                finally:
                    opacify(1.0)
        if not owned:
            self._draw_gun_select_lock(draw_rectangle, center_x)

    def _draw_gun_select_lock(self, draw_rectangle, center_x):
        center_y = GUN_SELECT_IMAGE_Y
        draw_rectangle(
            center_x - 28,
            center_y + 10,
            center_x + 28,
            center_y + 24,
            *GUN_SELECT_LOCK_COLOR,
            True,
        )
        draw_rectangle(
            center_x - 28,
            center_y - 12,
            center_x - 16,
            center_y + 18,
            *GUN_SELECT_LOCK_COLOR,
            True,
        )
        draw_rectangle(
            center_x + 16,
            center_y - 12,
            center_x + 28,
            center_y + 18,
            *GUN_SELECT_LOCK_COLOR,
            True,
        )
        draw_rectangle(
            center_x - 44,
            center_y - 58,
            center_x + 44,
            center_y + 12,
            *GUN_SELECT_LOCK_COLOR,
            True,
        )
        draw_rectangle(
            center_x - 8,
            center_y - 42,
            center_x + 8,
            center_y - 12,
            *GUN_SELECT_LOCK_KEYHOLE_COLOR,
            True,
        )

    def _draw_gun_select_stats(self, gun_id, center_x, owned):
        if not owned:
            return
        level = self.state.upgrade_level(gun_id) if self.state is not None else 0
        for row_index, (label, value) in enumerate(gun_select_stat_rows(gun_id, level)):
            draw_text_at_center(
                self.hud_font,
                center_x,
                gun_select_stat_row_y(row_index),
                "{} {}".format(label, value),
                GUN_SELECT_STATE_TEXT_COLOR,
            )

    def _draw_gun_select_exit_button(self, draw_rectangle):
        left, bottom, right, top = gun_select_exit_button_rect()
        hovered = self.gun_select_hover_target == ("exit", None)
        color = (
            GUN_SELECT_EXIT_BUTTON_HOVER_COLOR
            if hovered
            else GUN_SELECT_EXIT_BUTTON_COLOR
        )
        draw_rectangle(left, bottom, right, top, *color, 255, True)
        draw_text_at_center(
            self.hud_font,
            (left + right) / 2,
            (bottom + top) / 2,
            "EXIT",
            (255, 255, 255),
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
        color = (15, 180, 15, 255)
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
        location_colors = {
            "shop": (255, 220, 100),
            "records": (0, 128, 0),
            "stairs": (255, 70, 60),
            "training": (205, 133, 63),
            "portal": (80, 140, 255),
            "center": (255, 255, 255),
        }
        color = location_colors.get(location.key, (170, 190, 220))
        draw_text_at_center(
            self.hud_font,
            location.zone_x,
            label_y,
            location.label,
            color,
        )

    def _draw_records_panel(self, draw_rectangle):
        """Draw the battle records on the paper area of the book image."""
        if self.records_background is not None:
            self.records_background.draw(
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 2,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            )
        else:
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

        book_bottom = (SCREEN_HEIGHT - RECORDS_BOOK_HEIGHT) / 2
        if self.records_book_image is not None:
            self.records_book_image.draw(
                SCREEN_WIDTH / 2,
                book_bottom + RECORDS_BOOK_HEIGHT / 2,
                RECORDS_BOOK_WIDTH,
                RECORDS_BOOK_HEIGHT,
            )
        else:
            draw_rectangle(
                SCREEN_WIDTH / 2 - RECORDS_BOOK_WIDTH / 2,
                book_bottom,
                SCREEN_WIDTH / 2 + RECORDS_BOOK_WIDTH / 2,
                book_bottom + RECORDS_BOOK_HEIGHT,
                60,
                40,
                25,
                255,
                True,
            )

        if self.hud_font is None:
            return
        paper_top_y = SCREEN_HEIGHT - (
            book_bottom + RECORDS_BOOK_PAPER_TOP_IMAGE_Y
        )
        paper_bottom_y = SCREEN_HEIGHT - (
            book_bottom + RECORDS_BOOK_PAPER_BOTTOM_IMAGE_Y
        )
        title_y = paper_top_y - RECORDS_TITLE_Y_OFFSET
        first_row_y = paper_top_y - RECORDS_FIRST_ROW_Y_OFFSET
        text_color = (40, 30, 20)
        battle_records = self.state.records if self.state is not None else []
        training_records = (
            self.state.training_records if self.state is not None else []
        )
        draw_text_at_center(
            self.hud_font,
            RECORDS_LEFT_PAGE_CENTER_X,
            title_y,
            "BATTLE RECORDS",
            text_color,
        )
        draw_text_at_center(
            self.hud_font,
            RECORDS_RIGHT_PAGE_CENTER_X,
            title_y,
            "TRAINING RECORDS",
            text_color,
        )
        if battle_records:
            for index, record in enumerate(battle_records):
                text = result_record_text(
                    record.result,
                    record.reached_wave,
                    TOTAL_WAVES,
                    record.elapsed_time,
                    record.clear_time,
                )
                row_y = first_row_y - index * RECORDS_ROW_GAP
                if row_y < paper_bottom_y:
                    break
                draw_text_at_center(
                    self.hud_font,
                    RECORDS_LEFT_PAGE_CENTER_X,
                    row_y,
                    text,
                    text_color,
                )
        else:
            draw_text_at_center(
                self.hud_font,
                RECORDS_LEFT_PAGE_CENTER_X,
                first_row_y,
                "NO RECORDS YET",
                text_color,
            )
        if training_records:
            for index, record in enumerate(training_records):
                row_y = first_row_y - index * RECORDS_ROW_GAP
                if row_y < paper_bottom_y:
                    break
                draw_text_at_center(
                    self.hud_font,
                    RECORDS_RIGHT_PAGE_CENTER_X,
                    row_y,
                    training_record_text(record.targets_destroyed),
                    text_color,
                )
        else:
            draw_text_at_center(
                self.hud_font,
                RECORDS_RIGHT_PAGE_CENTER_X,
                first_row_y,
                "NO RECORDS YET",
                text_color,
            )
        self._draw_records_exit_button(draw_rectangle)

    def _draw_records_exit_button(self, draw_rectangle):
        left, bottom, right, top = records_exit_button_rect()
        color = (
            GUN_SELECT_EXIT_BUTTON_HOVER_COLOR
            if self.records_hover_exit
            else GUN_SELECT_EXIT_BUTTON_COLOR
        )
        draw_rectangle(left, bottom, right, top, *color, 255, True)
        draw_text_at_center(
            self.hud_font,
            (left + right) / 2,
            (bottom + top) / 2,
            "EXIT",
            (255, 255, 255),
        )

    def key_down(self, key):
        key = key.lower()
        if key in self.keys:
            return
        self.keys.add(key)
        if self.portal_entry_active:
            return
        if self.panel is not None:
            if self.panel == "gun_select":
                self._handle_gun_selection_key(key)
            elif key in ("q", "escape"):
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
            self.pending_action = "return_to_title"
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
        self._start_portal_entry()

    def _stop_lobby_music(self):
        if self.audio is None:
            return
        stop = getattr(self.audio, "stop", None)
        if stop is not None:
            stop()

    def _play_portal_entry_sound(self):
        if self.audio is None:
            return
        play_sound = getattr(self.audio, "play_sound", None)
        if play_sound is not None:
            play_sound(LOBBY_PORTAL_ENTRY_SOUND_FILE)

    def _start_portal_entry(self):
        if self.portal_entry_active:
            return
        portal = LOBBY_NODE_BY_KEY["portal"]
        start_x = self.player.x if self.player is not None else portal.zone_x
        start_y = self.player.y if self.player is not None else portal.zone_y
        self.portal_entry_active = True
        self.portal_entry_elapsed = 0.0
        self.portal_entry_start = (start_x, start_y)
        self.portal_entry_target = (
            portal.zone_x,
            portal.zone_y + PORTAL_ENTRY_MOVE_DEPTH,
        )
        self.portal_entry_angle = 0.0
        self.portal_entry_opacity = 1.0
        self.portal_entry_scale = 1.0
        self._stop_lobby_music()
        self._play_portal_entry_sound()

    def open_gun_selection(self):
        """Show the gun selection screen before the battle starts."""
        self.panel = "gun_select"
        self.gun_selection_index = 0
        self.gun_select_pending_gun_id = None
        self.gun_select_hover_target = None
        self.gun_select_hover_index = None
        self.gun_select_difficulty_hover_index = None
        self.gun_select_difficulty = (
            normalize_difficulty(self.state.difficulty)
            if self.state is not None
            else DEFAULT_DIFFICULTY
        )
        if self.state is None:
            return
        if self.state.selected_gun in self.state.owned_guns:
            self.gun_selection_index = self.state.owned_guns.index(
                self.state.selected_gun
            )

    def _handle_gun_selection_key(self, key):
        """Move the selection and confirm or cancel the chosen gun."""
        if key == "escape":
            self.close_panel()
            return
        owned_guns = self.state.owned_guns if self.state is not None else []
        if not owned_guns:
            return
        if key in ("w", "up"):
            self.gun_selection_index = (self.gun_selection_index - 1) % len(owned_guns)
        elif key in ("s", "down"):
            self.gun_selection_index = (self.gun_selection_index + 1) % len(owned_guns)
        elif key == "space":
            self._confirm_gun_selection()

    def _confirm_gun_selection(self, gun_id=None):
        """Store the chosen gun and start the portal entry animation."""
        if self.state is None:
            self.close_panel()
            return
        if gun_id is None:
            gun_id = self.state.owned_guns[self.gun_selection_index]
        if not self.state.owns_gun(gun_id):
            return
        self.state.set_difficulty(self.gun_select_difficulty)
        self.state.select_gun(gun_id)
        self.close_panel()
        self._start_portal_entry()

    def _play_records_music(self):
        if self.audio is not None:
            self.audio.play(RECORDS_MUSIC_FILE)

    def _restore_lobby_music(self):
        if self.audio is not None:
            self.audio.play(LOBBY_MUSIC_FILE)

    def open_records(self):
        """Show the battle record panel."""
        if self.panel == "records":
            return
        self.panel = "records"
        self.records_hover_exit = False
        self._play_records_music()

    def close_panel(self):
        """Close the panel that is currently open."""
        was_records_panel = self.panel == "records"
        self.panel = None
        self.gun_select_pending_gun_id = None
        self.gun_select_hover_target = None
        self.gun_select_hover_index = None
        self.gun_select_difficulty_hover_index = None
        self.records_hover_exit = False
        if was_records_panel:
            self._restore_lobby_music()

    def key_up(self, key):
        self.keys.discard(key.lower())

    def _gun_select_target_at(self, screen_x, screen_y):
        canvas_y = SCREEN_HEIGHT - screen_y
        for index in range(len(DIFFICULTIES)):
            if rect_contains(
                gun_select_difficulty_button_rect(index), screen_x, canvas_y
            ):
                return ("difficulty", index)
        if rect_contains(gun_select_exit_button_rect(), screen_x, canvas_y):
            return ("exit", None)
        for index in range(len(GUN_SHOP_ORDER)):
            if rect_contains(gun_select_card_rect(index), screen_x, canvas_y):
                return ("gun", index)
        return None

    def mouse_move(self, screen_x, screen_y):
        self.mouse_screen_x = screen_x
        self.mouse_screen_y = screen_y
        if self.portal_entry_active:
            return
        canvas_y = SCREEN_HEIGHT - screen_y
        if self.panel == "records":
            self.gun_select_hover_target = None
            self.gun_select_hover_index = None
            self.gun_select_difficulty_hover_index = None
            self.records_hover_exit = rect_contains(
                records_exit_button_rect(), screen_x, canvas_y
            )
            return
        if self.panel != "gun_select":
            self.gun_select_hover_target = None
            self.gun_select_hover_index = None
            self.gun_select_difficulty_hover_index = None
            self.records_hover_exit = False
            return
        self.records_hover_exit = False
        target = self._gun_select_target_at(screen_x, screen_y)
        self.gun_select_hover_target = target
        self.gun_select_hover_index = (
            target[1] if target is not None and target[0] == "gun" else None
        )
        self.gun_select_difficulty_hover_index = (
            target[1]
            if target is not None and target[0] == "difficulty"
            else None
        )
        if self.state is None or self.gun_select_hover_index is None:
            return
        gun_id = GUN_SHOP_ORDER[self.gun_select_hover_index]
        if self.state.owns_gun(gun_id):
            self.gun_selection_index = self.state.owned_guns.index(gun_id)

    def mouse_down(self, button, screen_x=None, screen_y=None):
        if button != "left" or screen_x is None or screen_y is None:
            return None
        if self.portal_entry_active:
            return None
        if self.panel == "records":
            canvas_y = SCREEN_HEIGHT - screen_y
            if rect_contains(records_exit_button_rect(), screen_x, canvas_y):
                self.close_panel()
            return None
        if self.panel != "gun_select":
            return None
        target = self._gun_select_target_at(screen_x, screen_y)
        if target is not None and target[0] == "exit":
            self.close_panel()
            return None
        if target is not None and target[0] == "difficulty":
            self.gun_select_difficulty = DIFFICULTIES[target[1]]
            return None
        if target is None:
            return None
        gun_id = GUN_SHOP_ORDER[target[1]]
        if self.state is None or not self.state.owns_gun(gun_id):
            return None
        if self.gun_select_pending_gun_id == gun_id:
            self._confirm_gun_selection(gun_id)
        else:
            self.gun_select_pending_gun_id = gun_id
            self.gun_selection_index = self.state.owned_guns.index(gun_id)
        return None

    def mouse_up(self, button):
        return None

    def close(self):
        return None
